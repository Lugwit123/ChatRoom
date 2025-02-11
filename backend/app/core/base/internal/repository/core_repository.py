"""核心仓储模块
提供所有仓储的基础功能实现
"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.internal.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class CoreRepository(Generic[ModelType]):
    """核心仓储类，提供基本的CRUD操作
    
    这个类是所有仓储类的基类，提供了以下功能：
    1. 基本的CRUD操作（创建、读取、更新、删除）
    2. 异常处理和日志记录
    3. 事务管理
    4. 统一的会话管理 - 所有子类共享同一个会话实例
    
    使用示例:
    ```python
    class UserRepository(CoreRepository[User]):
        def __init__(self):
            super().__init__(User)
            
        async def get_by_username(self, username: str) -> Optional[User]:
            query = select(self.model).where(self.model.username == username)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
    ```
    """
    
    _shared_session: Optional[AsyncSession] = None
    
    @classmethod
    def set_session(cls, session: AsyncSession) -> None:
        """设置共享会话
        
        Args:
            session: 数据库会话
        """
        cls._shared_session = session
    
    @classmethod
    def get_session(cls) -> AsyncSession:
        """获取共享会话
        
        Returns:
            AsyncSession: 数据库会话
            
        Raises:
            RuntimeError: 如果会话未初始化
        """
        if cls._shared_session is None:
            raise RuntimeError("Database session not initialized. Please call set_session first.")
        return cls._shared_session
    
    def __init__(self, model: Type[ModelType]):
        """初始化仓储
        
        Args:
            model: 模型类
        """
        self.lprint = LM.lprint
        self.model = model
        self.session = self.get_session()

    async def create(self, **kwargs) -> ModelType:
        """创建新记录
        
        Args:
            **kwargs: 模型属性
            
        Returns:
            ModelType: 创建的记录
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.commit()
            await self.session.refresh(instance)
            return instance
        except Exception as e:
            self.lprint(f"创建记录失败: {e}")
            raise
            
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """根据ID获取记录
        
        Args:
            id: 记录ID
            
        Returns:
            Optional[ModelType]: 记录对象或None
        """
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def get_all_records(self) -> List[ModelType]:
        """获取所有记录
        
        Returns:
            List[ModelType]: 记录列表
        """
        query = select(self.model)
        result = await self.session.execute(query)
        return list(result.scalars().all())
        
    async def update(self, id: int, **kwargs) -> None:
        """更新记录
        
        Args:
            id: 记录ID
            **kwargs: 要更新的字段
        """
        try:
            query = update(self.model).where(self.model.id == id).values(**kwargs)
            await self.session.execute(query)
            await self.session.commit()
        except Exception as e:
            self.lprint(f"更新记录失败: {e}")
            raise
            
    async def delete(self, id: int) -> bool:
        """删除记录
        
        Args:
            id: 记录ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            query = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(query)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            self.lprint(f"删除记录失败: {e}")
            raise 