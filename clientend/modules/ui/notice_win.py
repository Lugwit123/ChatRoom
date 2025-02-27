from datetime import datetime
import os
import sys
import socket
import traceback
from typing import Optional, Dict, Any
import asyncio
from PySide6.QtCore import QTimer
from qasync import asyncSlot
from pathlib import Path
from qasync import QEventLoop, QApplication, asyncSlot, asyncClose
# 根据主机名选择Qt后端
hostname = socket.gethostname()
os.environ['QT_API'] = 'pyqt6' if hostname == 'OC5' else 'pyside6'
from dotenv import load_dotenv
load_dotenv()
import markdown
import re
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton, 
                           QVBoxLayout, QHBoxLayout, QWidget, QTextBrowser, QListWidget, QListWidgetItem, QMessageBox)
from PySide6.QtGui import QPixmap, QPainter, QPainterPath
from PySide6.QtCore import Qt, QPoint, QObject, Signal, Slot
import Lugwit_Module as LM


match = re.search(r'.+\\clientend', __file__)
if match:
    sys.path.append(match.group(0))
    print(match.group(0))
# 为了保证这个模块能独立运行,使用绝对路径导入
from modules.vnc.vnc_connector import vnc_connector
from modules.events.signals import chat_signals
from modules.types.types import MessageBase, ButtonConfig, ButtonId, NotificationConfig, DEFAULT_BUTTON_CONFIG, MessageType
from modules.ui.reject_reason_dialog import RejectReasonDialog

lprint = LM.lprint

if sys.version_info >= (3, 9):
    from zoneinfo import ZoneInfo
else:
    from backports.zoneinfo import ZoneInfo

def get_rounded_pixmap(image_path: str, width: int, height: int, radius: int) -> QPixmap:
    """创建圆角图片
    
    Args:
        image_path (str): 图片路径
        width (int): 宽度
        height (int): 高度
        radius (int): 圆角半径
        
    Returns:
        QPixmap: 处理后的图片
    """
    pixmap = QPixmap(image_path).scaled(
        width, height, 
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )
    rounded = QPixmap(pixmap.size())
    rounded.fill(Qt.GlobalColor.transparent)

    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(rounded.rect(), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()

    return rounded

def create_markdown_view(markdown_text: str) -> QTextBrowser:
    """创建Markdown视图

    Args:
        markdown_text (str): Markdown文本

    Returns:
        QTextBrowser: 处理后的视图
    """
    html = markdown.markdown(markdown_text)
    text_browser = QTextBrowser()
    text_browser.setAlignment(Qt.AlignmentFlag.AlignCenter)
    text_browser.setStyleSheet(
        "color: white; font-size: 14px; font-family: Arial; border: none; background: transparent;"
    )
    text_browser.setHtml(html)
    return text_browser

class NotificationWindow(QWidget):
    """通知窗口类"""
    
    # 定义信号
    request_accepted = Signal(str, str)  # (username, ip)
    request_rejected = Signal(str, str, bool)  # (username, reason, is_custom)
    notification_closed = Signal()  # 窗口关闭信号
    
    # 添加类变量来存储单例实例
    _instance = None
    
    def __new__(cls, config: NotificationConfig = None):
        """确保只创建一个窗口实例"""
        lprint(f"NotificationWindow.__new__ 被调用, 当前实例: {cls._instance}")
        if cls._instance is None:
            lprint("创建新的NotificationWindow实例")
            cls._instance = super(NotificationWindow, cls).__new__(cls)
            # 初始化QWidget
            super(NotificationWindow, cls._instance).__init__()
            # 初始化基本属性
            cls._instance._initialized = False
            cls._instance.request_list = []  # 请求队列
            cls._instance.current_request = None
            cls._instance.markdown_view = None
            cls._instance._parent_window = None
            lprint("基本属性已初始化")
        else:
            lprint("使用已存在的NotificationWindow实例")
        return cls._instance
    
    def __init__(self, config: NotificationConfig = None):
        """初始化通知窗口"""
        lprint(f"NotificationWindow.__init__ 被调用, 初始化状态: {hasattr(self, '_initialized')}")
        
        # 保存父窗口引用
        if config and config.parent_window:
            self.setParent(config.parent_window)
            lprint(f"设置父窗口: {config.parent_window}")
        
        # 如果已经初始化过，只更新配置
        if hasattr(self, '_initialized') and self._initialized:
            lprint("窗口已初始化，只更新配置")
            if config:
                self.config = config
                # 更新信号连接
                if config.chat_signals:
                    lprint("更新信号连接")
                    self._update_signal_connections(config.chat_signals)
                # 添加新消息
                if config.message:
                    lprint(f"添加新消息: {config.message}")
                    self.add_request(config.message)
            return
            
        # 第一次初始化
        lprint("开始首次初始化窗口")
        self._initialized = True
        self.config = config
        self.button_config = config.button_config or DEFAULT_BUTTON_CONFIG if config else DEFAULT_BUTTON_CONFIG
        
        # 连接信号到全局信号
        if config and config.chat_signals:
            lprint("初始化信号连接")
            self._update_signal_connections(config.chat_signals)
        
        # 初始化UI
        lprint("初始化UI")
        self._init_ui()

        # 添加初始请求
        if config and config.message:
            lprint(f"添加初始消息: {config.message}")
            self.add_request(config.message)


    def get_main_window(self):
        """获取主窗口实例"""
        # 遍历父窗口链，找到MainWindow实例
        parent = self.parent()
        while parent:
            if hasattr(parent, 'chat_handler'):  # 使用chat_handler作为MainWindow的标识
                return parent
            parent = parent.parent()
        return None

    def set_parent_window(self, parent_window):
        """设置父窗口引用"""
        self._parent_window = parent_window

    def _update_signal_connections(self, chat_signals):
        """更新信号连接"""
        # 断开旧的连接
        try:
            self.request_accepted.disconnect()
            self.request_rejected.disconnect()
            self.notification_closed.disconnect()
        except:
            pass  # 忽略断开连接时的错误
            
        # 建立新的连接
        self.request_accepted.connect(
            lambda username, ip: chat_signals.remote_control_accepted.emit(username, ip))
        self.request_rejected.connect(
            lambda username, reason, is_custom: chat_signals.remote_control_rejected.emit(username, reason, is_custom))
        self.notification_closed.connect(
            chat_signals.notification_closed.emit)
        chat_signals.message_received.connect(self._on_message_received)

    def _init_ui(self):
        """初始化UI"""
        try:
            lprint("开始初始化UI")
            # 设置窗口属性
            flags = (
                Qt.WindowType.FramelessWindowHint |  # 无边框
                Qt.WindowType.WindowStaysOnTopHint 
            )
            self.setWindowFlags(flags)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # 透明背景
            
            # 设置对象名称以便QSS定位
            self.setObjectName("NotificationWindow")
            
            # 创建主布局
            self.main_layout = QVBoxLayout(self)
            self.main_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
            self.main_layout.setSpacing(0)  # 移除间距
            
            # 创建背景窗口部件
            self.background_widget = QWidget()
            self.background_widget.setObjectName("background_widget")
            self.background_layout = QVBoxLayout()
            self.background_layout.setContentsMargins(10, 10, 10, 10)
            self.background_layout.setSpacing(5)
            self.background_widget.setLayout(self.background_layout)

            title_label = QLabel("远程控制请求列表")
            title_label.setObjectName("title_label")
            title_label.setFixedHeight(30)
            
            self.background_layout.addWidget(title_label)
            
            # 创建分隔线
            separator = QWidget()
            separator.setObjectName("separator")
            separator.setFixedHeight(1)
            self.background_layout.addWidget(separator)
            
            # 创建列表控件
            self.list_widget = QListWidget()
            self.list_widget.currentItemChanged.connect(self._on_selection_changed)
            self.background_layout.addWidget(self.list_widget)
            self.list_widget.setFixedHeight(50)

            
            # 创建内容区域
            self.content_widget = QLabel()
            self.content_widget.setObjectName("content_widget")
            self.background_layout.addWidget(self.content_widget)
            self.content_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # 设置内容区域的最小高度
            self.content_widget.setMinimumHeight(50)  
            
            # 创建按钮区域
            button_layout = QHBoxLayout()
            button_layout.setContentsMargins(10, 15, 10, 10)  # 增加上下边距
            button_layout.setSpacing(20)  # 增加按钮间距
            button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 居中对齐
            
            # 创建接受按钮，使用button_config中的配置
            self.accept_button = QPushButton(self.button_config.get('accept', "接受控制"))
            self.accept_button.setObjectName("accept_button")  # 设置对象名称以便QSS定位
            self.accept_button.setCursor(Qt.CursorShape.PointingHandCursor)  # 设置鼠标悬停时的光标形状
            self.accept_button.setFixedHeight(40)  # 设置按钮高度
            self.accept_button.clicked.connect(self._on_accept_clicked)
            button_layout.addWidget(self.accept_button)
            
            # 创建拒绝按钮，使用button_config中的配置
            self.reject_button = QPushButton(self.button_config.get('reject', "拒绝"))
            self.reject_button.setObjectName("reject_button")  # 设置对象名称以便QSS定位
            self.reject_button.setCursor(Qt.CursorShape.PointingHandCursor)  # 设置鼠标悬停时的光标形状
            self.reject_button.setFixedHeight(40)  # 设置按钮高度
            self.reject_button.clicked.connect(self._on_reject_clicked)
            button_layout.addWidget(self.reject_button)
            
            self.background_layout.addLayout(button_layout)
            
            # 将背景窗口部件添加到主布局
            self.main_layout.addWidget(self.background_widget)
            
            # 加载QSS样式
            style_file = Path(__file__).parent / "styles" / "notice_win.qss"
            if style_file.exists():
                with open(style_file, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
                lprint("已加载QSS样式文件")
            else:
                lprint(f"QSS样式文件不存在: {style_file}")

            
        except Exception as e:
            lprint(f"UI初始化失败: {str(e)}")
            traceback.print_exc()

    def _adjust_list_widget_height(self):
        """Adjust the height of the list widget to fit its contents."""
        total_height = 0
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item_height = self.list_widget.visualItemRect(item).height()
            total_height += item_height + 4  # 4 is the item spacing

        # Set the list widget height to fit its contents
        self.list_widget.setFixedHeight(total_height + 10)

    def add_request(self, message: MessageBase) -> bool:
        """添加新的请求"""
        try:
            # 检查是否是重复请求
            for request in self.request_list:
                if (request.sender == message.sender and 
                    request.message_type == message.message_type):
                    lprint(f"忽略重复请求: {message.sender}")
                    return False
            
            # 添加到队列
            self.request_list.append(message)
            
            # 从content中提取IP和昵称
            ip = "未知"
            sender_nickname = message.sender
            
            if isinstance(message.content, dict):
                ip = message.content.get('ip', "未知")
                sender_nickname = message.content.get('nickname', message.sender)
                
            # 添加到列表控件
            item_text = f"用户: {sender_nickname}\nIP: {ip}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, message)
            self.list_widget.addItem(item)
            
            # 调整列表和窗口高度
            
            
            # 如果是第一个请求，自动选中
            if len(self.request_list) == 1:
                self.list_widget.setCurrentRow(0)
                self._show_request(message)
            self.show()
            
            self.raise_()  # 将窗口置于最前
            
            self.activateWindow()  # 激活窗口
            
            self.setWindowState((self.windowState() & ~Qt.WindowState.WindowMinimized) | Qt.WindowState.WindowActive)

            self._adjust_list_widget_height()
            self._adjust_height()
            #self.adjustSize()
            lprint(f"成功添加新请求: {sender_nickname}")
            return True
            
        except Exception as e:
            lprint(f"添加请求失败: {str(e)}")
            traceback.print_exc()
            return False

    def _show_request(self, message: MessageBase):
        """显示请求内容
        
        Args:
            message (MessageBase): 请求消息
        """
        try:
            lprint(f"显示请求内容: {message}")
            self.current_request = message
            self.clear_content()
            
            # 从content中获取IP和昵称
            content = message.content
            ip = "未知"
            sender_nickname = message.sender
            
            if isinstance(content, dict):
                ip = content.get('ip', "未知")
                sender_nickname = content.get('nickname', message.sender)
            
            # 创建请求详情标签
            self.content_widget.setText(f"远程控制邀请\n发送人: {sender_nickname}")

            
            lprint("请求内容显示完成")
            
        except Exception as e:
            lprint(f"显示请求内容失败: {str(e)}")
            traceback.print_exc()

    def _adjust_height(self):

        
        # 更新窗口位置，确保不会超出屏幕
        self._position_window()
        
    def _on_selection_changed(self):
        """处理选择变化"""
        current_item = self.list_widget.currentItem()
        if current_item:
            message = current_item.data(Qt.ItemDataRole.UserRole)
            self._show_request(message)

    def remove_current_request(self):
        """移除当前请求"""
        current_row = self.list_widget.currentRow()
        lprint("移除当前请求")
        if current_row >= 0:
            self.list_widget.takeItem(current_row)
            self.request_list.pop(current_row)
            
            # 如果还有其他请求，选中下一个
            if self.list_widget.count() > 0:
                next_row = min(current_row, self.list_widget.count() - 1)
                self.list_widget.setCurrentRow(next_row)
            
            # 重新计算窗口高度
            self._adjust_height()

    def closeEvent(self, event: Any) -> None:
        """窗口关闭事件处理"""
        lprint("窗口关闭事件处理")
        # 清空请求列表，确保窗口关闭后不会重新弹出
        self.request_list.clear()
        self.list_widget.clear()
        super().closeEvent(event)

    def normal_toast(self) -> None:
        """普通消息显示"""
        lprint("普通消息显示")
        markdown_text = (
            "# 通知消息\n" +
            f"## 发送人:{self.config.message.sender}\n" +
            f"{self.config.message.content}"
        )
        lprint(markdown_text)
        self.markdown_view = create_markdown_view(markdown_text)
        self.main_layout.addWidget(self.markdown_view)

    def remote_control_toast(self) -> None:
        """远程控制消息显示"""
        lprint("远程控制消息显示")
        self.setFixedHeight(300)
        markdown_text = (
            "# 通知消息\n" +
            f"## 远程控制邀请\n\n" +
            f"## 发  送   人:  {self.config.message.sender}\n"
        )
        lprint(markdown_text)
        self.markdown_view = create_markdown_view(markdown_text)
        self.main_layout.addWidget(self.markdown_view)

    def abc_check_toast(self) -> None:
        """Abc检查消息显示"""
        lprint("Abc检查消息显示")
        if self.config.image_path:
            rounded_pixmap = get_rounded_pixmap(self.config.image_path, 560, 130, 15)
            pixmap_label = QLabel()
            pixmap_label.setFixedSize(560, 130)
            pixmap_label.setPixmap(rounded_pixmap)
            pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.main_layout.addWidget(pixmap_label)
            pixmap_label.setStyleSheet("background: transparent;border: 1px solid #a28135;border-radius: 15px;")

            markdown_text = (
                "# Abc检查反馈\n" +
                f"## 制作人:{self.config.message.recipient}\n" +
                f"### 审核数据:\n{self.config.message.content['url'] if isinstance(self.config.message.content, dict) else self.config.message.content}"
            )
            self.markdown_view = create_markdown_view(markdown_text)
            self.main_layout.addWidget(self.markdown_view)

    @asyncSlot()
    async def _on_accept_clicked(self):
        """处理接受按钮点击"""
        lprint("处理接受按钮点击")
        if not self.current_request:
            return
            
        try:
            # 从content中提取IP和消息ID
            content = self.current_request.content
            ip = "未知"
            message_id = None
            
            if isinstance(content, dict):
                ip = content.get('ip', "未知")
                message_id = content.get('message_id')
                
            lprint(f"接受来自 {self.current_request.sender} 的远程控制请求")
            lprint(f"准备连接到IP: {ip}, 消息ID: {message_id}")
            
            # 发送接受信号
            self.request_accepted.emit(self.current_request.sender, ip)
            self.remove_current_request()
            # 只在没有更多请求时隐藏窗口
            if self.list_widget.count() == 0:
                self.hide()
            # 使用VNC连接器建立连接
            if vnc_connector.connect(ip):
                lprint("VNC连接已建立")
            else:
                lprint("VNC连接失败")
            
            
                
        except Exception as e:
            lprint(f"处理接受请求失败: {str(e)}")
            traceback.print_exc()
            QMessageBox.warning(
                self,
                "错误",
                f"处理请求失败: {str(e)}",
                QMessageBox.StandardButton.Ok
            )

    @asyncSlot()
    async def _on_reject_clicked(self):
        """处理拒绝按钮点击"""
        lprint("处理拒绝按钮点击")
        try:
            if not self.current_request:
                lprint("没有当前请求，无法处理拒绝操作")
                return
                
            lprint(f"开始处理拒绝请求: {self.current_request.sender}")
            
            # 显示拒绝理由对话框
            dialog = RejectReasonDialog(self)
            reject_response = dialog.get_reason()
            
            if reject_response:
                lprint(f"用户选择的拒绝理由: {reject_response.reason}")
                lprint(f"是否自定义理由: {reject_response.is_custom}")
                
                try:
                    # 从content中获取消息ID
                    content = self.current_request.content
                    message_id = None
                    if isinstance(content, dict):
                        message_id = content.get('message_id')
                    
                    # 构造响应数据
                    response_data = {
                        "sender": self.current_request.recipient,  # 当前用户
                        "recipient": self.current_request.sender,  # 发起请求的用户
                        "content": {
                            "status": "rejected",
                            "reason": reject_response.reason,
                            "is_custom_reason": reject_response.is_custom,
                            "message_id": message_id,
                            "response_time": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
                        },
                        "message_type": MessageType.remote_control.value,
                        "direction": "response"  # 标识这是一个响应
                    }
                    
                    # 发送拒绝信号
                    self.request_rejected.emit(
                        self.current_request.sender,
                        reject_response.reason,
                        reject_response.is_custom
                    )
                    lprint("拒绝信号已发送")
                    
                    # 通过WebSocket发送响应给发起端
                    main_window = self.get_main_window()
                    if main_window and hasattr(main_window, 'chat_handler'):
                        await main_window.chat_handler.sio.emit('message', response_data, namespace='/chat/private')
                        lprint("已发送拒绝响应")
                    
                    self._remove_request_delayed()

                    
                except Exception as signal_error:
                    lprint(f"发送拒绝信号失败: {str(signal_error)}")
                    traceback.print_exc()
            else:
                lprint("用户取消了拒绝操作")
                    
        except Exception as e:
            lprint(f"处理拒绝请求失败: {str(e)}")
            traceback.print_exc()
            QMessageBox.warning(
                self,
                "错误",
                f"处理拒绝请求失败: {str(e)}",
                QMessageBox.StandardButton.Ok
            )

    def _remove_request_delayed(self):
        """延迟移除请求"""
        lprint("延迟移除请求")
        try:
            lprint("开始移除当前请求")
            current_sender = self.current_request.sender if self.current_request else "unknown"
            
            self.remove_current_request()
            lprint(f"已移除来自 {current_sender} 的请求")
            
            # 只在没有更多请求时隐藏窗口
            if self.list_widget.count() == 0:
                self._hide_window_delayed()
                
        except Exception as e:
            lprint(f"延迟移除请求失败: {str(e)}")
            traceback.print_exc()
            
    def _hide_window_delayed(self):
        """延迟隐藏窗口"""
        lprint("延迟隐藏窗口")
        try:
            lprint("开始隐藏窗口")
            self.hide()
            lprint("窗口已隐藏")
        except Exception as e:
            lprint(f"隐藏窗口失败: {str(e)}")
            traceback.print_exc()

    @Slot(object)
    def _on_message_received(self, message: MessageBase):
        """处理接收到的消息"""
        lprint("处理接收到的消息")
        try:
            if message.popup_message:
                self.add_request(message)
                self.show()
        except Exception as e:
            lprint(f"处理接收消息失败: {str(e)}")
            traceback.print_exc()

    def _position_window(self) -> None:
        """设置窗口位置到屏幕右下角"""
        try:
            lprint("开始设置窗口位置")
            # 获取主屏幕
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()  # 获取可用区域（不包括任务栏）
            
            # 计算窗口位置（右下角）
            x = screen_geometry.width() - self.width() - 20  # 右边留20像素边距
            y = screen_geometry.height() - self.height() - 20  # 底部留20像素边距
            
            # 确保窗口不会超出屏幕
            x = max(0, min(x, screen_geometry.width() - self.width()))
            y = max(0, min(y, screen_geometry.height() - self.height()))
            
            lprint(f"设置窗口位置: x={x}, y={y}")
            self.move(x, y)

            

            
        except Exception as e:
            lprint(f"设置窗口位置失败: {str(e)}")
            traceback.print_exc()

    def clear_content(self):
        """清空内容区域"""
        try:
            self.content_widget.setText("")
        except Exception as e:
            lprint(f"清空内容区域失败: {str(e)}")
            traceback.print_exc()

def create_notification_window(
    image_path: Optional[str], 
    message: MessageBase, 
    result: str = "", 
    button_config: Optional[ButtonConfig] = None,
    parent_window: Optional[QWidget] = None,
    chat_signals: Optional[Any] = None
) -> NotificationWindow:
    """创建通知窗口
    
    Args:
        image_path (Optional[str]): 图片路径
        message (MessageBase): 消息对象
        result (str, optional): 结果. Defaults to "".
        button_config (Optional[ButtonConfig], optional): 按钮配置. Defaults to None.
        parent_window (Optional[QWidget], optional): 父窗口. Defaults to None.
        chat_signals (Optional[Any], optional): 聊天信号. Defaults to None.
        
    Returns:
        NotificationWindow: 通知窗口实例
    """
    config = NotificationConfig(
        message=message,
        result=result,
        image_path=image_path,
        button_config=button_config,
        chat_signals=chat_signals,
        parent_window=parent_window
    )
    window = NotificationWindow(config)
    return window

def main(message: MessageBase, result: str = "") -> NotificationWindow:
    """主函数"""
    lprint("主函数")
    lprint(message)
    image_path = f'{LM.LugwitLibDir}/ChatRoom/backend/routers/check_file/static/alembic.png'
    
    button_config: ButtonConfig = {
        'accept': '确认',
        'open': '查看详情',
        'close': '取消'
    }
    
    notification_window = create_notification_window(
        image_path=image_path,
        message=message,
        result=result,
        button_config=button_config
    )
    notification_window.show()
    return notification_window

async def test():   
    app = QApplication(sys.argv)
        # 创建qasync事件循环
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    server_ip = os.environ['SERVER_IP']
    
    image_path = f'{LM.LugwitLibDir}/ChatRoom/backend/routers/check_file/static/alembic.png'
    
    message_data = {
        "sender": "system01",
        "recipient": "fengqingqing",
        "content": {
            'check_type': 'cfx_abc_check',
            'url': f'http://{server_ip}:1026/check_file/abc_check_show/ZTS/06.CFX/EP001/ep001_sc001_shot0010/ep001_sc001_shot0010_check.json',
            'check_data_file': '/ZTS/06.CFX/EP001/ep001_sc001_shot0010/ep001_sc001_shot0010_check.json'
        },
        "timestamp": datetime.now().isoformat(),
        "recipient_type": "user",
        "status": ["pending"],
        "direction": "request",
        "message_content_type": "html",
        "message_type": 'remote_control',
        "popup_message": True,
    }
    
    message = MessageBase(**message_data)
    notification_window = create_notification_window(image_path, message, "")
    notification_window.show()
    asyncio.create_task(run_event_loop(loop, app))
    return True

async def run_event_loop(loop: QEventLoop, app: QApplication):
    """运行Qt事件循环"""
    try:
        while True:
            app.processEvents()  # 处理Qt事件
            await asyncio.sleep(0.01)  # 避免CPU占用过高
    except Exception as e:
        lprint(f"事件循环运行失败: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test())
    loop.run_forever()

