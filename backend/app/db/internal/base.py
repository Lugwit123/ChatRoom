"""SQLAlchemy Base 类和常用导入"""
from sqlalchemy.orm import DeclarativeBase, declarative_base
from sqlalchemy.ext.asyncio import AsyncAttrs

Base = declarative_base()

__all__ = ["Base"]
