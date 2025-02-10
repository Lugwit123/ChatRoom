"""消息模块"""
from app.domain.common.enums.message import MessageType, MessageStatus
from .internal.repository.base import BaseMessageRepository
from .internal.repository.group import GroupMessageRepository
from .internal.repository.private import PrivateMessageRepository

__all__ = [
    'MessageType',
    'MessageStatus',
    'BaseMessageRepository',
    'GroupMessageRepository',
    'PrivateMessageRepository'
]
