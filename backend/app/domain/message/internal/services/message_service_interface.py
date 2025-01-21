"""
消息服务接口
定义消息服务的抽象接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.message.models import Message
from app.domain.message.facade.dto.message_dto import MessageCreateDTO

class IMessageService(ABC):
    """消息服务接口定义"""
    
    @abstractmethod
    async def send(self, message: Message) -> Message:
        """发送消息
        
        Args:
            message: 消息实体
            
        Returns:
            Message: 发送成功的消息
        """
        pass
    
    @abstractmethod
    async def get_messages(self, user_id: str, group_id: Optional[str] = None) -> List[Message]:
        """获取消息列表
        
        Args:
            user_id: 用户ID
            group_id: 群组ID，如果为None则获取私聊消息
            
        Returns:
            List[Message]: 消息列表
        """
        pass
    
    @abstractmethod
    async def mark_as_read(self, message_id: str, user_id: str) -> bool:
        """标记消息为已读
        
        Args:
            message_id: 消息ID
            user_id: 用户ID
            
        Returns:
            bool: 是否标记成功
        """
        pass
