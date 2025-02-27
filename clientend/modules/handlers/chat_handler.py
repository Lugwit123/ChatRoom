"""
聊天消息处理相关代码
"""
import json
import os
import asyncio
import traceback
import socket
from typing import Any, Dict, Optional, Callable, Union, Coroutine, cast, TYPE_CHECKING, Protocol, TypeVar, runtime_checkable
import aiohttp
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QWidget, QMessageBox
import socketio
import sys
from dotenv import load_dotenv
import time
from ..events.signals import chat_signals  # 添加导入
from datetime import datetime
from zoneinfo import ZoneInfo

from ..ui.waiting_response_window import WaitingResponseWindow

# 加载环境变量
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)

sys.path.append("D:\\TD_Depot\\Software\\Lugwit_syncPlug\\lugwit_insapp\\trayapp\\Lib")
import Lugwit_Module as LM
lprint = LM.lprint

from ..types.types import (MessageType, MessageTargetType, MessageContentType,
                        MessageDirection, MessageBase, ButtonConfig, ButtonId, NotificationConfig,
                        DEFAULT_BUTTON_CONFIG, RemoteControlResponseStatus, RemoteControlResponse)

from ..ui.notice_win import create_notification_window
from ..ui.reject_reason_dialog import RejectReasonDialog
from ..auth.auth_manager import AuthManager
from ..vnc.vnc_connector import VNCConnector
if TYPE_CHECKING:
    from clientend.pyqt_chatroom import MainWindow
    
@runtime_checkable
class MainWindowProtocol(Protocol):
    """主窗口协议，定义必需的属性和方法"""
    userName: str
    project_info: Dict[str, Any]
    central_widget: QWidget  # 修改为 central_widget
    start_blinking: Callable[[], None]
    restart_application: Callable[[], None]
    exit_application: Callable[[], None]
    chat_handler: Any

T = TypeVar('T')

class ChatHandler(QObject):
    """与 JavaScript 交互的处理类"""
    
    # 定义信号
    message_received = Signal(object)  # 收到新消息的信号
    connection_status = Signal(bool)  # 连接状态信号
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self, parent_com: Union['MainWindow', None] = None, app=None):
        if not hasattr(self, '_initialized'):  # 防止重复初始化
            super().__init__()
            self._initialized = True
            self._parent_window = parent_com
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
            
            # 设置URL和命名空间
            self.base_url = f'http://{self.server_ip}:{self.server_port}'
            self.namespace = '/chat/private'  # 使用固定的命名空间
            
            # Socket.IO相关
            engineio_opts = {
                'request_timeout': 30,  # 请求超时时间
                'http_session': None,
                'ssl_verify': False,  # 禁用SSL验证以避免证书问题
            }
            
            self.sio = socketio.AsyncClient(
                logger=False,
                engineio_logger=False,
                reconnection=False,  # 禁用内置重连，使用我们自己的重连机制
                handle_sigint=False,
                **engineio_opts
            )
            
            self.token: Optional[str] = None
            self.is_connected = False
            self.is_connecting = False
            self.connection_lost_time = None
            self.reconnect_attempts = 0  # 添加重连尝试计数器
            
            # 添加事件处理器属性
            self.on_connect: Optional[Callable[[], None]] = None
            self.on_disconnect: Optional[Callable[[], None]] = None
            
            
            # 注册Socket.IO事件处理器
            self._register_handlers()
            
            # 连接信号到槽
            self.message_received.connect(self._handle_message)

            self.vnc_connector = VNCConnector()
            self.auth_manager = AuthManager.get_instance()
            
            self.waiting_windows : Dict[str,WaitingResponseWindow] = {} # 存储等待响应的窗口
            
            lprint(f"ChatRoom初始化完成: server={self.server_ip}, port={self.server_port}, namespace={self.namespace}")

    @classmethod
    def get_instance(cls) -> 'ChatHandler':
        if not cls._instance:
            cls._instance = ChatHandler()
        return cls._instance

    def _register_handlers(self):
        """注册Socket.IO事件处理器"""
        try:
            @self.sio.event(namespace=self.namespace)
            async def connect():
                await self._on_connect()
                
            @self.sio.event(namespace=self.namespace)
            async def disconnect():
                await self._on_disconnect()
                
            @self.sio.event(namespace=self.namespace)
            async def connect_error(data):
                lprint(f"连接错误: {data}")
                self.is_connected = False
                self.is_connecting = False
                self.connection_status.emit(False)
                
            @self.sio.on('message', namespace=self.namespace)
            async def on_message(data):
                lprint(f"收到消息: {data}")
                await self._on_message(data)
                
            @self.sio.on('authentication_response', namespace=self.namespace)
            async def on_auth_response(data):
                if data.get('success'):
                    lprint('认证成功')
                else:
                    lprint(f'认证失败: {data.get("error")}')
                    
            lprint("Socket.IO事件处理器注册完成")
            
        except Exception as e:
            lprint(f"注册Socket.IO事件处理器失败: {str(e)}")
            traceback.print_exc()

    def get_parent_window(self) -> Optional[MainWindowProtocol]:
        """获取父窗口实例"""
        if self._parent_window:
            return cast(MainWindowProtocol, self._parent_window)
        return None

    def get_parent_widget(self) -> Optional[QWidget]:
        """获取父窗口的 widget"""
        parent = self.get_parent_window()
        if parent:
            return parent  # 返回主窗口实例
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

    async def handle_remote_control_message(self, message_data: Dict[str, Any]) -> None:
        """处理远程控制消息"""
        try:
            # 处理接收到的远程消息
            content = message_data.get('content', {})
            sender = message_data.get('sender_username', '')
            recipient = message_data.get('recipient_username', '')
            message_id = message_data.get('id')
            direction = message_data.get('direction', 'unknown')  # 获取消息方向
            
            
            lprint(f"发送者: {sender}, 接收者: {recipient}, 消息ID: {message_id}, 方向: {direction}")
            
            # 获取主窗口实例
            main_window = self.get_parent_window()
            if not main_window:
                lprint("错误：找不到主窗口")
                return
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                    lprint(f"解析后的content: {content}")
                except json.JSONDecodeError:
                    lprint(f"解析远程控制消息内容失败: {content}")
                    return  
            status = content.get("status")
            # 如果是请求消息
            if recipient == self.auth_manager.get_current_user():
                lprint(f"当前用户 {main_window.userName} 是接收者")
                if status in ["accepted","rejected"]:
                    lprint("接受者不处理完成的消息")
                    return
                # 获取远程控制类型和IP
                remote_ip = content.get('ip')
                sender_nickname = content.get('nickname', sender)
                
                lprint(f"远程IP: {remote_ip}, 发送者昵称: {sender_nickname}")
                        
                # 创建消息对象
                message = MessageBase(
                    sender=str(sender),
                    recipient=str(recipient),
                    content={
                        'ip': remote_ip,
                        'nickname': sender_nickname,
                        'message_id': message_id
                    },
                    message_type=MessageType.remote_control.value,
                    direction='request',
                    popup_message=True
                )
                        
                # 自定义按钮配置
                button_config: ButtonConfig = {
                    'accept': '接受控制',
                    'close': '拒绝'
                }
                
                lprint("创建通知窗口...")
                # 创建通知窗口
                notification_window = create_notification_window(
                    image_path=None,
                    message=message,
                    result="",
                    button_config=button_config,
                    chat_signals=chat_signals
                )
                
                # 处理窗口响应
                def handle_accept(username: str, ip: str):
                    lprint(f"用户接受了远程控制请求: {username}, {ip}")
                    response = RemoteControlResponse(
                        status=RemoteControlResponseStatus.accepted,
                        reason='用户同意远程控制',
                        nickname=main_window.userName,
                        ip=remote_ip
                    )
                    
                    # 发送响应消息到服务器
                    asyncio.create_task(self.send_message(
                        message_type=MessageType.remote_control.value,
                        content=response.to_dict(),
                        recipient_username=sender,
                        direction='response',
                        reference_id=message_id
                    ))
                    
                    # 启动VNC服务器
                    self.vnc_connector.start_vnc_server()

                def handle_reject(username: str, reason: str, is_custom: bool):
                    lprint(f"用户拒绝了远程控制请求: {username}, 原因: {reason}")
                    response = RemoteControlResponse(
                        status=RemoteControlResponseStatus.rejected,
                        reason=reason,
                        nickname=main_window.userName,
                        ip=remote_ip
                    )
                    
                    # 发送响应消息到服务器
                    asyncio.create_task(self.send_message(
                        message_type=MessageType.remote_control.value,
                        content=response.to_dict(),
                        recipient_username=sender,
                        direction='response',
                        reference_id=message_id
                    ))

                # 连接窗口的信号到响应处理函数
                notification_window.request_accepted.connect(handle_accept)
                notification_window.request_rejected.connect(handle_reject)
                
                notification_window.showNormal()
                notification_window.raise_()  # 确保窗口在最前
                    
            # 如果当前用户是发送者
            if sender == self.auth_manager.get_current_user():
                status = content.get('status')
                if status == 'rejected':
                    # 获取拒绝理由
                    reason = content.get('reason', '对方拒绝了远程控制请求')
                    # 更新等待窗口显示拒绝理由
                    waiting_window = self.waiting_windows.get(recipient)
                    if waiting_window:
                        waiting_window.handle_response(content)
                        waiting_window.reponseLableFromServer.set_text(f"对方拒绝:{reason}")
                elif status == 'accepted':
                    # 关闭等待窗口
                    waiting_window = self.waiting_windows.get(recipient)
                    if waiting_window:
                        waiting_window.handle_response(content)
                        # 启动VNC客户端连接
                        remote_ip = content.get('ip')
                        if remote_ip:
                            self.vnc_connector.connect_to_vnc(remote_ip)
                        # 移除窗口引用
                        del self.waiting_windows[recipient]
                        
        except Exception as e:
            lprint(f"处理远程控制消息失败: {str(e)}")
            traceback.print_exc()

    async def check_connection(self) -> bool:
        """检查连接状态
        
        Returns:
            bool: 是否连接正常
        """
        try:
            if not self.sio or not self.sio.connected:
                return False
                
            # 发送ping消息
            await self.sio.emit('ping', namespace=self.namespace)
            return True
            
        except Exception as e:
            lprint(f"连接检查失败: {str(e)}")
            return False

    async def send_message(self, **message_data) -> Optional[Dict[str, Any]]:
        """发送消息到服务器
        
        Returns:
            Optional[Dict[str, Any]]: 服务器响应，包含以下字段：
                - status: 'success' 或 'error'
                - message_id: 消息ID（成功时）
                - public_id: 消息公开ID（成功时）
                - timestamp: 消息时间戳（成功时）
                - message: 错误信息（失败时）
        """
        try:
            # 先检查连接状态
            if not await self.check_connection():
                lprint("连接检查失败，无法发送消息")
                return None
                
            # 使用WebSocket发送消息
            try:
                # 创建Future对象来等待响应
                future = asyncio.Future()
                
                def ack_callback(*args):
                    """Socket.IO回调函数"""
                    try:
                        if args:
                            response = args[0] if len(args) == 1 else args
                            if not future.done():
                                future.set_result(response)
                    except Exception as e:
                        if not future.done():
                            future.set_exception(e)
                
                # 发送消息并设置回调
                await self.sio.emit('message', message_data, namespace='/chat/private', callback=ack_callback)
                lprint(f"消息发送成功: {message_data}")
                
                # 等待响应，设置超时
                try:
                    response = await asyncio.wait_for(future, timeout=5.0)  # 5秒超时
                    lprint(f"服务器响应: {response}")
                    
                    # 检查响应状态
                    if response and isinstance(response, dict):
                        if response.get('status') == 'success':
                            lprint(f"消息已保存到服务器，ID: {response.get('message_id')}")
                        else:
                            lprint(f"消息处理失败: {response.get('message')}")
                    return response
                except asyncio.TimeoutError:
                    lprint("等待服务器响应超时")
                    return None
                
            except Exception as e:
                lprint(f"WebSocket消息发送失败: {str(e)}")
                traceback.print_exc()
                self.connection_status.emit(False)
                await self._handle_connection_error()
                return None
                
        except Exception as e:
            lprint(f"发送消息失败: {str(e)}")
            traceback.print_exc()
            self.connection_status.emit(False)
            await self._handle_connection_error()
            return None

    async def _send_remote_control_message(self, option: Dict[str, Any]) -> None:
        """发送远程控制消息"""
        if not self.vnc_connector.ensure_vnc_ready():
            return
        
        recipient: str = option.get('username', "")
        current_user = self.auth_manager.get_current_user()
        lprint(f"当前用户: {current_user}, 请求对象: {recipient}")
        waiting_window = None
        try:
            # 构造消息数据
            message_data = {
                'recipient_username': recipient,
                "message_type": MessageType.remote_control.value,
                "direction": MessageDirection.request.value,
                "popup_message": True,
                "content": {"status":"wait_server_return_message_id"}
            }

            # 显示等待响应窗口
            dialog = WaitingResponseWindow(recipient)
            dialog.show()
            dialog.raise_()  # 确保窗口在最前
            self.waiting_windows[recipient]=dialog
            
            # 发送消息
            try:
                # 使用send_message方法发送，它已经处理了回调
                response = await self.send_message(**message_data)
                if response and isinstance(response, dict):
                    if response.get('status') == 'success':
                        message_id = response.get('message_id')
                        dialog.reponseLableFromServer.setText(f"服务器回应远程控制请求ID: {message_id}")
                        lprint(f"远程控制请求已发送，ID: {message_id}")
                        return message_id
                    else:
                        error_msg = response.get('message', '未知错误')
                        lprint(f"远程控制请求发送失败: {error_msg}")
                else:
                    lprint("远程控制请求发送失败: 服务器未返回有效响应")
                
            except Exception as e:
                lprint(f"发送消息时发生错误: {str(e)}")
                traceback.print_exc()
            
            # 如果到这里，说明发送失败
            if waiting_window:
                waiting_window.close()
            return None
                
        except Exception as e:
            lprint(f"发送远程控制消息失败: {str(e)}")
            traceback.print_exc()
            if waiting_window:
                waiting_window.close()
            return None

    async def update_remote_control_message(self, message_id: Optional[str], response_data: dict) -> None:
        """更新远程控制消息状态
        
        Args:
            message_id: 消息ID
            response_data: 响应数据，包含状态和原因
        """
        try:
            if not message_id:
                lprint("无法更新消息：缺少消息ID")
                return
                
            # 构造更新数据
            update_data = {
                "message_id": message_id,
                "content": {
                    "status": response_data.get("status"),
                    "reason": response_data.get("reason"),
                    "response_time": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
                },
                "direction": "response"  # 添加响应方向
            }
            
            # 发送更新请求
            await self.sio.emit(
                "update_message",
                update_data,
                namespace=self.namespace
            )
            lprint(f"已发送消息更新请求: {update_data}")
            
        except Exception as e:
            lprint(f"更新远程控制消息失败: {str(e)}")
            traceback.print_exc()


    def exit_app(self) -> None:
        """退出应用"""
        try:
            if self.app:
                self.app.quit()
        except Exception as e:
            lprint(f"退出应用失败: {str(e)}")
            traceback.print_exc()

    def get_sid(self) -> str:
        """获取会话ID"""
        try:
            return self.sid
        except Exception as e:
            lprint(f"获取会话ID失败: {str(e)}")
            traceback.print_exc()
            return ""

    async def _handle_new_message_async(self, message: str) -> bool:
        """异步处理新消息"""
        try:
            if isinstance(message, str):
                message_data = json.loads(message)
                message_type = message_data.get('message_type')
                lprint(f"收到消息数据: {message_data}")
                
                # 检查消息类型是否是字符串
                if isinstance(message_type, str):
                    message_type = {
                        'remote_control': MessageType.remote_control.value,
                        'chat': MessageType.chat.value,
                        'open_path': MessageType.open_path.value
                    }.get(message_type, message_type)
                    
                # 确保message_type是整数
                try:
                    message_type = int(message_type)
                except (TypeError, ValueError):
                    lprint(f"无效的消息类型: {message_type}")
                    return False
                
                handlers = {
                    MessageType.chat.value: self.handle_private_message,  # chat
                    MessageType.remote_control.value: self.handle_remote_control_message,  # remote_control
                    MessageType.open_path.value: self.handle_open_path  # open_path
                }
                
                if handler := handlers.get(message_type):
                    lprint(f"准备调用消息处理器: {handler.__name__}, 消息类型: {message_type}")
                    await handler(message_data)
                    lprint(f"消息处理完成: 处理器={handler.__name__}, 消息类型={message_type}")
                    return True
                else:
                    lprint(f"未找到消息类型 {message_type} 的处理器")
                    return False
            return False
        except Exception as e:
            lprint(f'处理新消息失败: {str(e)}')
            traceback.print_exc()
            return False

    async def handle_private_message(self, message_data: dict) -> None:
        """处理私聊消息"""
        try:
            # 获取父窗口实例
            main_window = self.get_parent_window()
            if main_window:
                # 调用闪烁方法
                main_window.start_blinking()
        except Exception as e:
            lprint(f"处理私聊消息失败: {str(e)}")
            traceback.print_exc()

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

    async def connect_to_server(self) -> bool:
        """连接到服务器
        
        Returns:
            bool: 是否连接成功
        """
        if not self.token:
            lprint("未设置token，无法连接")
            return False
            
        if self.is_connecting:
            lprint("正在连接中，跳过重复连接")
            return False
            
        if self.is_connected and self.sio.connected:
            lprint("已经连接到服务器")
            return True
            
        try:
            self.is_connecting = True
            
            # 如果已经连接，先断开
            if self.sio.connected:
                await self.sio.disconnect()
                await asyncio.sleep(1)  # 等待断开完成
                
            # 设置认证信息
            auth = {
                'token': self.token
            }
            
            # 连接到服务器
            lprint("开始连接到Socket.IO服务器...")
            
            try:
                await self.sio.connect(
                    self.base_url,
                    auth=auth,
                    namespaces=[self.namespace],
                    transports=['websocket'],
                    wait_timeout=30,  # 增加等待超时时间
                    socketio_path='socket.io'
                )
                
                # 等待连接完成
                connection_timeout = 30  # 30秒连接超时
                start_time = time.time()
                
                while time.time() - start_time < connection_timeout:
                    if self.sio.connected:
                        lprint("Socket.IO连接已建立")
                        self.is_connected = True
                        self.is_connecting = False
                        self.reconnect_attempts = 0  # 重置重连计数
                        return True
                        
                    await asyncio.sleep(0.5)  # 更频繁地检查连接状态
                    
                lprint(f"连接超时(超过{connection_timeout}秒)")
                return False
                
            except asyncio.TimeoutError:
                lprint("连接超时")
                return False
            except aiohttp.ClientError as e:
                lprint(f"网络错误: {str(e)}")
                return False
            except Exception as e:
                lprint(f"连接过程中出错: {str(e)}")
                traceback.print_exc()
                return False
                
        except Exception as e:
            lprint(f"连接失败: {str(e)}")
            traceback.print_exc()
            return False
        finally:
            self.is_connecting = False

    async def _on_connect(self):
        """连接成功的处理"""
        try:
            self.is_connected = True
            self.is_connecting = False
            self.reconnect_attempts = 0  # 重置重连计数
            lprint("WebSocket连接成功")
            
            # 发送连接状态信号
            self.connection_status.emit(True)
            
            # 调用连接成功回调
            if self.on_connect:
                self.on_connect()
                
        except Exception as e:
            lprint(f"处理连接成功事件失败: {str(e)}")
            traceback.print_exc()

    async def _on_disconnect(self):
        """断开连接的处理"""
        try:
            if not self.is_connected:  # 如果已经是断开状态，不重复处理
                return
                
            self.is_connected = False
            lprint("WebSocket连接断开")
            
            # 发送连接状态信号
            self.connection_status.emit(False)
            
            # 调用断开连接回调
            if self.on_disconnect:
                self.on_disconnect()
                
        except Exception as e:
            lprint(f"处理断开连接事件失败: {str(e)}")
            traceback.print_exc()

    async def _on_message(self, data):
        """处理收到的消息"""
        try:
            lprint(f"收到消息: {data}")      
            # 处理其他类型的消息
            if isinstance(data, dict):
                self.message_received.emit(data)
            
        except Exception as e:
            lprint(f"处理消息失败: {str(e)}")
            traceback.print_exc()

    async def _handle_connection_error(self) -> None:
        """处理连接错误"""
        try:
            if self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                delay = min(30, self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)))  # 指数退避，最大30秒
                lprint(f"准备第{self.reconnect_attempts}次重连，延迟{delay}秒")
                
                # 确保连接已断开
                if self.sio.connected:
                    await self.sio.disconnect()
                    await asyncio.sleep(1)  # 等待断开完成
                    
                await asyncio.sleep(delay)
                await self.connect_to_server()  # 使用已保存的token重连
            else:
                lprint("达到最大重连次数，停止重连")
                self.is_connected = False
                self.connection_status.emit(False)
        except Exception as e:
            lprint(f"重连过程中出错: {str(e)}")
            traceback.print_exc()
            self.is_connected = False
            self.connection_status.emit(False)
            
    async def close(self):
        """关闭连接"""
        try:
            if self.sio and self.sio.connected:
                await self.sio.disconnect()
                self.is_connected = False
                self.connection_status.emit(False)
        except Exception as e:
            lprint(f"关闭连接失败: {str(e)}")
            traceback.print_exc()
