"""
消息操作模块
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Optional
from sqlalchemy import select, and_
from .schemas import (
    MessageStatus, MessageBase, MessageType, 
    MessageContentType, MessageTargetType,
    MessageResponse
)
from .db_connection import async_session

async def get_messages_by_target(
    target_type: MessageTargetType,
    target_id: str,
    limit: int = 50,
    before_id: Optional[int] = None
) -> List[MessageBase]:
    """获取指定目标的消息"""
    async with async_session() as session:
        stmt = select(MessageBase).where(
            and_(
                MessageBase.target_type == target_type,
                MessageBase.target_id == target_id
            )
        )
        if before_id:
            stmt = stmt.where(MessageBase.id < before_id)
        stmt = stmt.order_by(MessageBase.id.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

async def get_message_by_id(message_id: int) -> Optional[MessageBase]:
    """根据ID获取消息"""
    async with async_session() as session:
        stmt = select(MessageBase).where(MessageBase.id == message_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

async def insert_message(
    content: str,
    message_type: MessageType,
    sender: str,
    target_type: Optional[MessageTargetType] = None,
    target_id: Optional[str] = None,
    message_content_type: MessageContentType = MessageContentType.plain_text,
    popup_message: bool = False
) -> MessageBase:
    """插入消息到数据库"""
    async with async_session() as session:
        message = MessageBase(
            content=content,
            message_type=message_type,
            sender=sender,
            target_type=target_type,
            target_id=target_id,
            message_content_type=message_content_type,
            popup_message=popup_message,
            timestamp=datetime.now(ZoneInfo("Asia/Shanghai")),
            status=[MessageStatus.sent.value]  # 添加默认状态
        )
        session.add(message)
        await session.commit()
        await session.refresh(message)
        return message
