"""数据库模块，提供统一的数据库操作接口"""
from .facade.database_facade import DatabaseFacade
from .internal.base import Base
from .repository.base_repository import BaseRepository

__all__ = [
    'DatabaseFacade',
    'Base',
    'BaseRepository'
]
