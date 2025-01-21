"""认证相关的数据传输对象"""
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """访问令牌"""
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
    device_id: str

class TokenData(BaseModel):
    """令牌数据"""
    username: Optional[str] = None
    device_id: Optional[str] = None
    exp: Optional[int] = None
