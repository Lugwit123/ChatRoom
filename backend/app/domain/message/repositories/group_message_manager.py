"""群消息管理器"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import engine
from app.domain.message.models import create_group_message_table, MessageStatus

class GroupMessageManager:
    """群消息管理器，用于处理消息归档、迁移和清理"""
    
    def __init__(self, group_id: str):
        """初始化群消息管理器
        
        Args:
            group_id: 群组ID
        """
        self.group_id = group_id
        self.message_class = create_group_message_table(group_id)
        self.archive_class = self._create_archive_table()
    
    def _create_archive_table(self):
        """创建归档表"""
        table_name = f"group_messages_{self.group_id}_archive"
        
        # 创建归档表类
        class GroupMessageArchive(self.message_class):
            __tablename__ = table_name
            __table_args__ = {'extend_existing': True}
            
            archive_time = Column(DateTime(timezone=True), default=datetime.utcnow)
            original_id = Column(String(50))  # 原始消息ID
        
        return GroupMessageArchive
    
    async def ensure_archive_table(self, session: AsyncSession) -> None:
        """确保归档表存在
        
        Args:
            session: 数据库会话
        """
        table_name = f"group_messages_{self.group_id}_archive"
        result = await session.execute(
            text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')")
        )
        exists = result.scalar()
        
        if not exists:
            lprint(f"Creating archive table {table_name}")
            await session.execute(text(str(self.archive_class.__table__.create(bind=session.bind))))
            await session.commit()
    
    async def archive_messages(
        self,
        session: AsyncSession,
        before_date: datetime,
        batch_size: int = 1000
    ) -> Tuple[int, int]:
        """归档旧消息
        
        Args:
            session: 数据库会话
            before_date: 此日期之前的消息将被归档
            batch_size: 每批处理的消息数量
            
        Returns:
            Tuple[int, int]: (归档的消息数量, 删除的消息数量)
        """
        try:
            # 确保归档表存在
            await self.ensure_archive_table(session)
            
            archived_count = 0
            deleted_count = 0
            
            while True:
                # 获取一批需要归档的消息
                messages = await session.execute(
                    select(self.message_class)
                    .where(self.message_class.created_at <= before_date)
                    .limit(batch_size)
                )
                messages = messages.scalars().all()
                
                if not messages:
                    break
                
                # 创建归档记录
                for msg in messages:
                    archive = self.archive_class(
                        public_id=f"arch_{msg.public_id}",
                        content=msg.content,
                        sender_id=msg.sender_id,
                        content_type=msg.content_type,
                        status=msg.status,
                        created_at=msg.created_at,
                        updated_at=msg.updated_at,
                        extra_data=msg.extra_data,
                        is_deleted=msg.is_deleted,
                        delete_at=msg.delete_at,
                        reply_to_id=msg.reply_to_id,
                        forward_from_id=msg.forward_from_id,
                        search_vector=msg.search_vector,
                        original_id=msg.public_id
                    )
                    session.add(archive)
                    archived_count += 1
                
                # 删除原始消息
                msg_ids = [msg.id for msg in messages]
                result = await session.execute(
                    self.message_class.__table__.delete().where(
                        self.message_class.id.in_(msg_ids)
                    )
                )
                deleted_count += result.rowcount
                
                await session.commit()
            
            return archived_count, deleted_count
            
        except Exception as e:
            lprint(f"归档消息失败: {traceback.format_exc()}")
            raise
    
    async def migrate_messages(
        self,
        session: AsyncSession,
        target_group_id: str,
        message_ids: List[str] = None,
        before_date: datetime = None
    ) -> int:
        """迁移消息到另一个群
        
        Args:
            session: 数据库会话
            target_group_id: 目标群组ID
            message_ids: 要迁移的消息ID列表，如果为None则根据before_date迁移
            before_date: 迁移此日期之前的消息
            
        Returns:
            int: 迁移的消息数量
        """
        try:
            # 创建目标群消息表
            target_message_class = create_group_message_table(target_group_id)
            
            # 构建查询
            query = select(self.message_class)
            if message_ids:
                query = query.where(self.message_class.public_id.in_(message_ids))
            elif before_date:
                query = query.where(self.message_class.created_at <= before_date)
            
            # 获取要迁移的消息
            messages = await session.execute(query)
            messages = messages.scalars().all()
            
            # 迁移消息
            migrated_count = 0
            for msg in messages:
                new_msg = target_message_class(
                    public_id=f"migr_{msg.public_id}",
                    content=msg.content,
                    sender_id=msg.sender_id,
                    content_type=msg.content_type,
                    status=msg.status,
                    created_at=msg.created_at,
                    updated_at=msg.updated_at,
                    extra_data=msg.extra_data,
                    is_deleted=msg.is_deleted,
                    delete_at=msg.delete_at,
                    reply_to_id=msg.reply_to_id,
                    forward_from_id=msg.forward_from_id,
                    search_vector=msg.search_vector
                )
                session.add(new_msg)
                migrated_count += 1
            
            await session.commit()
            return migrated_count
            
        except Exception as e:
            lprint(f"迁移消息失败: {traceback.format_exc()}")
            raise
    
    async def cleanup_messages(
        self,
        session: AsyncSession,
        retention_days: int = 30,
        cleanup_deleted: bool = True,
        cleanup_archived: bool = True
    ) -> Dict[str, int]:
        """清理消息
        
        Args:
            session: 数据库会话
            retention_days: 保留天数
            cleanup_deleted: 是否清理已删除消息
            cleanup_archived: 是否清理已归档消息
            
        Returns:
            Dict[str, int]: 清理结果统计
        """
        try:
            cleanup_stats = {
                "deleted_messages": 0,
                "archived_messages": 0
            }
            
            retention_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # 清理已删除消息
            if cleanup_deleted:
                result = await session.execute(
                    self.message_class.__table__.delete().where(
                        self.message_class.is_deleted == True,
                        self.message_class.delete_at <= retention_date
                    )
                )
                cleanup_stats["deleted_messages"] = result.rowcount
            
            # 清理已归档消息
            if cleanup_archived:
                # 确保归档表存在
                await self.ensure_archive_table(session)
                
                result = await session.execute(
                    self.archive_class.__table__.delete().where(
                        self.archive_class.created_at <= retention_date
                    )
                )
                cleanup_stats["archived_messages"] = result.rowcount
            
            await session.commit()
            return cleanup_stats
            
        except Exception as e:
            lprint(f"清理消息失败: {traceback.format_exc()}")
            raise
    
    async def get_message_stats(
        self,
        session: AsyncSession,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取消息统计信息
        
        Args:
            session: 数据库会话
            start_time: 统计开始时间
            end_time: 统计结束时间
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            query = select(
                func.count().label("total_count"),
                func.count(self.message_class.is_deleted == True).label("deleted_count"),
                func.count(self.message_class.reply_to_id != None).label("reply_count"),
                func.count(self.message_class.forward_from_id != None).label("forward_count")
            ).select_from(self.message_class)
            
            if start_time:
                query = query.where(self.message_class.created_at >= start_time)
            if end_time:
                query = query.where(self.message_class.created_at <= end_time)
            
            result = await session.execute(query)
            stats = result.mappings().first()
            
            # 获取归档消息统计
            await self.ensure_archive_table(session)
            archive_query = select(func.count()).select_from(self.archive_class)
            if start_time:
                archive_query = archive_query.where(self.archive_class.created_at >= start_time)
            if end_time:
                archive_query = archive_query.where(self.archive_class.created_at <= end_time)
            
            archive_result = await session.execute(archive_query)
            archive_count = archive_result.scalar()
            
            return {
                "total_messages": stats["total_count"],
                "deleted_messages": stats["deleted_count"],
                "reply_messages": stats["reply_count"],
                "forwarded_messages": stats["forward_count"],
                "archived_messages": archive_count,
                "active_messages": stats["total_count"] - stats["deleted_count"],
                "start_time": start_time,
                "end_time": end_time
            }
            
        except Exception as e:
            lprint(f"获取消息统计失败: {traceback.format_exc()}")
            raise
