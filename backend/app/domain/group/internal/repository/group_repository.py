"""群组仓库模块"""
# 标准库
from datetime import datetime
from typing import List, Optional, Dict, Any, Sequence
from zoneinfo import ZoneInfo

# 第三方库
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import traceback

# 本地模块
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from app.domain.common.models.tables import Group, GroupMember, User
from app.domain.common.enums.group import GroupMemberRole, GroupStatus
from app.domain.base.internal.repository.base_repository import BaseRepository

class GroupRepository(BaseRepository[Group]):
    """群组仓储类
    
    提供群组相关的数据库操作，包括：
    1. 基本的CRUD操作（继承自BaseRepository）
    2. 群组查询（按名称、状态等）
    3. 群组统计
    4. 成员管理
    """
    
    def __init__(self):
        """初始化群组仓储"""
        super().__init__(Group)

    async def create_group(
        self,
        name: str,
        owner_id: int,
        description: Optional[str] = None,
        avatar_url: Optional[str] = None,
        max_members: int = 200
    ) -> Group:
        """创建群组
        
        Args:
            name: 群组名称
            owner_id: 创建者ID
            description: 群组描述
            avatar_url: 群组头像URL
            max_members: 最大成员数
            
        Returns:
            创建的群组
            
        Raises:
            Exception: 创建失败时抛出
        """
        try:
            group = Group(
                name=name,
                owner_id=owner_id,
                description=description,
                avatar_url=avatar_url,
                max_members=max_members,
                status=GroupStatus.normal,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            return await self.create(group)
        except Exception as e:
            lprint(f"创建群组失败: {traceback.format_exc()}")
            raise

    async def get_by_name(self, name: str) -> Optional[Group]:
        """根据名称获取群组
        
        Args:
            name: 群组名称
            
        Returns:
            找到的群组或None
        """
        try:
            query = select(self.model).where(self.model.name == name)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            lprint(f"根据名称获取群组失败: {traceback.format_exc()}")
            return None

    async def get_user_groups(
        self,
        user_id: int,
        status: Optional[GroupStatus] = None
    ) -> Sequence[Group]:
        """获取用户的群组
        
        Args:
            user_id: 用户ID
            status: 群组状态（可选）
            
        Returns:
            群组列表
        """
        try:
            conditions = []
            if status:
                conditions.append(self.model.status == status)

            query = (
                select(self.model)
                .join(GroupMember)
                .where(
                    and_(
                        GroupMember.user_id == user_id,
                        *conditions
                    )
                )
            )
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            lprint(f"获取用户群组失败: {traceback.format_exc()}")
            return []

    async def search_groups(
        self,
        keyword: str,
        limit: int = 20
    ) -> Sequence[Group]:
        """搜索群组
        
        Args:
            keyword: 搜索关键词
            limit: 限制数量
            
        Returns:
            匹配的群组列表
        """
        try:
            query = (
                select(self.model)
                .where(
                    and_(
                        self.model.status == GroupStatus.normal,
                        or_(
                            self.model.name.ilike(f"%{keyword}%"),
                            self.model.description.ilike(f"%{keyword}%")
                        )
                    )
                )
                .limit(limit)
            )
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            lprint(f"搜索群组失败: {traceback.format_exc()}")
            return []

    async def get_member_count(self, group_id: int) -> int:
        """获取群组成员数量
        
        Args:
            group_id: 群组ID
            
        Returns:
            成员数量
        """
        try:
            query = (
                select(func.count())
                .select_from(GroupMember)
                .where(GroupMember.group_id == group_id)
            )
            result = await self.session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            lprint(f"获取群组成员数量失败: {traceback.format_exc()}")
            return 0

    async def update_status(
        self,
        group_id: int,
        status: GroupStatus
    ) -> bool:
        """更新群组状态
        
        Args:
            group_id: 群组ID
            status: 新状态
            
        Returns:
            是否成功
        """
        try:
            return await self.update_by_id(group_id, status=status) is not None
        except Exception as e:
            lprint(f"更新群组状态失败: {traceback.format_exc()}")
            return False

    async def get_group_stats(self, group_id: int) -> Dict[str, Any]:
        """获取群组统计信息
        
        Args:
            group_id: 群组ID
            
        Returns:
            统计信息字典
        """
        try:
            # 获取成员数量
            member_count = await self.get_member_count(group_id)
            
            # 获取今日消息数
            today = datetime.utcnow().date()
            message_query = (
                select(func.count())
                .select_from(self.model)
                .where(
                    and_(
                        self.model.group_id == group_id,
                        func.date(self.model.created_at) == today
                    )
                )
            )
            message_count = await self.session.execute(message_query)
            
            return {
                "member_count": member_count,
                "today_message_count": message_count.scalar() or 0,
                "created_at": (await self.get_by_id(group_id)).created_at
            }
        except Exception as e:
            lprint(f"获取群组统计信息失败: {traceback.format_exc()}")
            return {
                "member_count": 0,
                "today_message_count": 0,
                "created_at": None
            }

class GroupMemberRepository(BaseRepository[GroupMember]):
    """群组成员仓储"""
    
    def __init__(self):
        """初始化群组成员仓储"""
        super().__init__(GroupMember)

    async def get_group_members(self, group_id: int) -> Sequence[GroupMember]:
        """获取群组成员
        
        Args:
            group_id: 群组ID
            
        Returns:
            成员列表
        """
        try:
            query = select(self.model).where(self.model.group_id == group_id)
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            lprint(f"获取群组成员失败: {traceback.format_exc()}")
            return []

    async def is_member(self, group_id: int, user_id: int) -> bool:
        """检查用户是否是群组成员
        
        Args:
            group_id: 群组ID
            user_id: 用户ID
            
        Returns:
            是否是成员
        """
        try:
            query = select(GroupMember).where(
                and_(
                    GroupMember.group_id == group_id,
                    GroupMember.user_id == user_id
                )
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            lprint(f"检查群组成员失败: {traceback.format_exc()}")
            return False

    async def add_member(self, group_id: int, user_id: int, role: GroupMemberRole = GroupMemberRole.member) -> GroupMember:
        """添加群组成员
        
        Args:
            group_id: 群组ID
            user_id: 用户ID
            role: 成员角色
            
        Returns:
            创建的成员记录
            
        Raises:
            Exception: 添加失败时抛出
        """
        try:
            member = GroupMember(
                group_id=group_id,
                user_id=user_id,
                role=role
            )
            self.session.add(member)
            await self.session.flush()
            return member
        except Exception as e:
            lprint(f"添加群组成员失败: {traceback.format_exc()}")
            await self.session.rollback()
            raise

    async def remove_member(self, group_id: int, user_id: int) -> bool:
        """移除群组成员
        
        Args:
            group_id: 群组ID
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        try:
            query = select(self.model).where(
                and_(
                    self.model.group_id == group_id,
                    self.model.user_id == user_id
                )
            )
            result = await self.session.execute(query)
            member = result.scalar_one_or_none()
            if member:
                await self.session.delete(member)
                await self.session.commit()
                return True
            return False
        except Exception as e:
            lprint(f"移除群组成员失败: {traceback.format_exc()}")
            return False
