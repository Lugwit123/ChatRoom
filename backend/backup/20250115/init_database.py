"""数据库初始化脚本"""
import os
import json
import asyncio
import sys
import traceback
import aiofiles
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional
from sqlalchemy.orm import exc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, inspect, Column, ARRAY, String, DateTime, create_engine, Integer, ForeignKey
from sqlalchemy import MetaData, Table
import Lugwit_Module as LM
from app.db.schemas import (
    User, Group, PrivateMessage, Device,
    get_group_message_table_name, create_group_message_table,
    UserRole, UserStatusEnum, user_group_link, MessageType,
    MessageContentType, MessageStatus, MessageTargetType,
    MessageTypeModel, MessageContentTypeModel,
    Base
)
from app.db.db_connection import engine, async_session
from app.utils.encoding_utils import setup_encoding, print_encoding_info
from app.core.logging_config import setup_logging
from passlib.context import CryptContext
from app.utils.security_utils import get_password_hash

lprint = LM.lprint

# 获取当前目录
curDir: str = os.path.dirname(os.path.abspath(__file__))

async def table_exists(session: AsyncSession, table_name: str) -> bool:
    """检查表是否存在"""
    try:
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = :table_name
            )
        """)
        result = await session.execute(query, {"table_name": table_name})
        exists = result.scalar()
        return exists
    except Exception as e:
        lprint(f"检查表是否存在出错: {traceback.format_exc()}")
        return False

async def load_initial_users(session: AsyncSession) -> Dict[str, int]:
    """从JSON文件加载初始用户数据"""
    lprint("开始加载初始用户数据...")
    
    # 用于存储用户名到ID的映射
    username_to_id = {}
    
    json_path = os.path.join(curDir, "data", "initial_users.json")
    if not os.path.exists(json_path):
        lprint(f"初始用户文件未找到: {json_path}")
        return username_to_id

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            users_data = json.load(f)

        current_time = datetime.now(ZoneInfo("Asia/Shanghai"))
        
        for user_data in users_data:
            # 检查用户是否已存在
            stmt = select(User).where(User.username == user_data["username"])
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                username_to_id[existing_user.username] = existing_user.id
                continue

            # 创建新用户
            hashed_password = get_password_hash(user_data["password"])
            new_user = User(
                username=user_data["username"],
                hashed_password=hashed_password,
                role=UserRole[user_data["role"]],
                nickname=user_data.get("nickname"),
                email=user_data.get("email"),
                status="normal",  # 直接使用字符串值
                created_at=current_time,
                updated_at=current_time
            )
            session.add(new_user)
            await session.flush()  # 刷新会话以获取新用户的ID
            
            username_to_id[new_user.username] = new_user.id
            lprint(f"用户 {new_user.username} 创建成功")

        await session.commit()
        lprint("初始用户数据加载完成")
        return username_to_id
    except Exception as e:
        lprint(f"加载初始用户数据失败: {traceback.format_exc()}")
        raise

async def load_initial_groups(session: AsyncSession, username_to_id: Dict[str, int]) -> None:
    """从JSON文件加载初始群组数据"""
    lprint("开始加载初始群组数据...")
    
    json_path = os.path.join(curDir, "data", "initial_groups.json")
    if not os.path.exists(json_path):
        lprint(f"初始群组文件未找到: {json_path}")
        return
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            groups_data = json.load(f)
        
        current_time = datetime.now(ZoneInfo("Asia/Shanghai"))
        
        for group_data in groups_data:
            # 检查群组是否已存在
            stmt = select(Group).where(Group.name == group_data["name"])
            result = await session.execute(stmt)
            existing_group = result.scalar_one_or_none()
            
            if existing_group:
                lprint(f"群组 {group_data['name']} 已存在")
                continue
            
            # 获取群主ID
            owner_id = username_to_id.get(group_data["owner"])
            if not owner_id:
                lprint(f"群主 {group_data['owner']} 不存在,跳过创建群组 {group_data['name']}")
                continue
            
            # 创建新群组
            new_group = Group(
                name=group_data["name"],
                description=group_data["description"],
                owner_id=owner_id,
                created_at=current_time,
                updated_at=current_time,
                avatar=group_data.get("avatar", ""),
                extra_data=group_data.get("extra_data", {})
            )
            session.add(new_group)
            await session.flush()
            
            # 添加群主和管理员到群组
            owner_link = {
                "user_id": owner_id,
                "group_id": new_group.id,
                "role": UserRole.admin
            }
            await session.execute(user_group_link.insert().values(**owner_link))
            
            # 添加管理员到群组
            for admin_name in group_data.get('admins', []):
                admin_id = username_to_id.get(admin_name)
                if admin_id:
                    admin_link = {
                        "user_id": admin_id,
                        "group_id": new_group.id,
                        "role": UserRole.admin
                    }
                    await session.execute(user_group_link.insert().values(**admin_link))
                else:
                    lprint(f"管理员 {admin_name} 不存在,跳过添加到群组 {new_group.name}")
            
            lprint(f"群组 {new_group.name} 创建成功")
        
        await session.commit()
        lprint("初始群组数据加载完成")
    except Exception as e:
        lprint(f"加载初始群组数据失败: {traceback.format_exc()}")
        raise

async def load_initial_messages(session: AsyncSession, username_to_id: Dict[str, int]) -> None:
    """加载初始消息数据"""
    lprint("开始加载初始消息...")
    
    json_path = os.path.join(curDir, "data", "initial_messages.json")
    if not os.path.exists(json_path):
        lprint(f"初始消息文件未找到: {json_path}")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            messages_data = json.load(f)

        # 获取消息类型ID
        stmt = select(MessageTypeModel).where(MessageTypeModel.type_code == MessageType.private_chat)
        result = await session.execute(stmt)
        message_type = result.scalar_one()
        
        # 获取消息内容类型ID
        stmt = select(MessageContentTypeModel).where(
            MessageContentTypeModel.type_code == MessageContentType.plain_text
        )
        result = await session.execute(stmt)
        content_type = result.scalar_one()

        current_time = datetime.now(ZoneInfo("Asia/Shanghai"))

        # 处理私聊消息
        for msg_data in messages_data.get("private_messages", []):
            sender_id = username_to_id.get(msg_data["sender"])
            recipient_id = username_to_id.get(msg_data["recipient"])
            
            if not sender_id or not recipient_id:
                lprint(f"找不到发送者或接收者ID: {msg_data['sender']} -> {msg_data['recipient']}")
                continue

            new_message = PrivateMessage(
                content=msg_data["content"],
                sender_id=sender_id,
                recipient_id=recipient_id,
                timestamp=current_time,
                message_type_id=message_type.id,
                message_content_type_id=content_type.id,
                status=[MessageStatus.sent],
                popup_message=False,
                extra_data=json.dumps({})  # 将字典转换为JSON字符串
            )
            session.add(new_message)

        await session.commit()
        lprint("初始消息加载成功")
    except Exception as e:
        lprint(f"加载初始消息失败: {traceback.format_exc()}")
        raise

async def load_initial_devices(session: AsyncSession, username_to_id: Dict[str, int]) -> None:
    """从 JSON 文件加载初始设备数据"""
    lprint("开始加载初始设备...")
    
    json_path = os.path.join(curDir, "data", "initial_devices.json")
    if not os.path.exists(json_path):
        lprint(f"初始设备文件未找到: {json_path}")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            devices_data = json.load(f)

        current_time = datetime.now(ZoneInfo("Asia/Shanghai"))

        for device_data in devices_data:
            user_id = username_to_id.get(device_data["username"])
            if not user_id:
                lprint(f"找不到用户ID: {device_data['username']}")
                continue

            new_device = Device(
                device_id=device_data["device_id"],
                user_id=user_id,
                device_name=device_data.get("device_name", ""),
                device_type=device_data.get("device_type", ""),
                login_status=device_data.get("login_status", False),
                ip_address=device_data.get("ip_address", ""),
                user_agent=device_data.get("user_agent", ""),
                first_login=current_time,
                last_seen=current_time,
                login_count=1
            )
            session.add(new_device)

        await session.commit()
        lprint("初始设备加载完成")
    except Exception as e:
        lprint(f"加载初始设备失败: {traceback.format_exc()}")
        raise

async def clear_database(session: AsyncSession) -> None:
    """清空数据库"""
    try:
        lprint("开始清空数据库")
        
        # 查询所有用户创建的表
        tables_query = """
            SELECT tablename 
            FROM pg_catalog.pg_tables
            WHERE schemaname = 'public'
        """
        
        result = await session.execute(text(tables_query))
        tables = result.scalars().all()
        
        # 删除每个表
        for table in tables:
            await session.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            
        await session.commit()
        lprint("数据库清空完成")
    except Exception as e:
        lprint(f"清空数据库时出错: {traceback.format_exc()}")
        raise

async def drop_enums(session: AsyncSession) -> None:
    """删除枚举类型"""
    try:
        lprint("开始删除枚举类型")
        
        # 查询所有用户定义的枚举类型
        enum_query = """
            SELECT t.typname
            FROM pg_type t
            JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
            WHERE t.typtype = 'e'  -- 'e' 表示枚举类型
            AND n.nspname = 'public'  -- 只查询public schema中的类型
        """
        
        result = await session.execute(text(enum_query))
        enum_types = result.scalars().all()
        
        # 删除每个枚举类型
        for enum_type in enum_types:
            await session.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE"))
            
        await session.commit()
        lprint("枚举类型删除完成")
    except Exception as e:
        lprint(f"删除枚举类型时出错: {traceback.format_exc()}")
        raise

async def create_enums(session: AsyncSession) -> None:
    """创建枚举类型"""
    lprint("开始创建枚举")

    # 创建消息类型枚举
    message_type_values = ", ".join(f"'{member.value}'" for member in MessageType)
    stmt = text(f"""
            CREATE TYPE messagetype AS ENUM (
                {message_type_values}
            )
        """)
    await session.execute(stmt)
    lprint(f"枚举 messagetype 创建成功")

    # 创建消息内容类型枚举
    message_content_type_values = ", ".join(f"'{member.value}'" for member in MessageContentType)
    stmt = text(f"""
            CREATE TYPE messagecontenttype AS ENUM (
                {message_content_type_values}
            )
        """)
    await session.execute(stmt)
    lprint(f"枚举 messagecontenttype 创建成功")

    # 创建用户状态枚举
    user_status_values = ", ".join(f"'{member.value}'" for member in UserStatusEnum)
    stmt = text(f"""
            CREATE TYPE userstatus AS ENUM (
                {user_status_values}
            )
        """)
    await session.execute(stmt)
    lprint(f"枚举 userstatus 创建成功")

    # 创建用户角色枚举
    user_role_values = ", ".join(f"'{member.value}'" for member in UserRole)
    stmt = text(f"""
            CREATE TYPE userrole AS ENUM (
                {user_role_values}
            )
        """)
    await session.execute(stmt)
    lprint(f"枚举 userrole 创建成功")

    # 创建消息状态枚举
    message_status_values = ", ".join(f"'{member.value}'" for member in MessageStatus)
    stmt = text(f"""
            CREATE TYPE messagestatus AS ENUM (
                {message_status_values}
            )
        """)
    await session.execute(stmt)
    lprint(f"枚举 messagestatus 创建成功")

    # 创建消息目标类型枚举
    message_target_type_values = ", ".join(f"'{member.value}'" for member in MessageTargetType)
    stmt = text(f"""
            CREATE TYPE messagetargettype AS ENUM (
                {message_target_type_values}
            )
        """)
    await session.execute(stmt)
    lprint(f"枚举 messagetargettype 创建成功")

    await session.commit()
    lprint("枚举创建完成")

async def create_tables():
    """创建所有表"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        lprint("创建表成功")
    except Exception as e:
        lprint(f"创建表失败: {traceback.format_exc()}")

async def create_base_tables():
    """创建基础表（不包括群组消息表）"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        lprint(f"创建基础表失败: {traceback.format_exc()}")

async def create_group_message_tables():
    """为所有群组创建消息表"""
    try:
        async with async_session() as session:
            result = await session.execute(select(Group))
            groups = result.scalars().all()
            for group in groups:
                table_name = get_group_message_table_name(group.id)
                await init_group_message_table(session, group.name, table_name)
    except Exception as e:
        lprint(f"创建群组消息表失败: {traceback.format_exc()}")

async def init_group_message_table(session: AsyncSession, group_name: str, table_name: str) -> None:
    """初始化群组消息表"""
    try:
        exists = await table_exists(session, table_name)
        if not exists:
            # 创建群组消息表
            await session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    content VARCHAR,
                    sender_id INTEGER REFERENCES users(id),
                    group_name VARCHAR REFERENCES groups(name),
                    timestamp TIMESTAMP WITH TIME ZONE,
                    message_type_id INTEGER REFERENCES message_types(id),
                    message_content_type_id INTEGER REFERENCES message_content_types(id),
                    status VARCHAR[],
                    popup_message INTEGER,
                    extra_data VARCHAR
                )
            """))
            await session.commit()
            lprint(f"成功创建表 {table_name}")

            # 获取消息类型ID
            message_type_result = await session.execute(
                text("SELECT id FROM message_types WHERE type_code = 'group_chat'")
            )
            message_type = message_type_result.scalar()

            # 获取消息内容类型ID
            content_type_result = await session.execute(
                text("SELECT id FROM message_content_types WHERE type_code = 'plain_text'")
            )
            content_type = content_type_result.scalar()

            # 插入初始消息
            current_time = datetime.now(timezone.utc)
            initial_messages = [
                {
                    'content': f'欢迎来到{group_name}群组！',
                    'sender_id': 1,  # admin用户
                    'group_name': group_name,
                    'timestamp': current_time,
                    'message_type_id': message_type,
                    'message_content_type_id': content_type,
                    'status': ['sent'],
                    'popup_message': False,
                    'extra_data': '{}'
                },
                {
                    'content': '大家好，我是管理员',
                    'sender_id': 1,
                    'group_name': group_name,
                    'timestamp': current_time,
                    'message_type_id': message_type,
                    'message_content_type_id': content_type,
                    'status': ['sent'],
                    'popup_message': False,
                    'extra_data': '{}'
                }
            ]

            # 使用原生SQL插入数据
            for msg in initial_messages:
                await session.execute(
                    text(f"""
                        INSERT INTO {table_name} (
                            content, sender_id, group_name, timestamp,
                            message_type_id, message_content_type_id,
                            status, popup_message, extra_data
                        ) VALUES (
                            :content, :sender_id, :group_name, :timestamp,
                            :message_type_id, :message_content_type_id,
                            :status, :popup_message, :extra_data
                        )
                    """),
                    {
                        'content': msg['content'],
                        'sender_id': msg['sender_id'],
                        'group_name': msg['group_name'],
                        'timestamp': msg['timestamp'],
                        'message_type_id': msg['message_type_id'],
                        'message_content_type_id': msg['message_content_type_id'],
                        'status': msg['status'],
                        'popup_message': msg['popup_message'],
                        'extra_data': msg['extra_data']
                    }
                )
            await session.commit()
            lprint(f"成功插入{table_name}初始消息")
    except Exception as e:
        lprint(f"创建群组消息表出错: {traceback.format_exc()}")
        raise

async def create_private_message(session: AsyncSession):
    """创建私聊消息表"""
    lprint("创建私聊消息表...")
    
    try:
        # 检查表是否已存在
        if await table_exists(session, "private_messages"):
            lprint("私聊消息表已存在")
            return
        
        # 创建私聊消息表
        stmt = text("""
            CREATE TABLE IF NOT EXISTS private_messages (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                sender VARCHAR(255) REFERENCES users(username),
                recipient_type VARCHAR(50) NOT NULL CHECK (recipient_type IN ('user', 'group')),
                recipient VARCHAR(255) REFERENCES users(username),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                message_type_id INTEGER REFERENCES message_types(id),
                message_content_type_id INTEGER REFERENCES message_content_types(id),
                status VARCHAR(50)[] DEFAULT ARRAY['sent'],
                popup_message BOOLEAN DEFAULT FALSE,
                extra_data JSONB DEFAULT '{}'::jsonb
            )
        """)
        await session.execute(stmt)
        await session.commit()
        lprint("私聊消息表创建成功")
    except Exception as e:
        lprint(f"创建私聊消息表失败: {traceback.format_exc()}")
        raise

async def get_or_create_message_type(session: AsyncSession, message_type: MessageType) -> MessageTypeModel:
    """获取或创建消息类型"""
    stmt = select(MessageTypeModel).where(MessageTypeModel.type_code == message_type.value)
    result = await session.execute(stmt)
    existing_type = result.scalar_one_or_none()
    
    if existing_type:
        return existing_type
    
    new_type = MessageTypeModel(type_code=message_type.value, description=message_type.value)
    session.add(new_type)
    await session.commit()
    return new_type

async def get_or_create_content_type(session: AsyncSession, content_type: MessageContentType) -> MessageContentTypeModel:
    """获取或创建消息内容类型"""
    stmt = select(MessageContentTypeModel).where(MessageContentTypeModel.type_code == content_type.value)
    result = await session.execute(stmt)
    existing_type = result.scalar_one_or_none()
    
    if existing_type:
        return existing_type
    
    new_type = MessageContentTypeModel(type_code=content_type.value, description=content_type.value)
    session.add(new_type)
    await session.commit()
    return new_type

async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    stmt = select(User).where(User.username == username)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_message_types(session: AsyncSession) -> None:
    """创建消息类型数据"""
    lprint("开始创建消息类型...")
    
    try:
        for msg_type in MessageType:
            # 检查消息类型是否已存在
            stmt = select(MessageTypeModel).where(
                MessageTypeModel.type_code == msg_type.value
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                message_type = MessageTypeModel(
                    type_code=msg_type.value,
                    description=msg_type.name  # 使用枚举名称作为描述
                )
                session.add(message_type)
                lprint(f"创建消息类型: {msg_type.name}")

        await session.commit()
        lprint("消息类型创建完成")
    except Exception as e:
        lprint(f"创建消息类型失败: {traceback.format_exc()}")
        raise

async def create_message_content_types(session: AsyncSession) -> None:
    """创建消息内容类型数据"""
    lprint("开始创建消息内容类型...")
    
    try:
        for content_type in MessageContentType:
            # 检查内容类型是否已存在
            stmt = select(MessageContentTypeModel).where(
                MessageContentTypeModel.type_code == content_type.value
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                content_type_model = MessageContentTypeModel(
                    type_code=content_type.value,
                    description=content_type.name  # 使用枚举名称作为描述
                )
                session.add(content_type_model)
                lprint(f"创建消息内容类型: {content_type.name}")

        await session.commit()
        lprint("消息内容类型创建完成")
    except Exception as e:
        lprint(f"创建消息内容类型失败: {traceback.format_exc()}")
        raise


async def init_database():
    """初始化数据库"""
    try:
        setup_logging()
        setup_encoding()
        print_encoding_info()

        async with async_session() as session:
            # 清空数据库
            await clear_database(session)
            lprint("数据库已清空")

            # 删除并重建枚举类型
            await drop_enums(session)
            await create_enums(session)
            lprint("枚举类型已重建")

            # 创建基础表
            await create_base_tables()
            lprint("基础表已创建")

            # 创建消息类型和内容类型
            await create_message_types(session)
            await create_message_content_types(session)
            lprint("消息类型和内容类型已创建")

            # 加载初始数据
            username_to_id = await load_initial_users(session)
            await load_initial_groups(session, username_to_id)
            await load_initial_devices(session, username_to_id)
            await load_initial_messages(session, username_to_id)
            lprint("初始数据已加载")

            # 为所有群组创建消息表
            await create_group_message_tables()
            lprint("群组消息表已创建")

            await session.commit()
            lprint("数据库初始化完成")

    except Exception as e:
        lprint(f"数据库初始化失败: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    asyncio.run(init_database())
