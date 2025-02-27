from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QPainterPath
import Lugwit_Module as LM
import traceback
import os
lprint = LM.lprint

class WaitingResponseWindow(QDialog):
    """等待远程控制响应的窗口"""
    
    # 定义信号
    response_received = Signal(dict)  # 收到响应的信号
    
    def __init__(self, target_user: str, parent=None):
        super().__init__(parent)
        self.target_user = target_user
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建容器widget
        self.container = QWidget(self)
        self.container.setObjectName("container")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        
        # 等待提示
        self.status_label = QLabel(f"正在等待 {self.target_user} 的响应...\n剩余时间: 60秒")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.status_label)

        # 服务器响应标签
        self.reponseLableFromServer = QLabel("", self.container)
        self.reponseLableFromServer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.reponseLableFromServer)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # 设置为0表示无限循环
        container_layout.addWidget(self.progress_bar)
        
        # 按钮容器
        button_layout = QHBoxLayout()
        
        # 重新发起按钮
        self.retry_button = QPushButton("重新发起")
        self.retry_button.setObjectName("retry_button")  # 设置对象名以便应用样式
        self.retry_button.clicked.connect(self._handle_retry)
        button_layout.addWidget(self.retry_button)
        
        # 关闭按钮
        self.close_button = QPushButton("关闭")
        self.close_button.setObjectName("close_button")  # 设置对象名以便应用样式
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        # 添加按钮布局
        container_layout.addLayout(button_layout)
        
        # 将容器添加到主布局
        main_layout.addWidget(self.container)
        
        # 加载样式表
        style_path = os.path.join(os.path.dirname(__file__), "styles", "waiting_response.qss")
        with open(style_path, "r", encoding="utf-8") as f:
            self.container.setStyleSheet(f.read())
        
        # 初始化定时器
        self.countdown = 60
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._update_countdown)
        self.countdown_timer.start(1000)
        
        self.timeout_timer = QTimer(self)
        self.timeout_timer.timeout.connect(self._on_timeout)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.start(60000)
        
        # 初始化时禁用重新发起按钮
        self.retry_button.setEnabled(False)
        
        # 设置窗口大小
        self.resize(300, 200)

    def paintEvent(self, event):
        """重写绘制事件以实现圆角和阴影效果"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制阴影
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(10):
            opacity = (10 - i) / 40
            painter.setBrush(QColor(0, 0, 0, int(opacity * 255)))
            painter.drawRoundedRect(self.rect().adjusted(i, i, -i, -i), 10, 10)

    def _update_countdown(self):
        """更新倒计时"""
        self.countdown -= 1
        self.status_label.setText(f"正在等待 {self.target_user} 的响应...\n剩余时间: {self.countdown}秒")

        self.progress_bar.setValue(self.countdown)
        
        if self.countdown <= 0:
            self.countdown_timer.stop()
            self._on_timeout()
        
    def _on_timeout(self):
        """超时处理"""
        lprint("等待响应超时")
        self.status_label.setText(f"{self.target_user} 未响应")
        self.reponseLableFromServer.setText("连接超时")
        
        # 超时后启用重新发起按钮
        self.retry_button.setEnabled(True)
        
    def handle_response(self, response: dict):
        """处理收到的响应"""
        self.timeout_timer.stop()
        
        if response.get('status') == 'rejected':
            reason = response.get('reason', '未提供原因')
            self.status_label.setText(f"请求被拒绝\n原因: {reason}")
            self.reponseLableFromServer.setText(reason)
        else:
            self.status_label.setText("请求已接受")
            # 立即关闭窗口
            self.close()
            
        # 发送响应信号
        self.response_received.emit(response)
        
    def closeEvent(self, event):
        """关闭事件处理"""
        self.timeout_timer.stop()
        self.countdown_timer.stop()  # 停止倒计时
        super().closeEvent(event)
        
    def _handle_retry(self):
        """处理重新发起按钮点击"""
        try:
            # 重置倒计时
            self.countdown = 60
            self.progress_bar.setValue(60)
            self.status_label.setText(f"正在等待 {self.target_user} 的响应...\n剩余时间: 60秒")
            
            # 重启定时器
            self.countdown_timer.start()
            self.timeout_timer.start()
            
            # 禁用重新发起按钮
            self.retry_button.setEnabled(False)
            
            # 发送重试信号
            self.response_received.emit({"status": "retry"})
            
        except Exception as e:
            lprint(f"重新发起请求失败: {str(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 设置应用程序级别的样式
    app.setStyle("Fusion")
    
    # 创建测试窗口
    window = WaitingResponseWindow("测试用户")
    window.show()
    
    # 模拟3秒后收到响应
    def simulate_response():
        window.handle_response({
            'status': 'rejected',
            'reason': '测试拒绝原因'
        })
    QTimer.singleShot(3000, simulate_response)
    
    # 模拟6秒后接受请求
    def simulate_accept():
        window.handle_response({
            'status': 'accepted'
        })
    QTimer.singleShot(6000, simulate_accept)
    
    sys.exit(app.exec()) 