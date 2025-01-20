"""群组消息仓储实现"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from sqlalchemy import select, update, delete, text, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
import traceback

# 本地模块
from app.db.database import AsyncSessionLocal, engine
from app.domain.message.enums import MessageStatus, MessageContentType
from app.domain.message.models import MessageReaction, MessageMention, create_group_message_table
from app.domain.group.models import GroupMember

class GroupMessageRepository:
    """群组消息仓储实现"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._message_models = {}  # 缓存群组消息模型
        
    def _get_message_model(self, group_id: Union[int, str]):
        """获取群组消息模型
        
        Args:
            group_id: 群组ID
            
        Returns:
            消息模型类
        """
        group_id = str(group_id)
        if group_id not in self._message_models:
            self._message_models[group_id] = create_group_message_table(group_id)
        return self._message_models[group_id]
        
    async def create_table_if_not_exists(self, group_id: Union[int, str]):
        """创建群组消息表
        
        Args:
            group_id: 群组ID
        """
        try:
            # 获取消息模型
            message_model = self._get_message_model(group_id)
            
            # 检查表是否存在
            result = await self.session.execute(
                text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{message_model.__tablename__}')")
            )
            exists = result.scalar()
            
            if not exists:
                # 创建表
                print(f"Creating table {message_model.__tablename__}")
                
                # 获取表的 DDL
                table = message_model.__table__
                columns = []
                for column in table.columns:
                    # 将DATETIME类型转换为TIMESTAMP WITH TIME ZONE
                    if isinstance(column.type, type(table.c.created_at.type)):
                        col_type = "TIMESTAMP WITH TIME ZONE"
                    else:
                        col_type = str(column.type)
                        
                    # 添加主键和自增
                    if column.name == 'id':
                        columns.append(f"{column.name} SERIAL PRIMARY KEY")
                    else:
                        columns.append(f"{column.name} {col_type}")
                
                # 构建创建表的 SQL
                create_table_sql = f"""
                CREATE TABLE {table.name} (
                    {', '.join(columns)}
                )
                """
                
                # 执行创建表的 SQL
                await self.session.execute(text(create_table_sql))
                await self.session.commit()
                
        except Exception as e:
            print(f"创建群组消息表失败: {str(e)}")
            await self.session.rollback()
            raise
    
    async def create(self, group_id: Union[int, str], message_data: Dict[str, Any]):
        """创建群组消息
        
        Args:
            group_id: 群组ID
            message_data: 消息数据
            
        Returns:
            创建的消息
        """
        try:
            # 确保表存在
            await self.create_table_if_not_exists(group_id)
            
            # 获取消息模型
            message_model = self._get_message_model(group_id)
            
            # 创建消息
            message = message_model(**message_data)
            self.session.add(message)
            await self.session.flush()
            
            # 处理@提醒
            if message_data.get("mentions"):
                for user_id in message_data["mentions"]:
                    mention = MessageMention(
                        message_table=message_model.__tablename__,
                        message_id=message.id,
                        user_id=user_id
                    )
                    self.session.add(mention)
            
            await self.session.commit()
            return message
            
        except Exception as e:
            await self.session.rollback()
            print(f"创建群组消息失败: {str(e)}")
            raise
            
    async def get_by_id(self, group_id: Union[int, str], message_id: int):
        """根据ID获取消息
        
        Args:
            group_id: 群组ID
            message_id: 消息ID
            
        Returns:
            消息对象
        """
        try:
            message_model = self._get_message_model(group_id)
            stmt = select(message_model).where(message_model.id == message_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            print(f"获取群组消息失败: {str(e)}")
            raise
            
    async def get_messages(self, 
                          group_id: Union[int, str],
                          limit: int = 20,
                          before_id: Optional[int] = None,
                          after_id: Optional[int] = None):
        """获取群组消息列表
        
        Args:
            group_id: 群组ID
            limit: 返回消息数量
            before_id: 在此ID之前的消息
            after_id: 在此ID之后的消息
            
        Returns:
            消息列表
        """
        try:
            message_model = self._get_message_model(group_id)
            
            # 确保表存在
            await self.create_table_if_not_exists(group_id)
            
            # 构建查询条件
            conditions = []
            if before_id:
                conditions.append(message_model.id < before_id)
            if after_id:
                conditions.append(message_model.id > after_id)
                
            # 构建查询语句
            stmt = select(message_model)
            if conditions:
                stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(desc(message_model.id)).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            print(f"获取群组消息列表失败: {str(e)}")
            raise
            
    async def update_status(self, group_id: Union[int, str], message_id: int, status: MessageStatus):
        """更新消息状态
        
        Args:
            group_id: 群组ID
            message_id: 消息ID
            status: 新状态
        """
        try:
            message_model = self._get_message_model(group_id)
            stmt = (
                select(message_model)
                .where(message_model.id == message_id)
            )
            result = await self.session.execute(stmt)
            message = result.scalar_one_or_none()
            
            if message:
                message.status = status
                await self.session.commit()
                
        except Exception as e:
            await self.session.rollback()
            print(f"更新群组消息状态失败: {str(e)}")
            raise
            
    async def add_reaction(self, group_id: Union[int, str], message_id: int, user_id: int, reaction: str):
        """添加表情回应
        
        Args:
            group_id: 群组ID
            message_id: 消息ID
            user_id: 用户ID
            reaction: 表情
        """
        try:
            message_model = self._get_message_model(group_id)
            
            # 确保表存在
            await self.create_table_if_not_exists(group_id)
            
            # 检查消息是否存在
            stmt = select(message_model).where(message_model.id == message_id)
            result = await self.session.execute(stmt)
            if not result.scalar_one_or_none():
                raise ValueError(f"消息不存在: {message_id}")
                
            # 创建表情回应
            reaction = MessageReaction(
                message_table=message_model.__tablename__,
                message_id=message_id,
                user_id=user_id,
                reaction=reaction
            )
            self.session.add(reaction)
            await self.session.commit()
            
        except Exception as e:
            await self.session.rollback()
            print(f"添加表情回应失败: {str(e)}")
            raise
            
    async def remove_reaction(self, group_id: Union[int, str], message_id: int, user_id: int, reaction: str):
        """移除表情回应
        
        Args:
            group_id: 群组ID
            message_id: 消息ID
            user_id: 用户ID
            reaction: 表情
        """
        try:
            message_model = self._get_message_model(group_id)
            
            # 确保表存在
            await self.create_table_if_not_exists(group_id)
            
            # 删除表情回应
            stmt = (
                select(MessageReaction)
                .where(
                    and_(
                        MessageReaction.message_table == message_model.__tablename__,
                        MessageReaction.message_id == message_id,
                        MessageReaction.user_id == user_id,
                        MessageReaction.reaction == reaction
                    )
                )
            )
            result = await self.session.execute(stmt)
            reaction = result.scalar_one_or_none()
            
            if reaction:
                await self.session.delete(reaction)
                await self.session.commit()
                
        except Exception as e:
            await self.session.rollback()
            print(f"移除表情回应失败: {str(e)}")
            raise
            
    async def mark_as_read(self, group_id: Union[int, str], message_id: int) -> bool:
        """标记群组消息为已读"""
        try:
            message_model = self._get_message_model(group_id)
            stmt = (
                update(message_model)
                .where(message_model.id == message_id)
                .values(status=MessageStatus.read)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            print(f"标记群组消息已读失败: {str(e)}")
            raise
            
    async def delete_message(self, group_id: Union[int, str], message_id: int, user_id: str = None) -> bool:
        """删除群组消息"""
        try:
            message_model = self._get_message_model(group_id)
            
            # 确保表存在
            await self.create_table_if_not_exists(group_id)
            
            # 获取消息
            message = await self.get_by_id(group_id, message_id)
            if not message:
                return False
            
            # 检查权限
            if user_id and message.sender_id != user_id:
                print(f"用户 {user_id} 无权删除消息 {message_id}")
                return False
            
            # 软删除
            stmt = (
                update(message_model)
                .where(message_model.id == message_id)
                .values(
                    is_deleted=True,
                    delete_at=datetime.utcnow()
                )
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            print(f"删除群组消息失败: {str(e)}")
            raise
            
    async def get_unread_count(self, group_id: Union[int, str], user_id: str) -> int:
        """获取用户在群组中的未读消息数量"""
        try:
            message_model = self._get_message_model(group_id)
            
            # 确保表存在
            await self.create_table_if_not_exists(group_id)
            
            # 检查用户是否在群组中
            member_result = await self.session.execute(
                select(GroupMember).where(
                    GroupMember.group_id == group_id,
                    GroupMember.user_id == user_id
                )
            )
            if not member_result.scalar_one_or_none():
                return 0
            
            stmt = (
                select(message_model)
                .where(message_model.status == MessageStatus.unread)
            )
            result = await self.session.execute(stmt)
            return len(result.scalars().all())
        except Exception as e:
            print(f"获取群组未读消息数量失败: {str(e)}")
            raise
            
    async def search_messages(
        self,
        group_id: Union[int, str],
        keyword: str,
        user_id: str = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List:
        """搜索消息"""
        try:
            message_model = self._get_message_model(group_id)
            
            # 确保表存在
            await self.create_table_if_not_exists(group_id)
            
            # 构建查询
            stmt = select(message_model)
            
            # 关键词搜索
            if keyword:
                stmt = stmt.where(message_model.content.ilike(f"%{keyword}%"))
            
            # 发送者过滤
            if user_id:
                stmt = stmt.where(message_model.sender_id == user_id)
            
            # 时间范围
            if start_time:
                stmt = stmt.where(message_model.created_at >= start_time)
            if end_time:
                stmt = stmt.where(message_model.created_at <= end_time)
            
            # 排序和分页
            stmt = stmt.order_by(desc(message_model.created_at))
            stmt = stmt.offset(offset).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            print(f"搜索消息失败: {str(e)}")
            raise
            
    async def archive_old_messages(
        self,
        group_id: Union[int, str],
        before_date: datetime,
        batch_size: int = 1000
    ) -> Dict[str, int]:
        """归档旧消息
        
        Args:
            group_id: 群组ID
            before_date: 此日期之前的消息将被归档
            batch_size: 每批处理的消息数量
            
        Returns:
            Dict[str, int]: 归档结果统计
        """
        # TODO: 实现归档旧消息逻辑
        pass
    
    async def migrate_to_group(
        self,
        group_id: Union[int, str],
        target_group_id: str,
        message_ids: List[str] = None,
        before_date: datetime = None
    ) -> int:
        """迁移消息到另一个群
        
        Args:
            group_id: 群组ID
            target_group_id: 目标群组ID
            message_ids: 要迁移的消息ID列表
            before_date: 迁移此日期之前的消息
            
        Returns:
            int: 迁移的消息数量
        """
        # TODO: 实现迁移消息逻辑
        pass
    
    async def cleanup_old_messages(
        self,
        group_id: Union[int, str],
        retention_days: int = 30,
        cleanup_deleted: bool = True,
        cleanup_archived: bool = True
    ) -> Dict[str, int]:
        """清理旧消息
        
        Args:
            group_id: 群组ID
            retention_days: 保留天数
            cleanup_deleted: 是否清理已删除消息
            cleanup_archived: 是否清理已归档消息
            
        Returns:
            Dict[str, int]: 清理结果统计
        """
        # TODO: 实现清理旧消息逻辑
        pass
    
    async def get_statistics(
        self,
        group_id: Union[int, str],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取消息统计信息
        
        Args:
            group_id: 群组ID
            start_time: 统计开始时间
            end_time: 统计结束时间
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        # TODO: 实现获取消息统计信息逻辑
        pass
    
    async def restore_messages(
        self,
        group_id: Union[int, str],
        message_ids: List[str]
    ) -> Dict[str, int]:
        """恢复已删除的消息
        
        Args:
            group_id: 群组ID
            message_ids: 要恢复的消息ID列表
            
        Returns:
            Dict[str, int]: 恢复结果统计
        """
        # TODO: 实现恢复已删除消息逻辑
        pass
    
    async def export_messages(
        self,
        group_id: Union[int, str],
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        include_deleted: bool = False
    ) -> str:
        """导出消息
        
        Args:
            group_id: 群组ID
            format: 导出格式 (json 或 csv)
            start_time: 开始时间
            end_time: 结束时间
            include_deleted: 是否包含已删除消息
            
        Returns:
            str: 导出文件路径
        """
        # TODO: 实现导出消息逻辑
        pass
    
    async def backup_messages(
        self,
        group_id: Union[int, str],
        include_deleted: bool = True,
        include_archived: bool = True
    ) -> str:
        """备份消息
        
        Args:
            group_id: 群组ID
            include_deleted: 是否包含已删除消息
            include_archived: 是否包含已归档消息
            
        Returns:
            str: 备份文件路径
        """
        # TODO: 实现备份消息逻辑
        pass
    
    async def restore_from_backup(
        self,
        group_id: Union[int, str],
        backup_file: str,
        restore_deleted: bool = True,
        restore_archived: bool = True
    ) -> Dict[str, int]:
        """从备份文件恢复消息
        
        Args:
            group_id: 群组ID
            backup_file: 备份文件路径
            restore_deleted: 是否恢复已删除消息
            restore_archived: 是否恢复已归档消息
            
        Returns:
            Dict[str, int]: 恢复结果统计
        """
        # TODO: 实现从备份文件恢复消息逻辑
        pass

    async def save_message(self, message_data: Dict[str, Any]):
        """保存群组消息"""
        try:
            # 获取消息模型
            message_model = await self._get_message_model(message_data["group_id"])
            
            # 创建消息对象
            message = message_model(
                content=message_data["content"],
                sender_id=message_data["sender_id"],
                group_id=message_data["group_id"],
                content_type=message_data.get("content_type", MessageContentType.plain_text),
                status=MessageStatus.sent,
                extra_data=message_data.get("extra_data", {})
            )
            
            # 保存消息
            self.session.add(message)
            await self.session.flush()
            
            # 处理@提醒
            if message_data.get("mentions"):
                for user_id in message_data["mentions"]:
                    mention = MessageMention(
                        message_table=message_model.__tablename__,
                        message_id=message.id,
                        user_id=user_id
                    )
                    self.session.add(mention)
            
            await self.session.commit()
            return message.public_id
            
        except Exception as e:
            await self.session.rollback()
            print(f"创建群组消息失败: {str(e)}")
            raise
