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
from typing import Optional

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
        
# 添加父目录到系统路径以导入必要的模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Lugwit_Module as LM
lprint = LM.lprint

class MessageType(Enum):
    GROUP_CHAT = "group_chat"
    PRIVATE_CHAT = "private_chat"
    BROADCAST = "broadcast"
    SYSTEM = "system"

class MessageTargetType(Enum):
    """消息目标类型"""
    USER = "user"
    GROUP = "group"
    BROADCAST = "broadcast"
    SYSTEM = "system"

class ChatClient:
    def __init__(self, host='127.0.0.1', port=1026):
        self.base_url = f'http://{host}:{port}'
        self.sio = socketio.AsyncClient(logger=True, engineio_logger=True)
        self.token = None
        
        @self.sio.event
        async def connect():
            lprint('连接到服务器成功!')



        @self.sio.on('message')
        async def on_message(data):
            try:
                message_type = data.get('message_type')
                if message_type == MessageType.PRIVATE_CHAT.value:
                    lprint(f'收到私聊消息: {data}')
                elif message_type == MessageType.GROUP_CHAT.value:
                    lprint(f'收到群聊消息: {data}')
                elif message_type == MessageType.SYSTEM.value:
                    lprint(f'收到系统消息: {data}')
                else:
                    lprint(f'收到其他类型消息: {data}')
            except Exception as e:
                lprint(f'处理消息时出错: {str(e)}')
            
        @self.sio.event
        async def connect_error(data):
            lprint(f'连接错误: {data}')
            
        @self.sio.on('authentication_response')
        async def on_auth_response(data):
            if data.get('success'):
                lprint('认证成功')
            else:
                lprint(f'认证失败: {data.get("error")}')
                
        @self.sio.on('connection_established')
        async def on_connection_established(data):
            lprint(f'连接已建立: {data}')
        
    async def login(self, username, password):
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
            traceback.print_exc()
            return False

    async def connect(self):
        """连接到Socket.IO服务器"""
        try:
            # 添加token到auth参数
            auth = {
                'token': self.token
            } if self.token else {}
            
            lprint(f"开始连接服务器 {self.base_url}, auth={auth}")
            await self.sio.connect(
                self.base_url,
                auth=auth,
                transports=['websocket'],
                wait_timeout=10,
                socketio_path='socket.io'
            )
            lprint("等待连接建立...")
            await asyncio.sleep(1)  # 等待认证完成
            
            if not self.sio.connected:
                lprint("连接失败")
                return False
                
            lprint("连接成功")
            return True
        except Exception as e:
            lprint(f"连接服务器失败: {str(e)}")
            lprint(traceback.format_exc())
            return False



    async def send_message(
        self,
        content: str,
        target_type: MessageTargetType,
        target_id: Optional[str] = None,
        message_type: MessageType = MessageType.PRIVATE_CHAT,
        message_content_type: str = "plain_text",
        popup_message: bool = False
    ) -> None:
        """发送消息
        
        Args:
            content: 消息内容
            target_type: 目标类型（用户/群组/广播/系统）
            target_id: 目标ID（用户名/群组名）
            message_type: 消息类型
            message_content_type: 消息内容类型
            popup_message: 是否弹窗
        """
        try:
            # 验证目标类型和ID
            if target_type in [MessageTargetType.USER, MessageTargetType.GROUP] and not target_id:
                lprint(f"{target_type.value} 类型消息必须指定目标ID")
                return
                
            # 构建基础消息数据
            message_data = {
                "content": content,
                "message_type": message_type.value,
                "message_content_type": message_content_type,
                "target_type": target_type.value,
                "timestamp": datetime.datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
                "popup_message": popup_message,
                "status": "unread"
            }
            
            # 根据目标类型添加特定字段
            if target_type == MessageTargetType.USER:
                message_data["recipient"] = target_id
            elif target_type == MessageTargetType.GROUP:
                message_data["group_name"] = target_id
                
            await self.sio.emit("message", message_data)
            lprint(f"消息已发送: {content} -> {target_type.value}:{target_id or 'all'}")
            
        except Exception as e:
            lprint(f"发送消息失败: {str(e)}")
            lprint(traceback.format_exc())
            
    async def send_private_message(self, content: str, recipient: str, **kwargs) -> None:
        """发送私聊消息"""
        await self.send_message(
            content=content,
            target_type=MessageTargetType.USER,
            target_id=recipient,
            message_type=MessageType.PRIVATE_CHAT,
            **kwargs
        )
        
    async def send_group_message(self, content: str, group_name: str, **kwargs) -> None:
        """发送群聊消息"""
        await self.send_message(
            content=content,
            target_type=MessageTargetType.GROUP,
            target_id=group_name,
            message_type=MessageType.GROUP_CHAT,
            **kwargs
        )
        
    async def send_broadcast_message(self, content: str, **kwargs) -> None:
        """发送广播消息"""
        await self.send_message(
            content=content,
            target_type=MessageTargetType.BROADCAST,
            message_type=MessageType.BROADCAST,
            **kwargs
        )

async def main():
    """主函数"""
    try:
        # 创建客户端实例
        client = ChatClient()
        
        # 登录
        if not await client.login("system01", "666"):
            lprint("登录失败,退出程序")
            return
            
        # 连接服务器
        if not await client.connect():
            lprint("连接服务器失败,退出程序")
            return
            
        # 发送测试消息
        await client.send_private_message("你好!", "test_user")
        await client.send_group_message("大家好!", "test_group")
        await client.send_broadcast_message("这是一条广播消息")
        
        # 保持连接一段时间
        await asyncio.sleep(10)
        
    except Exception as e:
        lprint(f"程序运行出错: {str(e)}")
        traceback.print_exc()
    finally:
        # 断开连接
        if hasattr(client, 'sio') and client.sio.connected:
            await client.sio.disconnect()

if __name__ == "__main__":
    asyncio.run(main())