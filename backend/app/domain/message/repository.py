"""消息仓储外观类"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from datetime import datetime
from typing import List, Optional, Union, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.message.enums import MessageType, MessageStatus
from app.domain.message.repositories import GroupMessageRepository, PrivateMessageRepository
from app.db import DatabaseManager

class MessageRepository:
    """消息仓储，整合群组消息和私聊消息的仓储
    
    这是一个外观类，它封装了群组消息和私聊消息的具体实现，
    为上层提供统一的接口。
    """

    def __init__(self):
        """初始化消息仓储"""
        session = DatabaseManager.get_session()
        self.private_repository = PrivateMessageRepository(session)
        self._group_repositories: Dict[str, GroupMessageRepository] = {}
        self._session = session

    def _get_group_repository(self, group_id: str) -> GroupMessageRepository:
        """获取群组消息仓储
        
        如果指定群组的仓储不存在，则创建一个新的实例。
        
        Args:
            group_id: 群组ID
        """
        if group_id not in self._group_repositories:
            self._group_repositories[group_id] = GroupMessageRepository(self._session)
        return self._group_repositories[group_id]

    async def save_message(self, message) -> str:
        """保存消息
        
        根据消息类型选择合适的仓储进行保存。
        
        Args:
            message: 消息对象
            
        Returns:
            str: 消息ID
            
        Raises:
            ValueError: 消息类型无效
        """
        if message.message_type == MessageType.group_chat:
            repo = self._get_group_repository(message.group_id)
            return await repo.save_message(message)
        elif message.message_type == MessageType.private_chat:
            return await self.private_repository.save_message(message)
        else:
            raise ValueError(f"不支持的消息类型: {message.message_type}")

    async def get_message(self, message_id: str, message_type: MessageType, group_id: Optional[str] = None):
        """获取消息
        
        Args:
            message_id: 消息ID
            message_type: 消息类型
            group_id: 群组ID（群聊消息必需）
            
        Returns:
            消息对象
            
        Raises:
            ValueError: 消息类型无效
        """
        if message_type == MessageType.group_chat:
            if not group_id:
                raise ValueError("获取群聊消息必须提供群组ID")
            repo = self._get_group_repository(group_id)
            return await repo.get_message(message_id)
        elif message_type == MessageType.private_chat:
            return await self.private_repository.get_message(message_id)
        else:
            raise ValueError(f"不支持的消息类型: {message_type}")

    async def get_messages(self, 
                          user_id: str, 
                          message_type: Optional[MessageType] = None,
                          group_id: Optional[str] = None,
                          limit: int = 50,
                          before: Optional[datetime] = None) -> List:
        """获取消息列表
        
        Args:
            user_id: 用户ID
            message_type: 消息类型，如果为None则获取所有类型
            group_id: 群组ID（获取群聊消息时必需）
            limit: 返回消息数量限制
            before: 获取此时间之前的消息
            
        Returns:
            List: 消息对象列表
        """
        if message_type == MessageType.group_chat:
            if not group_id:
                raise ValueError("获取群聊消息必须提供群组ID")
            repo = self._get_group_repository(group_id)
            return await repo.get_messages(user_id, limit, before)
        elif message_type == MessageType.private_chat:
            return await self.private_repository.get_messages(user_id, limit, before)
        else:
            # 获取所有类型的消息
            private_messages = await self.private_repository.get_messages(user_id, limit, before)
            
            # 如果指定了群组，只获取该群组的消息
            if group_id:
                repo = self._get_group_repository(group_id)
                group_messages = await repo.get_messages(user_id, limit, before)
            else:
                # 否则获取所有群组的消息
                group_messages = []
                for repo in self._group_repositories.values():
                    messages = await repo.get_messages(user_id, limit, before)
                    group_messages.extend(messages)
            
            # 合并并按时间排序
            all_messages = private_messages + group_messages
            return sorted(all_messages, 
                        key=lambda x: x.created_at, 
                        reverse=True)[:limit]

    async def mark_as_read(self, message_id: str, message_type: MessageType, group_id: Optional[str] = None) -> bool:
        """标记消息为已读
        
        Args:
            message_id: 消息ID
            message_type: 消息类型
            group_id: 群组ID（群聊消息必需）
            
        Returns:
            bool: 是否成功
            
        Raises:
            ValueError: 消息类型无效
        """
        if message_type == MessageType.group_chat:
            if not group_id:
                raise ValueError("标记群聊消息必须提供群组ID")
            repo = self._get_group_repository(group_id)
            return await repo.mark_as_read(message_id)
        elif message_type == MessageType.private_chat:
            return await self.private_repository.mark_as_read(message_id)
        else:
            raise ValueError(f"不支持的消息类型: {message_type}")

    async def delete_message(self, message_id: str, message_type: MessageType, group_id: Optional[str] = None) -> bool:
        """删除消息
        
        Args:
            message_id: 消息ID
            message_type: 消息类型
            group_id: 群组ID（群聊消息必需）
            
        Returns:
            bool: 是否成功
            
        Raises:
            ValueError: 消息类型无效
        """
        if message_type == MessageType.group_chat:
            if not group_id:
                raise ValueError("删除群聊消息必须提供群组ID")
            repo = self._get_group_repository(group_id)
            return await repo.delete_message(message_id)
        elif message_type == MessageType.private_chat:
            return await self.private_repository.delete_message(message_id)
        else:
            raise ValueError(f"不支持的消息类型: {message_type}")

    async def update_message_status(self, 
                                  message_id: str, 
                                  status: MessageStatus,
                                  message_type: MessageType,
                                  group_id: Optional[str] = None) -> bool:
        """更新消息状态
        
        Args:
            message_id: 消息ID
            status: 新状态
            message_type: 消息类型
            group_id: 群组ID（群聊消息必需）
            
        Returns:
            bool: 是否成功
            
        Raises:
            ValueError: 消息类型无效
        """
        if message_type == MessageType.group_chat:
            if not group_id:
                raise ValueError("更新群聊消息状态必须提供群组ID")
            repo = self._get_group_repository(group_id)
            return await repo.update_message_status(message_id, status)
        elif message_type == MessageType.private_chat:
            return await self.private_repository.update_message_status(message_id, status)
        else:
            raise ValueError(f"不支持的消息类型: {message_type}")

    async def get_unread_count(self, user_id: str, message_type: Optional[MessageType] = None, group_id: Optional[str] = None) -> int:
        """获取未读消息数量
        
        Args:
            user_id: 用户ID
            message_type: 消息类型，如果为None则获取所有类型
            group_id: 群组ID（获取群聊消息时可选）
            
        Returns:
            int: 未读消息数量
        """
        if message_type == MessageType.group_chat:
            if group_id:
                # 获取指定群组的未读消息数量
                repo = self._get_group_repository(group_id)
                return await repo.get_unread_count(user_id)
            else:
                # 获取所有群组的未读消息数量
                total = 0
                for repo in self._group_repositories.values():
                    count = await repo.get_unread_count(user_id)
                    total += count
                return total
        elif message_type == MessageType.private_chat:
            return await self.private_repository.get_unread_count(user_id)
        else:
            # 获取所有类型的未读消息数量
            private_count = await self.private_repository.get_unread_count(user_id)
            
            # 获取所有群组的未读消息数量
            group_count = 0
            if group_id:
                # 如果指定了群组，只获取该群组的未读消息数量
                repo = self._get_group_repository(group_id)
                group_count = await repo.get_unread_count(user_id)
            else:
                # 否则获取所有群组的未读消息数量
                for repo in self._group_repositories.values():
                    count = await repo.get_unread_count(user_id)
                    group_count += count
                    
            return private_count + group_count

    async def get_chat_history(self, 
                             user1_id: str, 
                             user2_id: str,
                             limit: int = 50,
                             before: Optional[datetime] = None) -> List:
        """获取两个用户之间的聊天历史
        
        这个方法只对私聊消息有效。
        
        Args:
            user1_id: 用户1 ID
            user2_id: 用户2 ID
            limit: 返回消息数量限制
            before: 获取此时间之前的消息
            
        Returns:
            List: 消息对象列表
        """
        return await self.private_repository.get_chat_history(
            user1_id, user2_id, limit, before
        )

    async def close(self):
        """关闭数据库会话"""
        await self._session.close()
