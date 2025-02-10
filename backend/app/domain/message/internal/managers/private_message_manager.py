"""
私聊消息管理器
提供私聊消息的管理功能,包括导出、备份、恢复、撤回和清理等
"""
import os
import json
from datetime import datetime, timedelta
import Lugwit_Module as LM

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.message.models import BaseMessage
from app.domain.message.enums import MessageType
from app.domain.message.internal.repository.base import BaseMessageRepository

class PrivateMessageManager(BaseMessageRepository):
    """私聊消息管理器
    
    提供私聊消息的管理功能,包括:
    - 导出私聊消息到JSON文件
    - 备份用户的所有私聊消息
    - 从备份文件恢复私聊消息
    - 撤回私聊消息(带权限和时间限制)
    - 清理过期的私聊消息
    """
    
    def __init__(self, session: AsyncSession):
        """初始化私聊消息管理器
        
        Args:
            session: 数据库会话
        """
        super().__init__(session)
        self.lprint = LM.lprint
        
    async def export_messages(self, user_id: int, other_id: int, export_dir: str) -> str:
        """导出指定用户与另一用户之间的私聊消息
        
        Args:
            user_id: 当前用户ID
            other_id: 对方用户ID
            export_dir: 导出目录
            
        Returns:
            str: 导出文件的路径
        """
        try:
            # 查询私聊消息
            stmt = select(Message).where(
                Message.type == MessageType.PRIVATE,
                ((Message.sender_id == user_id) & (Message.recipient_id == other_id)) |
                ((Message.sender_id == other_id) & (Message.recipient_id == user_id))
            ).order_by(Message.created_at)
            
            result = await self._session.execute(stmt)
            messages = result.scalars().all()
            
            # 转换为可序列化的格式
            message_list = []
            for msg in messages:
                message_list.append({
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "recipient_id": msg.recipient_id,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                })
            
            # 创建导出目录
            os.makedirs(export_dir, exist_ok=True)
            
            # 生成导出文件路径
            filename = f"private_chat_{user_id}_{other_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(export_dir, filename)
            
            # 写入文件
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(message_list, f, ensure_ascii=False, indent=2)
                
            self.lprint(f"成功导出私聊消息到文件: {filepath}")
            return filepath
            
        except Exception as e:
            self.lprint(f"导出私聊消息失败: {str(e)}")
            raise
            
    async def backup_messages(self, user_id: int, backup_dir: str) -> str:
        """备份用户的所有私聊消息
        
        Args:
            user_id: 用户ID
            backup_dir: 备份目录
            
        Returns:
            str: 备份文件的路径
        """
        try:
            # 查询该用户的所有私聊消息
            stmt = select(Message).where(
                Message.type == MessageType.PRIVATE,
                (Message.sender_id == user_id) | (Message.recipient_id == user_id)
            ).order_by(Message.created_at)
            
            result = await self._session.execute(stmt)
            messages = result.scalars().all()
            
            # 转换为可序列化的格式
            message_list = []
            for msg in messages:
                message_list.append({
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "recipient_id": msg.recipient_id,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                })
            
            # 创建备份目录
            os.makedirs(backup_dir, exist_ok=True)
            
            # 生成备份文件路径
            filename = f"private_messages_backup_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(backup_dir, filename)
            
            # 写入文件
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(message_list, f, ensure_ascii=False, indent=2)
                
            self.lprint(f"成功备份私聊消息到文件: {filepath}")
            return filepath
            
        except Exception as e:
            self.lprint(f"备份私聊消息失败: {str(e)}")
            raise
            
    async def restore_from_backup(self, backup_file: str) -> int:
        """从备份文件恢复私聊消息
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            int: 恢复的消息数量
        """
        try:
            # 读取备份文件
            with open(backup_file, "r", encoding="utf-8") as f:
                messages = json.load(f)
            
            # 恢复消息
            count = 0
            for msg_data in messages:
                msg = Message(
                    sender_id=msg_data["sender_id"],
                    recipient_id=msg_data["recipient_id"],
                    content=msg_data["content"],
                    type=MessageType.PRIVATE,
                    created_at=datetime.fromisoformat(msg_data["created_at"])
                )
                self._session.add(msg)
                count += 1
            
            await self._session.commit()
            self.lprint(f"成功恢复 {count} 条私聊消息")
            return count
            
        except Exception as e:
            self.lprint(f"恢复私聊消息失败: {str(e)}")
            raise
            
    async def recall_message(self, message_id: int, user_id: int) -> bool:
        """撤回私聊消息
        
        Args:
            message_id: 消息ID
            user_id: 请求撤回的用户ID
            
        Returns:
            bool: 是否撤回成功
        """
        try:
            # 查询消息
            stmt = select(Message).where(
                Message.id == message_id,
                Message.type == MessageType.PRIVATE,
                Message.sender_id == user_id
            )
            result = await self._session.execute(stmt)
            message = result.scalar_one_or_none()
            
            if not message:
                self.lprint(f"消息不存在或无权撤回")
                return False
                
            # 检查撤回时间限制(2分钟内)
            if datetime.now() - message.created_at > timedelta(minutes=2):
                self.lprint(f"消息发送超过2分钟,无法撤回")
                return False
                
            # 删除消息
            await self._session.delete(message)
            await self._session.commit()
            
            self.lprint(f"成功撤回消息: {message_id}")
            return True
            
        except Exception as e:
            self.lprint(f"撤回消息失败: {str(e)}")
            raise
            
    async def clean_messages(self, user_id: int, days: int) -> int:
        """清理指定天数前的私聊消息
        
        Args:
            user_id: 用户ID
            days: 保留天数
            
        Returns:
            int: 清理的消息数量
        """
        try:
            # 计算清理时间点
            clean_before = datetime.now() - timedelta(days=days)
            
            # 查询需要清理的消息
            stmt = select(Message).where(
                Message.type == MessageType.PRIVATE,
                (Message.sender_id == user_id) | (Message.recipient_id == user_id),
                Message.created_at < clean_before
            )
            result = await self._session.execute(stmt)
            messages = result.scalars().all()
            
            # 删除消息
            count = 0
            for msg in messages:
                await self._session.delete(msg)
                count += 1
            
            await self._session.commit()
            self.lprint(f"成功清理 {count} 条私聊消息")
            return count
            
        except Exception as e:
            self.lprint(f"清理私聊消息失败: {str(e)}")
            raise
