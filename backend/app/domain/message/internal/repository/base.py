"""
基础消息仓储类

本文件实现了消息仓储的基础功能，作为其他消息仓储的基类。
包含了消息的基础操作和状态管理功能。

BaseMessageRepository类的主要功能:
1. 基础操作:
   - get_by_id(): 根据ID获取消息
   - get_many(): 批量获取消息
   - create(): 创建消息
   - update(): 更新消息
   - delete(): 删除消息

2. 消息状态:
   - mark_as_read(): 标记消息为已读
   - mark_as_delivered(): 标记消息为已送达
   - mark_as_deleted(): 标记消息为已删除

3. 消息互动:
   - add_reaction(): 添加消息表情回应
   - remove_reaction(): 移除表情回应
   - get_reactions(): 获取表情回应
   - add_mention(): 添加@提醒
   - remove_mention(): 移除@提醒
   - get_mentions(): 获取@提醒列表
"""
"""消息仓储基类"""
# 标准库
from datetime import datetime
from typing import List, Optional, Dict, Any, cast, Sequence

# 第三方库
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

# 本地模块
from app.domain.common.models.tables import BaseMessage
from app.domain.common.enums.message import MessageStatus
from app.domain.base.internal.repository.base_repository import BaseRepository

import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

class BaseMessageRepository(BaseRepository[BaseMessage]):
    """基础消息仓储实现"""
    
    def __init__(self):
        """初始化消息仓储"""
        super().__init__(BaseMessage)
        lprint = LM.lprint
    
    async def save_message(self, message_data: Dict[str, Any]) -> BaseMessage:
        """保存消息
        
        Args:
            message_data: 消息数据字典
            
        Returns:
            BaseMessage: 保存后的消息
        """
        try:
            async with self.get_session() as session:
                # 创建消息实体
                # 删除id字段，让数据库自动生成
                message_data.pop('id', None)  # 使用pop并提供默认值None，这样即使id不存在也不会报错
                message = self.model(**message_data)
                
                # 保存到数据库
                session.add(message)
                await session.commit()
                await session.refresh(message)
                return message
            
        except Exception as e:
            lprint(f"保存消息失败: {str(e)}")
            raise
    
    async def get_messages(self, user_id: int, limit: int = 20) -> Sequence[BaseMessage]:
        """获取用户的消息列表
        
        Args:
            user_id: 用户ID
            limit: 限制返回的消息数量
            
        Returns:
            Sequence[BaseMessage]: 消息列表
        """
        stmt = select(self.model).where(
            or_(
                self.model.sender_id == user_id,
                self.model.recipient_id == user_id
            )
        ).order_by(desc(self.model.created_at)).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_many(self, message_ids: List[int]) -> List[BaseMessage]:
        """批量获取消息
        
        Args:
            message_ids: 消息ID列表
            
        Returns:
            List[BaseMessage]: 消息对象列表
        """
        stmt = select(self.model).where(self.model.id.in_(message_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def mark_as_read(self, message_id: int) -> bool:
        """标记消息为已读
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否成功
        """
        try:
            await self.update(
                message_id,
                status="read",
                read_at=datetime.now()
            )
            return True
        except Exception as e:
            lprint(f"标记消息已读失败: {str(e)}")
            return False
        
    async def mark_as_delivered(self, message_id: int) -> bool:
        """标记消息为已送达
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否成功
        """
        try:
            await self.update(
                message_id,
                status="delivered"
            )
            return True
        except Exception as e:
            lprint(f"标记消息已送达失败: {str(e)}")
            return False

    async def mark_as_deleted(self, message_id: int) -> bool:
        """标记消息为已删除
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否成功
        """
        try:
            await self.update(
                message_id,
                status="deleted",
                deleted_at=datetime.now()
            )
            return True
        except Exception as e:
            lprint(f"标记消息删除失败: {str(e)}")
            return False

    async def get_unread_messages(self, user_id: int) -> List[BaseMessage]:
        """获取用户的未读消息
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[BaseMessage]: 未读消息列表
        """
        stmt = select(self.model).where(
            and_(
                self.model.recipient_id == user_id,
                self.model.status != "read"
            )
        ).order_by(desc(self.model.created_at))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
