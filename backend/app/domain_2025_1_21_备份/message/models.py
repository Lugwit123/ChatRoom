"""
消息模块数据模型定义文件

本文件定义了消息系统中使用的所有数据模型，主要包括：

1. 工具函数:
   - generate_public_id(): 生成带前缀的公开ID，用于消息标识

2. 基础消息模型(BaseMessage):
   - 定义了所有消息类型共有的基础字段
   - 包含ID、内容、发送者、状态等基础信息
   - 支持软删除和消息撤回功能

3. 私聊消息模型(PrivateMessage):
   - 继承自BaseMessage
   - 增加了接收者字段
   - 实现了消息序列化方法

4. 消息表情回应模型(MessageReaction):
   - 记录用户对消息的表情回应
   - 支持多种表情类型
   - 包含时间戳和用户信息

5. 消息@提醒模型(MessageMention):
   - 记录消息中的@提醒信息
   - 关联被@的用户
   - 包含创建时间信息

6. 群组消息表创建函数:
   - create_group_message_table(): 根据群组ID动态创建消息表
   - 支持分表存储群组消息
"""

# 标准库
from datetime import datetime
import uuid
import hashlib
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo

# 第三方库
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, JSON, Enum as SQLAlchemyEnum, Boolean, Table, Text
from sqlalchemy.orm import relationship, declared_attr

# 本地模块
from app.db.base import Base
from app.domain.message.enums import MessageContentType, MessageType, MessageStatus

def generate_public_id(prefix: str) -> str:
    """生成带前缀的公开 ID
    
    格式: prefix_timestamp_randomhash
    例如: msg_1642342123_a1b2c3
    
    Args:
        prefix: ID 前缀
        
    Returns:
        str: 生成的公开 ID
    """
    timestamp = int(datetime.utcnow().timestamp())
    random_bytes = uuid.uuid4().bytes
    hash_suffix = hashlib.sha256(random_bytes).hexdigest()[:6]
    return f"{prefix}_{timestamp}_{hash_suffix}"

class BaseMessage(Base):
    """消息基类"""
    __abstract__ = True  # 标记为抽象基类
    
    # 内部ID，自增整数
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 公开ID，用于前端和API
    public_id = Column(String(50), unique=True, nullable=False, index=True)
    content = Column(String, nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'))
    content_type = Column(SQLAlchemyEnum(MessageContentType), default=MessageContentType.plain_text)
    status = Column(SQLAlchemyEnum(MessageStatus), default=MessageStatus.unread)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")), onupdate=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    extra_data = Column(JSON, default=dict)
    
    # 新增字段
    is_deleted = Column(Boolean, default=False)  # 消息是否被删除（撤回）
    delete_at = Column(DateTime, nullable=True)  # 消息删除时间
    reply_to_id = Column(String(50), nullable=True)  # 回复的消息ID
    forward_from_id = Column(String(50), nullable=True)  # 转发自哪条消息
    search_vector = Column(String, nullable=True)  # 全文搜索向量
    
    def __init__(self, **kwargs):
        """初始化消息实例
        
        如果没有提供 public_id，则自动生成一个
        """
        if not kwargs.get("public_id"):
            kwargs["public_id"] = generate_public_id("msg")
        super().__init__(**kwargs)
    
    @declared_attr
    def sender(cls):
        """发送者关系"""
        return relationship("app.domain.user.models.User", foreign_keys=[cls.sender_id])
    
    @property
    def message_type(self) -> str:
        """获取消息类型
        
        Returns:
            str: 消息类型，如 'private_chat' 或 'group_chat'
        """
        if isinstance(self, PrivateMessage):
            return MessageType.private_chat.value
        return MessageType.group_chat.value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 字典格式的消息数据
        """
        return {
            "id": self.id,  # 内部ID
            "public_id": self.public_id,  # 公开ID
            "content": self.content,
            "sender_id": self.sender_id,
            "sender_name": self.sender.username if self.sender else None,
            "content_type": self.content_type.value if self.content_type else None,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.astimezone(ZoneInfo("Asia/Shanghai")).isoformat() if self.created_at else None,
            "updated_at": self.updated_at.astimezone(ZoneInfo("Asia/Shanghai")).isoformat() if self.updated_at else None,
            "message_type": self.message_type,
            "is_deleted": self.is_deleted,
            "delete_at": self.delete_at.astimezone(ZoneInfo("Asia/Shanghai")).isoformat() if self.delete_at else None,
            "reply_to_id": self.reply_to_id,
            "forward_from_id": self.forward_from_id,
            "extra_data": self.extra_data or {},
        }

def create_group_message_table(group_id: str):
    """根据群组ID创建消息表
    
    Args:
        group_id: 群组ID
    """
    table_name = f"group_messages_{group_id}"
    
    class GroupMessage(BaseMessage):
        __tablename__ = table_name
        __table_args__ = (
            Index(f"idx_{table_name}_sender", "sender_id"),
        )
        
        def __init__(self, **kwargs):
            if not kwargs.get("public_id"):
                kwargs["public_id"] = generate_public_id(f"gm_{group_id}")
            super().__init__(**kwargs)
            
    return GroupMessage

class PrivateMessage(BaseMessage):
    """私聊消息模型"""
    __tablename__ = "private_messages"
    __table_args__ = (
        Index("idx_private_messages_sender", "sender_id"),
        Index("idx_private_messages_receiver", "receiver_id"),
    )
    
    receiver_id = Column(Integer, ForeignKey('users.id'))
    
    @declared_attr
    def receiver(cls):
        """接收者关系"""
        return relationship("app.domain.user.models.User", foreign_keys=[cls.receiver_id])
    
    def __init__(self, **kwargs):
        if not kwargs.get("public_id"):
            kwargs["public_id"] = generate_public_id("pm")
        super().__init__(**kwargs)
    
    def to_dict(self):
        """转换为字典格式"""
        shanghai_tz = ZoneInfo("Asia/Shanghai")
        created_at = self.created_at
        if created_at and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=shanghai_tz)
            
        base_dict = super().to_dict()
        base_dict.update({
            "receiver_id": self.receiver_id,
            "receiver_username": self.receiver.username if self.receiver else None,
        })
        return base_dict

# 消息表情回应
class MessageReaction(Base):
    """消息表情回应"""
    __tablename__ = "message_reactions"
    
    id = Column(Integer, primary_key=True)
    message_table = Column(String(50))  # 消息所在的表名
    message_id = Column(Integer)  # 消息ID
    user_id = Column(Integer, ForeignKey('users.id'))
    reaction = Column(String)  # 表情符号
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    
    user = relationship("app.domain.user.models.User")
    
    def to_dict(self):
        """转换为字典格式"""
        shanghai_tz = ZoneInfo("Asia/Shanghai")
        created_at = self.created_at
        if created_at and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=shanghai_tz)
            
        return {
            "id": self.id,
            "message_table": self.message_table,
            "message_id": self.message_id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "reaction": self.reaction,
            "created_at": created_at.isoformat() if created_at else None
        }

# 消息@提醒
class MessageMention(Base):
    """消息@提醒"""
    __tablename__ = "message_mentions"
    
    id = Column(Integer, primary_key=True)
    message_table = Column(String(50))  # 消息所在的表名
    message_id = Column(Integer)  # 消息ID
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    
    user = relationship("app.domain.user.models.User")
