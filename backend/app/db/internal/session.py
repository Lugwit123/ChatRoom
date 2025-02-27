"""会话管理模块"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Dict, Set
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

class SessionPool:
    """会话池，用于管理和复用数据库会话"""
    
    def __init__(self, max_size: int = 20):
        """初始化会话池
        
        Args:
            max_size: 最大会话数量
        """
        self._available: Set[AsyncSession] = set()
        self._in_use: Dict[AsyncSession, datetime] = {}
        self._max_size = max_size
        self._lock = asyncio.Lock()
        
    async def acquire(self, session_factory) -> AsyncSession:
        """获取一个可用的会话
        
        Args:
            session_factory: 会话工厂函数
            
        Returns:
            AsyncSession: 数据库会话
        """
        async with self._lock:
            # 清理过期会话
            await self._cleanup_expired_sessions()
            
            # 如果有可用会话，直接使用
            if self._available:
                session = self._available.pop()
            # 如果没有达到最大限制，创建新会话
            elif len(self._in_use) < self._max_size:
                session = session_factory()
            # 如果达到限制，等待可用会话
            else:
                lprint("会话池已满，等待可用会话...")
                while not self._available and len(self._in_use) >= self._max_size:
                    await asyncio.sleep(0.1)
                    await self._cleanup_expired_sessions()
                session = self._available.pop() if self._available else session_factory()
            
            self._in_use[session] = datetime.now()
            return session
            
    async def release(self, session: AsyncSession) -> None:
        """释放会话回池
        
        Args:
            session: 要释放的会话
        """
        async with self._lock:
            if session in self._in_use:
                del self._in_use[session]
                if not session.is_active:
                    self._available.add(session)
                    
    async def _cleanup_expired_sessions(self, max_idle_time: int = 1800) -> None:
        """清理过期的会话
        
        Args:
            max_idle_time: 最大空闲时间（秒）
        """
        now = datetime.now()
        expired = [
            session for session, start_time in self._in_use.items()
            if (now - start_time).total_seconds() > max_idle_time
        ]
        for session in expired:
            await session.close()
            del self._in_use[session]

class SessionManager:
    """会话管理器"""
    
    def __init__(self, engine: AsyncEngine):
        """初始化会话管理器
        
        Args:
            engine: 数据库引擎
        """
        self._engine = engine
        self._session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        self._pool = SessionPool()
        
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话
        
        Yields:
            AsyncSession: 数据库会话
        """
        session = await self._pool.acquire(self._session_factory)
        try:
            yield session
        finally:
            try:
                await session.close()
            except Exception as e:
                lprint(f"关闭会话时出错: {e}")
            await self._pool.release(session)
            
    async def cleanup(self) -> None:
        """清理所有会话"""
        async with self._pool._lock:
            for session in self._pool._available:
                await session.close()
            for session in self._pool._in_use:
                await session.close()
            self._pool._available.clear()
            self._pool._in_use.clear()
