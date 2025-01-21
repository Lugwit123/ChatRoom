"""
消息服务实现
处理消息的发送、接收、查询等业务逻辑
"""
import Lugwit_Module as LM
from typing import List, Optional
from .message_service_interface import IMessageService
from ..models import Message
from ..repositories.base import MessageRepository
from ..repositories.group import GroupMessageRepository
from ..repositories.private import PrivateMessageRepository

class MessageService(IMessageService):
    """消息服务实现类"""
    
    def __init__(self):
        self.lprint = LM.lprint
        self._group_repo = GroupMessageRepository()
        self._private_repo = PrivateMessageRepository()
    
    async def send(self, message: Message) -> Message:
        """发送消息
        
        Args:
            message: 消息实体
            
        Returns:
            Message: 发送成功的消息
        
        Raises:
            ValueError: 当消息格式不正确时
        """
        try:
            if message.group_id:
                self.lprint(f"发送群组消息: {message.content} 到群组 {message.group_id}")
                return await self._group_repo.save_message(message)
            else:
                self.lprint(f"发送私聊消息: {message.content} 到用户 {message.receiver_id}")
                return await self._private_repo.save_message(message)
        except Exception as e:
            self.lprint(f"发送消息失败: {str(e)}")
            raise
    
    async def get_messages(self, user_id: str, group_id: Optional[str] = None) -> List[Message]:
        """获取消息列表
        
        Args:
            user_id: 用户ID
            group_id: 群组ID，如果为None则获取私聊消息
            
        Returns:
            List[Message]: 消息列表
        """
        try:
            if group_id:
                self.lprint(f"获取群组 {group_id} 的消息")
                return await self._group_repo.get_messages(group_id)
            else:
                self.lprint(f"获取用户 {user_id} 的私聊消息")
                return await self._private_repo.get_messages(user_id)
        except Exception as e:
            self.lprint(f"获取消息列表失败: {str(e)}")
            raise
    
    async def mark_as_read(self, message_id: str, user_id: str) -> bool:
        """标记消息为已读
        
        Args:
            message_id: 消息ID
            user_id: 用户ID
            
        Returns:
            bool: 是否标记成功
        """
        try:
            # 先尝试标记私聊消息
            if await self._private_repo.mark_as_read(message_id, user_id):
                return True
            # 如果不是私聊消息，尝试标记群组消息
            return await self._group_repo.mark_as_read(message_id, user_id)
        except Exception as e:
            self.lprint(f"标记消息已读失败: {str(e)}")
            raise
