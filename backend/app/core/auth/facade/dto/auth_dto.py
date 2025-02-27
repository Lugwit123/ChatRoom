"""认证相关的数据传输对象"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column

from app.domain.common.enums import UserRole, UserStatusEnum
from app.domain.common.models.tables import User
from app.utils.time_utils import to_timestamp

def convert_column_to_value(value: Column | Any) -> Any:
    """转换SQLAlchemy列值为Python原生类型"""
    if hasattr(value, '_value'):
        return value._value()
    if hasattr(value, 'real'):
        return value.real
    return value

class LoginRequest(BaseModel):
    """登录请求DTO"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    grant_type: str = Field("password", description="授权类型")
    scope: str = Field("", description="权限范围")
    client_id: Optional[str] = Field(None, description="客户端ID")
    client_secret: Optional[str] = Field(None, description="客户端密钥")

class Token(BaseModel):
    """访问令牌DTO"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    role: UserRole = Field(..., description="用户角色")
    device_id: str = Field(..., description="设备ID")

class UserAuthDTO(BaseModel):
    """用户认证DTO
    
    用于用户认证过程中传递必要的认证信息。
    不包含敏感信息如密码哈希。
    """
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    role: UserRole = Field(..., description="用户角色")
    status: UserStatusEnum = Field(..., description="用户状态")
    nickname: Optional[str] = Field(None, description="昵称")
    is_temporary: bool = Field(False, description="是否临时用户")
    
    @classmethod
    def from_internal(cls, user: User) -> 'UserAuthDTO':
        """从内部用户模型创建认证DTO"""
        if not user:
            raise ValueError("User cannot be None")
            
        return cls(
            id=convert_column_to_value(user.id),
            username=str(convert_column_to_value(user.username)),
            email=str(convert_column_to_value(user.email)),
            role=UserRole(convert_column_to_value(user.role)),
            status=UserStatusEnum(convert_column_to_value(user.status)),
            nickname=str(convert_column_to_value(user.nickname)) if user.nickname else None,
            is_temporary=bool(convert_column_to_value(user.is_temporary)) if hasattr(user, 'is_temporary') else False
        )

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: to_timestamp
        }

class UserAuthInternalDTO(UserAuthDTO):
    """内部使用的用户认证DTO
    
    扩展自UserAuthDTO，包含敏感信息。
    仅用于内部认证流程，不应向外部暴露。
    """
    hashed_password: str = Field(..., description="密码哈希")
    
    @classmethod
    def from_internal(cls, user: User) -> 'UserAuthInternalDTO':
        """从内部用户模型创建认证DTO"""
        if not user:
            raise ValueError("User cannot be None")
            
        base = UserAuthDTO.from_internal(user)
        return cls(
            **base.model_dump(),
            hashed_password=str(convert_column_to_value(user.hashed_password))
        )

class LoginResponseDTO(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    device_id: str
    username: str
    role: UserRole
