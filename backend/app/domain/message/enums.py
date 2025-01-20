"""消息相关枚举类型"""
from enum import Enum

class MessageType(str, Enum):
    """消息类型枚举"""
    private_chat = "private_chat"
    group_chat = "group_chat"
    system = "system"
    broadcast = "broadcast"
    self_chat = "self_chat"
    chat_history = "chat_history"
    validation = "validation"
    user_list_update = "user_list_update"
    error = "error"
    get_users = "get_users"
    remote_control = "remote_control"
    open_path = "open_path"

class MessageContentType(str, Enum):
    """消息内容类型枚举"""
    rich_text = 'rich_text'  # 富文本消息
    url = 'url'              # 超链接
    audio = 'audio'          # 音频
    image = 'image'          # 图片
    video = 'video'          # 视频
    file = 'file'            # 文件
    plain_text = 'plain_text' # 纯文本
    user_list = 'user_list'
    html = 'html'

class MessageStatus(str, Enum):
    """消息状态枚举"""
    unread = "unread"
    read = "read"
    sending = "sending"
    sent = "sent"
    delivered = "delivered"
    success = "success"
    failed = "failed"
    deleted = "deleted"
    recalled = "recalled"
    unknown = "unknown"

class MessageTargetType(str, Enum):
    """消息目标类型枚举"""
    user = "user"
    group = "group"

class MessageDirection(str, Enum):
    """消息方向枚举"""
    response = "response"
    request = "request"
