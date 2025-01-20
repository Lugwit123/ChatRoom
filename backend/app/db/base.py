"""
SQLAlchemy Base 类和常用导入
"""
from sqlalchemy.orm import DeclarativeBase, declarative_base
from sqlalchemy.ext.asyncio import AsyncAttrs

Base = declarative_base()

# 为了避免循环导入，我们在需要使用这些模型的地方再导入
__all__ = [
    "Base",
]

"""基础仓储类"""
from typing import Generic, List, Optional, Type, TypeVar
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

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
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
    ```
    """
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """初始化仓储
        
        Args:
            model: 实体模型类
            session: 数据库会话
        """
        self.model = model
        self.session = session

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """根据ID获取实体
        
        Args:
            id: 实体ID
            
        Returns:
            找到的实体或None
        """
        try:
            query = select(self.model).where(self.model.id == id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            print(f"获取实体失败: {e}")
            return None

    async def get_all(self) -> List[ModelType]:
        """获取所有实体
        
        Returns:
            实体列表
        """
        try:
            query = select(self.model)
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"获取所有实体失败: {e}")
            return []

    async def create(self, entity: ModelType) -> ModelType:
        """创建实体
        
        Args:
            entity: 要创建的实体
            
        Returns:
            创建的实体
        """
        try:
            self.session.add(entity)
            await self.session.flush()
            await self.session.refresh(entity)
            return entity
        except Exception as e:
            print(f"创建实体失败: {e}")
            raise

    async def update(self, entity: ModelType) -> ModelType:
        """更新实体
        
        Args:
            entity: 要更新的实体
            
        Returns:
            更新后的实体
        """
        try:
            await self.session.merge(entity)
            await self.session.flush()
            await self.session.refresh(entity)
            return entity
        except Exception as e:
            print(f"更新实体失败: {e}")
            raise

    async def delete(self, entity: ModelType) -> bool:
        """删除实体
        
        Args:
            entity: 要删除的实体
            
        Returns:
            是否删除成功
        """
        try:
            await self.session.delete(entity)
            await self.session.flush()
            return True
        except Exception as e:
            print(f"删除实体失败: {e}")
            return False

    async def delete_by_id(self, id: int) -> bool:
        """根据ID删除实体
        
        Args:
            id: 实体ID
            
        Returns:
            是否删除成功
        """
        try:
            entity = await self.get_by_id(id)
            if entity:
                return await self.delete(entity)
            return False
        except Exception as e:
            print(f"根据ID删除实体失败: {e}")
            return False
