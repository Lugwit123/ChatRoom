"""
私聊消息仓储
处理私聊消息的存储和查询
"""
# 标准库
from datetime import datetime
from typing import Optional, List, Dict, Any, NamedTuple, Sequence
from zoneinfo import ZoneInfo
import traceback

# 第三方库
from sqlalchemy import select, and_, update, delete, text, or_, desc, case
from sqlalchemy.sql import expression
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

# 本地模块
import Lugwit_Module as LM
lprint = LM.lprint

from app.domain.common.models.tables import PrivateMessage, User
from app.domain.common.enums.message import MessageStatus
from app.domain.message.internal.repository.base import BaseMessageRepository

class MessageWithUsernames(NamedTuple):
    """消息及用户名信息"""
    message: PrivateMessage
    sender_username: str
    recipient_username: str
    other_username: str

class PrivateMessageRepository(BaseMessageRepository):
    """私聊消息仓储实现"""
    
    def __init__(self):
        """初始化私聊消息仓储"""
        super().__init__()
        self.model = PrivateMessage
        
    async def save_message(self, message_data: dict) -> PrivateMessage:
        """保存私聊消息
        
        Args:
            message_data: 消息数据
            
        Returns:
            PrivateMessage: 保存的消息
        """
        try:
            # 检查必要字段
            if not message_data.get("recipient_id"):
                raise ValueError("私聊消息必须指定接收者ID")
                
            # 保存消息
            return await super().save_message(message_data)
            
        except Exception as e:
            self.lprint(f"保存私聊消息失败: {str(e)}")
            raise
            
    async def get_messages(self, user_id: int, limit: int = 20) -> Sequence[PrivateMessage]:
        """获取用户的私聊消息
        
        Args:
            user_id: 用户ID
            limit: 返回结果数量限制
            
        Returns:
            Sequence[PrivateMessage]: 消息列表
        """
        stmt = select(self.model).where(
            or_(
                self.model.sender_id == user_id,
                self.model.recipient_id == user_id
            )
        ).order_by(desc(self.model.created_at)).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_chat_messages(
        self,
        user_id: int,
        other_id: int,
        limit: int = 20,
        before_id: Optional[int] = None
    ) -> List[MessageWithUsernames]:
        """获取两个用户间的聊天记录
        
        Args:
            user_id: 用户ID
            other_id: 对方ID
            limit: 限制数量
            before_id: 在此ID之前的消息
            
        Returns:
            List[MessageWithUsernames]: 消息列表
        """
        return await self.get_messages(user_id, limit)
    
    async def get_unread_count(self, user_id: int) -> int:
        """获取未读消息数
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 未读消息数
        """
        unread_value = MessageStatus.unread.value
        query = (
            select(PrivateMessage)
            .where(
                and_(
                    PrivateMessage.recipient_id == user_id,
                    text(f"{unread_value} = ANY(status)")  # 使用 PostgreSQL 的 ANY 操作符
                )
            )
        )
        async with self.session.begin():
            result = await self.session.execute(query)
            return len(result.scalars().all())
    
    async def mark_all_as_read(self, user_id: int, other_id: int) -> bool:
        """标记所有消息为已读
        
        Args:
            user_id: 用户ID
            other_id: 对方ID
            
        Returns:
            bool: 是否成功
        """
        unread_value = MessageStatus.unread.value
        stmt = (
            update(PrivateMessage)
            .where(
                and_(
                    PrivateMessage.recipient_id == user_id,
                    PrivateMessage.sender_id == other_id,
                    text(f"{unread_value} = ANY(status)")  # 使用 PostgreSQL 的 ANY 操作符
                )
            )
            .values(
                status=[MessageStatus.read.value],  # 使用 status 和枚举值
                read_at=datetime.now(ZoneInfo("Asia/Shanghai"))
            )
        )
        async with self.session.begin():
            await self.session.execute(stmt)
            return True

    async def get_chat_partners(self, user_id: int) -> List[int]:
        """获取用户的所有聊天伙伴ID
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[int]: 聊天伙伴ID列表
        """
        try:
            # 使用独立的会话
            async with self.get_session() as session:
                # 查询用户作为发送者的所有私聊消息的接收者
                query = select(PrivateMessage.recipient_id).where(
                    PrivateMessage.sender_id == user_id
                ).distinct()
                
                # 查询用户作为接收者的所有私聊消息的发送者
                query2 = select(PrivateMessage.sender_id).where(
                    PrivateMessage.recipient_id == user_id
                ).distinct()
                
                # 执行查询
                result1 = await session.execute(query)
                result2 = await session.execute(query2)
                
                # 获取所有不重复的用户ID
                partner_ids = set()
                for row in result1:
                    partner_ids.add(row[0])
                for row in result2:
                    partner_ids.add(row[0])
                    
                self.lprint(f"用户 {user_id} 的聊天伙伴: {partner_ids}")
                return list(partner_ids)
                
        except Exception as e:
            self.lprint(f"获取聊天伙伴失败: {str(e)}")
            self.lprint(traceback.format_exc())
            return []
