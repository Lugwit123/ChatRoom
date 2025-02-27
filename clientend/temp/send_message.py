# chat_client.py

import json
import time
import socketio
import requests
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from Lugwit_Module import lprint
from pydantic import BaseModel
import os
import sys
import traceback
# 从文件读取服务器IP地址
try:
    with open("A:/temp/chat/privateRoomLog/server_ip_address.txt", "r") as f:
        server_ip = f.read().strip()
        os.environ['SERVER_IP'] = server_ip
except Exception as e:
    print(f"Error reading server IP: {e}")
    server_ip = "localhost"  # 如果读取失败则使用localhost作为后备
# 确保导入schemas模块的路径正确
sys.path.append(r"D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\ChatRoom")
from backend import schemas

class ChatClient:
    def __init__(self, username: str, password: str):
        """
        初始化ChatClient实例。

        :param server_url: Socket.IO服务器的URL。
        :param login_url: 登录API的URL。
        :param username: 登录用户名。
        :param password: 登录密码。
        """
        self.server_url = f'http://{server_ip}:1026'
        self.login_url = f'http://{server_ip}:1026/api/auth/login'
        self.username = username
        self.password = password
        self.token: Optional[str] = None
        self.sio = socketio.Client()

        # 关闭代理
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''

        # 设置Socket.IO事件
        self.sio.on('connect', self.on_connect)
        self.sio.on('connect_error', self.on_connect_error)

    def on_connect(self):
        print("连接成功!")

    def on_connect_error(self, data):
        print("连接失败:", data)

    def login(self) -> bool:
        """
        执行登录操作并获取访问令牌。

        :return: 如果登录成功，返回True；否则，返回False。
        """
        login_data = {
            "username": self.username,
            "password": self.password
        }
        try:
            response = requests.post(self.login_url, data=login_data)
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                print("登录成功，获取的访问令牌:", self.token)
                return True
            else:
                print("登录失败:", response.text)
                return False
        except requests.RequestException as e:
            print("登录请求异常:", e)
            return False

    def on_private_message_sent(self, response=None):
        """处理私聊消息发送回执"""
        try:
            lprint(f"私聊消息发送成功: {response}")
        except Exception as e:
            lprint(f"处理私聊消息发送回执失败: {str(e)}")
            traceback.print_exc()

    def on_group_message_sent(self, response=None):
        """处理群聊消息发送回执"""
        try:
            lprint(f"群聊消息发送成功: {response}")
        except Exception as e:
            lprint(f"处理群聊消息发送回执失败: {str(e)}")
            traceback.print_exc()

    def run(self, message: schemas.MessageBase):
        """运行客户端"""
        try:
            # 连接服务器
            self.sio.connect(
                self.server_url,
                auth={'token': self.token},
                namespaces=['/chat/private', '/chat/group']
            )
            
            # 发送消息
            if message.message_type == schemas.MessageType.remote_control:
                self.sio.emit('message', message.model_dump_json(), callback=self.on_private_message_sent)
            elif message.message_type == schemas.MessageType.chat:
                if hasattr(message, 'group_id') and message.group_id:
                    self.sio.emit('message', message.model_dump_json(), callback=self.on_group_message_sent)
                else:
                    self.sio.emit('message', message.model_dump_json(), callback=self.on_private_message_sent)
            
            # 等待消息发送完成
            time.sleep(1)
            
            # 断开连接
            self.sio.disconnect()
            
        except Exception as e:
            lprint(f"运行客户端失败: {str(e)}")
            traceback.print_exc()

def build_message(sender: str, 
                  recipient: str, 
                  check_type: str, 
                  url: str, 
                  check_data_file: str,
                  popup_message=True,) -> schemas.MessageBase:
    """
    构建消息对象。

    :param sender: 发送者用户名。
    :param recipient: 接收者用户名。
    :param check_type: 检查类型。
    :param url: 检查文件的URL。
    :param check_data_file: 检查数据文件路径。
    :return: schemas.MessageBase实例。
    """
    message_data = {
        "sender": sender,
        "recipient": recipient,
        "content": {
            'check_type': check_type,
            'url': url,
            'check_data_file': check_data_file
        },
        "timestamp": datetime.now().isoformat(),
        "recipient_type": "private",
        "status": ["pending"],
        "direction": "request",
        "message_content_type": "html",
        "message_type": 'validation',
        "popup_message": True
    }
    return schemas.MessageBase(**message_data)        


def send_message(sender: str,
                recipient: str,
                jsonFilePath: str="",
                messageType: Literal["remote_control", "private_message"]="private_message",
                popup_message: bool = True):
    """
    发送消息
    
    Args:
        sender: 发送者
        recipient: 接收者
        jsonFilePath: JSON文件路径
        messageType: 消息类型，必须是 "remote_control" 或 "private_message"
        popup_message: 是否弹窗显示，默认为True
    """
    password = '666'  # 登录密码
    # 创建ChatClient实例
    client = ChatClient(sender, password)

    # 从其他模块导入并构建消息内容
    message = schemas.MessageBase(
        sender=sender,
        recipient=recipient,
        message_type=schemas.MessageType(messageType),
        content="远程控制",
        popup_message=popup_message
    )

    # 发送消息
    client.run(message)
        
if __name__ == "__main__":
    send_message(sender="fengqingqing",
                recipient="OC1",
                messageType="remote_control",)
