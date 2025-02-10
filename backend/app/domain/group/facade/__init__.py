"""群组门面模块"""
from functools import lru_cache
from app.domain.group.facade.group_facade import GroupFacade

@lru_cache()
def get_group_facade() -> GroupFacade:
    """获取群组门面实例
    
    Returns:
        GroupFacade: 群组门面实例
    """
    return GroupFacade()
