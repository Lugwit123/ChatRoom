# schemas.py

from __future__ import annotations
import json  # 处理前向引用
from pydantic import (
    BaseModel, 
    EmailStr, 
    Field, 
    field_validator, 
    model_validator, 
    ValidationInfo, 
    validator,
    field_serializer
)
from typing import Dict, List, Optional, Union, Literal, Any
from enum import Enum
from datetime import datetime, timezone
import Lugwit_Module as LM
lprint=LM.lprint

default_notice='''
**重要通知:**
亲爱的用户，
为了提升服务质量，我们将于**2024年5月10日（星期五）凌晨1:00至5:00**进行系统维护。在此期间，部分功能可能暂时无法使用。维护完成后，所有服务将恢复正常。
对您造成的不便，敬请谅解！如有疑问，请联系**support@example.com**或拨打**400-123-4567**。\n
**[公司名称]**  
**联系方式：**support@example.com | 400-123-4567
'''

# ============================
# Enums
# ============================

class UserRole(str, Enum):
    """用户角色枚举"""
    admin = "admin"
    user = "user"
    system = "system"
    test = "test"


# ============================
# Group Models
# ============================

class GroupInDatabase(BaseModel):
    """组在数据库中的模型"""
    id: Optional[int] = Field(default=6, description="组ID")
    name: str = Field(default="OC_Studio", description="组名")

    model_config = {
        "from_attributes": True,
    }


class GroupResponse(BaseModel):
    """组响应模型，包含成员列表"""
    id: int
    name: str
    members: Optional[List[UserBase]] = None  # 成员列表设为可选

    model_config = {
        "from_attributes": True,

    }


# ============================
# User Models
# ============================

class UserBase(BaseModel):
    """用户基础信息模型"""
    username: str = Field(..., description="用户名")
    nickname: Optional[str] = Field(None, description="昵称")
    email: Optional[EmailStr] = Field(None, description="电子邮箱")
    groups: List[GroupInDatabase] = Field(default_factory=list, description="所属群组列表")
    role: UserRole = Field(default=UserRole.user, description="用户角色")

    model_config = {
        "from_attributes": True,

    }


class UserRegistrationRequest(UserBase):
    """用户注册请求模型，包含密码"""
    password: str = Field(..., description="密码")

    model_config = {
        "from_attributes": True,
    }


class UserLoginRequest(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

    model_config = {
        "from_attributes": True,

    }


class UserBase(UserBase):
    """用户数据库模型，包含数据库相关的字段"""
    id: Optional[int] = Field(None, description="用户ID")
    hashed_password: str = Field(..., description="哈希后的密码")
    is_temporary: bool = Field(default=False, description="是否为临时用户")
    online: bool = Field(default=False, description="是否在线")
    avatar_index:int = Field(0, description="头像索引")

    model_config = {
        "from_attributes": True,

    }

    def get_group_names(self) -> List[str]:
        """获取用户所属群组的名称列表。"""
        return [group.name for group in self.groups if hasattr(group, 'name')]


class UserResponse(BaseModel):
    """用户响应模型，返回给前端的基本用户信息"""
    id: Optional[int] = Field(None, description="用户ID")
    username: str = Field(..., description="用户名")
    nickname: Optional[str] = Field(None, description="昵称")
    email: Optional[EmailStr] = Field(None, description="电子邮箱")
    groups: List[GroupInDatabase] = Field(default_factory=list, description="所属群组列表")
    role: UserRole = Field(default=UserRole.user, description="用户角色")
    avatar_index: int = Field(default=0, description="头像索引")
    messages: List[MessageBase] = Field(default_factory=list, description="消息列表")

    model_config = {
        "from_attributes": True,
    }


class UserStatus(BaseModel):
    """用户状态模型，包含在线状态和未读消息数"""
    online: bool = Field(..., description="是否在线")
    unread_message_count: int = Field(..., description="未读消息数量")

    model_config = {
        "from_attributes": True,

    }


class UserBaseAndStatus(UserResponse, UserStatus):
    """用户详细信息模型，包含基本信息和状态信息"""
    unread_message_count: int = Field(default=0, description="未读消息数量")  # 修正默认值
    avatar_index: int = Field(default=0, description="头像")  # 修正默认值

    model_config = {
        "from_attributes": True,

    }


class UserListResponse(BaseModel):
    """用户列表响应模型，包含当前用户信息、其他用户信息和群组列表"""
    current_user: UserResponse = Field(..., description="当前登录的用户信息")
    users: List[UserBaseAndStatus] = Field(..., description="其他用户的详细信息列表")

    model_config = {
        "from_attributes": True,
    }
    
class UsersInfoDictResponse():
    """用户列表响应模型，包含当前用户信息、其他用户信息和群组列表"""
    current_user: UserResponse = Field(..., description="当前登录的用户信息")
    user_map: Dict[str, UserBaseAndStatus] = Field(..., description="其他用户的详细信息列表")

    model_config = {
        "from_attributes": True,
    }


class DeleteUserRequest(BaseModel):
    """删除用户请求模型"""
    username: str = Field(..., description="要删除的用户名")

    model_config = {
        "from_attributes": True,

    }


# ============================
# Authentication Models
# ============================

class Token(BaseModel):
    """令牌模型，用于认证和授权"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(..., description="令牌类型")

    model_config = {
        "from_attributes": True,

    }


# ============================
# Message Models
# ============================

class MessageDirection(str, Enum):
    RESPONSE  = 'response'
    REQUEST  = 'request'

class MessageStatus(str, Enum):
    UNREAD = "unread"         # 未读
    READ = "read"             # 已读
    PENDING = "pending"       # 处理中
    SUCCESS = "success"       # 处理成功
    FAILED = "failed"         # 处理失败


class ValidationType(str, Enum):
    CFX_ABC_Check = "unread"         # 未读


class MessageContentType(str, Enum):
    """消息内容类型枚举"""
    rich_text = 'rich_text'  # 富文本消息
    url = 'url'              # 超链接
    audio = 'audio'          # 音频
    image = 'image'          # 图片
    video = 'video'          # 视频
    file = 'file'            # 文件
    plain_text = 'plain_text' # 纯文本
    user_list = 'user_list'
    html = 'html'


class MessageType(str, Enum):
    """消息类型枚举"""
    BROADCAST = 'broadcast'
    PRIVATE_CHAT = 'private_chat'  # 重命名为私聊
    GROUP_CHAT = 'group_chat'      # 新增群聊
    SELF_CHAT = 'self_chat',
    CHAT_HISTORY = 'chat_history'
    SYSTEM = 'system'
    VALIDATION = 'validation'
    USER_LIST_UPDATE = 'user_list_update'
    ERROR = 'error'
    GET_USERS = 'get_users'  # 添加新的消息类型
    REMOTE_CONTROL = 'remote_control',
    OPEN_PATH = 'open-path'
 

class MessageBase(BaseModel):
    """消息基础模型"""
    id: Optional[Union[int, str]] = Field(default=0, description="消息ID")
    sender: str = Field(default="", description="发送者用户名")
    recipient: Union[str, List[str]] = Field(default="", description="接收者")
    content: Optional[Union[Any,str, Dict[str, Any]]] = Field(default="", description="消息内容")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="消息时间戳")
    recipient_type: Optional[str] = Field(default=None, description="消息类型")
    status: list[MessageStatus] = Field(default=[MessageStatus.SUCCESS], description="消息状态列表")
    direction : MessageDirection = Field(default=MessageDirection.REQUEST, description="消息方向")
    message_content_type: MessageContentType = Field(
        default=MessageContentType.HTML,
        description="消息内容类型"
    )
    popup_message: Optional[bool] = Field(default=False, description="弹窗消息内容") 
    message_type: MessageType = Field(default=MessageType.PRIVATE_CHAT, description="消息类型")
    
    # 针对 VALIDATION 类型的字段
    validation_type: Optional[ValidationType] = Field(default=None, description="验证的具体类型")
    validation_extra_data: Optional[Dict] = Field(default=None, description="与验证相关的附加数据")

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "extra": "ignore"
    }
     # 新增字段
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        """将 datetime 对象格式化为 ISO 8601 字符串，保留时区信息"""
        return value.isoformat()
    
    def add_status(self, new_status: Union[MessageStatus, List[MessageStatus]]):
        """
        添加状态，并自动删除互斥状态。
        支持单个状态和状态列表作为输入。
        """
        # 互斥规则映射
        mutex_map = {
            MessageStatus.READ: [MessageStatus.UNREAD],
            MessageStatus.UNREAD: [MessageStatus.READ],
            MessageStatus.PENDING: [MessageStatus.SUCCESS, MessageStatus.FAILED],
            MessageStatus.SUCCESS: [MessageStatus.PENDING, MessageStatus.FAILED],
            MessageStatus.FAILED: [MessageStatus.PENDING, MessageStatus.SUCCESS],
        }

        # 如果 new_status 是单个状态，转换为列表处理
        if isinstance(new_status, MessageStatus):
            new_status = [new_status]

        # 遍历输入的状态列表，逐个处理
        for status in new_status:
            # 删除与当前状态互斥的状态
            if status in mutex_map:
                self.status = [s for s in self.status if s not in mutex_map[status]]
            
            # 添加状态，如果它尚不存在
            if status not in self.status:
                self.status.append(status)


class MessageRange(BaseModel):
    """消息范围模型"""
    start: int = Field(..., description="起始消息ID")
    end: Optional[int] = Field(None, description="结束消息ID（可选）")


class DeleteMessagesRequest(BaseModel):
    """删除消息请求模型"""
    message_ids: Union[List[int], str] = Field(default="[15:20,23]", description="要删除的消息ID列表")

    @validator("message_ids", pre=True, always=True)
    def parse_message_ids(cls, value):
        # 字符串形式转换为列表
        lprint(value)
        value = value.strip("[]")
        items = value.split(",")
        result = []
        for item in items:
            if ":" in item:
                start, end = map(int, item.split(":"))
                result.extend(range(start, end + 1))
            else:
                result.append(int(item))
        lprint(result)
        return result
        


class SendMessageRequest(MessageBase):
    """发送消息请求模型"""
    recipient_type: str = Field(default='private', description="接收者类型，'private'或'group'")
    recipient: str = Field(default='fengqingqing', description="接收者ID，用户名或群组名")
    content: str = Field(default=default_notice, description="消息内容")
    popup_message: Optional[bool] = Field(default=True, description="是否需要弹窗通知")

    model_config = {
        "from_attributes": True,

    }


class UserCreate(BaseModel):
    username: str
    nickname: str
    password: str
    email: EmailStr
    role: UserRole
    groups: List[str]
    is_temporary: Optional[bool] = False
    online: Optional[bool] = False  # 默认值为 False

    class Config:
        orm_mode = True
        
class MessageCreate(BaseModel):
    sender: str
    recipient: str
    content: str
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    popup_message: Optional[bool] = False  # 默认值为 False

    class Config:
        orm_mode = True

class MessagesRequest(BaseModel):
    """获取消息请求模型"""
    chat_id: str | int = Field(default='fengqingqing', description="聊天对象ID，用户名或群组名")
    messages_nums: int = Field(default=20, description="获取消息数量")
    model_config = {
        "from_attributes": True,

    }


# ============================
# Specialized Message Models
# ============================

class UserListUpdateMessage(MessageBase):
    """用户列表更新消息"""
    message_type: Literal[MessageType.USER_LIST_UPDATE] = Field(MessageType.USER_LIST_UPDATE)
    user_list: List[UserBaseAndStatus] = Field(..., description="更新后的用户列表")
    groups: List[str] = Field(..., description="更新后的群组列表")

    model_config = {
        "from_attributes": True,
    }


class SystemMessage(MessageBase):
    """系统消息"""
    message_type: Literal[MessageType.SYSTEM] = Field(MessageType.SYSTEM)
    content: str = Field(..., description="系统消息内容")

    model_config = {
        "from_attributes": True,
    }

class ChatHistoryRequestMessage(BaseModel):
    """聊天历史请求消息"""
    message_type: Literal[MessageType.CHAT_HISTORY] = Field(MessageType.CHAT_HISTORY)
    username: str = Field(..., description="请求聊天历史的用户名")

    model_config = {
        "from_attributes": True,
    }


class GroupChatMessage(MessageBase):
    """群组聊天消息"""
    message_type: Literal[MessageType.GROUP_CHAT] = Field(MessageType.GROUP_CHAT)
    recipient_type: Literal['group'] = Field('group', description="接收者类型固定为'group'")
    sender: str = Field(..., description="发送者用户名")
    recipient: str = Field(..., description="接收者群组名")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(..., description="消息时间戳")
    status: str = Field(..., description="消息状态，例如'read' | 'unread'")
    avatar_index: Optional[int] = Field(0, description="发送者头像索引")

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
    }

    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        """将 datetime 对象格式化为所需的字符串格式"""
        return value.strftime('%Y-%m-%d %H:%M:%S')


class SelfPrivateChatMessage(MessageBase):
    """自己发送的私聊消息"""
    message_type: Literal[MessageType.PRIVATE_CHAT] = Field(MessageType.PRIVATE_CHAT)
    recipient_type: Literal['self_chat'] = Field('self_chat', description="接收者类型固定为'self_chat'")
    sender: str = Field(..., description="发送者用户名")
    recipient: str = Field(..., description="接收者用户名")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(..., description="消息时间戳")
    status: str = Field(..., description="消息状态，例如'read' | 'unread'")
    avatar_index: Optional[int] = Field(0, description="发送者头像索引")

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
    }

    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        """将 datetime 对象格式化为所需的字符串格式"""
        return value.strftime('%Y-%m-%d %H:%M:%S')


# ============================
# WebSocket Message Union
# ============================

WebSocketMessage = Union[
    UserListUpdateMessage,
    SystemMessage,
    GroupChatMessage,
    SelfPrivateChatMessage,
    ChatHistoryRequestMessage
]


class UserMessageIDDataUpdate(BaseModel):
    """消息更新数据结构"""
    sender_id: int
    id: int
    recipient_id: Optional[int] = None

    class Config:
        from_attributes = True
