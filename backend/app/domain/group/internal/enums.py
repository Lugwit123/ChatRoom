"""群组相关枚举类型"""
from enum import Enum

class GroupRole(str, Enum):
    """群组角色枚举"""
    owner = "owner"
    admin = "admin"
    member = "member"

class GroupMemberRole(str, Enum):
    """群组成员角色"""
    OWNER = "owner"  # 群主
    ADMIN = "admin"  # 管理员
    MEMBER = "member"  # 普通成员

class GroupStatus(str, Enum):
    """群组状态枚举"""
    active = "active"
    inactive = "inactive"
    archived = "archived"
    deleted = "deleted"
