"""基础仓储类"""
from typing import TypeVar, Generic, Type, Optional, List, Union, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlmodel.sql.expression import SelectOfScalar

import Lugwit_Module as LM

lprint = LM.lprint

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """基础仓储类，提供通用的数据库操作方法"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        """根据ID获取单个对象"""
        query = select(self.model).where(self.model.id == id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_field(self, session: AsyncSession, field: str, value: Any) -> Optional[ModelType]:
        """根据字段名和值获取单个对象"""
        query = select(self.model).where(getattr(self.model, field) == value)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        session: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelType]:
        """获取多个对象"""
        query = select(self.model).offset(skip).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()
    
    async def create(self, session: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """创建新对象"""
        db_obj = self.model.from_orm(obj_in)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
    
    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """更新对象"""
        obj_data = db_obj.dict()
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
    
    async def remove(self, session: AsyncSession, *, id: int) -> Optional[ModelType]:
        """删除对象"""
        obj = await self.get(session=session, id=id)
        if obj:
            await session.delete(obj)
            await session.commit()
        return obj
    
    async def count(self, session: AsyncSession) -> int:
        """获取对象总数"""
        result = await session.execute(select(self.model))
        return len(result.scalars().all())
    
    async def exists(self, session: AsyncSession, id: Any) -> bool:
        """检查对象是否存在"""
        obj = await self.get(session=session, id=id)
        return obj is not None
