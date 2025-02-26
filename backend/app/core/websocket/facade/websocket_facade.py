"""
WebSocket门面类
提供统一的WebSocket管理接口
"""
import sys,os
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
from app.core.events.services import Services
from app.core.events.interfaces import (
    EventType, WebSocketEvent, UserEvent, MessageEvent, DeviceEvent,
    Event, EventHandler
)
from .metrics import Metrics
from app.core.services.service_core import get_user_facade,get_auth_facade, get_device_facade
from app.utils.common import generate_device_id
from app.core.websocket.internal.manager.private_room_manager import PrivateRoomManager
from app.core.auth.facade.auth_facade import AuthenticationError
from fastapi import HTTPException

    
lprint = LM.lprint

# 类型别名
SID: TypeAlias = str
UserID: TypeAlias = str
DeviceID: TypeAlias = str

# Use a function to get the container when needed
def get_container_instance():
    from app.core.di.container import get_container
    return get_container()

class WebSocketFacade:
    """WebSocket门面类
    
    提供WebSocket相关的功能:
    1. 用户会话管理
    2. 消息广播
    3. 实时通知
    """
    _instance = None
    _initialized = False
    _MAX_RETRIES = 2
    _RETRY_DELAY = 1.0  # seconds
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self):
        """初始化WebSocket门面"""
        if not self._initialized:
            self._sio: Optional[socketio.AsyncServer] = None
            container = get_container_instance()
            self._connection_manager = container.resolve(IConnectionManager)
            self._room_manager = container.resolve(IRoomManager)
            self._event_bus = Services.get_event_bus()
            self._metrics = Metrics()
            self._event_queue = asyncio.PriorityQueue()
            self._initialized = True
            self._register_event_handlers()
            asyncio.create_task(self._event_processing_loop())
            lprint("WebSocket门面初始化完成")
            self.auth_facade = get_auth_facade()
            self.user_facade = get_user_facade()
            self.device_facade = get_device_facade()  # 添加设备门面
            self._private_room_manager = PrivateRoomManager()
            
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
        # 只记录错误和关键状态变化
        if level == "error" or message.startswith(("连接", "断开", "错误", "失败")):
            log_data = {
                "message": message,
                "timestamp": datetime.now().isoformat(),
                **kwargs
            }
            lprint(log_data)

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
            EventType.user_login: 1,
            EventType.user_logout: 1,
            EventType.user_status_changed: 2,
            EventType.websocket_connected: 1,
            EventType.websocket_disconnected: 1
        }
        
        # 用户相关事件
        for event_type, priority in priorities.items():
            handler_name = f"_handle_{event_type.value.replace('.', '_')}"
            self._event_bus.subscribe(
                event_type,
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
            traceback.print_exc()

    async def _handle_websocket_connected(self, event: Event) -> None:
        """处理WebSocket连接事件"""
        if not isinstance(event, WebSocketEvent) or not self._sio:
            return
            
        try:
            await self._safe_emit("state", {
                "type": "websocket_connected",
                "sid": event.sid,
                "user_id": event.user_id,
                "device_id": event.device_id,
                "timestamp": event.created_at.isoformat(),
                **event.data
            })
            lprint(f"连接建立成功: sid={event.sid}, user_id={event.user_id}, device_id={event.device_id}")
        except Exception as e:
            lprint(f"处理WebSocket连接事件失败: {str(e)}")
            traceback.print_exc()

    def init_server(self, sio: socketio.AsyncServer):
        """初始化Socket.IO服务器
        
        Args:
            sio: Socket.IO服务器实例
        """
        if not self._sio:
            self._sio = sio
            # 注册事件处理器
            self._register_handlers()
            # 注册/chat/private命名空间
            self._sio.on('connect', self.connect, namespace='/chat/private')
            self._sio.on('disconnect', self.disconnect, namespace='/chat/private')
            lprint("Socket.IO服务器初始化完成")
        
    async def _safe_emit(self, event: str, data: Dict[str, Any], room: Optional[str] = None, namespace: str = '/chat/private') -> bool:
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
        """安全地执行连接管理器操作"""
        for attempt in range(self._MAX_RETRIES):
            try:
                operation_func = getattr(self._connection_manager, operation)
                # 直接调用，不使用 await
                operation_func(*args, **kwargs)
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
            lprint("Socket.IO服务器未初始化")
            return False
            
        try:
            # 获取命名空间参数
            namespace = kwargs.get('namespace', '/chat/private')
            sid = args[0] if args else kwargs.get('sid')
            
            # 检查客户端是否已连接到该命名空间
            if sid and not await self._is_connected(sid, namespace):
                lprint(f"客户端 {sid} 未连接到命名空间 {namespace}")
                return False
                
            # 执行操作
            operation_func = getattr(self._sio, operation)
            await operation_func(*args, **kwargs)
            return True
            
        except Exception as e:
            lprint(f"Socket.IO操作 {operation} 失败: {str(e)}")
            traceback.print_exc()
            return False

    async def _is_connected(self, sid: str, namespace: str = '/chat/private') -> bool:
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

    async def _auto_join_private_rooms(self, user_id: str, sid: str) -> None:
        """自动加入私聊房间"""
        try:
            online_user_ids = await self.user_facade.get_online_user_ids()
            if not online_user_ids:
                lprint(f"没有其他在线用户，跳过创建私聊房间")
                return

            if user_id in online_user_ids:
                online_user_ids.remove(user_id)

            joined_rooms = []
            for other_user_id in online_user_ids:
                # 创建并加入私聊房间
                room_name = self._private_room_manager.create_room(user_id, other_user_id)
                if self._private_room_manager.join_room(sid, room_name):
                    # 加入 Socket.IO 房间
                    if self._sio:
                        await self._sio.enter_room(sid, room_name, namespace='/chat/private')
                    joined_rooms.append(room_name)
                    
                    # 获取房间信息
                    room_info = self._private_room_manager.get_room_info(room_name)
                    if room_info:
                        lprint(f"房间 {room_name} 信息: "
                              f"成员数={len(room_info.members)}, "
                              f"消息数={room_info.message_count}, "
                              f"创建时间={room_info.created_at}")
                
            if joined_rooms:
                lprint(f"自动加入私聊房间完成, 用户ID: {user_id}, 已加入房间: {', '.join(joined_rooms)}")
            else:
                lprint(f"用户ID: {user_id}, 没有其他在线用户，跳过创建私聊房间")
            
        except Exception as e:
            lprint(f"加入私聊房间失败: {str(e)}")
            traceback.print_exc()

    def _get_real_ip(self, environ: dict) -> str:
        ip_adress=environ.get('asgi.scope',{}).get("client",[])[0]
        if ip_adress=='127.0.0.1':
            ip_adress="192.168.112.233"
        return ip_adress

    async def connect(self, sid: str, environ: dict, auth: Optional[dict] = None) -> None:
        """连接事件处理器"""
        try:
            lprint(f"开始处理新连接请求: sid={sid}")
            lprint(f"认证数据: {auth}")
  
            if not auth or 'token' not in auth:
                self._metrics.record_error("auth_missing")
                lprint(f"认证失败: 未提供token, sid={sid}")
                await self._safe_disconnect(sid)
                return
                
            token = auth['token']
            lprint(f"收到token: {token[:10]}...")
            
            try:
                lprint("开始验证用户token...")
                user = await self.auth_facade.get_current_user(token)
                if not user:
                    self._metrics.record_error("auth_failed")
                    lprint(f"认证失败: 用户验证失败, sid={sid}, token={token[:10]}...")
                    await self._safe_disconnect(sid)
                    return
                lprint(f"用户验证成功: user_id={user.id}, username={user.username}")
            except Exception as e:
                self._metrics.record_error("auth_error")
                lprint(f"认证过程发生错误: {str(e)}, sid={sid}")
                lprint(f"错误详情: {traceback.format_exc()}")
                await self._safe_disconnect(sid)
                return

            # 获取设备信息
            ip_address = self._get_real_ip(environ)
            user_agent = environ.get('HTTP_USER_AGENT', 'unknown_device')
            
            lprint(f"用户:{user.username}获取到客户端IP地址: {ip_address}")

            # 使用工具函数生成设备ID
            device_id = generate_device_id(
                client_ip=ip_address,
                username=str(user.username),  # 确保转换为字符串
                user_agent=user_agent
            )

            # 检查设备是否已存在且在线
            device_info = await self.device_facade.get_device_info(device_id)
            if not device_info.success or not device_info.data or not device_info.data.login_status:
                # 设备不存在或离线时才更新状态
                lprint(f"设备离线或不存在，更新设备状态: device_id={device_id}")
                await self.device_facade.update_device_status(
                    device_id=device_id,
                    is_online=True,
                    user_id=int(str(user.id)),
                    client_ip=ip_address,
                    device_name=user_agent
                )
            else:
                lprint(f"设备已在线，跳过状态更新: device_id={device_id}")

            # 使用 to_dto 方法获取用户数据
            user_dto = user.to_dto()
            user_data = user_dto.to_dict()
            
            websocket_event = WebSocketEvent(
                event_type=EventType.websocket_connected,
                sid=sid,
                user_id=int(str(user_dto.id)),  # 确保是整数
                device_id=device_id,
                data={
                    'ip_address': ip_address,
                    'user_info': user_data
                }
            )
            await self._event_bus.publish_event(websocket_event)

            # 其余代码保持不变...
            if not await self._safe_manager_operation('add_connection', sid, str(user_dto.id), device_id, ip_address):
                self._metrics.record_error("connection_add_failed")
                lprint(f"添加连接失败: sid={sid}")
                await self._safe_disconnect(sid)
                return
                
            self._metrics.update_connections(1)
            lprint(f"新连接建立成功: sid={sid}, user_id={user_dto.id}")
            
            # 等待命名空间连接完成
            await asyncio.sleep(1)
            
            # 自动加入私聊房间
            await self._auto_join_private_rooms(str(user_dto.id), sid)
            
            success = await self._safe_emit("connection_established", {
                "sid": sid,
                "user_id": str(user_dto.id),
                "device_id": device_id
            }, room=sid)
            
            if not success:
                self._metrics.record_error("connection_event_failed")
                lprint(f"发送连接成功事件失败: sid={sid}")
                await self._safe_disconnect(sid)

        except Exception as e:
            self._metrics.record_error("connection_error")
            lprint(f"处理连接事件失败: {str(e)}")
            lprint(f"错误详情: {traceback.format_exc()}")
            await self._safe_disconnect(sid)

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
                await self._sio.emit("message", message.dict(), room=room, namespace='/chat/private')
            else:
                # 私聊消息发送到对应的私聊房间
                user_ids = sorted([str(message.sender_id), str(message.recipient_id)])
                room_name = f"private_{user_ids[0]}_{user_ids[1]}"
                await self._sio.emit("message", message.dict(), room=room_name, namespace='/chat/private')
                    
        except Exception as e:
            lprint(f"广播消息失败: {str(e)}")
            raise

    async def disconnect(self, sid: str) -> None:
        """处理断开连接"""
        try:
            # 获取用户信息
            user_id = self._connection_manager.get_user_id(sid)
            if not user_id:
                return
                
            # 获取用户的所有私聊房间
            user_rooms = await self._private_room_manager.get_user_rooms(user_id)
            
            # 离开所有房间
            for room_name in user_rooms:
                await self._private_room_manager.leave_room(sid, room_name)
                if self._sio:
                    await self._sio.leave_room(sid, room_name, namespace='/chat/private')
                    
            # 发布断开连接事件
            device_session = self._connection_manager.get_device_session(sid)
            device_id = device_session.device_id if device_session else "unknown"
            
            websocket_event = WebSocketEvent(
                event_type=EventType.websocket_disconnected,
                sid=sid,
                user_id=int(user_id) if user_id else None,
                device_id=device_id
            )
            await self._event_bus.publish_event(websocket_event)
            
            # 移除连接
            await self._safe_room_operation('remove_sid', sid)
            await self._safe_manager_operation('remove_connection', sid)
            
            self._metrics.update_connections(-1)
            
            # 广播用户离线状态
            if user_id:
                await self._safe_emit("state", {
                    "type": "user_offline",
                    "user_id": user_id,
                    "device_id": device_id,
                    "timestamp": datetime.now().isoformat()
                })
            
            lprint(f"连接断开成功: sid={sid}, user_id={user_id}, device_id={device_id}")
            
        except Exception as e:
            lprint(f"处理断开连接失败: {str(e)}")
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
            
        # 获取用户的所有连接并转换为列表以避免遍历时修改
        sids = list(self._connection_manager.get_user_connections(user_id))
        
        # 如果是消息事件，确保消息被保存
        if event == "message" and isinstance(data, dict):
            # 标记消息为未读
            if 'id' in data:
                from app.domain.message.facade.message_facade import MessageFacade
                message_facade = MessageFacade()
                # 异步保存未读状态
                asyncio.create_task(message_facade.mark_as_unread(int(data['id'])))
        
        # 如果用户没有活跃连接
        if not sids:
            lprint(f"用户 {user_id} 没有活跃连接，消息将在用户上线时推送")
            return
            
        success = False
        errors = []
        
        for sid in sids:
            try:
                # 检查连接是否仍然有效
                if await self._is_connected(sid):
                    if await self._safe_emit(event, data, room=sid):
                        success = True
                else:
                    lprint(f"连接已断开: sid={sid}, user_id={user_id}")
                    await self._safe_manager_operation('remove_connection', sid)
            except Exception as e:
                errors.append(str(e))
                continue
        
        if not success:
            error_msg = f"向用户 {user_id} 发送事件 {event} 失败"
            if errors:
                error_msg += f": {'; '.join(errors)}"
            lprint(error_msg)

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
        await self._sio.emit(event, data, room=room, namespace='/chat/private')
            
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

    async def get_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        return self._metrics.get_prometheus_metrics()

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._metrics.get_stats()

    async def get_client_ip(self, sid: str) -> str:
        """
        获取WebSocket客户端IP地址
        
        Args:
            sid: WebSocket会话ID
            
        Returns:
            str: 客户端IP地址
        """
        try:
            # 从连接管理器获取会话信息
            device_session = self._connection_manager.get_device_session(sid)
            if device_session and device_session.ip_address:
                return device_session.ip_address
            return "127.0.0.1"
            
        except Exception as e:
            lprint(f"获取WebSocket客户端IP失败: {str(e)}")
            traceback.print_exc()
            return "127.0.0.1"
