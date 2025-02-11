"""基础事件接口定义"""
from typing import Protocol, TypeVar, Generic, Dict, Any, Callable, Awaitable, Union
from dataclasses import dataclass, field
from datetime import datetime

T = TypeVar('T')

class Event(Protocol):
    """事件基础协议"""
    event_type: str
    created_at: datetime

@dataclass
class BaseEvent:
    """事件基类"""
    event_type: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

# 事件处理器类型
EventHandler = Union[
    Callable[[Event], None],  # 同步处理器
    Callable[[Event], Awaitable[None]]  # 异步处理器
]

class EventBus(Protocol):
    """事件总线协议"""
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """订阅事件"""
        ...
        
    def publish(self, event: Event) -> None:
        """发布事件"""
        ...
        
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """取消订阅"""
        ... 