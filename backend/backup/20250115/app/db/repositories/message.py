"""消息仓储类"""
from typing import Optional, List, Union, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, and_, or_, text
from zoneinfo import ZoneInfo
import traceback

from app.db.schemas import (
    PrivateMessage, MessageCreate, MessageType, 
    MessageContentType, MessageStatus, MessageTargetType, User,
    create_group_message_table, MessageTypeModel,
    MessageContentTypeModel, Group
)
import Lugwit_Module as LM

lprint = LM.lprint

def get_group_message_table_name(group_id: int) -> str:
    return f"group_message_{group_id}"

class MessageRepository:
    """消息仓储类，提供消息相关的数据库操作方法"""
    
    def __init__(self):
        pass
    
    async def create_message(
        self,
        session: AsyncSession,
        *,
        content: str,
        message_type: MessageType,
        sender: str,
        target_type: Optional[MessageTargetType] = None,
        target_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        popup_message: bool = False,
        message_content_type: MessageContentType = MessageContentType.plain_text
    ) -> PrivateMessage:
        """创建新消息"""
        try:
            if not created_at:
                created_at = datetime.now(ZoneInfo("Asia/Shanghai"))
            
            # 获取消息类型ID
            message_type_stmt = select(MessageTypeModel).where(
                MessageTypeModel.type_code == message_type.value
            )
            message_type_result = await session.execute(message_type_stmt)
            message_type_obj = message_type_result.scalar_one_or_none()
            if not message_type_obj:
                raise ValueError(f"找不到消息类型: {message_type.value}")
                
            # 获取消息内容类型ID
            content_type_stmt = select(MessageContentTypeModel).where(
                MessageContentTypeModel.type_code == message_content_type.value
            )
            content_type_result = await session.execute(content_type_stmt)
            content_type_obj = content_type_result.scalar_one_or_none()
            if not content_type_obj:
                raise ValueError(f"找不到消息内容类型: {message_content_type.value}")
            
            # 验证目标类型和ID
            if message_type in [MessageType.private_chat, MessageType.group_chat]:
                if not target_type or not target_id:
                    raise ValueError(f"{message_type.value} 类型消息必须指定目标类型和目标ID")
            else:
                # 系统消息和广播消息不需要目标
                target_type = None
                target_id = None
            
            # 创建消息对象
            message = PrivateMessage(
                content=content,
                message_type_id=message_type_obj.id,
                sender=sender,
                target_type=target_type.value if target_type else None,
                target_id=target_id,
                created_at=created_at,
                popup_message=popup_message,
                message_content_type_id=content_type_obj.id,
                status=[MessageStatus.sent.value]
            )
            
            session.add(message)
            await session.commit()
            await session.refresh(message)
            
            # 根据消息类型记录不同的日志
            if target_type:
                lprint(f"消息创建成功: sender={sender}, target={target_type.value}:{target_id}")
            else:
                lprint(f"{message_type.value}消息创建成功: sender={sender}")
                
            return message
            
        except Exception as e:
            lprint(f"创建消息失败: {str(e)}")
            lprint(traceback.format_exc())
            await session.rollback()
            raise
            
    async def get_messages(
        self,
        session: AsyncSession,
        *,
        group_id: int,
        limit: int = 50
    ) -> List[PrivateMessage]:
        """获取消息列表"""
        try:
            # 获取消息表名
            table_name = get_group_message_table_name(group_id)
            
            # 查询消息
            query = text(f"""
                SELECT m.*, u.username as sender_name, u.nickname as sender_nickname
                FROM {table_name} m
                LEFT JOIN users u ON m.sender_id = u.id
                ORDER BY m.timestamp DESC
                LIMIT :limit
            """)
            
            result = await session.execute(query, {"limit": limit})
            messages = result.mappings().all()
            return list(messages)
            
        except Exception as e:
            lprint(f"获取消息失败: {str(e)}")
            lprint(traceback.format_exc())
            raise
            
    async def create_group_message(
        self,
        session: AsyncSession,
        *,
        content: str,
        sender: str,
        group_id: int,
        created_at: Optional[datetime] = None,
        popup_message: bool = False
    ):
        """创建群组消息"""
        try:
            if not created_at:
                created_at = datetime.now(ZoneInfo("Asia/Shanghai"))
            
            # 获取发送者ID
            sender_result = await session.execute(
                select(User).where(User.username == sender)
            )
            sender_user = sender_result.scalar_one()
            
            # 获取消息类型ID
            message_type_result = await session.execute(
                select(MessageTypeModel).where(
                    MessageTypeModel.type_code == MessageType.group_chat.value
                )
            )
            message_type = message_type_result.scalar_one()
            
            # 获取消息内容类型ID
            content_type_result = await session.execute(
                select(MessageContentTypeModel).where(
                    MessageContentTypeModel.type_code == MessageContentType.plain_text.value
                )
            )
            content_type = content_type_result.scalar_one()
            
            # 创建消息表名
            table_name = get_group_message_table_name(group_id)
            
            # 插入消息
            query = text(f"""
                INSERT INTO {table_name} (
                    content, sender_id, recipient_type, recipient, group_id,
                    timestamp, message_type_id, message_content_type_id,
                    status, popup_message, extra_data
                ) VALUES (
                    :content, :sender_id, :recipient_type, :recipient, :group_id,
                    :timestamp, :message_type_id, :message_content_type_id,
                    :status, :popup_message, :extra_data
                ) RETURNING id
            """)
            
            result = await session.execute(
                query,
                {
                    "content": content,
                    "sender_id": sender_user.id,
                    "recipient_type": MessageTargetType.group.value,
                    "recipient": group_id,
                    "group_id": group_id,
                    "timestamp": created_at,
                    "message_type_id": message_type.id,
                    "message_content_type_id": content_type.id,
                    "status": [MessageStatus.unread.value],
                    "popup_message": popup_message,
                    "extra_data": "{}"
                }
            )
            
            await session.commit()
            message_id = result.scalar_one()
            
            return message_id
        except Exception as e:
            lprint(f"创建群组消息失败: {traceback.format_exc()}")
            raise

    async def get_group_messages(
        self,
        session: AsyncSession,
        group_id: int,
        limit: int = 100
    ):
        """获取群组消息"""
        try:
            # 获取消息表名
            table_name = get_group_message_table_name(group_id)
            
            # 查询消息
            query = text(f"""
                SELECT m.*, u.username as sender_name, u.nickname as sender_nickname
                FROM {table_name} m
                LEFT JOIN users u ON m.sender_id = u.id
                ORDER BY m.timestamp DESC
                LIMIT :limit
            """)
            
            result = await session.execute(query, {"limit": limit})
            messages = result.mappings().all()
            
            return messages
        except Exception as e:
            lprint(f"获取群组消息失败: {traceback.format_exc()}")
            raise

    async def get_private_messages(
        self,
        session: AsyncSession,
        user1: str,
        user2: str,
        limit: int = 100,
        before_id: Optional[int] = None,
        after_id: Optional[int] = None
    ) -> List[PrivateMessage]:
        """获取两个用户之间的私聊消息
        
        Args:
            session: 数据库会话
            user1: 用户1
            user2: 用户2
            limit: 返回的最大消息数量
            before_id: 获取ID小于此值的消息（向前翻页）
            after_id: 获取ID大于此值的消息（向后翻页）
        """
        try:
            # 基础查询
            query = (
                select(PrivateMessage)
                .where(
                    or_(
                        and_(
                            PrivateMessage.sender == user1,
                            PrivateMessage.target_id == user2,
                            PrivateMessage.target_type == MessageTargetType.user.value
                        ),
                        and_(
                            PrivateMessage.sender == user2,
                            PrivateMessage.target_id == user1,
                            PrivateMessage.target_type == MessageTargetType.user.value
                        )
                    )
                )
            )

            # 添加分页条件
            if before_id is not None:
                query = query.where(PrivateMessage.id < before_id)
            elif after_id is not None:
                query = query.where(PrivateMessage.id > after_id)
                query = query.order_by(PrivateMessage.created_at.asc())
            else:
                query = query.order_by(PrivateMessage.created_at.desc())

            # 限制返回数量
            query = query.limit(limit)

            # 执行查询
            result = await session.execute(query)
            messages = result.scalars().all()

            # 如果是向后翻页，需要反转结果顺序
            if after_id is not None:
                messages = list(reversed(messages))

            return messages

        except Exception as e:
            lprint(f"获取私聊消息失败: {traceback.format_exc()}")
            raise

    async def get_all_group_messages_dict(
        self,
        session: AsyncSession,
        groups: List[int],
        limit: int = 100
    ) -> Dict[int, List[Any]]:
        """获取所有群组的消息字典"""
        messages_dict = {}
        for group_id in groups:
            messages = await self.get_group_messages(session, group_id, limit)
            messages_dict[group_id] = messages
        return messages_dict
        
    async def get_chat_history(
        self,
        session: AsyncSession,
        *,
        user1: str,
        user2: str,
        limit: int = 100
    ) -> List[PrivateMessage]:
        """获取两个用户之间的聊天历史记录"""
        try:
            # 构建查询语句
            stmt = select(PrivateMessage).where(
                or_(
                    and_(
                        PrivateMessage.sender == user1,
                        PrivateMessage.target_id == user2,
                        PrivateMessage.target_type == MessageTargetType.user.value
                    ),
                    and_(
                        PrivateMessage.sender == user2,
                        PrivateMessage.target_id == user1,
                        PrivateMessage.target_type == MessageTargetType.user.value
                    )
                )
            ).order_by(PrivateMessage.created_at.desc()).limit(limit)
            
            result = await session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            lprint(f"获取聊天历史记录失败: {str(e)}")
            lprint(traceback.format_exc())
            raise
