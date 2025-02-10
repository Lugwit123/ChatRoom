"""设备相关的数据传输对象"""
import pdb
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List, Sequence

from pydantic import BaseModel, Field

from app.domain.common.enums.device import DeviceType, DeviceStatus
from app.domain.common.models.tables import Device
from app.utils.time_utils import format_datetime
from Lugwit_Module import lprint

class DeviceBase(BaseModel):
    """设备基础数据传输对象
    
    包含设备的基本信息。
    
    Attributes:
        name:
            设备名称
            设备的显示名称
        
        description:
            设备描述
            设备的详细说明
        
        type:
            设备类型
            设备的类型标识
        
        extra_data:
            额外数据
            设备的其他补充信息
    """
    id: int
    name: str
    description: Optional[str] = None
    type: int = 0
    status: DeviceStatus = DeviceStatus.offline
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: format_datetime
        }

class DeviceDTO(BaseModel):
    """设备数据传输对象
    
    用于传递设备的完整信息。
    
    Attributes:
        device_id:
            设备ID
            设备的唯一标识符
        
        device_name:
            设备名称
            设备的显示名称
        
        device_type:
            设备类型
            设备的类型标识
        
        status:
            设备状态
            当前设备的状态
        
        user_id:
            用户ID
            设备所属用户的ID
        
        login_status:
            登录状态
            设备的登录状态
        
        websocket_online:
            WebSocket在线状态
            设备的WebSocket连接状态
        
        ip_address:
            IP地址
            设备的IP地址
        
        user_agent:
            用户代理
            设备的浏览器或客户端信息
        
        first_login:
            首次登录时间
            设备第一次登录的时间
        
        last_login:
            最后登录时间
            设备最近一次登录的时间
        
        login_count:
            登录次数
            设备的总登录次数
        
        system_info:
            系统信息
            设备的系统相关信息
        
        extra_data:
            额外数据
            设备的其他补充信息
    """
    device_id: str = Field(..., description="设备ID")
    device_name: str = Field(..., description="设备名称")
    device_type: DeviceType = Field(DeviceType.desktop, description="设备类型")
    status: Optional[DeviceStatus] = Field(None, description="设备状态")
    user_id: Optional[int] = Field(None, description="用户ID")
    login_status: bool = Field(False, description="登录状态")
    websocket_online: bool = Field(False, description="WebSocket在线状态")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    first_login: Optional[datetime] = Field(None, description="首次登录时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    login_count: int = Field(1, description="登录次数")
    system_info: Dict[str, Any] = Field(default_factory=dict, description="系统信息")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="额外数据")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: format_datetime
        }

    @classmethod
    def from_internal(cls, device: Device) -> "DeviceDTO":
        """从内部模型转换为DTO
        
        Args:
            device: 内部设备模型
            
        Returns:
            设备DTO
        """
        return cls(
            device_id=str(device.device_id),
            device_name=str(device.device_name),
            device_type=device.device_type,
            status=device.status,
            user_id=int(device.user_id) if device.user_id else None,
            login_status=bool(device.login_status),
            websocket_online=bool(device.websocket_online),
            ip_address=str(device.ip_address) if device.ip_address else None,
            user_agent=str(device.user_agent) if device.user_agent else None,
            first_login=device.first_login,
            last_login=device.last_login,
            login_count=int(device.login_count),
            system_info=dict(device.system_info) if device.system_info else {},
            extra_data=dict(device.extra_data) if device.extra_data else {}
        )

    def to_internal(self) -> Device:
        """转换为内部模型
        
        Returns:
            内部设备模型
        """
        return Device(
            device_id=self.device_id,
            device_name=self.device_name,
            device_type=self.device_type,
            status=self.status,
            user_id=self.user_id,
            login_status=self.login_status,
            websocket_online=self.websocket_online,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            first_login=self.first_login,
            last_login=self.last_login,
            login_count=self.login_count,
            system_info=self.system_info,
            extra_data=self.extra_data
        )
