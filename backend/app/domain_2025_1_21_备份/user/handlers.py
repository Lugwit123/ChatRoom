import traceback
from datetime import datetime
from typing import Dict, Optional, List

import socketio
from socketio.exceptions import SocketIOError

import Lugwit_Module as LM
from app.core.websocket.manager import ConnectionManager
from app.domain.user.repository import UserRepository
from app.domain.user.models import UserStatus

lprint = LM.lprint

class UserStatusHandler:
    def __init__(
        self,
        sio: socketio.AsyncServer,
        connection_manager: ConnectionManager,
        user_repository: UserRepository,
    ):
        self.sio = sio
        self.connection_manager = connection_manager
        self.user_repository = user_repository

    def register_handlers(self):
        """注册用户状态事件处理器"""
        self.sio.on("connect", self.handle_connect)
        self.sio.on("disconnect", self.handle_disconnect)

    async def _update_and_broadcast_status(self, username: str, status: UserStatus):
        """更新并广播用户状态
        
        Args:
            username: 用户名
            status: 新状态
        """
        try:
            # 更新用户状态
            await self.user_repository.update_status(username, status)
            
            # 广播用户状态变更
            await self.sio.emit("user_status_change", {
                "username": username,
                "status": status.value,
                "timestamp": datetime.now().isoformat()
            })
            
            lprint(f"用户 {username} {status.value}")
            return True
        except Exception as e:
            lprint(f"更新用户状态失败: {str(e)}")
            lprint(traceback.format_exc())
            return False

    async def handle_connect(self, sid: str, environ: Dict):
        """处理连接事件"""
        try:
            # 从环境中获取用户名
            username = environ.get("HTTP_USERNAME")
            if not username:
                lprint(f"连接失败: 未提供用户名")
                return False

            # 获取用户信息
            user = await self.user_repository.get_user_by_username(username)
            if not user:
                lprint(f"连接失败: 用户 {username} 不存在")
                return False

            # 添加连接
            if await self.connection_manager.handle_connect(sid, username):
                # 处理用户上线逻辑
                await self._update_and_broadcast_status(username, UserStatus.online)
                return True
            return False

        except Exception as e:
            lprint(f"处理连接事件失败: {str(e)}")
            lprint(traceback.format_exc())
            return False

    async def handle_disconnect(self, sid: str):
        """处理断开连接事件"""
        try:
            # 获取用户名并处理断开连接
            username = await self.connection_manager.handle_disconnect(sid)
            if username:
                # 检查用户是否还有其他活动连接
                if not await self.connection_manager.is_user_online(username):
                    # 处理用户离线逻辑
                    await self._update_and_broadcast_status(username, UserStatus.offline)
                lprint(f"用户 {username} 断开连接")

        except Exception as e:
            lprint(f"处理断开连接事件失败: {str(e)}")
            lprint(traceback.format_exc())

    async def is_online(self, username: str) -> bool:
        """检查用户是否在线"""
        return await self.connection_manager.is_user_online(username)

    async def get_online_usernames(self) -> List[str]:
        """获取所有在线用户的用户名列表"""
        return list(await self.connection_manager.get_online_users())