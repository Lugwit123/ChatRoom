"""数据库门面类，提供统一的数据库操作接口"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

import os
import traceback
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

from ..internal.base import Base
from ..internal.session import SessionManager
from ..internal.transaction import TransactionManager

class DatabaseFacade:
    """数据库门面类"""
    
    def __init__(self):
        """初始化数据库门面"""
        self.lprint = LM.lprint
        self._engine: Optional[AsyncEngine] = None
        self._session_manager: Optional[SessionManager] = None
        self._transaction_manager: Optional[TransactionManager] = None
        
    async def init(self, database_url: str):
        """初始化数据库连接
        
        Args:
            database_url: 数据库连接URL
        """
        try:
            # 创建引擎
            self._engine = create_async_engine(
                database_url,
                echo=False,
                future=True
            )
            
            # 初始化会话管理器
            self._session_manager = SessionManager(self._engine)
            
            # 初始化事务管理器
            self._transaction_manager = TransactionManager()
            
            self.lprint("数据库连接初始化成功")
            
        except Exception as e:
            self.lprint(f"数据库连接初始化失败: {str(e)}\n{traceback.format_exc()}")
            raise
            
    async def create_tables(self):
        """创建所有数据库表"""
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self.lprint("数据库表创建成功")
        except Exception as e:
            self.lprint(f"数据库表创建失败: {str(e)}\n{traceback.format_exc()}")
            raise
            
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
                
    async def create_session(self) -> AsyncSession:
        """创建新的数据库会话
        
        Returns:
            AsyncSession: 数据库会话
        """
        if not self._session_manager:
            raise RuntimeError("数据库未初始化")
            
        return await self._session_manager.create_session()
        
    async def cleanup(self):
        """清理数据库资源"""
        try:
            if self._engine:
                await self._engine.dispose()
                self._engine = None
            self._session_manager = None
            self._transaction_manager = None
            self.lprint("数据库资源清理成功")
        except Exception as e:
            self.lprint(f"数据库资源清理失败: {str(e)}\n{traceback.format_exc()}")
            raise
