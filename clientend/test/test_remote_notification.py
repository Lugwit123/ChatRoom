import sys
import os
import asyncio
from PySide6.QtWidgets import QApplication
import qasync

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
os.chdir(parent_dir)
sys.path.append(parent_dir)

import Lugwit_Module as LM
from modules.types.types import MessageBase, ButtonConfig, RejectResponse
from modules.ui.notice_win import create_notification_window
from modules.ui.reject_reason_dialog import RejectReasonDialog

lprint = LM.lprint

class TestWindow:
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.loop = qasync.QEventLoop(self.app)
        asyncio.set_event_loop(self.loop)

    async def show_notification(self):
        """显示通知窗口"""
        try:
            lprint("创建测试消息...")
            # 创建测试消息
            message = MessageBase(
                sender="test_user",
                recipient="current_user",
                content="用户 test_user 请求远程控制\nIP: 192.168.1.100",
                message_type="remote_control",
                popup_message=True
            )
            
            lprint("配置按钮...")
            # 自定义按钮配置
            button_config: ButtonConfig = {
                'accept': '接受控制',
                'close': '拒绝'
            }
            
            lprint("创建通知窗口...")
            # 创建通知窗口
            notification_window = create_notification_window(
                image_path=None,
                message=message,
                result="",
                button_config=button_config
            )
            
            lprint("显示通知窗口...")
            notification_window.show()
            
            # 等待窗口关闭
            while notification_window.isVisible():
                await asyncio.sleep(0.1)
            
            # 处理结果
            result = notification_window.config.result
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
            
            # 退出应用
            self.app.quit()
            
        except Exception as e:
            lprint(f"显示通知窗口失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.app.quit()

    async def run(self):
        """运行测试"""
        try:
            lprint("开始测试远程控制通知窗口...")
            # 等待1秒后显示窗口
            await asyncio.sleep(1)
            await self.show_notification()
        except Exception as e:
            lprint(f"测试运行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.app.quit()

def main():
    """主函数"""
    try:
        lprint(f"当前工作目录: {os.getcwd()}")
        lprint(f"Python路径: {sys.path}")
        
        test = TestWindow()
        with test.loop:
            test.loop.run_until_complete(test.run())
            
    except Exception as e:
        lprint(f"程序启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main()) 