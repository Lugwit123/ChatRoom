"""消息相关的 Schema 定义"""
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from zoneinfo import ZoneInfo

def to_timestamp(dt: datetime) -> str:
    """将datetime转换为ISO格式字符串"""
    if dt:
        return dt.astimezone(ZoneInfo("Asia/Shanghai")).isoformat()
    return None

# 基础模型
class MessageBase(BaseModel):
    """消息基础模型"""
    id: int = Field(..., description="消息的内部ID，自增整数")
    public_id: str = Field(..., description="消息的公开ID，格式：[类型前缀]_[时间戳]_[随机哈希]")
    content: str = Field(..., description="消息内容")
    sender_id: int = Field(..., description="发送者ID")
    sender_name: str = Field(..., description="发送者名称")
    sender_avatar: Optional[str] = Field(None, description="发送者头像URL")
    content_type: str = Field(..., description="消息类型：text/image/file/audio/video")
    status: str = Field(..., description="消息状态：sent/delivered/read")
    is_deleted: bool = Field(False, description="消息是否已删除")
    reply_to_id: Optional[str] = Field(None, description="回复的消息ID")
    forward_from_id: Optional[str] = Field(None, description="转发自哪条消息")
    reactions: List[Dict[str, Any]] = Field(default_factory=list, description="消息的表情回应")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="额外数据")

# 响应模型
class MessageResponse(MessageBase):
    """消息响应模型"""
    id: int
    public_id: str
    content: str
    sender_id: int
    receiver_id: int
    content_type: str = "plain_text"
    status: str = "unread"
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

class PrivateMessageResponse(MessageBase):
    """私聊消息响应模型"""
    recipient_id: str = Field(..., description="接收者ID")
    recipient_name: str = Field(..., description="接收者名称")
    recipient_avatar: Optional[str] = Field(None, description="接收者头像URL")
    is_sender: bool = Field(..., description="当前用户是否为发送者")

class GroupMessageResponse(MessageBase):
    """群聊消息响应模型"""
    group_id: str = Field(..., description="群组ID")
    group_name: str = Field(..., description="群组名称")
    group_avatar: Optional[str] = Field(None, description="群组头像URL")
    mentioned_users: List[str] = Field(default_factory=list, description="被@的用户ID列表")

class MessageListResponse(BaseModel):
    """消息列表响应模型"""
    messages: List[Union[PrivateMessageResponse, GroupMessageResponse]] = Field(..., description="消息列表")
    has_more: bool = Field(..., description="是否还有更多消息")
    next_cursor: Optional[str] = Field(None, description="下一页游标（消息ID）")
    unread_count: int = Field(..., description="未读消息数量")

# 请求模型
class MessageCreate(BaseModel):
    """创建消息请求模型"""
    content: str = Field(..., description="消息内容")
    recipient_id: Optional[str] = Field(None, description="接收者ID（私聊必需）")
    group_id: Optional[str] = Field(None, description="群组ID（群聊必需）")
    content_type: str = Field(default="text", description="消息类型：text/image/file/audio/video")
    reply_to_id: Optional[str] = Field(None, description="回复的消息ID")
    mentioned_users: List[str] = Field(default_factory=list, description="被@的用户ID列表（群聊可用）")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="额外数据")

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
    reaction: str = Field(..., description="表情代码")

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
