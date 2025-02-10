"""领域基础仓储类"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.internal.base import Base
from app.core.base.internal.repository.base_repository import CoreBaseRepository

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(CoreBaseRepository[ModelType]):
    """领域基础仓储类
    
    继承自核心基础仓储类，可以在这里添加领域特定的功能
    """
    
    def __init__(self, model: Type[ModelType]):
        """初始化仓储
        
        Args:
            model: 模型类
        """
        super().__init__(model)

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
        return result.scalars().all()
        
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
            
    async def delete(self, id: int) -> None:
        """删除记录
        
        Args:
            id: 记录ID
        """
        try:
            query = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(query)
            return result.rowcount > 0
        except Exception as e:
            self.lprint(f"删除记录失败: {e}")
            raise
