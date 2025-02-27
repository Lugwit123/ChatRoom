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
    recipient: str
    other_username: str

class PrivateMessageRepository(BaseMessageRepository):
    """私聊消息仓储实现"""
    
    def __init__(self):
        """初始化私聊消息仓储"""
        super().__init__()
        self.model = PrivateMessage
        
    async def save_message(self, message_data: Dict[str, Any]) -> PrivateMessage:
        """保存或更新私聊消息
        
        Args:
            message_data: 消息数据字典，如果包含 id 字段且不为 '-1'，则更新已存在的消息
            
        Returns:
            PrivateMessage: 保存或更新的消息
        """
        try:
            message_id = int(message_data.get('id'))
            
            # 如果消息ID存在且不是'-1'，则更新消息
            if message_id != -1 :
                # 确保ID是整数类型
                try:
                    if isinstance(message_id, str):
                        message_id = int(message_id)
                    # 使用CoreRepository中的get_by_id方法查询现有消息
                    existing_message = await self.get_by_id(message_id)
                    lprint(f"查询结果: {existing_message}")
                    
                    if existing_message:
                        async with self.transaction() as session:
                            # 更新消息内容
                            for key, value in message_data.items():
                                # 排除id、发送者ID和接收者ID，这些字段不应该被修改
                                if key != 'id' and key != 'sender_id' and key != 'recipient_id' and hasattr(existing_message, key):
                                    lprint(f"更新字段 {key}: {value}")
                                    setattr(existing_message, key, value)
                            
                            # 更新修改时间
                            existing_message.updated_at = datetime.now(ZoneInfo('Asia/Shanghai'))
                            
                            # 使用merge而不是add，避免主键冲突
                            merged_message = await session.merge(existing_message)
                            
                            # 刷新以获取最新状态
                            await session.flush()
                            
                            # 返回合并后的对象
                            return merged_message
                except ValueError as e:
                    lprint(f"ID转换错误: {e}")
                except Exception as e:
                    lprint(f"查询或更新消息时出错: {e}")
                    traceback.print_exc()
            
            # 如果消息不存在或ID为'-1'，则创建新消息
            lprint("创建新消息")
            return await super().save_message(message_data)
            
        except Exception as e:
            lprint(f"保存或更新私聊消息失败: {str(e)}")
            traceback.print_exc()
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

            # 查询用户作为发送者的所有私聊消息的接收者
            query = select(PrivateMessage.recipient_id).where(
                PrivateMessage.sender_id == user_id
            ).distinct()
            
            # 查询用户作为接收者的所有私聊消息的发送者
            query2 = select(PrivateMessage.sender_id).where(
                PrivateMessage.recipient_id == user_id
            ).distinct()
            
            # 执行查询
            result1 = await self.session.execute(query)
            result2 = await self.session.execute(query2)
            
            # 获取所有不重复的用户ID
            partner_ids = set()
            for row in result1:
                partner_ids.add(row[0])
            for row in result2:
                partner_ids.add(row[0])
                
            lprint(f"用户 {user_id} 的聊天伙伴: {partner_ids}")
            return list(partner_ids)
                
        except Exception as e:
            lprint(f"获取聊天伙伴失败: {str(e)}")
            traceback.print_exc()
            return []

    async def mark_as_unread(self, message_id: int) -> bool:
        """标记消息为未读
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否成功
        """
        try:
            # 更新消息状态为未读
            result = await self.session.execute(
                update(PrivateMessage)
                .where(PrivateMessage.id == message_id)
                .values(status=MessageStatus.unread.value)
            )
            await self.session.commit()
            return bool(result.rowcount > 0)
        except Exception as e:
            lprint(f"标记私聊消息未读失败: {str(e)}")
            traceback.print_exc()
            return False
