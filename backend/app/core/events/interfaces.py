"""事件系统接口定义

提供事件系统的基础类型和接口定义
"""
from typing import Any, Callable, TypeVar, Generic, Dict, List, Protocol, runtime_checkable, Optional, Awaitable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

T = TypeVar('T')

class EventType(str, Enum):
    """事件类型枚举"""
    # 用户事件
    user_login = "user.login"
    user_logout = "user.logout"
    user_created = "user.created"
    user_updated = "user.updated"
    user_deleted = "user.deleted"
    user_status_changed = "user.status_changed"
    user_query = "user.query"  # 用户查询
    
    # 消息事件
    private_message_sent = "message.private.sent"
    group_message_sent = "message.group.sent"
    message_received = "message.received"
    message_read = "message.read"
    message_deleted = "message.deleted"
    
    # 群组事件
    group_query = "group.query"  # 群组查询
    group_member_check = "group.member.check"  # 群组成员检查
    
    # 设备事件
    device_connected = "device.connected"
    device_disconnected = "device.disconnected"
    device_status_changed = "device.status_changed"
    
    # WebSocket事件
    websocket_connected = "websocket.connected"
    websocket_disconnected = "websocket.disconnected"
    websocket_error = "websocket.error"

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
    
    def __lt__(self, other):
        if not isinstance(other, BaseEvent):
            return NotImplemented
        return self.created_at < other.created_at

@dataclass
class UserEvent:
    """用户相关事件"""
    event_type: EventType
    user_id: int
    username: str
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        if not isinstance(other, UserEvent):
            return NotImplemented
        return self.created_at < other.created_at

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
    _process_count: int = field(default=0)  # 处理计数器
    MAX_PROCESS_COUNT: int = 3  # 最大处理次数
    
    def __lt__(self, other):
        if not isinstance(other, MessageEvent):
            return NotImplemented
        return self.created_at < other.created_at
        
    def increment_process_count(self) -> bool:
        """增加处理计数，并返回是否可以继续处理"""
        self._process_count += 1
        return self._process_count <= self.MAX_PROCESS_COUNT

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
    
    def __lt__(self, other):
        if not isinstance(other, DeviceEvent):
            return NotImplemented
        return self.created_at < other.created_at

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
    
    def __lt__(self, other):
        if not isinstance(other, WebSocketEvent):
            return NotImplemented
        return self.created_at < other.created_at

# 修改事件处理器类型定义
EventHandler = Union[Callable[[Event], Any], Callable[[Event], Awaitable[Any]]]

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