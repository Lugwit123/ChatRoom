"""基础仓储类"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from typing import TypeVar, Generic, Type, Optional, List, Dict
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..internal.base import Base

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
        """初始化仓储
        
        Args:
            model: 模型类
            session: 数据库会话
        """
        self.lprint = LM.lprint
        self.model = model
        self._session = session
        
    async def create(self, **kwargs) -> ModelType:
        """创建新记录
        
        Args:
            **kwargs: 模型属性
            
        Returns:
            ModelType: 创建的记录
        """
        try:
            instance = self.model(**kwargs)
            self._session.add(instance)
            await self._session.flush()
            return instance
        except Exception as e:
            self.lprint(f"创建记录失败: {str(e)}")
            raise
            
    async def get(self, id: int) -> Optional[ModelType]:
        """根据ID获取记录
        
        Args:
            id: 记录ID
            
        Returns:
            Optional[ModelType]: 查找到的记录，如果不存在则返回None
        """
        try:
            query = select(self.model).where(self.model.id == id)
            result = await self._session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            self.lprint(f"获取记录失败: {str(e)}")
            raise
            
    async def get_all(self) -> List[ModelType]:
        """获取所有记录
        
        Returns:
            List[ModelType]: 记录列表
        """
        try:
            query = select(self.model)
            result = await self._session.execute(query)
            return result.scalars().all()
        except Exception as e:
            self.lprint(f"获取所有记录失败: {str(e)}")
            raise
            
    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """更新记录
        
        Args:
            id: 记录ID
            **kwargs: 要更新的属性
            
        Returns:
            Optional[ModelType]: 更新后的记录，如果记录不存在则返回None
        """
        try:
            query = update(self.model).where(self.model.id == id).values(**kwargs)
            await self._session.execute(query)
            return await self.get(id)
        except Exception as e:
            self.lprint(f"更新记录失败: {str(e)}")
            raise
            
    async def delete(self, id: int) -> bool:
        """删除记录
        
        Args:
            id: 记录ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            query = delete(self.model).where(self.model.id == id)
            result = await self._session.execute(query)
            return result.rowcount > 0
        except Exception as e:
            self.lprint(f"删除记录失败: {str(e)}")
            raise
