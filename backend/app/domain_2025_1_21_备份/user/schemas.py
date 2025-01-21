"""用户相关Pydantic模型"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from zoneinfo import ZoneInfo
from .enums import UserRole, UserStatusEnum
from app.domain.message.schemas import MessageResponse, to_timestamp
from app.domain.device.schemas import UserDevice

class UserBase(BaseModel):
    """用户基础信息模型"""
    username: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    role: UserRole = UserRole.user
    avatar_index: int = 0
    status: UserStatusEnum
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: to_timestamp
        }

class UserBaseAndStatus(UserBase):
    """用户基础信息和状态模型"""
    login_status: bool = False
    last_seen: Optional[datetime] = None
    last_login: Optional[datetime] = None
    devices: List[UserDevice] = []  # 在线设备列表
    messages: List[MessageResponse] = Field(default_factory=list, description="与当前登录用户的消息记录")
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: to_timestamp
        }

class UserCreate(UserBase):
    """用户创建请求模型"""
    password: str

class UserUpdate(BaseModel):
    """用户更新请求模型"""
    nickname: Optional[str] = None
    email: Optional[str] = None
    avatar_index: Optional[int] = None
    status: Optional[UserStatusEnum] = None
    
    class Config:
        from_attributes = True

class UserDevice(BaseModel):
    """用户设备信息模型"""
    device_id: str
    device_name: str
    device_type: str
    login_status: bool = False
    last_seen: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: to_timestamp
        }

class UserResponse(UserBaseAndStatus):
    """用户响应模型"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: to_timestamp
        }

class UserMapInfo(BaseModel):
    """用户映射信息模型"""
    username: str
    nickname: Optional[str] = None
    avatar_index: int = 0
    role: UserRole = UserRole.user
    login_status: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: to_timestamp
        }

class UsersInfoDictResponse(BaseModel):
    """用户列表响应模型，包含当前用户信息、其他用户信息和群组列表"""
    current_user: UserResponse = Field(..., description="当前登录的用户信息")
    user_map: Dict[str, UserBaseAndStatus] = Field(..., description="其他用户的详细信息列表")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: to_timestamp
        }

class Token(BaseModel):
    """JWT Token响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    username: str = Field(..., description="用户名")
    role: str = Field(..., description="用户角色")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_index: Optional[int] = Field(None, description="头像索引")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: to_timestamp
        }
