"""事务管理模块"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

class TransactionManager:
    """事务管理器"""
    
    def __init__(self):
        """初始化事务管理器"""
        self.lprint = LM.lprint
        
    @asynccontextmanager
    async def transaction(self, session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
        """事务上下文管理器
        
        Args:
            session: 数据库会话
            
        Yields:
            AsyncSession: 数据库会话
        """
        async with session.begin():
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
