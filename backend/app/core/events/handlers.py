"""事件处理器"""
from typing import Dict, Any, Optional
from app.core.events.interfaces import (
    EventType, Event, UserEvent, MessageEvent, WebSocketEvent
)
import Lugwit_Module as LM
import traceback

lprint = LM.lprint

class EventHandlers:
    """事件处理器集合"""
    
    @staticmethod
    async def register_handlers(event_bus):
        """注册事件处理器
        
        核心系统事件:
        - websocket_error: WebSocket错误
        - device_status_changed: 设备状态变更
        
        以下事件已移动到对应领域:
        1. 消息领域 (message_facade.py):
           - message.private.sent
           - message.group.sent
           - message.received
           - message.read
           - message.deleted
           
        2. 用户领域 (user_facade.py):
           - user.query
           - user.created
           
        3. 认证领域 (auth_facade.py):
           - user.login
           - user.logout
           
        4. WebSocket领域 (websocket_facade.py):
           - websocket.connected
           - websocket.disconnected
           - user.status_changed
        """
        # 只保留核心系统事件处理器
        event_bus.subscribe(EventType.websocket_error, EventHandlers._handle_websocket_error)
        event_bus.subscribe(EventType.device_status_changed, EventHandlers._handle_device_status_changed)
        
    @staticmethod
    async def _handle_websocket_error(event: Event) -> None:
        """处理WebSocket错误事件"""
        if not isinstance(event, WebSocketEvent):
            return
        lprint(f"WebSocket错误: {event.data.get('error', '未知错误')}")
        
    @staticmethod
    async def _handle_device_status_changed(event: Event) -> None:
        """处理设备状态变更事件"""
        if not isinstance(event, UserEvent):
            return
        lprint(f"设备状态变更: user_id={event.user_id}, status={event.data.get('status', '未知')}")

def get_core_event_handler() -> EventHandlers:
    """获取核心事件处理器实例
    
    Returns:
        EventHandlers: 事件处理器实例
    """
    return EventHandlers()