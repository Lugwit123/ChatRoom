import asyncio
import sys
import os
import datetime
from datetime import datetime
from zoneinfo import ZoneInfo
import traceback

# 设置Python环境编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'zh_CN.UTF-8'

# 添加父目录到系统路径以导入必要的模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Lugwit_Module as LM
lprint = LM.lprint

# 导入ChatClient类
from test_socket_client_and_send_message import ChatClient

async def send_remote_control_request():
    """发送远程控制请求"""
    try:
        # 创建客户端实例
        client = ChatClient()
        
        # 登录
        if not await client.login("system01", "666"):
            lprint("登录失败,退出程序")
            return
            
        # 获取枚举定义
        await client.fetch_enums()
            
        # 连接服务器
        if not await client.connect():
            lprint("连接服务器失败,退出程序")
            return
            
        # 发送远程控制请求
        await client.send_message(
            content="请求远程控制",
            target_type='user',
            target_id='fengqingqing',
            message_type='remote_control',  # 设置为远程控制消息
            message_content_type='plain_text',  # 使用纯文本类型
            popup_message=True  # 设置弹窗提醒
        )
        
        # 等待消息发送完成
        await asyncio.sleep(1)
        
        # 保持连接一段时间等待响应
        await asyncio.sleep(1)
        
        # 打印统计信息
        lprint("\n性能统计:")
        lprint(f"登录耗时: {client.stats['login_time']:.3f}秒")
        lprint(f"平均发送耗时: {(client.stats['send_time']/max(1, client.stats['send_count'])):.3f}秒")
        lprint(f"平均接收耗时: {(client.stats['receive_time']/max(1, client.stats['message_count'])):.3f}秒")
        lprint(f"发送消息数: {client.stats['send_count']}")
        lprint(f"接收消息数: {client.stats['message_count']}")
        
    except Exception as e:
        lprint(f"发送远程控制请求时发生错误: {str(e)}")
        traceback.print_exc()
    finally:
        # 断开连接
        import time
        time.sleep(1)
        if hasattr(client, 'sio') and client.sio.connected:
            await client.sio.disconnect()

if __name__ == "__main__":
    asyncio.run(send_remote_control_request())
