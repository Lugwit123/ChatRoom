"""
菜单相关代码
"""
from PySide6.QtCore import QPropertyAnimation, QPoint, QTimer, QEasingCurve, QRect, Qt, Signal, QThread, QObject
from PySide6.QtWidgets import QMenu, QMessageBox, QWidget, QMainWindow
from PySide6.QtGui import QScreen, QGuiApplication, QIcon, QAction
import os
import json
import asyncio
import aiohttp
import traceback
from typing import Optional, Dict, Any, TYPE_CHECKING, cast, Callable, Coroutine, Union
from qasync import QEventLoop, asyncSlot
import Lugwit_Module as LM
lprint = LM.lprint
import time

if TYPE_CHECKING:
    from clientend.pyqt_chatroom import MainWindow

class ActionWorker(QObject):
    """处理菜单动作的工作线程"""
    finished = Signal()  # 完成信号
    error = Signal(str)  # 错误信号

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def run(self):
        try:
            lprint(f"工作线程开始执行回调函数: {self.callback.__name__}")
            # 在新线程中执行回调
            self.callback()
            lprint(f"工作线程执行完成: {self.callback.__name__}")
            self.finished.emit()
        except Exception as e:
            lprint(f"工作线程执行失败: {str(e)}")
            lprint(traceback.format_exc())
            self.error.emit(str(e))

class HoverMenu(QMenu):
    """自定义菜单类"""
    
    # 定义信号
    message_received = Signal(dict)  # 收到新消息的信号
    login_status_changed = Signal(bool)  # 登录状态变化信号
    
    def __init__(self, parent: Optional['MainWindow'] = None):
        try:
            super().__init__(parent)
            self._parent_window = parent  # 保存父窗口引用
            
            # 消息相关
            self.unread_messages = {}  # 存储未读消息 {用户名: 消息数量}
            self.message_received.connect(self.handle_new_message)
            
            # 登录相关
            self.is_logged_in = False
            self.token = None
            self.username = None
            
            # 设置UI
            self.setup_menu_actions()  # 先设置菜单项
            self.setup_login_ui()      # 再设置登录UI
        except Exception as e:
            lprint(f"HoverMenu 初始化失败: {str(e)}")
            lprint(traceback.format_exc())
            raise
        
    def get_main_window(self) -> Optional['MainWindow']:
        """获取主窗口实例"""
        return self._parent_window
        
    def setup_login_ui(self):
        """设置登录相关UI"""
        try:
            # 用户信息按钮
            main_window = self.get_main_window()
            if main_window and hasattr(main_window, 'userName'):
                username = main_window.userName
                if username:
                    # 创建用户信息动作
                    self.user_action = QAction(QIcon(os.path.join(os.path.dirname(__file__), '..', '..', 'icons', 'user.svg')), 
                                          f"当前用户: {username}", self)
                    self.user_action.triggered.connect(self.show_user_info)
                    
                    # 将用户信息动作插入到菜单最顶部
                    actions = self.actions()
                    if actions:
                        self.insertAction(actions[0], self.user_action)
                    else:
                        self.addAction(self.user_action)
                    
                    # 添加分隔线
                    if actions:
                        self.insertSeparator(actions[0])
                    else:
                        self.addSeparator()
                        
        except Exception as e:
            lprint(f"设置登录UI失败: {str(e)}")
            lprint(traceback.format_exc())

    def show_user_info(self):
        """显示用户详情"""
        try:
            main_window = self.get_main_window()
            if main_window and hasattr(main_window, 'userName'):
                username = main_window.userName
                if username:
                    project_info = getattr(main_window, 'project_info', {})
                    if project_info:
                        info_text = f"用户名: {username}\n"
                        info_text += f"全名: {project_info.get('FullName', '')}\n"
                        info_text += f"邮箱: {project_info.get('Email', '')}\n"
                        info_text += f"用户组: {', '.join(group['name'] for group in project_info.get('userGroups', []))}\n"
                        info_text += f"自定义组: {', '.join(project_info.get('customGroups', []))}"
                        
                        QMessageBox.information(main_window, "用户信息", info_text)
        except Exception as e:
            lprint(f"显示用户信息失败: {str(e)}")
            lprint(traceback.format_exc())

    def setup_menu_actions(self):
        """设置菜单动作"""
        try:
            # 添加登录/登出按钮
            self.login_action = QAction(QIcon(os.path.join(os.path.dirname(__file__), '..', '..', 'icons', 'login.svg')), 
                                      "登录", self)
            self.login_action.triggered.connect(self.handle_login)
            self.addAction(self.login_action)

            # 添加分隔线
            self.addSeparator()

            # 添加"退出"动作
            self.exit_action = QAction(QIcon(os.path.join(os.path.dirname(__file__), '..', '..', 'icons', 'exit.svg')), 
                                "退出", self)
            if main_window := self.get_main_window():
                if hasattr(main_window, 'exit_application'):
                    lprint("设置退出按钮动作")
                    self.exit_action.triggered.connect(self.handle_exit_action)
            self.addAction(self.exit_action)
        except Exception as e:
            lprint(f"设置菜单动作失败: {str(e)}")
            lprint(traceback.format_exc())

    def handle_action_in_thread(self, action_name: str, callback: Callable):
        """在线程中处理动作"""
        try:
            lprint(f"开始处理{action_name}动作")
            # 创建工作线程
            thread = QThread()
            worker = ActionWorker(callback)
            
            # 将worker移动到线程中
            worker.moveToThread(thread)
            
            # 连接信号
            thread.started.connect(worker.run)
            worker.finished.connect(thread.quit)
            worker.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            worker.error.connect(lambda e: lprint(f"执行动作 {action_name} 失败: {e}"))
            
            # 启动线程前添加小延迟
            lprint(f"准备启动{action_name}线程")
            QTimer.singleShot(100, thread.start)
            
        except Exception as e:
            lprint(f"创建工作线程失败: {str(e)}")
            lprint(traceback.format_exc())

    def handle_new_message(self, message_data: dict):
        """处理新消息"""
        try:
            sender = message_data.get('sender_username')
            if sender:
                # 更新未读消息计数
                self.unread_messages[sender] = self.unread_messages.get(sender, 0) + 1
                # 更新菜单项显示
                self.update_menu_items()
                # 开始闪烁提醒
                main_window = self.get_main_window()
                if main_window and hasattr(main_window, 'start_blinking'):
                    main_window.start_blinking()
        except Exception as e:
            lprint(f"处理新消息错误: {str(e)}")
            lprint(traceback.format_exc())
            
    def update_menu_items(self):
        """更新菜单项显示"""
        try:
            for action in self.actions():
                if isinstance(action, QAction):
                    text = action.text()
                    # 检查是否是用户相关的菜单项
                    for sender, count in self.unread_messages.items():
                        if sender in text:
                            # 添加未读消息计数
                            new_text = f"{text} ({count})"
                            action.setText(new_text)
                            # 设置高亮样式
                            icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'icons', 'message.svg')
                            action.setIcon(QIcon(icon_path))
        except Exception as e:
            lprint(f"更新菜单项显示错误: {str(e)}")
            lprint(traceback.format_exc())
            
    def mark_messages_read(self, sender: str):
        """标记指定发送者的消息为已读"""
        try:
            if sender in self.unread_messages:
                del self.unread_messages[sender]
                self.update_menu_items()
                # 如果没有未读消息，停止闪烁
                main_window = self.get_main_window()
                if not self.unread_messages and main_window and hasattr(main_window, 'stop_blinking'):
                    main_window.stop_blinking()
        except Exception as e:
            lprint(f"标记消息已读错误: {str(e)}")
            lprint(traceback.format_exc())
            
    def showEvent(self, event):
        """显示菜单时的事件处理"""
        try:
            super().showEvent(event)
            # 使用QTimer添加一个很小的延迟
            QTimer.singleShot(10, self.update_menu_items)
        except Exception as e:
            lprint(f"菜单显示错误: {str(e)}")
            lprint(traceback.format_exc())

    def hideEvent(self, event):
        """隐藏事件处理"""
        try:
            super().hideEvent(event)
        except Exception as e:
            lprint(f"处理菜单隐藏事件失败: {str(e)}")
            lprint(traceback.format_exc())
            
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        try:
            action = self.actionAt(event.pos())
            if action:
                lprint(f"菜单项被点击: {action.text()}")
            super().mousePressEvent(event)
        except Exception as e:
            lprint(f"鼠标按下事件错误: {str(e)}")
            lprint(traceback.format_exc())
            
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        try:
            # 先调用父类的事件处理
            super().mouseReleaseEvent(event)
            
            # 获取点击的动作
            action = self.actionAt(event.pos())
            if action:
                lprint(f"处理菜单项点击: {action.text()}, 按键: {event.button()}")
                if action == self.exit_action and event.button() == Qt.MouseButton.LeftButton:
                    event.accept()
                    return
                
        except Exception as e:
            lprint(f"处理鼠标释放事件失败: {str(e)}")
            lprint(traceback.format_exc())
            
    @asyncSlot()
    async def handle_login(self):
        """处理登录/登出操作"""
        try:
            if not self.is_logged_in:
                # 获取用户名和密码
                main_window = self.get_main_window()
                if main_window and hasattr(main_window, 'userName'):
                    username = main_window.userName
                    password = "666"  # 固定密码
                    if username:
                        try:
                            success = await self.login(username, password)
                            if success:
                                lprint("登录成功")
                            else:
                                lprint("登录失败")
                        except Exception as e:
                            lprint(f"登录过程出错: {str(e)}")
                            lprint(traceback.format_exc())
            else:
                # 处理登出
                self.logout()
        except Exception as e:
            lprint(f"处理登录/登出操作失败: {str(e)}")
            lprint(traceback.format_exc())

    async def login(self, username: str, password: str) -> bool:
        """登录到服务器"""
        try:
            # 获取服务器地址
            server_ip = os.getenv('SERVER_IP', 'localhost')
            server_port = int(os.getenv('SERVER_PORT', '1026'))
            base_url = f'http://{server_ip}:{server_port}'
            
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('username', username)
                data.add_field('password', password)
                data.add_field('grant_type', 'password')
                data.add_field('scope', '')
                data.add_field('client_id', '')
                data.add_field('client_secret', '')
                
                headers = {
                    'Accept': 'application/json',
                }
                
                async with session.post(
                    f'{base_url}/api/auth/login',
                    data=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.token = result.get('access_token')
                        self.username = username
                        self.is_logged_in = True
                        self.update_login_status()
                        # 通知父窗口登录成功
                        main_window = self.get_main_window()
                        if main_window and hasattr(main_window, 'on_login_success'):
                            await main_window.on_login_success(self.token)
                        return True
                    else:
                        response_text = await response.text()
                        lprint(f"登录失败: {response_text}")
                        return False
        except Exception as e:
            lprint(f"登录过程出错: {str(e)}")
            lprint(traceback.format_exc())
            return False

    def logout(self):
        """登出"""
        try:
            self.is_logged_in = False
            self.token = None
            self.username = None
            self.update_login_status()
            # 通知父窗口登出
            main_window = self.get_main_window()
            if main_window and hasattr(main_window, 'on_logout'):
                main_window.on_logout()
        except Exception as e:
            lprint(f"登出过程出错: {str(e)}")
            lprint(traceback.format_exc())
            
    def update_login_status(self):
        """更新登录状态显示"""
        if self.is_logged_in:
            self.login_action.setText(f"登出 ({self.username})")
            self.login_action.setIcon(QIcon(os.path.join(os.path.dirname(__file__), '..', '..', 'icons', 'logout.svg')))
        else:
            self.login_action.setText("登录")
            self.login_action.setIcon(QIcon(os.path.join(os.path.dirname(__file__), '..', '..', 'icons', 'login.svg')))

    def handle_exit_action(self):
        """处理退出动作的确认对话框"""
        try:
            lprint("触发退出按钮")
            main_window = self.get_main_window()
            if main_window:
                reply = QMessageBox.question(
                    main_window,
                    "确认退出",
                    "确定要退出程序吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    lprint("用户确认退出")
                    self.handle_action_in_thread("退出", main_window.exit_application)
                else:
                    lprint("用户取消退出")
        except Exception as e:
            lprint(f"处理退出动作失败: {str(e)}")
            lprint(traceback.format_exc())

    def popup(self, pos):
        """重写popup方法来调整菜单位置"""
        try:
            # 获取菜单大小和屏幕信息
            menu_size = self.sizeHint()
            screen = QGuiApplication.screenAt(pos)
            if not screen:
                screen = QGuiApplication.primaryScreen()
            
            screen_geometry = screen.geometry()
            
            # 计算菜单位置，默认显示在鼠标位置
            x = pos.x()
            y = pos.y()
            
            # 如果菜单会超出屏幕右边，向左偏移
            if x + menu_size.width() > screen_geometry.right():
                x = x - menu_size.width()
            
            # 如果菜单会超出屏幕底部，向上偏移
            if y + menu_size.height() > screen_geometry.bottom():
                y = y - menu_size.height()
            
            # 确保不会超出屏幕左边和顶部
            x = max(screen_geometry.left(), x)
            y = max(screen_geometry.top(), y)
            
            # 调用父类的popup方法显示菜单
            super().popup(QPoint(x, y))
            
        except Exception as e:
            lprint(f"显示菜单错误: {str(e)}")
            lprint(traceback.format_exc())
            # 如果出错，使用默认位置显示
            super().popup(pos) 