from datetime import datetime
import os
import sys
import socket

# 根据主机名选择Qt后端
hostname = socket.gethostname()
os.environ['QT_API'] = 'pyqt6' if hostname == 'OC5' else 'pyside6'

from qtpy.QtWidgets import (QApplication, QLabel, QPushButton, 
                               QVBoxLayout, QHBoxLayout, QWidget, QTextBrowser)
from qtpy.QtGui import QPixmap, QPainter, QPainterPath
from qtpy.QtCore import Qt, QPoint
import Lugwit_Module as LM
print("-------------",os.path.abspath('./'))
sys.path.append(os.path.abspath('./'))
from backend import schemas

lprint = LM.lprint

def get_rounded_pixmap(image_path, width, height, radius):
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

import markdown

def create_markdown_view(markdown_text):
    # 将 Markdown 转换为 HTML
    html = markdown.markdown(markdown_text)
    
    # 创建 QTextBrowser
    text_browser = QTextBrowser()
    text_browser.setAlignment(Qt.AlignmentFlag.AlignCenter)
    text_browser.setStyleSheet(
        "color: white; font-size: 14px; font-family: Arial; border: none; background: transparent;"
    )
    
    # 设置 HTML 内容
    text_browser.setHtml(html)
    return text_browser



def create_notification_window(image_path, message: schemas.MessageBase, result,on_close=None):
    # 创建主窗口
    class NotificationWindow(QWidget):
        def __init__(self, message, result,on_close=None):
            super().__init__()
            self.on_close = on_close
            self.result=result
            self.markdown_view = None
            # 设置窗口样式
            self.setWindowFlags(
                Qt.WindowType.Tool | 
                Qt.WindowType.FramelessWindowHint | 
                Qt.WindowType.WindowStaysOnTopHint
            )
            self.setStyleSheet("background-color: #2A2D3E; border: 1px solid #3C404F; border-radius: 10px;")
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.resize(560, 400)  # 调整窗口大小为 360x220
            self.message=message
            # 创建布局
            self.main_layout = QVBoxLayout()
            self.main_layout.setSpacing(0)
            if self.message.message_type=="validation":
                self.abc_check_toast()
            elif self.message.message_type=="remote_control":
                self.remote_control_toast()
            else:
                self.normal_toast()
            self.markdown_view.setStyleSheet("background-color: #2A2D3E;color: white;border: 1px solid #a28135;border-radius: 15px;padding:15px")

            # 创建按钮
            button_accept = QPushButton("接受")
            button_accept.clicked.connect(self.on_accept_clicked)
            button_accept.setStyleSheet(
                "QPushButton {"
                "background-color: #4CAF50; color: white; font-size: 12px; font-family: Arial; padding: 5px 10px;"
                "border-radius: 5px;"
                "}"
                "QPushButton:hover {"
                "background-color: #66BB6A;"
                "}"
            )

            button_open = QPushButton("打开")
            button_open.clicked.connect(self.on_open_clicked)
            button_open.setStyleSheet(
                "QPushButton {"
                "background-color: #2196F3; color: white; font-size: 12px; font-family: Arial; padding: 5px 10px;"
                "border-radius: 5px;"
                "}"
                "QPushButton:hover {"
                "background-color: #42A5F5;"
                "}"
            )

            button_close = QPushButton("关闭")
            button_close.clicked.connect(self.on_close_clicked)
            button_close.setStyleSheet(
                "QPushButton {"
                "background-color: red; color: white; font-size: 12px; font-family: Arial; padding: 5px 10px;"
                "border-radius: 5px;"
                "}"
                "QPushButton:hover {"
                "background-color: #FF6666;"
                "}"
            )
            self.setStyleSheet("QPushButton {height: 30px;}")
            button_layout = QHBoxLayout()
            button_layout.addWidget(button_accept)
            button_layout.addWidget(button_open)
            button_layout.addWidget(button_close)
            self.main_layout.addLayout(button_layout)

            # 设置主布局
            self.setLayout(self.main_layout)

            # 设置窗口位置到右下角
            screen_geometry = QApplication.primaryScreen().availableGeometry()
            x = screen_geometry.width() - self.width() - 20
            y = screen_geometry.height() - self.height() - 20
            self.move(x, y)

        def on_accept_clicked(self):
            print("接受按钮被点击了！")
            self.result='accept'
            self.close()

        def on_open_clicked(self):
            print("打开按钮被点击了！")
            self.result='open'
            self.close()

        def on_close_clicked(self):
            if LM.is_main():
                print("主程序退出")
                os._exit(0)
            else:
                print("关闭窗口！")
                self.close()

        def closeEvent(self, event):
            if self.on_close:
                self.on_close()
            super().closeEvent(event)

        def normal_toast(self,):
            self.setFixedHeight(300)
            markdown_text=(
                "# 通知消息\n"+
                f"## 发送人:{self.message.sender}\n"+
                f"{self.message.content}"
            )
            lprint(markdown_text)
            self.markdown_view = create_markdown_view(markdown_text)

            self.main_layout.addWidget(self.markdown_view)

        def remote_control_toast(self,):
            self.setFixedHeight(300)
            markdown_text=(
                "# 通知消息\n"+
                f"## 远程控制邀请\n\n"+
                f"## 发  送   人:  {self.message.sender}\n"
            )
            lprint(markdown_text)
            self.markdown_view = create_markdown_view(markdown_text)

            self.main_layout.addWidget(self.markdown_view)

        def abc_check_toast(self,):
            # 创建图片
            if image_path:
                rounded_pixmap = get_rounded_pixmap(image_path, 560, 130, 15)  # 20为圆角半径
                pixmap_label = QLabel()
                pixmap_label.setFixedSize(560, 130)
                pixmap_label.setPixmap(rounded_pixmap)
                pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.main_layout.addWidget(pixmap_label)
                pixmap_label.setStyleSheet("background: transparent;border: 1px solid #a28135;border-radius: 15px;")

                markdown_text=(
                    "# Abc检查反馈\n"+
                    f"## 制作人:{message.recipient}\n"+
                    f"### 审核数据:\n{message.content['url'] if isinstance(message.content, dict) else message.content}"
                )
                self.markdown_view = create_markdown_view(markdown_text)
                self.main_layout.addWidget(self.markdown_view)

    return NotificationWindow(message, result,on_close=on_close)

def main(message, result="",on_close=None):
    # 创建通知窗口
    lprint(message)
    image_path = f'{LM.LugwitLibDir}/ChatRoom/backend/routers/check_file/static/alembic.png'  # 替换为实际的图片路径
    
    notification_window = create_notification_window(image_path, message, 
                                                    result=result,
                                                    on_close=on_close,)
    notification_window.show()
    return notification_window


if __name__ == "__main__":
    app = QApplication(sys.argv)
    server_ip = os.environ['SERVER_IP']
    # 创建通知窗口
    image_path = f'{LM.LugwitLibDir}/ChatRoom/backend/routers/check_file/static/alembic.png'  # 替换为实际的图片路径
    message={
        "sender": "system01",                # 发送者用户名
        "recipient": "fengqingqing",         # 接收者用户名()
        "content": {'check_type':'cfx_abc_check',
                    'url':f'http://{server_ip}:1026/check_file/abc_check_show/ZTS/06.CFX/EP001/ep001_sc001_shot0010/ep001_sc001_shot0010_check.json',  # 消息内容
                    'check_data_file':'/ZTS/06.CFX/EP001/ep001_sc001_shot0010/ep001_sc001_shot0010_check.json'},  # 消息内容
        "timestamp": datetime.now().isoformat(),  # 时间戳
        "recipient_type": "user",            # 接收者类型
        "status": ["pending"],               # 消息状态
        "direction": "request",              # 消息方向
        "message_content_type": "html",       # 消息内容类型
        "message_type":'validation',
        "popup_message":True,
    }
    result={}
    message=schemas.MessageBase(**message)
    notification_window = create_notification_window(image_path, message,result)
    notification_window.show()

    sys.exit(app.exec())
