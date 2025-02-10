"""
设备相关枚举定义

包含以下枚举类：
- DeviceType: 设备类型枚举
- DeviceStatus: 设备状态枚举
"""
from enum import IntEnum
from typing import Dict, Any
from app.domain.common.enums.message import enum_to_dict

class DeviceType(IntEnum):
    """设备类型枚举
    
    用于定义设备的类型。
    
    Attributes:
        desktop:
            桌面设备，如PC、笔记本等
        
        mobile:
            移动设备，如手机等
            
        tablet:
            平板设备，如iPad等
        
        web:
            Web浏览器
        
        other:
            其他类型设备
    """
    desktop = 0  # 桌面设备
    mobile = 1   # 移动设备
    tablet = 2   # 平板设备
    web = 3      # Web浏览器
    other = 4    # 其他设备

class DeviceStatus(IntEnum):
    """设备状态枚举
    
    用于标识设备的当前状态。
    
    Attributes:
        online:
            在线状态，设备正常连接
        
        offline:
            离线状态，设备未连接
        
        busy:
            忙碌状态，设备正在处理任务
        
        error:
            错误状态，设备出现故障
    """
    online = 0   # 在线状态
    offline = 1  # 离线状态
    busy = 2     # 忙碌状态
    error = 3    # 错误状态

def get_all_enums() -> Dict[str, Dict[str, Any]]:
    """获取所有设备相关枚举的定义
    
    Returns:
        Dict[str, Dict[str, Any]]: 包含所有设备相关枚举的定义，格式为：
        {
            "DeviceType": {
                "values": {"desktop": 0, "mobile": 1, "tablet": 2, "web": 3, "other": 4},
                "labels": {0: "desktop", 1: "mobile", 2: "tablet", 3: "web", 4: "other"},
                "descriptions": {
                    0: "桌面设备，如PC、笔记本等",
                    1: "移动设备，如手机等",
                    2: "平板设备，如iPad等",
                    3: "Web浏览器",
                    4: "其他类型设备"
                }
            },
            "DeviceStatus": {...}
        }
    """
    return {
        "DeviceType": enum_to_dict(DeviceType),
        "DeviceStatus": enum_to_dict(DeviceStatus)
    }
