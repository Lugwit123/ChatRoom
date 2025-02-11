"""领域事件定义"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class DomainEventType(Enum):
    """领域事件类型"""
    # 用户事件
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

@dataclass
class UserEvent:
    """用户相关事件"""
    event_type: str
    user_id: int
    username: str
    created_at: datetime
    data: Dict[str, Any]

@dataclass
class MessageEvent:
    """消息相关事件"""
    event_type: str
    message_id: int
    sender_id: int
    created_at: datetime
    recipient_id: Optional[int]
    group_id: Optional[int]
    data: Dict[str, Any]

@dataclass
class DeviceEvent:
    """设备相关事件"""
    event_type: str
    device_id: str
    user_id: int
    created_at: datetime
    ip_address: Optional[str]
    data: Dict[str, Any]

@dataclass
class WebSocketEvent:
    """WebSocket相关事件"""
    event_type: str
    sid: str
    created_at: datetime
    user_id: Optional[int]
    device_id: Optional[str]
    data: Dict[str, Any] 