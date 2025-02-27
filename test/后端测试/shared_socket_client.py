"""
共享的Socket.IO客户端模块
提供可重用的ChatClient类和相关功能
"""
import asyncio
import json
import sys
import os
import datetime
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import aiohttp
import socketio
import traceback
from enum import IntEnum
from typing import Optional, Dict, Any, List
import Lugwit_Module as LM
import platform
lprint = LM.lprint

class EnumDefinition:
    """枚举定义类，用于动态创建枚举"""
    def __init__(self, values: Dict[str, int]):
        self._values = values
        for name, value in values.items():
            setattr(self, name.lower(), value)
            
    def __getattr__(self, name: str) -> Any:
        if name.lower() in self._values:
            return self._values[name.lower()]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
            
    @property
    def value(self) -> int:
        """兼容IntEnum的value属性"""
        return self._value if hasattr(self, '_value') else 0

class ChatClient:
    """聊天客户端类"""
    def __init__(self, host='192.168.112.233', port=1026):
        self.base_url = f'http://{host}:{port}'
        # 每个实例创建独立的 Socket.IO 客户端
        self.sio = socketio.AsyncClient(
            logger=False,
            engineio_logger=False,
            reconnection=False,  # 禁用自动重连
            reconnection_attempts=0,
            reconnection_delay=0,
            handle_sigint=False
        )
        self.token = None
        self.enums = None  # 存储枚举定义
        self.stats = {
            'login_time': 0.0,
            'send_time': 0.0,
            'receive_time': 0.0,
            'message_count': 0,
            'send_count': 0
        }
        self.namespace = '/chat/private'  # 添加命名空间
        self.message_start_time = time.time()  # 添加消息开始时间
        self._register_handlers()
        
    def _register_handlers(self):
        """注册所有事件处理器"""
        
        @self.sio.event(namespace=self.namespace)
        async def connect():
            lprint('连接到服务器成功!')

        @self.sio.event(namespace=self.namespace)
        async def error(data):
            lprint(f'Socket.IO错误: {data}')

        @self.sio.event(namespace=self.namespace)
        async def message_error(data):
            lprint(f'消息错误: {data}')

        @self.sio.on('message', namespace=self.namespace)
        async def on_message(data):
            """处理接收到的消息"""
            try:
                self.message_start_time = time.time()  # 更新消息开始时间
                lprint(f"收到消息: {data}")
                self.stats['message_count'] += 1
                self.stats['receive_time'] += time.time() - self.message_start_time
            except Exception as e:
                lprint(f"处理消息失败: {str(e)}")
                traceback.print_exc()

        @self.sio.event(namespace=self.namespace)
        async def connect_error(data):
            lprint(f'连接错误: {data}')
            
        @self.sio.on('authentication_response', namespace=self.namespace)
        async def on_auth_response(data):
            if data.get('success'):
                lprint('认证成功')
            else:
                lprint(f'认证失败: {data.get("error")}')
                
        @self.sio.on('connection_established', namespace=self.namespace)
        async def on_connection_established(data):
            lprint(f'连接已建立: {data}')
        
        @self.sio.on('private_message_sent', namespace=self.namespace)
        async def on_private_message_sent(data):
            """处理私聊消息发送回执"""
            try:
                lprint(f"私聊消息发送成功: {data}")
            except Exception as e:
                lprint(f"处理私聊消息发送回执失败: {str(e)}")
                traceback.print_exc()

        @self.sio.on('group_message_sent', namespace=self.namespace)
        async def on_group_message_sent(data):
            """处理群聊消息发送回执"""
            try:
                lprint(f"群聊消息发送成功: {data}")
            except Exception as e:
                lprint(f"处理群聊消息发送回执失败: {str(e)}")
                traceback.print_exc()

    def _get_user_agent(self) -> str:
        """生成用户代理字符串"""
        python_version = platform.python_version()
        system = platform.system()
        machine = platform.machine()
        return f"PythonClient/{python_version} ({system}; {machine})"

    async def login(self, username, password):
        """登录并获取token"""
        try:
            start_time = datetime.now()
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
                    'User-Agent': self._get_user_agent()  # 使用动态生成的 User-Agent
                }
                
                async with session.post(
                    f'{self.base_url}/api/auth/login',
                    data=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response_text = await response.text()
                    lprint(f"登录响应: {response_text}")
                    
                    if response.status == 200:
                        result = json.loads(response_text)
                        self.token = result.get('access_token')
                        if not self.token:
                            lprint("登录响应中没有access_token")
                            return False
                            
                        lprint(f"登录成功，token: {self.token[:10]}...")
                        self.stats['login_time'] = (datetime.now() - start_time).total_seconds()
                        return True
                    else:
                        lprint(f"登录失败: {response_text}")
                        return False
                        
        except Exception as e:
            lprint(f"登录过程中发生错误: {str(e)}")
            traceback.print_exc()
            return False

    async def connect(self) -> bool:
        """连接到Socket.IO服务器"""
        try:
            if not self.token:
                lprint("未获取到token,无法连接")
                return False
                
            # 如果已经连接，先断开
            if self.sio.connected:
                await self.sio.disconnect()
                await asyncio.sleep(1)  # 等待断开完成
                
            # 设置认证信息
            auth = {
                'token': self.token
            }
            
            # 连接到服务器
            lprint("开始连接到Socket.IO服务器...")
            await self.sio.connect(
                self.base_url,
                auth=auth,
                namespaces=[self.namespace],  # 指定命名空间
                transports=['websocket'],
                wait_timeout=10,
                socketio_path='socket.io'
            )
            
            lprint("Socket.IO连接已建立")
            return True
            
        except Exception as e:
            lprint(f"连接失败: {str(e)}")
            traceback.print_exc()
            return False

    async def fetch_enums(self) -> None:
        """从API获取枚举定义"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{self.base_url}/api/enums/message') as response:
                    if response.status == 200:
                        data = await response.json()
                        self.enums = {
                            'MessageType': EnumDefinition(data['MessageType']['values']),
                            'MessageContentType': EnumDefinition(data['MessageContentType']['values']),
                            'MessageTargetType': EnumDefinition(data['MessageTargetType']['values']),
                            'MessageStatus': EnumDefinition(data['MessageStatus']['values'])
                        }
                        lprint("成功获取枚举定义")
                    else:
                        lprint(f"获取枚举定义失败: {response.status}")
        except Exception as e:
            lprint(f"获取枚举定义出错: {str(e)}")
            traceback.print_exc()
            
    def _get_enum(self, enum_type: str) -> EnumDefinition:
        """获取枚举定义，如果未初始化则使用默认值"""
        if not self.enums or enum_type not in self.enums:
            # 使用默认值
            defaults = {
                'MessageType': {'chat': 1, 'system': 2, 'broadcast': 3},
                'MessageContentType': {'plain_text': 7},
                'MessageTargetType': {'user': 1, 'group': 2, 'broadcast': 3},
                'MessageStatus': {'unread': 1, 'read': 2, 'archived': 3}
            }
            return EnumDefinition(defaults.get(enum_type, {}))
        return self.enums[enum_type]

    async def send_message(
        self,
        content: str,
        target_type: str,
        target_id: Optional[str] = None,
        message_type: str = 'chat',
        message_content_type: str = 'plain_text',
        popup_message: bool = False
    ) -> None:
        """发送消息
        
        Args:
            content: 消息内容
            target_type: 目标类型（user/group/broadcast）
            target_id: 目标ID（用户名/群组名）
            message_type: 消息类型
            message_content_type: 消息内容类型
            popup_message: 是否弹窗
        """
        try:
            start_time = datetime.now()
            # 获取枚举值
            msg_target_type = self._get_enum('MessageTargetType')
            msg_type = self._get_enum('MessageType')
            msg_content_type = self._get_enum('MessageContentType')
            msg_status = self._get_enum('MessageStatus')
            
            target_type_value = getattr(msg_target_type, target_type)
            message_type_value = getattr(msg_type, message_type)
            content_type_value = getattr(msg_content_type, message_content_type)
            
            # 验证目标类型和ID
            if target_type in ['user', 'group'] and not target_id:
                lprint(f"{target_type} 类型消息必须指定目标ID")
                return
                
            # 构建基础消息数据
            message_data = {
                "content": content,
                "message_type": message_type_value,
                "content_type": content_type_value,
                "target_type": target_type_value,
                "timestamp": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
                "popup_message": popup_message,
            }
            
            # 根据目标类型添加特定字段
            if target_type == 'user':
                message_data["recipient"] = target_id
            elif target_type == 'group':
                message_data["group_id"] = target_id
                
            lprint(f"准备发送消息: {message_data}")
            await self.sio.emit("message", message_data, namespace=self.namespace)  # 添加命名空间
            lprint(f"消息已发送: {content} -> {target_type}:{target_id or 'all'}")
            
            self.stats['send_time'] += (datetime.now() - start_time).total_seconds()
            self.stats['send_count'] += 1
            
        except Exception as e:
            lprint(f"发送消息失败: {str(e)}")
            traceback.print_exc()
            
    async def send_private_message(self, content: str, recipient: str, **kwargs) -> None:
        """发送私聊消息"""
        await self.send_message(
            content=content,
            target_type='user',
            target_id=recipient,
            message_type='chat',
            **kwargs
        )
        
    async def send_group_message(self, content: str, group_name: str, **kwargs) -> None:
        """发送群聊消息"""
        await self.send_message(
            content=content,
            target_type='group',
            target_id=group_name,
            message_type='chat',
            **kwargs
        )
        
    async def send_broadcast_message(self, content: str, **kwargs) -> None:
        """发送广播消息"""
        await self.send_message(
            content=content,
            target_type='broadcast',
            message_type='broadcast',
            **kwargs
        )

    async def disconnect(self, sid):
        """断开连接"""
        try:
            lprint(f"断开连接: {sid}")
            if self.sio and self.sio.connected:
                # 添加延迟以确保消息发送完成
                await asyncio.sleep(1)
                await self.sio.disconnect()
                lprint("断开连接成功")
        except Exception as e:
            lprint(f"断开连接失败: {str(e)}")
            traceback.print_exc()

async def create_client(username: str, password: str = "666") -> Optional[ChatClient]:
    """创建并初始化ChatClient实例
    
    Args:
        username: 用户名
        password: 密码，默认为"666"
        
    Returns:
        Optional[ChatClient]: 初始化成功的ChatClient实例，失败则返回None
    """
    try:
        # 创建客户端实例
        client = ChatClient()
        
        # 登录
        if not await client.login(username, password):
            lprint("登录失败")
            return None
            
        # 获取枚举定义
        await client.fetch_enums()
            
        # 连接服务器
        if not await client.connect():
            lprint("连接服务器失败")
            return None
            
        return client
        
    except Exception as e:
        lprint(f"创建客户端失败: {str(e)}")
        traceback.print_exc()
        return None 