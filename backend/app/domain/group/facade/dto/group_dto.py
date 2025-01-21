"""群组相关Pydantic模型"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ..user.enums import UserRole
from .enums import GroupRole, GroupStatus

class GroupBase(BaseModel):
    """群组基础信息模型"""
    name: str
    description: Optional[str] = None
    avatar: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class GroupCreate(GroupBase):
    """群组创建请求模型"""
    owner_id: Optional[int] = None

class GroupUpdate(BaseModel):
    """群组更新请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[str] = None
    status: Optional[GroupStatus] = None
    extra_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class GroupResponse(GroupBase):
    """群组响应模型"""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    members: List[str] = Field(default_factory=list)
    status: GroupStatus = GroupStatus.active
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class GroupMemberResponse(BaseModel):
    """群组成员响应模型"""
    username: str
    role: UserRole
    group_role: GroupRole = GroupRole.member
    joined_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
