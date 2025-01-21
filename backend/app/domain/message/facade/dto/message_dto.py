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
