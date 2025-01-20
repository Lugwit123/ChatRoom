from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_repository import BaseRepository
from app.domain.message.models import PrivateMessage, MessageReaction, MessageMention
from app.domain.message.enums import MessageStatus
import Lugwit_Module as LM
lprint = LM.lprint

class PrivateMessageRepository:
    """私聊消息仓储"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create(self, message_data: Dict[str, Any]):
        """创建私聊消息
        
        Args:
            message_data: 消息数据
            
        Returns:
            创建的消息
        """
        try:
            # 创建消息
            message = PrivateMessage(**message_data)
            self.session.add(message)
            await self.session.flush()
            
            # 处理@提醒
            if message_data.get("mentions"):
                for user_id in message_data["mentions"]:
                    mention = MessageMention(
                        message_table="private_messages",
                        message_id=message.id,
                        user_id=user_id
                    )
                    self.session.add(mention)
                    
            await self.session.commit()
            return message
            
        except Exception as e:
            await self.session.rollback()
            lprint(f"创建私聊消息失败: {str(e)}")
            raise
            
    async def get_by_id(self, message_id: int):
        """根据ID获取消息
        
        Args:
            message_id: 消息ID
            
        Returns:
            消息对象
        """
        try:
            stmt = select(PrivateMessage).where(PrivateMessage.id == message_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            lprint(f"获取私聊消息失败: {str(e)}")
            raise
            
    async def get_messages(self, 
                          user_id: int,
                          other_id: int,
                          limit: int = 20,
                          before_id: Optional[int] = None,
                          after_id: Optional[int] = None):
        """获取两个用户之间的私聊消息
        
        Args:
            user_id: 当前用户ID
            other_id: 对方用户ID
            limit: 返回消息数量
            before_id: 在此ID之前的消息
            after_id: 在此ID之后的消息
            
        Returns:
            消息列表
        """
        try:
            # 构建查询条件
            conditions = [
                or_(
                    and_(
                        PrivateMessage.sender_id == user_id,
                        PrivateMessage.receiver_id == other_id
                    ),
                    and_(
                        PrivateMessage.sender_id == other_id,
                        PrivateMessage.receiver_id == user_id
                    )
                )
            ]
            
            if before_id:
                conditions.append(PrivateMessage.id < before_id)
            if after_id:
                conditions.append(PrivateMessage.id > after_id)
                
            # 构建查询语句
            stmt = select(PrivateMessage)
            if conditions:
                stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(desc(PrivateMessage.id)).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            lprint(f"获取私聊消息列表失败: {str(e)}")
            raise
            
    async def update_status(self, message_id: int, status: MessageStatus):
        """更新消息状态
        
        Args:
            message_id: 消息ID
            status: 新状态
        """
        try:
            message = await self.get_by_id(message_id)
            if message:
                message.status = status
                await self.session.commit()
                
        except Exception as e:
            await self.session.rollback()
            lprint(f"更新私聊消息状态失败: {str(e)}")
            raise
            
    async def add_reaction(self, message_id: int, user_id: int, reaction: str):
        """添加表情回应
        
        Args:
            message_id: 消息ID
            user_id: 用户ID
            reaction: 表情
        """
        try:
            # 检查消息是否存在
            message = await self.get_by_id(message_id)
            if not message:
                raise ValueError(f"消息不存在: {message_id}")
                
            # 创建表情回应
            reaction = MessageReaction(
                message_table="private_messages",
                message_id=message_id,
                user_id=user_id,
                reaction=reaction
            )
            self.session.add(reaction)
            await self.session.commit()
            
        except Exception as e:
            await self.session.rollback()
            lprint(f"添加表情回应失败: {str(e)}")
            raise
            
    async def remove_reaction(self, message_id: int, user_id: int, reaction: str):
        """移除表情回应
        
        Args:
            message_id: 消息ID
            user_id: 用户ID
            reaction: 表情
        """
        try:
            # 删除表情回应
            stmt = (
                select(MessageReaction)
                .where(
                    and_(
                        MessageReaction.message_table == "private_messages",
                        MessageReaction.message_id == message_id,
                        MessageReaction.user_id == user_id,
                        MessageReaction.reaction == reaction
                    )
                )
            )
            result = await self.session.execute(stmt)
            reaction = result.scalar_one_or_none()
            
            if reaction:
                await self.session.delete(reaction)
                await self.session.commit()
                
        except Exception as e:
            await self.session.rollback()
            lprint(f"移除表情回应失败: {str(e)}")
            raise
            
    async def get_unread_count(self, user_id: int) -> int:
        """获取用户的未读私聊消息数量"""
        try:
            stmt = (
                select(PrivateMessage)
                .where(
                    and_(
                        PrivateMessage.receiver_id == user_id,
                        PrivateMessage.status == MessageStatus.unread
                    )
                )
            )
            result = await self.session.execute(stmt)
            return len(result.scalars().all())
            
        except Exception as e:
            lprint(f"获取未读私聊消息数量失败: {str(e)}")
            raise
            
    async def mark_as_read(self, user_id: int, other_id: int) -> int:
        """标记与某个用户的所有未读消息为已读
        
        Args:
            user_id: 当前用户ID
            other_id: 对方用户ID
            
        Returns:
            更新的消息数量
        """
        try:
            stmt = (
                select(PrivateMessage)
                .where(
                    and_(
                        PrivateMessage.receiver_id == user_id,
                        PrivateMessage.sender_id == other_id,
                        PrivateMessage.status == MessageStatus.unread
                    )
                )
            )
            result = await self.session.execute(stmt)
            messages = result.scalars().all()
            
            for message in messages:
                message.status = MessageStatus.read
                
            await self.session.commit()
            return len(messages)
            
        except Exception as e:
            await self.session.rollback()
            lprint(f"标记私聊消息已读失败: {str(e)}")
            raise
