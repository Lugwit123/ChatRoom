# 标准库
from datetime import datetime
from typing import Dict, Any, Optional, List
from zoneinfo import ZoneInfo

# 第三方库
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, JSON, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

# 本地模块
from app.db.base import Base
from app.domain.user.enums import UserRole

class Group(Base):
    """群组模型"""
    __tablename__ = "groups"
    __table_args__ = (
        Index("idx_group_name", "name", unique=True),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, default="")
    owner_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    avatar = Column(String, default="")
    extra_data = Column(JSON, default=dict)

    # 关系 - 使用字符串形式的引用
    owner = relationship("app.domain.user.models.User", back_populates="owned_groups", foreign_keys=[owner_id])
    members = relationship("app.domain.group.models.GroupMember", back_populates="group")

class GroupMember(Base):
    """群组成员模型"""
    __tablename__ = "group_members"
    __table_args__ = (
        Index("idx_group_member", "group_id", "user_id", unique=True),
    )

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    role = Column(String(20), nullable=False, default="MEMBER")
    extra_data = Column(JSON, default=dict)

    # 关系 - 使用字符串形式的引用
    group = relationship("app.domain.group.models.Group", back_populates="members")
    user = relationship("app.domain.user.models.User", back_populates="group_memberships")
