"""
菜单相关代码
"""
from PySide6.QtCore import QPropertyAnimation, QPoint, QTimer, QEasingCurve, QRect, Qt, Signal, QThread, QObject
from PySide6.QtWidgets import QMenu, QMessageBox, QWidget, QMainWindow, QLabel, QInputDialog, QLineEdit, QStyle
from PySide6.QtGui import QIcon, QAction, QCursor, QGuiApplication, QScreen
import os
import re
import json
import asyncio
import aiohttp
import traceback
from typing import Optional, Dict, Any, TYPE_CHECKING, cast, Callable, Coroutine, Union
from qasync import QEventLoop, asyncSlot
import Lugwit_Module as LM
lprint = LM.lprint
import time
import yaml
import subprocess
from functools import partial
from datetime import datetime
from zoneinfo import ZoneInfo

from ..vnc.vnc_connector import vnc_connector  # VNC连接器
from ..vnc.vnc_installer import install_vnc  # VNC安装器
from ..handlers.chat_handler import ChatHandler  # 改为新的类名
from ..types.types import ConnectionState  # 导入ConnectionState类型

if TYPE_CHECKING:
    from clientend.pyqt_chatroom import MainWindow

clientDir_match = re.search('.+/clientend',__file__.replace(os.sep, '/'))
if clientDir_match:
    clientDir = clientDir_match.group()
else:
    clientDir = ''
iconDir = os.path.join(clientDir, 'icons')

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
            traceback.print_exc()
            self.error.emit(str(e))

class HoverMenu(QMenu):
    """自定义菜单类"""
    
    # 定义信号
    message_received = Signal(dict)  # 收到新消息的信号
    
    def __init__(self, parent: Optional['MainWindow'] = None):
        super().__init__(parent)
        self._parent_window = parent  # 保存父窗口引用
        self.chat_handler = ChatHandler.get_instance()  # 使用新的类名
        
        # 消息相关
        self.unread_messages = {}  # 存储未读消息 {用户名: 消息数量}
        self.message_received.connect(self.handle_new_message)
        
        # 设置UI
        self.init_login_ui()      # 先设置登录UI
        self.setup_menu_actions()  # 再设置菜单项
        
        # 样式已移到 dark_theme.qss，这里不需要重复定义
        
    def get_main_window(self) -> Optional['MainWindow']:
        """获取主窗口实例"""
        return self._parent_window
        
    def init_login_ui(self):
        """设置登录相关UI"""
        try:
            # 用户信息按钮
            main_window = self.get_main_window()
            if main_window and hasattr(main_window, 'userName'):
                username = main_window.userName
                lprint(f"用户名: {username}")
                if username:
                    # 创建用户信息动作
                    user_icon_path=iconDir+'/user.svg'
                    self.user_action = QAction(QIcon(user_icon_path), 
                                        f"等待连接 {main_window.nickname}", self)  
                    
                    # 设置工具提示
                    project_info = getattr(main_window, 'project_info', {})
                    if project_info:
                        tooltip_text = "<html><body style='white-space:pre;'>"
                        tooltip_text += "<table style='border-spacing: 5px;'>"
                        tooltip_text += f"<tr><td><b>用户名:</b></td><td style='padding-left:10px'>{username}</td></tr>"
                        tooltip_text += f"<tr><td><b>全名:</b></td><td style='padding-left:10px'>{project_info.get('FullName', '')}</td></tr>"
                        tooltip_text += f"<tr><td><b>邮箱:</b></td><td style='padding-left:10px'>{project_info.get('Email', '')}</td></tr>"
                        tooltip_text += f"<tr><td><b>用户组:</b></td><td style='padding-left:10px'>{', '.join(group['name'] for group in project_info.get('userGroups', []))}</td></tr>"
                        tooltip_text += f"<tr><td><b>自定义组:</b></td><td style='padding-left:10px'>{', '.join(project_info.get('customGroups', []))}</td></tr>"
                        # 添加设备ID信息
                        device_id = project_info.get('device_id', '待获取')
                        if device_id:
                            tooltip_text += f"<tr><td><b>设备ID:</b></td><td style='padding-left:10px'>{device_id}</td></tr>"
                        tooltip_text += "</table>"
                        tooltip_text += "</body></html>"
                        self.user_action.setToolTip(tooltip_text)
                        # 设置工具提示显示时间（默认是5000毫秒）
                        self.setToolTipsVisible(True)
                        self.setToolTipDuration(10000)  # 设置为10秒
                    
                    self.user_action.triggered.connect(self.show_user_info)

                    self.addAction(self.user_action)
                    
                    self.addSeparator()
                        
        except Exception as e:
            lprint(f"设置登录UI失败: {str(e)}")
            traceback.print_exc()

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
            traceback.print_exc()

    def check_remote_control_permission(self, action_type: str = 'request') -> bool:
        """检查是否有远程控制权限
        
        Args:
            action_type: 控制类型,'request'表示请求对方控制,'control'表示主动控制对方
            
        Returns:
            bool: 是否有权限
        """
        try:
            # 如果是请求对方控制,直接返回True
            if action_type == 'accept':
                return True
                
            # 以下是主动请求控制的权限验证
            main_window = self.get_main_window()
            if not main_window or not hasattr(main_window, 'project_info'):
                return False
                
            project_info = main_window.project_info
            if not isinstance(project_info, dict):
                return False
                
            # 检查用户组
            user_groups = project_info.get('userGroups', [])
            lprint(user_groups)
            for group in user_groups:
                if isinstance(group, dict) and group.get('name') == 'TD':
                    return True
                    
            # 如果不在TD组,弹出密码输入对话框
            password, ok = QInputDialog.getText(
                self,
                "远程控制验证",
                "请输入远程控制密码:",
                QLineEdit.EchoMode.Password
            )
            
            if ok and password == "fqq":
                return True
                
            return False
            
        except Exception as e:
            lprint(f"检查远程控制权限失败: {str(e)}")
            traceback.print_exc()
            return False

    def setup_menu_actions(self):
        # NOTE """设置菜单动作"""
        try:
            # 添加设备ID和会话ID菜单项
            main_window = self.get_main_window()
            if main_window and hasattr(main_window, 'project_info'):
                project_info = main_window.project_info
                if isinstance(project_info, dict):
                    # 添加设备ID菜单项
                    device_id = project_info.get('device_id', '待获取')
                    self.device_id_action = QAction(self.style().standardIcon(QStyle.SP_ComputerIcon), 
                                             f"设备ID: {device_id}", self)
                    self.device_id_action.setEnabled(False)  # 设置为不可点击
                    self.addAction(self.device_id_action)
                    
                    # 添加会话ID菜单项
                    sid = self.chat_handler.get_sid() or "未连接"
                    self.session_id_action = QAction(self.style().standardIcon(QStyle.SP_DialogYesButton), 
                                             f"会话ID: {sid}", self)
                    self.session_id_action.setEnabled(False)  # 设置为不可点击
                    self.addAction(self.session_id_action)
                    
                    # 添加连接时间菜单项
                    conn_status = self.chat_handler.get_connection_status()
                    last_heartbeat_time = conn_status.get("connection_time")  # 使用连接时间而不是心跳时间
                    conn_time_str = "未连接"
                    if last_heartbeat_time:
                        conn_time = datetime.fromtimestamp(last_heartbeat_time, ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
                        conn_time_str = conn_time
                    
                    # 创建连接时间子菜单
                    self.connection_time_menu = QMenu(f"连接时间: {conn_time_str}", self)
                    self.connection_time_menu.setIcon(self.style().standardIcon(QStyle.SP_DialogYesButton))
                    
                    # 添加连接日志记录
                    logs = self.chat_handler.get_connection_logs()
                    if logs:
                        for log in logs:
                            log_action = QAction(log, self.connection_time_menu)
                            log_action.setEnabled(False)  # 设置为不可点击
                            self.connection_time_menu.addAction(log_action)
                    else:
                        no_log_action = QAction("暂无连接记录", self.connection_time_menu)
                        no_log_action.setEnabled(False)
                        self.connection_time_menu.addAction(no_log_action)
                    
                    # 将连接时间子菜单添加到主菜单
                    self.addMenu(self.connection_time_menu)
                    
                    # 添加分隔线
                    self.addSeparator()
            
            # 创建控制子菜单
            self.control_menu = QMenu("主动控制", self)
            self.control_menu.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
            self.addMenu(self.control_menu)
            
            # 从yaml配置文件读取远程控制选项
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'remote_control.yaml')
            try:
                lprint(f"读取远程控制配置: {config_path}")
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    for option in config['remote_control_options']:
                        try:
                            lprint(f"添加远程控制选项: {option['label']}")
                            action = QAction(self.style().standardIcon(QStyle.SP_ComputerIcon), 
                                        option['label'], self)
                            # 邀请控制列表
                            if option['action'] == 'request':
                                action.triggered.connect(lambda checked=False, opt=option: asyncio.create_task(self.handle_request(opt)))
                                self.addAction(action)
                            elif option['action'] == 'connect':
                                action.triggered.connect(
                                    lambda checked, host=option['host'], port=option['port'], 
                                       password=option['password']: self.connect_vnc(host, port, password, 'request')
                                )
                                self.control_menu.addAction(action)
                            lprint(f"远程控制选项 {option['label']} 添加成功")
                        except Exception as e:
                            lprint(f"添加远程控制选项 {option.get('label', '未知')} 失败: {str(e)}")
                            traceback.print_exc()
                lprint("远程控制选项添加完成")
            except Exception as e:
                lprint(f"加载远程控制配置失败: {str(e)}")
                traceback.print_exc()

            # 添加分隔线
            self.addSeparator()

            # 添加显示/隐藏按钮
            self.show_action = QAction(QIcon(os.path.join(iconDir, 'show.svg')), 
                                     "显示", self)
            self.show_action.triggered.connect(self.show_window)
            self.addAction(self.show_action)

            self.hide_action = QAction(QIcon(os.path.join(iconDir, 'hide.svg')), 
                                     "隐藏", self)
            self.hide_action.triggered.connect(self.hide_window)
            self.addAction(self.hide_action)
            
            # 添加登录/登出按钮
            self.login_action = QAction(QIcon(os.path.join(iconDir, 'login.svg')), 
                                      "登录/重新登录", self)
            self.login_action.triggered.connect(self.handle_login)
            self.addAction(self.login_action)
            
            # 添加重启按钮
            self.restart_action = QAction(QIcon(os.path.join(iconDir, 'restart.svg')), 
                                        "重启", self)
            self.restart_action.triggered.connect(self.restart_application)
            self.addAction(self.restart_action)

            # 添加分隔线
            self.addSeparator()

            # 添加"退出"动作
            self.exit_action = QAction(QIcon(os.path.join(iconDir, 'exit.svg')), 
                                "退出", self)
            if main_window := self.get_main_window():
                if hasattr(main_window, 'exit_application'):
                    lprint("设置退出按钮动作")
                    self.exit_action.triggered.connect(self.handle_exit_action)
            self.addAction(self.exit_action)
            self.addAction(QAction("", self))
        except Exception as e:
            lprint(f"设置菜单动作失败: {str(e)}")
            traceback.print_exc()

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
            traceback.print_exc()

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
            traceback.print_exc()
            
    def update_menu_items(self):
        #TODO 这个设置是有问题的, 加入代办事项
        return
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
                            icon_path = os.path.join(iconDir, 'message.svg')
                            action.setIcon(QIcon(icon_path))
        except Exception as e:
            lprint(f"更新菜单项显示错误: {str(e)}")
            traceback.print_exc()
            
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
            traceback.print_exc()
            
    def showEvent(self, event):
        """菜单显示时更新状态标签位置"""
        try:
            super().showEvent(event)
            
            # 更新用户状态
            if self._parent_window and hasattr(self._parent_window, 'chat_handler'):
                is_connected = self._parent_window.chat_handler.is_connected
                self.update_login_status(is_connected)
            
            # 确保会话ID是最新的
            if hasattr(self, 'session_id_action') and self.chat_handler:
                sid = self.chat_handler.get_sid() or "未连接"
                self.session_id_action.setText(f"会话ID: {sid}")
                
            # 确保设备ID是最新的
            if hasattr(self, 'device_id_action') and self.chat_handler:
                device_id = self.chat_handler.get_device_id() or "未连接"
                self.device_id_action.setText(f"设备ID: {device_id}")
                
            # 更新连接时间菜单
            if hasattr(self, 'connection_time_menu') and self.chat_handler:
                self.update_connection_time_menu()
                
        except Exception as e:
            lprint(f"显示菜单事件处理失败: {str(e)}")
            traceback.print_exc()

    def hideEvent(self, event):
        """菜单隐藏时隐藏状态标签"""
        try:
            super().hideEvent(event)
        except Exception as e:
            lprint(f"隐藏菜单事件处理失败: {str(e)}")
            traceback.print_exc()
            
            
    @asyncSlot()
    async def handle_login(self):
        """处理登录/登出操作"""
        try:
            main_window = self.get_main_window()
            if main_window:
                await main_window.handle_login()
        except Exception as e:
            lprint(f"处理登录/登出操作失败: {str(e)}")
            traceback.print_exc()

    def update_login_status(self, is_connected: bool):
        """更新用户状态显示"""
        try:
            if hasattr(self, 'user_action'):
                if is_connected:
                    self.user_action.setText(f"{self._parent_window.nickname}   已连接")
                    self.update_tooltip()  # 更新工具提示
                else:
                    self.user_action.setText("等待连接")
                    
            # 更新会话ID菜单项
            if hasattr(self, 'session_id_action'):
                sid = self.chat_handler.get_sid() or "未连接"
                self.session_id_action.setText(f"会话ID: {sid}")
                
            # 更新设备ID菜单项
            if hasattr(self, 'device_id_action'):
                device_id = self.chat_handler.get_device_id() or "未连接"
                self.device_id_action.setText(f"设备ID: {device_id}")
                
            # 更新连接时间菜单
            if hasattr(self, 'connection_time_menu'):
                self.update_connection_time_menu()
                
        except Exception as e:
            lprint(f"更新登录状态失败: {str(e)}")
            traceback.print_exc()

    def update_tooltip(self):
        """更新工具提示"""
        try:
            main_window = self.get_main_window()
            if main_window and hasattr(main_window, 'userName'):
                username = main_window.userName
                if username and hasattr(self, 'user_action'):
                    project_info = getattr(main_window, 'project_info', {})
                    if project_info:
                        tooltip_text = "<html><body style='white-space:pre;'>"
                        tooltip_text += "<table style='border-spacing: 5px;'>"
                        tooltip_text += f"<tr><td><b>用户名:</b></td><td style='padding-left:10px'>{username}</td></tr>"
                        tooltip_text += f"<tr><td><b>全名:</b></td><td style='padding-left:10px'>{project_info.get('FullName', '')}</td></tr>"
                        tooltip_text += f"<tr><td><b>邮箱:</b></td><td style='padding-left:10px'>{project_info.get('Email', '')}</td></tr>"
                        tooltip_text += f"<tr><td><b>用户组:</b></td><td style='padding-left:10px'>{', '.join(group['name'] for group in project_info.get('userGroups', []))}</td></tr>"
                        tooltip_text += f"<tr><td><b>自定义组:</b></td><td style='padding-left:10px'>{', '.join(project_info.get('customGroups', []))}</td></tr>"
                        # 添加设备ID信息
                        device_id = self.chat_handler.get_device_id() or "未连接"
                        if device_id:
                            tooltip_text += f"<tr><td><b>设备ID:</b></td><td style='padding-left:10px'>{device_id}</td></tr>"
                        
                        # 添加会话ID和连接时间信息
                        if self.chat_handler:
                            # 获取会话ID
                            sid = self.chat_handler.get_sid() or "未连接"
                            tooltip_text += f"<tr><td><b>会话ID:</b></td><td style='padding-left:10px'>{sid}</td></tr>"
                            
                            # 获取连接状态信息
                            conn_status: ConnectionState = self.chat_handler.get_connection_status()
                            last_heartbeat_time = conn_status.get("connection_time")  # 使用连接时间而不是心跳时间
                            if last_heartbeat_time:
                                # 格式化连接时间
                                conn_time = datetime.fromtimestamp(last_heartbeat_time, ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
                                tooltip_text += f"<tr><td><b>连接时间:</b></td><td style='padding-left:10px'>{conn_time}</td></tr>"
                        
                        tooltip_text += "</table>"
                        tooltip_text += "</body></html>"
                        self.user_action.setToolTip(tooltip_text)
        except Exception as e:
            lprint(f"更新工具提示失败: {str(e)}")
            traceback.print_exc()

    def update_connection_time_menu(self):
        """更新连接时间菜单"""
        try:
            if hasattr(self, 'connection_time_menu') and self.chat_handler:
                # 获取连接状态信息
                conn_status: ConnectionState = self.chat_handler.get_connection_status()
                last_heartbeat_time = conn_status.get("connection_time")  # 使用连接时间而不是心跳时间
                conn_time_str = "未连接"
                if last_heartbeat_time:
                    conn_time = datetime.fromtimestamp(last_heartbeat_time, ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
                    conn_time_str = conn_time
                
                # 更新连接时间菜单标题
                self.connection_time_menu.setTitle(f"连接时间: {conn_time_str}")
                
                # 清除原有菜单项
                self.connection_time_menu.clear()
                
                # 添加连接日志记录
                logs = self.chat_handler.get_connection_logs()
                if logs:
                    for log in logs:
                        log_action = QAction(log, self.connection_time_menu)
                        log_action.setEnabled(False)  # 设置为不可点击
                        self.connection_time_menu.addAction(log_action)
                else:
                    no_log_action = QAction("暂无连接记录", self.connection_time_menu)
                    no_log_action.setEnabled(False)
                    self.connection_time_menu.addAction(no_log_action)
        except Exception as e:
            lprint(f"更新连接时间菜单失败: {str(e)}")
            traceback.print_exc()

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
            traceback.print_exc()
            # 如果出错，使用默认位置显示
            super().popup(pos) 

    def show_window(self):
        """显示主窗口"""
        main_window = self.get_main_window()
        if main_window:
            if not main_window.isVisible():
                main_window.showNormal()
                main_window.activateWindow()

    def hide_window(self):
        """隐藏主窗口"""
        main_window = self.get_main_window()
        if main_window:
            main_window.hide()

    def restart_application(self):
        """重启应用程序"""
        main_window = self.get_main_window()
        if main_window:
            main_window.restart_application()

    def connect_vnc(self, host: str, port: int, password: str, action_type: str = 'request') -> None:
        """连接VNC服务器
        
        Args:
            host: 主机地址
            port: 端口号
            password: 密码
        """
        try:
            # 检查权限,传入action_type='request'表示主动请求控制
            if not self.check_remote_control_permission(action_type):
                QMessageBox.warning(
                    self,
                    "权限不足",
                    "您没有远程控制权限,请联系管理员或输入正确的密码。",
                    QMessageBox.StandardButton.Ok,
                    QMessageBox.StandardButton.Ok
                )
                return
            
            # 使用vnc_connector模块连接
            if vnc_connector.connect(host):
                lprint(f"VNC连接成功: {host}:{port}")
            else:
                QMessageBox.warning(
                    self,
                    "连接失败",
                    "无法连接到VNC服务器，请检查服务器是否在线",
                    QMessageBox.StandardButton.Ok,
                    QMessageBox.StandardButton.Ok
                )
                
        except Exception as e:
            lprint(f"连接VNC服务器失败: {str(e)}")
            traceback.print_exc()
            QMessageBox.warning(
                self,
                "连接失败",
                f"连接VNC服务器时发生错误: {str(e)}",
                QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Ok
            )


    def handle_exit_action(self):
        """处理退出动作的确认对话框"""
        try:
            lprint("触发退出按钮")
            main_window = self.get_main_window()
            if main_window:
                msg_box = QMessageBox(main_window)
                msg_box.setWindowTitle("确认退出")
                msg_box.setText("确定要退出程序吗？")
                msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                msg_box.setDefaultButton(QMessageBox.StandardButton.No)
                
                reply = msg_box.exec()
                if reply == QMessageBox.StandardButton.Yes:
                    import multiprocessing
                    for process in multiprocessing.active_children():
                        process.terminate()  # 终止所有子进程
                    self.handle_action_in_thread("退出", main_window.exit_application)
                else:
                    lprint("用户取消退出")
        except Exception as e:
            lprint(f"处理退出动作失败: {str(e)}")
            traceback.print_exc()

    async def handle_request(self, option):
        """处理远程控制请求"""
        await self.chat_handler._send_remote_control_message(option) 