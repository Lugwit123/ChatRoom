"""连接管理器模块"""
from typing import Dict, Optional, Set
from ...interfaces import IConnectionManager
from ...facade.dto import UserSession, DeviceSession
import Lugwit_Module as LM
lprint = LM.lprint

class ConnectionManager(IConnectionManager):
    """连接管理器
    
    管理WebSocket连接的会话信息，包括:
    1. 用户会话
    2. 设备会话
    3. 连接状态
    """
    
    def __init__(self):
        """初始化连接管理器"""
        self._user_sessions: Dict[str, UserSession] = {}  # user_id -> UserSession
        self._device_sessions: Dict[str, DeviceSession] = {}  # sid -> DeviceSession
        self._user_connections: Dict[str, Set[str]] = {}  # user_id -> Set[sid]
        
    def add_connection(self, sid: str, user_id: str, device_id: str, ip_address: str) -> None:
        """添加新连接
        
        Args:
            sid: 会话ID
            user_id: 用户ID
            device_id: 设备ID
            ip_address: IP地址
        """
        try:
            # 创建或更新用户会话
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = UserSession(user_id=user_id)
            
            # 创建设备会话
            self._device_sessions[sid] = DeviceSession(
                sid=sid,
                user_id=user_id,
                device_id=device_id,
                ip_address=ip_address
            )
            
            # 添加到用户连接集合
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(sid)
            
            lprint(f"添加新连接: sid={sid}, user_id={user_id}, device_id={device_id}")
            
        except Exception as e:
            lprint(f"添加连接失败: {str(e)}")
            raise
            
    def remove_connection(self, sid: str) -> None:
        """移除连接
        
        Args:
            sid: 会话ID
        """
        try:
            # 获取设备会话
            device_session = self._device_sessions.get(sid)
            if not device_session:
                return
                
            user_id = device_session.user_id
            
            # 从用户连接集合中移除
            if user_id in self._user_connections:
                self._user_connections[user_id].discard(sid)
                if not self._user_connections[user_id]:
                    del self._user_connections[user_id]
                    if user_id in self._user_sessions:
                        del self._user_sessions[user_id]
                        
            # 删除设备会话
            del self._device_sessions[sid]
            
            lprint(f"移除连接: sid={sid}, user_id={user_id}")
            
        except Exception as e:
            lprint(f"移除连接失败: {str(e)}")
            raise
            
    def get_user_session(self, user_id: str) -> Optional[UserSession]:
        """获取用户会话"""
        return self._user_sessions.get(user_id)
        
    def get_device_session(self, sid: str) -> Optional[DeviceSession]:
        """获取设备会话"""
        return self._device_sessions.get(sid)
        
    def get_user_id_by_sid(self, sid: str) -> Optional[str]:
        """获取会话关联的用户ID"""
        device_session = self._device_sessions.get(sid)
        return device_session.user_id if device_session else None
        
    def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return user_id in self._user_connections and bool(self._user_connections[user_id])
        
    def get_user_connections(self, user_id: str) -> Set[str]:
        """获取用户的所有连接"""
        return self._user_connections.get(user_id, set()) 