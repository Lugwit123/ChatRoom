"""
消息模块枚举定义文件

本文件定义了消息系统中使用的所有枚举类型，包括：
1. MessageType: 消息类型枚举
   - private_chat: 私聊消息
   - group_chat: 群聊消息
   - system: 系统消息
   - broadcast: 广播消息
   - self_chat: 自己发给自己的消息
   - chat_history: 聊天历史记录
   - validation: 验证消息
   - user_list_update: 用户列表更新
   - error: 错误消息
   - get_users: 获取用户列表
   - remote_control: 远程控制消息
   - open_path: 打开路径消息

2. MessageContentType: 消息内容类型枚举
   - rich_text: 富文本消息
   - url: 超链接
   - audio: 音频
   - image: 图片
   - video: 视频
   - file: 文件
   - plain_text: 纯文本
   - user_list: 用户列表
   - html: HTML内容

3. MessageStatus: 消息状态枚举
   - unread: 未读
   - read: 已读
   - sending: 发送中
   - sent: 已发送
   - delivered: 已送达
   - success: 发送成功
   - failed: 发送失败
   - deleted: 已删除
   - recalled: 已撤回
   - unknown: 未知状态

4. MessageTargetType: 消息目标类型枚举
   - user: 用户
   - group: 群组

5. MessageDirection: 消息方向枚举
   - response: 响应消息
   - request: 请求消息

"""
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
