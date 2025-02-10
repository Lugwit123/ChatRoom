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

from .dto import SessionManager, ConnectionInfo, UserSession, DeviceSession

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
        if not self._initialized:
            self._sio: socketio.AsyncServer
            self._session_manager = SessionManager()  # 使用新的会话管理器
            self.group_members: Dict[str, Set[UserID]] = {}  # group -> members
            self._initialized = True
            
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
        lprint("WebSocket门面初始化完成")
        
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
                (session for session in self._session_manager.device_sessions.values()
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
            self._session_manager.add_session(sid, str(user.id), device_id, ip_address)
            lprint(f"新连接建立成功: sid={sid}, user_id={user.id}, device_id={device_id}")
            
            # 发送连接成功事件
            await self._sio.emit("connection_established", {
                "sid": sid,
                "user_id": str(user.id),
                "device_id": device_id
            }, room=sid)
            
            # 获取用户的聊天伙伴
            from app.domain.message.facade import get_message_facade
            message_facade = get_message_facade()
            chat_partners = await message_facade.private_repo.get_chat_partners(user.id)
            lprint(f"获取到用户 {user.username} 的聊天伙伴: {chat_partners}")
            
            # 构建房间列表
            rooms = []
            for partner_id in chat_partners:
                user_ids = sorted([user.id, partner_id])
                room_name = f"private_{user_ids[0]}_{user_ids[1]}"
                rooms.append({"room_name": room_name})
                lprint(f"创建私聊房间: {room_name}")
                
            # 发送房间分配消息
            await self._sio.emit("room_assigned", {
                "rooms": rooms
            }, namespace='/chat')
            lprint(f"已发送房间分配消息: rooms={rooms},命名空间是")

        except Exception as e:
            lprint(f"处理连接事件失败: {str(e)}")
            lprint(traceback.format_exc())
            await self._sio.disconnect(sid)
        
    def _register_handlers(self):
        """注册Socket.IO事件处理器"""
        if not self._sio:
            return
        else:
            # 注册连接事件处理器
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
            user_id = self._session_manager.get_user_id(sid)
            if not user_id:
                lprint(f"无法获取用户ID, sid={sid}")
                return None
            return user_id
        except Exception as e:
            lprint(f"获取用户ID失败: {str(e)}, sid={sid}")
            return None
        
    async def set_user_id(self, sid: str, user_id: str):
        """设置会话关联的用户ID
        
        Args:
            sid: 会话ID
            user_id: 用户ID
        """
        try:
            # 检查是否已经存在映射
            existing_user_id = await self.get_user_id(sid)
            if existing_user_id:
                if existing_user_id != user_id:
                    lprint(f"会话已关联其他用户, sid={sid}, existing_user={existing_user_id}, new_user={user_id}")
                return
                
            # 添加新的映射
            self._session_manager.sid_to_user[sid] = user_id
            if user_id not in self._session_manager.user_sessions:
                self._session_manager.user_sessions[user_id] = UserSession(user_id=user_id)
            self._session_manager.user_sessions[user_id].add_sid(sid)
            lprint(f"设置用户ID成功: sid={sid}, user_id={user_id}")
            
        except Exception as e:
            lprint(f"设置用户ID失败: {str(e)}, sid={sid}, user_id={user_id}")
        
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
                # 私聊消息只发送给接收者
                recipient_sids = self._session_manager.get_user_sids(str(message.recipient_id))
                for sid in recipient_sids:
                    await self._sio.emit("message", message.dict(), room=sid, namespace='/chat')
                    
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
            device_session = self._session_manager.get_device_session(sid)
            device_id = device_session.device_id if device_session else "unknown"
            
            lprint(f"开始断开连接: sid={sid}, user_id={user_id}, device_id={device_id}")
            
            # 移除会话
            self._session_manager.remove_session(sid)
            
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
        return self._session_manager.is_user_online(user_id)
        
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
            
        for sid in self._session_manager.get_user_sids(user_id):
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
            
        if group not in self.group_members:
            self.group_members[group] = set()
        self.group_members[group].add(user_id)
        
        # 将用户的所有会话加入群组
        for sid in self._session_manager.get_user_sids(user_id):
            await self._sio.enter_room(sid, group)
                
    async def leave_group(self, user_id: str, group: str):
        """用户离开群组
        
        Args:
            user_id: 用户ID
            group: 群组名称
        """
        if not self._sio:
            lprint("Socket.IO server not initialized")
            return
            
        if group in self.group_members:
            self.group_members[group].discard(user_id)
            if not self.group_members[group]:
                del self.group_members[group]
                
        # 将用户的所有会话离开群组
        for sid in self._session_manager.get_user_sids(user_id):
            await self._sio.leave_room(sid, group)
                
    async def broadcast_to_group(self, group: str, event: str, data: dict):
        """向群组广播消息
        
        Args:
            group: 群组名
            event: 事件名
            data: 消息数据
        """
        if group in self.group_members:
            await self.broadcast_to_users(self.group_members[group], event, data)
            
    def get_group_members(self, group: str) -> Set[str]:
        """获取群组成员
        
        Args:
            group: 群组名
            
        Returns:
            Set[str]: 群组成员ID集合
        """
        return self.group_members.get(group, set())
        
    def get_user_groups(self, user_id: str) -> Set[str]:
        """获取用户加入的群组
        
        Args:
            user_id: 用户ID
            
        Returns:
            Set[str]: 群组名集合
        """
        return {
            group for group, members in self.group_members.items()
            if user_id in members
        }
