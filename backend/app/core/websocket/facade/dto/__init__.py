"""
WebSocket相关的数据传输对象
"""
from .websocket_dto import (
    ConnectionInfo,
    UserSession,
    DeviceSession,
    SessionManager
)

__all__ = [
    'ConnectionInfo',
    'UserSession',
    'DeviceSession',
    'SessionManager'
]
