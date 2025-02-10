"""数据库初始化模块base.py"""
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import traceback
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional

# 第三方库
from sqlalchemy import text, select
from dotenv import load_dotenv
import aiofiles




# 加载环境变量
load_dotenv()

# 动态获取项目根目录并添加到Python路径
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parents[4]

# 为了快速开发,暂时保留这里的硬编码
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\ChatRoom\backend')


import Lugwit_Module as LM
lprint = LM.lprint  # 继续使用自定义的 lprint


# 导入数据库相关
from app.db.facade.database_facade import DatabaseFacade
from app.db.internal.base import Base
from app.domain.common.models.tables import (
    User, Group, GroupMember, Device,
    BaseMessage, PrivateMessage
)
from app.domain.common.enums.user import UserStatusEnum, UserRole
from app.domain.common.enums.group import GroupType, GroupMemberRole, GroupMemberStatus
from app.domain.common.enums.device import DeviceType, DeviceStatus
from app.domain.common.enums.message import (
    MessageType, MessageStatus, MessageContentType, 
    MessageTargetType, MessageDirection
)
from app.utils.security import get_password_hash
from app.core.auth.facade.auth_facade import AuthFacade


async def get_tables(conn) -> List[str]:
    """获取当前所有表名"""
    query = text("""
        SELECT tablename FROM pg_catalog.pg_tables 
        WHERE schemaname = 'public'
    """)
    result = await conn.execute(query)
    tables = [row[0] for row in result.fetchall()]
    return tables


async def drop_all_tables(conn) -> bool:
    """删除所有表"""
    try:
        tables = await get_tables(conn)
        if tables:
            lprint(f"准备删除表: {', '.join(tables)}")
            for table in tables:
                # 使用参数化查询防止SQL注入风险（虽然表名通常是可信的）
                drop_query = text(f'DROP TABLE IF EXISTS "{table}" CASCADE')
                await conn.execute(drop_query)
                lprint(f"已删除表: {table}")
        lprint("所有表删除完成")
        return True
    except Exception as e:
        lprint(f"删除表时出错: {str(e)}")
        return False


async def create_all_tables(db_facade: DatabaseFacade) -> bool:
    """使用SQLAlchemy创建所有表"""
    try:
        # 初始化基础表结构
        async with db_facade.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        lprint("基础表创建完成")
        return True
    except Exception as e:
        lprint(f"创建表时出错: {str(e)}")
        return False


async def verify_database_tables(conn) -> bool:
    """验证数据库表是否正确创建"""
    try:
        tables = await get_tables(conn)
        lprint(f"当前存在的表: {tables}")

        # 基础必需表
        required_tables = {
            'users',
            'groups',
            'group_members',
            'private_messages',
            'devices'
        }

        missing_tables = required_tables - set(tables)
        if missing_tables:
            lprint(f"以下必需的表未创建成功: {', '.join(missing_tables)}")
            return False

        # 检查群组消息表
        group_message_tables = [table for table in tables if table.startswith('group_messages_')]
        if not group_message_tables:
            lprint("警告: 未发现任何群组消息表，这些表将在需要时动态创建")
            
        lprint("所有必需的基础表已创建成功")
        return True
    except Exception as e:
        lprint(f"验证表时出错: {str(e)}")
        return False


async def load_json_file(file_path: Path) -> Optional[List[Dict[str, Any]]]:
    """异步加载JSON文件"""
    if not file_path.exists():
        lprint(f"找不到文件: {file_path}")
        return None
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
            data = json.loads(content)
            return data
    except json.JSONDecodeError as e:
        lprint(f"解析JSON文件 {file_path} 时出错: {str(e)}")
        return None
    except Exception as e:
        lprint(f"读取文件 {file_path} 时出错: {str(e)}")
        return None


async def load_initial_data(db_facade: DatabaseFacade) -> bool:
    """从 JSON 文件加载初始数据"""
    data_dir = CURRENT_DIR / "data"
    if not data_dir.exists():
        lprint("找不到数据目录")
        return False
    session=db_facade.session
    try:
        # 步骤1：加载用户数据
        users_data = await load_json_file(data_dir / "users.json")
        if users_data:
            for user_data in users_data:
                if not all(k in user_data for k in ("username", "nickname", "password", "email", "role", "status")):
                    lprint(f"用户数据缺少必要字段: {user_data}")
                    continue

                existing_user = await session.execute(
                    select(User).where(User.username == user_data["username"])
                )
                if existing_user.scalar_one_or_none():
                    lprint(f"用户已存在: {user_data['username']}, 跳过插入")
                    continue

                role_value = UserRole[user_data["role"]].value if user_data["role"] in UserRole.__members__ else UserRole.user.value
                status_value = UserStatusEnum[user_data["status"]].value if user_data["status"] in UserStatusEnum.__members__ else UserStatusEnum.normal.value

                user = User(
                    username=user_data["username"],
                    nickname=user_data["nickname"],
                    hashed_password=get_password_hash(user_data["password"]),
                    email=user_data["email"],
                    role=role_value,
                    status=status_value
                )
                session.add(user)
                lprint(f"插入用户: {user_data['username']}")
            await session.commit()
            lprint("用户数据加载完成")

        # 步骤2：加载群组数据
        groups_data = await load_json_file(data_dir / "groups.json")
        if groups_data:
            for group_data in groups_data:
                if not all(k in group_data for k in ("name", "owner")):
                    lprint(f"群组数据缺少必要字段: {group_data}")
                    continue

                existing_group = await session.execute(
                    select(Group).where(Group.name == group_data["name"])
                )
                if existing_group.scalar_one_or_none():
                    lprint(f"群组已存在: {group_data['name']}, 跳过插入")
                    continue

                owner = await session.execute(
                    select(User).where(User.username == group_data["owner"])
                )
                owner = owner.scalar_one_or_none()
                if owner is None:
                    lprint(f"找不到群主 {group_data['owner']}，跳过群组 {group_data['name']}")
                    continue

                group_type = GroupType[group_data.get("type", "normal")].value if "type" in group_data and group_data["type"] in GroupType.__members__ else GroupType.normal.value
                group = Group(
                    name=group_data["name"],
                    description=group_data.get("description", ""),
                    owner_id=owner.id,
                    type=group_type,
                    extra_data=group_data.get("extra_data", {})
                )
                session.add(group)
                lprint(f"插入群组: {group_data['name']}")
            await session.commit()
            lprint("群组数据加载完成")

            # 添加群成员
            for group_data in groups_data:
                group = await session.execute(
                    select(Group).where(Group.name == group_data["name"])
                )
                group = group.scalar_one_or_none()
                if not group:
                    continue

                owner = await session.execute(
                    select(User).where(User.id == group.owner_id)
                )
                owner = owner.scalar_one_or_none()
                if owner:
                    existing_member = await session.execute(
                        select(GroupMember).where(
                            GroupMember.group_id == group.id,
                            GroupMember.user_id == owner.id
                        )
                    )
                    if not existing_member.scalar_one_or_none():
                        member = GroupMember(
                            group_id=group.id,
                            user_id=owner.id,
                            role=GroupMemberRole.owner.value,
                            status=GroupMemberStatus.active.value
                        )
                        session.add(member)
                        lprint(f"添加群主: {owner.username} -> {group.name}")

                admins = group_data.get("admins", [])
                members = group_data.get("members", [])

                for admin_name in admins:
                    admin = await session.execute(
                        select(User).where(User.username == admin_name)
                    )
                    admin = admin.scalar_one_or_none()
                    if admin:
                        existing_member = await session.execute(
                            select(GroupMember).where(
                                GroupMember.group_id == group.id,
                                GroupMember.user_id == admin.id
                            )
                        )
                        if not existing_member.scalar_one_or_none():
                            member = GroupMember(
                                group_id=group.id,
                                user_id=admin.id,
                                role=GroupMemberRole.admin.value,
                                status=GroupMemberStatus.active.value
                            )
                            session.add(member)
                            lprint(f"添加管理员: {admin_name} -> {group.name}")
                    else:
                        lprint(f"找不到管理员 {admin_name}，跳过")

                for member_name in members:
                    member_user = await session.execute(
                        select(User).where(User.username == member_name)
                    )
                    member_user = member_user.scalar_one_or_none()
                    if member_user:
                        existing_member = await session.execute(
                            select(GroupMember).where(
                                GroupMember.group_id == group.id,
                                GroupMember.user_id == member_user.id
                            )
                        )
                        if not existing_member.scalar_one_or_none():
                            member = GroupMember(
                                group_id=group.id,
                                user_id=member_user.id,
                                role=GroupMemberRole.member.value,
                                status=GroupMemberStatus.active.value
                            )
                            session.add(member)
                            lprint(f"添加成员: {member_name} -> {group.name}")
                    else:
                        lprint(f"找不到成员 {member_name}，跳过")
            await session.commit()
            lprint("群成员数据加载完成")

        # 步骤3：加载设备数据
        devices_data = await load_json_file(data_dir / "devices.json")
        if devices_data:
            for device_data in devices_data:
                if not all(k in device_data for k in ("device_id", "device_name", "device_type", "username")):
                    lprint(f"设备数据缺少必要字段: {device_data}")
                    continue

                existing_device = await session.execute(
                    select(Device).where(Device.device_id == device_data["device_id"])
                )
                if existing_device.scalar_one_or_none():
                    lprint(f"设备已存在: {device_data['device_id']}, 跳过插入")
                    continue

                user = await session.execute(
                    select(User).where(User.username == device_data["username"])
                )
                user = user.scalar_one_or_none()
                if user is None:
                    lprint(f"找不到用户 {device_data['username']}，跳过设备 {device_data['device_id']}")
                    continue

                device_type = DeviceType[device_data["device_type"]].value if device_data["device_type"] in DeviceType.__members__ else DeviceType.other.value
                device = Device(
                    device_id=device_data["device_id"],
                    device_name=device_data["device_name"],
                    device_type=device_type,
                    status=DeviceStatus.offline.value,  # 默认状态
                    user_id=user.id,
                    ip_address=device_data.get("ip_address", ""),
                    user_agent=device_data.get("user_agent", "")
                )
                session.add(device)
                lprint(f"插入设备: {device_data['device_id']}")
            await session.commit()
            lprint("设备数据加载完成")

        # 步骤3：加载私聊消息数据
        messages_data = await load_json_file(data_dir / "messages.json")
        if messages_data and "private_messages" in messages_data:
            from app.domain.common.models.tables import PrivateMessage
            from app.domain.common.enums.message import MessageStatus, MessageContentType
            from app.domain.message.internal.repository.private import PrivateMessageRepository
            from app.domain.user.internal.repository import UserRepository
            
            private_repo = PrivateMessageRepository()
            user_repo = UserRepository()
            
            # 获取所有用户的映射
            users = await user_repo.get_all_users()
            username_to_id = {user.username: user.id for user in users}
            
            # 默认消息类型
            DEFAULT_CONTENT_TYPE = MessageContentType.plain_text.value
            DEFAULT_MESSAGE_TYPE = MessageType.chat.value
            DEFAULT_TARGET_TYPE = MessageTargetType.user.value

            for message_data in messages_data["private_messages"]:
                # 检查必要字段
                if not all(k in message_data for k in ("sender", "recipient", "content")):
                    lprint(f"消息数据缺少必要字段: {message_data}")
                    continue
                
                # 获取发送者和接收者的ID
                sender_id = username_to_id.get(message_data["sender"])
                recipient_id = username_to_id.get(message_data["recipient"])
                
                if not sender_id or not recipient_id:
                    lprint(f"找不到发送者或接收者: {message_data['sender']} -> {message_data['recipient']}")
                    continue

                # 获取消息状态列表
                status = []
                if "status" in message_data:
                    for status_name in message_data["status"]:
                        try:
                            status.append(MessageStatus[status_name.lower()].value)
                        except KeyError:
                            lprint(f"无效的消息状态: {status_name}")
                            continue
                if not status:
                    status = [MessageStatus.sent.value]  # 默认状态

                # 创建消息对象
                message = PrivateMessage(
                    sender_id=sender_id,
                    recipient_id=recipient_id,
                    content=message_data["content"],
                    content_type=DEFAULT_CONTENT_TYPE,
                    message_type=DEFAULT_MESSAGE_TYPE,
                    target_type=DEFAULT_TARGET_TYPE,
                    status=status,  # 直接使用status列表
                    created_at=datetime.now(ZoneInfo("Asia/Shanghai")),
                )

                # 保存消息
                try:
                    session.add(message)
                    lprint(f"成功插入私聊消息: {message_data['content'][:20]}...")
                except Exception as e:
                    lprint(f"插入私聊消息时出错: {str(e)}")
                    continue
            
            # 提交所有消息
            await session.commit()
            lprint("私聊消息数据加载完成")

        # 步骤4：加载群组消息数据
        messages_data = await load_json_file(data_dir / "messages.json")
        if messages_data and isinstance(messages_data, dict):
            from app.domain.common.models.tables import create_group_message_table
            from app.domain.common.enums.message import MessageStatus, MessageContentType
            from app.domain.message.internal.repository.group import GroupMessageRepository, TableNamingConfig
            from app.domain.group.internal.repository.group_repository import GroupRepository
            from app.domain.user.internal.repository.user_repository import UserRepository

            # 初始化仓储
            user_repo = UserRepository()
            group_repo = GroupRepository()
            table_config = TableNamingConfig()
            created_tables = {}
            
            # 获取所有用户的映射
            users = await user_repo.get_all_users()
            username_to_id = {}
            for user in users:
                if hasattr(user, 'username') and hasattr(user, 'id'):
                    username = str(getattr(user, 'username', ''))
                    user_id = int(getattr(user, 'id', 0))
                    if username and user_id:
                        username_to_id[username] = user_id

            # 获取所有群组的映射
            groups = await group_repo.get_all_records()
            group_name_to_id = {}
            for group in groups:
                if hasattr(group, 'name') and hasattr(group, 'id'):
                    group_name = str(getattr(group, 'name', ''))
                    group_id = int(getattr(group, 'id', 0))
                    if group_name and group_id:
                        group_name_to_id[group_name] = group_id

            # 默认消息类型
            DEFAULT_CONTENT_TYPE = MessageContentType.plain_text.value
            DEFAULT_MESSAGE_TYPE = MessageType.chat.value
            DEFAULT_TARGET_TYPE = MessageTargetType.group.value

            # 加载群组消息
            group_messages = messages_data.get("group_messages", []) if isinstance(messages_data, dict) else []
            for message_data in group_messages:
                # 检查必要字段
                if not all(k in message_data for k in ("sender", "group_name", "content")):
                    lprint(f"消息数据缺少必要字段: {message_data}")
                    continue

                # 获取发送者和群组的ID
                sender_name = str(message_data.get("sender", ""))
                group_name = str(message_data.get("group_name", ""))
                
                sender_id = username_to_id.get(sender_name)
                group_id = group_name_to_id.get(group_name)

                if not sender_id or not group_id:
                    lprint(f"找不到发送者或群组: {sender_name} -> {group_name}")
                    continue

                # 使用新的表命名策略
                created_at = datetime.now(ZoneInfo("Asia/Shanghai"))
                table_name = table_config.generate_table_name(group_id, created_at)
                
                if table_name not in created_tables:
                    # 创建新表，继承基础消息模型
                    GroupMessage = create_group_message_table(table_name)
                    # 确保表在数据库中创建
                    async with db_facade.engine.begin() as conn:
                        await conn.run_sync(GroupMessage.__table__.create)
                    created_tables[table_name] = GroupMessage
                    
                    # 更新群组的消息表名
                    group = await group_repo.get_by_id(group_id)
                    if group:
                        group.message_table_name = table_name
                        await session.commit()
                        
                    lprint(f"创建了新的消息表: {table_name}")
                else:
                    GroupMessage = created_tables[table_name]
                
                # 获取消息状态列表
                status = []
                if "status" in message_data:
                    for status_name in message_data["status"]:
                        try:
                            status.append(MessageStatus[status_name.lower()].value)
                        except KeyError:
                            lprint(f"无效的消息状态: {status_name}")
                            continue
                if not status:
                    status = [MessageStatus.sent.value]  # 默认状态

                # 创建消息对象
                message = GroupMessage(
                    sender_id=sender_id,
                    group_id=group_id,
                    content=message_data["content"],
                    content_type=DEFAULT_CONTENT_TYPE,
                    message_type=DEFAULT_MESSAGE_TYPE,
                    target_type=DEFAULT_TARGET_TYPE,
                    status=status,
                    created_at=created_at,
                )

                # 保存消息
                try:
                    session.add(message)
                    lprint(f"成功插入群组消息到表 {table_name}: {message_data['content'][:20]}...")
                except Exception as e:
                    lprint(f"插入群组消息时出错: {str(e)}")
                    continue

            # 提交所有消息
            await session.commit()
            lprint("群组消息数据加载完成")

        lprint("所有初始数据加载完成")
        return True

    except Exception as e:
        await session.rollback()
        print(traceback.format_exc())
        return False


async def init_db() -> bool:
    """初始化数据库
    1. 删除所有表
    2. 创建所有表
    3. 初始化基础数据
    """
    try:
        db_facade = DatabaseFacade()
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("环境变量 DATABASE_URL 未设置")
            return False

        await db_facade.init(database_url)
        print("数据库连接初始化完成")

        async with db_facade.engine.begin() as conn:
            if not await drop_all_tables(conn):
                print("删除表失败")
                return False

        if not await create_all_tables(db_facade):
            print("创建表失败")
            return False

        async with db_facade.engine.begin() as conn:
            if not await verify_database_tables(conn):
                print("表验证失败")
                return False

        if not await load_initial_data(db_facade):
            print("初始数据加载失败")
            return False

        print("数据库初始化完成")
        return True

    except Exception as e:
        print(f"数据库初始化失败: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    asyncio.run(init_db())
