"""事务管理模块"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Callable, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, DBAPIError

class TransactionError(Exception):
    """事务错误"""
    pass

class RetryableError(TransactionError):
    """可重试的事务错误"""
    pass

class TransactionManager:
    """事务管理器
    
    提供事务管理功能，包括：
    1. 事务的开始和提交
    2. 异常时的回滚
    3. 嵌套事务支持
    4. 事务重试机制
    """
    
    def __init__(self, session: AsyncSession):
        """初始化事务管理器
        
        Args:
            session: 数据库会话
        """
        self._session = session
        self._retry_exceptions = (DBAPIError,)  # 可以根据需要添加其他可重试的异常
        self._max_retries = 3
        self._retry_delay = 0.1  # 初始重试延迟（秒）
        
    @asynccontextmanager
    async def transaction(self, 
                        retries: int = None,
                        retry_delay: float = None,
                        retry_exceptions: tuple = None) -> AsyncGenerator[AsyncSession, None]:
        """开启事务
        
        Args:
            retries: 最大重试次数，None表示使用默认值
            retry_delay: 重试延迟（秒），None表示使用默认值
            retry_exceptions: 可重试的异常类型，None表示使用默认值
            
        Yields:
            AsyncSession: 数据库会话
            
        Raises:
            TransactionError: 事务执行失败
        """
        retries = retries if retries is not None else self._max_retries
        retry_delay = retry_delay if retry_delay is not None else self._retry_delay
        retry_exceptions = retry_exceptions if retry_exceptions is not None else self._retry_exceptions
        
        attempt = 0
        last_error = None
        
        while attempt <= retries:
            if attempt > 0:
                delay = retry_delay * (2 ** (attempt - 1))  # 指数退避
                lprint(f"事务重试第 {attempt} 次，延迟 {delay} 秒")
                await asyncio.sleep(delay)
            
            try:
                async with self._session.begin() as transaction:  # 使用普通事务而不是嵌套事务
                    try:
                        yield self._session
                        await transaction.commit()  # 提交事务
                        return  # 成功完成，退出循环
                    except Exception as e:
                        await transaction.rollback()  # 回滚事务
                        raise  # 重新抛出异常以触发外层事务的处理
                        
            except retry_exceptions as e:
                last_error = e
                attempt += 1
                if attempt <= retries:
                    lprint(f"事务执行失败: {e}，准备重试")
                    continue
                lprint(f"事务重试次数已达上限 ({retries})")
                raise RetryableError(f"事务重试失败: {str(last_error)}")
                
            except Exception as e:
                lprint(f"事务执行出现不可重试的错误: {e}")
                raise TransactionError(f"事务执行失败: {str(e)}")
                
    @asynccontextmanager
    async def in_transaction(self, 
                           retry_policy: Optional[dict] = None) -> AsyncGenerator[AsyncSession, None]:
        """在事务中执行操作的便捷方法
        
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
        retry_policy = retry_policy or {}
        async with self.transaction(**retry_policy) as session:
            yield session
