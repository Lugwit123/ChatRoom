"""群消息工具类"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
from app.core.config import settings
from app.domain.message.models import create_group_message_table, MessageStatus

class GroupMessageUtils:
    """群消息工具类，用于处理消息恢复、导出和备份"""
    
    def __init__(self, group_id: str):
        """初始化群消息工具类
        
        Args:
            group_id: 群组ID
        """
        self.group_id = group_id
        self.message_class = create_group_message_table(group_id)
        self.backup_dir = os.path.join(settings.DATA_DIR, "backups", "messages", group_id)
        self.export_dir = os.path.join(settings.DATA_DIR, "exports", "messages", group_id)
        
        # 创建必要的目录
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)
    
    async def restore_messages(
        self,
        session: AsyncSession,
        message_ids: List[str]
    ) -> Dict[str, int]:
        """恢复已删除的消息
        
        Args:
            session: 数据库会话
            message_ids: 要恢复的消息ID列表
            
        Returns:
            Dict[str, int]: 恢复结果统计
        """
        try:
            # 获取要恢复的消息
            messages = await session.execute(
                select(self.message_class).where(
                    self.message_class.public_id.in_(message_ids),
                    self.message_class.is_deleted == True
                )
            )
            messages = messages.scalars().all()
            
            restored_count = 0
            for msg in messages:
                msg.is_deleted = False
                msg.delete_at = None
                restored_count += 1
            
            await session.commit()
            return {"restored_messages": restored_count}
            
        except Exception as e:
            lprint(f"恢复消息失败: {traceback.format_exc()}")
            raise
    
    async def export_messages(
        self,
        session: AsyncSession,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        include_deleted: bool = False
    ) -> str:
        """导出消息
        
        Args:
            session: 数据库会话
            format: 导出格式 (json 或 csv)
            start_time: 开始时间
            end_time: 结束时间
            include_deleted: 是否包含已删除消息
            
        Returns:
            str: 导出文件路径
        """
        try:
            # 构建查询
            query = select(self.message_class)
            
            if not include_deleted:
                query = query.where(self.message_class.is_deleted == False)
            
            if start_time:
                query = query.where(self.message_class.created_at >= start_time)
            if end_time:
                query = query.where(self.message_class.created_at <= end_time)
            
            # 获取消息
            messages = await session.execute(query)
            messages = messages.scalars().all()
            
            # 准备导出数据
            export_data = []
            for msg in messages:
                msg_data = {
                    "id": msg.public_id,
                    "content": msg.content,
                    "sender_id": msg.sender_id,
                    "content_type": msg.content_type.value,
                    "status": msg.status.value,
                    "created_at": msg.created_at.isoformat(),
                    "updated_at": msg.updated_at.isoformat(),
                    "is_deleted": msg.is_deleted,
                    "delete_at": msg.delete_at.isoformat() if msg.delete_at else None,
                    "reply_to_id": msg.reply_to_id,
                    "forward_from_id": msg.forward_from_id,
                    "extra_data": msg.extra_data
                }
                export_data.append(msg_data)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"messages_export_{timestamp}.{format}"
            filepath = os.path.join(self.export_dir, filename)
            
            # 写入文件
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                if format == "json":
                    await f.write(json.dumps(export_data, ensure_ascii=False, indent=2))
                else:  # csv
                    # 获取所有字段
                    fieldnames = export_data[0].keys() if export_data else []
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    await f.write("\ufeff")  # BOM for Excel
                    writer.writeheader()
                    for row in export_data:
                        writer.writerow(row)
            
            return filepath
            
        except Exception as e:
            lprint(f"导出消息失败: {traceback.format_exc()}")
            raise
    
    async def backup_messages(
        self,
        session: AsyncSession,
        include_deleted: bool = True,
        include_archived: bool = True
    ) -> str:
        """备份消息
        
        Args:
            session: 数据库会话
            include_deleted: 是否包含已删除消息
            include_archived: 是否包含已归档消息
            
        Returns:
            str: 备份文件路径
        """
        try:
            backup_data = {
                "group_id": self.group_id,
                "backup_time": datetime.now().isoformat(),
                "messages": [],
                "archived_messages": [] if include_archived else None
            }
            
            # 获取主表消息
            query = select(self.message_class)
            if not include_deleted:
                query = query.where(self.message_class.is_deleted == False)
            
            messages = await session.execute(query)
            messages = messages.scalars().all()
            
            for msg in messages:
                msg_data = {
                    "id": msg.public_id,
                    "content": msg.content,
                    "sender_id": msg.sender_id,
                    "content_type": msg.content_type.value,
                    "status": msg.status.value,
                    "created_at": msg.created_at.isoformat(),
                    "updated_at": msg.updated_at.isoformat(),
                    "is_deleted": msg.is_deleted,
                    "delete_at": msg.delete_at.isoformat() if msg.delete_at else None,
                    "reply_to_id": msg.reply_to_id,
                    "forward_from_id": msg.forward_from_id,
                    "extra_data": msg.extra_data,
                    "reactions": [
                        {
                            "user_id": r.user_id,
                            "reaction": r.reaction,
                            "created_at": r.created_at.isoformat()
                        }
                        for r in msg.reactions
                    ],
                    "mentions": [
                        {
                            "user_id": m.user_id,
                            "created_at": m.created_at.isoformat()
                        }
                        for m in msg.mentions
                    ]
                }
                backup_data["messages"].append(msg_data)
            
            # 获取归档表消息
            if include_archived:
                archive_class = self.message_class.get_archive_class()
                archived_messages = await session.execute(select(archive_class))
                archived_messages = archived_messages.scalars().all()
                
                for msg in archived_messages:
                    msg_data = {
                        "id": msg.public_id,
                        "content": msg.content,
                        "sender_id": msg.sender_id,
                        "content_type": msg.content_type.value,
                        "status": msg.status.value,
                        "created_at": msg.created_at.isoformat(),
                        "updated_at": msg.updated_at.isoformat(),
                        "is_deleted": msg.is_deleted,
                        "delete_at": msg.delete_at.isoformat() if msg.delete_at else None,
                        "reply_to_id": msg.reply_to_id,
                        "forward_from_id": msg.forward_from_id,
                        "extra_data": msg.extra_data,
                        "archive_time": msg.archive_time.isoformat(),
                        "original_id": msg.original_id
                    }
                    backup_data["archived_messages"].append(msg_data)
            
            # 生成备份文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"messages_backup_{timestamp}.json"
            filepath = os.path.join(self.backup_dir, filename)
            
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(json.dumps(backup_data, ensure_ascii=False, indent=2))
            
            return filepath
            
        except Exception as e:
            lprint(f"备份消息失败: {traceback.format_exc()}")
            raise
    
    async def restore_from_backup(
        self,
        session: AsyncSession,
        backup_file: str,
        restore_deleted: bool = True,
        restore_archived: bool = True
    ) -> Dict[str, int]:
        """从备份文件恢复消息
        
        Args:
            session: 数据库会话
            backup_file: 备份文件路径
            restore_deleted: 是否恢复已删除消息
            restore_archived: 是否恢复已归档消息
            
        Returns:
            Dict[str, int]: 恢复结果统计
        """
        try:
            # 读取备份文件
            async with aiofiles.open(backup_file, "r", encoding="utf-8") as f:
                content = await f.read()
                backup_data = json.loads(content)
            
            # 验证备份数据
            if backup_data["group_id"] != self.group_id:
                raise ValueError("备份文件与群组不匹配")
            
            restored_stats = {
                "active_messages": 0,
                "deleted_messages": 0,
                "archived_messages": 0
            }
            
            # 恢复主表消息
            for msg_data in backup_data["messages"]:
                if msg_data["is_deleted"] and not restore_deleted:
                    continue
                    
                # 检查消息是否已存在
                existing = await session.execute(
                    select(self.message_class).where(
                        self.message_class.public_id == msg_data["id"]
                    )
                )
                if not existing.scalar_one_or_none():
                    # 创建新消息
                    msg = self.message_class(
                        public_id=msg_data["id"],
                        content=msg_data["content"],
                        sender_id=msg_data["sender_id"],
                        content_type=msg_data["content_type"],
                        status=msg_data["status"],
                        created_at=datetime.fromisoformat(msg_data["created_at"]),
                        updated_at=datetime.fromisoformat(msg_data["updated_at"]),
                        is_deleted=msg_data["is_deleted"],
                        delete_at=datetime.fromisoformat(msg_data["delete_at"]) if msg_data["delete_at"] else None,
                        reply_to_id=msg_data["reply_to_id"],
                        forward_from_id=msg_data["forward_from_id"],
                        extra_data=msg_data["extra_data"]
                    )
                    session.add(msg)
                    
                    if msg_data["is_deleted"]:
                        restored_stats["deleted_messages"] += 1
                    else:
                        restored_stats["active_messages"] += 1
            
            # 恢复归档消息
            if restore_archived and backup_data["archived_messages"]:
                archive_class = self.message_class.get_archive_class()
                for msg_data in backup_data["archived_messages"]:
                    existing = await session.execute(
                        select(archive_class).where(
                            archive_class.public_id == msg_data["id"]
                        )
                    )
                    if not existing.scalar_one_or_none():
                        msg = archive_class(
                            public_id=msg_data["id"],
                            content=msg_data["content"],
                            sender_id=msg_data["sender_id"],
                            content_type=msg_data["content_type"],
                            status=msg_data["status"],
                            created_at=datetime.fromisoformat(msg_data["created_at"]),
                            updated_at=datetime.fromisoformat(msg_data["updated_at"]),
                            is_deleted=msg_data["is_deleted"],
                            delete_at=datetime.fromisoformat(msg_data["delete_at"]) if msg_data["delete_at"] else None,
                            reply_to_id=msg_data["reply_to_id"],
                            forward_from_id=msg_data["forward_from_id"],
                            extra_data=msg_data["extra_data"],
                            archive_time=datetime.fromisoformat(msg_data["archive_time"]),
                            original_id=msg_data["original_id"]
                        )
                        session.add(msg)
                        restored_stats["archived_messages"] += 1
            
            await session.commit()
            return restored_stats
            
        except Exception as e:
            lprint(f"从备份恢复消息失败: {traceback.format_exc()}")
            raise
