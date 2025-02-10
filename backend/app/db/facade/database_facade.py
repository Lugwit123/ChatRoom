"""数据库门面类，提供统一的数据库操作接口"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

import os
import traceback
from typing import Optional, AsyncGenerator, AsyncContextManager
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

from ..internal.base import Base
from ..internal.session import SessionManager
from ..internal.transaction import TransactionManager

class DatabaseFacade:
    """数据库门面类"""
    
    _instance = None
    
    def __new__(cls):
        """创建单例实例"""
        if cls._instance is None:
            cls._instance = super(DatabaseFacade, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化数据库门面"""
        if not self.initialized:
            self.lprint = LM.lprint
            self._engine: Optional[AsyncEngine] = None
            self._session_manager: Optional[SessionManager] = None
            self._transaction_manager: Optional[TransactionManager] = None
            self._shared_session: Optional[AsyncSession] = None
            self.initialized = True
        
    async def init(self, database_url: str):
        """初始化数据库连接
        
        Args:
            database_url: 数据库连接URL
        """
        try:
            # 创建数据库引擎
            self._engine = create_async_engine(
                database_url,
                echo=False,
                pool_pre_ping=True,
                future=True
            )
            
            # 创建会话管理器
            self._session_manager = SessionManager(self._engine)
            self._transaction_manager = TransactionManager()
            
            # 创建共享会话
            self._shared_session = self._session_manager.create_session()
            
            # 设置核心仓储的共享会话
            from app.core.base.internal.repository.base_repository import CoreBaseRepository
            CoreBaseRepository.set_session(self._shared_session)
            
            # 设置领域仓储的共享会话
            from app.domain.base.internal.repository.base_repository import BaseRepository
            BaseRepository.set_session(self._shared_session)
            
            self.lprint(f"数据库连接初始化成功,会话为{self._shared_session}")
        except Exception as e:
            self.lprint(f"数据库连接初始化失败: {str(e)}")
            raise
            
    def init_sync(self, database_url: str):
        """同步初始化数据库连接
        
        Args:
            database_url: 数据库连接URL
        """
        try:
            # 创建数据库引擎
            self._engine = create_async_engine(
                database_url,
                echo=False,
                pool_pre_ping=True,
                future=True
            )
            
            # 创建会话管理器
            self._session_manager = SessionManager(self._engine)
            self._transaction_manager = TransactionManager()
            
            # 创建共享会话
            self._shared_session = self._session_manager.create_session()
            
            # 设置核心仓储的共享会话
            from app.core.base.internal.repository.base_repository import CoreBaseRepository
            CoreBaseRepository.set_session(self._shared_session)
            
            # 设置领域仓储的共享会话
            from app.domain.base.internal.repository.base_repository import BaseRepository
            BaseRepository.set_session(self._shared_session)
            
            self.lprint(f"数据库连接初始化成功,会话为{self._shared_session}")
        except Exception as e:
            self.lprint(f"数据库连接初始化失败: {str(e)}")
            raise

    async def create_tables(self) -> bool:
        """创建所有数据库表"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            return True
        except Exception as e:
            print(f"数据库表创建失败: {str(e)}\n{traceback.format_exc()}")
            return False

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话，用于依赖注入
        
        Yields:
            AsyncSession: 数据库会话
        """
        if not self._session_manager:
            raise RuntimeError("数据库未初始化")
            
        async with self._session_manager.get_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise
                
    @property
    def engine(self) -> AsyncEngine:
        """获取数据库引擎"""
        if not self._engine:
            raise RuntimeError("数据库未初始化")
        return self._engine

    @property
    def session(self) -> AsyncSession:
        """获取共享会话"""
        if not self._shared_session:
            raise RuntimeError("数据库未初始化")
        return self._shared_session

    async def create_session(self) -> AsyncSession:
        """创建新的数据库会话"""
        if not self._session_manager:
            raise RuntimeError("数据库未初始化")
            
        session = self._session_manager.create_session()
        
        # 设置核心仓储的共享会话
        from app.core.base.internal.repository.base_repository import CoreBaseRepository
        CoreBaseRepository.set_session(session)
        
        # 设置领域仓储的共享会话
        from app.domain.base.internal.repository.base_repository import BaseRepository
        BaseRepository.set_session(session)
        
        return session
        
    async def cleanup(self):
        """清理数据库资源"""
        if self._shared_session:
            await self._shared_session.close()
            self._shared_session = None
            
        if self._engine:
            await self._engine.dispose()
            self._engine = None
        self._session_manager = None
        self._transaction_manager = None
        self.lprint("数据库资源清理成功")
