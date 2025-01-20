from typing import Dict, Any, Callable,Optional,cast
from datetime import datetime
import logging
import traceback
from fastapi import WebSocket, HTTPException
import socketio
import schemas
import json

from authenticate import authenticate_token
from schemas import (
    MessageBase, MessageType, UserBase, MessageBase, 
    UserBase, MessageContentType, UserListResponse,
    GroupResponse, UserResponse,
)
from connection_manager import ConnectionManager
import user_database
from utils import get_avatar_index
import Lugwit_Module as LM
lprint = LM.lprint


class MessageHandlers:
    def __init__(self, connection_manager: ConnectionManager, sio: socketio.AsyncServer):
        self.connection_manager = connection_manager
        self.sio = sio
        self.setup_socketio_handlers()

    def setup_socketio_handlers(self):
        print("只保留必要的事件处理器")
        self.sio.on('connect', self.handle_connect)
        self.sio.on('disconnect', self.handle_disconnect)
        self.sio.on('message', self.handle_message)  # 统一的消息处理入口


    async def handle_connect(self, sid: str, environ: dict, auth: dict):
        print("""处理连接事件""")
        try:
            # 从ASGI scope中获取客户端IP
            scope = environ.get('asgi.scope', {})
            client = scope.get('client', None)
            client_ip = client[0] if client else 'unknown'
            
            token = auth.get('token')
            if not token:
                lprint(f"Socket.IO连接失败: 缺少token, sid={sid}, ip={client_ip}", popui=False)
                await self.sio.emit('authentication_response', {
                    'success': False,
                    'error': 'No token provided'
                }, room=sid)
                return False

            # 验证用户并存储连接信息
            user = await authenticate_token(token)
            if not user:
                lprint(f"认证失败: 无效的token, sid={sid}, ip={client_ip}", popui=False)
                await self.sio.emit('authentication_response', {
                    'success': False,
                    'error': 'Invalid token'
                }, room=sid)
                return False

            # 存储连接信息
            success = await self.connection_manager.connect(sid, user.username, client_ip)
            if not success:
                lprint(f"存储连接信息失败, sid={sid}, ip={client_ip}", popui=False)
                await self.sio.emit('authentication_response', {
                    'success': False,
                    'error': 'Failed to store connection'
                }, room=sid)
                return False

            # 发送认证成功响应
            await self.sio.emit('authentication_response', {
                'success': True,
                'sid': sid,
                'username': user.username
            }, room=sid)

            # 发送初始数据
            await self.send_initial_data(sid, user)

            lprint(f"✅ 用户 {user.username} 从IP {client_ip} 连接成功", popui=False)
            return True

        except Exception as e:
            lprint(traceback.format_exc(), popui=False)
            await self.sio.emit('authentication_response', {
                'success': False,
                'error': 'Internal server error'
            }, room=sid)
            return False

    async def handle_disconnect(self, sid: str):
        print("""处理断开连接事件""")
        username = self.connection_manager.get_username(sid)
        if username:
            await self.connection_manager.disconnect(sid)
            await self.broadcast_user_status_change(username, False)
            await self.connection_manager.send_system_message(f"{username} 已离开聊��室!")
            await self.connection_manager.broadcast_user_list()

    
    async def handle_message(self, sid: str, data: str | bytes | dict):
        lprint(f"统一的消息处理入口收到消息类型: {type(data)}, 数据: {data}")
        try:
            # 统一数据格式处理
            if isinstance(data, bytes):
                data = data.decode('utf8')
            if isinstance(data,str):
                message=MessageBase.model_validate_json(data,
                                                    strict= False)
            elif isinstance(data,dict):
                message=MessageBase.model_validate(data,
                                                    strict= False)


            # 验证发送者身份
            user = self.connection_manager.sid_to_user.get(sid)
            if not user:
                lprint(f"❌ 消息处理失败: 未找到用户信息 sid={sid}")
                return {'status': 'failed', 'error': 'User not found'}
            
            message.status = [schemas.MessageStatus.SUCCESS]
            message.recipient_type='private'
            message_from_database = await user_database.insert_message(message)
            
            # 处理消息
            handlers = {
                MessageType.PRIVATE_CHAT.value: self.handle_private_message,
                MessageType.GROUP_CHAT.value: self.handle_group_message,
                MessageType.GET_USERS.value: self.handle_get_users,
                MessageType.VALIDATION.value: self.handle_validation,
                MessageType.REMOTE_CONTROL.value: self.handle_private_message,
            }
            
            handler = handlers.get(message_from_database.message_type)
            if handler:
                return (await handler(sid, message_from_database)).model_dump()
            else:
                return {'status': 'failed', 'error': 'Unknown message type'}
            
        except Exception as e:
            lprint(traceback.format_exc(), popui=False)
            return {'status': 'failed', 'error': str(e)}

    async def handle_validation(self, sid: str, data: MessageBase,):
        lprint("消息验证",data)
        data.direction=schemas.MessageDirection.RESPONSE
        data.status=[schemas.MessageStatus.SUCCESS]
        recipient = data.recipient
        lprint(recipient,self.connection_manager.sid_to_user)
        if recipient:
            await self.connection_manager.send_message(str(recipient), data)
        return data

    
    

    async def handle_private_message(self, sid: str, data: MessageBase,):
        print("处理私聊消息,sid : 发送者sid")
        try:
            data.status=[schemas.MessageStatus.SUCCESS]
            return await self.connection_manager.\
                send_with_retry(data)
        except Exception as e:
            lprint(traceback.format_exc(), popui=False)

    async def handle_group_message(self, sid: str, data: dict):
        print("""处理群组消息""")
        try:
            user = await self.connection_manager.get_user(sid)
            if not user:
                logging.error(f"群组消息处理失败: 未找到用户, sid={sid}")
                return

            message = MessageBase(**data)
            group = message.recipient

            if group not in [g.name for g in user.groups]:
                logging.error(f"用户 {user.username} 不属于群组 '{group}'")
                return

            # 保存消息到数据库并获取消息ID
            # message_id = await user_database.insert_message(
            #     sender=user.username,
            #     recipient=group,
            #     content=message.content,
            #     timestamp=datetime.fromisoformat(data.get('timestamp')),
            #     msg_type='group'
            # )
            


            # 发送群组消息
            await self.connection_manager.send_group_message(message, group)

        except Exception as e:
            logging.error(f"处理群组消息时出错: {e}")
            logging.error(traceback.format_exc())

    async def handle_get_users(self, sid: str, data: dict,callback:Optional[Callable]=None):
        print("""处理获取用户列表请求""")
        try:
            lprint(f"处理获取用户列表请求 - sid: {sid}", popui=False)
            
            # 获取当前用户
            current_user = await self.connection_manager.get_user(sid)
            if not current_user:
                lprint("错误: 未认证的用户请求", popui=False)
                raise HTTPException(status_code=401, detail="未认证")

            # 获取用户列表和群组信息
            users = await user_database.fetch_registered_users(
                current_username=current_user.username,
                exclude_types=[]
            )
            groups = await user_database.get_all_groups_info()

            # 构造响应消息
            response = MessageBase(
                sender='system',
                recipient=current_user.username,
                content={
                    'user_list': users,  # 不必转换为字典
                    'groups': groups  # 不必转换为字典
                },
                timestamp=datetime.now(),
                recipient_type='private',
                message_type=MessageType.USER_LIST_UPDATE,
                status=[schemas.MessageStatus.SUCCESS],
                message_content_type=MessageContentType.USER_LIST
            )

            # 发送响应
            try:
                response_json = response.model_dump_json()
                await self.sio.emit('message', response_json, room=sid)
                lprint(f"✅ 用户列表已发送到 sid: {sid}", traceback.format_exc(), popui=False)
            except Exception as e:
                lprint(f"❌ 发送用户列表失败: {str(e)}", traceback.format_exc(),popui=False)
                raise Exception(traceback.format_exc())

        except Exception as e:
            lprint(traceback.format_exc(), popui=False)
            # 发送错误消息给客户端
            error_message = {
                'type': 'error',
                'content': f"获取用户列表失败: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
            await self.sio.emit('message', error_message, room=sid)

    async def send_initial_data(self, sid: str, user: UserBase):
        print("发送初始数据给新连接的用户")
        try:
            users_in_db = await user_database.fetch_registered_users(
                current_username=user.username,
                exclude_types=[]
            )
            groups = await user_database.get_all_groups_info()

            # 发送用户列表更新
            serializable_users = [
                {
                    "id": user.id,
                    "username": user.username,
                    "nickname": user.nickname,
                    "email": user.email,
                    "role": user.role.value,
                    "avatar_index": user.avatar_index,
                    "online": user.username in self.connection_manager.active_connections,
                    "unread_message_count": 0,
                    "groups": user.groups
                }
                for user in users_in_db
            ]

            user_list_update = MessageBase(
                sender='system01',
                message_type=MessageType.USER_LIST_UPDATE,
                recipient=list(self.connection_manager.active_connections.keys()),
                timestamp=datetime.now(),
                content={
                    "user_list": serializable_users,
                    "groups": groups
                },
                direction=schemas.MessageDirection.RESPONSE,
                status=[schemas.MessageStatus.SUCCESS]
            )
            await self.sio.emit('message', user_list_update.model_dump_json(), room=sid)

            # 发送聊天历史
            await self.send_chat_histories(sid, user, users_in_db)

        except Exception as e:
            logging.error(f"发送初始数据失败: {e}")
            logging.error(traceback.format_exc())

    async def send_chat_histories(self, sid: str, user: UserBase, users_in_db: list):
        print("""发送聊天历史记录""")
        try:
            # 发送用户聊天历史
            for other_user in users_in_db:
                try:
                    chat_history = await user_database.get_chat_history(other_user.username, user)
                    if chat_history:
                        history_message = MessageBase(
                            message_type=MessageType.CHAT_HISTORY,
                            sender=other_user.username,
                            recipient=user.username,
                            content=chat_history.model_dump() if hasattr(chat_history, 'model_dump') else chat_history,
                            timestamp=datetime.now(),
                            status=[schemas.MessageStatus.SUCCESS]
                        )
                        await self.sio.emit('message', history_message.model_dump_json(), room=sid)
                except Exception as e:
                    logging.error(traceback.format_exc(),history_message)
                    continue

            # 发送群组聊天历史
            for group_info in user.groups:
                try:
                    chat_history = await user_database.get_chat_history(group_info.name, user)
                    if chat_history:
                        history_message = MessageBase(
                            message_type=MessageType.CHAT_HISTORY,
                            sender="system",
                            recipient=group_info.name,
                            recipient_type="group",
                            content=chat_history.model_dump() if hasattr(chat_history, 'model_dump') else chat_history,
                            timestamp=datetime.now(),
                            status=[schemas.MessageStatus.SUCCESS]
                        )
                        await self.sio.emit('message', history_message.model_dump_json(), room=sid)
                except Exception as e:
                    logging.error(f"发送群组 {group_info.name} 的聊天历史失: {e}")
                    continue

        except Exception as e:
            logging.error(f"发送聊天历史任务失败: {e}")
            logging.error(traceback.format_exc())

    async def broadcast_user_status_change(self, username: str, login_status: bool):
        print("""广播用户状态变化""")
        status_message = MessageBase(
            sender="system",
            message_type=MessageType.USER_LIST_UPDATE,
            recipient="all",
            content={
                "user_list": [{
                    "username": username,
                    "online": login_status
                }]
            },
            timestamp=datetime.now(),
            status=[schemas.MessageStatus.SUCCESS]
        )
        await self.connection_manager.broadcast(status_message) 