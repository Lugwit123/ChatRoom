"""
消息DTO模块
定义所有与消息相关的数据传输对象
"""
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
import zoneinfo
from sqlalchemy import inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute

import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from app.domain.common.models.tables import BaseMessage, PrivateMessage
from app.domain.common.enums.message import MessageStatus, MessageContentType, MessageType, MessageTargetType
from app.utils.time_utils import to_timestamp

class MessageCreateDTO(BaseModel):
    """消息创建DTO
    
    用于创建新消息的数据传输对象。
    
    Attributes:
        content: 消息内容
        recipient_username: 接收者用户名，默认为"fengqingqing"
        content_type: 消息内容类型，默认为纯文本(7)
        message_type: 消息类型，默认为聊天消息(1)
        reply_to_id: 回复的消息ID，可选
        
    Note:
        target_type 固定为 user(1)，私聊消息只能发送给用户
    """
    content: str = Field(..., description="消息内容", example="你好!")
    recipient_username: str = Field(default="fengqingqing", description="接收者用户名", example="fengqingqing")
    content_type: int = Field(default=MessageContentType.plain_text, description="消息内容类型: 1=rich_text, 2=url, 3=audio, 4=image, 5=video, 6=file, 7=plain_text", example=7)
    message_type: int = Field(default=MessageType.chat, description="消息类型: 1=chat, 2=system, 3=broadcast, 4=chat_history", example=1)
    reply_to_id: str = Field(default="", description="回复的消息ID", example=None)

    def to_internal(self, sender_username: str) -> Dict[str, Any]:
        """转换为内部格式
        
        Args:
            sender_username: 发送者用户名
            
        Returns:
            Dict[str, Any]: 内部格式的消息数据
        """
        return {
            "content": self.content,
            "sender_username": sender_username,
            "recipient_username": self.recipient_username,
            "content_type": self.content_type,
            "message_type": self.message_type,
            "target_type": MessageTargetType.user,  # 固定为用户类型
            "reply_to_id": self.reply_to_id
        }

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: to_timestamp
        }
        schema_extra = {
            "example": {
                "content": "你好!",
                "recipient_username": "fengqingqing",
                "content_type": 7,
                "message_type": 1,
                "reply_to_id": None
            }
        }

class GroupMessageCreateDTO(BaseModel):
    """群聊消息创建DTO
    
    用于创建群聊消息的数据传输对象。
    
    Attributes:
        content: 消息内容
        group_name: 群组名称
        content_type: 消息内容类型，默认为纯文本(7)
        message_type: 消息类型，默认为聊天消息(1)
        target_type: 目标类型，固定为群组(2)
        reply_to_id: 回复的消息ID，可选
        mentioned_users: @提到的用户名列表
    """
    content: str = Field(..., description="消息内容")
    group_name: str = Field(..., description="群组名称")
    content_type: int = Field(default=MessageContentType.plain_text, description="消息内容类型: 1=rich_text, 2=url, 3=audio, 4=image, 5=video, 6=file, 7=plain_text")
    message_type: int = Field(default=MessageType.chat, description="消息类型: 1=chat, 2=system, 3=notification, 4=status")
    target_type: int = Field(default=MessageTargetType.group, description="目标类型: 1=user, 2=group, 3=broadcast")
    reply_to_id: Optional[str] = Field(default=None, description="回复的消息ID")
    mentioned_users: List[str] = Field(default_factory=list, description="@提到的用户名列表")

    def to_internal(self, sender_username: str) -> Dict[str, Any]:
        """转换为内部格式
        
        Args:
            sender_username: 发送者用户名
            
        Returns:
            Dict[str, Any]: 内部格式的消息数据
        """
        return {
            "content": self.content,
            "sender_username": sender_username,
            "group_name": self.group_name,
            "content_type": self.content_type,
            "message_type": self.message_type,
            "target_type": self.target_type,
            "reply_to_id": self.reply_to_id,
            "mentioned_users": self.mentioned_users
        }

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: to_timestamp
        }

class BaseMessageDTO(BaseModel):
    """消息基类DTO"""
    id: Any = Field(..., description="消息ID")
    public_id: str = Field("", description="公开ID")
    content: str = Field(..., description="消息内容")
    sender_id: Any = Field(..., description="发送者ID")
    content_type: int = Field(1, description="消息类型: 1=text, 2=image, 3=file, 4=audio, 5=video")
    message_type: int = Field(..., description="消息类型：系统消息/广播/私聊等")
    target_type: int = Field(..., description="目标类型：用户/群组")
    status: List[int] = Field(default_factory=lambda: [1], description="消息状态列表")  # 1 表示 unread
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(None, description="更新时间")
    read_at: Optional[datetime] = Field(None, description="读取时间")
    is_deleted: bool = Field(False, description="是否已删除")
    delete_at: Optional[datetime] = Field(None, description="删除时间")
    reply_to_id: Optional[str] = Field(None, description="回复的消息ID")
    forward_from_id: Optional[str] = Field(None, description="转发自哪条消息")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="额外数据")

    class Config:
        arbitrary_types_allowed = True  # 允许任意类型

    @classmethod
    def from_db(cls, message: BaseMessage) -> "BaseMessageDTO":
        """从数据库模型创建DTO"""
        def get_value(obj: Any, attr: str) -> Any:
            value = getattr(obj, attr)
            if isinstance(value, InstrumentedAttribute):
                return value.value
            return value

        now = datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai"))
        
        # 获取状态，如果为空则使用默认值
        status = get_value(message, 'status')
        if not status:
            status = [1]  # 1 表示 unread
        elif isinstance(status, str):
            try:
                status = [int(status)]
            except ValueError:
                status = [1]
        elif isinstance(status, (list, tuple)):
            try:
                status = [int(s) for s in status]
            except (ValueError, TypeError):
                status = [1]

        # 处理 content_type
        content_type = get_value(message, 'content_type')
        if not isinstance(content_type, int):
            raise ValueError(f"content_type must be an integer, got {type(content_type)}")

        return cls(
            id=get_value(message, 'id'),
            public_id=get_value(message, 'public_id') or str(get_value(message, 'id')),
            content=get_value(message, 'content'),
            sender_id=get_value(message, 'sender_id'),
            content_type=content_type,
            message_type=get_value(message, 'message_type'),
            target_type=get_value(message, 'target_type'),
            status=status,
            created_at=get_value(message, 'created_at') or now,
            updated_at=get_value(message, 'updated_at') or now,
            read_at=get_value(message, 'read_at'),
            is_deleted=get_value(message, 'is_deleted') or False,
            delete_at=get_value(message, 'delete_at'),
            reply_to_id=get_value(message, 'reply_to_id'),
            forward_from_id=get_value(message, 'forward_from_id'),
            extra_data=get_value(message, 'extra_data') or {}
        )

class PrivateMessageDTO(BaseModel):
    """私聊消息DTO"""
    id: str
    sender_id: str
    recipient_id: str
    content: str
    created_at: datetime
    read_at: Optional[datetime] = None
    reply_to_id: Optional[int] = None
    
    @classmethod
    def from_db(cls, message):
        """从数据库对象创建DTO
        
        Args:
            message: 数据库消息对象
            
        Returns:
            PrivateMessageDTO: 消息DTO对象
        """
        return cls(
            id=str(message.id),
            sender_id=str(message.sender_id),
            recipient_id=str(message.recipient_id),
            content=message.content,
            created_at=message.created_at,
            read_at=message.read_at,
            reply_to_id=message.reply_to_id
        )

class GroupMessageDTO(BaseModel):
    """群组消息DTO"""
    id: str
    sender_id: str
    group_id: str
    content: str
    created_at: datetime
    read_at: Optional[datetime] = None
    reply_to_id: Optional[int] = None
    
    @classmethod
    def from_db(cls, message):
        """从数据库对象创建DTO
        
        Args:
            message: 数据库消息对象
            
        Returns:
            GroupMessageDTO: 消息DTO对象
        """
        return cls(
            id=str(message.id),
            sender_id=str(message.sender_id),
            group_id=str(message.group_id),
            content=message.content,
            created_at=message.created_at,
            read_at=message.read_at,
            reply_to_id=message.reply_to_id
        )

class MessageResponse(BaseModel):
    """消息响应模型基类"""
    id: int
    public_id: str
    content: str
    sender_id: int
    content_type: int = Field(1, description="消息类型: 1=text, 2=image, 3=file, 4=audio, 5=video")
    status: List[int] = Field(default_factory=lambda: [1], description="消息状态列表")  # 1 表示 unread
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    delete_at: Optional[datetime] = None
    reply_to_id: Optional[str] = None
    forward_from_id: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: to_timestamp
        }

class PrivateMessageResponse(MessageResponse):
    """私聊消息响应模型"""
    recipient_id: int = Field(..., description="接收者ID")
    recipient_name: str = Field(..., description="接收者名称")
    recipient_avatar: Optional[str] = Field(None, description="接收者头像URL")
    is_sender: bool = Field(..., description="当前用户是否为发送者")

class GroupMessageResponse(MessageResponse):
    """群聊消息响应模型"""
    group_id: int = Field(..., description="群组ID")
    group_name: str = Field(..., description="群组名称")
    group_avatar: Optional[str] = Field(None, description="群组头像URL")
    mentioned_users: List[str] = Field(default_factory=list, description="被@的用户ID列表")

class MessageListResponse(BaseModel):
    """消息列表响应模型"""
    messages: List[Union[PrivateMessageResponse, GroupMessageResponse]] = Field(..., description="消息列表")
    has_more: bool = Field(..., description="是否还有更多消息")
    next_cursor: Optional[str] = Field(None, description="下一页游标（消息ID）")
    unread_count: int = Field(..., description="未读消息数量")

class MessageStatusUpdate(BaseModel):
    """消息状态更新请求模型"""
    status: str = Field(..., description="新状态：delivered/read")

class MessageDelete(BaseModel):
    """消息删除请求模型"""
    delete_for_all: bool = Field(default=False, description="是否为所有人删除")

class MessageForward(BaseModel):
    """消息转发请求模型"""
    target_type: str = Field(..., description="目标类型：private/group")
    target_id: str = Field(..., description="目标ID（用户ID或群组ID）")
    message_ids: List[str] = Field(..., description="要转发的消息ID列表")

class MessageReactionCreate(BaseModel):
    """消息表情回应请求模型"""
    emoji: str = Field(..., description="表情符号")

class MessageReaction(BaseModel):
    """消息表情回应模型"""
    emoji: str = Field(..., description="表情符号")
    user_id: str = Field(..., description="用户ID")
    user_name: str = Field(..., description="用户名称")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

class MessageMention(BaseModel):
    """消息提及模型"""
    user_id: str = Field(..., description="被提及用户ID")
    user_name: str = Field(..., description="被提及用户名称")
    offset: int = Field(..., description="在消息中的位置偏移")
    length: int = Field(..., description="提及内容的长度")

class MessageSearch(BaseModel):
    """消息搜索请求模型"""
    query: str = Field(..., description="搜索关键词")
    chat_with: Optional[str] = Field(None, description="在指定私聊中搜索")
    group_id: Optional[str] = Field(None, description="在指定群组中搜索")
    before: Optional[str] = Field(None, description="搜索此消息之前的消息")
    after: Optional[str] = Field(None, description="搜索此消息之后的消息")
    limit: int = Field(default=20, ge=1, le=50, description="返回结果数量限制")

class MessageSearchResponse(BaseModel):
    """消息搜索响应模型"""
    messages: List[Union[PrivateMessageResponse, GroupMessageResponse]] = Field(..., description="搜索结果")
    total: int = Field(..., description="总结果数")
    has_more: bool = Field(..., description="是否还有更多结果")

class PrivateMessageExportDTO(BaseModel):
    """私聊消息导出DTO"""
    messages: list[PrivateMessageDTO]
    total_count: int
    export_time: datetime

class PrivateMessageBackupDTO(BaseModel):
    """私聊消息备份DTO"""
    messages: list[PrivateMessageDTO]
    backup_time: datetime
    backup_size: int

class PrivateMessageRestoreDTO(BaseModel):
    """私聊消息恢复DTO"""
    messages: list[PrivateMessageDTO]
    restore_time: datetime
    restore_count: int

class PrivateMessageRecallDTO(BaseModel):
    """私聊消息撤回DTO"""
    message_id: str
    recall_time: datetime

class PrivateMessageCleanDTO(BaseModel):
    """私聊消息清理DTO"""
    cleaned_count: int
    clean_time: datetime
