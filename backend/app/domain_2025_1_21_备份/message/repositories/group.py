"""
群组消息仓储实现文件

本文件实现了群组消息的数据访问层，负责群组消息的存储和检索。

GroupMessageRepository类的主要功能:
1. 基础操作(继承自BaseMessageRepository):
   - get_by_id(): 根据ID获取消息
   - get_many(): 批量获取消息
   - mark_as_read(): 标记消息为已读
   - mark_as_deleted(): 标记消息为已删除
   - mark_as_recalled(): 标记消息为已撤回

2. 消息查询:
   - get_messages(): 获取群组消息列表
   - get_message_by_public_id(): 根据公开ID获取消息
   - search_messages(): 搜索群组消息
   - get_unread_count(): 获取未读消息数

3. 消息互动(继承自BaseMessageRepository):
   - add_reaction(): 添加消息表情回应
   - remove_reaction(): 移除消息表情回应
   - get_reactions(): 获取消息的表情回应
   - add_mention(): 添加@提醒
   - remove_mention(): 移除@提醒
   - get_mentions(): 获取消息的@提醒

4. 表管理:
   - create_message_table(): 创建群组消息表
   - drop_message_table(): 删除群组消息表
   - table_exists(): 检查消息表是否存在
"""

from typing import Dict, Any, List, Optional, Union, Type
from datetime import datetime
from sqlalchemy import select, and_, or_, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.message.models import create_group_message_table
from app.domain.message.enums import MessageStatus
from app.domain.group.models import GroupMember
from app.domain.message.repositories.base import BaseMessageRepository

class GroupMessageRepository(BaseMessageRepository):
    """群组消息仓储实现"""
    
    def __init__(self, session: AsyncSession, group_id: str):
        """初始化群组消息仓储
        
        Args:
            session: 数据库会话
            group_id: 群组ID
        """
        self.group_id = group_id
        self.message_table = create_group_message_table(group_id)
        super().__init__(session, self.message_table)
    
    async def get_messages(
        self,
        limit: int = 20,
        before_id: Optional[int] = None,
        after_id: Optional[int] = None
    ) -> List[Any]:
        """获取群组消息列表
        
        Args:
            limit: 限制数量
            before_id: 在此ID之前的消息
            after_id: 在此ID之后的消息
            
        Returns:
            List[Any]: 消息列表
        """
        conditions = []
        
        if before_id:
            conditions.append(self.message_model.id < before_id)
        if after_id:
            conditions.append(self.message_model.id > after_id)
        
        query = select(self.message_model)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(desc(self.message_model.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_message_by_public_id(self, public_id: str) -> Optional[Any]:
        """根据公开ID获取消息
        
        Args:
            public_id: 消息公开ID
            
        Returns:
            Optional[Any]: 消息对象或None
        """
        query = select(self.message_model).where(self.message_model.public_id == public_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def search_messages(
        self,
        keyword: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Any]:
        """搜索群组消息
        
        Args:
            keyword: 关键词
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[Any]: 消息列表
        """
        query = (
            select(self.message_model)
            .where(self.message_model.content.ilike(f"%{keyword}%"))
            .order_by(desc(self.message_model.created_at))
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_unread_count(self, user_id: int) -> int:
        """获取未读消息数
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 未读消息数
        """
        # 获取用户加入群组的时间
        member_query = select(GroupMember).where(
            and_(
                GroupMember.group_id == self.group_id,
                GroupMember.user_id == user_id
            )
        )
        member_result = await self.session.execute(member_query)
        member = member_result.scalar_one_or_none()
        
        if not member:
            return 0
        
        # 获取未读消息数
        query = select(self.message_model).where(
            and_(
                self.message_model.created_at >= member.joined_at,
                self.message_model.sender_id != user_id,
                self.message_model.status == MessageStatus.unread
            )
        )
        result = await self.session.execute(query)
        return len(result.scalars().all())
    
    async def create_message_table(self) -> None:
        """创建群组消息表"""
        await self.session.execute(text(f"CREATE TABLE IF NOT EXISTS group_messages_{self.group_id} LIKE group_messages_template"))
        await self.session.commit()
    
    async def drop_message_table(self) -> None:
        """删除群组消息表"""
        await self.session.execute(text(f"DROP TABLE IF EXISTS group_messages_{self.group_id}"))
        await self.session.commit()
    
    async def table_exists(self) -> bool:
        """检查消息表是否存在
        
        Returns:
            bool: 表是否存在
        """
        result = await self.session.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = :table_name)"
            ),
            {"table_name": f"group_messages_{self.group_id}"}
        )
        return result.scalar_one()
