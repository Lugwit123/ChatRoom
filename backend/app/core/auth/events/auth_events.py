"""认证事件定义"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from app.core.events.base import BaseEvent

class AuthEventType(Enum):
    """认证事件类型"""
    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    LOGIN_FAILED = "auth.login_failed"
    TOKEN_EXPIRED = "auth.token_expired"
    TOKEN_INVALID = "auth.token_invalid"

@dataclass
class AuthEvent(BaseEvent):
    """认证事件基类"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LoginEvent(AuthEvent):
    """登录事件"""
    def __init__(self, user_id: int, username: str, device_id: str, ip_address: str, **kwargs):
        super().__init__(
            event_type=AuthEventType.LOGIN.value,
            user_id=user_id,
            username=username,
            device_id=device_id,
            ip_address=ip_address,
            **kwargs
        )

@dataclass
class LogoutEvent(AuthEvent):
    """登出事件"""
    def __init__(self, user_id: int, username: str, device_id: str, **kwargs):
        super().__init__(
            event_type=AuthEventType.LOGOUT.value,
            user_id=user_id,
            username=username,
            device_id=device_id,
            **kwargs
        )

@dataclass
class LoginFailedEvent(AuthEvent):
    """登录失败事件"""
    def __init__(self, username: str, ip_address: str, reason: str, **kwargs):
        super().__init__(
            event_type=AuthEventType.LOGIN_FAILED.value,
            username=username,
            ip_address=ip_address,
            data={"reason": reason},
            **kwargs
        ) 