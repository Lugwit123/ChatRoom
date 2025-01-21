"""
基础DTO模块
提供统一的数据传输对象基类和响应格式
"""
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any

T = TypeVar('T')

class ResponseDTO(BaseModel, Generic[T]):
    """统一响应格式
    
    属性:
        success: 操作是否成功
        message: 响应消息
        data: 响应数据，可选
    """
    success: bool
    message: str
    data: Optional[T] = None
    
    @classmethod
    def success(cls, data: Any = None, message: str = "操作成功"):
        """创建成功响应"""
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error(cls, message: str = "操作失败", data: Any = None):
        """创建错误响应"""
        return cls(success=False, message=message, data=data)
