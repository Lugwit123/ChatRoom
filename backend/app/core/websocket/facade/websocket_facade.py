"""
WebSocket门面类
提供统一的WebSocket管理接口
"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
from typing import Dict, Set, Optional, TypeAlias, Tuple, cast, Any
import socketio
import traceback
from datetime import datetime
import asyncio
from app.domain.common.models.tables import BaseMessage
import uuid
import time
from collections import defaultdict

from .dto import ConnectionInfo, UserSession, DeviceSession
from ..interfaces import IConnectionManager, IRoomManager
from ..internal.manager import ConnectionManager
from ..internal.manager import RoomManager
from app.core.di.container import Container
from app.core.services import Services
from app.core.events.interfaces import (
    EventType, WebSocketEvent, UserEvent, MessageEvent, DeviceEvent,
    Event, EventHandler
)
from .metrics import Metrics

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
    _MAX_RETRIES = 3
    _RETRY_DELAY = 1.0  # seconds
    
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
            # 获取事件总线服务
            self._event_bus = Services.get_event_bus()
            # 初始化指标收集器
            self._metrics = Metrics()
            self._event_queue = asyncio.PriorityQueue()
            self._initialized = True
            # 注册事件处理器
            self._register_event_handlers()
            # 启动事件处理循环
            asyncio.create_task(self._event_processing_loop())
            lprint("WebSocket门面初始化完成")
            
    async def _event_processing_loop(self):
        """事件处理循环"""
        while True:
            try:
                priority, (handler_name, event) = await self._event_queue.get()
                start_time = time.time()
                
                try:
                    await self._safe_event_handler(handler_name, event)
                    latency = time.time() - start_time
                    self._metrics.record_event(event.event_type.value, latency)
                    
                    self._log(
                        "事件处理完成",
                        event_type=event.event_type.value,
                        latency=latency,
                        priority=priority
                    )
                except Exception as e:
                    self._metrics.record_error(f"event_processing_{event.event_type.value}")
                    self._log(
                        "事件处理失败",
                        level="error",
                        event_type=event.event_type.value,
                        error=str(e)
                    )
                finally:
                    self._event_queue.task_done()
                    self._metrics.record_queue_size(self._event_queue.qsize())
                    
            except Exception as e:
                self._metrics.record_error("event_loop_error")
                self._log(
                    "事件处理循环错误",
                    level="error",
                    error=str(e)
                )
                await asyncio.sleep(1)  # 避免错误循环过快

    def _log(self, message: str, level: str = "info", **kwargs) -> None:
        """结构化日志记录
        
        Args:
            message: 日志消息
            level: 日志级别
            **kwargs: 额外的日志字段
        """
        log_data = {
            "module": "WebSocketFacade",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }

    async def _safe_event_handler(self, handler_name: str, event: Event) -> None:
        """安全地执行事件处理器"""
        for attempt in range(self._MAX_RETRIES):
            try:
                handler = getattr(self, handler_name)
                await handler(event)
                self._log(
                    "事件处理成功",
                    handler=handler_name,
                    event_type=event.event_type.value
                )
                return
            except Exception as e:
                self._log(
                    "事件处理失败",
                    level="error",
                    handler=handler_name,
                    event_type=event.event_type.value,
                    attempt=attempt + 1,
                    error=str(e)
                )
                if attempt < self._MAX_RETRIES - 1:
                    await asyncio.sleep(self._RETRY_DELAY)
                continue
        self._log(
            "事件处理最终失败",
            level="error",
            handler=handler_name,
            event_type=event.event_type.value
        )

    def _register_event_handlers(self):
        """注册事件处理器"""
        # 定义事件优先级 (数字越小优先级越高)
        priorities = {
            EventType.USER_LOGIN: 1,
            EventType.USER_LOGOUT: 1,
            EventType.USER_STATUS_CHANGED: 2,
            EventType.MESSAGE_SENT: 3,
            EventType.MESSAGE_RECEIVED: 3,
            EventType.DEVICE_CONNECTED: 2,
            EventType.DEVICE_DISCONNECTED: 2,
            EventType.WEBSOCKET_CONNECTED: 1,
            EventType.WEBSOCKET_DISCONNECTED: 1
        }
        
        # 用户相关事件
        for event_type, priority in priorities.items():
            handler_name = f"_handle_{event_type.value.replace('.', '_')}"
            self._event_bus.subscribe(
                event_type.value,  # 使用事件类型的值
                lambda e, h=handler_name, p=priority: asyncio.create_task(
                    self._event_queue.put((p, (h, e)))
                )
            )
            
    async def _handle_websocket_disconnected(self, event: Event) -> None:
        """处理WebSocket断开连接事件"""
        if not isinstance(event, WebSocketEvent) or not self._sio:
            return
            
        try:
            await self._safe_emit("state", {
                "type": "websocket_disconnected",
                "sid": event.sid,
                "user_id": event.user_id,
                "device_id": event.device_id,
                "timestamp": datetime.now().isoformat()
            })
            lprint(f"连接断开成功: sid={event.sid}, user_id={event.user_id}, device_id={event.device_id}")
        except Exception as e:
            lprint(f"处理WebSocket断开连接事件失败: {str(e)}")
            lprint(traceback.format_exc())

    def init_server(self, sio: socketio.AsyncServer):
        """初始化Socket.IO服务器
        
        Args:
            sio: Socket.IO服务器实例
        """
        if not self._sio:
            self._sio = sio
            # 注册事件处理器
            self._register_handlers()
            # 注册/chat命名空间
            self._sio.on('connect', self.connect, namespace='/chat')
            self._sio.on('disconnect', self.disconnect, namespace='/chat')
            lprint("Socket.IO服务器初始化完成")
        
    async def _safe_emit(self, event: str, data: Dict[str, Any], room: Optional[str] = None, namespace: str = '/chat') -> bool:
        """安全地发送事件，包含重试机制"""
        if not self._sio:
            self._log("Socket.IO server not initialized", level="error")
            return False

        for attempt in range(self._MAX_RETRIES):
            try:
                if room:
                    await self._sio.emit(event, data, room=room, namespace=namespace)
                else:
                    await self._sio.emit(event, data, namespace=namespace)
                self._log("事件发送成功", event=event, room=room, data=data)
                return True
            except Exception as e:
                self._log(
                    "发送事件失败",
                    level="error",
                    event=event,
                    room=room,
                    attempt=attempt + 1,
                    error=str(e)
                )
                if attempt < self._MAX_RETRIES - 1:
                    await asyncio.sleep(self._RETRY_DELAY)
                continue
        return False

    async def _safe_disconnect(self, sid: str) -> bool:
        """安全地断开连接
        
        Args:
            sid: 会话ID
            
        Returns:
            bool: 是否成功断开
        """
        if not self._sio:
            return False
            
        try:
            await self._sio.disconnect(sid)
            return True
        except Exception as e:
            lprint(f"断开连接失败: {str(e)}")
            return False

    async def _safe_manager_operation(self, operation: str, *args, **kwargs) -> bool:
        """安全地执行连接管理器操作
        
        Args:
            operation: 操作名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            bool: 操作是否成功
        """
        for attempt in range(self._MAX_RETRIES):
            try:
                operation_func = getattr(self._connection_manager, operation)
                await operation_func(*args, **kwargs)
                return True
            except Exception as e:
                lprint(f"连接管理器操作失败 ({operation}) (尝试 {attempt + 1}/{self._MAX_RETRIES}): {str(e)}")
                if attempt < self._MAX_RETRIES - 1:
                    await asyncio.sleep(self._RETRY_DELAY)
                continue
        return False

    async def _safe_room_operation(self, operation: str, *args, **kwargs) -> bool:
        """安全地执行房间管理器操作
        
        Args:
            operation: 操作名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            bool: 操作是否成功
        """
        for attempt in range(self._MAX_RETRIES):
            try:
                operation_func = getattr(self._room_manager, operation)
                await operation_func(*args, **kwargs)
                return True
            except Exception as e:
                lprint(f"房间管理器操作失败 ({operation}) (尝试 {attempt + 1}/{self._MAX_RETRIES}): {str(e)}")
                if attempt < self._MAX_RETRIES - 1:
                    await asyncio.sleep(self._RETRY_DELAY)
                continue
        return False

    async def _safe_socket_operation(self, operation: str, *args, **kwargs) -> bool:
        """安全地执行Socket.IO操作
        
        Args:
            operation: 操作名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            bool: 操作是否成功
        """
        if not self._sio:
            return False
            
        for attempt in range(self._MAX_RETRIES):
            try:
                operation_func = getattr(self._sio, operation)
                await operation_func(*args, **kwargs)
                return True
            except Exception as e:
                lprint(f"Socket.IO操作失败 ({operation}) (尝试 {attempt + 1}/{self._MAX_RETRIES}): {str(e)}")
                if attempt < self._MAX_RETRIES - 1:
                    await asyncio.sleep(self._RETRY_DELAY)
                continue
        return False

    async def _is_connected(self, sid: str, namespace: str = '/chat') -> bool:
        """检查会话是否连接
        
        Args:
            sid: 会话ID
            namespace: 命名空间
            
        Returns:
            bool: 是否连接
        """
        if not self._sio or not hasattr(self._sio, 'manager'):
            return False
        return bool(self._sio.manager.is_connected(sid, namespace))

    async def connect(self, sid: str, environ: dict, auth: Optional[dict] = None) -> None:
        """连接事件处理器"""
        try:
            lprint(f"收到连接请求: sid={sid}")
            
            if not auth or 'token' not in auth:
                self._metrics.record_error("auth_missing")
                lprint(f"认证失败: 未提供token, sid={sid}")
                await self._safe_disconnect(sid)
                return
                
            token = auth['token']
            
            try:
                from app.core.auth.facade.auth_facade import get_auth_facade
                user = await get_auth_facade().get_current_user(token)
                if not user:
                    self._metrics.record_error("auth_failed")
                    lprint(f"认证失败: 用户验证失败, sid={sid}")
                    await self._safe_disconnect(sid)
                    return
            except Exception as e:
                self._metrics.record_error("auth_error")
                lprint(f"认证失败: {str(e)}, sid={sid}")
                await self._safe_disconnect(sid)
                return

            device_id = environ.get('HTTP_X_DEVICE_ID', str(uuid.uuid4()))
            ip_address = environ.get('REMOTE_ADDR', '0.0.0.0')
            
            websocket_event = WebSocketEvent(
                event_type=EventType.WEBSOCKET_CONNECTED,
                sid=sid,
                user_id=user.id,
                device_id=device_id,
                data={
                    'ip_address': ip_address,
                    'user_info': user.dict()
                }
            )
            self._event_bus.publish_event(websocket_event)
            
            if not await self._safe_manager_operation('add_connection', sid, str(user.id), device_id, ip_address):
                self._metrics.record_error("connection_add_failed")
                lprint(f"添加连接失败: sid={sid}")
                await self._safe_disconnect(sid)
                return
                
            self._metrics.update_connections(1)
            lprint(f"新连接建立成功: sid={sid}, user_id={user.id}, device_id={device_id}")
            
            success = await self._safe_emit("connection_established", {
                "sid": sid,
                "user_id": str(user.id),
                "device_id": device_id
            }, room=sid)
            
            if success:
                await self._auto_join_private_rooms(str(user.id), sid)
            else:
                self._metrics.record_error("connection_event_failed")
                lprint(f"发送连接成功事件失败: sid={sid}")
                await self._safe_disconnect(sid)
        
        except Exception as e:
            self._metrics.record_error("connection_error")
            lprint(f"处理连接事件失败: {str(e)}")
            lprint(traceback.format_exc())
            await self._safe_disconnect(sid)

    async def _auto_join_private_rooms(self, user_id: str, sid: str):
        """自动将用户加入私聊房间"""
        try:
            # 确保会话已连接
            if not await self._is_connected(sid):
                lprint(f"会话未连接，等待重试: sid={sid}")
                await asyncio.sleep(0.5)
                if not await self._is_connected(sid):
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
                    
                    # 使用安全的房间操作
                    if await self._safe_room_operation('join_room', sid, room_name):
                        if await self._safe_socket_operation('enter_room', sid, room_name, namespace='/chat'):
                            lprint(f"用户 {user_id} 已加入房间: {room_name}")
                        else:
                            lprint(f"加入Socket.IO房间失败: {room_name}")
                    else:
                        lprint(f"加入房间管理器失败: {room_name}")
                        
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
        """断开连接"""
        try:
            user_id = await self.get_user_id(sid)
            device_session = self._connection_manager.get_device_session(sid)
            device_id = device_session.device_id if device_session else "unknown"
            
            websocket_event = WebSocketEvent(
                event_type=EventType.WEBSOCKET_DISCONNECTED,
                sid=sid,
                user_id=int(user_id) if user_id else None,
                device_id=device_id
            )
            await self._event_bus.publish_event(websocket_event)
            
            lprint(f"开始断开连接: sid={sid}, user_id={user_id}, device_id={device_id}")
            
            await self._safe_room_operation('remove_sid', sid)
            await self._safe_manager_operation('remove_connection', sid)
            
            self._metrics.update_connections(-1)
            
            if user_id:
                await self._safe_emit("state", {
                    "type": "user_offline",
                    "user_id": user_id,
                    "device_id": device_id,
                    "timestamp": datetime.now().isoformat()
                })
                
            lprint(f"连接断开成功: sid={sid}, user_id={user_id}, device_id={device_id}")
            
        except Exception as e:
            self._metrics.record_error("disconnect_error")
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
        """向指定用户发送事件"""
        if not self._sio:
            lprint("Socket.IO server not initialized")
            return
            
        success = False
        for sid in self._connection_manager.get_user_connections(user_id):
            if await self._safe_emit(event, data, room=sid):
                success = True
        
        if not success:
            lprint(f"向用户 {user_id} 发送事件 {event} 失败")

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

    # 事件处理器
    async def _handle_user_login(self, event: Event) -> None:
        """处理用户登录事件"""
        if not isinstance(event, UserEvent) or not self._sio:
            return
        await self._safe_emit("state", {
            "type": "user_login",
            "user_id": event.user_id,
            "username": event.username,
            "timestamp": event.created_at.isoformat(),
            **event.data
        })

    async def _handle_user_logout(self, event: Event) -> None:
        """处理用户登出事件"""
        if not isinstance(event, UserEvent) or not self._sio:
            return
        await self._safe_emit("state", {
            "type": "user_logout",
            "user_id": event.user_id,
            "username": event.username,
            "timestamp": event.created_at.isoformat(),
            **event.data
        })

    async def _handle_user_status_change(self, event: Event) -> None:
        """处理用户状态变更事件"""
        if not isinstance(event, UserEvent) or not self._sio:
            return
        await self._safe_emit("state", {
            "type": "user_status",
            "user_id": event.user_id,
            "username": event.username,
            "timestamp": event.created_at.isoformat(),
            **event.data
        })

    async def _handle_message_sent(self, event: Event) -> None:
        """处理消息发送事件"""
        start_time = time.time()
        if not isinstance(event, MessageEvent) or not self._sio:
            return
            
        message_data = {
            **event.data,
            "message_id": event.message_id,
            "sender_id": event.sender_id,
            "recipient_id": event.recipient_id,
            "group_id": event.group_id,
            "timestamp": event.created_at.isoformat()
        }

        success = False
        try:
            if event.group_id is not None:
                room = f"group_{event.group_id}"
                success = await self._safe_emit("message", message_data, room=room)
                if success:
                    self._metrics.record_message("group")
            else:
                user_ids = sorted([str(event.sender_id), str(event.recipient_id)])
                room_name = f"private_{user_ids[0]}_{user_ids[1]}"
                success = await self._safe_emit("message", message_data, room=room_name)
                if success:
                    self._metrics.record_message("private")
                
            if not success:
                self._log(f"发送消息失败: message_id={event.message_id}")
                self._metrics.record_error("message_send_failed")
            else:
                latency = time.time() - start_time
                self._metrics.record_event("message_sent", latency)
                
        except Exception as e:
            self._log(
                "消息发送异常",
                level="error",
                message_id=event.message_id,
                error=str(e)
            )
            self._metrics.record_error("message_send_error")

    async def _handle_message_received(self, event: Event) -> None:
        """处理消息接收事件"""
        if not isinstance(event, MessageEvent) or not self._sio:
            return
            
        receipt_data = {
            "type": "receipt",
            "message_id": event.message_id,
            "recipient_id": event.recipient_id,
            "timestamp": event.created_at.isoformat()
        }
        
        success = await self._safe_emit("message", receipt_data, room=str(event.sender_id))
        if not success:
            lprint(f"发送消息回执失败: message_id={event.message_id}")

    async def _handle_device_connected(self, event: Event) -> None:
        """处理设备连接事件"""
        if not isinstance(event, DeviceEvent) or not self._sio:
            return
        await self._safe_emit("state", {
            "type": "device_connected",
            "user_id": event.user_id,
            "device_id": event.device_id,
            "ip_address": event.ip_address,
            "timestamp": event.created_at.isoformat(),
            **event.data
        })

    async def _handle_device_disconnected(self, event: Event) -> None:
        """处理设备断开连接事件"""
        if not isinstance(event, DeviceEvent) or not self._sio:
            return
        await self._safe_emit("state", {
            "type": "device_disconnected",
            "user_id": event.user_id,
            "device_id": event.device_id,
            "timestamp": event.created_at.isoformat(),
            **event.data
        })

    async def get_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        return self._metrics.get_prometheus_metrics()

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._metrics.get_stats()
