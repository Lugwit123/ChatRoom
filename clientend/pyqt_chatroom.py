# -*- coding: utf-8 -*-
import ctypes
from functools import partial
from ipaddress import ip_address
import json
import subprocess
import sys
import os
import time
import psutil
import asyncio
import threading
import socket
import traceback
from pynput.keyboard import Key, Controller
from pywinauto import Application
import yaml
import fire
hostname = socket.gethostname()
os.environ['QT_API'] = 'pyqt6'
sys.path.append("D:\\TD_Depot\\Software\\Lugwit_syncPlug\\lugwit_insapp\\trayapp\\Lib")
import Lugwit_Module as LM
LM.lprint(os.environ['QT_API'])
import send_message

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
from qtpy.QtCore import (QUrl, QObject, Slot, QTimer, Signal, QPropertyAnimation, QPoint,
                        QEasingCurve, Qt, QRect)
from qtpy.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
    QAction,
    QMainWindow,
    QToolBar,
    QWidget,
    QTabWidget,
    QMessageBox,
    QProgressDialog
)
from qtpy.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from qtpy.QtWebEngineWidgets import QWebEngineView
from qtpy.QtWebChannel import QWebChannel
from qtpy.QtGui import QIcon, QAction

from L_Tools import vnc_install
from importlib import reload
from LPerforce import (loginP4, p4_baselib, P4Lib)
from LPerforce.P4LoginInfoModule import p4_loginInfo
curdir=os.path.dirname(__file__)
sys.path.append(curdir)
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\ChatRoom')
import notice_win
from backend import schemas
from typing import Optional, Dict, Any
lprint=LM.lprint
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



# 定义与 JavaScript 交互的处理类
class CallHandler(QObject):
    """
    定义一个处理与 JavaScript 交互的类，包含可供调用的槽函数。
    """
    notificationComplete = Signal(str)

    def __init__(self, parent_com: 'Browser' ):
        super().__init__(parent_com)
        self.parent_com: 'Browser' = parent_com

    @Slot(str)
    def pythonFunction(self, message):
        return True  # 返回 True 表示操作成功

    @Slot(str)
    def handleNewMessage(self, message: str):
        asyncio.ensure_future(self._handle_new_message_async(message))

    @asyncSlot(str)
    async def _handle_new_message_async(self, message:str):
        """处理新消息的槽函数"""
        print("收到通知消息", message)
        try:
            if isinstance(message, str):
                message = json.loads(message)
            reload(notice_win)

            message : schemas.MessageBase= schemas.MessageBase(**message)  # type: ignore
            LM.lprint(message)

            if message.popup_message:
                await self.sendNotification(message)
            self.notificationComplete.emit("Success")
            
            handlers = {
                schemas.MessageType.PRIVATE_CHAT.value: self.handle_private_message,
                # schemas.MessageType.GROUP_CHAT.value: self.handle_group_message,
                # schemas.MessageType.GET_USERS.value: self.handle_get_users,
                # schemas.MessageType.VALIDATION.value: self.handle_validation,
                # schemas.MessageType.REMOTE_CONTROL.value: self.handle_remote_control_message,
                schemas.MessageType.OPEN_PATH.value: self.handle_open_path,
            }
            if handlers.get(message.message_type):
                handler = handlers.get(message.message_type)
                await handler(message)
            return True
        except Exception as e:
            LM.lprint(f"Error in handleNewMessage: {e}")
            return False

    async def handle_private_message(self,message: schemas.MessageBase):
        self.parent_com.start_blinking()
    
    async def handle_remote_control_message(self,message: schemas.MessageBase):
        ip=message.content.get('ip')
        self.parent_com.parent_widget.connect_vnc(ip, 5900, 'OC.123456')
        # keyboard.press(Key.enter)
        # keyboard.release(Key.enter)


    async def handle_open_path(self,message: schemas.MessageBase):
        message_conetent=message.content
        localPath=message_conetent.get('localPath')
        if os.path.exists(localPath):
            os.startfile(os.path.dirname(localPath))
        elif os.path.exists('G:'+localPath[2:]):
            os.startfile(os.path.dirname('G:'+localPath[2:]))
        else:
            await QMessageBox.information(None, "信息提示", "文件或者文件夹不存在！")

    @asyncSlot(str)
    async def sendNotification(self,message: schemas.MessageBase):
        """发送通知消息"""
        try:
            event = asyncio.Event()
            # 修改notice_win.main调用，传入回调函数
            notice_win_ins = notice_win.main(message, on_close=lambda: event.set())
            # 等待通知窗口关闭
            await event.wait()
            lprint(notice_win_ins.result)
            if notice_win_ins.result=='open':
                self.parent_com.parent_widget.showNormal()
                self.parent_com.parent_widget.activateWindow()
                self.parent_com.scrool(chat_username=message.sender,
                                        message_id=message.id)
            if notice_win_ins.result=='accept':
                await self.handle_remote_control_message(message)
            
            return True
        except Exception as e:
            LM.lprint(f"Error in sendNotification: {str(e)}")
            return False

    @Slot(str)
    def exit_app(self, message):
        print("退出应用程序")
        os._exit(0)

    @Slot(str)
    def get_sid(self, message):
        return message



# 定义自定义浏览器窗口类
class Browser(QMainWindow):
    """
    自定义浏览器窗口类。加载指定URL，并在页面加载完成后，通过runJavaScript执行alert。
    使用自定义的 MyWebEnginePage 来处理JS对话框，使其以QMessageBox的形式显示。
    """

    def __init__(self,parent_widget=None):
        super().__init__()
        self.setWindowTitle("ChatRoom")
        self.parent_widget:MainWindow=parent_widget

        

        # 创建中心部件和标签页
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.tab_widget)

        # 创建浏览器页面
        self.browser = QWebEngineView()
        page = QWebEnginePage(self.browser)
        
        # 允许所有内容，包括复制功能
        settings = page.settings()
        settings.setAttribute(settings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(settings.WebAttribute.JavascriptCanAccessClipboard, True)
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(settings.WebAttribute.AllowRunningInsecureContent, True)
        
        # 启用剪贴板权限
        try:
            # PyQt6
            page.setFeaturePermission(
                QUrl(f"http://{server_ip}:7500"),
                QWebEnginePage.Feature.Clipboard,
                QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            )
        except:
            try:
                # PySide6
                page.setFeaturePermission(
                    QUrl(f"http://{server_ip}:7500"),
                    QWebEnginePage.Feature.ClipboardReadWrite,
                    QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
                )
            except Exception as e:
                print(f"Error setting clipboard permission: {e}")

        self.browser.setPage(page)
        self.tab_widget.addTab(self.browser, "聊天室")

        # 创建调试页面
        self.inspector = QWebEngineView()
        self.inspector.load(QUrl(f'http://{server_ip}:9222'))
        self.tab_widget.addTab(self.inspector, "调试")

        # 设置其他属性
        self.browser.loadFinished.connect(self.handlerHtmlLoaded)

        # 设置 QWebChannel 与处理器
        self.channel = QWebChannel()
        self.handler = CallHandler(parent_com=self)
        self.channel.registerObject('pyObj', self.handler)
        self.browser.page().setWebChannel(self.channel)

        # 加载本地网页，请确保 http://localhost:7500 可正常访问且有简单页面
        self.browser.setUrl(QUrl(f"http://{server_ip}:7500"))
        self.browser.loadFinished.connect(self.autoLogin)

    def handlerHtmlLoaded(self, ok):
        if ok:
            self.browser.page().setDevToolsPage(self.inspector.page())
            self.inspector.show()

    def autoLogin(self):
        data = {
            "username": userName,
            "password": "666"
        }
        time.sleep(0.2)
        # 将数据转换为 JSON 字符串
        data_json = json.dumps(data)

        # 构造调用 setFormData 的 JavaScript 代码
        js_code = f'''
        if (window.setFormData){{
            window.setFormData({data_json});
            }}
        '''
        self.browser.page().runJavaScript(js_code)
        time.sleep(0.1)
        self.browser.page().runJavaScript(js_code)
        click_js = """
        var button = document.querySelector('.submit-button');
        console.log(button)
        if (button) {
            button.click();
            console.log("按下")
        } else {
            console.log('未找到提交按钮。');
        }
        """
        self.browser.page().runJavaScript(click_js)
        time.sleep(0.1)
        self.browser.page().runJavaScript(click_js)
        get_sid_code = """
        (function() {
            var input = document.querySelector('#sid');
            if (input) {
                return input.value;
            } else {
                return 'error';
            }
        })();
        """
        self.browser.page().runJavaScript(get_sid_code, 0, self.handle_result)

    def on_load_finished(self):
        get_sid_code = """
        (function() {
            var input = document.querySelector('#sid');
            if (input) {
                return input.value;
            } else {
                return 'error';
            }
        })();
        """
        self.browser.page().runJavaScript(get_sid_code, 0, self.handle_result)

    def handle_result(self, result):
        if result != 'error':
            print(f"Input value: {result}")
        else:
            print("未找到元素 #sid")

    def scrool(self, chat_username="", message_id=0):
        js_code = (
            f'window.handleSelectUserbyUserName("{chat_username}");' +
            f'window.setTargetMessageIndex({message_id});'
        )
        lprint(locals())
        self.browser.page().runJavaScript(js_code)

    def js_callback(self, result):
        print("JavaScript 返回:", result)

    def close_all(self):
        """关闭浏览器和调试窗口"""
        if hasattr(self, 'tab_widget'):
            self.tab_widget.clear()
        if hasattr(self, 'inspector'):
            self.inspector.close()
            self.inspector.deleteLater()
        if hasattr(self, 'browser'):
            self.browser.close()
            self.browser.deleteLater()

    def start_blinking(self, date='', interval=500, *args, **kwargs):
        self.parent_widget.start_blinking(date, interval, *args, **kwargs)

    def stop_blinking(self):
        self.parent_widget.stop_blinking()

# 检查进程是否正在运行
def is_process_running(process_name: str) -> bool:
    for process in psutil.process_iter(['name']):
        if process.info['name'] == process_name:
            lprint(process, process_name)
            return True
    return False

# 处理 JavaScript 结果（备用函数）
def handle_result(result):
    print(f"获取到的值: {result}")

# 定义自定义菜单类，用于处理鼠标离开事件
class HoverMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)  # 启用鼠标追踪
        
        # 创建动画对象
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(200)  # 动画持续时间（毫秒）
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)  # 设置缓动曲线
        self.animation.finished.connect(self._on_animation_finished)
        
        self.is_hiding = False

    def showEvent(self, event):
        super().showEvent(event)
        self.is_hiding = False
        
    def leaveEvent(self, event):
        if not self.is_hiding:
            self.slide_out()
        super().leaveEvent(event)
        
    def slide_out(self):
        if self.is_hiding:
            return
            
        self.is_hiding = True
        start_pos = self.pos()
        end_pos = QPoint(start_pos.x(), start_pos.y() + self.height())
        
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        
        # 使用QTimer延迟3秒后启动动画
        QTimer.singleShot(3000, self.animation.start)

    def _on_animation_finished(self):
        if self.is_hiding:
            self.hide()
            self.is_hiding = False

class MainWindow(QMainWindow):
    def __init__(self, geometry=None):
        super().__init__()
        self.setWindowTitle('聊天室')
        # 创建中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        # 创建主布局
        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.init_ui()
        # 如果有保存的几何信息，则恢复
        if geometry:
            self.setGeometry(geometry)
        
        self.setup_window_properties()
        self.setup_tray_icon()
        # 初始化自动最小化定时器
        if LM.hostName != 'PC-20240202CTEU':
            self.minimize_timer = QTimer(self)
            self.minimize_timer.setSingleShot(True)  # 只触发一次
            self.minimize_timer.timeout.connect(self.hide_window)
            self.minimize_timer.start(8000)  # 8000毫秒 = 8秒
    
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

        
        self.layout.addLayout(button_layout)
        
        # 创建浏览器实例
        self.browser = Browser(parent_widget=self)
        self.layout.addWidget(self.browser)
        
        self.setLayout(self.layout)

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
                        partial(self.connect_vnc, 
                                option['host'], 
                                option['port'], 
                                option['password'])
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

    def connect_vnc(self, host: str, port: int, password: str):
        """连接到VNC服务器"""
        try:
            # 启动 VNC Viewer 并连接到指定地址
            pywinauto_app = Application().start(f'"D:\\TD_Depot\\Software\\ProgramFilesLocal\\RealVNC\\VNC Viewer\\vncviewer.exe" {host}:{port}')

            # 等待认证窗口加载
            dlg = pywinauto_app.window(title='Authentication')
            dlg.wait('exists', timeout=2)

            # 定位 Password 输入框并输入密码
            password_input = dlg.child_window(class_name="Edit", found_index=1)
            password_input.type_keys(password, with_spaces=True)

            # 定位 OK 按钮并点击
            ok_button = dlg.child_window(title="OK", class_name="Button")
            ok_button.click()
        except Exception as e:
            QMessageBox.warning(self, "连接失败", f"无法连接到 {host}:{port}\n错误: {str(e)}")

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
    async def request_remote_control(self, sender: str, recipient: str, role_type: str):
        """请求远程控制
        Args:
            sender: 发送者用户名
            recipient: 接收者用户名
            role_type: 远程控制类型
        """
        # 检查VNC版本和运行状态
        is_v7, version = self.check_vnc_version()
        
        if is_v7:
            # 如果是7.x版本，检查是否在运行
            if self.is_vnc_running():
                # VNC已在运行，直接发送远程控制请求
                send_message.send_message(
                    sender=sender,
                    recipient=recipient,
                    messageType="remote_control",
                )
                return
            else:
                # VNC 7.x已安装但未运行，启动服务
                try:
                    subprocess.run(['net', 'start', 'vncserver'], check=True)
                    send_message.send_message(
                        sender=sender,
                        recipient=recipient,
                        messageType="remote_control",
                    )
                    return
                except subprocess.CalledProcessError:
                    QMessageBox.warning(self, "启动服务失败", "VNC服务启动失败，请手动启动服务或重新安装。")
                    return
        else:
            # 不是7.x版本，提示安装
            reply = QMessageBox.question(
                self,
                "安装VNC Server",
                f"当前{'未安装VNC Server' if not version else f'VNC版本为{version}'}\n"
                "需要安装VNC Server 7.x版本才能使用远程控制功能。\n"
                "是否现在安装？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply != QMessageBox.Yes:
                return

        # 复制VNC服务器文件
        subprocess.run(['robocopy','/MIR',
            LM.ProgramFilesLocal_Public+r'\VNC-Server',
            r'D:\TD_Depot\Temp\VNC-Server'
        ])
        os.makedirs(r'D:\TD_Depot\Temp\VNC-Server',exist_ok=True)

        try:
            # 使用线程池执行安装
            loop = asyncio.get_event_loop()
            def run_installer():
                # 运行安装程序
                result = subprocess.run(
                    [r'D:\TD_Depot\Temp\VNC-Server\Installer.exe', '/qn'],
                    capture_output=True,
                    text=True
                )
                return result.stdout, result.stderr

            # 在线程池中执行安装
            try:
                stdout, stderr = await loop.run_in_executor(None, run_installer)
                
                if stderr:
                    lprint(f"VNC安装错误输出: {stderr}")
                    QMessageBox.warning(self, "安装失败", f"VNC服务安装失败\n{stderr}")
                else:
                    lprint("VNC安装成功")
                    # 等待服务启动
                    await asyncio.sleep(2)
                    # 发送远程控制请求
                    send_message.send_message(
                        sender=sender,
                        recipient=recipient,
                        messageType="remote_control",
                    )

            except Exception as e:
                lprint(traceback.format_exc())
                QMessageBox.warning(self, "安装失败", f"VNC服务安装失败: {str(e)}")

        except Exception as e:
            lprint(f"远程控制准备失败: {str(e)}")
            QMessageBox.warning(self, "远程控制准备", f"远程控制准备失败: {str(e)}")

    def show_window(self):
        """显示主窗口"""
        self.showNormal()
        self.activateWindow()
        # 启动8秒后自动最小化的定时器
        

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

    def start_blinking(self, date='', interval=500, *args, **kwargs):
        """开始托盘图标闪烁"""
        self.overlay_visible = False
        self.blink_timer.start(interval)

    def stop_blinking(self):
        """停止托盘图标闪烁"""
        self.blink_timer.stop()
        print("停止闪烁")
        self.tray_icon.setIcon(QIcon(self.tray_icon_path))
        self.overlay_visible = False

    def reload_browser(self):
        """重载浏览器"""
        if self.browser:
            self.browser.close_all()
            self.layout.removeWidget(self.browser)
            self.browser.deleteLater()
        
        self.browser = Browser(parent_widget=self)
        self.layout.addWidget(self.browser)

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
            QSystemTrayIcon.Information,
            2000,
        )

    def restart_window(self):
        """重启窗口"""
        # 保存当前窗口的几何信息

        self.restart_application()
        # # 创建新的MainWindow
        # new_window = MainWindow()
        # # 使用setGeometry一次性设置位置和大小
        # new_window.setGeometry(current_geometry)
        # new_window.show()

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
        with open (LM.oriEnvVarFile,'r',encoding='utf-8') as f:
            oriEnvVar=json.load(f)
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

if __name__ == "__main__":
    fire.Fire(main)
