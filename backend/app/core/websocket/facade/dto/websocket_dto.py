"""
WebSocket数据传输对象
定义WebSocket相关的数据结构
"""
from datetime import datetime
from typing import Set, Dict, Optional
from pydantic import BaseModel

class ConnectionInfo(BaseModel):
    """连接信息"""
    sid: str
    connected_at: datetime = datetime.utcnow()
    last_active: datetime = datetime.utcnow()

class UserSession(BaseModel):
    """用户会话信息"""
    user_id: str
    sids: Set[str] = set()
    
    def add_sid(self, sid: str):
        """添加会话ID"""
        self.sids.add(sid)
        
    def remove_sid(self, sid: str):
        """移除会话ID"""
        self.sids.discard(sid)
        
    @property
    def is_online(self) -> bool:
        """是否在线"""
        return len(self.sids) > 0

class DeviceSession(BaseModel):
    """设备会话信息"""
    sid: str
    user_id: str
    device_id: str
    ip_address: str
    connected_at: datetime = datetime.utcnow()
    last_active: datetime = datetime.utcnow() 