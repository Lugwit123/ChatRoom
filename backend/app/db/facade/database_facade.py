"""数据库门面类，提供统一的数据库操作接口"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

import os
import traceback
from typing import Optional, AsyncGenerator, AsyncContextManager
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..internal.base import Base
from ..internal.session import SessionManager
from ..internal.transaction import TransactionManager, TransactionError, RetryableError


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
            self._engine: Optional[AsyncEngine] = None
            self._session_manager: Optional[SessionManager] = None
            self.initialized = True

    def init_async(self, database_url: str) -> None:
        """异步初始化数据库连接
        
        Args:
            database_url: 数据库连接URL
        """
        try:
            lprint(f"开始初始化数据库连接{database_url}...")
            
            # 创建异步引擎
            self._engine = create_async_engine(
                database_url,
                echo=False,
                future=True,
                pool_size=20,  # 连接池大小
                max_overflow=10,  # 最大溢出连接数
                pool_timeout=30,  # 连接池超时时间
                pool_recycle=1800,  # 连接回收时间(30分钟)
                pool_pre_ping=True,  # 连接前ping一下，确保连接有效
                connect_args={
                    "command_timeout": 10,  # 命令超时时间
                    "server_settings": {
                        "application_name": "lugwit_chatroom"  # 应用名称，方便数据库监控
                    }
                }
            )
            
            # 创建会话管理器
            self._session_manager = SessionManager(self._engine)
            
            lprint("数据库连接初始化完成")
            
        except Exception as e:
            lprint(f"数据库连接初始化失败: {str(e)}")
            traceback.print_exc()
            raise
            
    @asynccontextmanager
    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话
        
        Returns:
            AsyncSession: 数据库会话
            
        Raises:
            RuntimeError: 数据库未初始化时抛出
        """
        if not self._session_manager:
            raise RuntimeError("数据库未初始化")
            
        async with self._session_manager.get_session() as session:
            yield session
            
    @asynccontextmanager
    async def transaction(self, retry_policy: Optional[dict] = None) -> AsyncGenerator[AsyncSession, None]:
        """开启事务
        
        Args:
            retry_policy: 重试策略配置
                {
                    'retries': 最大重试次数,
                    'retry_delay': 重试延迟（秒）,
                    'retry_exceptions': 可重试的异常类型元组
                }
                
        Yields:
            AsyncSession: 数据库会话
            
        Raises:
            RuntimeError: 数据库未初始化时抛出
            TransactionError: 事务执行失败
        """
        if not self._session_manager:
            raise RuntimeError("数据库未初始化")
            
        async with self._session_manager.get_session() as session:
            transaction_manager = TransactionManager(session)
            async with transaction_manager.in_transaction(retry_policy) as session:
                yield session
                
    async def cleanup(self) -> None:
        """清理数据库资源"""
        if self._session_manager:
            await self._session_manager.cleanup()
        if self._engine:
            await self._engine.dispose()
