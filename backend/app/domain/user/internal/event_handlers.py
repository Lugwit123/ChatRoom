"""用户领域事件处理器"""
import Lugwit_Module as LM
from typing import Optional
from app.core.events.base import EventHandler
from app.domain.common.events import DomainEventType, UserEvent
from app.core.services import Services

lprint = LM.lprint

class UserEventHandler:
    """用户事件处理器"""
    
    def __init__(self):
        """初始化事件处理器"""
        self._event_bus = Services.get_event_bus()
        self._register_handlers()
    
    def _register_handlers(self):
        """注册事件处理器"""
        self._event_bus.subscribe(DomainEventType.USER_CREATED.value, self.handle_user_created)
        self._event_bus.subscribe(DomainEventType.USER_UPDATED.value, self.handle_user_updated)
        self._event_bus.subscribe(DomainEventType.USER_STATUS_CHANGED.value, self.handle_user_status_changed)
            
    async def handle_user_created(self, event: UserEvent) -> None:
        """处理用户创建事件"""
        try:
            lprint(f"处理用户创建事件: {event.username}")
            # 发送欢迎邮件
            # 初始化用户配置
            # 记录创建日志
        except Exception as e:
            lprint(f"处理用户创建事件失败: {str(e)}")
            
    async def handle_user_updated(self, event: UserEvent) -> None:
        """处理用户更新事件"""
        try:
            lprint(f"处理用户更新事件: {event.username}")
            # 更新缓存
            # 记录更新日志
            # 发送通知
        except Exception as e:
            lprint(f"处理用户更新事件失败: {str(e)}")

    async def handle_user_status_changed(self, event: UserEvent) -> None:
        """处理用户状态变更事件"""
        try:
            lprint(f"处理用户状态变更事件: {event.username}")
            # 更新用户状态缓存
            # 记录状态变更日志
            # 发送状态变更通知
        except Exception as e:
            lprint(f"处理用户状态变更事件失败: {str(e)}")

# 创建全局事件处理器实例
_user_event_handler = None

def get_user_event_handler() -> UserEventHandler:
    """获取用户事件处理器实例"""
    global _user_event_handler
    if _user_event_handler is None:
        _user_event_handler = UserEventHandler()
    return _user_event_handler 