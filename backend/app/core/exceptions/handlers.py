"""异常处理器"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from .exceptions import (
    ChatRoomException,
    AuthenticationError,
    DatabaseError,
    WebSocketError,
    ValidationError,
    ResourceNotFoundError,
    PermissionError,
    BusinessError
)
from Lugwit_Module import lprint
import traceback

async def chatroom_exception_handler(request: Request, exc: ChatRoomException) -> JSONResponse:
    """处理ChatRoom基础异常"""
    lprint(f"ChatRoom异常: {exc.detail if hasattr(exc, 'detail') else str(exc)}")
    return JSONResponse(
        status_code=exc.status_code if hasattr(exc, 'status_code') else status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.detail if hasattr(exc, 'detail') else str(exc)}
    )

async def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    """处理认证错误"""
    lprint(f"认证错误: {exc.detail if hasattr(exc, 'detail') else str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail if hasattr(exc, 'detail') else str(exc)}
    )

async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """处理数据库错误"""
    lprint(f"数据库错误: {exc.detail if hasattr(exc, 'detail') else str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.detail if hasattr(exc, 'detail') else str(exc)}
    )

async def websocket_error_handler(request: Request, exc: WebSocketError) -> JSONResponse:
    """处理WebSocket错误"""
    lprint(f"WebSocket错误: {exc.detail if hasattr(exc, 'detail') else str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.detail if hasattr(exc, 'detail') else str(exc)}
    )

async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """处理数据验证错误"""
    lprint(f"数据验证错误: {exc.detail if hasattr(exc, 'detail') else str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.detail if hasattr(exc, 'detail') else str(exc)}
    )

async def resource_not_found_error_handler(request: Request, exc: ResourceNotFoundError) -> JSONResponse:
    """处理资源未找到错误"""
    lprint(f"资源未找到: {exc.detail if hasattr(exc, 'detail') else str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.detail if hasattr(exc, 'detail') else str(exc)}
    )

async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
    """处理权限错误"""
    lprint(f"权限错误: {exc.detail if hasattr(exc, 'detail') else str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.detail if hasattr(exc, 'detail') else str(exc)}
    )

async def business_error_handler(request: Request, exc: BusinessError) -> JSONResponse:
    """处理业务逻辑错误"""
    lprint(f"业务逻辑错误: {exc.detail if hasattr(exc, 'detail') else str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail if hasattr(exc, 'detail') else str(exc)}
    )
