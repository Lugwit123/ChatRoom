from typing import Optional, TYPE_CHECKING
from app.domain.common.models.tables import User


# 创建全局实例
if TYPE_CHECKING:
    from app.domain.user.facade.user_facade import UserFacade
    from app.domain.message.facade.message_facade import MessageFacade
    from app.core.websocket.facade.websocket_facade import WebSocketFacade
    from app.domain.device.facade.device_facade import DeviceFacade
    from app.core.auth.facade.auth_facade import AuthFacade


# 提供获取实例的函数
def get_user_facade() -> 'UserFacade':
    from app.domain.user.facade.user_facade import UserFacade
    user_facade = UserFacade()
    return user_facade

def get_message_facade() -> 'MessageFacade':
    from app.domain.message.facade.message_facade import MessageFacade
    message_facade = MessageFacade()
    return message_facade

def get_websocket_facade() -> 'WebSocketFacade':
    from app.core.websocket.facade.websocket_facade import WebSocketFacade
    websocket_facade = WebSocketFacade()
    return websocket_facade

def get_device_facade() -> 'DeviceFacade':
    from app.domain.device.facade.device_facade import DeviceFacade
    device_facade = DeviceFacade()
    return device_facade

def get_auth_facade() -> 'AuthFacade':
    from app.core.auth.facade.auth_facade import AuthFacade
    auth_facade = AuthFacade()
    return auth_facade

# 其他用户相关的操作... 