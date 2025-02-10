"""
浏览器窗口相关代码
"""
import os
import json
import time
import socket
import sys
from typing import Optional, TYPE_CHECKING, Dict, Any, cast, Union
from PySide6.QtCore import QUrl, Qt, QObject, Slot, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QTabWidget,
    QMessageBox, QVBoxLayout, QLayout
)
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
import traceback

import Lugwit_Module as LM
lprint = LM.lprint

from ..handlers.chat_handler import ChatRoom

if TYPE_CHECKING:
    from ...pyqt_chatroom import MainWindow

class Browser(QMainWindow):
    """
    浏览器窗口类,负责:
    1. 加载前端页面
    2. 处理页面交互
    3. 通过WebSocket处理消息
    """

    def __init__(self, parent_widget: Optional['MainWindow'] = None):
        super().__init__()
        self.setWindowTitle("ChatRoom")
        self.parent_widget = parent_widget
        self.username = getattr(parent_widget, 'userName', None) if parent_widget else None
        
        # 创建中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建布局
        self._layout = QVBoxLayout()
        self.central_widget.setLayout(self._layout)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self._layout.addWidget(self.tab_widget)
        
        # 创建WebView
        self.web_view = QWebEngineView()
        self.tab_widget.addTab(self.web_view, "聊天室")
        
        # 创建调试页面
        self.inspector = QWebEngineView()
        self.inspector.load(QUrl(f'http://{socket.gethostname()}:9222'))
        self.tab_widget.addTab(self.inspector, "调试")
        
        # 设置处理器
        self.handler = ChatRoom(parent_com=cast('MainWindow', parent_widget))
        
        # 设置WebChannel
        self.channel = QWebChannel()
        self.channel.registerObject('pyObj', self.handler)
        self.web_view.page().setWebChannel(self.channel)
        
        # 连接信号
        self.web_view.loadFinished.connect(self.on_load_finished)
        
        # 设置浏览器
        self.setup_browser()
        
    @property
    def layout(self) -> Union[QLayout, None]:
        """获取布局"""
        return self._layout

    def setup_browser(self):
        """设置浏览器"""
        try:
            # 设置页面大小
            self.setMinimumSize(800, 600)
            
            # 启用开发者工具
            settings = self.web_view.page().settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
            
            # 设置剪贴板权限
            profile = QWebEngineProfile.defaultProfile()
            profile.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
            
            # 获取服务器地址
            server_ip = os.getenv('SERVER_IP', 'localhost')
            
            # 加载前端页面
            self.web_view.setUrl(QUrl(f"http://{server_ip}:7500"))
            
        except Exception as e:
            lprint(f"设置浏览器失败: {str(e)}")
            lprint(traceback.format_exc())
            
    def on_load_finished(self, ok: bool):
        """页面加载完成的处理"""
        if ok:
            # 设置开发者工具
            self.web_view.page().setDevToolsPage(self.inspector.page())
            
            # 自动登录
            self.auto_login()
            
    def auto_login(self):
        """自动登录"""
        try:
            if not self.username:
                return
                
            data = {
                "username": self.username,
                "password": "666"
            }
            
            # 将数据转换为 JSON 字符串
            data_json = json.dumps(data)
            
            # 注入登录数据
            js_code = f'''
            if (window.setFormData) {{
                window.setFormData({data_json});
            }}
            '''
            self.web_view.page().runJavaScript(js_code)
            
            # 点击登录按钮
            click_js = """
            var button = document.querySelector('.submit-button');
            if (button) {
                button.click();
            }
            """
            self.web_view.page().runJavaScript(click_js)
            
        except Exception as e:
            lprint(f"自动登录失败: {str(e)}")
            lprint(traceback.format_exc())

    def scrool(self, chat_username="", message_id=0):
        """滚动到指定消息"""
        try:
            js_code = (
                f'window.handleSelectUserbyUserName("{chat_username}");' +
                f'window.setTargetMessageIndex({message_id});'
            )
            self.web_view.page().runJavaScript(js_code)
        except Exception as e:
            lprint(f"滚动到消息失败: {str(e)}")
            lprint(traceback.format_exc())

    def close_all(self):
        """关闭所有窗口"""
        try:
            if hasattr(self, 'tab_widget'):
                self.tab_widget.clear()
            if hasattr(self, 'inspector'):
                self.inspector.close()
                self.inspector.deleteLater()
            if hasattr(self, 'web_view'):
                self.web_view.close()
                self.web_view.deleteLater()
        except Exception as e:
            lprint(f"关闭窗口失败: {str(e)}")
            lprint(traceback.format_exc())

    def start_blinking(self, date='', interval=500, *args, **kwargs):
        """开始闪烁提醒"""
        if self.parent_widget is not None:
            self.parent_widget.start_blinking(date, interval, *args, **kwargs)

    def stop_blinking(self):
        """停止闪烁提醒"""
        if self.parent_widget is not None:
            self.parent_widget.stop_blinking() 