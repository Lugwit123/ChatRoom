"""WebSocket模块初始化"""
from .facade.websocket_facade import WebSocketFacade
from .internal.server import SocketServer

__all__ = ['WebSocketFacade', 'SocketServer']