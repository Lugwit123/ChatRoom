"""WebSocket连接相关的数据传输对象"""
from dataclasses import dataclass, field
from datetime import datetime
import pytz

@dataclass
class ConnectionInfo:
    """连接信息
    
    Attributes:
        sid: Socket.IO会话ID
        user_id: 用户ID
        device_id: 设备ID
        ip_address: 客户端IP地址
        connected_at: 连接建立时间
    """
    sid: str
    user_id: str
    device_id: str
    ip_address: str
    connected_at: datetime = field(default_factory=lambda: datetime.now(pytz.utc))
