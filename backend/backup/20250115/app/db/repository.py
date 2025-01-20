"""
数据库仓库模块
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from .schemas import (
    User, Group, MessagePayload, Device,
    MessageType, MessageStatus, MessageDirection,
    UserRole, MessageTypeModel, MessageContentTypeModel
)
import traceback
import logging

logging.basicConfig(level=logging.INFO)
lprint = logging.info

class UserRepository:
    """用户仓库"""
    
    async def get_by_username(self, session: AsyncSession, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_registered_users(
        self, 
        session: AsyncSession, 
        exclude_roles: List[UserRole] = []
    ) -> List[User]:
        """获取所有注册用户"""
        stmt = select(User).where(
            and_(
                User.is_temporary == False,
                User.role.notin_(exclude_roles)
            )
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_all_temporary(self, session: AsyncSession) -> List[User]:
        """获取所有临时用户"""
        stmt = select(User).where(User.is_temporary == True)
        result = await session.execute(stmt)
        return result.scalars().all()

class GroupRepository:
    """群组仓库"""
    
    async def get_by_id(self, session: AsyncSession, group_id: int) -> Optional[Group]:
        """通过ID获取群组"""
        stmt = select(Group).where(Group.id == group_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_by_name(self, session: AsyncSession, name: str) -> Optional[Group]:
        """通过名称获取群组"""
        stmt = select(Group).where(Group.name == name)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_all(self, session: AsyncSession) -> List[Group]:
        """获取所有群组"""
        stmt = select(Group)
        result = await session.execute(stmt)
        return result.scalars().all()
        
    async def get_group_members(self, session: AsyncSession, group_name: str) -> List[str]:
        """获取群组成员列表
        
        Args:
            session: 数据库会话
            group_name: 群组名称
            
        Returns:
            List[str]: 群组成员用户名列表
        """
        try:
            group = await self.get_by_name(session, group_name)
            if not group:
                return []
            return group.members
        except Exception as e:
            lprint(f"获取群组成员失败: {str(e)}")
            lprint(traceback.format_exc())
            return []

class DeviceRepository:
    """设备仓库"""
    
    async def get_by_id(self, session: AsyncSession, device_id: str) -> Optional[Device]:
        """通过ID获取设备"""
        stmt = select(Device).where(Device.device_id == device_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_devices(
        self,
        session: AsyncSession,
        user_id: int
    ) -> List[Device]:
        """获取用户的所有设备"""
        stmt = select(Device).where(Device.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def update_device_status(
        self,
        session: AsyncSession,
        device_id: str,
        login_status: bool
    ) -> None:
        """更新设备状态"""
        stmt = (
            update(Device)
            .where(Device.device_id == device_id)
            .values(
                login_status=login_status,
                last_seen=datetime.now(timezone.utc)
            )
        )
        await session.execute(stmt)
        await session.commit()
