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
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QMessageBox
import socketio
import sys
from dotenv import load_dotenv

# 加载环境变量
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)

sys.path.append("D:\\TD_Depot\\Software\\Lugwit_syncPlug\\lugwit_insapp\\trayapp\\Lib")
import Lugwit_Module as LM
lprint = LM.lprint

from ..message import MessageType, MessageTargetType, MessageContentType

if TYPE_CHECKING:
    from clientend.pyqt_chatroom import MainWindow

class ChatRoom(QObject):
    """与 JavaScript 交互的处理类"""
    
    # 定义信号
    message_received = Signal(object)  # 收到新消息的信号
    connection_status = Signal(bool)  # 连接状态信号
    
    def __init__(self, parent_com: Optional['MainWindow'] = None, app=None):
        super().__init__()
        self._parent_window = parent_com  # 保存父窗口引用
        self.app = app
        self.sid = ""  # 初始化 sid
        self.parent_widget: Optional[QWidget] = None
        if self._parent_window:
            self.parent_widget = getattr(self._parent_window, 'parent_widget', None)
            
        # 从环境变量获取配置
        self.server_ip = os.getenv('SERVER_IP', '127.0.0.1')  # 从环境变量获取服务器IP
        self.server_port = int(os.getenv('SERVER_PORT', '1026'))
        self.ws_port = int(os.getenv('WS_PORT', '1026'))
        self.ws_ping_interval = int(os.getenv('WS_PING_INTERVAL', '20'))
        self.ws_ping_timeout = int(os.getenv('WS_PING_TIMEOUT', '10'))
        self.ws_close_timeout = int(os.getenv('WS_CLOSE_TIMEOUT', '5'))
        self.max_reconnect_attempts = int(os.getenv('WS_MAX_RECONNECT_ATTEMPTS', '5'))
        self.reconnect_delay = int(os.getenv('WS_INITIAL_RECONNECT_DELAY', '1'))
        
        # 设置URL
        self.base_url = f'http://{self.server_ip}:{self.server_port}'
        
        # Socket.IO相关
        self.sio = socketio.AsyncClient(logger=False, engineio_logger=False)
        self.token: Optional[str] = None
        self.reconnect_attempts = 0
        
        # 注册Socket.IO事件处理器
        self._register_handlers()
        
        # 连接信号到槽
        self.message_received.connect(self._handle_message)
        
        lprint(f"ChatRoom初始化完成: server={self.server_ip}, port={self.server_port}")

    def _register_handlers(self):
        """注册Socket.IO事件处理器"""
        
        @self.sio.event
        async def connect():
            lprint('Socket.IO连接成功!')
            self.connection_status.emit(True)
            self.reconnect_attempts = 0

        @self.sio.event
        async def disconnect():
            """处理断开连接事件"""
            lprint('Socket.IO连接断开')
            self.connection_status.emit(False)
            if self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                delay = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), 30)
                lprint(f"准备第{self.reconnect_attempts}次重连，延迟{delay}秒")
                await asyncio.sleep(delay)
                await self.connect_ws()
            else:
                lprint("达到最大重连次数，停止重连")

        @self.sio.event
        async def connect_error(data):
            """处理连接错误事件"""
            lprint(f'Socket.IO连接错误: {data}')
            self.connection_status.emit(False)
            if self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                delay = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), 30)
                lprint(f"准备第{self.reconnect_attempts}次重连，延迟{delay}秒")
                await asyncio.sleep(delay)
                await self.connect_ws()
            else:
                lprint("达到最大重连次数，停止重连")

        @self.sio.on('message')
        async def on_message(data):
            try:
                lprint(f'收到消息: {data}')
                self.message_received.emit(data)
            except Exception as e:
                lprint(f'处理消息错误: {str(e)}')
                lprint(traceback.format_exc())

        @self.sio.on('authentication_response')
        async def on_auth_response(data):
            if data.get('success'):
                lprint('Socket.IO认证成功')
            else:
                lprint(f'Socket.IO认证失败: {data.get("error")}')

    def get_parent_window(self) -> Optional['MainWindow']:
        """获取父窗口实例"""
        return self._parent_window

    def get_parent_widget(self) -> Optional[QWidget]:
        """获取父窗口的 widget"""
        if self._parent_window and hasattr(self._parent_window, 'parent_widget'):
            return cast(QWidget, self._parent_window.parent_widget)
        return None

    def _get_enum(self, enum_name: str) -> Any:
        """获取枚举类型"""
        enum_map = {
            'MessageType': MessageType,
            'MessageTargetType': MessageTargetType,
            'MessageContentType': MessageContentType
        }
        return enum_map.get(enum_name)

    def pythonFunction(self, message: str) -> bool:
        """处理从 QML 发来的消息"""
        try:
            data = json.loads(message)
            self.message_received.emit(data)
            return True
        except Exception as e:
            lprint(f"处理消息失败: {str(e)}")
            return False

    def _handle_message(self, message_data: dict) -> None:
        """处理接收到的消息"""
        try:
            lprint(f"处理消息: {message_data}")
            # 在这里添加消息处理逻辑
            asyncio.create_task(self._handle_new_message_async(json.dumps(message_data)))
        except Exception as e:
            lprint(f"消息处理错误: {str(e)}")
            traceback.print_exc()

    async def handle_remote_control_message(self, message_data: dict) -> None:
        """处理远程控制消息"""
        try:
            content = message_data.get('content', {})
            sender = message_data.get('sender_username')
            recipient = message_data.get('recipient_username')
            
            main_window = self.get_parent_window()
            if not main_window:
                return
                
            # 如果我是接收者
            if recipient == main_window.userName:
                # 获取远程控制类型和IP
                control_type = content.get('type')
                remote_ip = content.get('ip')
                
                if not all([control_type, remote_ip]):
                    lprint(f"远程控制消息缺少必要参数: {content}")
                    return
                    
                # 显示确认对话框
                parent_widget = self.get_parent_widget()
                if parent_widget:
                    reply = QMessageBox.question(
                        parent_widget,
                        "远程控制请求",
                        f"用户 {sender} 请求{control_type}远程控制\nIP: {remote_ip}\n是否允许？",
                        button0=QMessageBox.StandardButton.Yes,
                        button1=QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        # 启动VNC连接
                        if hasattr(main_window, 'connect_vnc'):
                            main_window.connect_vnc(remote_ip, 5900, 'OC.123456')
                            
            # 如果我是发送者，收到接收者的响应
            elif sender == main_window.userName:
                # 获取响应状态
                status = content.get('status')
                if status == 'accepted':
                    lprint(f"远程控制请求已被 {recipient} 接受")
                elif status == 'rejected':
                    parent_widget = self.get_parent_widget()
                    if parent_widget:
                        QMessageBox.warning(
                            parent_widget,
                            "远程控制请求",
                            f"用户 {recipient} 拒绝了远程控制请求",
                            button0=QMessageBox.StandardButton.Ok,
                            button1=QMessageBox.StandardButton.Ok
                        )
                        
        except Exception as e:
            lprint(f"处理远程控制消息失败: {str(e)}")
            lprint(traceback.format_exc())

    async def send_message(self, **message_data) -> Optional[Dict[str, Any]]:
        """发送消息到服务器"""
        try:
            if not self.sio.connected:
                lprint("Socket.IO未连接，尝试重新连接")
                await self.connect_ws()
                
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
            self.connection_status.emit(False)
            await self._handle_connection_error()
            return None

    async def _send_remote_control_message(self, sender: str, recipient: str, role_type: str) -> None:
        """发送远程控制消息"""
        try:
            msg_type = self._get_enum('MessageType')
            target_type = self._get_enum('MessageTargetType')
            content_type = self._get_enum('MessageContentType')
            
            # 获取本机IP地址
            local_ip = socket.gethostbyname(socket.gethostname())
            
            # 构造消息数据
            message_data = {
                "sender": sender,
                "recipient": recipient,
                "message_type": msg_type.remote_control.value,
                "target_type": target_type.user.value,
                "content_type": content_type.plain_text.value,
                "content": {
                    "type": role_type,
                    "ip": local_ip  # 使用本机IP
                },
                "popup_message": True
            }
            
            # 发送消息
            result = await self.send_message(**message_data)
            if result:
                lprint(f"已发送远程控制请求: {sender} -> {recipient}")
            else:
                parent_widget = self.get_parent_widget()
                if parent_widget:
                    QMessageBox.warning(
                        parent_widget,
                        "发送失败",
                        "发送远程控制请求失败",
                        button0=QMessageBox.StandardButton.Ok,
                        button1=QMessageBox.StandardButton.Ok
                    )
        except Exception as e:
            lprint(f"发送远程控制消息失败: {str(e)}")
            lprint(traceback.format_exc())

    def exit_app(self) -> None:
        """退出应用"""
        try:
            if self.app:
                self.app.quit()
        except Exception as e:
            lprint(f"退出应用失败: {str(e)}")
            lprint(traceback.format_exc())

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
                
                handlers = {
                    1: self.handle_private_message,  # chat
                    8: self.handle_remote_control_message,  # remote_control
                    9: self.handle_open_path  # open_path
                }
                
                if handler := handlers.get(message_type):
                    await handler(message_data)
                    return True
            return False
        except Exception as e:
            lprint(f'Error in handleNewMessage: {e}')
            return False

    async def handle_private_message(self, message_data: dict) -> None:
        """处理私聊消息"""
        if self._parent_window and self._parent_window.parent_widget:
            self._parent_window.parent_widget.start_blinking()

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
                if self._parent_window and self._parent_window.parent_widget:
                    QMessageBox.information(
                        self._parent_window.parent_widget,
                        "信息提示",
                        "文件或者文件夹不存在！"
                    )

    async def connect_ws(self, token: Optional[str] = None):
        """连接到Socket.IO服务器"""
        try:
            if token:
                self.token = token
                
            if not self.token:
                lprint("未提供token，无法连接Socket.IO")
                return
                
            if self.sio.connected:
                lprint("Socket.IO已连接")
                return
                
            lprint(f"正在连接Socket.IO: {self.base_url}")
            
            # 设置认证信息
            auth = {'token': self.token}
            
            await self.sio.connect(
                self.base_url,
                auth=auth,
                transports=['websocket'],
                wait_timeout=10,
                socketio_path='socket.io'
            )
            
            lprint("等待Socket.IO连接建立...")
            await asyncio.sleep(1)  # 等待认证完成
            
            if not self.sio.connected:
                lprint("Socket.IO连接失败")
                self.connection_status.emit(False)
                await self._handle_connection_error()
            else:
                lprint("Socket.IO连接成功")
                self.connection_status.emit(True)
                self.reconnect_attempts = 0
            
        except Exception as e:
            lprint(f"Socket.IO连接失败: {str(e)}")
            lprint(traceback.format_exc())
            self.connection_status.emit(False)
            await self._handle_connection_error()
            
    async def _handle_connection_error(self) -> None:
        """处理连接错误"""
        try:
            if self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                delay = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), 30)  # 指数退避，最大30秒
                lprint(f"准备第{self.reconnect_attempts}次重连，延迟{delay}秒")
                await asyncio.sleep(delay)
                await self.connect_ws()  # 使用已保存的token重连
            else:
                lprint("达到最大重连次数，停止重连")
        except Exception as e:
            lprint(f"重连过程中出错: {str(e)}")
            lprint(traceback.format_exc())
            
    async def close(self):
        """关闭连接"""
        if self.sio.connected:
            await self.sio.disconnect()
            self.connection_status.emit(False)
            lprint("Socket.IO连接已关闭")

    async def connect_websocket(self, token: str):
        """连接WebSocket服务器"""
        try:
            lprint("开始连接Socket.IO服务器...")
            await self.connect_ws(token)
            lprint("Socket.IO连接成功")
        except Exception as e:
            lprint(f"连接Socket.IO服务器失败: {str(e)}")
            lprint(traceback.format_exc()) 