"""事件总线服务

提供事件总线的全局访问点和管理功能
"""
import Lugwit_Module as LM
from typing import Optional, Dict, List, Type, TypeVar, Any
import traceback
from .interfaces import (
    EventBus, Event, EventType, EventHandler,
    UserEvent, MessageEvent, DeviceEvent, WebSocketEvent
)
import asyncio

lprint = LM.lprint

T = TypeVar('T', bound=Event)

class EventBusService:
    """事件总线服务"""
    _instance: Optional['EventBusService'] = None
    _event_bus: Optional[EventBus] = None
    _handlers: Dict[str, List[EventHandler]] = {}
    _event_types: Dict[str, Type[Event]] = {
        'user': UserEvent,
        'message': MessageEvent,
        'device': DeviceEvent,
        'websocket': WebSocketEvent
    }

    def __new__(cls) -> 'EventBusService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._event_bus = EventBus()
            cls._instance._handlers = {}  # 初始化 _handlers
        return cls._instance

    @property
    def event_bus(self) -> EventBus:
        """获取事件总线实例"""
        if self._event_bus is None:
            self._event_bus = EventBus()
        return self._event_bus

    async def publish_event(self, event: Event) -> None:
        """发布事件
        
        Args:
            event: 事件对象
        """
        try:
            event_type = str(event.event_type.value if hasattr(event.event_type, 'value') else event.event_type)
            lprint(f"开始发布事件: {event_type}")
            handlers = self._handlers.get(event_type, [])
            lprint(f"找到 {len(handlers)} 个处理器")
            
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        lprint(f"执行异步处理器: {handler.__name__}")
                        await handler(event)
                    else:
                        lprint(f"执行同步处理器: {handler.__name__}")
                        handler(event)
                except Exception as handler_error:
                    lprint(f"处理器执行失败: {str(handler_error)}")
                    lprint(traceback.format_exc())
                    
            lprint(f"事件 {event_type} 处理完成")
            
        except Exception as e:
            lprint(f"发布事件失败: {str(e)}")
            lprint(traceback.format_exc())
            raise

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """订阅事件"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        lprint(f"订阅事件: {event_type}")

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """取消订阅"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
            lprint(f"取消订阅事件: {event_type}")

    def get_subscribers(self, event_type: str) -> List[EventHandler]:
        """获取事件订阅者列表
        
        Args:
            event_type: 事件类型
            
        Returns:
            List[EventHandler]: 订阅者列表
        """
        return self._handlers.get(event_type, []) 