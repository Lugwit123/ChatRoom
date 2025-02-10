"""会话管理模块"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker

class SessionManager:
    """会话管理器"""
    
    def __init__(self, engine: AsyncEngine):
        """初始化会话管理器
        
        Args:
            engine: 数据库引擎
        """
        self.lprint = LM.lprint
        self._engine = engine
        self._session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话
        
        Yields:
            AsyncSession: 数据库会话
        """
        session: AsyncSession = self._session_factory()
        try:
            yield session
        finally:
            await session.close()
            
    def create_session(self) -> AsyncSession:
        """创建新的数据库会话
        
        Returns:
            AsyncSession: 数据库会话
        """
        return self._session_factory()
