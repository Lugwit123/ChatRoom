import sys
import os
import asyncio
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import Lugwit_Module as LM

from ..types.types import MessageBase, ButtonConfig, RejectResponse
from .notice_win import create_notification_window
from .reject_reason_dialog import RejectReasonDialog

lprint = LM.lprint

async def simulate_remote_control_request():
    """模拟接收到远程控制请求"""
    # 创建测试消息
    message = MessageBase(
        sender="test_user",
        recipient="current_user",
        content="用户 test_user 请求远程控制\nIP: 192.168.1.100",
        message_type="remote_control",
        popup_message=True
    )
    
    # 自定义按钮配置
    button_config: ButtonConfig = {
        'accept': '接受控制',
        'close': '拒绝'
    }
    
    # 创建通知窗口
    notification_window = create_notification_window(
        image_path=None,
        message=message,
        result="",
        button_config=button_config
    )
    
    # 模拟结果处理
    async def handle_result(result: str):
        if result == 'accept':
            lprint("用户接受了远程控制请求")
            lprint("模拟连接VNC: IP=192.168.1.100, Port=5900")
        elif result == 'close':
            # 显示拒绝理由对话框
            dialog = RejectReasonDialog()
            reject_response = dialog.get_reason()
            
            if reject_response:
                lprint(f"用户拒绝了远程控制请求")
                lprint(f"拒绝理由: {reject_response.reason}")
                lprint(f"是否自定义理由: {reject_response.is_custom}")
                
                # 模拟发送拒绝消息
                reject_data = {
                    "type": "远程控制响应",
                    "status": "rejected",
                    "reason": reject_response.reason,
                    "is_custom_reason": reject_response.is_custom
                }
                lprint(f"发送拒绝消息: {reject_data}")
    
    # 显示窗口
    notification_window.show()
    
    # 等待窗口关闭
    while notification_window.isVisible():
        await asyncio.sleep(0.1)
    
    # 处理结果
    await handle_result(notification_window.config.result)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 延迟1秒后显示通知窗口
    QTimer.singleShot(1000, lambda: loop.create_task(simulate_remote_control_request()))
    
    # 运行事件循环
    try:
        app.exec()
    finally:
        loop.close()

if __name__ == "__main__":
    main() 