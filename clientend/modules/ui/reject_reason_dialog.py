from typing import Optional
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QRadioButton, QButtonGroup, QLineEdit,
                             QPushButton, QLabel)
from PySide6.QtCore import Qt, Signal

from ..types.types import REJECT_REASONS, RejectResponse

class RejectReasonDialog(QDialog):
    """拒绝理由选择对话框"""
    
    reason_selected = Signal(RejectResponse)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("请选择拒绝理由")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 添加说明标签
        label = QLabel("请选择或输入拒绝远程控制的理由：")
        layout.addWidget(label)
        
        # 创建单选按钮组
        self.button_group = QButtonGroup(self)
        self.custom_input = None
        
        for i, reason in enumerate(REJECT_REASONS):
            radio = QRadioButton(reason)
            layout.addWidget(radio)
            self.button_group.addButton(radio, i)
            
            # 如果是"其他原因"选项，添加输入框
            if reason == "其他原因":
                self.custom_input = QLineEdit()
                self.custom_input.setPlaceholderText("请输入其他原因...")
                self.custom_input.setEnabled(False)
                layout.addWidget(self.custom_input)
                
        # 连接单选按钮信号
        self.button_group.buttonClicked.connect(self._on_button_clicked)
        
        # 添加确定和取消按钮
        button_layout = QHBoxLayout()
        
        confirm_button = QPushButton("确定")
        confirm_button.clicked.connect(self.accept)
        confirm_button.setStyleSheet(
            "QPushButton {"
            "background-color: #4CAF50; color: white; "
            "padding: 5px 15px; border-radius: 3px;}"
            "QPushButton:hover {background-color: #66BB6A;}"
        )
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet(
            "QPushButton {"
            "background-color: #F44336; color: white; "
            "padding: 5px 15px; border-radius: 3px;}"
            "QPushButton:hover {background-color: #EF5350;}"
        )
        
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2A2D3E;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QRadioButton {
                color: white;
                font-size: 13px;
                padding: 5px;
            }
            QRadioButton::indicator {
                width: 15px;
                height: 15px;
            }
            QRadioButton::indicator:checked {
                background-color: #4CAF50;
                border: 2px solid white;
                border-radius: 7px;
            }
            QRadioButton::indicator:unchecked {
                background-color: #424242;
                border: 2px solid #757575;
                border-radius: 7px;
            }
            QLineEdit {
                background-color: #424242;
                color: white;
                border: 1px solid #757575;
                border-radius: 3px;
                padding: 5px;
            }
            QLineEdit:disabled {
                background-color: #363636;
                color: #757575;
            }
        """)
    
    def _on_button_clicked(self, button):
        """单选按钮点击事件处理"""
        if self.custom_input:
            self.custom_input.setEnabled(button.text() == "其他原因")
    
    def get_reason(self) -> Optional[RejectResponse]:
        """获取选择的拒绝理由
        
        Returns:
            Optional[RejectResponse]: 拒绝理由响应对象，如果取消则返回None
        """
        if self.exec() == QDialog.DialogCode.Accepted:
            selected_button = self.button_group.checkedButton()
            if selected_button:
                if selected_button.text() == "其他原因" and self.custom_input:
                    custom_reason = self.custom_input.text().strip()
                    if custom_reason:
                        return RejectResponse(reason=custom_reason, is_custom=True)
                    return None
                return RejectResponse(reason=selected_button.text())
        return None 