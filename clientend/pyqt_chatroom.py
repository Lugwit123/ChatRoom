"""
主应用程序入口
"""
import ctypes
import sys
import os
import time
import psutil
import asyncio
import socket
import traceback
import yaml
import fire
import subprocess
from typing import Optional, Dict, Any
from pywinauto import Application

hostname = socket.gethostname()
os.environ['QT_API'] = 'pyqt6'
sys.path.append("D:\\TD_Depot\\Software\\Lugwit_syncPlug\\lugwit_insapp\\trayapp\\Lib")
import Lugwit_Module as LM
lprint = LM.lprint

# 从文件读取服务器IP地址
try:
    with open("A:/temp/chatRoomLog/server_ip_address.txt", "r") as f:
        server_ip = f.read().strip()
        os.environ['SERVER_IP'] = server_ip
except Exception as e:
    print(f"Error reading server IP: {e}")
    server_ip = "localhost"  # 如果读取失败则使用localhost作为后备

# 根据主机名选择Qt后端
from qasync import QEventLoop, QApplication, asyncSlot
from PySide6.QtCore import (QRect, Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve)
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSystemTrayIcon, QMenu, QMainWindow, QToolBar, QMessageBox
)
from PySide6.QtGui import QIcon, QAction

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

lprint = LM.lprint
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
    def __init__(self, geometry: Optional[QRect] = None):
        super().__init__()
        self.parent_widget = self  # 设置parent_widget为self
        self.setWindowTitle('聊天室')
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QHBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)
        
        self.init_ui()
        
        if geometry:
            self.setGeometry(geometry)
        
        self.setup_window_properties()
        self.setup_tray_icon()
        
        if LM.hostName != 'PC-20240202CTEU':
            self.minimize_timer = QTimer(self)
            self.minimize_timer.setSingleShot(True)
            self.minimize_timer.timeout.connect(self.hide_window)
            self.minimize_timer.start(8000)
        
        # 创建ChatRoom实例
        self.chat_room = ChatRoom(parent_com=self)

    def init_ui(self):
        """初始化UI组件"""
        # 创建工具栏
        toolbar = QToolBar()
        toolbar.setStyleSheet("""
            QToolBar {
                spacing: 0;
                padding: 0;
                margin: 0;
                border: none;
            }
            QToolBar QToolButton {
                padding: 5px;
                margin: 0;
            }
        """)
        self.addToolBar(toolbar)

        # 添加重载按钮
        reload_action = QAction('重载', self)
        reload_action.triggered.connect(self.reload_browser)
        toolbar.addAction(reload_action)

        # 添加重启按钮
        restart_action = QAction('重启', self)
        restart_action.triggered.connect(self.restart_window)
        toolbar.addAction(restart_action)

        # 创建按钮布局
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)
        
        self.central_layout.addLayout(button_layout)
        
        # 创建浏览器实例
        self.browser = Browser(parent_widget=self)
        self.central_layout.addWidget(self.browser)
        
        self.setLayout(self.central_layout)

    def setup_window_properties(self):
        """设置窗口属性"""
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("chatroom")
        self.setWindowIcon(QIcon(os.path.join(LM.LugwitToolDir, 'icons', 'logo.png')))
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

    def setup_tray_icon(self):
        """设置系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon_path = os.path.join(LM.LugwitToolDir, 'icons', 'logo.png')
        self.new_message_icon_path = os.path.join(LM.LugwitToolDir, 'icons', 'mail-message-new.png')
        
        if not os.path.exists(self.tray_icon_path):
            self.tray_icon_path = QIcon.fromTheme("application-exit")
        self.tray_icon.setIcon(QIcon(self.tray_icon_path))

        # 创建托盘图标的上下文菜单
        tray_menu = HoverMenu(self)  # 使用自定义菜单类
        tray_menu.setStyleSheet("QMenu { font-size: 25px; font-family: 'Consolas', monospace; }")  # 设置菜单字体大小和等宽字体

        # 从yaml配置文件读取远程控制选项
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'remote_control.yaml')

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            for option in config['remote_control_options']:
                action = QAction(option['label'], self)
                if option['action'] == 'request':
                    # 创建一个lambda函数来包装参数
                    action.triggered.connect(
                        lambda checked, opt=option: self.request_remote_control(
                            userName, opt.get('username'), opt.get('type')
                        )
                    )
                elif option['action'] == 'connect':
                    # VNC直接连接
                    action.triggered.connect(
                        lambda checked, host=option['host'], port=option['port'], 
                               password=option['password']: self.connect_vnc(host, port, password)
                    )
                tray_menu.addAction(action)

        # 添加"显示"动作
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        # 添加"隐藏"动作
        hide_action = QAction("隐藏", self)
        hide_action.triggered.connect(self.hide_window)
        tray_menu.addAction(hide_action)

        # 添加"重启"动作
        restart_action = QAction("重启", self)
        restart_action.triggered.connect(self.restart_application)
        tray_menu.addAction(restart_action)

        # 添加"退出"动作
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.exit_application)
        tray_menu.addAction(exit_action)

        # 设置托盘图标菜单
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # 设置闪烁定时器
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_overlay)
        self.overlay_visible = False
        
        # 显示托盘图标
        self.tray_icon.show()

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
                    await self.chat_room._send_remote_control_message(sender, recipient, role_type)
                return
            else:
                # VNC 7.x已安装但未运行，启动服务
                try:
                    subprocess.run(['net', 'start', 'vncserver'], check=True)
                    if sender and recipient and role_type:  # Type narrowing
                        await self.chat_room._send_remote_control_message(sender, recipient, role_type)
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
                    await self.chat_room._send_remote_control_message(sender, recipient, role_type)

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
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        QApplication.quit()

    def on_tray_icon_activated(self, reason):
        """处理托盘图标的激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isMinimized() or not self.isVisible():
                self.showNormal()
                self.raise_()
            else:
                self.hide()
        self.stop_blinking()

    def toggle_overlay(self):
        """切换托盘图标闪烁效果"""
        if self.overlay_visible:
            self.tray_icon.setIcon(QIcon(self.tray_icon_path))
            self.overlay_visible = False
        else:
            self.tray_icon.setIcon(QIcon(self.new_message_icon_path))
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
    
    def closeEvent(self, event):
        """重写关闭事件，将窗口最小化到托盘而不是关闭"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "ChatRoom",
            "应用程序已最小化到系统托盘。双击托盘图标可重新打开。",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def restart_window(self):
        """重启窗口"""
        # 保存当前窗口的几何信息
        self.restart_application()

    def restart_application(self,current_geometry_str=""):
        """重启应用程序"""
        try:
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
            print(f"重启失败: {str(e)}")

def main(*args,**kwargs):
    lprint(is_process_running("lugwit_chatroom.exe") ,joinChatRoom)
    if joinChatRoom:
        # 使用独立环境变量启动进程
        app = QApplication(sys.argv)
        apply_stylesheet(app)  # 应用暗色主题
        geometry=kwargs.get("geometry")
        window = MainWindow()
        window.show()
        window.save_window_handle()
        print(geometry)
        print(type(geometry))
        if geometry:
            window.setGeometry(QRect(*geometry))
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)

        with loop:
            loop.run_forever()
        
def apply_stylesheet(app):
    """应用暗色主题样式"""
    style_file = os.path.join(os.path.dirname(__file__), 'dark_theme.css')
    if os.path.exists(style_file):
        with open(style_file, 'r',encoding='utf-8') as f:
            app.setStyleSheet(f.read())

def is_process_running(process_name: str) -> bool:
    """检查进程是否正在运行"""
    for process in psutil.process_iter(['name']):
        if process.info['name'] == process_name:
            lprint(process, process_name)
            return True
    return False

if __name__ == "__main__":
    fire.Fire(main)
