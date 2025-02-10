"""
群组消息仓储
处理群组消息的存储和查询
"""
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any, Type, Union, cast
from zoneinfo import ZoneInfo

from sqlalchemy import select, and_, update, delete, text, or_, desc, Column, true, false
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList
from sqlalchemy.sql import Select
from sqlalchemy.sql.expression import cast as sql_cast
from sqlalchemy.types import Integer, DateTime, Boolean

import Lugwit_Module as LM
lprint = LM.lprint

from app.domain.common.models.tables import BaseMessage, Group, create_group_message_table, GroupMember
from app.domain.common.enums.message import MessageStatus
from app.domain.message.internal.repository.base import BaseMessageRepository

class TablePartitionStrategy(Enum):
    """表分区策略"""
    HASH = "hash"  # 哈希分区，适合均匀分布的数据
    TIME = "time"  # 时间分区，适合按时间查询和归档
    HYBRID = "hybrid"  # 混合分区，同时考虑群组ID和时间

class TableNamingConfig:
    """表命名配置"""
    def __init__(self):
        self.table_prefix = "group_messages"
        self.partition_strategy = TablePartitionStrategy.HYBRID
        self.time_format = "%Y%m"
        
    def generate_table_name(self, group_id: int, created_at: Optional[datetime] = None) -> str:
        """生成表名
        
        Args:
            group_id: 群组ID
            created_at: 创建时间
            
        Returns:
            str: 表名，格式为 group_messages_[group_id]_[YYYYMM]
        """
        if not created_at:
            created_at = datetime.now()
            
        time_suffix = created_at.strftime(self.time_format)
        return f"{self.table_prefix}_{group_id}_{time_suffix}"

class GroupMessageRepository(BaseMessageRepository):
    """群组消息仓储实现"""
    
    def __init__(self):
        """初始化群组消息仓储"""
        super().__init__()
        self._group_id: Optional[int] = None
        self.model = None
        self.table_config = TableNamingConfig()
        self._table_cache = {}
        
    @property
    def group_id(self) -> Optional[int]:
        return self._group_id
        
    @group_id.setter
    def group_id(self, value: int):
        self._group_id = value
        
    async def _get_message_table(self, group_id: int, created_at: Optional[datetime] = None) -> Type[BaseMessage]:
        """获取消息表类"""
        # 先查找群组当前使用的表
        group_result = await self.session.execute(
            select(Group).where(Group.id == group_id)
        )
        group = group_result.scalar_one_or_none()
        
        if group and getattr(group, 'message_table_name', None):
            table_name = str(group.message_table_name)
        else:
            # 如果没有表名或者群组不存在，生成新表名
            table_name = self.table_config.generate_table_name(group_id, created_at)
            
            # 更新群组的消息表名
            if group:
                await self.session.execute(
                    update(Group)
                    .where(Group.id == group_id)
                    .values(message_table_name=table_name)
                )
                await self.session.commit()
        
        # 使用缓存避免重复创建表类
        if table_name in self._table_cache:
            return self._table_cache[table_name]
            
        # 创建新表类
        message_table = create_group_message_table(table_name)
        self._table_cache[table_name] = message_table
        
        # 确保表在数据库中存在
        await self.session.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                LIKE group_messages_base INCLUDING ALL
            )
        """))
        await self.session.commit()
        
        return message_table
        
    async def save_message(self, message_data: dict) -> BaseMessage:
        """保存群组消息
        
        Args:
            message_data: 消息数据
            
        Returns:
            BaseMessage: 保存的消息
        """
        try:
            group_id = message_data.get("group_id")
            if not group_id:
                raise ValueError("群组消息必须指定群组ID")
                
            created_at = message_data.get("created_at")
            self.model = await self._get_message_table(group_id, created_at)
            
            return await super().save_message(message_data)
            
        except Exception as e:
            self.lprint(f"保存群组消息失败: {str(e)}")
            raise
            
    async def get_messages(
        self,
        group_id: int,
        offset: int = 0,
        limit: int = 20,
        before_id: Optional[int] = None,
        after_id: Optional[int] = None,
        user_id: Optional[int] = None,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """获取群组消息列表"""
        try:
            self.group_id = group_id
            message_table = await self._get_message_table(group_id)
            if not message_table:
                return []
                
            self.model = message_table
            conditions = []
            
            if before_id:
                conditions.append(sql_cast(self.model.id, Integer) < before_id)
            if after_id:
                conditions.append(sql_cast(self.model.id, Integer) > after_id)
                
            # 如果指定了用户ID，只返回该用户加入群组后的消息
            if user_id:
                member = await self._get_user_join_time(user_id)
                if member is not None and isinstance(member, GroupMember):
                    member_joined_at = getattr(member, 'joined_at', None)
                    if member_joined_at is not None:
                        conditions.append(
                            sql_cast(self.model.created_at, DateTime) >= member_joined_at
                        )
                    
            query = select(self.model)
            if conditions:
                query = query.where(and_(*conditions))
                
            if before_id:
                query = query.order_by(desc(self.model.id))
            else:
                query = query.order_by(self.model.id.asc())
                
            query = query.offset(offset).limit(limit)
            
            result = await self.session.execute(query)
            messages = result.scalars().all()
            
            return [message.to_dict() for message in messages]
            
        except Exception as e:
            self.lprint(f"获取群组消息失败: {str(e)}")
            return []

    async def get_message_by_public_id(self, group_id: int, public_id: str) -> Optional[BaseMessage]:
        """根据公开ID获取消息"""
        try:
            self.group_id = group_id
            message_table = await self._get_message_table(group_id)
            if not message_table:
                return None
                
            self.model = message_table
            query = select(self.model).where(self.model.public_id == public_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            self.lprint(f"获取消息失败: {str(e)}")
            return None
    
    async def search_messages(
        self,
        group_id: int,
        keyword: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[BaseMessage]:
        """搜索群组消息"""
        try:
            self.group_id = group_id
            message_table = await self._get_message_table(group_id)
            if not message_table:
                return []
                
            self.model = message_table
            query = (
                select(self.model)
                .where(self.model.content.ilike(f"%{keyword}%"))
                .order_by(desc(self.model.created_at))
                .offset(offset)
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            self.lprint(f"搜索消息失败: {str(e)}")
            return []
    
    async def get_unread_count(self, group_id: int, user_id: int) -> int:
        """获取未读消息数"""
        try:
            self.group_id = group_id
            message_table = await self._get_message_table(group_id)
            if not message_table:
                return 0
                
            self.model = message_table
            # 获取用户加入群组的时间
            member = await self._get_user_join_time(user_id)
            if member is None or not isinstance(member, GroupMember):
                return 0
                
            member_joined_at = getattr(member, 'joined_at', None)
            if member_joined_at is None:
                return 0
            
            # 获取未读消息数
            query = select(self.model).where(
                and_(
                    sql_cast(self.model.created_at, DateTime) >= member_joined_at,
                    sql_cast(self.model.sender_id, Integer) != user_id,
                    or_(
                        sql_cast(self.model.status, Boolean).is_(None),
                        sql_cast(self.model.status, Boolean).any(MessageStatus.unread.value)
                    )
                )
            )
            result = await self.session.execute(query)
            return len(result.scalars().all())
        except Exception as e:
            self.lprint(f"获取未读消息数失败: {str(e)}")
            return 0
        
    async def _get_user_join_time(self, user_id: int) -> Optional[GroupMember]:
        """获取用户加入群组的时间"""
        try:
            if not self.group_id:
                return None
                
            member_query = select(GroupMember).where(
                and_(
                    GroupMember.user_id == user_id,
                    GroupMember.group_id == self.group_id
                )
            )
            result = await self.session.execute(member_query)
            return result.scalar_one_or_none()
        except Exception as e:
            self.lprint(f"获取用户加入时间失败: {str(e)}")
            return None
        
    async def get_message_by_id(self, message_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取消息"""
        message = await self.get_by_id(message_id)
        return message.to_dict() if message else None
    
    async def create_message_table(self) -> None:
        """创建群组消息表"""
        await self.session.execute(text(f"CREATE TABLE IF NOT EXISTS group_messages_{self.group_id} LIKE group_messages_template"))
        await self.session.commit()
    
    async def drop_message_table(self) -> None:
        """删除群组消息表"""
        await self.session.execute(text(f"DROP TABLE IF EXISTS group_messages_{self.group_id}"))
        await self.session.commit()
    
    async def table_exists(self) -> bool:
        """检查群组消息表是否存在"""
        result = await self.session.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = :table_name)"
            ),
            {"table_name": f"group_messages_{self.group_id}"}
        )
        return result.scalar_one()
