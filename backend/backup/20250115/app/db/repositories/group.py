"""群组仓储类"""
from typing import Optional, List, Union, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.schemas import Group
from app.db.schemas import GroupCreate
import Lugwit_Module as LM

lprint = LM.lprint

class GroupRepository:
    """群组仓储类，提供群组相关的数据库操作方法"""
    
    def __init__(self):
        pass
    
    async def get_by_name(self, session: AsyncSession, name: str) -> Optional[Group]:
        """根据群组名称获取群组"""
        query = select(Group).where(Group.name == name)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_groups(
        self,
        session: AsyncSession,
        username: str
    ) -> List[Group]:
        """获取用户所在的所有群组"""
        query = select(Group).where(Group.members.contains([username]))
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_group_members(
        self,
        session: AsyncSession,
        group_name: str
    ) -> List[str]:
        """获取群组的所有成员"""
        group = await self.get_by_name(session, group_name)
        if not group:
            return []
        return group.members
    
    async def add_user_to_group(
        self,
        session: AsyncSession,
        *,
        group_name: str,
        username: str
    ) -> Optional[Group]:
        """将用户添加到群组"""
        group = await self.get_by_name(session, group_name)
        if not group:
            return None
            
        if username not in group.members:
            group.members.append(username)
            session.add(group)
            await session.commit()
            await session.refresh(group)
            
        return group
    
    async def remove_user_from_group(
        self,
        session: AsyncSession,
        *,
        group_name: str,
        username: str
    ) -> Optional[Group]:
        """从群组中移除用户"""
        group = await self.get_by_name(session, group_name)
        if not group:
            return None
            
        if username in group.members:
            group.members.remove(username)
            session.add(group)
            await session.commit()
            await session.refresh(group)
            
        return group
    
    async def get_group_users(
        self,
        session: AsyncSession,
        group_name: str
    ) -> List[Dict[str, Any]]:
        """获取群组中的所有用户信息"""
        group = await self.get_by_name(session, group_name)
        if not group:
            return []
        
        from app.db.repositories.user import UserRepository
        user_repo = UserRepository()
        users = []
        
        for username in group.members:
            user = await user_repo.get_by_username(session, username)
            if user:
                users.append({
                    "username": user.username,
                    "nickname": user.nickname,
                    "online": user.login_status,
                    "role": user.role
                })
        
        return users
