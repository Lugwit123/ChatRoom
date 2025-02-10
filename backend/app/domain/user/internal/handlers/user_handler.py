import traceback
from datetime import datetime
from typing import Dict, Optional, List

import socketio
from socketio.exceptions import SocketIOError

import Lugwit_Module as LM
from app.core.websocket.facade.websocket_facade import WebSocketFacade
from app.domain.user.facade.user_facade import UserFacade
from app.domain.common.enums.user import UserOnlineStatus

lprint = LM.lprint

class UserStatusHandler:
    def __init__(
        self,
        sio: socketio.AsyncServer,
        websocket_facade: WebSocketFacade,
        user_facade: UserFacade,
    ):
        """初始化用户状态处理器
        
        Args:
            sio: Socket.IO服务器实例
            websocket_facade: WebSocket门面实例
            user_facade: 用户门面实例
        """
        self.sio = sio
        self.websocket_facade = websocket_facade
        self.user_facade = user_facade

    def register_handlers(self):
        """注册用户状态事件处理器"""
        self.sio.on("connect", self.handle_connect)
        self.sio.on("disconnect", self.handle_disconnect)

    async def _update_and_broadcast_status(self, user_id: str, status: UserOnlineStatus):
        """更新并广播用户状态
        
        Args:
            user_id: 用户ID
            status: 新状态
        """
        try:
            # 更新用户状态
            result = await self.user_facade.update_status(user_id, status)
            if not result.success:
                return False
            
            # 广播用户状态变更
            await self.websocket_facade.broadcast_user_status(user_id, status)
            
            lprint(f"用户 {user_id} {status.value}")
            return True
        except Exception as e:
            lprint(f"更新用户状态失败: {str(e)}")
            lprint(traceback.format_exc())
            return False

    async def handle_connect(self, sid: str, environ: Dict):
        """处理连接事件"""
        try:
            # 从环境中获取用户信息
            user_id = environ.get("HTTP_USER_ID")
            device_id = environ.get("HTTP_DEVICE_ID")
            ip_address = environ.get("REMOTE_ADDR", "unknown")
            
            if not user_id or not device_id:
                lprint(f"连接失败: 未提供用户ID或设备ID")
                return False

            # 获取用户信息
            user_result = await self.user_facade.get_user(user_id)
            if not user_result.success:
                lprint(f"连接失败: 用户 {user_id} 不存在")
                return False

            # 添加连接
            if await self.websocket_facade.connect(sid, user_id, device_id, ip_address):
                # 处理用户上线逻辑
                await self._update_and_broadcast_status(user_id, UserOnlineStatus.ONLINE)
                return True
            return False

        except Exception as e:
            lprint(f"处理连接事件失败: {str(e)}")
            lprint(traceback.format_exc())
            return False

    async def handle_disconnect(self, sid: str):
        """处理断开连接事件"""
        try:
            # 获取用户ID
            user_id = self.websocket_facade.get_user_id(sid)
            if user_id:
                # 处理断开连接
                await self.websocket_facade.disconnect(sid)
                
                # 检查用户是否还有其他活动连接
                if not await self.websocket_facade.is_user_online(user_id):
                    # 处理用户离线逻辑
                    await self._update_and_broadcast_status(user_id, UserOnlineStatus.OFFLINE)
                lprint(f"用户 {user_id} 断开连接")

        except Exception as e:
            lprint(f"处理断开连接事件失败: {str(e)}")
            lprint(traceback.format_exc())

    async def is_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return await self.websocket_facade.is_user_online(user_id)