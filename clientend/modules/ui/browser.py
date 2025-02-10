"""
浏览器窗口相关代码
"""
import os
import json
import time
import socket
import sys
from typing import Optional, TYPE_CHECKING, Dict, Any
from PySide6.QtCore import QUrl, Qt, QObject, Slot, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QTabWidget,
    QMessageBox
)
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel

import Lugwit_Module as LM
lprint = LM.lprint

from ..handlers.chat_handler import ChatRoom

if TYPE_CHECKING:
    from ...pyqt_chatroom import MainWindow

class Browser(QMainWindow):
    """
    自定义浏览器窗口类。加载指定URL，并在页面加载完成后，通过runJavaScript执行alert。
    使用自定义的 MyWebEnginePage 来处理JS对话框，使其以QMessageBox的形式显示。
    """

    def __init__(self, parent_widget: Optional['MainWindow'] = None):
        super().__init__()
        self.setWindowTitle("ChatRoom")
        self.parent_widget = parent_widget
        self.username = getattr(parent_widget, 'userName', None) if parent_widget else None
        
        # 创建中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QHBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)

        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setContentsMargins(0, 0, 0, 0)
        self.central_layout.addWidget(self.tab_widget)

        # 创建浏览器页面
        self.browser = QWebEngineView()
        self.page = QWebEnginePage(self.browser)
        
        # 设置页面权限
        settings = self.page.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        
        # 设置剪贴板权限 - 使用新的方式
        profile = QWebEngineProfile.defaultProfile()
        profile.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)

        self.browser.setPage(self.page)
        self.tab_widget.addTab(self.browser, "聊天室")

        # 创建调试页面
        self.inspector = QWebEngineView()
        self.inspector.load(QUrl(f'http://{socket.gethostname()}:9222'))
        self.tab_widget.addTab(self.inspector, "调试")

        # 设置其他属性
        self.browser.loadFinished.connect(self.handlerHtmlLoaded)

        # 设置 QWebChannel 与处理器
        self.channel = QWebChannel()
        self.handler = ChatRoom(parent_com=self)
        self.channel.registerObject('pyObj', self.handler)
        self.browser.page().setWebChannel(self.channel)

        # 加载本地网页，请确保 http://localhost:7500 可正常访问且有简单页面
        self.browser.setUrl(QUrl(f"http://{socket.gethostname()}:7500"))
        self.browser.loadFinished.connect(self.autoLogin)

    def handlerHtmlLoaded(self, ok):
        if ok:
            self.browser.page().setDevToolsPage(self.inspector.page())
            self.inspector.show()

    def autoLogin(self):
        data = {
            "username": self.username,
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
        if self.parent_widget is not None:
            self.parent_widget.start_blinking(date, interval, *args, **kwargs)

    def stop_blinking(self):
        if self.parent_widget is not None:
            self.parent_widget.stop_blinking() 