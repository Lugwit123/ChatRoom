"""群组相关的数据传输对象"""
import pdb
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List, Sequence

from pydantic import BaseModel, Field

from app.domain.common.enums.group import GroupType, GroupStatus, GroupMemberRole, GroupMemberStatus
from app.domain.common.enums.user import UserRole
from app.domain.common.models.tables import Group, GroupMember, User
from app.utils.time_utils import format_datetime
from Lugwit_Module import lprint

class GroupBase(BaseModel):
    """群组基础数据传输对象
    
    包含群组的基本信息。
    
    Attributes:
        name:
            群组名称
            群组的显示名称
        
        description:
            群组描述
            群组的详细说明
        
        avatar_index:
            头像索引
            群组头像的索引值
        
        extra_data:
            额外数据
            群组的其他补充信息
    """
    id: int
    name: str
    description: Optional[str] = None
    avatar_index: int = 0
    status: GroupStatus = GroupStatus.normal
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: format_datetime
        }

class GroupCreate(GroupBase):
    """群组创建数据传输对象
    
    用于创建新群组时传递的数据。
    
    Attributes:
        owner_id:
            群主ID
            创建群组的用户ID
        
        initial_members:
            初始成员
            创建时添加的成员ID列表
    """
    owner_id: str = Field(..., description="群主ID")
    initial_members: List[str] = Field(default_factory=list, description="初始成员")

class GroupUpdate(BaseModel):
    """群组更新数据传输对象
    
    用于更新群组信息时传递的数据。
    
    Attributes:
        name:
            群组名称
            群组的新名称
        
        description:
            群组描述
            群组的新描述
        
        type:
            群组类型
            群组的新类型
        
        extra_data:
            额外数据
            群组的新补充信息
    """
    name: Optional[str] = Field(None, description="群组名称")
    description: Optional[str] = Field(None, description="群组描述")
    type: Optional[GroupType] = Field(None, description="群组类型")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="额外数据")

class GroupResponse(GroupBase):
    """群组响应数据传输对象
    
    用于API响应中返回群组信息。
    
    Attributes:
        id:
            群组ID
            群组的唯一标识符
        
        owner_id:
            群主ID
            群主的用户ID
        
        created_at:
            创建时间
            群组的创建时间
        
        updated_at:
            更新时间
            群组信息的最后更新时间
        
        member_count:
            成员数量
            群组当前的成员数量
    """
    id: str = Field(..., description="群组ID")
    owner_id: str = Field(..., description="群主ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    member_count: int = Field(0, description="成员数量")

# 为了向后兼容，将 GroupDTO 定义为 GroupResponse 的别名
GroupDTO = GroupResponse

class GroupMemberBase(BaseModel):
    """群组成员基础数据传输对象
    
    包含群组成员的基本信息。
    
    Attributes:
        user_id:
            用户ID
            成员的用户ID
        
        role:
            角色
            成员在群组中的角色
        
        status:
            状态
            成员在群组中的状态
    """
    user_id: str = Field(..., description="用户ID")
    role: GroupMemberRole = Field(GroupMemberRole.member, description="角色")
    status: GroupMemberStatus = Field(GroupMemberStatus.active, description="状态")

class GroupMemberCreate(GroupMemberBase):
    """群组成员创建数据传输对象
    
    用于添加群组成员时传递的数据。
    
    Attributes:
        group_id:
            群组ID
            要加入的群组ID
    """
    group_id: str = Field(..., description="群组ID")

class GroupMemberUpdate(BaseModel):
    """群组成员更新数据传输对象
    
    用于更新群组成员信息时传递的数据。
    
    Attributes:
        role:
            角色
            成员的新角色
        
        status:
            状态
            成员的新状态
    """
    role: Optional[GroupMemberRole] = Field(None, description="角色")
    status: Optional[GroupMemberStatus] = Field(None, description="状态")

class GroupMemberInfo(GroupMemberBase):
    """群组成员详细信息数据传输对象
    
    用于API响应中返回群组成员信息。
    
    Attributes:
        id:
            成员ID
            群组成员的唯一标识符
        
        group_id:
            群组ID
            所属群组的ID
        
        joined_at:
            加入时间
            成员加入群组的时间
        
        updated_at:
            更新时间
            成员信息的最后更新时间
        
        username:
            用户名
            成员的用户名
        
        nickname:
            昵称
            成员的显示名称
        
        avatar_index:
            头像索引
            成员头像的索引值
    """
    id: str = Field(..., description="成员ID")
    group_id: str = Field(..., description="群组ID")
    joined_at: datetime = Field(..., description="加入时间")
    updated_at: datetime = Field(..., description="更新时间")
    username: str = Field(..., description="用户名")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_index: int = Field(0, description="头像索引")

class GroupMessageInfo(BaseModel):
    """群组消息信息数据传输对象
    
    用于传递群组的消息相关信息。
    
    Attributes:
        group_id:
            群组ID
            群组的唯一标识符
        
        name:
            群组名称
            群组的显示名称
        
        description:
            群组描述
            群组的详细说明
        
        type:
            群组类型
            群组的类型标识
        
        unread_count:
            未读消息数
            群组中的未读消息数量
        
        last_message:
            最后一条消息
            群组中的最后一条消息
        
        member_count:
            成员数量
            群组当前的成员数量
    """
    group_id: str = Field(..., description="群组ID")
    name: str = Field(..., description="群组名称")
    description: Optional[str] = Field(None, description="群组描述")
    type: GroupType = Field(GroupType.normal, description="群组类型")
    unread_count: int = Field(0, description="未读消息数")
    last_message: Optional[Any] = Field(None, description="最后一条消息")
    member_count: int = Field(0, description="成员数量")

class GroupListResponse(BaseModel):
    """群组列表响应数据传输对象
    
    用于返回群组列表信息。
    
    Attributes:
        groups:
            群组列表
            包含所有群组的信息
        
        total:
            总数量
            群组的总数量
    """
    groups: List[GroupResponse] = Field(..., description="群组列表")
    total: int = Field(..., description="总数量")

class GroupMemberListResponse(BaseModel):
    """群组成员列表响应数据传输对象
    
    用于返回群组成员列表信息。
    
    Attributes:
        members:
            成员列表
            包含所有成员的信息
        
        total:
            总数量
            成员的总数量
    """
    members: List[GroupMemberInfo] = Field(..., description="成员列表")
    total: int = Field(..., description="总数量")
