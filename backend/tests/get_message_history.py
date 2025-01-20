import asyncio
import json
import sys
import os
import datetime
from zoneinfo import ZoneInfo
import aiohttp
import socketio
import io
import traceback
from enum import Enum
from typing import Optional, List

# 设置Python环境编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'zh_CN.UTF-8'

# 设置标准输出和错误输出的编码
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# 添加父目录到系统路径以导入必要的模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Lugwit_Module as LM
lprint = LM.lprint

class MessageType(Enum):
    GROUP_CHAT = "group_chat"
    PRIVATE_CHAT = "private_chat"

class ChatHistoryClient:
    def __init__(self, host='127.0.0.1', port=1026):
        self.base_url = f'http://{host}:{port}'
        self.token = None
        
    async def login(self, username: str, password: str) -> bool:
        """登录并获取token"""
        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('username', username)
                data.add_field('password', password)
                data.add_field('grant_type', 'password')
                data.add_field('scope', '')
                data.add_field('client_id', '')
                data.add_field('client_secret', '')
                
                headers = {
                    'Accept': 'application/json',
                }
                
                async with session.post(
                    f'{self.base_url}/api/auth/login',
                    data=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.token = result.get('access_token')
                        lprint("登录成功")
                        return True
                    else:
                        response_text = await response.text()
                        lprint(f"登录失败: {response_text}")
                        return False
        except Exception as e:
            lprint(f"登录过程中发生错误: {str(e)}")
            lprint(traceback.format_exc())
            return False
            
    async def get_private_messages(
        self,
        sender: str,
        recipient: str,
        limit: int = 50
    ) -> List[dict]:
        """获取私聊消息历史"""
        try:
            if not self.token:
                lprint("未登录，请先登录")
                return []
                
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/messages/private"
                params = {
                    "sender": sender,
                    "recipient": recipient,
                    "limit": limit
                }
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        lprint(f"获取到 {len(data)} 条私聊消息")
                        return data
                    else:
                        text = await response.text()
                        lprint(f"获取私聊消息失败: {response.status} - {text}")
                        return []
                        
        except Exception as e:
            lprint(f"获取私聊消息时发生错误: {str(e)}")
            lprint(traceback.format_exc())
            return []
            
    async def get_group_messages(
        self,
        group_name: str,
        limit: int = 50
    ) -> List[dict]:
        """获取群聊消息历史"""
        try:
            if not self.token:
                lprint("未登录，请先登录")
                return []
                
            lprint("\n=== 开始获取群聊消息 ===")
            lprint(f"群组名称: {group_name}")
            lprint(f"消息数量限制: {limit}")
            
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Accept': 'application/json'
            }
            lprint(f"认证Token: {self.token[:10]}...")
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/messages/group/{group_name}"
                params = {"limit": limit}
                
                lprint("\n请求详情:")
                lprint(f"- 完整URL: {url}")
                lprint(f"- 查询参数: {json.dumps(params, indent=2)}")
                lprint(f"- 请求头: {json.dumps(headers, indent=2)}")
                
                try:
                    lprint("\n发送HTTP请求...")
                    async with session.get(url, params=params, headers=headers) as response:
                        lprint(f"收到响应 - 状态码: {response.status}")
                        lprint(f"响应头: {json.dumps(dict(response.headers), indent=2)}")
                        
                        if response.status == 200:
                            data = await response.json()
                            message_count = len(data)
                            lprint(f"\n成功获取群聊消息:")
                            lprint(f"- 消息总数: {message_count}")
                            if message_count > 0:
                                lprint("- 第一条消息:")
                                lprint(json.dumps(data[0], indent=2, ensure_ascii=False))
                                lprint("- 最后一条消息:")
                                lprint(json.dumps(data[-1], indent=2, ensure_ascii=False))
                            return data
                        else:
                            text = await response.text()
                            lprint("\n请求失败:")
                            lprint(f"- 状态码: {response.status}")
                            lprint(f"- 错误响应: {text}")
                            try:
                                error_json = json.loads(text)
                                lprint(f"- 错误详情: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                            except json.JSONDecodeError:
                                lprint("- 错误响应不是JSON格式")
                            return []
                except aiohttp.ClientError as e:
                    lprint(f"\n发送请求时发生错误: {str(e)}")
                    lprint(f"错误类型: {type(e).__name__}")
                    return []
                        
        except Exception as e:
            lprint("\n获取群聊消息时发生异常:")
            lprint(f"- 错误类型: {type(e).__name__}")
            lprint(f"- 错误信息: {str(e)}")
            lprint("- 错误堆栈:")
            lprint(traceback.format_exc())
            return []

def format_message(message: dict) -> str:
    """格式化消息显示"""
    timestamp = datetime.datetime.fromisoformat(message['timestamp'])
    formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    status = message.get('status', ['unknown'])[0]
    content_type = message.get('message_content_type', 'text')
    
    return (
        f"[{formatted_time}] "
        f"{message['sender']} -> {message.get('recipient', 'GROUP')}: "
        f"{message['content']} "
        f"({content_type}, {status})"
    )

async def main():
    """主函数"""
    try:
        # 创建客户端实例
        client = ChatHistoryClient()
        
        # 登录
        if not await client.login("system01", "666"):
            return
            
        # 测试参数
        sender = "system01"
        recipient = "fengqingqing"
        group_name = "asset_group"
        
        # 获取私聊消息历史
        lprint("\n=== 获取私聊消息历史 ===")
        private_messages = await client.get_private_messages(
            sender, recipient
        )
        for msg in private_messages:
            lprint(format_message(msg))
            
        # 获取群聊消息历史
        lprint("\n=== 获取群聊消息历史 ===")
        group_messages = await client.get_group_messages(
            group_name
        )
        for msg in group_messages:
            lprint(format_message(msg))
            
    except Exception as e:
        lprint(f"测试执行失败: {str(e)}")
        lprint(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())