"""用户门面模块"""
from functools import lru_cache
from app.domain.user.facade.user_facade import UserFacade

@lru_cache()
def get_user_facade() -> UserFacade:
    """获取用户门面实例
    
    Returns:
        UserFacade: 用户门面实例
    """
    return UserFacade()
