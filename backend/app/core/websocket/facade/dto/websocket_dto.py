"""
WebSocket相关的数据传输对象定义
包含连接信息、会话管理等所有WebSocket相关的数据结构
"""
from dataclasses import dataclass, field
from typing import Dict, Set, Optional
from datetime import datetime
from Lugwit_Module import lprint


@dataclass
class ConnectionInfo:
    """WebSocket连接信息"""
    sid: str  # 会话ID
    user_id: str  # 用户ID
    device_id: str  # 设备ID
    ip_address: str  # IP地址
    connected_at: datetime = field(default_factory=datetime.now)  # 连接时间

@dataclass
class UserSession:
    """用户会话信息"""
    user_id: str  # 用户ID
    sids: Set[str] = field(default_factory=set)  # 用户的所有会话ID
    last_active: datetime = field(default_factory=datetime.now)  # 最后活跃时间
    
    def add_sid(self, sid: str) -> None:
        """添加会话ID"""
        self.sids.add(sid)
        self.last_active = datetime.now()
        
    def remove_sid(self, sid: str) -> None:
        """移除会话ID"""
        self.sids.discard(sid)
        self.last_active = datetime.now()
        
    @property
    def is_online(self) -> bool:
        """是否在线"""
        return bool(self.sids)

@dataclass
class DeviceSession:
    """设备会话信息"""
    user_id: str  # 用户ID
    device_id: str  # 设备ID
    sid: str  # 会话ID
    ip_address: str  # IP地址
    connected_at: datetime = field(default_factory=datetime.now)  # 连接时间
    
    @property
    def connection_info(self) -> ConnectionInfo:
        """获取连接信息"""
        return ConnectionInfo(
            sid=self.sid,
            user_id=self.user_id,
            device_id=self.device_id,
            ip_address=self.ip_address,
            connected_at=self.connected_at
        )

@dataclass
class SessionManager:
    """会话管理器"""
    sid_to_user: Dict[str, str] = field(default_factory=dict)  # sid -> user_id
    user_sessions: Dict[str, UserSession] = field(default_factory=dict)  # user_id -> UserSession
    device_sessions: Dict[str, DeviceSession] = field(default_factory=dict)  # sid -> DeviceSession
    
    def add_session(self, sid: str, user_id: str, device_id: str, ip_address: str) -> None:
        """添加新会话
        
        Args:
            sid: 会话ID
            user_id: 用户ID
            device_id: 设备ID
            ip_address: IP地址
        """
        # 更新sid到用户的映射
        self.sid_to_user[sid] = user_id
        lprint(f"添加新会话: sid={sid}, user_id={user_id}")
        
        # 更新用户会话信息
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession(user_id=user_id)
        self.user_sessions[user_id].add_sid(sid)
        
        # 更新设备会话信息
        self.device_sessions[sid] = DeviceSession(
            user_id=user_id,
            device_id=device_id,
            sid=sid,
            ip_address=ip_address
        )
        
    def remove_session(self, sid: str) -> None:
        """移除会话
        
        Args:
            sid: 会话ID
        """
        # 获取用户ID
        user_id = self.sid_to_user.get(sid)
        if not user_id:
            return
            
        # 清理用户会话信息
        if user_id in self.user_sessions:
            self.user_sessions[user_id].remove_sid(sid)
            if not self.user_sessions[user_id].is_online:
                del self.user_sessions[user_id]
                
        # 清理设备会话信息
        if sid in self.device_sessions:
            del self.device_sessions[sid]
            
        # 清理sid映射
        del self.sid_to_user[sid]
        
    def get_user_sids(self, user_id: str) -> Set[str]:
        """获取用户的所有会话ID
        
        Args:
            user_id: 用户ID
            
        Returns:
            Set[str]: 会话ID集合
        """
        return self.user_sessions.get(user_id, UserSession(user_id=user_id)).sids
        
    def get_device_session(self, sid: str) -> Optional[DeviceSession]:
        """获取设备会话信息
        
        Args:
            sid: 会话ID
            
        Returns:
            Optional[DeviceSession]: 设备会话信息
        """
        return self.device_sessions.get(sid)
        
    def get_user_id(self, sid: str) -> Optional[str]:
        """获取会话关联的用户ID
        
        Args:
            sid: 会话ID
            
        Returns:
            Optional[str]: 用户ID
        """
        return self.sid_to_user.get(sid)
        
    def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否在线
        """
        return user_id in self.user_sessions and self.user_sessions[user_id].is_online 