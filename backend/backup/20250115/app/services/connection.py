# backend/connection_manager.py

from dataclasses import dataclass, field
import traceback
from typing import Dict, Set, List, Optional, TypeAlias, Callable, cast
from user_database import (
    fetch_user,
    set_user_online_status,
    fetch_registered_users,
    get_chat_history
)
from utils import get_avatar_index
from datetime import datetime
import logging
import schemas
import Lugwit_Module as LM
import socketio
import json
import asyncio
from schemas import MessageBase

lprint = LM.lprint


# 定义类型别名
Username: TypeAlias = str
SID: TypeAlias = str

@dataclass
class ConnectionInfo:
    sid: SID
    username: Username
    ip_address: str
    pending_messages: Dict[str, MessageBase] = field(default_factory=dict)  # 存储待确认的消息
    retry_count: Dict[str, int] = field(default_factory=dict)  # 存储消息重试次数
import pdb
class ConnectionManager:
    
    def __init__(self, sio_instance: socketio.AsyncServer) -> None:
        lprint("开始socket连接")
        self.sio = sio_instance
        self.engineio_logger = False
        self.active_connections: Dict[Username, ConnectionInfo] = {}  # username -> ConnectionInfo
        self.group_members: Dict[str, Set[Username]] = {}
        self.sid_to_user: Dict[SID, schemas.UserBase] = {}  # sid -> user
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 2  # 重试间隔(秒)



    def _get_lan_ip(self) -> str:
        """获取局域网IP地址"""
        import socket
        try:
            # 获取所有网络接口
            interfaces = socket.getaddrinfo(socket.gethostname(), None)
            lprint("所有网络接口:", [interface[4][0] for interface in interfaces])
            
            for interface in interfaces:
                ip = interface[4][0]
                # 只获取IPv4地址，并且是局域网地址
                if ip.count('.') == 3:  # IPv4
                    # 检查是否是局域网IP
                    first_octet = int(ip.split('.')[0])
                    if (ip.startswith('192.168.') or  # 192.168.x.x
                        ip.startswith('10.') or       # 10.x.x.x
                        (first_octet == 172 and       # 172.16.x.x - 172.31.x.x
                         16 <= int(ip.split('.')[1]) <= 31)):
                        return ip
            return 'unknown'
        except Exception as e:
            lprint(f"获取局域网IP失败: {e}", popui=False)
            return 'unknown'

    async def connect(self, sid: SID, username: Username, client_ip: str) -> bool:
        """处理新的WebSocket连接
        
        Args:
            sid: Socket.IO的会话ID
            username: 用户名
            client_ip: 客户端IP地址
            
        Returns:
            bool: 连接是否成功
        """
        try:
            user = await fetch_user(username)
            if not user:
                lprint(f"❌ 无法获取用户信息: {username}", popui=False)
                return False

            lprint(f"📝 用户 {username} 从IP {client_ip} 连接", popui=False)
                
            # 存储新连接信息
            self.active_connections[username] = ConnectionInfo(sid=sid, username=username, ip_address=client_ip)
            self.sid_to_user[sid] = user

            await set_user_online_status(username, True)
            
            # 发送连接成功确认
            await self.sio.emit('connection_established', {
                'status': 'connected',
                'sid': sid,
                'username': username
            }, room=sid)
            
            # 广播用户上线状态
            await self.broadcast_user_status(username, True)
            
            return True
            
        except Exception as e:
            lprint(f"连接处理失败: {str(e)}", popui=False)
            lprint(traceback.format_exc(), popui=False)
            return False

    async def disconnect(self, sid: SID) -> None:
        user = self.sid_to_user.get(sid)
        lprint(user,sid,'disconect', popui=True)
        if not user:
            logging.warning(f"Disconnect: 未找到 sid={sid} 对应的用户")
            return

        username = user.username
        if username in self.active_connections:
            del self.active_connections[username]

        if sid in self.sid_to_user:
            del self.sid_to_user[sid]
        
        await set_user_online_status(username, False)
        # 广播用户离线状态
        await self.broadcast_user_status(username, False)

    def get_username(self, sid: SID) -> Optional[Username]:
        print("通过sid获取用户名")
        user = self.sid_to_user.get(sid)
        if user:
            return user.username
        return None

    def get_groups(self, sid: SID) -> List[str]:
        user = self.sid_to_user.get(sid)
        if user:
            return [group.name for group in user.groups]
        return []

    async def broadcast_user_list(self) -> None:
        print("广播用户列表")
        try:
            if not self.sid_to_user:
                logging.info("没有在线用户，无需广播用户列表。")
                return
            # 查询所有用户信息
            any_sid = next(iter(self.sid_to_user), None)
            if any_sid is None:
                return
            any_user = self.sid_to_user[any_sid]
            users = await fetch_registered_users(
                current_username=any_user.username, 
                include_unread_count=True
            )
            
            # 构造用户细信息列表
            online_usernames = set(self.active_connections)
            user_detail_list = [
                schemas.UserBaseAndStatus(
                    id=user.id,
                    username=user.username,
                    nickname=user.nickname,
                    email=user.email,
                    groups=user.groups,
                    role=user.role,
                    online=(user.username in online_usernames),
                    unread_message_count=user.unread_message_count,
                    avatar_index=get_avatar_index(user.username)
                ).dict()
                for user in users
            ]
            # lprint(user_detail_list[:2])
            # 构建广播消息
            message = schemas.MessageBase(
                message_type=schemas.MessageType.USER_LIST_UPDATE,
                sender="system01",
                recipient="all",  # 表示广播给所有在线用户
                content=user_detail_list,
                timestamp=datetime.now(),
                status=[schemas.MessageStatus.UNREAD],
                message_content_type=schemas.MessageContentType.USER_LIST,
            )
            
            # 广播消息到所有在线连接
            await self.broadcast(message)
            logging.info(f"广播成功，共更新 {len(user_detail_list)} 个用户的状态。")
        except Exception as e:
            logging.error(f"Error broadcasting user list: {e}")

    async def broadcast(self, message:schemas.MessageBase, room: Optional[str] = None) -> None:
        print ("广播消息")
        try:
            connections_copy = list(self.active_connections.values())
            for connection_info in connections_copy:
                await self.sio.emit('message', message.model_dump(), room=connection_info.sid)
        except Exception as e:
            logging.error(traceback.format_exc())

    async def send_with_retry(self, message: MessageBase, 
                            await_confirmation: bool = False) -> MessageBase:
        print("send_with_retry")
        try:
            connection_info = self.active_connections.get(message.recipient) # type: ignore #
            # 确保消息已经保存到数据库并有唯一ID
            if isinstance(message, dict):
                message = MessageBase(**message)
            if not hasattr(message, 'id'):
                lprint("错误: 消息没有有效的ID属性", popui=False)
                lprint(f"消息内容: {message}", popui=False)
                return message
            if message.message_type==schemas.MessageType.REMOTE_CONTROL:
                sender_connection = self.active_connections.get(message.sender)
                if sender_connection:
                    sender_ip = sender_connection.ip_address
                    lprint(f"发送者IP地址: {sender_ip}")
                    # 可以将IP地址添加到消息内容中
                    message.content={
                        "ip": sender_ip,
                        "comment": message.content
                    }
            if connection_info:
                message.direction=schemas.MessageDirection.REQUEST
                send_mes=message.model_dump_json()
                lprint(send_mes)
                await self.sio.emit('message', send_mes, room=connection_info.sid)
                print ("发送消息成功")
                #pdb.set_trace()  # 设置断点
            if connection_info==None:
                message.status=[schemas.MessageStatus.UNREAD,schemas.MessageStatus.SUCCESS]
            return message
        except:
            lprint(traceback.format_exc())
            return message

    async def send_system_message(self, message: str, exclude_username: Optional[str] = None) -> None:
        system_message = {
            "message_type": schemas.MessageType.SYSTEM,
            "sender": "system",
            "recipient": "all",
            "content": f"System message: {message}",
            "timestamp": datetime.now().isoformat(),
            "recipient_type": "group",
            "status": "unread",
            "message_content_type": schemas.MessageContentType.PLAIN_TEXT
        }
        for username, connection_info in self.active_connections.items():
            if exclude_username and username == exclude_username:
                continue
            await self.sio.emit('message', system_message, room=connection_info.sid)

    async def send_group_message(self, message: schemas.MessageBase, group: str) -> None:
        print("发送组消息")
        members = self.group_members.get(group, set())
        failed_members = []
        for username in members:
            connection_info = self.active_connections.get(username)
            if connection_info:
                success = await self.send_with_retry(message.dict(), connection_info)
                if not success:
                    failed_members.append(username)
        
        if failed_members:
            lprint(f"Failed to send group message to members: {failed_members}")

    async def get_user(self, sid: SID) -> Optional[schemas.UserBase]:
        return self.sid_to_user.get(sid)


    async def broadcast_to_group(self, group_name: str, message: dict) -> None:
        print("""发送消息给群组的所有成员""")
        # 获取群组所有成员的 socket ids
        group_sids = [
            sid for sid, username in self.active_connections.items()
            if group_name in self.user_groups.get(username, [])
        ]

        if not group_sids:
            logging.warning(f"群组 {group_name} 没有在线成员")
            return

        # 发送消息到群组的所有成员
        for sid in group_sids:
            try:
                await self.sio.emit('message', message, room=sid)
            except Exception as e:
                logging.error(f"发送群组消息失败: {str(e)}")

    async def broadcast(self, message: schemas.MessageBase, exclude: Optional[str] = None) -> None:
        print ("""广播消息给所有用户，可选择排除某个用户""")
        return
        try:
            if exclude:
                # 获取除了被排除用户之外的所有 socket ids
                sids = [
                    sid for sid, username in self.active_connections.items() 
                    if username != exclude
                ]
                for sid in sids:
                    await self.sio.emit('message', message.model_dump(), room=sid)
            else:
                # 广播给所有连接的客户端
                await self.sio.emit('message', message,message.model_dump())
        except Exception as e:
            logging.error(f"广播消息失败: {str(e)}")

    
    async def send_message(self, username:str,
                        message:schemas.MessageBase) -> None:
        user_sids = [
            s for s, u in self.sid_to_user.items() 
            if u.username == username
        ]
        lprint(f"发送消息给{username}",message)
        for user_sid in user_sids:
            await self.sio.emit('message', message.model_dump(), room=user_sid)
    async def send_system_message(self, content: str) -> None:
        print("""发送系统消息""")
        message = {
            'type': 'system',
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        await self.broadcast(message)

    async def broadcast_user_status(self, username: str, login_status: bool) -> None:
        """广播单个用户的在线状态变化"""
        try:
            user = await fetch_user(username)
            if not user:
                return
                
            user_status = {
                "username": user.username,
                "nickname": user.nickname,
                "online": login_status,
                "avatar_index": get_avatar_index(user.username)
            }
            
            message = schemas.MessageBase(
                message_type=schemas.MessageType.USER_STATUS_UPDATE,
                sender="system01",
                recipient="all",
                content=user_status,
                timestamp=datetime.now().astimezone(),  # 使用带时区的时间戳
                status=[schemas.MessageStatus.UNREAD],
                message_content_type=schemas.MessageContentType.USER_STATUS,
            )
            
            # 广播给所有在线用户
            for connection_info in self.active_connections.values():
                await self.sio.emit('message', message.model_dump(), room=connection_info.sid)
                
        except Exception as e:
            logging.error(f"广播用户状态失败: {str(e)}")
            lprint(traceback.format_exc(), popui=False)

    # 处
