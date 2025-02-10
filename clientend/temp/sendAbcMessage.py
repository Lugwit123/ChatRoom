# chat_client.py

import json
import time
import socketio
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from Lugwit_Module import lprint
from pydantic import BaseModel
import os
import sys

# 确保导入schemas模块的路径正确
sys.path.append(r"D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\ChatRoom\backend")
import schemas

class ChatClient:
    def __init__(self, username: str, password: str):
        """
        初始化ChatClient实例。

        :param server_url: Socket.IO服务器的URL。
        :param login_url: 登录API的URL。
        :param username: 登录用户名。
        :param password: 登录密码。
        """
        self.server_url = 'http://127.0.0.1:1026'
        self.login_url = 'http://127.0.0.1:1026/api/auth/login'
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

    def on_message_sent(self, response=None):
        """
        消息发送后的回调函数。

        :param response: 服务器的响应。
        """
        print(f"服务器响应: {response}")

    def send_message(self, message: schemas.MessageBase) -> None:
        """
        发送消息到Socket.IO服务器。

        :param message: 要发送的消息对象。
        """
        if not self.token:
            print("没有有效的令牌，无法发送消息。")
            return

        auth_info = {
            'token': self.token,
            'transports': ['websocket'],
        }
        try:
            self.sio.connect(self.server_url, auth=auth_info)
            self.sio.emit('message', message.model_dump_json(), callback=self.on_message_sent)
            # 等待消息发送和回调执行
            time.sleep(1)
        except socketio.exceptions.ConnectionError as e:
            print("Socket.IO连接异常:", e)
        finally:
            self.sio.disconnect()

    def run(self, message: schemas.MessageBase) -> None:
        """
        执行完整的登录和发送消息流程。

        :param message: 要发送的消息对象。
        """
        if self.login():
            self.send_message(message)
        else:
            print("无法获取令牌，消息未发送")

def build_message(sender: str, 
                  recipient: str, 
                  check_type: str, 
                  url: str, 
                  check_data_file: str,
                  popup_message=True) -> schemas.MessageBase:
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

def send_message(recipient:str,jsonFilePath:str):
        username = 'system01'  # 登录用户名
        password = '666'  # 登录密码

        # 创建ChatClient实例
        client = ChatClient(username, password)
        if not jsonFilePath:
            jsonFilePath=r'G:/ZTS/06.CFX/EP001/ep001_sc001_shot0010/ep001_sc001_shot0010_check.json'
        lprint(jsonFilePath)
        jsonFilePath=os.path.basename(jsonFilePath)
        url=f"http://127.0.0.1:1026/check_file/abc_check_show/{jsonFilePath}"
        print("jsonFilePath,rul",jsonFilePath,url)
        # 从其他模块导入并构建消息内容
        message = build_message(
            sender="system01",
            recipient=recipient,
            check_type="cfx_abc_check",
            url=url,
            check_data_file=jsonFilePath,
            popup_message=True
        )

        # 发送消息
        client.run(message)
        
if __name__ == "__main__":
    send_message("")
