"""
WebSocket门面类
提供统一的WebSocket管理接口
"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
from typing import Dict, Set, Optional, TypeAlias, Tuple, cast
import socketio
import traceback
from datetime import datetime
from app.domain.common.models.tables import BaseMessage
import uuid
from app.core.auth.facade.auth_facade import get_auth_facade
import asyncio

from .dto import ConnectionInfo, UserSession, DeviceSession
from ..interfaces import IConnectionManager, IRoomManager
from ..internal.manager import ConnectionManager
from ..internal.manager import RoomManager
from app.core.di.container import Container

lprint = LM.lprint

# 类型别名
SID: TypeAlias = str
UserID: TypeAlias = str
DeviceID: TypeAlias = str

class WebSocketFacade:
    """WebSocket门面类
    
    提供WebSocket相关的功能:
    1. 用户会话管理
    2. 消息广播
    3. 实时通知
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self):
        """初始化WebSocket门面"""
        if not self._initialized:
            self._sio: Optional[socketio.AsyncServer] = None
            # 从容器获取管理器实例
            container = Container()
            self._connection_manager = container.resolve(IConnectionManager)
            self._room_manager = container.resolve(IRoomManager)
            self._initialized = True
            lprint("WebSocket门面初始化完成")
            
    def init_server(self, sio: socketio.AsyncServer):
        """初始化Socket.IO服务器
        
        Args:
            sio: Socket.IO服务器实例
        """
        self._sio = sio
        # 注册事件处理器
        self._register_handlers()
        # 注册/chat命名空间
        self._sio.on('connect', self.connect, namespace='/chat')
        self._sio.on('disconnect', self.disconnect, namespace='/chat')
        lprint("Socket.IO服务器初始化完成")
        
    async def connect(self, sid: str, environ: dict, auth: Optional[dict] = None) -> None:
        """连接事件处理器
        
        Args:
            sid: 会话ID
            environ: WSGI环境
            auth: 认证数据
        """
        try:
            lprint(f"收到连接请求: sid={sid}")
            
            # 从auth获取token
            if not auth or 'token' not in auth:
                lprint(f"认证失败: 未提供token, sid={sid}")
                await self._sio.disconnect(sid)
                return
                
            token = auth['token']
            lprint(f"获取到token: {token}")
            
            # 验证token并获取用户信息
            try:
                user = await get_auth_facade().get_current_user(token)
                if not user:
                    lprint(f"认证失败: 用户验证失败, sid={sid}")
                    await self._sio.disconnect(sid)
                    return
            except Exception as e:
                lprint(f"认证失败: {str(e)}, sid={sid}")
                await self._sio.disconnect(sid)
                return

            # 获取设备信息
            device_id = environ.get('HTTP_X_DEVICE_ID', str(uuid.uuid4()))
            ip_address = environ.get('REMOTE_ADDR', '0.0.0.0')
            
            # 检查是否已经有相同设备的连接
            old_session = next(
                (session for session in self._connection_manager._device_sessions.values()
                 if session.user_id == str(user.id) and session.device_id == device_id),
                None
            )
            
            if old_session:
                lprint(f"发现旧连接: old_sid={old_session.sid}, user_id={user.id}, device_id={device_id}")
                # 断开旧连接
                await self._sio.emit("user_offline", {
                    "user_id": str(user.id),
                    "device_id": old_session.device_id
                })
                # 清理旧连接
                await self.disconnect(old_session.sid)
            
            # 添加新会话
            await self._connection_manager.add_connection(sid, str(user.id), device_id, ip_address)
            lprint(f"新连接建立成功: sid={sid}, user_id={user.id}, device_id={device_id}")
            
            # 发送连接成功事件
            await self._sio.emit("connection_established", {
                "sid": sid,
                "user_id": str(user.id),
                "device_id": device_id
            }, room=sid)

            # 直接尝试加入房间
            await self._auto_join_private_rooms(str(user.id), sid)
        
        except Exception as e:
            lprint(f"处理连接事件失败: {str(e)}")
            lprint(traceback.format_exc())
            await self._sio.disconnect(sid)

    async def _auto_join_private_rooms(self, user_id: str, sid: str):
        """自动将用户加入私聊房间
        
        Args:
            user_id: 用户ID
            sid: 会话ID
        """
        try:
            # 确保会话已连接
            if not self._sio.manager.is_connected(sid, namespace='/chat'):
                lprint(f"会话未连接，等待重试: sid={sid}")
                # 等待一小段时间后重试
                await asyncio.sleep(0.5)
                if not self._sio.manager.is_connected(sid, namespace='/chat'):
                    lprint(f"会话仍未连接，放弃加入房间: sid={sid}")
                    return
                
            # 获取用户的聊天伙伴
            from app.domain.message.facade import get_message_facade
            message_facade = get_message_facade()
            chat_partners = await message_facade.private_repo.get_chat_partners(int(user_id))
            
            # 为每个聊天伙伴创建并加入私聊房间
            for partner_id in chat_partners:
                try:
                    user_ids = sorted([int(user_id), partner_id])
                    room_name = f"private_{user_ids[0]}_{user_ids[1]}"
                    await self._room_manager.join_room(sid, room_name)
                    await self._sio.enter_room(sid, room_name, namespace='/chat')
                    lprint(f"用户 {user_id} 已加入房间: {room_name}")
                except Exception as e:
                    lprint(f"加入房间 {room_name} 失败: {str(e)}")
                    lprint(traceback.format_exc())
                    continue
                    
        except Exception as e:
            lprint(f"自动加入私聊房间失败: {str(e)}")
            lprint(traceback.format_exc())
            
    def _register_handlers(self):
        """注册Socket.IO事件处理器"""
        if not self._sio:
            return
        else:
            # 只注册连接相关的事件
            self._sio.on('connect')(self.connect) # type: ignore
            self._sio.on('disconnect')(self.disconnect) # type: ignore
            
    @property
    def sio(self) -> Optional[socketio.AsyncServer]:
        """获取Socket.IO服务器实例"""
        return self._sio

    async def get_user_id(self, sid: str) -> Optional[str]:
        """获取会话关联的用户ID
        
        Args:
            sid: 会话ID
            
        Returns:
            Optional[str]: 用户ID，如果会话未关联用户则返回None
        """
        try:
            user_id = self._connection_manager.get_user_id(sid)
            if not user_id:
                lprint(f"无法获取用户ID, sid={sid}")
                return None
            return user_id
        except Exception as e:
            lprint(f"获取用户ID失败: {str(e)}, sid={sid}")
            return None
        
    async def broadcast_message(self, message: BaseMessage):
        """广播消息
        
        Args:
            message: 要广播的消息
        """
        try:
            if not self._sio:
                lprint("Socket.IO server not initialized")
                return
                
            if message.group_id is not None:
                # 群组消息广播给所有群成员
                room = f"group_{message.group_id}"
                await self._sio.emit("message", message.dict(), room=room, namespace='/chat')
            else:
                # 私聊消息发送到对应的私聊房间
                user_ids = sorted([str(message.sender_id), str(message.recipient_id)])
                room_name = f"private_{user_ids[0]}_{user_ids[1]}"
                await self._sio.emit("message", message.dict(), room=room_name, namespace='/chat')
                    
        except Exception as e:
            lprint(f"广播消息失败: {str(e)}")
            raise

    async def disconnect(self, sid: SID):
        """断开连接
        
        Args:
            sid: 会话ID
        """
        try:
            # 获取会话信息用于日志
            user_id = await self.get_user_id(sid)
            device_session = self._connection_manager.get_device_session(sid)
            device_id = device_session.device_id if device_session else "unknown"
            
            lprint(f"开始断开连接: sid={sid}, user_id={user_id}, device_id={device_id}")
            
            # 清理房间记录
            await self._room_manager.remove_sid(sid)
            
            # 移除会话
            await self._connection_manager.remove_connection(sid)
            
            # 发送离线通知
            if user_id:
                await self._sio.emit("user_offline", {
                    "user_id": user_id,
                    "device_id": device_id
                })
                
            lprint(f"连接断开成功: sid={sid}, user_id={user_id}, device_id={device_id}")
            
        except Exception as e:
            lprint(f"断开连接失败: {str(e)}, sid={sid}")
            traceback.print_exc()

    def is_connected(self, user_id: str) -> bool:
        """检查用户是否在线
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否在线
        """
        return self._connection_manager.is_user_online(user_id)
        
    async def emit_to_user(self, user_id: UserID, event: str, data: dict):
        """向指定用户发送事件
        
        Args:
            user_id: 用户ID
            event: 事件名称
            data: 事件数据
        """
        if not self._sio:
            lprint("Socket.IO server not initialized")
            return
            
        for sid in self._connection_manager.get_user_connections(user_id):
            await self._sio.emit(event, data, room=sid, namespace='/chat')
                
    async def broadcast_to_users(self, user_ids: Set[str], event: str, data: dict):
        """向多个用户广播事件
        
        Args:
            user_ids: 用户ID集合
            event: 事件名称
            data: 事件数据
        """
        for user_id in user_ids:
            await self.emit_to_user(user_id, event, data)
            
    async def broadcast_to_all(self, event: str, data: dict):
        """向所有连接的用户广播事件
        
        Args:
            event: 事件名称
            data: 消息数据
        """
        if not self._sio:
            lprint("Socket.IO server not initialized")
            return
            
        await self._sio.emit(event, data)
        
    async def join_group(self, user_id: str, group: str):
        """用户加入群组
        
        Args:
            user_id: 用户ID
            group: 群组名称
        """
        if not self._sio:
            lprint("Socket.IO server not initialized")
            return
            
        room = f"group_{group}"
        # 将用户的所有会话加入群组
        for sid in self._connection_manager.get_user_connections(user_id):
            await self._room_manager.join_room(sid, room)
            await self._sio.enter_room(sid, room)
                
    async def leave_group(self, user_id: str, group: str):
        """用户离开群组
        
        Args:
            user_id: 用户ID
            group: 群组名称
        """
        if not self._sio:
            lprint("Socket.IO server not initialized")
            return
            
        room = f"group_{group}"
        # 将用户的所有会话离开群组
        for sid in self._connection_manager.get_user_connections(user_id):
            await self._room_manager.leave_room(sid, room)
            await self._sio.leave_room(sid, room)
                
    async def broadcast_to_group(self, group: str, event: str, data: dict):
        """向群组广播消息
        
        Args:
            group: 群组名
            event: 事件名
            data: 消息数据
        """
        if not self._sio:
            lprint("Socket.IO server not initialized")
            return
            
        room = f"group_{group}"
        await self._sio.emit(event, data, room=room, namespace='/chat')
            
    def get_group_members(self, group: str) -> Set[str]:
        """获取群组成员
        
        Args:
            group: 群组名
            
        Returns:
            Set[str]: 群组成员ID集合
        """
        room = f"group_{group}"
        return self._room_manager.get_room_members(room)
        
    def get_user_groups(self, user_id: str) -> Set[str]:
        """获取用户加入的群组
        
        Args:
            user_id: 用户ID
            
        Returns:
            Set[str]: 群组名集合
        """
        groups = set()
        for sid in self._connection_manager.get_user_connections(user_id):
            for room in self._room_manager.get_user_rooms(sid):
                if room.startswith("group_"):
                    groups.add(room[6:])  # 移除"group_"前缀
        return groups

    async def get_session(self, sid: str) -> Optional[DeviceSession]:
        """获取会话信息
        
        Args:
            sid: 会话ID
            
        Returns:
            Optional[DeviceSession]: 会话信息，如果不存在则返回None
        """
        try:
            return self._connection_manager.get_device_session(sid)
        except Exception as e:
            lprint(f"获取会话信息失败: {str(e)}, sid={sid}")
            return None
