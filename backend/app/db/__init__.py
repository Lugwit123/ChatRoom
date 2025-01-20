"""数据库相关模块，包含数据库初始化、连接管理和基础操作"""

import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')

import Lugwit_Module as LM

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

# 导入日志
lprint = LM.lprint

# 导入基类和数据库管理器
from .base import Base
from .database import DatabaseManager, get_session, create_session, get_db, cleanup_db, init_db

__all__ = [
    'DatabaseManager',
    'get_session',
    'create_session',
    'get_db',
    'cleanup_db',
    'init_db',
    'Base'
]
