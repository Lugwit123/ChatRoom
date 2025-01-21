"""
基础消息仓储类

本文件实现了消息仓储的基础功能，作为其他消息仓储的基类。
包含了消息的基础操作、状态管理和互动功能。

BaseMessageRepository类的主要功能:
1. 基础操作:
   - get_by_id(): 根据ID获取消息
   - get_many(): 批量获取消息
   - create(): 创建消息
   - update(): 更新消息
   - delete(): 删除消息

2. 消息状态:
   - mark_as_read(): 标记消息为已读
   - mark_as_deleted(): 标记消息为已删除
   - mark_as_recalled(): 标记消息为已撤回

3. 消息互动:
   - add_reaction(): 添加消息表情回应
   - remove_reaction(): 移除消息表情回应
   - get_reactions(): 获取消息的表情回应
   - add_mention(): 添加@提醒
   - remove_mention(): 移除@提醒
   - get_mentions(): 获取消息的@提醒
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.message.models import MessageReaction, MessageMention
from app.domain.message.enums import MessageStatus
from zoneinfo import ZoneInfo

class BaseMessageRepository:
    """基础消息仓储实现"""
    
    def __init__(self, session: AsyncSession, message_model: Any):
        """初始化基础仓储
        
        Args:
            session: 数据库会话
            message_model: 消息模型类
        """
        self.session = session
        self.message_model = message_model
    
    async def get_by_id(self, message_id: int) -> Optional[Any]:
        """根据ID获取消息
        
        Args:
            message_id: 消息ID
            
        Returns:
            Optional[Any]: 消息对象或None
        """
        query = select(self.message_model).where(self.message_model.id == message_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_many(self, message_ids: List[int]) -> List[Any]:
        """批量获取消息
        
        Args:
            message_ids: 消息ID列表
            
        Returns:
            List[Any]: 消息对象列表
        """
        query = select(self.message_model).where(self.message_model.id.in_(message_ids))
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def mark_as_read(self, message_id: int) -> bool:
        """标记消息为已读
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否成功
        """
        message = await self.get_by_id(message_id)
        if message:
            message.status = MessageStatus.read
            message.updated_at = datetime.now(ZoneInfo("Asia/Shanghai"))
            await self.session.commit()
            return True
        return False
    
    async def mark_as_deleted(self, message_id: int) -> bool:
        """标记消息为已删除
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否成功
        """
        message = await self.get_by_id(message_id)
        if message:
            message.is_deleted = True
            message.delete_at = datetime.now(ZoneInfo("Asia/Shanghai"))
            message.updated_at = datetime.now(ZoneInfo("Asia/Shanghai"))
            await self.session.commit()
            return True
        return False
    
    async def mark_as_recalled(self, message_id: int) -> bool:
        """标记消息为已撤回
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否成功
        """
        message = await self.get_by_id(message_id)
        if message:
            message.status = MessageStatus.recalled
            message.updated_at = datetime.now(ZoneInfo("Asia/Shanghai"))
            await self.session.commit()
            return True
        return False
    
    async def add_reaction(self, message_id: int, user_id: int, reaction: str) -> Optional[MessageReaction]:
        """添加消息表情回应
        
        Args:
            message_id: 消息ID
            user_id: 用户ID
            reaction: 表情
            
        Returns:
            Optional[MessageReaction]: 表情回应对象或None
        """
        message = await self.get_by_id(message_id)
        if message:
            reaction_obj = MessageReaction(
                message_table=self.message_model.__tablename__,
                message_id=message_id,
                user_id=user_id,
                reaction=reaction
            )
            self.session.add(reaction_obj)
            await self.session.commit()
            return reaction_obj
        return None
    
    async def remove_reaction(self, message_id: int, user_id: int, reaction: str) -> bool:
        """移除消息表情回应
        
        Args:
            message_id: 消息ID
            user_id: 用户ID
            reaction: 表情
            
        Returns:
            bool: 是否成功
        """
        query = select(MessageReaction).where(
            and_(
                MessageReaction.message_table == self.message_model.__tablename__,
                MessageReaction.message_id == message_id,
                MessageReaction.user_id == user_id,
                MessageReaction.reaction == reaction
            )
        )
        result = await self.session.execute(query)
        reaction_obj = result.scalar_one_or_none()
        if reaction_obj:
            await self.session.delete(reaction_obj)
            await self.session.commit()
            return True
        return False
    
    async def get_reactions(self, message_id: int) -> List[MessageReaction]:
        """获取消息的表情回应
        
        Args:
            message_id: 消息ID
            
        Returns:
            List[MessageReaction]: 表情回应列表
        """
        query = select(MessageReaction).where(
            and_(
                MessageReaction.message_table == self.message_model.__tablename__,
                MessageReaction.message_id == message_id
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def add_mention(self, message_id: int, user_id: int) -> Optional[MessageMention]:
        """添加@提醒
        
        Args:
            message_id: 消息ID
            user_id: 被@的用户ID
            
        Returns:
            Optional[MessageMention]: @提醒对象或None
        """
        message = await self.get_by_id(message_id)
        if message:
            mention = MessageMention(
                message_table=self.message_model.__tablename__,
                message_id=message_id,
                user_id=user_id
            )
            self.session.add(mention)
            await self.session.commit()
            return mention
        return None
    
    async def remove_mention(self, message_id: int, user_id: int) -> bool:
        """移除@提醒
        
        Args:
            message_id: 消息ID
            user_id: 被@的用户ID
            
        Returns:
            bool: 是否成功
        """
        query = select(MessageMention).where(
            and_(
                MessageMention.message_table == self.message_model.__tablename__,
                MessageMention.message_id == message_id,
                MessageMention.user_id == user_id
            )
        )
        result = await self.session.execute(query)
        mention = result.scalar_one_or_none()
        if mention:
            await self.session.delete(mention)
            await self.session.commit()
            return True
        return False
    
    async def get_mentions(self, message_id: int) -> List[MessageMention]:
        """获取消息的@提醒
        
        Args:
            message_id: 消息ID
            
        Returns:
            List[MessageMention]: @提醒列表
        """
        query = select(MessageMention).where(
            and_(
                MessageMention.message_table == self.message_model.__tablename__,
                MessageMention.message_id == message_id
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()
