"""消息仓储包"""

from .private import PrivateMessageRepository
from .group import GroupMessageRepository

__all__ = ["PrivateMessageRepository", "GroupMessageRepository"]
