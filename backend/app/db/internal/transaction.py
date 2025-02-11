"""事务管理模块"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

class TransactionManager:
    """事务管理器
    
    提供事务管理功能，包括：
    1. 事务的开始和提交
    2. 异常时的回滚
    3. 嵌套事务支持
    """
    
    def __init__(self, session: AsyncSession):
        """初始化事务管理器
        
        Args:
            session: 数据库会话
        """
        self._session = session
        
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """开启事务
        
        使用示例:
        ```python
        async with transaction_manager.transaction() as session:
            # 在事务中执行操作
            session.add(some_object)
            await session.commit()
        ```
        
        Yields:
            AsyncSession: 数据库会话
        """
        try:
            async with self._session.begin():
                yield self._session
        except Exception:
            await self._session.rollback()
            raise
