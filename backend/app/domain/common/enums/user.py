"""
用户相关枚举定义

包含以下枚举类：
- UserRole: 用户角色枚举
- UserStatusEnum: 用户状态枚举
"""
from enum import IntEnum
from typing import Dict, Any
from app.domain.common.enums.message import enum_to_dict

class UserRole(IntEnum):
    """用户角色枚举
    
    用于定义用户在系统中的角色和权限级别。
    
    Attributes:
        user:
            普通用户，具有基本的聊天和群组功能权限
        
        admin:
            管理员，具有用户管理和系统配置权限
        
        system:
            系统用户，用于发送系统消息和执行系统操作
    """
    user = 0    # 普通用户
    admin = 1   # 管理员
    system = 2  # 系统用户

class UserStatusEnum(IntEnum):
    """用户状态枚举
    
    用于标识用户账号的当前状态。
    
    Attributes:
        normal:
            正常状态，用户可以正常使用所有功能
        
        disabled:
            禁用状态，用户暂时无法登录和使用功能
        
        deleted:
            删除状态，用户账号已被删除
    """
    normal = 0    # 正常状态
    disabled = 1  # 禁用状态
    deleted = 2   # 删除状态

def get_all_enums() -> Dict[str, Dict[str, Any]]:
    """获取所有用户相关枚举的定义
    
    Returns:
        Dict[str, Dict[str, Any]]: 包含所有用户相关枚举的定义，格式为：
        {
            "UserRole": {
                "values": {"user": 0, "admin": 1, "system": 2},
                "labels": {0: "user", 1: "admin", 2: "system"},
                "descriptions": {
                    0: "普通用户，具有基本的聊天和群组功能权限",
                    1: "管理员，具有用户管理和系统配置权限",
                    2: "系统用户，用于发送系统消息和执行系统操作"
                }
            },
            "UserStatus": {...}
        }
    """
    return {
        "UserRole": enum_to_dict(UserRole),
        "UserStatus": enum_to_dict(UserStatusEnum)
    }
