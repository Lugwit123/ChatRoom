"""消息仓储基类"""
# 标准库
from abc import ABC, abstractmethod
from typing import List, Optional, Union, Sequence
from datetime import datetime

# 本地模块
from app.domain.message.enums import MessageStatus, MessageType
from app.domain.message.models import GroupMessage, PrivateMessage

class BaseMessageRepository(ABC):
    """消息仓储基类接口定义
    
    所有消息仓储实现都必须继承此基类并实现其抽象方法。
    """
    
    @abstractmethod
    async def save_message(self, message) -> str:
        """保存消息
        
        Args:
            message: 消息对象
            
        Returns:
            str: 消息的公开 ID
        """
        pass
    
    @abstractmethod
    async def get_message_by_public_id(self, public_id: str):
        """通过公开 ID 获取消息
        
        Args:
            public_id: 消息的公开 ID
            
        Returns:
            消息对象
        """
        pass
    
    @abstractmethod
    async def get_messages(self, 
                          user_id: str, 
                          limit: int = 50, 
                          before_timestamp: Optional[int] = None,
                          message_type: Optional[MessageType] = None) -> List:
        """获取消息列表
        
        Args:
            user_id: 用户ID
            limit: 返回消息数量限制
            before_timestamp: 获取此时间戳之前的消息
            message_type: 消息类型
            
        Returns:
            List: 消息对象列表
        """
        pass
    
    @abstractmethod
    async def mark_as_read(self, public_id: str) -> bool:
        """标记消息为已读
        
        Args:
            public_id: 消息的公开 ID
            
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    async def delete_message(self, public_id: str) -> bool:
        """删除消息
        
        Args:
            public_id: 消息的公开 ID
            
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    async def update_message_status(self, public_id: str, status: MessageStatus) -> bool:
        """更新消息状态
        
        Args:
            public_id: 消息的公开 ID
            status: 新状态
            
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    async def get_unread_count(self, user_id: str) -> int:
        """获取未读消息数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 未读消息数量
        """
        pass
