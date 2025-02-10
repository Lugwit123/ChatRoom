"""
聊天消息处理相关代码
"""
import json
import os
import asyncio
import traceback
import socket
from typing import Any, Dict, Optional, Callable, Union, Coroutine, cast, TYPE_CHECKING
import aiohttp
from PySide6.QtCore import QObject, Slot, Signal
from PySide6.QtWidgets import QWidget, QMessageBox

import Lugwit_Module as LM
lprint = LM.lprint

from ..message import MessageType, MessageTargetType, MessageContentType

if TYPE_CHECKING:
    from PySide6.QtCore import SignalInstance

class ChatRoom(QObject):
    """与 JavaScript 交互的处理类"""
    
    # 定义信号
    message_received = Signal(str)  # type: ignore
    
    def __init__(self, parent_com=None, app=None):
        super().__init__()
        self.parent_com = parent_com
        self.app = app
        self.sid = ""  # 初始化 sid
        self.parent_widget: Optional[QWidget] = None
        if self.parent_com:
            self.parent_widget = getattr(self.parent_com, 'parent_widget', None)
        self.base_url = f'http://{socket.gethostname()}:1026'
        
        # 连接信号到槽
        self.message_received.connect(self._handle_message)

    def _get_enum(self, enum_name: str) -> Any:
        """获取枚举类型"""
        enum_map = {
            'MessageType': MessageType,
            'MessageTargetType': MessageTargetType,
            'MessageContentType': MessageContentType
        }
        return enum_map.get(enum_name)

    @Slot(str, result=bool)
    def pythonFunction(self, message: str) -> bool:
        """处理从 QML 发来的消息"""
        try:
            self.message_received.emit(message)
            return True
        except Exception as e:
            lprint(f"处理消息失败: {str(e)}")
            return False

    def _handle_message(self, message: str) -> None:
        """处理接收到的消息"""
        try:
            # 将字符串消息转换为字典
            message_data = json.loads(message)
            # 使用 asyncio.create_task 来处理异步调用
            asyncio.create_task(self.handle_remote_control_message(message_data))
        except Exception as e:
            lprint(f"处理远程控制消息失败: {str(e)}")
            lprint(traceback.format_exc())

    async def handle_remote_control_message(self, message_data: Dict[str, Any]) -> None:
        """处理远程控制消息"""
        try:
            if self.parent_com and hasattr(self.parent_com, 'start_remote_control'):
                content = message_data.get('content', {})
                ip = content.get('ip')
                if ip:
                    await self.parent_com.start_remote_control(ip, 5900, 'OC.123456')
        except Exception as e:
            lprint(f"处理远程控制消息失败: {str(e)}")
            lprint(traceback.format_exc())

    async def send_message(self, **message_data) -> Optional[Dict[str, Any]]:
        """发送消息到服务器"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/api/messages/send',
                    json=message_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        lprint(f"消息发送成功: {result}")
                        return result
                    else:
                        error_text = await response.text()
                        lprint(f"消息发送失败: {error_text}")
                        return None
        except Exception as e:
            lprint(f"发送消息失败: {str(e)}")
            lprint(traceback.format_exc())
            return None

    async def _send_remote_control_message(self, sender: str, recipient: str, role_type: str) -> None:
        """发送远程控制消息"""
        try:
            msg_type = self._get_enum('MessageType')
            target_type = self._get_enum('MessageTargetType')
            content_type = self._get_enum('MessageContentType')
            
            # 构造消息数据
            message_data = {
                "sender": sender,
                "recipient": recipient,
                "message_type": msg_type.remote_control.value,
                "target_type": target_type.user.value,
                "content_type": content_type.plain_text.value,
                "content": {
                    "type": role_type,
                    "ip": socket.gethostbyname(socket.gethostname())
                },
                "popup_message": True
            }
            
            # 发送消息
            result = await self.send_message(**message_data)
            if result:
                lprint(f"已发送远程控制请求: {sender} -> {recipient}")
            else:
                if self.parent_widget:
                    reply = QMessageBox.warning(
                        parent=self.parent_widget,
                        title="发送失败",
                        text="发送远程控制请求失败",
                        button0=QMessageBox.StandardButton.Ok,
                        button1=QMessageBox.StandardButton.Ok
                    )
        except Exception as e:
            lprint(f"发送远程控制消息失败: {str(e)}")
            lprint(traceback.format_exc())
            if self.parent_widget:
                reply = QMessageBox.warning(
                    parent=self.parent_widget,
                    title="发送失败",
                    text=f"发送远程控制请求失败: {str(e)}",
                    button0=QMessageBox.StandardButton.Ok,
                    button1=QMessageBox.StandardButton.Ok
                )

    @Slot()
    def exit_app(self) -> None:
        """退出应用"""
        try:
            if self.app:
                self.app.quit()
        except Exception as e:
            lprint(f"退出应用失败: {str(e)}")
            lprint(traceback.format_exc())

    @Slot()
    def get_sid(self) -> str:
        """获取会话ID"""
        try:
            return self.sid
        except Exception as e:
            lprint(f"获取会话ID失败: {str(e)}")
            lprint(traceback.format_exc())
            return ""

    async def _handle_new_message_async(self, message: str) -> bool:
        """异步处理新消息"""
        try:
            if isinstance(message, str):
                message_data = json.loads(message)
                message_type = message_data.get('message_type')
                
                handlers: Dict[int, Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]] = {
                    1: self.handle_private_message,  # chat
                    8: self.handle_remote_control_message,  # remote_control
                    9: self.handle_open_path  # open_path
                }
                
                if handler := handlers.get(message_type):
                    await handler(message_data)
                    return True
            return False
        except Exception as e:
            lprint(f"Error in handleNewMessage: {e}")
            return False

    async def handle_private_message(self, message_data: dict) -> None:
        """处理私聊消息"""
        if self.parent_com and self.parent_com.parent_widget:
            self.parent_com.parent_widget.start_blinking()

    async def handle_open_path(self, message_data: dict) -> None:
        """处理打开路径消息"""
        content = message_data.get('content', {})
        local_path = content.get('localPath')
        if local_path:
            if os.path.exists(local_path):
                os.startfile(os.path.dirname(local_path))
            elif os.path.exists('G:'+local_path[2:]):
                os.startfile(os.path.dirname('G:'+local_path[2:]))
            else:
                if self.parent_com and self.parent_com.parent_widget:
                    QMessageBox.information(
                        self.parent_com.parent_widget,
                        "信息提示",
                        "文件或者文件夹不存在！"
                    ) 