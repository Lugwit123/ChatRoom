"""WebSocket管理器模块"""
import socketio
from typing import Optional

class WebSocketManager:
    """WebSocket管理器，管理全局 Socket.IO 实例"""
    _instance = None
    _sio: Optional[socketio.AsyncServer] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    @classmethod
    def init_server(cls) -> socketio.AsyncServer:
        """初始化 Socket.IO 服务器
        
        Returns:
            socketio.AsyncServer: Socket.IO 服务器实例
        """
        if cls._sio is None:
            cls._sio = socketio.AsyncServer(
                async_mode='asgi',
                cors_allowed_origins='*',
                logger=False,
                engineio_logger=False
            )
        return cls._sio
        
    @classmethod
    def get_server(cls) -> Optional[socketio.AsyncServer]:
        """获取 Socket.IO 服务器实例
        
        Returns:
            Optional[socketio.AsyncServer]: Socket.IO 服务器实例，如果未初始化则返回 None
        """
        return cls._sio
