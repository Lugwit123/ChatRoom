"""
数据库表模型定义
包含所有的SQLAlchemy模型类,数据库使用的Postgre
"""

# 标准库
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Type, TypeVar
from zoneinfo import ZoneInfo
from typing import Type
import json
import traceback
from dataclasses import dataclass, field

# 第三方库
from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Boolean, Enum as SQLAlchemyEnum, 
    Text, func, Index, JSON, ARRAY, BigInteger
)
from sqlalchemy.orm import relationship, declarative_base, backref
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import BinaryExpression

# 本地模块 - 枚举类型
from app.domain.common.enums.user import UserRole, UserStatusEnum
from app.domain.common.enums.group import GroupMemberRole, GroupMemberStatus, GroupType
from app.domain.common.enums.message import (
    MessageType, MessageContentType, MessageStatus,
    MessageTargetType, MessageDirection
)
from app.domain.common.enums.device import DeviceType, DeviceStatus

# 本地模块 - 基类
from app.db.internal.base import Base

@dataclass
class PrivateMessageDTO:
    """私聊消息DTO结构体
    
    用于规范化私聊消息数据传输格式
    
    Attributes:
        id (str): 消息ID
        public_id (str): 公开ID
        sender_id (str): 发送者ID
        recipient_id (Optional[str]): 接收者ID
        content (Union[str, Dict[str, Any]]): 消息内容
        message_type (int): 消息类型
        content_type (int): 内容类型
        target_type (int): 目标类型
        status (List[int]): 状态列表
        created_at (Optional[str]): 创建时间
        updated_at (Optional[str]): 更新时间
        read_at (Optional[str]): 读取时间
        extra_data (Dict[str, Any]): 额外数据
        sender_username (Optional[str]): 发送者用户名
        sender_nickname (Optional[str]): 发送者昵称
        recipient_username (Optional[str]): 接收者用户名
        recipient_nickname (Optional[str]): 接收者昵称
    """
    id: str
    public_id: str
    sender_id: str
    recipient_id: Optional[str] = None
    content: Union[str, Dict[str, Any]] = ""
    message_type: int = MessageType.chat.value
    content_type: int = MessageContentType.plain_text.value
    target_type: int = MessageTargetType.user.value
    status: List[int] = field(default_factory=lambda: [MessageStatus.unread.value])
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    read_at: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    # 用户信息
    sender_username: Optional[str] = None
    sender_nickname: Optional[str] = None
    recipient_username: Optional[str] = None
    recipient_nickname: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典形式的DTO数据
        """
        return {
            'id': self.id,
            'public_id': self.public_id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'content': self.content,
            'message_type': self.message_type,
            'content_type': self.content_type,
            'target_type': self.target_type,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'read_at': self.read_at,
            'extra_data': self.extra_data,
            'sender_username': self.sender_username,
            'sender_nickname': self.sender_nickname,
            'recipient_username': self.recipient_username,
            'recipient_nickname': self.recipient_nickname
        }

def generate_public_id(prefix: str) -> str:
    """生成公开ID"""
    return f"{prefix}_{uuid.uuid4().hex}"

class BaseMessage(Base):
    """消息基类"""
    __abstract__ = True

    # 基本信息
    id = Column(Integer, primary_key=True, autoincrement=True)
    public_id = Column(String, nullable=False)
    
    # 消息内容和类型
    content = Column(Text, nullable=False)
    content_type = Column(Integer, nullable=False)
    message_type = Column(Integer, nullable=False)
    
    # 消息关系
    target_type = Column(Integer, nullable=False)  # 消息目标类型：用户或群组
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    
    # 消息状态和时间
    status = Column(JSON, nullable=False, default=list)  # 存储状态列表
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 额外数据
    extra_data = Column(JSON, nullable=True, default=dict)

    @property
    def content_type_enum(self) -> MessageContentType:
        """获取内容类型枚举值"""
        return MessageContentType(self.content_type)

    @content_type_enum.setter
    def content_type_enum(self, value: MessageContentType):
        """设置内容类型枚举值"""
        self.content_type = value.value

    @property
    def message_type_enum(self) -> MessageType:
        """获取消息类型枚举值"""
        return MessageType(self.message_type)

    @message_type_enum.setter
    def message_type_enum(self, value: MessageType):
        """设置消息类型枚举值"""
        self.message_type = value.value

    @property
    def target_type_enum(self) -> MessageTargetType:
        """获取目标类型枚举值"""
        return MessageTargetType(self.target_type)

    @target_type_enum.setter
    def target_type_enum(self, value: MessageTargetType):
        """设置目标类型枚举值"""
        self.target_type = value.value

    @property
    def status_list(self) -> List[MessageStatus]:
        """获取扁平化的状态列表"""
        status_value = getattr(self, 'status')
        if isinstance(status_value, (InstrumentedAttribute, BinaryExpression)):
            return [MessageStatus.unread]  # 默认为未读状态
        if not status_value:
            return [MessageStatus.unread]  # 默认为未读状态
        if isinstance(status_value, list):
            if not status_value:
                return [MessageStatus.unread]
            if isinstance(status_value[0], list):
                return [MessageStatus(s) for s in status_value[0]]  # 如果是嵌套列表，返回第一个子列表的枚举值
            return [MessageStatus(s) for s in status_value]  # 如果是扁平列表，返回枚举值
        return [MessageStatus.unread]  # 其他情况返回默认值

    @status_list.setter
    def status_list(self, value: List[MessageStatus]):
        """设置状态列表"""
        if not value:
            self.status = [MessageStatus.unread.value]
        elif isinstance(value, list):
            self.status = [s.value for s in value]
        else:
            self.status = [MessageStatus.unread.value]

    def __init__(self, **kwargs):
        """初始化消息"""
        # 处理额外字段
        known_fields = {c.key for c in self.__table__.columns}
        extra_data = {}
        filtered_kwargs = {}
        
        for key, value in kwargs.items():
            if key in known_fields:
                filtered_kwargs[key] = value
            else:
                extra_data[key] = value
                
        if extra_data:
            filtered_kwargs['extra_data'] = extra_data
            
        # 生成公开ID
        if not filtered_kwargs.get("public_id"):
            filtered_kwargs["public_id"] = generate_public_id("pm")
            
        # 处理状态
        if "status" in filtered_kwargs:
            status = filtered_kwargs["status"]
            if not isinstance(status, list):
                filtered_kwargs["status"] = [status]
        else:
            filtered_kwargs["status"] = [MessageStatus.unread.value]
            
        super().__init__(**filtered_kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        created_at_value = getattr(self, 'created_at')
        updated_at_value = getattr(self, 'updated_at')
        
        created_at_str = None
        if isinstance(created_at_value, datetime):
            created_at_str = created_at_value.isoformat()
            
        updated_at_str = None
        if isinstance(updated_at_value, datetime):
            updated_at_str = updated_at_value.isoformat()
            
        return {
            "id": self.id,
            "public_id": self.public_id,
            "content": self.content,
            "content_type": self.content_type_enum.value,
            "message_type": self.message_type_enum.value,
            "target_type": self.target_type_enum.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "group_id": self.group_id,
            "status": [status.value for status in self.status_list],
            "created_at": created_at_str,
            "updated_at": updated_at_str
        }
        
class GroupMessage(BaseMessage):
    __abstract__ = True  # 作为基类，不映射到具体表
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # 关系定义
    sender = relationship("User", foreign_keys=[sender_id])
    group = relationship("Group", foreign_keys=[group_id])

# 创建群组消息表
def create_group_message_table(table_name: str) -> Type[GroupMessage]:
    """创建群组消息分表
    
    Args:
        table_name: 表名
        
    Returns:
        Type[BaseMessage]: 消息表类
    """
    # 检查是否已存在该表的映射类
    if table_name in Base.metadata.tables:
        for mapper in Base.registry.mappers:
            if mapper.class_.__table__.name == table_name:
                return mapper.class_
    class GroupMessage_Table(GroupMessage):
        __tablename__ = table_name
        
        __table_args__ = (
        Index(f'{__tablename__}_sender_id_idx', 'sender_id'),
        Index(f'{__tablename__}_group_id_idx', 'group_id'),
        Index(f'{__tablename__}_created_at_idx', 'created_at'),
    )
    
    return GroupMessage_Table


class PrivateMessage(BaseMessage):
    """私聊消息模型"""
    __tablename__ = "private_messages"

    # 基本信息
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 消息内容和类型
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # 关系
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_private_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_private_messages")

    read_at = Column(DateTime(timezone=True), nullable=True)

    def to_dto(self) -> PrivateMessageDTO:
        """将消息转换为DTO
        
        Returns:
            PrivateMessageDTO: 消息DTO对象
        """
        try:
            # 处理时间字段
            created_at = self.created_at.isoformat() if isinstance(self.created_at, datetime) else None
            updated_at = self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else None
            read_at = self.read_at.isoformat() if isinstance(self.read_at, datetime) else None
            
            # 处理content字段
            content = self.content
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    pass
                    
            # 创建DTO对象
            return PrivateMessageDTO(
                id=str(self.id),
                public_id=self.public_id,
                sender_id=str(self.sender_id),
                recipient_id=str(self.recipient_id) if self.recipient_id else None,
                content=content,
                message_type=self.message_type,
                content_type=self.content_type,
                target_type=self.target_type,
                status=self.status if isinstance(self.status, list) else [MessageStatus.unread.value],
                created_at=created_at,
                updated_at=updated_at,
                read_at=read_at,
                extra_data=self.extra_data if self.extra_data else {}
            )
            
        except Exception as e:
            print(f"转换消息到DTO失败: {str(e)}")
            traceback.print_exc()
            # 返回一个带有最小必要信息的DTO
            return PrivateMessageDTO(
                id=str(getattr(self, 'id', 0)),
                public_id=getattr(self, 'public_id', ''),
                sender_id=str(getattr(self, 'sender_id', 0))
            )

    def to_socket_dict(self) -> Dict[str, Any]:
        """转换为适合WebSocket传输的字典格式
        
        Returns:
            Dict[str, Any]: 包含完整消息信息的字典
        """
        try:
            # 处理时间字段
            created_at_str = self.created_at.isoformat() if isinstance(self.created_at, datetime) else None
            updated_at_str = self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else None
            read_at_str = self.read_at.isoformat() if isinstance(self.read_at, datetime) else None
            
            # 处理content字段
            content = self.content
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    pass
                    
            # 获取发送者和接收者信息
            sender_info = {}
            if self.sender:
                sender_info = {
                    'username': self.sender.username,
                    'nickname': self.sender.nickname,
                    'avatar_index': self.sender.avatar_index
                }
                
            recipient_info = {}
            if self.recipient:
                recipient_info = {
                    'username': self.recipient.username,
                    'nickname': self.recipient.nickname,
                    'avatar_index': self.recipient.avatar_index
                }
            
            return {
                'id': self.id,
                'public_id': self.public_id,
                'sender_id': self.sender_id,
                'recipient_id': self.recipient_id,
                'content': content,
                'message_type': self.message_type,
                'content_type': self.content_type,
                'target_type': self.target_type,
                'status': self.status,
                'created_at': created_at_str,
                'updated_at': updated_at_str,
                'read_at': read_at_str,
                'extra_data': self.extra_data,
                'sender_info': sender_info,
                'recipient_info': recipient_info
            }
            
        except Exception as e:
            print(f"转换消息到Socket字典失败: {str(e)}")
            traceback.print_exc()
            # 返回基本信息
            return {
                'id': getattr(self, 'id', 0),
                'public_id': getattr(self, 'public_id', ''),
                'sender_id': getattr(self, 'sender_id', 0),
                'recipient_id': getattr(self, 'recipient_id', None),
                'content': getattr(self, 'content', ''),
                'message_type': getattr(self, 'message_type', 0),
                'target_type': getattr(self, 'target_type', 0)
            }

@dataclass
class UserDTO:
    """用户DTO结构体
    
    用于规范化用户数据传输格式
    
    Attributes:
        id (int): 用户ID
        username (str): 用户名
        email (Optional[str]): 邮箱
        nickname (Optional[str]): 昵称
        avatar_index (int): 头像索引
        role (int): 角色
        status (int): 状态
        last_login (Optional[str]): 最后活跃时间
        created_at (Optional[str]): 创建时间
        updated_at (Optional[str]): 更新时间
        extra_data (Dict[str, Any]): 额外数据
    """
    id: int
    username: str
    email: Optional[str] = None
    nickname: Optional[str] = None
    avatar_index: int = 0
    role: int = UserRole.user.value
    status: int = UserStatusEnum.normal.value
    last_login: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典形式的DTO数据
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname,
            'avatar_index': self.avatar_index,
            'role': self.role,
            'status': self.status,
            'last_login': self.last_login,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'extra_data': self.extra_data
        }

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_username", "username", unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    hashed_password = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    nickname = Column(String(50), nullable=True)
    avatar_index = Column(Integer, default=0)
    role = Column(Integer, nullable=False, default=UserRole.user.value)
    status = Column(Integer, nullable=False, default=UserStatusEnum.normal.value)
    last_login = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("UTC")))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("UTC")))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("UTC")), onupdate=lambda: datetime.now(ZoneInfo("UTC")))
    extra_data = Column(JSON, default=dict)

    # 关系
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    groups = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
    owned_groups = relationship("Group", back_populates="owner", cascade="all, delete-orphan")
    sent_private_messages = relationship(
        "PrivateMessage", 
        back_populates="sender", 
        foreign_keys=[PrivateMessage.sender_id],  # 使用 Column 对象
        cascade="all, delete-orphan"
    )
    received_private_messages = relationship(
        "PrivateMessage", 
        back_populates="recipient", 
        foreign_keys=[PrivateMessage.recipient_id],
        cascade="all, delete-orphan"
    )

    @property
    def role_enum(self) -> UserRole:
        """获取角色枚举"""
        return UserRole(self.role)

    @property
    def status_enum(self) -> UserStatusEnum:
        """获取状态枚举"""
        return UserStatusEnum(self.status)

    @role_enum.setter
    def role_enum(self, value: UserRole):
        """设置角色枚举值"""
        self.role = value.value

    @status_enum.setter
    def status_enum(self, value: UserStatusEnum):
        """设置状态枚举值"""
        self.status = value.value

    def to_dto(self) -> UserDTO:
        """将用户对象转换为DTO
        
        Returns:
            UserDTO: 用户DTO对象
        """
        try:
            # 处理时间字段
            last_login = self.last_login.isoformat() if isinstance(self.last_login, datetime) else None
            created_at = self.created_at.isoformat() if isinstance(self.created_at, datetime) else None
            updated_at = self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else None
            
            # 创建DTO对象
            return UserDTO(
                id=int(self.id),
                username=str(self.username),
                email=str(self.email) if self.email else None,
                nickname=str(self.nickname) if self.nickname else None,
                avatar_index=int(self.avatar_index),
                role=int(self.role),
                status=int(self.status),
                last_login=last_login,
                created_at=created_at,
                updated_at=updated_at,
                extra_data=self.extra_data if self.extra_data else {}
            )
            
        except Exception as e:
            print(f"转换用户到DTO失败: {str(e)}")
            traceback.print_exc()
            # 返回一个带有最小必要信息的DTO
            return UserDTO(
                id=int(getattr(self, 'id', 0)),
                username=str(getattr(self, 'username', ''))
            )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.to_dto().to_dict()

class Group(Base):
    """群组模型"""
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Integer, default=GroupType.normal.value)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_table_name = Column(String(100), nullable=True)  # 当前使用的消息表名
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("UTC")))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("UTC")), onupdate=lambda: datetime.now(ZoneInfo("UTC")))
    extra_data = Column(JSON, default=dict)
    # 关系
    owner = relationship("User", back_populates="owned_groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")

class GroupMember(Base):
    """群组成员模型"""
    __tablename__ = "group_members"
    __table_args__ = (
        Index("idx_group_user", "group_id", "user_id", unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Integer, default=GroupMemberRole.member.value)
    status = Column(Integer, default=GroupMemberStatus.active.value)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("UTC")))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("UTC")), onupdate=lambda: datetime.now(ZoneInfo("UTC")))

    # 关系
    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="groups")

    @property
    def role_enum(self) -> GroupMemberRole:
        """获取角色枚举值"""
        return GroupMemberRole(self.role)

    @role_enum.setter
    def role_enum(self, value: GroupMemberRole):
        """设置角色枚举值"""
        self.role = value.value

    @property
    def status_enum(self) -> GroupMemberStatus:
        """获取状态枚举值"""
        return GroupMemberStatus(self.status)

    @status_enum.setter
    def status_enum(self, value: GroupMemberStatus):
        """设置状态枚举值"""
        self.status = value.value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "group_id": self.group_id,
            "user_id": self.user_id,
            "role": self.role_enum.name,
            "status": self.status_enum.name,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<GroupMember(group_id={self.group_id}, user_id={self.user_id}, role={self.role})>"

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
    device_type = Column(Integer, default=DeviceType.desktop.value)
    status = Column(Integer, default=DeviceStatus.offline.value)
    login_status = Column(Boolean, default=False)
    websocket_online = Column(Boolean, default=False)
    ip_address = Column(String, default="")
    user_agent = Column(String, default="")
    first_login = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("UTC")))
    last_login = Column(DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("UTC")))
    login_count = Column(Integer, default=1)
    system_info = Column(JSON, default=dict)
    extra_data = Column(JSON, default=dict)

    # 关系
    user = relationship("User", back_populates="devices")

    @property
    def device_type_enum(self) -> DeviceType:
        """获取设备类型枚举值"""
        try:
            return DeviceType(self.device_type)
        except ValueError:
            # 如果值无效，返回默认值
            return DeviceType.other

    @device_type_enum.setter
    def device_type_enum(self, value: DeviceType):
        """设置设备类型枚举值"""
        self.device_type = value.value

    @property
    def status_enum(self) -> DeviceStatus:
        """获取状态枚举值"""
        try:
            return DeviceStatus(self.status)
        except ValueError:
            # 如果值无效，返回默认值
            return DeviceStatus.offline

    @status_enum.setter
    def status_enum(self, value: DeviceStatus):
        """设置状态枚举值"""
        self.status = value.value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "user_id": self.user_id,
            "device_name": self.device_name,
            "device_type": self.device_type_enum.name,
            "status": self.status_enum.name,
            "login_status": self.login_status,
            "websocket_online": self.websocket_online,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "first_login": self.first_login.isoformat() if self.first_login else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
            "system_info": self.system_info,
            "extra_data": self.extra_data
        }

    def is_online(self) -> bool:
        """判断用户是否在线
        如果用户有任何一个设备在线，就认为用户在线
        """
        return self.login_status or self.websocket_online

    def set_offline(self):
        """设置设备离线"""
        self.login_status = False
        self.websocket_online = False

    def __repr__(self):
        return f"<Device(id={self.id}, device_id='{self.device_id}', user_id={self.user_id})>"

def setup_group_message_relationships(partition_count: int = 5):
    """设置群组消息关系
    
    Args:
        partition_count (int): 分表数量,默认为5
    """
    # 创建分表
    group_message_tables = {}
    for i in range(1, partition_count + 1):
        group_message_tables[i] = create_group_message_table(f"group_messages_{i}")

    # 动态添加关系
    for i in range(1, partition_count + 1):
        # 为 User 类添加 sent_group_messages_{i} 关系
        setattr(User, f"sent_group_messages_{i}", relationship(
            group_message_tables[i],
            foreign_keys=[group_message_tables[i].sender_id],
            back_populates="sender",
            cascade="all, delete-orphan"
        ))

        # 为 Group 类添加 messages_{i} 关系
        setattr(Group, f"messages_{i}", relationship(
            group_message_tables[i],
            back_populates="group",
            cascade="all, delete-orphan"
        ))
    
    return group_message_tables
