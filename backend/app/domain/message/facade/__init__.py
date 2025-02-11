"""消息门面模块初始化"""
from typing import Optional
from functools import lru_cache
from app.core.di.container import get_container

from .message_facade import MessageFacade

@lru_cache()
def get_message_facade() -> MessageFacade:
    """获取消息门面实例
    
    Returns:
        MessageFacade: 消息门面实例
    """
    return get_container().resolve(MessageFacade)

# 导出MessageFacade类和工厂函数
__all__ = ['MessageFacade', 'get_message_facade']
