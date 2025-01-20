"""自定义异常类"""

class ChatRoomException(Exception):
    """聊天室基础异常类"""
    pass

class BusinessError(ChatRoomException):
    """业务逻辑异常"""
    pass

class UserNotFoundError(ChatRoomException):
    """用户不存在异常"""
    pass

class GroupNotFoundError(ChatRoomException):
    """群组不存在异常"""
    pass

class MessageCreateError(ChatRoomException):
    """消息创建失败异常"""
    pass

class MessageQueryError(ChatRoomException):
    """消息查询失败异常"""
    pass

class MessageUpdateError(ChatRoomException):
    """消息更新失败异常"""
    pass

class PermissionError(ChatRoomException):
    """权限错误异常"""
    pass
