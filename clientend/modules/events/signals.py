"""
聊天室信号模块

提供所有与聊天相关的信号定义和处理。
这个模块定义了一个全局的信号类,用于在不同组件之间进行通信。
"""

from PySide6.QtCore import QObject, Signal
from typing import Any, Dict, Optional

class ChatSignals(QObject):
    """聊天相关的信号定义"""
    # 远程控制相关信号
    remote_control_accepted = Signal(str, str)  # (username, ip)
    remote_control_rejected = Signal(str, str, bool)  # (username, reason, is_custom)
    notification_closed = Signal()  # 通知窗口关闭信号
    message_received = Signal(object)  # 收到新消息的信号
    
    # 通知相关信号
    notification_requested = Signal(object)  # 请求显示通知
    notification_response = Signal(str, object)  # 通知响应(response_type, data)
    
    # ABC检查相关信号
    abc_check_received = Signal(object)  # 收到ABC检查消息
    abc_check_response = Signal(str, object)  # ABC检查响应
    
    # 状态相关信号
    status_changed = Signal(str)  # 状态改变
    blink_requested = Signal(str)  # 请求闪烁
    
    # 消息相关信号
    message_sent = Signal(object)  # 消息发送
    message_read = Signal(int)  # 消息已读(message_id)

# 创建全局信号实例
chat_signals = ChatSignals() 