"""事件系统接口定义

提供事件系统的基础类型和接口定义
"""
from typing import Any, Callable, TypeVar, Generic, Dict, List, Protocol, runtime_checkable, Optional, Awaitable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

T = TypeVar('T')

class EventType(Enum):
    """事件类型枚举"""
    # 用户事件
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_STATUS_CHANGED = "user.status_changed"
    
    # 消息事件
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_READ = "message.read"
    MESSAGE_DELETED = "message.deleted"
    
    # 设备事件
    DEVICE_CONNECTED = "device.connected"
    DEVICE_DISCONNECTED = "device.disconnected"
    DEVICE_STATUS_CHANGED = "device.status_changed"
    
    # WebSocket事件
    WEBSOCKET_CONNECTED = "websocket.connected"
    WEBSOCKET_DISCONNECTED = "websocket.disconnected"
    WEBSOCKET_ERROR = "websocket.error"

@runtime_checkable
class Event(Protocol):
    """事件基础协议"""
    event_type: EventType
    created_at: datetime

@dataclass
class BaseEvent:
    """事件基类"""
    event_type: EventType
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserEvent:
    """用户相关事件"""
    event_type: EventType
    user_id: int
    username: str
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MessageEvent:
    """消息相关事件"""
    event_type: EventType
    message_id: int
    sender_id: int
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    recipient_id: Optional[int] = field(default=None)
    group_id: Optional[int] = field(default=None)

@dataclass
class DeviceEvent:
    """设备相关事件"""
    event_type: EventType
    device_id: str
    user_id: int
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = field(default=None)

@dataclass
class WebSocketEvent:
    """WebSocket相关事件"""
    event_type: EventType
    sid: str
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[int] = field(default=None)
    device_id: Optional[str] = field(default=None)

# 修改事件处理器类型定义
EventHandler = Union[Callable[[Event], None], Callable[[Event], Awaitable[None]]]

@runtime_checkable
class EventSubscriber(Protocol):
    """事件订阅者协议"""
    def handle_event(self, event: Event) -> None:
        """处理事件"""
        ...

class EventBus:
    """事件总线"""
    _subscribers: Dict[str, List[EventHandler]]

    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        if event_type.value not in self._subscribers:
            self._subscribers[event_type.value] = []
        self._subscribers[event_type.value].append(handler)

    def publish(self, event: Event) -> None:
        """发布事件
        
        Args:
            event: 事件对象
        """
        handlers = self._subscribers.get(event.event_type.value, [])
        for handler in handlers:
            handler(event)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """取消订阅
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        if event_type.value in self._subscribers:
            self._subscribers[event_type.value].remove(handler) 