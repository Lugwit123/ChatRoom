"""用户相关依赖"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import DatabaseManager
from app.domain.user.repository import UserRepository
from app.domain.user.service import UserService

async def get_user_repo(session: AsyncSession = Depends(DatabaseManager.get_session)) -> UserRepository:
    """获取用户仓储实例
    
    Args:
        session: 数据库会话
        
    Returns:
        用户仓储实例
    """
    return UserRepository(session)

async def get_user_service(repo: UserRepository = Depends(get_user_repo)) -> UserService:
    """获取用户服务实例
    
    Args:
        repo: 用户仓储
        
    Returns:
        用户服务实例
    """
    return UserService(repo)
