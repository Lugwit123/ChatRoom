"""
SQLAlchemy 基类定义
"""
from typing import Any
from sqlalchemy.orm import declarative_base, declared_attr

class BaseModel:
    """所有模型的基类"""
    
    @declared_attr
    def __tablename__(cls) -> str:
        """返回表名"""
        return cls.__name__.lower()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self) -> str:
        """返回字符串表示"""
        values = ", ".join(
            f"{column.name}={getattr(self, column.name)!r}"
            for column in self.__table__.columns
        )
        return f"{self.__class__.__name__}({values})"
    
    def get(self, key: str, default: Any = None) -> Any:
        """类似于字典的get方法，获取对象属性"""
        return getattr(self, key, default)

# 创建基类
Base = declarative_base(cls=BaseModel)

__all__ = ['Base']
