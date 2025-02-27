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
from modules.types.types import MessageBase, ButtonConfig
from modules.ui.notice_win import create_notification_window

lprint = LM.lprint

class TestWindow:
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.loop = qasync.QEventLoop(self.app)
        asyncio.set_event_loop(self.loop)
        self.notification_window = None

    def create_test_message(self, sender: str, ip: str) -> MessageBase:
        """创建测试消息"""
        return MessageBase(
            sender=sender,
            recipient="current_user",
            content=f"用户 {sender} 请求远程控制\nIP: {ip}",
            message_type="remote_control",
            popup_message=True
        )

    async def add_new_request(self):
        """模拟添加新的请求"""
        await asyncio.sleep(1)  # 等待5秒后添加新请求
        if self.notification_window and self.notification_window.isVisible():
            lprint("添加新的远程控制请求...")
            new_message = self.create_test_message("user4", "192.168.1.104")
            self.notification_window.add_request(new_message)
            
            await asyncio.sleep(1)  # 再等待3秒
            new_message = self.create_test_message("user5", "192.168.1.105")
            self.notification_window.add_request(new_message)

    async def show_notification(self):
        """显示通知窗口"""
        try:
            lprint("创建测试消息...")
            # 创建初始测试消息
            messages = [
                self.create_test_message("user1", "192.168.1.101"),
            ]
            
            lprint("配置按钮...")
            button_config: ButtonConfig = {
                'accept': '接受控制',
                'close': '拒绝'
            }
            
            lprint("创建通知窗口...")
            self.notification_window = create_notification_window(
                image_path=None,
                message=messages[0],
                result="",
                button_config=button_config
            )
            
            # 添加其他消息
            for message in messages[1:]:
                self.notification_window.add_request(message)
            
            lprint("显示通知窗口...")
            self.notification_window.show()
            
            # 创建任务来添加新请求
            add_request_task = asyncio.create_task(self.add_new_request())
            
            # 等待窗口关闭
            while self.notification_window.isVisible():
                await asyncio.sleep(0.1)
            
            # 取消添加请求的任务
            add_request_task.cancel()
            
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
            lprint("开始测试多个远程控制请求...")
            lprint("测试场景：")
            lprint("1. 初始显示3个用户的请求")
            lprint("2. 5秒后添加user4的请求")
            lprint("3. 再过3秒添加user5的请求")
            lprint("4. 测试处理请求时的窗口行为")
            
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