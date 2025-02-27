"""
远程控制请求测试模块
用于测试发送多个远程控制请求
"""
import asyncio
import json
import sys
import os
import io
from datetime import datetime
from zoneinfo import ZoneInfo
import traceback
from typing import Optional, Dict, Any, List
from Lugwit_Module import lprint
import time

# 导入共享的客户端模块
from shared_socket_client import create_client

# 设置Python环境编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'zh_CN.UTF-8'

# 设置标准输出和错误输出的编码
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 设置Windows控制台代码页
if sys.platform == 'win32':
    os.system('chcp 65001')

async def send_remote_control_request(sender: str, recipient: str, control_type: str = "TD") -> None:
    """发送远程控制请求
    
    Args:
        sender: 发送者用户名
        recipient: 接收者用户名
        control_type: 控制类型，默认为"TD"
    """
    try:
        # 创建新的客户端实例并登录
        client = await create_client(sender, "666")
        if not client:
            lprint(f"创建客户端失败: {sender}")
            return

        try:
            # 构造消息数据
            message_data = {
                "sender": sender,
                "recipient": recipient,
                "content": {
                    "type": control_type,
                    "ip": "192.168.112.90",  # 使用测试IP
                    "nickname": sender
                },
                "message_type": 8,  # remote_control
                "content_type": 7,  # plain_text
                "target_type": 1,  # user
                "popup_message": True
            }
            
            # 发送消息
            await client.sio.emit('message', message_data, namespace='/chat/private')
            lprint(f"已发送远程控制请求: {sender} -> {recipient}")
            
            # 等待消息发送完成
            await asyncio.sleep(1)
            
        finally:
            # 确保断开连接
            if client.sio.connected:
                await client.disconnect(client.sio.sid)
            
    except Exception as e:
        lprint(f"发送远程控制请求失败: {str(e)}")
        traceback.print_exc()

async def send_multiple_requests(requests: List[Dict[str, str]]) -> None:
    """发送多个远程控制请求
    
    Args:
        requests: 请求列表，每个请求是一个包含sender、recipient和control_type的字典
    """
    try:
        # 串行发送所有请求
        for request in requests:
            await send_remote_control_request(
                request['sender'],
                request['recipient'],
                request.get('control_type', 'TD')
            )
            # 等待一段时间再发送下一个请求
            await asyncio.sleep(2)
            
        lprint("所有远程控制请求已发送")
        
    except Exception as e:
        lprint(f"发送多个请求失败: {str(e)}")
        traceback.print_exc()

async def main():
    """主函数"""
    try:
        # 准备多个测试请求
        test_requests = [
            {
                'sender': 'system01',  # 调换顺序，先测试 system01
                'recipient': 'fengqingqing',
                'control_type': 'TD'
            },
            {
                'sender': 'zhangqunzhong',
                'recipient': 'fengqingqing',
                'control_type': 'TD'
            }
        ]
        
        # 发送多个请求
        await send_multiple_requests(test_requests)
        
        # 等待一段时间以确保消息发送完成
        await asyncio.sleep(5)
        
    except Exception as e:
        lprint(f"测试过程中发生错误: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
