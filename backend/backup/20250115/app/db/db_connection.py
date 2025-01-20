"""
数据库连接和会话管理

本模块提供了三种不同的数据库会话管理方式：
1. get_session(): 用于依赖注入场景
2. create_session(): 用于直接创建会话
3. init_db(): 用于数据库初始化

每种方式有其特定用途和最佳实践场景。
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging
from Lugwit_Module import lprint
from app.db.schemas import Base

# 加载环境变量
load_dotenv()

# 获取数据库URL
DATABASE_URL = os.getenv("DATABASE_URL")

lprint(f"数据库URL: {DATABASE_URL}")
# 获取 SQLAlchemy 的日志记录器
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 生产环境中设为 False
    future=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
    pool_timeout=60,    # 增加连接超时时间
    pool_recycle=1800,  # 每30分钟回收连接
    pool_pre_ping=True, # 在每次连接前ping一下数据库
    connect_args={
        "command_timeout": 60,  # 命令超时时间
    }
)

# 创建异步会话工厂
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_session():
    """获取数据库会话，专用于依赖注入场景
    
    这个函数是一个异步生成器，主要用于FastAPI的依赖注入系统。
    它提供了完整的会话生命周期管理，包括：
    1. 创建会话
    2. 自动提交或回滚事务
    3. 自动关闭会话
    
    与create_session()的区别：
    - get_session()是生成器，用yield返回会话
    - 适合在依赖注入和上下文管理器中使用
    - 自动处理事务和会话生命周期
    """
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        lprint(f"数据库操作失败: {e}")
        raise
    finally:
        await session.close()

async def create_session():
    """创建一个新的数据库会话，用于直接使用场景
    
    这个函数直接返回一个新的会话对象，主要用于需要手动管理会话生命周期的场景。
    使用此函数时需要注意：
    1. 需要手动调用commit()或rollback()
    2. 需要手动关闭会话
    3. 建议使用try/finally确保会话被正确关闭
    
    与get_session()的区别：
    - create_session()直接返回会话对象
    - 需要手动管理事务和会话生命周期
    - 更灵活，但需要更多代码
    """
    return async_session()

async def get_db():
    """获取数据库会话，专用于FastAPI的依赖注入系统
    
    这个函数是FastAPI依赖注入系统的入口点。
    它提供了与get_session()相同的功能，但是：
    1. 直接管理会话，不依赖于get_session()
    2. 避免创建多层生成器
    3. 提供更清晰的错误处理
    """
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        lprint(f"数据库操作失败: {e}")
        raise
    finally:
        await session.close()

async def init_db():
    """初始化数据库，创建所有表结构
    
    这个函数使用engine.begin()而不是普通会话，因为：
    1. 数据库初始化是特殊操作，直接使用engine创建表结构
    2. 不需要普通的会话管理
    3. 不需要事务管理
    4. engine.begin()提供了自动的事务和连接管理
    5. 特别适合DDL（数据定义语言）操作
    
    注意：这个函数只应该在初始化数据库时调用，不用于普通的数据库操作
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    lprint("数据库连接初始化成功")
