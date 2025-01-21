"""
私聊消息仓储
处理私聊消息的存储和查询
"""
import Lugwit_Module as LM
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, desc
from datetime import datetime

from app.domain.message.internal.models import PrivateMessage
from app.domain.message.internal.enums import MessageStatus
from app.domain.message.repositories.base import BaseMessageRepository

class PrivateMessageRepository(BaseMessageRepository):
    """私聊消息仓储实现"""
    
    def __init__(self, session: AsyncSession):
        """初始化私聊消息仓储
        
        Args:
            session: 数据库会话
        """
        super().__init__(session, PrivateMessage)
    
    async def get_messages(
        self,
        user_id: int,
        other_id: Optional[int] = None,
        limit: int = 20,
        before_id: Optional[int] = None
    ) -> List[PrivateMessage]:
        """获取私聊消息列表
        
        Args:
            user_id: 用户ID
            other_id: 对方ID
            limit: 限制数量
            before_id: 在此ID之前的消息
            
        Returns:
            List[PrivateMessage]: 消息列表
        """
        conditions = []
        if other_id:
            conditions.append(
                or_(
                    and_(PrivateMessage.sender_id == user_id, PrivateMessage.receiver_id == other_id),
                    and_(PrivateMessage.sender_id == other_id, PrivateMessage.receiver_id == user_id)
                )
            )
        else:
            conditions.append(
                or_(
                    PrivateMessage.sender_id == user_id,
                    PrivateMessage.receiver_id == user_id
                )
            )
        
        if before_id:
            conditions.append(PrivateMessage.id < before_id)
        
        query = (
            select(PrivateMessage)
            .where(and_(*conditions))
            .order_by(desc(PrivateMessage.created_at))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_chat_messages(
        self,
        user_id: int,
        other_id: int,
        limit: int = 20,
        before_id: Optional[int] = None
    ) -> List[PrivateMessage]:
        """获取两个用户间的聊天记录
        
        Args:
            user_id: 用户ID
            other_id: 对方ID
            limit: 限制数量
            before_id: 在此ID之前的消息
            
        Returns:
            List[PrivateMessage]: 消息列表
        """
        return await self.get_messages(user_id, other_id, limit, before_id)
    
    async def get_unread_count(self, user_id: int) -> int:
        """获取未读消息数
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 未读消息数
        """
        query = select(PrivateMessage).where(
            and_(
                PrivateMessage.receiver_id == user_id,
                PrivateMessage.status == MessageStatus.unread
            )
        )
        result = await self.session.execute(query)
        return len(result.scalars().all())
