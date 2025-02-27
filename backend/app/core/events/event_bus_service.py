"""事件总线服务

提供事件总线的全局访问点和管理功能
"""
import inspect
import Lugwit_Module as LM
from typing import Optional, Dict, List, Type, TypeVar, Any
import traceback
from .interfaces import (
    EventBus, Event, EventType, EventHandler,
    UserEvent, MessageEvent, DeviceEvent, WebSocketEvent
)
import asyncio
from enum import Enum

lprint = LM.lprint

T = TypeVar('T', bound=Event)

class EventHandlerNotFoundError(Exception):
    """找不到事件处理器时抛出的异常"""
    def __init__(self, event_type: EventType, message: Optional[str] = None):
        self.event_type = event_type
        self.message = message or f"未找到事件 {event_type} 的处理器"
        super().__init__(self.message)

class EventBusService:
    """事件总线服务"""
    
    def __init__(self):
        """初始化事件总线"""
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        lprint = LM.lprint
        
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """订阅事件
        
        Args:
            event_type: 事件类型(枚举)
            handler: 事件处理器
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        lprint(f"订阅事件: {event_type}")
        
    async def publish_event(self, event: Event) -> Optional[Any]:
        """发布事件
        
        Args:
            event: 事件对象
            
        Returns:
            Optional[Any]: 事件处理结果
            
        Raises:
            EventHandlerNotFoundError: 找不到事件处理器时抛出
            Exception: 事件处理过程中的其他错误
        """
        try:
            # 检查是否是消息事件，并验证处理次数
            if isinstance(event, MessageEvent):
                if not event.increment_process_count():
                    lprint(f"事件处理次数超过限制，停止处理: event_type={event.event_type}, message_id={event.message_id}")
                    return

            handlers = self._handlers.get(event.event_type)
            if not handlers:
                error_msg = (
                    f"未找到事件 {event.event_type} 的处理器\n"
                    f"当前已注册的事件类型: {[et for et in self._handlers.keys()]}"
                )
                lprint(error_msg)
                raise EventHandlerNotFoundError(event.event_type, error_msg)
                
            # lprint(f"\n事件 {event.event_type} 的处理器列表:")
            results = []
            for handler in handlers:
                try:
                    handler_name = handler.__name__ if hasattr(handler, '__name__') else str(handler)
                    handler_module = handler.__module__ if hasattr(handler, '__module__') else 'unknown'
                    
                    # 获取处理器的源文件位置和行号
                    try:
                        file_location = inspect.getfile(handler)
                        # 获取行号
                        lines, start_line = inspect.getsourcelines(handler)
                        end_line = start_line + len(lines) - 1
                        location_info = f"{file_location}:{start_line}-{end_line}"
                    except (TypeError, OSError):
                        location_info = 'unknown location'

                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(event)
                    else:
                        result = handler(event)
                        
                    if result is not None:
                        results.append(result)
                    lprint(f"处理器 {handler_name} 模块路径: {location_info} \n返回结果: {result}")
                    #lprint(f"aa\nbb")
                except Exception as e:
                    lprint(f"处理器 {handler_name} 模块路径: {location_info} \n执行失败: {str(e)}")
                    traceback.print_exc()
                    
            # 如果有多个处理器返回结果，返回第一个非None的结果
            for result in results:
                if result is not None:
                    return result
            return None
            
        except EventHandlerNotFoundError:
            raise
        except Exception as e:
            error_msg = f"事件 {event.event_type} 发布失败: {str(e)}"
            lprint(error_msg)
            traceback.print_exc()
            raise Exception(error_msg) from e

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """取消订阅
        
        Args:
            event_type: 事件类型(枚举)
            handler: 事件处理器
        """
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
            lprint(f"取消订阅事件: {event_type}")

    def get_subscribers(self, event_type: EventType) -> List[EventHandler]:
        """获取事件订阅者列表
        
        Args:
            event_type: 事件类型(枚举)
            
        Returns:
            List[EventHandler]: 订阅者列表
        """
        return self._handlers.get(event_type, []) 
