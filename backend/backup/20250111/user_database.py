# backend/user_database.py

import asyncio
import logging
import os
import re
import json
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone, timedelta
import aiofiles
from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, selectinload, Session
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSON
import logging
import Lugwit_Module as LM
lprint=LM.lprint

import schemas

# 用户查询缓存
user_query_cache = {}



# 密码哈希配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 数据库连接字符串（生产环境中请确保安全）
DATABASE_URL = "postgresql+asyncpg://postgres:OC.123456@localhost:5432/chatroom"

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 生产环境中设为 False
    future=True,
    pool_size=20,       # 增加连接池大小
    max_overflow=30,    # 增加最大溢出连接数
    pool_timeout=60,    # 增加超时时间
    pool_pre_ping=True, # 添加连接检查
    pool_recycle=3600   # 每小时回收连接
)

# 创建异步会话工厂
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# 创建一个消息ID更新队列
message_update_queue = asyncio.Queue()

# 基础模型类
Base = declarative_base()

# 关联表：用户和群组之间的多对多关系
user_group_association = sa.Table(
    'user_group_association',
    Base.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True),
    sa.Column('group_id', sa.Integer, sa.ForeignKey('groups.id'), primary_key=True)
)

# ============================
# 数据库模型
# ============================

class MessageType(Base):
    __tablename__ = "message_type"

    id = sa.Column(sa.Integer, primary_key=True, index=True, autoincrement=True)
    type_code = sa.Column(SAEnum(schemas.MessageType, name="message_type_enum"), unique=True, nullable=False)
    description = sa.Column(sa.String(255))  # 类型描述
    is_active = sa.Column(sa.Boolean, default=True)  # 是否启用


class MessageContentType(Base):
    __tablename__ = "message_content_type"

    id = sa.Column(sa.Integer, primary_key=True, index=True, autoincrement=True)
    type_code = sa.Column(SAEnum(schemas.MessageContentType, name="message_content_type_enum"), unique=True, nullable=False)
    description = sa.Column(sa.String(255))  # 类型描述
    is_active = sa.Column(sa.Boolean, default=True)  # 是否启用


class Message(Base):
    __tablename__ = "message"

    id = sa.Column(sa.Integer, primary_key=True, index=True, autoincrement=True)
    sender = sa.Column(sa.String(50), sa.ForeignKey("users.username"), nullable=False)
    recipient = sa.Column(sa.String(50), sa.ForeignKey("users.username"), nullable=False)
    content = sa.Column(sa.Text, nullable=False)
    timestamp = sa.Column(sa.DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    recipient_type = sa.Column(sa.String(50), default="")
    popup_message = sa.Column(sa.Boolean, nullable=False, default=False)
    status = sa.Column(postgresql.ARRAY(sa.String), nullable=False, default=["unread"])
    message_type_id = sa.Column(sa.Integer, sa.ForeignKey("message_type.id"), nullable=False)
    message_content_type_id = sa.Column(sa.Integer, sa.ForeignKey("message_content_type.id"), nullable=False)

    # 关系
    sender_user = relationship("UserResponse", back_populates="sent_messages", foreign_keys=[sender])
    recipient = relationship("UserResponse", back_populates="received_messages", foreign_keys=[recipient])
    message_type = relationship("MessageType")
    message_content_type = relationship("MessageContentType")


class Group(Base):
    __tablename__ = "groups"

    id = sa.Column(sa.Integer, primary_key=True, index=True, autoincrement=True)
    name = sa.Column(sa.String(50), unique=True, nullable=False)

    users = relationship(
        "UserResponse",
        secondary=user_group_association,
        back_populates="groups",
        lazy="selectin"
    )


class UserResponse(Base):
    """用户数据库模型"""
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True, index=True, autoincrement=True)
    username = sa.Column(sa.String(50), unique=True, nullable=False, index=True)
    nickname = sa.Column(sa.String(100), nullable=False)
    hashed_password = sa.Column(sa.String(255), nullable=False)
    email = sa.Column(sa.String(255), unique=True, nullable=False, index=True)
    is_temporary = sa.Column(sa.Boolean, default=False)
    online = sa.Column(sa.Boolean, default=False)
    avatar_index = sa.Column(sa.Integer, default=0)
    role = sa.Column(SAEnum(schemas.UserRole, name="user_role_enum"), default=schemas.UserRole.user, nullable=False)
    message_ids = sa.Column(postgresql.ARRAY(sa.Integer), default=[], nullable=False)
    
    groups = relationship(
        "Group",
        secondary=user_group_association,
        back_populates="users",
        lazy="selectin"
    )
    
    sent_messages = relationship(
        "Message", 
        back_populates="sender_user", 
        foreign_keys=[Message.sender],
        lazy="selectin"
    )
    
    received_messages = relationship(
        "Message", 
        back_populates="recipient", 
        foreign_keys=[Message.recipient],
        lazy="selectin"
    )

    async def get_recent_message_ids(self, session: AsyncSession) -> List[int]:
        """获取最近的消息ID列表"""
        query = sa.select(Message.id).where(
            sa.or_(
                Message.sender == self.username,
                Message.recipient == self.username
            )
        ).order_by(Message.timestamp.desc()).limit(20)
        
        result = await session.execute(query)
        return result.scalars().all()

    async def get_all_message_ids(self, session: AsyncSession) -> List[int]:
        """获取所有消息ID列表"""
        query = sa.select(Message.id).where(
            sa.or_(
                Message.sender == self.username,
                Message.recipient == self.username
            )
        ).order_by(Message.timestamp.desc())
        
        result = await session.execute(query)
        return result.scalars().all()

    def safe_id(self):
        """安全地获取用户ID"""
        return get_column_value(self.id)

    def safe_username(self):
        """安全地获取用户名"""
        return get_column_value(self.username)


# ============================
# 初始化函数
# ============================

async def init_message_types() -> None:
    """初始化消息类型和内容类型"""
    async with async_session() as session:
        async with session.begin():
            existing_types = await session.execute(sa.select(MessageType))
            if existing_types.scalars().first():
                logging.info("消息类型和内容类型已初始化，跳过初始化。")
                return

            message_types = [
                MessageType(
                    type_code=type_code,
                    description=type_code.value  
                )
                for type_code in schemas.MessageType
            ]
            session.add_all(message_types)

            content_types = [
                MessageContentType(
                    type_code=type_code,
                    description=type_code.value  
                )
                for type_code in schemas.MessageContentType
            ]
            session.add_all(content_types)
        await session.commit()
        logging.info("初始化消息类型和内容类型完成。")


async def get_message_type_id(type_code: str) -> int:
    """根据 type_code 获取消息类型的 ID"""
    async with async_session() as session:
        stmt = sa.select(MessageType.id).where(MessageType.type_code == type_code)
        result = await session.execute(stmt)
        message_type_id = result.scalar_one_or_none()
        if message_type_id is None:
            raise ValueError(f"MessageType 类型代码 '{type_code}' 不存在。")
        return message_type_id


async def get_content_type_id(type_code: str) -> int:
    """根据 type_code 获取消息内容类型的 ID"""
    async with async_session() as session:
        stmt = sa.select(MessageContentType.id).where(MessageContentType.type_code == type_code)
        result = await session.execute(stmt)
        content_type_id = result.scalar_one_or_none()
        if content_type_id is None:
            raise ValueError(f"MessageContentType 类型代码 '{type_code}' 不存在。")
        return content_type_id


# ============================
# 核心函数
# ============================

async def create_tables(drop_existing: bool = False) -> None:
    """创建所有数据库表。可选择是否先删除现有表。"""
    async with engine.begin() as conn:
        if drop_existing:
            await conn.run_sync(Base.metadata.drop_all)
            logging.info("所有表已被删除。")
        await conn.run_sync(Base.metadata.create_all)
        logging.info("所有表已创建或已存在。")


def validate_username(username: str) -> bool:
    """确保用户名仅包含字母数字字符和下划线"""
    return re.match(r"^[A-Za-z0-9_]+$", username, flags=re.I) is not None


def validate_nickname(nickname: str) -> bool:
    """简单验证昵称是否包含中文字符"""
    return re.search(r"[\u4e00-\u9fff]", nickname) is not None


async def insert_group(group_data: dict) -> None:
    """插入一个新的群组到数据库"""
    async with async_session() as session:
        async with session.begin():
            group = Group(
                name=group_data['name']
            )
            session.add(group)
        try:
            await session.commit()
            logging.info(f"群组添加: {group_data['name']}")
        except IntegrityError:
            await session.rollback()
            logging.warning(f"群组 '{group_data['name']}' 已存在。")


async def get_group_by_name(name: str, session: AsyncSession) -> Optional[Group]:
    """根据群组名称获取群组对象"""
    stmt = sa.select(Group).where(Group.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def insert_user(
    username: str,
    nickname: str,
    password: str,
    email: str,
    role: schemas.UserRole,
    group_names: List[str],
    is_temporary: bool = False,
    online: bool = False
) -> None:
    if not validate_username(username):
        raise ValueError("用户名必须仅包含字母数字字符和下划线")
    if not validate_nickname(nickname):
        raise ValueError("昵称必须包含至少一个中文字符")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise ValueError("无效的电子邮箱格式")
    if role not in schemas.UserRole:
        raise ValueError("无效的用户角色")

    hashed_password = pwd_context.hash(password)

    async with async_session() as session:
        async with session.begin():
            groups: List[Group] = []
            for group_name in group_names:
                group = await get_group_by_name(group_name, session)
                if not group:
                    raise ValueError(f"群组 '{group_name}' 不存在")
                groups.append(group)

            new_user = UserResponse(
                username=username,
                nickname=nickname,
                hashed_password=hashed_password,
                email=email,
                is_temporary=is_temporary,
                online=online,
                role=role,
                groups=groups,
            )
            session.add(new_user)
            try:
                await session.commit()
                logging.info(f"用户已添加: {username}")
            except IntegrityError as e:
                await session.rollback()
                error_message: str = str(e)
                if 'duplicate key value violates unique constraint "users_username_key"' in error_message:
                    raise ValueError("用户名已存在")
                elif 'duplicate key value violates unique constraint "users_email_key"' in error_message:
                    raise ValueError("电��邮箱已存在")
                else:
                    raise ValueError("数据库错误")


async def fetch_user(identifier: Union[str, int]) -> Optional[schemas.UserBase]:
    """
    根据用户名或用户ID从数据库中获取用户信息。

    参数:
    - identifier (Union[str, int]): 用户名（str）或用户ID（int）。

    返回:
    - Optional[schemas.UserBase]: 如果找到用户则返回用户信息，否则返回 None。
    """
    cache_key = f"id:{identifier}" if isinstance(identifier, int) else f"username:{identifier}"

    cached_result = user_query_cache.get(cache_key)
    if cached_result:
        if cached_result["timestamp"] > datetime.now().timestamp() - 300:  
            return cached_result["user"]

    async with async_session() as session:
        try:
            if isinstance(identifier, int):
                stmt = sa.select(UserResponse).where(UserResponse.id == identifier)
            else:
                stmt = sa.select(UserResponse).where(UserResponse.username == identifier)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                user_data = schemas.UserBase.from_orm(user)
                user_query_cache[cache_key] = {
                    "user": user_data,
                    "timestamp": datetime.now().timestamp()
                }

                if isinstance(identifier, int):
                    username_key = f"username:{user.username}"
                    user_query_cache[username_key] = {
                        "user": user_data,
                        "timestamp": datetime.now().timestamp()
                    }
                else:
                    id_key = f"id:{user.id}"
                    user_query_cache[id_key] = {
                        "user": user_data,
                        "timestamp": datetime.now().timestamp()
                    }

                return user_data
            return None

        except Exception as e:
            logging.error(f"获取用户信息失败: {e}")
            logging.error(traceback.format_exc())
            return None


async def background_message_ids_updater():
    """后台任务：处理消息ID更新队列"""
    logging.info("启动后台消息ID更新任务")
    try:
        while True:
            try:
                update_data = await asyncio.wait_for(message_update_queue.get(), timeout=5.0)
                try:
                    await update_all_message_ids(update_data)

                except Exception as e:
                    logging.error(f"处理消息ID更新时出错: {e}")
                    logging.error(traceback.format_exc())
                finally:
                    message_update_queue.task_done()

            except Exception as e:
                logging.error(f"消息ID更新队列处理器出错: {e}")
                logging.error(traceback.format_exc())
                await asyncio.sleep(1)
    except asyncio.CancelledError:
        logging.info("后台消息ID更新任务被取消")
        raise
    except Exception as e:
        logging.error(f"后台消息ID更新任务异常退出: {e}")
        logging.error(traceback.format_exc())
        raise


async def update_user_message_ids(username: str, message_id: int, session: AsyncSession) -> None:
    """更新用户的最近消息ID列表，并将全部消息ID的更新加入队列"""
    stmt = sa.select(UserResponse).where(UserResponse.username == username)
    result = await session.execute(stmt)
    sender = result.scalar_one_or_none()

    if sender:
        msg_stmt = sa.select(Message).where(Message.id == message_id)
        msg_result = await session.execute(msg_stmt)
        message = msg_result.scalar_one_or_none()

        if message:
            recipient_stmt = sa.select(UserResponse.id).where(UserResponse.username == message.recipient)
            recipient_result = await session.execute(recipient_stmt)
            recipient_id = recipient_result.scalar_one_or_none()

            update_data = schemas.UserMessageIDDataUpdate(
                sender_id=sender.id,
                id=message_id,
                recipient_id=recipient_id
            )
            await update_message_ids(update_data)
            await message_update_queue.put(update_data)


async def insert_message(
        message: schemas.MessageBase
) -> schemas.MessageBase:
    """插入一条新消息到数据库并更新用户的消息ID列表"""
    async with async_session() as session:
        async with session.begin():
            message_type_id = await get_message_type_id(str(message.message_type.value))
            content_type_id = await get_content_type_id(message.message_content_type.value)

            content_str = str(message.content)

            sender_stmt = sa.select(UserResponse).where(UserResponse.username == message.sender)
            sender_result = await session.execute(sender_stmt)
            sender_user = sender_result.scalar_one_or_none()

            recipient = None
            if message.recipient_type == 'private':
                recipient_stmt = sa.select(UserResponse).where(UserResponse.username == message.recipient)
                recipient_result = await session.execute(recipient_stmt)
                recipient = recipient_result.scalar_one_or_none()

            new_message = Message(
                sender=message.sender,
                recipient=message.recipient,
                content=content_str,
                timestamp=message.timestamp,
                recipient_type=message.recipient_type,
                message_type_id=message_type_id,
                message_content_type_id=content_type_id,
                popup_message=message.popup_message,
            )
            session.add(new_message)
            await session.flush()  

            sender_user.sent_messages.append(new_message)

            if message.recipient_type == 'private' and recipient:
                recipient.received_messages.append(new_message)

            elif message.recipient_type == 'group':
                group_members_stmt = (
                    sa.select(UserResponse)
                    .join(user_group_association)
                    .join(Group)
                    .where(Group.name == message.recipient)
                )
                result = await session.execute(group_members_stmt)
                group_members = result.scalars().all()
                
                for member in group_members:
                    if member.username != message.sender:  
                        member.received_messages.append(new_message)

            message_response = message
            message_response.id = new_message.id
            
            update_data = schemas.UserMessageIDDataUpdate(
                sender_id=sender_user.id,
                id=message_response.id,
                recipient_id=recipient.id if recipient else None
            )
            await update_message_ids(update_data)
            await message_update_queue.put(update_data)
            
            return message_response


async def fetch_all_users() -> List[schemas.UserBase]:
    """从数据库中获取所有用户"""
    async with async_session() as session:
        stmt = sa.select(UserResponse).options(selectinload(UserResponse.groups))
        result = await session.execute(stmt)
        users: List[UserResponse] = result.scalars().all()
        return [
            schemas.UserBase(
                username=user.username,
                nickname=user.nickname,
                email=user.email,
                groups=[schemas.GroupInDatabase(id=grp.id, name=grp.name) for grp in user.groups],
                role=user.role
            )
            for user in users
        ]


async def fetch_registered_users(
    current_username: str,
    exclude_types: List[schemas.UserRole] = [schemas.UserRole.system],
    include_unread_count: bool = True
) -> List[schemas.UserBaseAndStatus]:
    """获取所有已注册（非临时）的用户，排除特定角色，并可选择是否包含未读消息数"""
    async with async_session() as session:
        stmt: sa.Select = sa.select(UserResponse).where(UserResponse.is_temporary == False).options(selectinload(UserResponse.groups))
        result = await session.execute(stmt)

        users: List[UserResponse] = result.scalars().all()
        user_details: List[schemas.UserBaseAndStatus] = []
        for user in users:
            if exclude_types and user.role in exclude_types:
                continue
            user_detail = schemas.UserBaseAndStatus.from_orm(user)
            if include_unread_count:
                unread_message_count = await fetch_unread_count(current_username, user.username)
                user_detail.unread_message_count = unread_message_count
            user_detail.online = user.online
            user_details.append(user_detail)
    return user_details


async def verify_user(username: str, password: str) -> bool:
    """验证用户凭证"""
    user: Optional[schemas.UserBase] = await fetch_user(username)
    if user and pwd_context.verify(password, user.hashed_password):
        if user.role == schemas.UserRole.system:
            admin_check: bool = await is_user_admin(username)
            if not admin_check:
                return False
        return True
    return False


async def is_user_admin(username: str) -> bool:
    """检查用户是否具有管理员角色"""
    async with async_session() as session:
        stmt = sa.select(UserResponse.role).where(UserResponse.username == username)
        result = await session.execute(stmt)
        role: Optional[schemas.UserRole] = result.scalar_one_or_none()
        return role == schemas.UserRole.admin


async def get_user_by_id(user_id: int, db: Session) -> Optional[schemas.UserBase]:
    """根据用户 ID 获取用户信息"""
    try:
        stmt = sa.select(UserResponse).where(UserResponse.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            return schemas.UserBase(
                id=user.id,
                username=user.username,
                nickname=user.nickname,
                email=user.email,
                role=user.role,
                avatar_index=user.avatar_index
            )
        return None
    except Exception as e:
        logging.error(f"获取用户 ID {user_id} 时出错: {e}")
        logging.error(traceback.format_exc())
        return None


async def fetch_messages(sender: str, 
                        recipient: str,
                        number_of_messages: int = 20) -> List[schemas.MessageBase]:
    """获取私聊消息"""
    async with async_session() as session:
        user_stmt = sa.select(UserResponse).where(UserResponse.username == sender)
        result = await session.execute(user_stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return []
        
        # 使用SQL查询获取相关消息
        stmt = (
            sa.select(Message)
            .where(
                sa.or_(
                    sa.and_(
                        Message.sender == sender,
                        Message.recipient == recipient
                    ),
                    sa.and_(
                        Message.sender == recipient,
                        Message.recipient == sender
                    )
                )
            )
            .order_by(Message.id.asc())
            .limit(number_of_messages)
        ).options(
            selectinload(Message.message_type),
            selectinload(Message.message_content_type)
        )
        
        result = await session.execute(stmt)
        messages = result.scalars().all()
        
        return [
            schemas.MessageBase(
                id=msg.id,
                sender=msg.sender,
                recipient=msg.recipient,
                content=msg.content,
                timestamp=msg.timestamp,
                recipient_type=msg.recipient_type,
                status=msg.status,
                message_type=schemas.MessageType(msg.message_type.type_code),
                message_content_type=schemas.MessageContentType(msg.message_content_type.type_code),
                popup_message=msg.popup_message,
                direction=schemas.MessageDirection.RESPONSE
            )
            for msg in messages
        ]


async def fetch_group_messages(group: str) -> List[schemas.MessageBase]:
    """获取指定群组的消息,使用群组成员的message_ids来获取最近消息"""
    async with async_session() as session:
        stmt = (
            sa.select(UserResponse.message_ids)
            .join(user_group_association)
            .join(Group)
            .where(Group.name == group)
        )
        result = await session.execute(stmt)
        users_message_ids = result.fetchall()

        message_ids = set()
        for user_message_ids in users_message_ids:
            if user_message_ids[0]:  
                message_ids.update(user_message_ids[0])

        if not message_ids:
            return []

        stmt = sa.select(Message).where(
            sa.and_(
                Message.id.in_(list(message_ids)),
                Message.recipient == group,
                Message.recipient_type == 'group'
            )
        ).order_by(Message.timestamp)

        result = await session.execute(stmt)
        messages = result.scalars().all()

        return [
            schemas.MessageBase(
                sender=msg.sender,
                recipient=msg.recipient,
                content=msg.content,
                timestamp=msg.timestamp,
                recipient_type=msg.recipient_type,
                status=msg.status,  
                message_type=schemas.MessageType(msg.message_type.type_code),  
                message_content_type=schemas.MessageContentType(msg.message_content_type.type_code),  
                popup_message=msg.popup_message,
                direction=schemas.MessageDirection.RESPONSE,  
            )
            for msg in messages
        ]


async def get_chat_history(username: str, 
                           current_user: schemas.UserBase,
                           number_of_messages: int = 100) -> List[schemas.MessageBase]:
    """获取与指定用户或群组的聊天历史记录"""
    if not current_user:
        raise ValueError("当前用户未找到。")

    recipient_info = await fetch_user_or_group(username)
    if not recipient_info:
        raise ValueError("聊天对象未找到。")

    recipient_type = 'group' if recipient_info.get("is_group") else 'private'
    recipient_type = 'private'
    
    if recipient_type == 'group':
        if username not in [grp.name for grp in current_user.groups]:
            raise PermissionError("无权限访问此群组。")
        messages = await fetch_group_messages(username)
    else:
        messages = await fetch_messages(
            sender=current_user.username,
            recipient=username,
            number_of_messages=number_of_messages
        )
    
    return messages


async def set_user_online_status(username: str, online: bool) -> None:
    """更新用户的在线状态"""
    async with async_session() as session:
        async with session.begin():
            stmt = sa.select(UserResponse).where(UserResponse.username == username)
            result = await session.execute(stmt)
            user: Optional[UserResponse] = result.scalar_one_or_none()
            if user:
                user.online = online
            else:
                logging.warning(f"尝试更新不存在的用户 '{username}' 的在线状态。")
        await session.commit()
        logging.info(f"用户 '{username}' 的在线状态已更新为 {'在线' if online else '离线'}。")


async def get_all_groups_info() -> List[schemas.GroupResponse]:
    """获取所有群组的详细信息"""
    async with async_session() as session:
        stmt = (
            sa.select(Group)
            .options(selectinload(Group.users))
        )
        result = await session.execute(stmt)
        groups = result.scalars().all()
        return [schemas.GroupResponse.model_validate(group) for group in groups]


async def delete_user(username: str) -> None:
    """从数据库中删除指定用户"""
    async with async_session() as session:
        async with session.begin():
            stmt = sa.select(UserResponse).where(UserResponse.username == username)
            result = await session.execute(stmt)
            user: Optional[UserResponse] = result.scalar_one_or_none()
            if not user:
                logging.warning(f"尝试删除不存在的用户 '{username}'。")
                raise ValueError(f"用户 '{username}' 不存在")
            await session.delete(user)
        await session.commit()
        logging.info(f"用户 '{username}' 已被删除")


async def load_initial_users(json_path: str) -> None:
    """从 JSON 文件加载初始用户和群组数据"""
    if not os.path.exists(json_path):
        logging.warning(f"初始用户文件未找到: {json_path}")
        return

    async with aiofiles.open(json_path, 'r', encoding='utf-8') as f:
        content = await f.read()
        data = json.loads(content)

    groups = data.get("groups", [])
    for group in groups:
        try:
            await insert_group({"name": group["name"]})
            logging.info(f"已添加群组: {group['name']}")
        except Exception as e:
            logging.error(f"添加群组 '{group.get('name', '未知')}' 失败: {e}")

    users = data.get("users", [])

    for user_data in users:
        try:
            user_create = schemas.UserCreate(**user_data)

            await insert_user(
                username=user_create.username,
                nickname=user_create.nickname,
                password=user_create.password,
                email=user_create.email,
                role=user_create.role,
                group_names=user_create.groups,
                is_temporary=user_create.is_temporary,
                online=user_create.online  
            )
            logging.info(f"已添加用户: {user_create.username}")
        except Exception as e:
            logging.error(f"添加用户 '{user_data.get('username', '未知')}' 失败: {e}")
            traceback.print_exc()


async def load_initial_messages(json_path: str) -> None:
    """从 JSON 文件加载初始消息"""
    if not os.path.exists(json_path):
        logging.warning(f"初始消息文件未找到: {json_path}")
        return

    async with aiofiles.open(json_path, 'r', encoding='utf-8') as f:
        content = await f.read()
        data = json.loads(content)

    try:
        required_users = set()
        for msg in data.get("private_messages", []):
            required_users.add(msg["sender"])
            required_users.add(msg["recipient"])

        missing_users = []
        for username in required_users:
            user = await fetch_user(username)
            if not user:
                logging.error(f"用户 '{username}' 不存在，跳过相关消息")
                missing_users.append(username)

        for msg_data in data.get("private_messages", []):
            if msg_data["sender"] in missing_users or msg_data["recipient"] in missing_users:
                logging.warning(f"跳过消息: {msg_data['content']} 因为发送者或接收者不存在")
                continue
            try:
                message_create = schemas.MessageCreate(**msg_data)

                if not message_create.timestamp:
                    message_create.timestamp = datetime.utcnow()

                direction = schemas.MessageDirection.RESPONSE  

                message = schemas.MessageBase(
                    sender=message_create.sender,
                    recipient=message_create.recipient,
                    content=message_create.content,
                    timestamp=message_create.timestamp,
                    recipient_type="private",
                    status=["unread"],  
                    message_type=schemas.MessageType.PRIVATE_CHAT,
                    message_content_type=schemas.MessageContentType.HTML,
                    popup_message=message_create.popup_message,
                    direction=direction
                )

                await insert_message(message)
                if message and message.id:
                    async with async_session() as session:
                        sender = await session.get(UserResponse, message.sender)
                        recipient = await session.get(UserResponse, message.recipient)
                        
                        if sender:
                            sender.sent_messages.append(message)
                            
                        if recipient:
                            recipient.received_messages.append(message)
                            
                        await session.commit()
                
                logging.info(f"已添加消息: 从 {message.sender} 到 {message.recipient}")
            except Exception as e:
                logging.error(f"添加消息失败: {e}")
                logging.error(traceback.format_exc())
                continue

        logging.info("初始消息加载完成")
    except Exception as e:
        logging.error(f"加载初始消息时出错: {e}")
        logging.error(traceback.format_exc())


async def update_messages_status(sender: str, recipient: str, new_status: List[str]) -> None:
    """更新发送者和接收者之间消息的状态"""
    async with async_session() as session:
        async with session.begin():
            stmt = (
                sa.update(Message)
                .where(
                    sa.and_(
                        Message.sender == sender,
                        Message.recipient == recipient,
                        sa.func.array_overlap(Message.status, ['unread'])  
                    )
                )
                .values(status=new_status)
            )
            await session.execute(stmt)
        await session.commit()
        logging.info(f"更新消息状态: 从 '{sender}' 到 '{recipient}' 的消息状态已更新为 '{new_status}'。")


async def update_group_messages_status(group: str, new_status: List[str]) -> None:
    """更新指定群组中所有未读消息的状态"""
    async with async_session() as session:
        async with session.begin():
            stmt = sa.text("""
                UPDATE message
                SET status = :new_status
                WHERE recipient = :group
                  AND recipient_type = 'group'
                  AND :status = ANY(status)
            """)
            await session.execute(
                stmt,
                {
                    'new_status': new_status,
                    'group': group,
                    'status': 'unread'
                }
            )
        await session.commit()
        logging.info(f"更新群组消息状态: 群组 '{group}' 中的所有未读消息状态已更新为 '{new_status}'。")


async def fetch_unread_count(current_username: str, other_username: str) -> int:
    """获取来自 other_username 到 current_username 的未读消息数量"""
    async with async_session() as session:
        stmt = sa.text("""
            SELECT COUNT(*) FROM message
            WHERE recipient = :current_username
              AND sender = :other_username
              AND 'unread' = ANY(status)
        """)
        result = await session.execute(
            stmt,
            {
                'current_username': current_username,
                'other_username': other_username
            }
        )
        count = result.scalar()
        return count if count else 0


async def fetch_user_or_group(identifier: str) -> Optional[Dict[str, Any]]:
    """根据标识符获取用户或群组的信息"""
    async with async_session() as session:
        stmt_user = sa.select(UserResponse).where(UserResponse.username == identifier)
        result_user = await session.execute(stmt_user)
        user: Optional[UserResponse] = result_user.scalar_one_or_none()

        if user:
            return {
                "is_group": False,
                "username": user.username,
                "nickname": user.nickname,
                "role": user.role,
                "email": user.email,
                "groups": [group.name for group in user.groups],
                "online": user.online,
                "avatar_index": user.avatar_index
            }

        stmt_group = sa.select(Group).where(Group.name == identifier)
        result_group = await session.execute(stmt_group)
        group: Optional[Group] = result_group.scalar_one_or_none()

        if group:
            return {
                "is_group": True,
                "name": group.name,
                "users": [user.username for user in group.users]
            }

        return None


async def get_all_groups_response() -> List[schemas.GroupResponse]:
    """获取所有群组及其成员的响应模型列表"""
    async with async_session() as session:
        stmt = sa.select(Group).options(selectinload(Group.users))
        result = await session.execute(stmt)
        groups = result.scalars().all()
        return [
            schemas.GroupResponse(
                id=group.id,
                name=group.name,
                members=[
                    schemas.UserBase(
                        username=user.username,
                        nickname=user.nickname,
                        email=user.email,
                        groups=[schemas.GroupInDatabase(id=grp.id, name=grp.name) for grp in user.groups],
                        role=user.role
                    )
                    for user in group.users
                ]
            )
            for group in groups
        ]


async def get_group_members(group_id: int) -> Optional[List[schemas.UserBase]]:
    """根据群组 ID 获取群组的所有成员"""
    async with async_session() as session:
        group = await session.get(Group, group_id)
        if not group:
            logging.warning(f"群组 ID '{group_id}' 不存在。")
            return None

        stmt = sa.select(UserResponse).join(user_group_association).where(user_group_association.c.group_id == group_id)
        result = await session.execute(stmt)
        users = result.scalars().all()
        return [
            schemas.UserBase(
                username=user.username,
                nickname=user.nickname,
                email=user.email,
                groups=[schemas.GroupInDatabase(id=grp.id, name=grp.name) for grp in user.groups],
                role=user.role
            )
            for user in users
        ]


async def fetch_users_by_condition(condition: str) -> List[schemas.UserBase]:
    """根据特定条件获取用户列表"""
    try:
        async with async_session() as session:
            stmt = sa.text(f"SELECT * FROM users WHERE {condition}")
            result = await session.execute(stmt)
            users = result.fetchall()

            return [
                schemas.UserBase(
                    id=user.id,
                    username=user.username,
                    nickname=user.nickname,
                    email=user.email,
                    role=user.role,
                    hashed_password=user.hashed_password,
                    is_temporary=user.is_temporary,
                    online=user.online,
                    avatar_index=user.avatar_index,
                    groups=[schemas.GroupInDatabase(id=grp.id, name=grp.name) for grp in user.groups]
                )
                for user in users
            ]
    except Exception as e:
        logging.error(f"根据条件获取用户失败: {e}")
        raise ValueError(f"根据条件获取用户失败: {str(e)}")


async def start_background_tasks():
    """启动后台任务"""
    logging.info("准备启动后台消息ID更新任务")
    task = asyncio.create_task(background_message_ids_updater())
    logging.info("后台消息ID更新任务已启动")
    return task


async def update_user_last_message(user_id: int, message_id: int) -> None:
    """更新用户的最后消息ID"""
    async with async_session() as session:
        query = sa.update(UserResponse).where(UserResponse.id == user_id).values(last_message_id=message_id)
        await session.execute(query)
        await session.commit()


async def process_message_updates():
    """处理消息更新队列"""
    while True:
        try:
            message_data = await message_update_queue.get()
            sender_id = message_data.sender_id
            recipient_id = message_data.recipient_id
            message_id = message_data.id

            async with async_session() as session:
                async with session.begin():
                    sender_stmt = sa.select(UserResponse).where(UserResponse.id == sender_id)
                    result = await session.execute(sender_stmt)
                    sender = result.scalar_one_or_none()

                    if sender:
                        if not isinstance(sender.message_ids, list):
                            sender.message_ids = []
                        sender.message_ids.append(message_id)

                    if recipient_id:
                        recipient_stmt = sa.select(UserResponse).where(UserResponse.id == recipient_id)
                        result = await session.execute(recipient_stmt)
                        recipient = result.scalar_one_or_none()

                        if recipient:
                            if not isinstance(recipient.message_ids, list):
                                recipient.message_ids = []
                            recipient.message_ids.append(message_id)

                await session.commit()

            message_update_queue.task_done()

        except Exception as e:
            logging.error(f"处理消息更新时出错: {str(e)}")
            logging.error(traceback.format_exc())
            message_update_queue.task_done()
            await asyncio.sleep(1)  


async def update_message_ids(update_data: schemas.UserMessageIDDataUpdate) -> None:
    """更新用户的消息ID列表"""
    try:
        async with async_session() as session:
            async with session.begin():
                sender_stmt = sa.select(UserResponse).where(UserResponse.id == update_data.sender_id)
                result = await session.execute(sender_stmt)
                sender = result.scalar_one_or_none()

                if sender:
                    if not isinstance(sender.message_ids, list):
                        sender.message_ids = []

                    new_message_ids = list(sender.message_ids)
                    new_message_ids.append(update_data.id)
                    sender.message_ids = new_message_ids

                if update_data.recipient_id:
                    recipient_stmt = sa.select(UserResponse).where(
                        UserResponse.id == update_data.recipient_id
                    )
                    result = await session.execute(recipient_stmt)
                    recipient = result.scalar_one_or_none()

                    if recipient:
                        if not isinstance(recipient.message_ids, list):
                            recipient.message_ids = []

                        new_message_ids = list(recipient.message_ids)
                        new_message_ids.append(update_data.id)
                        recipient.message_ids = new_message_ids

                await session.commit()
    except Exception as e:
        logging.error("更新消息ID时出错: %s", str(e))
        logging.error(traceback.format_exc())


async def update_all_message_ids(update_data: schemas.UserMessageIDDataUpdate) -> None:
    """更新用户的所有消息ID列表"""
    try:
        async with async_session() as session:
            async with session.begin():
                sender_stmt = sa.select(UserResponse).where(UserResponse.id == update_data.sender_id)
                result = await session.execute(sender_stmt)
                sender = result.scalar_one_or_none()

                if sender:
                    if not isinstance(sender.message_ids, list):
                        sender.message_ids = []
                    sender.message_ids.append(update_data.id)

                if update_data.recipient_id:
                    recipient_stmt = sa.select(UserResponse).where(
                        UserResponse.id == update_data.recipient_id
                    )
                    result = await session.execute(recipient_stmt)
                    recipient = result.scalar_one_or_none()

                    if recipient:
                        if not isinstance(recipient.message_ids, list):
                            recipient.message_ids = []
                        recipient.message_ids.append(update_data.id)

                await session.commit()

            logging.info(f"更新所有消息ID - 发送者ID: {update_data.sender_id}, 消息ID: {update_data.id}")
            if sender:
                logging.info(f"发送者 {sender.username} 的所有消息ID更新为: {sender.message_ids}")
            if update_data.recipient_id and recipient:
                logging.info(f"接收者 {recipient.username} 的所有消息ID更新为: {recipient.message_ids}")

    except Exception as e:
        logging.error(f"更新所有消息ID时出错: {str(e)}")
        logging.error(traceback.format_exc())
        raise


async def start_background_tasks():
    """启动后台任务"""
    logging.info("准备启动后台消息ID更新任务")
    task = asyncio.create_task(background_message_ids_updater())
    logging.info("后台消息ID更新任务已启动")
    return task


def get_column_value(value: Any) -> Any:
    """安全地获取 Column 值"""
    if hasattr(value, 'scalar'):
        return value.scalar()
    if isinstance(value, sa.Column):
        return value.expression
    return value


def convert_message_status(status: Any) -> List[schemas.MessageStatus]:
    """转换消息状态为正确的枚举类型"""
    if isinstance(status, list):
        return [schemas.MessageStatus(s) for s in status]
    return [schemas.MessageStatus.UNREAD]


def create_message_base(msg: Message) -> schemas.MessageBase:
    """从数据库消息创建 MessageBase 对象"""
    return schemas.MessageBase(
        sender=str(get_column_value(msg.sender)),
        recipient=str(get_column_value(msg.recipient)),
        content=str(get_column_value(msg.content)),
        timestamp=get_column_value(msg.timestamp),
        recipient_type=str(get_column_value(msg.recipient_type)),
        status=convert_message_status(get_column_value(msg.status)),
        message_type=schemas.MessageType(get_column_value(msg.message_type.type_code)),
        message_content_type=schemas.MessageContentType(get_column_value(msg.message_content_type.type_code)),
        popup_message=bool(get_column_value(msg.popup_message)),
        direction=schemas.MessageDirection.RESPONSE
    )


async def delete_messages(message_ids: List[int]) -> bool:
    """
    删除指定ID列表中的消息，并更新相关用户的message_ids列表。

    参数:
    - message_ids: 要删除的消息ID列表

    返回:
    - bool: 删除是否成功
    """
    try:
        async with async_session() as session:
            async with session.begin():
                # 先获取消息信息
                messages_stmt = sa.select(Message).where(Message.id.in_(message_ids))
                result = await session.execute(messages_stmt)
                messages = result.scalars().all()

                if not messages:
                    logging.warning(f"没有找到要删除的消息: {message_ids}")
                    return False

                # 获取发送者和接收者
                users_to_update = set()
                for message in messages:
                    users_to_update.add(message.sender)
                    users_to_update.add(message.recipient)

                # 获取所有涉及的用户对象
                users_stmt = sa.select(UserResponse).where(UserResponse.username.in_(users_to_update))
                result = await session.execute(users_stmt)
                users = result.scalars().all()

                # 更新每个用户的message_ids
                for user in users:
                    if user.message_ids:
                        user.message_ids = [mid for mid in user.message_ids if mid not in message_ids]

                # 删除消息
                for message in messages:
                    await session.delete(message)

                await session.commit()

                logging.info(f"成功删除消息: {message_ids}")
                return True

    except Exception as e:
        logging.error(f"删除消息时出错: {str(e)}")
        logging.error(traceback.format_exc())
        return False
