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
from app.core.base.internal.repository.core_repository import CoreRepository

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
            
    def init_sync(self, database_url: str) -> None:
        """同步初始化数据库连接
        
        Args:
            database_url: 数据库连接URL
        """
        try:
            self.lprint("开始初始化数据库连接...")
            
            # 创建异步引擎
            self._engine = create_async_engine(
                database_url,
                echo=False,
                future=True
            )
            
            # 创建会话工厂
            async_session = sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # 创建共享会话
            self._shared_session = async_session()
            
            # 设置共享会话到仓储基类
            CoreRepository.set_session(self._shared_session)
            
            # 创建会话管理器
            self._session_manager = SessionManager(async_session)
            
            # 创建事务管理器
            self._transaction_manager = TransactionManager(self._shared_session)
            
            self.lprint("数据库连接初始化完成")
            
        except Exception as e:
            self.lprint(f"数据库连接初始化失败: {str(e)}")
            traceback.print_exc()
            raise
            
    async def init_async(self, database_url: str) -> None:
        """异步初始化数据库连接
        
        Args:
            database_url: 数据库连接URL
        """
        try:
            self.lprint("开始初始化数据库连接...")
            
            # 创建异步引擎
            self._engine = create_async_engine(
                database_url,
                echo=False,
                future=True
            )
            
            # 创建会话工厂
            async_session = sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # 创建共享会话
            self._shared_session = async_session()
            
            # 设置共享会话到仓储基类
            CoreRepository.set_session(self._shared_session)
            
            # 创建会话管理器
            self._session_manager = SessionManager(async_session)
            
            # 创建事务管理器
            self._transaction_manager = TransactionManager(self._shared_session)
            
            # 创建所有表
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self.lprint("数据库连接初始化完成")
            
        except Exception as e:
            self.lprint(f"数据库连接初始化失败: {str(e)}")
            traceback.print_exc()
            raise
            
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话
        
        Returns:
            AsyncSession: 数据库会话
        """
        if not self._session_manager:
            raise RuntimeError("Database not initialized")
            
        async with self._session_manager.session() as session:
            # 设置共享会话到仓储基类
            CoreRepository.set_session(session)
            try:
                yield session
            finally:
                await session.close()
                
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """开启事务
        
        Returns:
            AsyncSession: 数据库会话
        """
        if not self._transaction_manager:
            raise RuntimeError("Database not initialized")
            
        async with self._transaction_manager.transaction() as session:
            yield session
            
    async def cleanup(self) -> None:
        """清理数据库资源"""
        try:
            self.lprint("开始清理数据库资源...")
            
            if self._shared_session:
                await self._shared_session.close()
                
            if self._engine:
                await self._engine.dispose()
                
            self.lprint("数据库资源清理完成")
            
        except Exception as e:
            self.lprint(f"数据库资源清理失败: {str(e)}")
            traceback.print_exc()
            raise
