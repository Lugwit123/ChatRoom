"""
消息归档服务
处理消息的归档、清理和迁移
"""
import Lugwit_Module as LM
from datetime import datetime, timedelta
from typing import List, Optional
from ..models import Message
from ..repositories.group import GroupMessageRepository
from ..repositories.private import PrivateMessageRepository

class MessageArchiveService:
    """消息归档服务"""
    
    def __init__(self):
        self._group_repo = GroupMessageRepository()
        self._private_repo = PrivateMessageRepository()
        self.lprint = LM.lprint
        
    async def archive_old_messages(self, days: int = 30) -> int:
        """归档旧消息
        
        Args:
            days: 超过多少天的消息将被归档
            
        Returns:
            int: 归档的消息数量
        """
        try:
            archive_date = datetime.now() - timedelta(days=days)
            self.lprint(f"开始归档 {archive_date} 之前的消息")
            
            # 归档群组消息
            group_count = await self._group_repo.archive_messages(archive_date)
            # 归档私聊消息
            private_count = await self._private_repo.archive_messages(archive_date)
            
            total_count = group_count + private_count
            self.lprint(f"归档完成，共归档 {total_count} 条消息")
            return total_count
        except Exception as e:
            self.lprint(f"归档消息失败: {str(e)}")
            raise
            
    async def clean_archived_messages(self, days: int = 90) -> int:
        """清理已归档的旧消息
        
        Args:
            days: 清理超过多少天的已归档消息
            
        Returns:
            int: 清理的消息数量
        """
        try:
            clean_date = datetime.now() - timedelta(days=days)
            self.lprint(f"开始清理 {clean_date} 之前的已归档消息")
            
            # 清理群组消息
            group_count = await self._group_repo.clean_archived_messages(clean_date)
            # 清理私聊消息
            private_count = await self._private_repo.clean_archived_messages(clean_date)
            
            total_count = group_count + private_count
            self.lprint(f"清理完成，共清理 {total_count} 条消息")
            return total_count
        except Exception as e:
            self.lprint(f"清理归档消息失败: {str(e)}")
            raise
            
    async def restore_archived_message(self, message_id: str) -> Optional[Message]:
        """恢复已归档的消息
        
        Args:
            message_id: 消息ID
            
        Returns:
            Optional[Message]: 恢复的消息，如果不存在则返回None
        """
        try:
            # 尝试从群组消息中恢复
            message = await self._group_repo.restore_archived_message(message_id)
            if message:
                return message
                
            # 尝试从私聊消息中恢复
            return await self._private_repo.restore_archived_message(message_id)
        except Exception as e:
            self.lprint(f"恢复归档消息失败: {str(e)}")
            raise
