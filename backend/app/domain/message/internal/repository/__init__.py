"""消息仓储模块"""
from .private import PrivateMessageRepository
from .group import GroupMessageRepository
from .base import BaseMessageRepository

__all__ = [
    'BaseMessageRepository',
    'GroupMessageRepository',
    'PrivateMessageRepository'
]
