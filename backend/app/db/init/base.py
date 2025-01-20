"""数据库初始化模块"""
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from zoneinfo import ZoneInfo
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\ChatRoom\backend')
from app.utils import encoding_utils
from app.db.database import engine, AsyncSessionLocal
from app.db.base import Base

# 导入所需的模型
from app.domain.user.models import User
from app.domain.group.models import Group, GroupMember
from app.domain.device.models import Device
from app.domain.message.models import PrivateMessage, MessageReaction, MessageMention

# 导入服务和仓储
from app.domain.user.service import UserService
from app.domain.user.repository import UserRepository
from app.domain.group.repository import GroupRepository, GroupMemberRepository
from app.domain.group.service import GroupService
from app.domain.message.service import MessageService
from app.domain.message.repositories import PrivateMessageRepository, GroupMessageRepository
from app.domain.message.enums import MessageStatus
from app.domain.device.service import DeviceService
from app.domain.device.repository import DeviceRepository

import Lugwit_Module as LM
lprint = LM.lprint

async def get_all_tables(engine) -> list:
    """获取数据库中的所有表名"""
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """))
        return [row[0] for row in result]

async def get_table_count(conn, table: str) -> int:
    """获取指定表的记录数"""
    result = await conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
    return result.scalar()

async def drop_all_tables(engine):
    """删除数据库中的所有表"""
    try:
        tables = await get_all_tables(engine)
        if not tables:
            lprint("[数据库初始化] 数据库为空,无需删除表")
            return True
        
        lprint(f"[数据库初始化] 准备清理以下表: {', '.join(tables)}")
        total_tables = len(tables)
        
        # 禁用外键约束
        async with engine.begin() as conn:
            await conn.execute(text("SET session_replication_role = 'replica';"))
            
            # 删除所有表
            for idx, table in enumerate(tables, 1):
                try:
                    await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    lprint(f"[数据库清理] ({idx}/{total_tables}) 已清理表 {table}")
                except Exception as e:
                    lprint(f"删除表 {table} 时出错: {str(e)}")
                    raise
            
            # 启用外键约束
            await conn.execute(text("SET session_replication_role = 'origin';"))
            
            # 验证表是否已全部删除
            verify_result = await conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            remaining_tables = [row[0] for row in verify_result]
            
            if remaining_tables:
                error_msg = f"表删除失败，以下表仍然存在: {', '.join(remaining_tables)}"
                lprint(error_msg)
                return False
            
            lprint("[数据库清理] 所有表已成功清理")
            return True
            
    except Exception as e:
        error_msg = f"删除表时发生错误: {str(e)}"
        lprint(error_msg)
        return False

async def verify_database_tables():
    """验证数据库表是否正确创建"""
    try:
        async with engine.begin() as conn:
            # 检查所有必需的表是否存在
            required_tables = [
                'users', 'groups', 'group_members', 'private_messages', 
                'message_reactions', 'message_mentions',
                'devices'
            ]
            
            # 获取当前存在的表
            result = await conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            existing_tables = {row[0] for row in result}
            
            # 检查必需的表是否都存在
            missing_tables = [table for table in required_tables if table not in existing_tables]
            if missing_tables:
                lprint(f"[数据库检查] 错误：以下必需的表未创建成功: {', '.join(missing_tables)}")
                return False
                
            # 检查每个表是否有数据
            for table in required_tables:
                count = await get_table_count(conn, table)
                lprint(f"[数据库检查] 表 {table} 当前记录数: {count}")
            
            return True
            
    except Exception as e:
        lprint(f"[数据库检查] 验证数据库表时出错: {str(e)}")
        return False

async def verify_table_data(conn, table_name: str, expected_count: int = None):
    """验证表中的数据"""
    try:
        count = await get_table_count(conn, table_name)
        lprint(f"[数据库验证] 表 {table_name} 当前记录数: {count}")
        return count == expected_count
    except Exception as e:
        lprint(f"[数据库验证] 验证表 {table_name} 数据时出错: {str(e)}")
        return False

async def verify_group_member(group_id: int, user_id: int, group_repo: GroupRepository, user_repo: UserRepository) -> bool:
    """验证用户是否是群组成员
    
    Args:
        group_id: 群组ID
        user_id: 用户ID
        group_repo: 群组仓储
        user_repo: 用户仓储
        
    Returns:
        是否是成员
    """
    try:
        # 创建群组成员仓储
        group_member_repo = GroupMemberRepository(group_repo.session)
        
        # 获取用户和群组信息
        user = await user_repo.get_by_id(user_id)
        group = await group_repo.get_by_id(group_id)
        
        if not user or not group:
            lprint(f"[群组成员验证] 用户或群组不存在: user_id={user_id}, group_id={group_id}")
            return False
            
        # 检查用户是否是群组成员
        is_member = await group_member_repo.is_member(group_id, user_id)
        if not is_member:
            lprint(f"[群组成员验证] 用户(ID:{user_id}, 用户名:{user.username})不是群组(ID:{group_id}, 群组名:{group.name})的成员")
            return False
            
        return True
    except Exception as e:
        lprint(f"[群组成员验证] 验证群组成员时出错: {str(e)}")
        return False

async def init_db() -> None:
    """初始化数据库"""
    try:
        # 删除所有表
        lprint("[数据库初始化] 开始初始化数据库...")
        if not await drop_all_tables(engine):
            lprint("[数据库初始化] 删除表失败")
            
        # 创建所有表
        lprint("[数据库初始化] 开始创建数据库...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # 验证数据库表是否创建成功
        if not await verify_database_tables():
            lprint("[数据库初始化] 数据库表创建失败")
            sys.exit(1)

        # 创建会话
        async with AsyncSessionLocal() as session:
            # 加载初始数据
            lprint("[数据加载] 开始加载初始数据...")
            
            # 创建仓储实例
            user_repo = UserRepository(session)
            group_repo = GroupRepository(session)
            member_repo = GroupMemberRepository(session)
            private_message_repo = PrivateMessageRepository(session)
            group_message_repo = GroupMessageRepository(session)
            device_repo = DeviceRepository(session)
            
            # 创建服务实例
            user_service = UserService(user_repo)
            group_service = GroupService(group_repo, member_repo, user_repo)
            message_service = MessageService(
                private_repo=private_message_repo,
                group_repo=group_message_repo,
                group_repository=group_repo,
                user_repo=user_repo,
                member_repo=member_repo
            )
            device_service = DeviceService(device_repo)
            
            # 读取初始数据
            data_dir = Path(__file__).parent / "data"
            
            try:
                # 步骤3: 加载用户数据
                lprint("[用户数据加载] 开始加载用户数据...")
                users_count = 0
                users_file = data_dir / "users.json"
                if users_file.exists():
                    with open(users_file, "r", encoding="utf-8") as f:
                        users_data = json.load(f)
                        for user_data in users_data:
                            await user_service.create_user(**user_data)
                            users_count += 1
                        await session.commit()
                
                # 验证用户数据
                async with engine.begin() as conn:
                    if not await verify_table_data(conn, "users", users_count):
                        lprint("[用户数据加载] 用户数据加载失败，程序退出")
                        sys.exit(1)
                lprint("[用户数据加载] 用户数据加载成功！")
                
                # 步骤4: 加载群组数据
                lprint("[群组数据加载] 开始加载群组数据...")
                groups_count = 0
                groups_file = data_dir / "groups.json"
                if groups_file.exists():
                    with open(groups_file, "r", encoding="utf-8") as f:
                        groups_data = json.load(f)
                        for group_data in groups_data:
                            # 获取群主ID
                            owner = await user_repo.get_by_username(group_data["owner"])
                            if not owner:
                                lprint(f"[群组数据加载] 跳过群组: 找不到群主 - {group_data}")
                                continue
                                
                            # 创建群组
                            group = await group_service.create_group(
                                name=group_data["name"],
                                owner_id=owner.id,
                                description=group_data.get("description", "")
                            )
                            
                            # 添加管理员为群组成员
                            for admin_username in group_data.get("admins", []):
                                admin = await user_repo.get_by_username(admin_username)
                                if not admin:
                                    lprint(f"[群组数据加载] 跳过群组管理员: 找不到用户 - {admin_username}")
                                    continue
                                await group_service.add_member(group.id, admin.id)
                                
                            # 添加群组成员
                            for member_username in group_data.get("members", []):
                                member = await user_repo.get_by_username(member_username)
                                if not member:
                                    lprint(f"[群组数据加载] 跳过群组成员: 找不到用户 - {member_username}")
                                    continue
                                await group_service.add_member(group.id, member.id)
                                
                            groups_count += 1
                        await session.commit()
                
                # 验证群组数据
                async with engine.begin() as conn:
                    if not await verify_table_data(conn, "groups", groups_count):
                        lprint("[群组数据加载] 群组数据加载失败，程序退出")
                        sys.exit(1)
                lprint("[群组数据加载] 群组数据加载成功！")
                
                # 步骤5: 加载消息数据
                lprint("[消息数据加载] 开始加载消息数据...")
                private_messages_count = 0
                group_messages_count = 0
                messages_file = data_dir / "messages.json"
                if messages_file.exists():
                    with open(messages_file, "r", encoding="utf-8") as f:
                        messages_data = json.load(f)
                        
                        # 加载私聊消息
                        for message_data in messages_data.get("private_messages", []):
                            sender = await user_repo.get_by_username(message_data["sender"])
                            recipient = await user_repo.get_by_username(message_data["recipient"])
                            
                            if not sender or not recipient:
                                lprint(f"[消息数据加载] 跳过消息: 发送者或接收者不存在 - {message_data}")
                                continue
                            
                            message_data.pop("mentions", None)
                            await message_service.create_message(
                                content=message_data["content"],
                                sender_id=sender.id,
                                receiver_id=recipient.id,
                                content_type=message_data["content_type"],
                                status=MessageStatus.sent
                            )
                            private_messages_count += 1
                        await session.commit()
                            
                        # 加载群组消息
                        for message_data in messages_data.get("group_messages", []):
                            sender = await user_repo.get_by_username(message_data["sender"])
                            group = await group_repo.get_by_name(message_data["group_name"])
                            
                            if not sender or not group:
                                lprint(f"[消息数据加载] 跳过消息: 发送者或群组不存在 - {message_data}")
                                continue
                            
                            # 验证发送者是否是群组成员
                            if not await verify_group_member(group.id, sender.id, group_repo, user_repo):
                                continue
                            
                            message_data.pop("mentions", None)
                            await message_service.create_message(
                                content=message_data["content"],
                                sender_id=sender.id,
                                group_id=group.id,
                                content_type=message_data["content_type"],
                                status=MessageStatus.sent
                            )
                            group_messages_count += 1
                        await session.commit()
                
                # 验证消息数据
                async with engine.begin() as conn:
                    if not await verify_table_data(conn, "private_messages", private_messages_count):
                        lprint("[消息数据加载] 私聊消息数据加载失败，程序退出")
                        sys.exit(1)
                    # 群组消息在各自的表中，这里只验证是否有数据
                    if group_messages_count > 0:
                        tables = await conn.execute(text("""
                            SELECT tablename FROM pg_tables 
                            WHERE schemaname = 'public' AND tablename LIKE 'group_messages_%'
                        """))
                        tables = [row[0] for row in tables]
                        if not tables:
                            lprint("[消息数据加载] 群组消息表未创建，程序退出")
                            sys.exit(1)
                        total_messages = 0
                        for table in tables:
                            result = await conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                            total_messages += result.scalar()
                        if total_messages != group_messages_count:
                            lprint(f"[消息数据加载] 群组消息数量不匹配。预期：{group_messages_count}，实际：{total_messages}")
                            sys.exit(1)
                lprint("[消息数据加载] 消息数据加载成功！")
                
                
            except Exception as e:
                lprint(f"[数据加载] 加载初始数据时出错: {str(e)}")
                sys.exit(1)
                
            lprint("[数据加载] 所有数据加载完成！")
            
    except Exception as e:
        lprint(f"[数据库初始化] 数据库初始化过程中出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(init_db())
