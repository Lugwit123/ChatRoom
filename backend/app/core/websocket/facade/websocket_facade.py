"""
WebSocket门面类
提供统一的WebSocket管理接口
"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
from typing import Dict, Set, Optional, TypeAlias
import socketio
import traceback

from .dto.connection_dto import ConnectionInfo

lprint = LM.lprint

# 类型别名
SID: TypeAlias = str
UserID: TypeAlias = str

class WebSocketFacade:
    """WebSocket门面类"""
    
    def __init__(self, sio: socketio.AsyncServer):
        """初始化WebSocket门面
        
        Args:
            sio: Socket.IO服务器实例
        """
        self.lprint = LM.lprint
        self.sio = sio
        self._sid_to_user: Dict[str, str] = {}  # sid -> user_id
        self._user_to_sids: Dict[str, Set[str]] = {}  # user_id -> set of sids
        self.active_connections: Dict[UserID, ConnectionInfo] = {}  # user_id -> ConnectionInfo
        self.group_members: Dict[str, Set[UserID]] = {}  # group -> members
        
    async def connect(self, sid: SID, user_id: UserID, device_id: str, ip_address: str) -> bool:
        """建立连接
        
        Args:
            sid: Socket.IO会话ID
            user_id: 用户ID
            device_id: 设备ID
            ip_address: 客户端IP地址
            
        Returns:
            bool: 是否成功
        """
        try:
            # 存储连接信息
            self.active_connections[user_id] = ConnectionInfo(
                sid=sid,
                user_id=user_id,
                device_id=device_id,
                ip_address=ip_address
            )
            
            # 更新映射关系
            self._sid_to_user[sid] = user_id
            if user_id not in self._user_to_sids:
                self._user_to_sids[user_id] = set()
            self._user_to_sids[user_id].add(sid)
            
            self.lprint(f"添加连接成功: sid={sid}, user_id={user_id}, device_id={device_id}")
            return True
            
        except Exception as e:
            self.lprint(f"添加连接失败: {str(e)}\n{traceback.format_exc()}")
            return False
        
    async def disconnect(self, sid: SID):
        """断开连接
        
        Args:
            sid: Socket.IO会话ID
        """
        try:
            # 获取用户ID
            user_id = self._sid_to_user.get(sid)
            if not user_id:
                return
                
            # 清理连接信息
            if user_id in self.active_connections:
                del self.active_connections[user_id]
            if sid in self._sid_to_user:
                del self._sid_to_user[sid]
            if user_id in self._user_to_sids:
                self._user_to_sids[user_id].discard(sid)
                if not self._user_to_sids[user_id]:
                    del self._user_to_sids[user_id]
                    
            # 从所有组中移除用户
            for group_members in self.group_members.values():
                group_members.discard(user_id)
                
            # 广播用户离线状态
            connection_info = self.active_connections.get(user_id)
            if connection_info:
                await self.sio.emit("user_offline", {
                    "user_id": user_id,
                    "device_id": connection_info.device_id
                })
                
            self.lprint(f"移除连接成功: sid={sid}, user_id={user_id}")
            
        except Exception as e:
            self.lprint(f"移除连接失败: {str(e)}\n{traceback.format_exc()}")
            
    def is_connected(self, user_id: str) -> bool:
        """检查用户是否在线
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否在线
        """
        return user_id in self._user_to_sids and bool(self._user_to_sids[user_id])
        
    async def broadcast_to_user(self, user_id: str, event: str, data: dict):
        """向用户广播消息
        
        Args:
            user_id: 用户ID
            event: 事件名
            data: 消息数据
        """
        if user_id in self._user_to_sids:
            for sid in self._user_to_sids[user_id]:
                await self.sio.emit(event, data, room=sid)
                
    async def broadcast_to_users(self, user_ids: Set[str], event: str, data: dict):
        """向多个用户广播消息
        
        Args:
            user_ids: 用户ID集合
            event: 事件名
            data: 消息数据
        """
        for user_id in user_ids:
            await self.broadcast_to_user(user_id, event, data)
            
    async def broadcast_to_all(self, event: str, data: dict):
        """向所有在线用户广播消息
        
        Args:
            event: 事件名
            data: 消息数据
        """
        await self.sio.emit(event, data)
        
    async def join_group(self, user_id: str, group: str):
        """用户加入群组
        
        Args:
            user_id: 用户ID
            group: 群组名
        """
        if group not in self.group_members:
            self.group_members[group] = set()
        self.group_members[group].add(user_id)
        
    async def leave_group(self, user_id: str, group: str):
        """用户离开群组
        
        Args:
            user_id: 用户ID
            group: 群组名
        """
        if group in self.group_members:
            self.group_members[group].discard(user_id)
            if not self.group_members[group]:
                del self.group_members[group]
                
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
