"""
菜单相关代码
"""
from PySide6.QtCore import QPropertyAnimation, QPoint, QTimer, QEasingCurve
from PySide6.QtWidgets import QMenu

class HoverMenu(QMenu):
    """自定义菜单类，用于处理鼠标离开事件"""
    
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