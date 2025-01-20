"""基础仓储类"""
from typing import TypeVar, Generic, Type, Optional, List, Dict
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

import Lugwit_Module as LM
lprint = LM.lprint

# 定义泛型类型变量
from .base import Base
ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """基础仓储类，提供基本的CRUD操作
    
    这个类是所有仓储类的基类，提供了以下功能：
    1. 基本的CRUD操作（创建、读取、更新、删除）
    2. 异常处理和日志记录
    3. 事务管理
    
    使用示例:
    ```python
    class UserRepository(BaseRepository[User]):
        def __init__(self, session: AsyncSession):
            super().__init__(User, session)
            
        async def get_by_username(self, username: str) -> Optional[User]:
            query = select(self.model).where(self.model.username == username)
            result = await self._session.execute(query)
            return result.scalar_one_or_none()
    ```
    """
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """初始化基础仓储
        
        Args:
            model: 模型类型
            session: 数据库会话
        """
        self.model = model
        self._session = session

    @property
    def session(self) -> AsyncSession:
        """获取数据库会话
        
        Returns:
            数据库会话
        """
        return self._session

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """根据ID获取实体
        
        Args:
            id: 实体ID
            
        Returns:
            找到的实体或None
        """
        try:
            query = select(self.model).where(self.model.id == id)
            result = await self._session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            lprint(f"获取实体失败: {str(e)}")
            return None

    async def get_all(self) -> List[ModelType]:
        """获取所有实体
        
        Returns:
            实体列表
        """
        try:
            query = select(self.model)
            result = await self._session.execute(query)
            return result.scalars().all()
        except Exception as e:
            lprint(f"获取所有实体失败: {str(e)}")
            return []

    async def create(self, entity: ModelType) -> Optional[ModelType]:
        """创建实体
        
        Args:
            entity: 要创建的实体
            
        Returns:
            创建的实体
            
        Raises:
            Exception: 创建失败时抛出
        """
        try:
            self._session.add(entity)
            await self._session.commit()
            await self._session.refresh(entity)
            return entity
        except Exception as e:
            await self._session.rollback()
            lprint(f"创建实体失败: {str(e)}")
            raise

    async def update(self, entity: ModelType, update_data: Dict[str, any] = None) -> Optional[ModelType]:
        """更新实体
        
        Args:
            entity: 要更新的实体
            update_data: 要更新的数据
            
        Returns:
            更新后的实体
            
        Raises:
            Exception: 更新失败时抛出
        """
        try:
            if update_data:
                for key, value in update_data.items():
                    setattr(entity, key, value)
            await self._session.merge(entity)
            await self._session.flush()
            await self._session.refresh(entity)
            return entity
        except Exception as e:
            lprint(f"更新实体失败: {str(e)}")
            raise

    async def delete(self, id: int) -> bool:
        """删除实体
        
        Args:
            id: 要删除的实体ID
            
        Returns:
            是否删除成功
            
        Raises:
            Exception: 删除失败时抛出
        """
        try:
            query = delete(self.model).where(self.model.id == id)
            result = await self._session.execute(query)
            return result.rowcount > 0
        except Exception as e:
            lprint(f"删除实体失败: {str(e)}")
            raise

    async def exists(self, id: int) -> bool:
        """检查实体是否存在
        
        Args:
            id: 要检查的实体ID
            
        Returns:
            实体是否存在
        """
        try:
            query = select(self.model).where(self.model.id == id)
            result = await self._session.execute(query)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            lprint(f"检查实体存在失败: {str(e)}")
            return False

    async def update_by_id(self, id: int, **kwargs) -> Optional[ModelType]:
        """根据ID更新实体的指定字段
        
        Args:
            id: 实体ID
            **kwargs: 要更新的字段和值
            
        Returns:
            更新后的实体或None
            
        Raises:
            Exception: 更新失败时抛出
        """
        try:
            query = update(self.model).where(self.model.id == id).values(**kwargs)
            await self._session.execute(query)
            return await self.get_by_id(id)
        except Exception as e:
            lprint(f"更新实体字段失败: {str(e)}")
            raise

    async def delete_by_filter(self, *criterion) -> int:
        """根据条件删除实体
        
        Args:
            *criterion: SQLAlchemy过滤条件
            
        Returns:
            删除的行数
            
        Raises:
            Exception: 删除失败时抛出
        """
        try:
            query = delete(self.model).where(*criterion)
            result = await self._session.execute(query)
            return result.rowcount
        except Exception as e:
            lprint(f"条件删除实体失败: {str(e)}")
            raise
