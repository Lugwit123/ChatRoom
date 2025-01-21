"""
消息DTO模块
定义所有与消息相关的数据传输对象
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ...internal.models import Message

class MessageCreateDTO(BaseModel):
    """消息创建DTO
    
    用于创建新消息时的数据传输
    """
    content: str
    sender_id: str
    receiver_id: Optional[str]
    group_id: Optional[str]
    
    def to_internal(self) -> Message:
        """转换为内部消息模型"""
        return Message(
            content=self.content,
            sender_id=self.sender_id,
            receiver_id=self.receiver_id,
            group_id=self.group_id,
            created_at=datetime.now()
        )

class MessageDTO(BaseModel):
    """消息DTO
    
    用于消息数据的传输展示
    """
    id: str
    content: str
    sender_id: str
    receiver_id: Optional[str]
    group_id: Optional[str]
    created_at: datetime
    read_at: Optional[datetime]
    
    @classmethod
    def from_internal(cls, message: Message) -> "MessageDTO":
        """从内部消息模型创建DTO"""
        return cls(
            id=message.id,
            content=message.content,
            sender_id=message.sender_id,
            receiver_id=message.receiver_id,
            group_id=message.group_id,
            created_at=message.created_at,
            read_at=message.read_at
        )
