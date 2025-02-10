"""
群组相关枚举定义

包含以下枚举类：
- GroupType: 群组类型枚举
- GroupStatus: 群组状态枚举
- GroupMemberRole: 群组成员角色枚举
- GroupMemberStatus: 群组成员状态枚举
"""
from enum import IntEnum
from typing import Dict, Any
from app.domain.common.enums.message import enum_to_dict

class GroupType(IntEnum):
    """群组类型枚举
    
    用于定义群组的类型和特性。
    
    Attributes:
        normal:
            普通群组，用户可以自由创建和加入
        
        system:
            系统群组，由系统创建和管理，用于特殊用途
        
        temporary:
            临时群组，用于临时性的群聊，可能会自动解散
    """
    normal = 0     # 普通群组
    system = 1     # 系统群组
    temporary = 2  # 临时群组

class GroupStatus(IntEnum):
    """群组状态枚举
    
    用于标识群组的当前状态。
    
    Attributes:
        normal:
            正常状态，群组功能正常运作
        
        disabled:
            禁用状态，群组暂时无法使用
        
        deleted:
            删除状态，群组已被删除
    """
    normal = 0     # 正常状态
    disabled = 1   # 禁用状态
    deleted = 2    # 删除状态

class GroupMemberRole(IntEnum):
    """群组成员角色枚举
    
    用于定义成员在群组中的角色和权限。
    
    Attributes:
        member:
            普通成员，具有基本的聊天权限
        
        admin:
            管理员，可以管理群组成员和设置
        
        owner:
            群主，拥有群组的所有权限
    """
    member = 0  # 普通成员
    admin = 1   # 管理员
    owner = 2   # 群主

class GroupMemberStatus(IntEnum):
    """群组成员状态枚举
    
    用于标识成员在群组中的状态。
    
    Attributes:
        active:
            活跃状态，可以正常参与群组活动
        
        inactive:
            不活跃状态，暂时无法参与群组活动
        
        banned:
            被禁言状态，无法发送消息
        
        left:
            已退出状态，不再是群组成员
    """
    active = 0    # 活跃状态
    inactive = 1  # 不活跃状态
    banned = 2    # 被禁言状态
    left = 3      # 已退出状态

def get_all_enums() -> Dict[str, Dict[str, Any]]:
    """获取所有群组相关枚举的定义
    
    Returns:
        Dict[str, Dict[str, Any]]: 包含所有群组相关枚举的定义，格式为：
        {
            "GroupType": {
                "values": {"normal": 0, "system": 1, "temporary": 2},
                "labels": {0: "normal", 1: "system", 2: "temporary"},
                "descriptions": {
                    0: "普通群组，用户可以自由创建和加入",
                    1: "系统群组，由系统创建和管理，用于特殊用途",
                    2: "临时群组，用于临时性的群聊，可能会自动解散"
                }
            },
            "GroupStatus": {...},
            "GroupMemberRole": {...},
            "GroupMemberStatus": {...}
        }
    """
    return {
        "GroupType": enum_to_dict(GroupType),
        "GroupStatus": enum_to_dict(GroupStatus),
        "GroupMemberRole": enum_to_dict(GroupMemberRole),
        "GroupMemberStatus": enum_to_dict(GroupMemberStatus)
    }
