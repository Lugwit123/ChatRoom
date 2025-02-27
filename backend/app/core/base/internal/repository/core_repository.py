"""核心仓储模块
提供所有仓储的基础功能实现
"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

import traceback
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any, AsyncGenerator, Callable, AsyncContextManager
from contextlib import asynccontextmanager
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.internal.base import Base
from app.db.facade.database_facade import DatabaseFacade
from app.db.internal.transaction import TransactionManager

ModelType = TypeVar("ModelType", bound=Base)

class CoreRepository(Generic[ModelType]):
    """核心仓储类，提供基本的CRUD操作
    
    这个类是所有仓储类的基类，提供了以下功能：
    1. 基本的CRUD操作（创建、读取、更新、删除）
    2. 异常处理和日志记录
    3. 事务管理
    4. 统一的会话管理
    
    使用示例:
    ```python
    class UserRepository(CoreRepository[User]):
        def __init__(self):
            super().__init__(User)
            
        async def get_by_username(self, username: str) -> Optional[User]:
            query = select(self.model).where(self.model.username == username)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
    ```
    """
    
    def __init__(self, model: Type[ModelType]):
        """初始化仓储
        
        Args:
            model: 模型类
        """
        self.model = model
        self._db_facade = DatabaseFacade()
        self._session: Optional[AsyncSession] = None
        self._transaction_manager: Optional[TransactionManager] = None
        
    @property
    def session(self) -> AsyncSession:
        """获取当前会话
        
        Returns:
            AsyncSession: 数据库会话
            
        Raises:
            RuntimeError: 如果会话未初始化
        """
        if self._session is None:
            raise RuntimeError("数据库会话未初始化，请在使用前先调用 get_session")
        return self._session
        
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话
        
        使用示例:
        ```python
        async with repository.get_session() as session:
            # 使用session进行数据库操作
            result = await session.execute(query)
        ```
        
        Yields:
            AsyncSession: 数据库会话
        """
        async with self._db_facade.get_db() as session:
            self._session = session
            try:
                yield session
            finally:
                self._session = None
                
    @asynccontextmanager
    async def transaction(self, retry_policy: Optional[dict] = None) -> AsyncGenerator[AsyncSession, None]:
        """在事务中执行操作
        
        使用示例:
        ```python
        async with repository.transaction() as session:
            # 在事务中执行操作
            await session.execute(query1)
            await session.execute(query2)
        ```
        
        Args:
            retry_policy: 重试策略配置
                {
                    'retries': 最大重试次数,
                    'retry_delay': 重试延迟（秒）,
                    'retry_exceptions': 可重试的异常类型元组
                }
                
        Yields:
            AsyncSession: 数据库会话
        """
        async with self._db_facade.transaction(retry_policy) as session:
            self._session = session
            try:
                yield session
            finally:
                self._session = None

    async def create(self, **kwargs) -> ModelType:
        """创建新记录
        
        Args:
            **kwargs: 模型属性
            
        Returns:
            ModelType: 创建的记录
        """
        try:
            async with self.transaction() as session:
                instance = self.model(**kwargs)
                session.add(instance)
                await session.flush()
                await session.refresh(instance)
                return instance
        except Exception:
            traceback.print_exc()
            raise
            
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """根据ID获取记录
        
        Args:
            id: 记录ID
            
        Returns:
            Optional[ModelType]: 记录对象或None
        """
        try:
            async with self.get_session() as session:
                query = select(self.model).where(self.model.id == id)
                result = await session.execute(query)
                return result.scalar_one_or_none()
        except Exception:
            traceback.print_exc()
            raise
            
    async def get_all_records(self) -> List[ModelType]:
        """获取所有记录
        
        Returns:
            List[ModelType]: 记录列表
        """
        try:
            async with self.get_session() as session:
                query = select(self.model)
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception:
            traceback.print_exc()
            raise
            
    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """更新记录
        
        Args:
            id: 记录ID
            **kwargs: 要更新的字段
            
        Returns:
            Optional[ModelType]: 更新后的记录，如果记录不存在则返回None
        """
        try:
            async with self.transaction() as session:
                query = update(self.model).where(self.model.id == id).values(**kwargs)
                result = await session.execute(query)
                
                # 如果更新成功，获取并返回更新后的对象
                if result.rowcount > 0:
                    await session.flush()
                    # 重新查询获取更新后的对象
                    refresh_query = select(self.model).where(self.model.id == id)
                    refresh_result = await session.execute(refresh_query)
                    return refresh_result.scalar_one_or_none()
                return None
        except Exception:
            traceback.print_exc()
            raise
            
    async def delete(self, id: int) -> bool:
        """删除记录
        
        Args:
            id: 记录ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            async with self.transaction() as session:
                query = delete(self.model).where(self.model.id == id)
                result = await session.execute(query)
                return result.rowcount > 0
        except Exception:
            traceback.print_exc()
            raise