"""设备相关的Pydantic模型"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.domain.message.schemas import to_timestamp

class UserDevice(BaseModel):
    """用户设备信息模型"""
    device_id: str
    device_name: str
    device_type: str
    login_status: bool = False
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    last_seen: Optional[datetime] = None
    last_login: Optional[datetime] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: to_timestamp
        }
