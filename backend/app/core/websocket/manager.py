# backend/connection_manager.py

from dataclasses import dataclass, field
import traceback
from typing import Dict, Set, List, Optional, TypeAlias, Any
import socketio
import Lugwit_Module as LM
from datetime import datetime
import pytz

lprint = LM.lprint

# 类型别名
SID: TypeAlias = str
Username: TypeAlias = str

@dataclass
class ConnectionInfo:
    """连接信息
    
    Attributes:
        sid: Socket.IO会话ID
        username: 用户名
        device_id: 设备ID
        ip_address: 客户端IP地址
        connected_at: 连接建立时间
    """
    sid: SID
    username: Username
    device_id: str
    ip_address: str
    connected_at: datetime = field(default_factory=lambda: datetime.now(pytz.utc))

class ConnectionManager:
    """WebSocket连接管理器，只负责核心的连接管理"""
    
    def __init__(self, sio: socketio.AsyncServer):
        """初始化连接管理器
        
        Args:
            sio: Socket.IO服务器实例
        """
        self.sio = sio
        self.active_connections: Dict[Username, ConnectionInfo] = {}  # username -> ConnectionInfo
        self.sid_to_username: Dict[SID, Username] = {}  # sid -> username
        self.group_members: Dict[str, Set[Username]] = {}  # group -> members
        
    async def add_connection(self, sid: SID, username: Username, device_id: str, ip_address: str) -> bool:
        """添加新连接
        
        Args:
            sid: 会话ID
            username: 用户名
            device_id: 设备ID
            ip_address: 客户端IP地址
            
        Returns:
            bool: 是否成功
        """
        try:
            # 存储连接信息
            self.active_connections[username] = ConnectionInfo(
                sid=sid,
                username=username,
                device_id=device_id,
                ip_address=ip_address
            )
            self.sid_to_username[sid] = username
            
            lprint(f"添加连接成功: sid={sid}, username={username}, device_id={device_id}")
            return True
            
        except Exception as e:
            lprint(f"添加连接失败: {str(e)}")
            lprint(traceback.format_exc())
            return False
            
    async def remove_connection(self, sid: SID):
        """移除连接
        
        Args:
            sid: 会话ID
        """
        try:
            # 获取用户名
            username = self.sid_to_username.get(sid)
            if not username:
                return
                
            # 清理连接信息
            if username in self.active_connections:
                del self.active_connections[username]
            if sid in self.sid_to_username:
                del self.sid_to_username[sid]
                
            # 从群组中移除
            for members in self.group_members.values():
                members.discard(username)
                
            lprint(f"移除连接成功: sid={sid}, username={username}")
            
        except Exception as e:
            lprint(f"移除连接失败: {str(e)}")
            lprint(traceback.format_exc())
            
    def get_username_by_sid(self, sid: SID) -> Optional[Username]:
        """通过会话ID获取用户名
        
        Args:
            sid: 会话ID
            
        Returns:
            Optional[Username]: 用户名，如果不存在返回None
        """
        return self.sid_to_username.get(sid)
        
    def get_sid_by_username(self, username: Username) -> Optional[SID]:
        """通过用户名获取会话ID
        
        Args:
            username: 用户名
            
        Returns:
            Optional[SID]: 会话ID，如果不存在返回None
        """
        conn_info = self.active_connections.get(username)
        return conn_info.sid if conn_info else None
        
    def is_connected(self, username: Username) -> bool:
        """检查用户是否已连接
        
        Args:
            username: 用户名
            
        Returns:
            bool: 是否已连接
        """
        return username in self.active_connections
        
    def get_connection_data(self, username: Username) -> Optional[ConnectionInfo]:
        """获取连接信息
        
        Args:
            username: 用户名
            
        Returns:
            Optional[ConnectionInfo]: 连接信息，如果不存在返回None
        """
        return self.active_connections.get(username)
        
    async def join_group(self, username: Username, group: str):
        """将用户加入群组
        
        Args:
            username: 用户名
            group: 群组名
        """
        if group not in self.group_members:
            self.group_members[group] = set()
        self.group_members[group].add(username)
        
    async def leave_group(self, username: Username, group: str):
        """将用户从群组中移除
        
        Args:
            username: 用户名
            group: 群组名
        """
        if group in self.group_members:
            self.group_members[group].discard(username)
            
    def get_group_members(self, group: str) -> Set[Username]:
        """获取群组成员
        
        Args:
            group: 群组名
            
        Returns:
            Set[Username]: 群组成员集合
        """
        return self.group_members.get(group, set())
        
    async def emit(self, event: str, data: Any, to: Optional[str] = None):
        """发送事件
        
        Args:
            event: 事件名
            data: 事件数据
            to: 目标用户名或None(广播)
        """
        try:
            if to:
                # 发送给指定用户
                sid = self.get_sid_by_username(to)
                if sid:
                    await self.sio.emit(event, data, room=sid)
            else:
                # 广播
                await self.sio.emit(event, data)
                
        except Exception as e:
            lprint(f"发送事件失败: {str(e)}")
            lprint(traceback.format_exc())
            
    async def emit_to_group(self, group: str, event: str, data: Any):
        """发送事件给群组
        
        Args:
            group: 群组名
            event: 事件名
            data: 事件数据
        """
        try:
            members = self.get_group_members(group)
            for username in members:
                sid = self.get_sid_by_username(username)
                if sid:
                    await self.sio.emit(event, data, room=sid)
                    
        except Exception as e:
            lprint(f"发送群组事件失败: {str(e)}")
            lprint(traceback.format_exc())

# 全局WebSocket连接管理器实例
connection_manager = ConnectionManager(None)

def get_connection_manager() -> ConnectionManager:
    """获取WebSocket连接管理器实例
    
    Returns:
        WebSocket连接管理器实例
    """
    return connection_manager
