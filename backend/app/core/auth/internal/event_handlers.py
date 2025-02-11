"""认证事件处理器"""
import Lugwit_Module as LM
from typing import Optional
from app.core.events.interfaces import Event
from app.core.events.base import EventHandler
from app.core.auth.events.auth_events import AuthEventType, AuthEvent, LoginEvent, LogoutEvent
from app.core.services import Services

lprint = LM.lprint

class AuthEventHandler:
    """认证事件处理器"""
    
    def __init__(self):
        """初始化事件处理器"""
        self._event_bus = Services.get_event_bus()
        self._register_handlers()
    
    def _register_handlers(self):
        """注册事件处理器"""
        self._event_bus.subscribe(AuthEventType.LOGIN.value, self.handle_login)
        self._event_bus.subscribe(AuthEventType.LOGOUT.value, self.handle_logout)
        self._event_bus.subscribe(AuthEventType.LOGIN_FAILED.value, self.handle_login_failed)
    
    async def handle_login(self, event: LoginEvent) -> None:
        """处理登录事件"""
        try:
            lprint(f"处理用户登录事件: {event.username}")
            # 更新用户最后登录时间
            # 记录登录日志
            # 更新设备状态
        except Exception as e:
            lprint(f"处理用户登录事件失败: {str(e)}")
    
    async def handle_logout(self, event: LogoutEvent) -> None:
        """处理登出事件"""
        try:
            lprint(f"处理用户登出事件: {event.username}")
            # 清理会话
            # 更新设备状态
            # 记录登出日志
        except Exception as e:
            lprint(f"处理用户登出事件失败: {str(e)}")
            
    async def handle_login_failed(self, event: AuthEvent) -> None:
        """处理登录失败事件"""
        try:
            lprint(f"处理登录失败事件: {event.username}, 原因: {event.data.get('reason')}")
            # 记录失败日志
            # 更新失败计数
            # 检查是否需要锁定账户
        except Exception as e:
            lprint(f"处理登录失败事件失败: {str(e)}")

# 创建全局事件处理器实例
_auth_event_handler = None

def get_auth_event_handler() -> AuthEventHandler:
    """获取认证事件处理器实例"""
    global _auth_event_handler
    if _auth_event_handler is None:
        _auth_event_handler = AuthEventHandler()
    return _auth_event_handler 