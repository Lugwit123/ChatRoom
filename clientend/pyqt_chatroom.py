"""
主应用程序入口
"""
import ctypes
import sys
import os
import atexit
import datetime
from typing import Optional, Dict, Any, TextIO

os.environ['QT_API'] = 'pyqt6'

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

# 全局变量用于存储退出原因
exit_reason = "程序正常退出"

def init_exit_logging():
    """初始化退出日志记录"""
    global exit_log_file
    try:
        log_dir = os.getenv('LOG_DIR', 'A:/temp/chatRoomLog')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'exit_log.txt')
        exit_log_file = open(log_path, 'a', encoding='utf-8')
        lprint(f"退出日志文件已初始化: {log_path}")
    except Exception as e:
        lprint(f"初始化退出日志失败: {str(e)}")

def log_exit(reason: str = "程序正常退出"):
    """记录程序退出信息"""
    global exit_reason
    try:
        # 如果没有提供reason，使用全局的exit_reason
        if reason:
            exit_reason = reason
            
        log_dir = os.getenv('LOG_DIR', 'A:/temp/chatRoomLog')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'exit_log.txt')
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{current_time}] 程序退出 - 原因: {exit_reason}\n"
        
        # 直接使用 with 语句确保文件正确关闭
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_message)
            f.flush()
        
        # 同时打印到控制台
        lprint(f"程序退出日志: {log_message.strip()}")
        
    except Exception as e:
        lprint(f"记录退出信息失败: {str(e)}")
        lprint(traceback.format_exc())

def handle_exception(exc_type, exc_value, exc_traceback):
    """处理未捕获的异常"""
    global exit_reason
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    lprint(f"未捕获的异常:\n{error_msg}")
    
    # 设置退出原因
    exit_reason = f"未捕获的异常: {str(exc_value)}\n{error_msg}"

# 设置异常钩子
sys.excepthook = handle_exception

# 注册退出处理函数
atexit.register(log_exit)

# 加载环境变量
os.chdir(os.path.dirname(__file__))
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)  # 强制覆盖已存在的环境变量
    lprint(f"已加载环境变量文件: {env_path}")
else:
    lprint(f"环境变量文件不存在: {env_path}")

hostname = socket.gethostname()


# 从环境变量获取配置
SERVER_IP = os.getenv('SERVER_IP', '127.0.0.1')
lprint(f"服务器IP: {SERVER_IP}")  # 打印服务器IP以便调试
SERVER_PORT = int(os.getenv('SERVER_PORT', '1026'))
WS_PORT = int(os.getenv('WS_PORT', '1026'))
APP_MIN_WIDTH = int(os.getenv('APP_MIN_WIDTH', '1300'))
APP_MIN_HEIGHT = int(os.getenv('APP_MIN_HEIGHT', '900'))
APP_DEFAULT_WIDTH = int(os.getenv('APP_DEFAULT_WIDTH', '1300'))
APP_DEFAULT_HEIGHT = int(os.getenv('APP_DEFAULT_HEIGHT', '800'))
TEMP_DIR = os.getenv('TEMP_DIR', 'D:/TD_Depot/Temp')
LOG_DIR = os.getenv('LOG_DIR', 'A:/temp/chatRoomLog')
ICON_DIR = os.getenv('ICON_DIR', 'D:/TD_Depot/Software/Lugwit_syncPlug/lugwit_insapp/trayapp/Lib/icons')
VNC_VIEWER_PATH = os.getenv('VNC_VIEWER_PATH', 'D:/TD_Depot/Software/ProgramFilesLocal/RealVNC/VNC Viewer/vncviewer.exe')
VNC_SERVER_PATH = os.getenv('VNC_SERVER_PATH', 'D:/TD_Depot/Temp/VNC-Server/Installer.exe')
VNC_DEFAULT_PORT = int(os.getenv('VNC_DEFAULT_PORT', '5900'))
VNC_DEFAULT_PASSWORD = os.getenv('VNC_DEFAULT_PASSWORD', 'OC.123456')

# 确保必要的目录存在
os.makedirs(TEMP_DIR, exist_ok=True)
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
from modules.message import MessageBase
from modules.handlers.chat_handler import ChatRoom

# 设置远程调试环境变量
os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"

# 获取项目配置信息
project_info = p4_loginInfo.get('project', {})
print("project_info", project_info)

if isinstance(project_info, dict):
    userName = project_info.get('User')
    departmentList = project_info.get('userGroups', [])
else:
    userName = None
    departmentList = []

joinChatRoom = False
for department in departmentList:
    if department.get("name") == 'ChatRoom':
        joinChatRoom = True
        break

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("聊天室")
        
        # 初始化UI组件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QHBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)
        
        # 初始化变量
        self.userName = os.getenv('USER_NAME', '')
        self.project_info = {}
        self.tray_icon: QSystemTrayIcon
        self.tray_menu: HoverMenu
        self.blink_timer: Optional[QTimer] = None
        self.is_blinking = False
        self.original_icon = None
        self.chat_handler: Optional[ChatRoom] = None
        self.browser: Optional[Browser] = None
        
        # 设置窗口
        self.setup_window()
        self.setup_tray()
        
        # 初始化聊天处理器
        self.init_chat_handler()
        
        # 创建浏览器实例
        self.browser = Browser(parent_widget=self)
        self.central_layout.addWidget(self.browser)
        
    @asyncClose
    async def async_close_event(self, event):
        """处理窗口关闭事件的异步版本，用于清理资源"""
        try:
            # 停止闪烁
            self.stop_blinking()
            
            # 关闭聊天处理器
            if self.chat_handler:
                await self.chat_handler.close()
            
            # 移除托盘图标
            if self.tray_icon:
                self.tray_icon.hide()
            
            event.accept()
        except Exception as e:
            lprint(f"关闭窗口时出错: {str(e)}")
            lprint(traceback.format_exc())
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
                self.tray_icon.showMessage(
                    "ChatRoom",
                    "应用程序已最小化到系统托盘。双击托盘图标可重新打开。",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
        except Exception as e:
            lprint(f"处理隐藏事件失败: {str(e)}")
            lprint(traceback.format_exc())

    def showEvent(self, event):
        """处理窗口显示事件"""
        try:
            super().showEvent(event)
            self.activateWindow()  # 确保窗口获得焦点
        except Exception as e:
            lprint(f"处理显示事件失败: {str(e)}")
            lprint(traceback.format_exc())

    @asyncSlot()
    async def on_login_success(self, token: str):
        """登录成功的处理"""
        try:
            if self.chat_handler:
                await self.chat_handler.connect_websocket(token)
        except Exception as e:
            lprint(f"登录成功处理出错: {str(e)}")
            lprint(traceback.format_exc())
            
    def on_logout(self):
        """登出的处理"""
        try:
            if self.chat_handler:
                self.chat_handler.disconnect()
        except Exception as e:
            lprint(f"登出处理出错: {str(e)}")
            lprint(traceback.format_exc())

    def init_chat_handler(self):
        """初始化聊天处理器"""
        self.chat_handler = ChatRoom(parent_com=self)

    def setup_window(self):
        """设置窗口属性"""
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("chatroom")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'logo.png')))
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
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'logo.png')
            lprint(f"托盘图标路径: {self.tray_icon_path}")
            
            if not os.path.exists(self.tray_icon_path):
                lprint(f"警告: 托盘图标文件不存在: {self.tray_icon_path}")
                self.tray_icon_path = QIcon.fromTheme("application-exit")
            self.tray_icon.setIcon(QIcon(self.tray_icon_path))
            lprint("已设置托盘图标")

            # 创建托盘图标的上下文菜单
            lprint("开始创建托盘菜单...")
            try:
                self.tray_menu = HoverMenu(parent=self)  # 设置parent为self
                lprint("托盘菜单创建完成")
            except Exception as e:
                lprint(f"创建托盘菜单失败: {str(e)}")
                lprint(traceback.format_exc())
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
                lprint(traceback.format_exc())

            # 从yaml配置文件读取远程控制选项
            config_path = os.path.join(os.path.dirname(__file__), 'config', 'remote_control.yaml')
            try:
                lprint(f"读取远程控制配置: {config_path}")
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    for option in config['remote_control_options']:
                        try:
                            lprint(f"添加远程控制选项: {option['label']}")
                            action = QAction(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'remote.svg')), 
                                          option['label'], self)
                            if option['action'] == 'request':
                                action.triggered.connect(
                                    lambda checked, opt=option: self.request_remote_control(
                                        userName, opt.get('username'), opt.get('type')
                                    )
                                )
                            elif option['action'] == 'connect':
                                action.triggered.connect(
                                    lambda checked, host=option['host'], port=option['port'], 
                                           password=option['password']: self.connect_vnc(host, port, password)
                                )
                            self.tray_menu.addAction(action)
                            lprint(f"远程控制选项 {option['label']} 添加成功")
                        except Exception as e:
                            lprint(f"添加远程控制选项 {option.get('label', '未知')} 失败: {str(e)}")
                            lprint(traceback.format_exc())
                lprint("远程控制选项添加完成")
            except Exception as e:
                lprint(f"加载远程控制配置失败: {str(e)}")
                lprint(traceback.format_exc())

            # 添加分隔线
            try:
                self.tray_menu.addSeparator()
                lprint("添加分隔线成功")
            except Exception as e:
                lprint(f"添加分隔线失败: {str(e)}")
                lprint(traceback.format_exc())

            # 添加基本菜单项
            try:
                # 添加"显示"动作
                show_action = QAction(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'show.svg')), 
                                    "显示", self)
                show_action.triggered.connect(self.show_window)
                self.tray_menu.addAction(show_action)
                lprint("添加显示菜单项成功")

                # 添加"隐藏"动作
                hide_action = QAction(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'hide.svg')), 
                                    "隐藏", self)
                hide_action.triggered.connect(self.hide_window)
                self.tray_menu.addAction(hide_action)
                lprint("添加隐藏菜单项成功")

                # 添加"重启"动作
                restart_action = QAction(QIcon(os.path.join(os.path.dirname(__file__), '..', '..', 'icons', 'restart.svg')), 
                                       "重启", self)
                restart_action.triggered.connect(self.restart_application)
                self.tray_menu.addAction(restart_action)
                lprint("添加重启菜单项成功")

                # 添加分隔线
                self.tray_menu.addSeparator()
                lprint("添加第二个分隔线成功")

                # 添加"退出"动作
                exit_action = QAction(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'exit.svg')), 
                                    "退出", self)
                exit_action.triggered.connect(self.exit_application)
                self.tray_menu.addAction(exit_action)
                lprint("添加退出菜单项成功")
            except Exception as e:
                lprint(f"添加基本菜单项失败: {str(e)}")
                lprint(traceback.format_exc())

            # 设置托盘图标菜单
            try:
                lprint("开始设置托盘图标菜单...")
                self.tray_icon.setContextMenu(self.tray_menu)
                self.tray_icon.activated.connect(self.on_tray_icon_activated)
                lprint("托盘图标菜单设置完成")

                # 设置闪烁定时器
                lprint("设置闪烁定时器...")
                self.blink_timer = QTimer(self)
                self.blink_timer.timeout.connect(self.toggle_overlay)
                self.overlay_visible = False
                lprint("闪烁定时器设置完成")
            except Exception as e:
                lprint(f"设置托盘图标菜单或闪烁定时器失败: {str(e)}")
                lprint(traceback.format_exc())

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
                lprint(traceback.format_exc())

        except Exception as e:
            lprint(f"设置托盘图标整体失败: {str(e)}")
            lprint(traceback.format_exc())

    @asyncSlot()
    async def auto_login(self):
        """自动登录"""
        try:
            if self.userName and hasattr(self, 'tray_menu'):
                await self.tray_menu.login(self.userName, "666")
        except Exception as e:
            lprint(f"自动登录失败: {str(e)}")
            lprint(traceback.format_exc())

    def connect_vnc(self, host: str, port: int, password: str) -> None:
        """连接VNC服务器"""
        try:
            # 尝试连接VNC服务器
            app = Application().start(
                f'"D:\\TD_Depot\\Software\\ProgramFilesLocal\\RealVNC\\VNC Viewer\\vncviewer.exe" {host}:{port}'
            )
            
            # 等待认证窗口出现
            try:
                dlg = app.window(title='Authentication')
                dlg.wait('exists', timeout=5)  # 增加超时时间
            except Exception as e:
                reply = QMessageBox.warning(
                    parent=self,
                    title="连接失败",
                    text="无法连接到VNC服务器，请检查服务器是否在线",
                    button0=QMessageBox.StandardButton.Ok,
                    button1=QMessageBox.StandardButton.Ok
                )
                return
                
            # 输入密码
            try:
                password_input = dlg.child_window(class_name="Edit", found_index=1)
                password_input.type_keys(password, with_spaces=True)
                
                ok_button = dlg.child_window(title="OK", class_name="Button")
                ok_button.click()
            except Exception as e:
                reply = QMessageBox.warning(
                    parent=self,
                    title="认证失败",
                    text="无法完成VNC认证，请检查密码是否正确",
                    button0=QMessageBox.StandardButton.Ok,
                    button1=QMessageBox.StandardButton.Ok
                )
                return
                
        except Exception as e:
            reply = QMessageBox.warning(
                parent=self,
                title="连接失败",
                text=f"连接VNC服务器时发生错误: {str(e)}",
                button0=QMessageBox.StandardButton.Ok,
                button1=QMessageBox.StandardButton.Ok
            )

    def check_vnc_version(self) -> tuple[bool, str]:
        """检查VNC版本
        Returns:
            tuple[bool, str]: (是否是7.x版本, 版本号)
        """
        try:
            import winreg
            # 检查64位程序
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            
            # 遍历所有子键查找VNC Server
            index = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, index)
                    subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                    
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        if "VNC Server" in display_name:
                            version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                            winreg.CloseKey(subkey)
                            winreg.CloseKey(key)
                            return version.startswith("7."), version
                    except WindowsError:
                        pass
                    finally:
                        winreg.CloseKey(subkey)
                    
                    index += 1
                except WindowsError:
                    break
            
            # 如果64位没找到，检查32位程序
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
            index = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, index)
                    subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
                    
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        if "VNC Server" in display_name:
                            version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                            winreg.CloseKey(subkey)
                            winreg.CloseKey(key)
                            return version.startswith("7."), version
                    except WindowsError:
                        pass
                    finally:
                        winreg.CloseKey(subkey)
                    
                    index += 1
                except WindowsError:
                    break
            
            winreg.CloseKey(key)
            return False, ""
            
        except Exception as e:
            lprint(f"检查VNC版本出错: {str(e)}")
            return False, ""

    def is_vnc_running(self) -> bool:
        """检查VNC服务是否正在运行"""
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == 'vncserver.exe':
                    return True
            return False
        except Exception:
            return False

    @asyncSlot()
    async def request_remote_control(self, sender: Optional[str], recipient: Optional[str], role_type: Optional[str]):
        """请求远程控制"""
        if not all([sender, recipient, role_type]):
            reply = QMessageBox.warning(
                parent=self,
                title="参数错误",
                text="远程控制请求缺少必要参数",
                button0=QMessageBox.StandardButton.Ok,
                button1=QMessageBox.StandardButton.Ok
            )
            return

        # 检查VNC版本和运行状态
        is_v7, version = self.check_vnc_version()
        
        if is_v7:
            # 如果是7.x版本，检查是否在运行
            if self.is_vnc_running():
                # VNC已在运行，直接发送远程控制请求
                if sender and recipient and role_type:  # Type narrowing
                    await self.chat_handler._send_remote_control_message(sender, recipient, role_type)
                return
            else:
                # VNC 7.x已安装但未运行，启动服务
                try:
                    subprocess.run(['net', 'start', 'vncserver'], check=True)
                    if sender and recipient and role_type:  # Type narrowing
                        await self.chat_handler._send_remote_control_message(sender, recipient, role_type)
                    return
                except subprocess.CalledProcessError:
                    reply = QMessageBox.warning(
                        parent=self,
                        title="启动服务失败",
                        text="VNC服务启动失败，请手动启动服务或重新安装。",
                        button0=QMessageBox.StandardButton.Ok,
                        button1=QMessageBox.StandardButton.Ok
                    )
                    return
        else:
            # 不是7.x版本，提示安装
            reply = QMessageBox.question(
                parent=self,
                title="安装VNC Server",
                text=f"当前{'未安装VNC Server' if not version else f'VNC版本为{version}'}\n"
                     "需要安装VNC Server 7.x版本才能使用远程控制功能。\n"
                     "是否现在安装？",
                button0=QMessageBox.StandardButton.Yes,
                button1=QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return

        # 复制VNC服务器文件
        subprocess.run(['robocopy','/MIR',
            LM.ProgramFilesLocal_Public+r'\VNC-Server',
            r'D:\TD_Depot\Temp\VNC-Server'
        ])
        os.makedirs(r'D:\TD_Depot\Temp\VNC-Server',exist_ok=True)

        try:
            # 运行安装程序
            result = subprocess.run(
                [r'D:\TD_Depot\Temp\VNC-Server\Installer.exe', '/qn'],
                capture_output=True,
                text=True
            )
            
            if result.stderr:
                lprint(f"VNC安装错误输出: {result.stderr}")
                reply = QMessageBox.warning(
                    parent=self,
                    title="安装失败",
                    text=f"VNC服务安装失败\n{result.stderr}",
                    button0=QMessageBox.StandardButton.Ok,
                    button1=QMessageBox.StandardButton.Ok
                )
            else:
                lprint("VNC安装成功")
                # 等待服务启动
                await asyncio.sleep(2)
                # 发送远程控制请求
                if sender and recipient and role_type:  # Type narrowing
                    await self.chat_handler._send_remote_control_message(sender, recipient, role_type)

        except Exception as e:
            lprint(f"远程控制准备失败: {str(e)}")
            reply = QMessageBox.warning(
                parent=self,
                title="远程控制准备",
                text=f"远程控制准备失败: {str(e)}",
                button0=QMessageBox.StandardButton.Ok,
                button1=QMessageBox.StandardButton.Ok
            )

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
        try:
            lprint("开始执行退出程序流程")
            # 先隐藏窗口和托盘图标，避免用户重复点击
            self.hide()
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
                lprint("已隐藏窗口和托盘图标")
            
            # 关闭浏览器
            if hasattr(self, 'browser'):
                try:
                    lprint("正在关闭浏览器...")
                    self.browser.close_all()
                    lprint("浏览器已关闭")
                except Exception as e:
                    lprint(f"关闭浏览器失败: {str(e)}")
            
            # 关闭WebSocket连接
            if hasattr(self, 'chat_handler'):
                try:
                    lprint("正在关闭WebSocket连接...")
                    loop = asyncio.get_event_loop()
                    if not loop.is_closed():
                        loop.create_task(self.chat_handler.close())
                        lprint("WebSocket关闭任务已创建")
                except Exception as e:
                    lprint(f"关闭WebSocket失败: {str(e)}")
            
            # 获取当前进程ID和子进程
            try:
                lprint("开始清理子进程...")
                current_pid = os.getpid()
                current_process = psutil.Process(current_pid)
                children = current_process.children(recursive=True)
                
                # 终止所有子进程
                for child in children:
                    try:
                        child.terminate()
                        lprint(f"已终止子进程: {child.pid}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
                        lprint(f"终止子进程失败: {str(e)}")
                
                # 等待子进程完全终止
                psutil.wait_procs(children, timeout=3)
                lprint("子进程清理完成")
                
            except Exception as e:
                lprint(f"清理子进程失败: {str(e)}")
            
            # 设置退出原因
            global exit_reason
            exit_reason = "用户主动退出"
            lprint("退出原因已设置: 用户主动退出")
            
            # 使用定时器延迟退出
            try:
                lprint("设置退出定时器...")
                QTimer.singleShot(100, self._force_exit)
                lprint("退出定时器已设置")
            except Exception as e:
                lprint(f"设置退出定时器失败: {str(e)}")
                lprint("直接调用强制退出")
                self._force_exit()
                
        except Exception as e:
            error_msg = f"退出应用程序失败: {str(e)}\n{traceback.format_exc()}"
            lprint(error_msg)
            exit_reason = f"异常退出: {str(e)}"
            os._exit(1)

    def _force_exit(self):
        """强制退出程序"""
        try:
            lprint("执行强制退出...")
            QApplication.quit()
        except Exception as e:
            lprint(f"QApplication.quit()失败: {str(e)}")
            lprint("使用os._exit(0)强制退出")
            os._exit(0)

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
            # 获取托盘图标的全局位置
            geometry = self.tray_icon.geometry()
            if geometry.isValid():
                # 如果能获取到托盘图标位置，就在托盘图标位置显示
                self.tray_menu.popup(geometry.topRight())
            else:
                # 否则在鼠标位置显示
                cursor_pos = QCursor.pos()
                self.tray_menu.popup(cursor_pos)

    def toggle_overlay(self):
        """切换托盘图标闪烁效果"""
        
        if self.overlay_visible:
            self.tray_icon.setIcon(QIcon(self.tray_icon_path))
            self.overlay_visible = False
        else:
            self.tray_icon.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'logo.png')))
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
            self.tray_icon.setIcon(QIcon(self.tray_icon_path))
            self.overlay_visible = False

    def reload_browser(self):
        """重载浏览器"""
        if self.browser:
            self.browser.close_all()
            self.central_layout.removeWidget(self.browser)
            self.browser.deleteLater()
        
        self.browser = Browser(parent_widget=self)
        self.central_layout.addWidget(self.browser)

    def save_window_handle(self):
        """保存窗口句柄"""
        win_id = self.winId()
        handle = int(win_id)
        with open("D:/TD_Depot/Temp/chatroom.txt", "w") as f:
            f.write(str(handle))
    
    def restart_window(self):
        """重启窗口"""
        # 保存当前窗口的几何信息
        self.restart_application()

    def restart_application(self,current_geometry_str=""):
        """重启应用程序"""
        try:
            # 记录重启事件
            log_exit("用户请求重启程序")
            
            # 隐藏托盘图标
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
            
            # 获取当前进程ID
            current_pid = os.getpid()
            
            # 获取当前进程的所有子进程
            current_process = psutil.Process(current_pid)
            children = current_process.children(recursive=True)
            
            # 终止所有子进程
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # 等待子进程完全终止
            for child in children:
                try:
                    child.wait(timeout=3)
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    pass
            
            rect = self.geometry()
            current_geometry_str=f"{rect.x()},{rect.y()},{rect.width()},{rect.height()}"
            subprocess.Popen(['lugwit_chatroom.exe', __file__,'--geometry',current_geometry_str])
            
            # 退出当前实例
            os._exit(0)
            
        except Exception as e:
            error_msg = f"重启失败: {str(e)}\n{traceback.format_exc()}"
            lprint(error_msg)
            log_exit(f"重启失败: {str(e)}")
            print(f"重启失败: {str(e)}")

    def on_new_message(self, message_data: dict):
        """处理新消息"""
        try:
            # 转发消息到菜单
            if hasattr(self, 'tray_menu'):
                self.tray_menu.message_received.emit(message_data)
        except Exception as e:
            lprint(f"处理新消息失败: {str(e)}")
            lprint(traceback.format_exc())

def main(*args,**kwargs):
    lprint(is_process_running("lugwit_chatroom.exe") ,joinChatRoom)
    if joinChatRoom:
        try:
            # 初始化退出日志
            init_exit_logging()
            
            # 创建QApplication实例
            app = QApplication(sys.argv)
            
            # 创建qasync事件循环
            loop = QEventLoop(app)
            asyncio.set_event_loop(loop)
            
            # 应用暗色主题
            apply_stylesheet(app)
            
            # 创建主窗口
            geometry = kwargs.get("geometry")
            window = MainWindow()
            window.show()
            window.save_window_handle()
            
            if geometry:
                window.setGeometry(QRect(*geometry))
            
            # 使用qasync运行事件循环
            with loop:
                loop.run_forever()
                
        except Exception as e:
            error_msg = f"程序运行出错: {str(e)}\n{traceback.format_exc()}"
            lprint(error_msg)
            log_exit(f"程序崩溃: {str(e)}")
            
            # 尝试优雅地关闭程序
            try:
                if 'window' in locals():
                    window.close()
                if 'app' in locals():
                    app.quit()
            except Exception as close_error:
                lprint(f"关闭程序时出错: {str(close_error)}")
                lprint(traceback.format_exc())
            
            sys.exit(1)

def apply_stylesheet(app):
    """应用暗色主题样式"""
    style_file = os.path.join(os.path.dirname(__file__), 'static', 'dark_theme.qss')
    if os.path.exists(style_file):
        with open(style_file, 'r',encoding='utf-8') as f:
            app.setStyleSheet(f.read())
            lprint(f"成功应用样式表: {style_file}")
    else:
        lprint(f"样式表文件不存在: {style_file}")

def is_process_running(process_name: str) -> bool:
    """检查进程是否正在运行"""
    for process in psutil.process_iter(['name']):
        if process.info['name'] == process_name:
            lprint(process, process_name)
            return True
    return False

if __name__ == "__main__":
    fire.Fire(main)
