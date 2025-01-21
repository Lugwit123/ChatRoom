"""
用户相关的数据模型
"""
# 标准库
from datetime import datetime
from typing import Dict, Any, Optional, List
from zoneinfo import ZoneInfo

# 第三方库
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, JSON, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

# 本地模块
from app.db.base import Base
from .enums import UserRole, UserStatusEnum

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_username", "username", unique=True),
    )

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    nickname = Column(String, nullable=True)
    email = Column(String, nullable=True)
    hashed_password = Column(String)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.user)
    status = Column(SQLAlchemyEnum(UserStatusEnum), default=UserStatusEnum.normal)
    avatar_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    last_login = Column(DateTime(timezone=True), nullable=True)
    extra_data = Column(JSON, default=dict)

    # 关系 - 使用字符串形式的引用
    owned_groups = relationship("app.domain.group.models.Group", back_populates="owner", foreign_keys="[app.domain.group.models.Group.owner_id]")
    devices = relationship("app.domain.device.models.Device", back_populates="user")
    group_memberships = relationship("app.domain.group.models.GroupMember", back_populates="user")
    sent_messages = relationship("app.domain.message.models.PrivateMessage", back_populates="sender", foreign_keys="[app.domain.message.models.PrivateMessage.sender_id]")
    received_messages = relationship("app.domain.message.models.PrivateMessage", back_populates="receiver", foreign_keys="[app.domain.message.models.PrivateMessage.receiver_id]")

    def __repr__(self):
        return f"<User {self.username}>"

    @property
    def login_status(self) -> bool:
        """判断用户是否在线
        如果用户有任何一个设备在线，就认为用户在线
        """
        return any(device.login_status for device in self.devices)

    def to_dict(self, current_user_id: Optional[int] = None) -> Dict[str, Any]:
        """转换为字典格式
        
        Args:
            current_user_id: 当前登录用户的ID，如果提供则会返回与该用户的消息记录
        """
        data = {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "email": self.email,
            "role": self.role.value,
            "status": self.status.value,
            "avatar_index": self.avatar_index,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login,
            "login_status": self.login_status,
            "extra_data": self.extra_data if self.extra_data is not None else {},
            "devices": [device.to_dict() for device in self.devices] if self.devices else []
        }
        
        # 如果提供了当前用户ID，则返回消息记录
        if current_user_id:
            # 获取发送给当前用户的消息
            sent_messages = [msg for msg in self.sent_messages if msg.receiver_id == current_user_id]
            # 获取从当前用户收到的消息
            received_messages = [msg for msg in self.received_messages if msg.sender_id == current_user_id]
            # 合并并按时间排序
            all_messages = sorted(sent_messages + received_messages, key=lambda x: x.created_at)
            messages = [msg.to_dict() for msg in all_messages]
            data["messages"] = messages
            
        return data
