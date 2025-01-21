"""
基础仓储模块
定义所有仓储类的基础接口和通用操作
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """基础仓储接口
    
    定义了所有仓储类都应该实现的基本操作方法
    """
    
    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[T]:
        """根据ID查找实体"""
        pass
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """保存实体"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除实体"""
        pass
