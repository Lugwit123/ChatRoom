"""自定义异常类"""
from fastapi import HTTPException, status

class ChatRoomException(Exception):
    """基础异常类"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class AuthenticationError(ChatRoomException):
    """认证错误"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(message)

class DatabaseError(ChatRoomException):
    """数据库错误"""
    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(message)

class WebSocketError(ChatRoomException):
    """WebSocket错误"""
    def __init__(self, message: str = "WebSocket操作失败"):
        super().__init__(message)

class ValidationError(ChatRoomException):
    """数据验证错误"""
    def __init__(self, message: str = "数据验证失败"):
        super().__init__(message)

class ResourceNotFoundError(ChatRoomException):
    """资源未找到错误"""
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} with id {resource_id} not found"
        super().__init__(message)

class PermissionError(ChatRoomException):
    """权限错误"""
    def __init__(self, message: str = "没有足够的权限"):
        super().__init__(message)

class BusinessError(ChatRoomException):
    """业务逻辑错误"""
    def __init__(self, message: str = "业务逻辑错误"):
        super().__init__(message)
