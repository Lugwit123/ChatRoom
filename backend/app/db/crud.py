"""数据库CRUD操作"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import Lugwit_Module as LM

from .schemas import User, Group, Device, GroupUser, MessageTypeModel, MessageContentTypeModel
from .schemas import UserRole, UserStatus, MessageType, MessageContentType

lprint = LM.lprint

# User CRUD
async def create_user(
    session: AsyncSession,
    username: str,
    password: str,
    role: UserRole = UserRole.user,
    status: UserStatus = UserStatus.normal
) -> User:
    """创建用户"""
    now = datetime.now()
    user = User(
        username=username,
        password=password,
        role=role,
        status=status,
        created_at=now,
        updated_at=now
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    """获取用户"""
    result = await session.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    """通过用户名获取用户"""
    result = await session.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none()

# Group CRUD
async def create_group(
    session: AsyncSession,
    name: str,
    description: Optional[str],
    created_by: int
) -> Group:
    """创建群组"""
    now = datetime.now()
    group = Group(
        name=name,
        description=description,
        created_by=created_by,
        created_at=now,
        updated_at=now
    )
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group

async def get_group(session: AsyncSession, group_id: int) -> Optional[Group]:
    """获取群组"""
    result = await session.execute(select(Group).filter(Group.id == group_id))
    return result.scalar_one_or_none()

# GroupUser CRUD
async def add_user_to_group(
    session: AsyncSession,
    user_id: int,
    group_id: int,
    is_admin: bool = False
) -> GroupUser:
    """添加用户到群组"""
    group_user = GroupUser(
        user_id=user_id,
        group_id=group_id,
        is_admin=is_admin,
        joined_at=datetime.now()
    )
    session.add(group_user)
    await session.commit()
    await session.refresh(group_user)
    return group_user

# Device CRUD
async def create_device(
    session: AsyncSession,
    name: str,
    user_id: int,
    description: Optional[str] = None
) -> Device:
    """创建设备"""
    now = datetime.now()
    device = Device(
        name=name,
        description=description,
        user_id=user_id,
        created_at=now,
        updated_at=now
    )
    session.add(device)
    await session.commit()
    await session.refresh(device)
    return device

async def get_device(session: AsyncSession, device_id: int) -> Optional[Device]:
    """获取设备"""
    result = await session.execute(select(Device).filter(Device.id == device_id))
    return result.scalar_one_or_none()

# MessageType CRUD
async def create_message_type(
    session: AsyncSession,
    type_code: MessageType
) -> MessageTypeModel:
    """创建消息类型"""
    message_type = MessageTypeModel(type_code=type_code)
    session.add(message_type)
    await session.commit()
    await session.refresh(message_type)
    return message_type

# MessageContentType CRUD
async def create_message_content_type(
    session: AsyncSession,
    type_code: MessageContentType
) -> MessageContentTypeModel:
    """创建消息内容类型"""
    content_type = MessageContentTypeModel(type_code=type_code)
    session.add(content_type)
    await session.commit()
    await session.refresh(content_type)
    return content_type
