# 标准库
from datetime import datetime
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo

# 第三方库
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, JSON, Boolean
from sqlalchemy.orm import relationship

# 本地模块
from app.db.base import Base

class Device(Base):
    """设备模型"""
    __tablename__ = "devices"
    __table_args__ = (
        Index("idx_device_id", "device_id", unique=True),
    )

    id = Column(Integer, primary_key=True)
    device_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    device_name = Column(String, default="")
    device_type = Column(String, default="")
    login_status = Column(Boolean, default=False)  # 改为私有字段
    websocket_online = Column(Boolean, default=False)  # WebSocket连接状态
    ip_address = Column(String, default="")
    user_agent = Column(String, default="")
    first_login = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    last_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    last_login = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    login_count = Column(Integer, default=1)
    system_info = Column(JSON, default=dict)
    extra_data = Column(JSON, default=dict)

    # 关系 - 使用字符串形式的引用
    user = relationship("app.domain.user.models.User", back_populates="devices")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "login_status": self.login_status,
            "websocket_online": self.websocket_online,
            "last_seen": int(self.last_seen.timestamp()) if self.last_seen else None,
            "last_login": int(self.last_login.timestamp()) if self.last_login else None,
            "extra_data": self.extra_data
        }


    @property
    def is_online(self) -> bool:
        """判断用户是否在线
        如果用户有任何一个设备在线，就认为用户在线
        """
        return any(device.websocket_online for device in self.user.devices)

    def set_offline(self):
        """设置设备离线"""
        self.login_status = False
        self.websocket_online = False

