"""后端主程序"""
# 标准库导入
import os
import sys
import uuid
import traceback
from datetime import datetime
from typing import List, Dict, Optional, Any
import asyncio
import contextlib

sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\ChatRoom\backend')
from app.utils import encoding_utils

from dotenv import load_dotenv
load_dotenv()
# 第三方库导入
import socketio
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import Lugwit_Module as LM
from viztracer import VizTracer

lprint = LM.lprint

from app.utils import logging_config
from app.core.di.container import Container, set_container, get_container
from app.core.base.core_facade import CoreFacade
from app.core.websocket.di import register_websocket_services
from app.core.websocket.internal.server import SocketServer
from app.db.facade.database_facade import DatabaseFacade
from app.domain.device.facade.device_facade import DeviceFacade
from app.domain.message.facade.message_facade import MessageFacade
from app.core.services import Services

lprint("启动后端")

def init_container() -> Container:
    """初始化依赖注入容器"""
    container = Container()
    set_container(container)
    
    # 创建核心门面
    core_facade = CoreFacade(container)
    
    # 初始化数据库
    database_facade = DatabaseFacade()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    database_facade.init_sync(database_url)
    
    # 注册事件总线
    Services.register_event_bus()
    
    # 注册核心服务
    core_facade.register_core_services()
    
    # 注册WebSocket服务
    register_websocket_services(container)
    sio = SocketServer.init_server(container)
    if not sio:
        raise RuntimeError("Failed to initialize Socket.IO server")
    
    # 注册设备服务
    device_facade = DeviceFacade()
    container.register_singleton(DeviceFacade, device_facade)
    
    # 注册消息服务
    message_facade = MessageFacade()
    container.register_singleton(MessageFacade, message_facade)
    
    return container

def init_app() -> FastAPI:
    """初始化FastAPI应用"""
    app = FastAPI(
        title="聊天室后端服务",
        description="提供聊天室相关功能的后端服务",
        version="1.0.0",
        docs_url=None,
        redoc_url=None
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    from app.domain.group.router import router as group_router
    from app.core.auth.router import router as auth_router
    from app.domain.user.router import router as user_router
    from app.domain.message.router import router as message_router
    from app.domain.common.router import router as enum_router
    from app.core.websocket.router import router as websocket_router
    
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(group_router)
    app.include_router(message_router)
    app.include_router(enum_router)
    app.include_router(websocket_router)
    
    # 注册异常处理器
    from app.core.exceptions.handlers import (
        chatroom_exception_handler,
        business_error_handler
    )
    app.add_exception_handler(HTTPException, chatroom_exception_handler)
    app.add_exception_handler(Exception, business_error_handler)
    
    return app

def init_websocket(app: FastAPI):
    """初始化WebSocket服务"""
    sio = SocketServer.get_server()
    app.mount("/ws", socketio.ASGIApp(sio))

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    try:
        lprint("后端服务启动...")
        
        # 初始化设备状态
        device_facade = get_container().resolve(DeviceFacade)
        await device_facade.init_all_devices_status()
        
        # 注册消息处理器事件
        message_facade = get_container().resolve(MessageFacade)
        await message_facade.register_handlers()
        
        lprint("后端服务启动完成")
        yield
    finally:
        try:
            lprint("后端服务关闭...")
            database_facade = get_container().resolve(DatabaseFacade)
            await database_facade.cleanup()
            lprint("所有清理操作完成")
        except Exception as e:
            lprint(f"关闭清理失败: {str(e)}")
            traceback.print_exc()
            raise

def create_app() -> FastAPI:
    """创建应用实例"""
    try:
        lprint("开始初始化应用...")
        
        # 初始化容器
        container = init_container()
        lprint("容器初始化完成")
        
        # 初始化应用
        app = init_app()
        
        # 初始化WebSocket
        init_websocket(app)
        
        # 设置生命周期管理
        app.router.lifespan_context = lifespan
        
        lprint("应用初始化完成")
        return app
    except Exception as e:
        lprint(f"应用初始化失败: {str(e)}")
        raise

# 创建应用实例
app = create_app()

# 创建 Socket.IO 应用
socket_app = socketio.ASGIApp(
    socketio_server=SocketServer.get_server(),
    other_asgi_app=app,
    socketio_path='socket.io'
)

# 将 Socket.IO 应用作为主应用
app = socket_app
