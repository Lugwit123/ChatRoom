"""
WebSocket服务的依赖注入配置
"""
import Lugwit_Module as LM
from app.core.di.container import Container
from app.core.auth.facade.auth_facade import AuthFacade
from .interfaces import IConnectionManager, IRoomManager, IWebSocketEventHandler
from .internal.manager import ConnectionManager, RoomManager
from .internal.handlers import WebSocketHandlers
from .facade.websocket_facade import WebSocketFacade

lprint = LM.lprint

def register_websocket_services(container: Container) -> None:
    """注册WebSocket相关的服务
    
    Args:
        container: 依赖注入容器
    """
    try:
        lprint("开始注册WebSocket服务...")
        
        # 注册基础服务
        container.register(IConnectionManager, ConnectionManager)
        container.register(IRoomManager, RoomManager)
        
        # 创建并注册管理器实例
        connection_manager = ConnectionManager()
        room_manager = RoomManager()
        
        container.register_singleton(IConnectionManager, connection_manager)
        container.register_singleton(IRoomManager, room_manager)
        
        # 获取认证门面
        auth_facade = container.resolve(AuthFacade)
        
        # 创建事件处理器
        event_handler = WebSocketHandlers(connection_manager, room_manager, auth_facade)
        container.register_singleton(IWebSocketEventHandler, event_handler)
        
        # 创建WebSocket门面
        websocket_facade = WebSocketFacade()
        container.register_singleton(WebSocketFacade, websocket_facade)
        
        lprint("WebSocket服务注册完成")
        
    except Exception as e:
        lprint(f"注册WebSocket服务失败: {str(e)}")
        raise 