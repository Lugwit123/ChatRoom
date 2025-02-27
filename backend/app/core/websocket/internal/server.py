"""Socket.IO服务器管理模块

提供Socket.IO服务器的全局单例管理
"""
import socketio
from typing import Optional
import Lugwit_Module as LM

lprint = LM.lprint

# Use a function to get the container when needed
def get_container_instance():
    from app.core.di.container import get_container, set_container, Container
    try:
        return get_container()
    except RuntimeError:
        # 如果容器未初始化，则进行初始化
        container = Container()
        set_container(container)
        return container

class SocketServer:
    """Socket.IO服务器管理类
    
    提供Socket.IO服务器的全局单例管理，确保整个应用使用同一个Socket.IO实例
    """
    _instance = None
    _sio: Optional[socketio.AsyncServer] = None
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    @classmethod
    def init_server(cls, container: get_container_instance) -> Optional[socketio.AsyncServer]:
        """初始化Socket.IO服务器
        
        如果服务器实例不存在，则创建新实例
        如果已存在，则返回现有实例
        
        Args:
            container: 依赖注入容器
            
        Returns:
            socketio.AsyncServer: Socket.IO服务器实例
        """
        if cls._sio is None:
            cls._sio = socketio.AsyncServer(
                async_mode='asgi',
                cors_allowed_origins='*',
                logger=False,
                engineio_logger=False
            )
            
            # 延迟导入以避免循环依赖
            from ..facade.websocket_facade import WebSocketFacade
            websocket_facade = container.resolve(WebSocketFacade)
            websocket_facade.init_server(cls._sio)
            
            lprint("Socket.IO服务器初始化完成")
            
        return cls._sio
        
    @classmethod
    def get_server(cls) -> Optional[socketio.AsyncServer]:
        """获取Socket.IO服务器实例
        
        Returns:
            Optional[socketio.AsyncServer]: Socket.IO服务器实例，如果未初始化则返回None
        """
        return cls._sio 