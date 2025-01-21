"""用户相关枚举类型"""
from enum import Enum

class UserRole(str, Enum):
    """用户角色枚举"""
    admin = "admin"
    user = "user"
    system = "system"
    test = "test"

class UserStatusEnum(str, Enum):
    """用户状态枚举"""
    normal = "normal"      # 正常
    disabled = "disabled"  # 禁用
    deleted = "deleted"    # 已删除
    locked = "locked"      # 锁定
    pending = "pending"    # 待审核
