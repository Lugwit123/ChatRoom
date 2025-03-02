"""
主应用程序入口
"""
import ctypes
import sys
import os
import atexit
import datetime
from typing import Optional, Dict, Any, TextIO

os.environ['QT_API'] = 'pyside6'

import time
import psutil
import asyncio
import socket
import traceback
import yaml
import fire
import subprocess
from pywinauto import Application
from dotenv import load_dotenv
from qasync import QEventLoop, QApplication, asyncSlot, asyncClose
import Lugwit_Module as LM
lprint = LM.lprint
import platform
import json

# 全局变量用于存储退出原因
exit_reason = "程序正常退出"

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)
sys.path.append(current_dir)

                
                
                
def init_exit_logging():
    """初始化退出日志记录"""
    global exit_log_file
    try:
        log_dir = os.getenv('LOG_DIR', 'A:/temp/chat/privateRoomLog')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'exit_log.txt')
        exit_log_file = open(log_path, 'a', encoding='utf-8')
        lprint(f"退出日志文件已初始化: {log_path}")
    except Exception as e:
        lprint(f"初始化退出日志失败: {str(e)}")


SERVER_IP =os.getenv('SERVER_IP','192.168.110.60')
# 加载环境变量
os.chdir(os.path.dirname(__file__))
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)  # 强制覆盖已存在的环境变量
    lprint(f"已加载环境变量文件: {env_path}")
else:
    lprint(f"环境变量文件不存在: {env_path}")
os.environ['SERVER_IP'] = SERVER_IP
hostname = socket.gethostname()
tray_icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'logo.png')
if SERVER_IP=='192.168.112.233':
    tray_icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'logo_fqq.png')


# SERVER_IP = os.getenv('SERVER_IP')
lprint(f"服务器IP: {SERVER_IP}")  # 打印服务器IP以便调试
SERVER_PORT = int(os.getenv('SERVER_PORT', '1026'))
WS_PORT = int(os.getenv('WS_PORT', '1026'))
LOG_DIR = os.getenv('LOG_DIR', 'A:/temp/chat/privateRoomLog')

# 确保必要的目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 从文件读取服务器IP地址（如果环境变量中没有设置）
if not os.getenv('SERVER_IP'):
    try:
        server_ip_file = os.path.join(LOG_DIR, 'server_ip_address.txt')
        if os.path.exists(server_ip_file):
            with open(server_ip_file, "r") as f:
                SERVER_IP = f.read().strip()
            os.environ['SERVER_IP'] = SERVER_IP
            lprint(f"从文件加载服务器IP: {SERVER_IP}")
    except Exception as e:
        lprint(f"Error reading server IP: {e}")

# 根据主机名选择Qt后端
from qasync import QEventLoop, QApplication, asyncSlot
from PySide6.QtCore import (QRect, Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve)
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSystemTrayIcon, QMenu, QMainWindow, QToolBar, QMessageBox
)
from PySide6.QtGui import QIcon, QAction, QCursor, QGuiApplication

from L_Tools import vnc_install
from importlib import reload
from LPerforce import (loginP4, p4_baselib, P4Lib)
from LPerforce.P4LoginInfoModule import p4_loginInfo

curdir = os.path.dirname(__file__)
sys.path.append(curdir)
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\ChatRoom')

from modules.ui.browser import Browser
from modules.ui.menu import HoverMenu
from modules.handlers.chat_handler import ChatHandler
from modules.auth.auth_manager import auth_manager  # 导入认证管理器

# 设置远程调试环境变量
os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"

# 获取项目配置信息
project_info = p4_loginInfo.get('project', {})
print("project_info", project_info)

if isinstance(project_info, dict):
    userName = project_info.get('User')
    nickname = project_info.get('FullName',userName)
    departmentList = project_info.get('userGroups', [])
else:
    userName = None
    departmentList = []

joinChatRoom = False
for department in departmentList:
    if department.get("name") == 'ChatRoom':
        joinChatRoom = True
        break
debug_users=['fengqingqing','OC1']


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.setWindowTitle("聊天室")
        
        # 初始化UI组件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QHBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)
        self.debug_users = debug_users
        self.isDebugUser:bool = (userName in debug_users)
        # 初始化变量
        self.userName: str = userName if userName else ""
        self.nickname : str = nickname
        self.project_info: Dict[str, Any] = project_info if isinstance(project_info, dict) else {}
        
        # 初始化UI相关属性
        self.blink_timer = QTimer(self)
        self.countdown_timer = QTimer(self)
        self.reconnect_timer = QTimer(self)
        self.connection_check_timer = QTimer(self)
        
        # 初始化状态变量
        self.is_blinking = False
        self.overlay_visible = False
        self.is_reconnecting = False
        self.reconnect_attempt = 0
        self.countdown_seconds = 0
        self.last_connection_time = time.time()
        self.chat_handler = None  # 显式初始化为 None
        
        # 初始化图标相关
        self.original_icon = QIcon()
        
        
        # 重连相关变量
        self.reconnect_attempt: int = 0
        self.max_reconnect_attempts: int = 50
        self.base_reconnect_delay: int = 3
        self.is_reconnecting: bool = False
        self.last_connection_time: float = time.time()
        
        # 连接认证管理器信号
        auth_manager.login_success.connect(self.on_login_success)
        auth_manager.login_failed.connect(self.on_login_failed)
        auth_manager.logout_success.connect(self.on_logout)
        
        # 设置窗口
        self.setup_window()
        
        # 初始化托盘和聊天处理器
        QTimer.singleShot(0, self._delayed_init)
        
        # 创建浏览器实例
        self.browser = Browser(parent_widget=self)
        self.central_layout.addWidget(self.browser)

        # 连接定时器信号
        self.reconnect_timer.timeout.connect(self.try_reconnect)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.connection_check_timer.timeout.connect(self.check_connection_status)

    def _delayed_init(self):
        """延迟初始化，避免启动卡顿"""
        try:
            # 设置托盘
            self.setup_tray()
            
            # 初始化聊天处理器
            self.init_chat_handler()
            
            # 初始化重连定时器
            self.setup_reconnect_timer()
            
            # 初始化连接检查定时器
            self.setup_connection_check_timer()
            
        except Exception as e:
            lprint(f"延迟初始化失败: {str(e)}")
            traceback.print_exc()

    def setup_reconnect_timer(self):
        """设置重连定时器"""
        try:
            if not self.reconnect_timer.isActive():
                # 设置定时器间隔
                self.reconnect_timer.setInterval(self.base_reconnect_delay *1000)
                self.reconnect_timer.start()
                self.is_reconnecting = False
                lprint(f"重连定时器已启动,间隔{self.base_reconnect_delay}秒")
            
        except Exception as e:
            lprint(f"设置重连定时器失败: {str(e)}")
            traceback.print_exc()

    def update_countdown(self):
        """更新倒计时显示"""
        try:
            if self.countdown_seconds > 0:
                self.countdown_seconds -= 1
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.setToolTip(
                        f"ChatRoom - 正在重连 (第 {self.reconnect_attempt} 次)\n"
                        f"下次重连倒计时: {self.countdown_seconds} 秒"
                    )
            else:
                self.countdown_timer.stop()
            
        except Exception as e:
            lprint(f"更新倒计时显示失败: {str(e)}")
            traceback.print_exc()

    def setup_connection_check_timer(self):
        """初始化连接检查定时器"""
        try:
            if not self.connection_check_timer.isActive():
                self.connection_check_timer.start(10000)  # 每10秒检查一次连接状态
                lprint("连接状态检查定时器已启动")
            
        except Exception as e:
            lprint(f"初始化连接检查定时器失败: {str(e)}")
            traceback.print_exc()

    def check_connection_status(self):
        """检查连接状态"""
        try:
            if not self.chat_handler:
                return
                
            if not self.is_reconnecting:
                is_connected = self.chat_handler.is_connected and self.chat_handler.sio.connected
                
                # 只有当状态真正改变时才更新
                if is_connected != self.chat_handler.is_connected:
                    self.update_connection_status(is_connected)
                    
                # 如果未连接且重连定时器未启动，则启动重连
                if not is_connected and (not self.reconnect_timer or not self.reconnect_timer.isActive()):
                    self.handle_connection_lost()
                    
        except Exception as e:
            lprint(f"检查连接状态失败: {str(e)}")
            traceback.print_exc()

    @asyncSlot()
    async def try_reconnect(self):
        """尝试重新连接"""
        if self.is_reconnecting:
            lprint("正在重连，跳过")
            return
            
        if self.chat_handler and self.chat_handler.is_connected and self.chat_handler.sio.connected:
            lprint("已经连接到服务器，停止重连")
            self.reconnect_timer.stop()
            self.countdown_timer.stop()  # 停止倒计时
            return
            
        try:
            self.is_reconnecting = True
            self.reconnect_attempt += 1
            
            # 计算延迟时间（指数退避）
            delay = min(30, self.base_reconnect_delay * (2 ** (self.reconnect_attempt - 1)))
            
            lprint(f"尝试第 {self.reconnect_attempt} 次重连，延迟 {delay} 秒")
            
            # 设置并启动倒计时
            self.countdown_seconds = delay
            self.countdown_timer.start(1000)  # 每秒更新一次
            
            # 更新托盘图标提示
            if hasattr(self, 'tray_icon'):
                self.tray_icon.setToolTip(
                    f"ChatRoom - 正在重连 (第 {self.reconnect_attempt} 次)\n"
                    f"下次重连倒计时: {self.countdown_seconds} 秒"
                )
            
            # 尝试重新连接
            connected = await self.chat_handler.connect_to_server()
            
            if connected:
                lprint("重连成功")
                self.reconnect_timer.stop()
                self.countdown_timer.stop()  # 停止倒计时
                self.reconnect_attempt = 0
                self.is_reconnecting = False
                self.last_connection_time = time.time()
                self.update_connection_status(True)
                
                # 更新托盘图标提示
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.setToolTip("ChatRoom - 已连接")
                    self.showMessage(
                        "ChatRoom",
                        "已重新连接到服务器",
                        QSystemTrayIcon.MessageIcon.Information,
                        2000
                    )
            else:
                lprint(f"重连失败，{delay}秒后重试")
                self.is_reconnecting = False
                if self.reconnect_attempt < self.max_reconnect_attempts:
                    self.reconnect_timer.setInterval(delay * 1000)
                    self.reconnect_timer.start()
                else:
                    lprint("达到最大重连次数，询问用户是否继续尝试")
                    self.reconnect_timer.stop()
                    self.countdown_timer.stop()  # 停止倒计时
                    
                    # 创建消息框询问用户
                    # msgBox = QMessageBox()
                    # msgBox.setWindowTitle("连接失败")
                    # msgBox.setText(f"已尝试重连 {self.max_reconnect_attempts} 次，但仍无法连接到服务器。")
                    # msgBox.setInformativeText("请选择下一步操作：")
                    
                    # # 添加按钮
                    # continueButton = msgBox.addButton("继续尝试", QMessageBox.ButtonRole.AcceptRole)
                    # exitButton = msgBox.addButton("退出程序", QMessageBox.ButtonRole.RejectRole)
                    
                    # # 设置图标
                    # msgBox.setIcon(QMessageBox.Icon.Warning)
                    
                    # # 显示消息框并获取用户选择
                    # msgBox.exec()
                    
                    # 根据用户选择执行不同操作
                    if msgBox.clickedButton() == continueButton:
                        lprint("用户选择继续尝试重连")
                        # 重置重连尝试次数
                        self.reconnect_attempt = 0
                        # 重新启动重连定时器
                        self.reconnect_timer.setInterval(self.base_reconnect_delay * 1000)
                        self.reconnect_timer.start()
                        self.is_reconnecting = False
                    else:
                        lprint("用户选择退出程序")
                        # 设置退出原因
                        global exit_reason
                        exit_reason = "用户在重连失败后选择退出"
                        # 退出程序
                        self.exit_application()
                    
        except Exception as e:
            lprint(f"重连过程中出错: {str(e)}")
            traceback.print_exc()
            self.is_reconnecting = False
            # 重置重连尝试计数器，以便下次重试
            self.reconnect_attempt = 0

    def handle_connection_lost(self):
        """处理连接丢失"""
        try:
            if self.is_reconnecting:
                return
                
            lprint("连接已断开")
            self.is_reconnecting = True
            self.reconnect_attempt = 0
            self.setup_reconnect_timer()
            self.update_connection_status(False)
            
            if hasattr(self, 'tray_icon'):
                self.tray_icon.setToolTip("聊天室 - 已断开连接")
        except Exception as e:
            lprint(f"处理连接丢失失败: {str(e)}")
            traceback.print_exc()

    def init_chat_handler(self):
        """初始化聊天处理器"""
        try:
            if not self.chat_handler:  # 只在未初始化时创建
                self.chat_handler = ChatHandler(self)
                # 添加连接状态监听
                self.chat_handler.on_disconnect = self.handle_connection_lost
                self.chat_handler.on_connect = self.handle_connection_restored
                
                # 初始化连接状态
                if hasattr(self, 'tray_menu'):
                    self.tray_menu.update_login_status(False)
                    
        except Exception as e:
            lprint(f"初始化聊天处理器失败: {str(e)}")
            traceback.print_exc()

    def update_connection_status(self, is_connected: bool):
        """更新连接状态显示"""
        try:
            if hasattr(self, 'tray_menu'):
                self.tray_menu.update_login_status(is_connected)
                
            # 更新托盘图标提示
            if hasattr(self, 'tray_icon'):
                status_text = "已连接" if is_connected else "未连接"
                self.tray_icon.setToolTip(f"ChatRoom - {status_text}")
        except Exception as e:
            lprint(f"更新连接状态显示失败: {str(e)}")
            traceback.print_exc()

    def handle_connection_restored(self):
        """处理连接恢复"""
        try:
            lprint("连接已恢复")
            if self.reconnect_timer.isActive():
                self.reconnect_timer.stop()
            self.reconnect_attempt = 0
            self.is_reconnecting = False
            self.last_connection_time = time.time()
            self.update_connection_status(True)
            
            if hasattr(self, 'tray_icon'):
                self.tray_icon.setToolTip("ChatRoom - 已连接")
        except Exception as e:
            lprint(f"处理连接恢复失败: {str(e)}")
            traceback.print_exc()

    @asyncClose
    async def async_close_event(self, event):
        """处理窗口关闭事件的异步版本，用于清理资源"""
        try:
            # 停止闪烁
            self.stop_blinking()
            
            # 停止重连定时器
            if self.reconnect_timer.isActive():
                self.reconnect_timer.stop()
            
            # 关闭聊天处理器
            if self.chat_handler:
                await self.chat_handler.close()
            
            # 移除托盘图标
            if self.tray_icon:
                self.tray_icon.hide()
            
            event.accept()
        except Exception as e:
            lprint(f"关闭窗口时出错: {str(e)}")
            traceback.print_exc()
            event.accept()

    def closeEvent(self, event):
        """重写关闭事件，将窗口最小化到托盘而不是关闭"""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()

    def hideEvent(self, event):
        """处理窗口隐藏事件"""
        try:
            super().hideEvent(event)
            if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
                self.showMessage(
                    "ChatRoom",
                    "应用程序已最小化到系统托盘。双击托盘图标可重新打开。",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
        except Exception as e:
            lprint(f"处理隐藏事件失败: {str(e)}")
            traceback.print_exc()

    def showMessage(self,*args,**kwargs):
        if userName in debug_users:
            self.tray_icon.showMessage(*args)
        
    def showEvent(self, event):
        """处理窗口显示事件"""
        try:
            super().showEvent(event)
            self.activateWindow()  # 确保窗口获得焦点
        except Exception as e:
            lprint(f"处理显示事件失败: {str(e)}")
            traceback.print_exc()

    @asyncSlot()
    async def handle_login(self):
        """处理登录/登出操作"""
        try:
            if self.userName:
                lprint(f"开始登录: {self.userName}")
                success, result = await auth_manager.login(self.userName, "666")
                if success:
                    lprint("登录成功")
                    # 更新托盘菜单状态
                    if self.tray_menu:
                        self.tray_menu.update_login_status(True)
                else:
                    lprint(f"登录失败: {result}")
                    if self.tray_menu:
                        self.tray_menu.update_login_status(False)

        except Exception as e:
            lprint(f"处理登录/登出操作失败: {str(e)}")
            traceback.print_exc()
            if self.tray_menu:
                self.tray_menu.update_login_status(False)

    @asyncSlot()
    async def auto_login(self):
        """自动登录"""
        try:
            if self.userName:
                # 复用handle_login的逻辑
                await self.handle_login()
        except Exception as e:
            lprint(f"自动登录失败: {str(e)}")
            traceback.print_exc()
            # 自动登录失败不显示错误消息框
            if self.tray_menu:
                self.tray_menu.update_login_status(False)

    @asyncSlot()
    async def on_login_success(self, token: str):
        """登录成功处理"""
        try:
            lprint("登录成功，开始连接到聊天服务器")
            # 获取设备ID并更新project_info
            device_id = auth_manager.device_id
            if device_id:
                self.project_info['device_id'] = device_id
                lprint(f"更新project_info，添加设备ID: {device_id}")
            
            if self.chat_handler:
                self.chat_handler.token = token
                connected = await self.chat_handler.connect_to_server()
                if not connected:
                    lprint("连接聊天服务器失败")
                    if self.tray_menu:
                        self.tray_menu.update_login_status(False)
                    return
            # 更新托盘菜单状态
            if self.tray_menu:
                self.tray_menu.update_login_status(True)
            # 保存登录状态
            self.save_login_state(token)
        except Exception as e:
            lprint(f"处理登录成功失败: {str(e)}")
            traceback.print_exc()
            if self.tray_menu:
                self.tray_menu.update_login_status(False)

    def save_login_state(self, token: str):
        """保存登录状态"""
        try:
            state = {
                "username": self.userName,
                "token": token,
                "timestamp": datetime.datetime.now().isoformat()
            }
            state_file = os.path.join(LOG_DIR, "login_state.json")
            with open(state_file, "w") as f:
                json.dump(state, f)
        except Exception as e:
            lprint(f"保存登录状态失败: {str(e)}")
            traceback.print_exc()

    def on_login_failed(self, error_msg: str):
        """登录失败处理"""
        lprint(f"登录失败: {error_msg}")
        self.update_connection_status(False)
        # 更新托盘菜单状态
        if self.tray_menu:
            self.tray_menu.update_login_status(False)

    @asyncSlot()
    async def on_logout(self):
        """登出处理"""
        try:
            if self.chat_handler:
                await self.chat_handler.close()
            self.update_connection_status(False)
            # 更新托盘菜单状态
            if self.tray_menu:
                self.tray_menu.update_login_status(False)
        except Exception as e:
            lprint(f"处理登出失败: {str(e)}")
            traceback.print_exc()

    def setup_window(self):
        """设置窗口属性"""
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("chatroom")
        self.setWindowIcon(QIcon(tray_icon_path))
        self.setWindowTitle('聊天室')
        
        # 设置最小尺寸
        self.setMinimumSize(1300, 900)
        
        # 只在第一次启动时设置默认位置和大小
        if not hasattr(self, '_geometry_set'):
            # 获取屏幕几何信息并居中窗口
            screen = QApplication.primaryScreen().geometry()
            self.setGeometry(
                (screen.width() - 1300) // 2,
                (screen.height() - 800) // 2,
                1300,
                800
            )
            self._geometry_set = True
            
        self.setStyleSheet("""
            QMainWindow {
                margin: 0;
                padding: 0;
                border: none;
            }
            QWidget {
                margin: 0;
                padding: 0;
                border: none;
            }
        """)

    def setup_tray(self):
        """设置系统托盘图标"""
        try:
            lprint("开始设置系统托盘图标...")
            
            # 检查是否已存在托盘图标
            if hasattr(self, 'tray_icon') and self.tray_icon is not None:
                lprint("托盘图标已存在，先移除")
                self.tray_icon.hide()
                self.tray_icon.deleteLater()
            
            self.tray_icon = QSystemTrayIcon(self)

            self.tray_icon.setIcon(QIcon(tray_icon_path))
            lprint("已设置托盘图标")

            # 创建托盘图标的上下文菜单
            lprint("开始创建托盘菜单...")
            try:
                self.tray_menu = HoverMenu(parent=self)  # 设置parent为self
                lprint("托盘菜单创建完成")
            except Exception as e:
                lprint(f"创建托盘菜单失败: {str(e)}")
                traceback.print_exc()
                raise

            # 初始化聊天处理器（如果还没有初始化）
            try:
                if not hasattr(self, 'chat_handler') or self.chat_handler is None:
                    self.init_chat_handler()
                
                # 连接聊天室的消息信号到菜单
                if hasattr(self, 'chat_handler') and self.chat_handler is not None:
                    lprint("连接聊天室消息信号...")
                    if hasattr(self.chat_handler, 'message_received'):
                        self.chat_handler.message_received.connect(self.on_new_message)
                        lprint("消息信号连接完成")
                    else:
                        lprint("警告: chat_handler 没有 message_received 属性")
                else:
                    lprint("警告: chat_handler 未初始化")
            except Exception as e:
                lprint(f"初始化聊天处理器或连接消息信号失败: {str(e)}")
                traceback.print_exc()

            # 设置托盘图标菜单
            try:
                lprint("开始设置托盘图标菜单...")
                self.tray_icon.setContextMenu(self.tray_menu)
                self.tray_icon.activated.connect(self.on_tray_icon_activated)
                lprint("托盘图标菜单设置完成")

                # 设置闪烁定时器
                lprint("设置闪烁定时器...")
                self.blink_timer: QTimer = QTimer(self)
                self.blink_timer.timeout.connect(self.toggle_overlay)
                self.overlay_visible = False
                lprint("闪烁定时器设置完成")
            except Exception as e:
                lprint(f"设置托盘图标菜单或闪烁定时器失败: {str(e)}")
                traceback.print_exc()

            # 显示托盘图标
            try:
                lprint("尝试显示托盘图标...")
                self.tray_icon.show()
                lprint("托盘图标显示成功")

                # 自动登录
                if self.userName:
                    lprint("准备自动登录...")
                    QTimer.singleShot(100, self.auto_login)
            except Exception as e:
                lprint(f"显示托盘图标或设置自动登录失败: {str(e)}")
                traceback.print_exc()

        except Exception as e:
            lprint(f"设置托盘图标整体失败: {str(e)}")
            traceback.print_exc()

    def on_tray_icon_activated(self, reason):
        """处理托盘图标激活事件"""
        lprint(f"托盘图标被激活，原因: {reason}")
        
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 单击
            lprint("单击托盘图标，切换窗口显示状态")
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:  # 双击
            lprint("双击托盘图标，显示窗口")
            self.show()
            self.activateWindow()
        elif reason == QSystemTrayIcon.ActivationReason.Context:  # 右键
            geometry = self.tray_icon.geometry()
            if geometry.isValid() and userName != 'Tangly':
                # 如果能获取到托盘图标位置，就在托盘图标位置显示
                self.tray_menu.popup(geometry.topRight())


    def toggle_overlay(self):
        """切换托盘图标闪烁效果"""
        if self.overlay_visible:
            self.tray_icon.setIcon(QIcon(tray_icon_path))
            self.overlay_visible = False
        else:
            self.tray_icon.setIcon(QIcon(tray_icon_path))
            self.overlay_visible = True

    def start_blinking(self, date: str = '', interval: int = 500) -> None:
        """开始托盘图标闪烁"""
        if hasattr(self, 'blink_timer'):
            self.overlay_visible = False
            self.blink_timer.start(interval)

    def stop_blinking(self):
        """停止托盘图标闪烁"""
        if hasattr(self, 'blink_timer'):
            self.blink_timer.stop()
            print("停止闪烁")
            self.tray_icon.setIcon(QIcon(tray_icon_path))
            self.overlay_visible = False

    def show_window(self) -> None:
        """显示主窗口"""
        if not self.isVisible():
            self.showNormal()
            self.activateWindow()

    def hide_window(self):
        """隐藏主窗口"""
        self.hide()

    def exit_application(self):
        """退出应用程序"""
        os._exit(0)

    def _force_exit(self):
        """强制退出程序"""
        try:
            lprint("执行强制退出...")
            QApplication.quit()
        except Exception as e:
            lprint(f"QApplication.quit()失败: {str(e)}")
            lprint("使用os._exit(0)强制退出")
            os._exit(0)

    def on_new_message(self, message_data: dict):
        """处理新消息"""
        try:
            # 转发消息到菜单
            if hasattr(self, 'tray_menu'):
                self.tray_menu.message_received.emit(message_data)
        except Exception as e:
            lprint(f"处理新消息失败: {str(e)}")
            traceback.print_exc()

    def restart_application(self):
        """重启应用程序"""
        try:
            # 保存当前窗口状态
            geometry = self.geometry()
            
            # 获取当前进程的可执行文件路径
            executable = sys.executable
            args = sys.argv[:]
            
            # 添加几何信息参数
            args.extend([
                f"--geometry={geometry.x()},{geometry.y()},{geometry.width()},{geometry.height()}"
            ])
            
            # 关闭当前实例
            self.close()
            
            # 启动新实例
            subprocess.Popen([executable] + args)
            
            # 退出当前实例
            self.exit_application()
            
        except Exception as e:
            lprint(f"重启应用程序失败: {str(e)}")
            traceback.print_exc()
            # 如果重启失败，显示错误消息
            QMessageBox.critical(
                self,
                "重启失败",
                f"重启应用程序时出错: {str(e)}",
                QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Ok
            )

def apply_stylesheet(app):
    """应用暗色主题样式"""
    style_file = os.path.join(os.path.dirname(__file__), 'static', 'dark_theme.qss')
    if os.path.exists(style_file):
        with open(style_file, 'r',encoding='utf-8') as f:
            app.setStyleSheet(f.read())
            lprint(f"成功应用样式表: {style_file}")
    else:
        lprint(f"样式表文件不存在: {style_file}")

# MainWindow 类保持不变...

# 全局变量
window: Optional[MainWindow] = None

async def init_qt_app():
    """初始化Qt应用"""
    global window
    try:
        # 检查是否有权限加入聊天室
        if not joinChatRoom:
            lprint("没有权限加入聊天室")
            return False
            
        # 创建QApplication实例
        app = QApplication(sys.argv)
        
        # 创建qasync事件循环
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        # 应用暗色主题
        apply_stylesheet(app)
        
        # 创建主窗口
        window = MainWindow()
        
        # 等待托盘图标初始化完成
        await asyncio.sleep(0.5)  # 给一点时间让托盘图标初始化
        
        # 启动事件循环
        asyncio.create_task(run_event_loop(loop, app))
        
        return True
        
    except Exception as e:
        lprint(f"初始化Qt应用失败: {str(e)}")
        traceback.print_exc()
        return False

async def run_event_loop(loop: QEventLoop, app: QApplication):
    """运行Qt事件循环"""
    try:
        while True:
            app.processEvents()  # 处理Qt事件
            await asyncio.sleep(0.01)  # 避免CPU占用过高
    except Exception as e:
        lprint(f"事件循环运行失败: {str(e)}")
        traceback.print_exc()

async def cleanup_qt_app():
    """清理Qt应用"""
    global window
    try:
        if window:
            # 先隐藏托盘图标
            if hasattr(window, 'tray_icon') and window.tray_icon is not None:
                lprint("隐藏托盘图标")
                window.tray_icon.hide()
                
            # 关闭窗口
            lprint("关闭主窗口")
            window.close()
            
            # 调用Qt应用退出方法
            lprint("退出Qt应用")
            QApplication.quit()
            
            # 如果上述方法无效，使用强制退出
            QTimer.singleShot(500, lambda: os._exit(0))
            
        return True
    except Exception as e:
        lprint(f"清理Qt应用失败: {str(e)}")
        traceback.print_exc()
        # 确保无论如何都能退出
        try:
            os._exit(0)
        except:
            pass
        return False

async def app(scope, receive, send):
    """ASGI 应用入口点"""
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                success = await init_qt_app()
                if success:
                    await send({"type": "lifespan.startup.complete"})
                else:
                    await send({"type": "lifespan.startup.failed"})
            elif message["type"] == "lifespan.shutdown":
                success = await cleanup_qt_app()
                if success:
                    await send({"type": "lifespan.shutdown.complete"})
                else:
                    await send({"type": "lifespan.shutdown.failed"})
                    raise Exception("清理Qt应用失败")
                return
                
    elif scope["type"] == "http":
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"text/plain"]],
        })
        await send({
            "type": "http.response.body",
            "body": b"Qt application is running",
        })

def is_process_running(process_name: str) -> bool:
    """检查进程是否正在运行"""
    for process in psutil.process_iter(['name']):
        if process.info['name'] == process_name:
            lprint(process, process_name)
            return True
    return False

if __name__ == "__main__":
    # 检查是否有权限运行
    if not joinChatRoom:
        lprint("没有权限加入聊天室")
        sys.exit(1)
    
    # 根据用户名判断启动方式
    if userName in debug_users:
        # 使用uvicorn启动
        import uvicorn
        uvicorn.run(
            "pyqt_chatroom:app",
            host="127.0.0.1",
            port=8000,
            reload=True
        )
    else:
        # 如果没有运行，则以异步方式启动
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(init_qt_app())
            loop.run_forever()
        except Exception as e:
            lprint(f"启动应用失败: {str(e)}")
            sys.exit(1)
