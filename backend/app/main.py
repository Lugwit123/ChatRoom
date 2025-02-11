"""后端主程序"""
# 标准库导入
import os
import sys
import uuid
import traceback
from datetime import datetime
from typing import List, Dict, Optional, Any
import asyncio

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
from app.core.di.container import Container, set_container
from app.core.base.core_facade import CoreFacade
from app.core.websocket.di import register_websocket_services
from app.core.websocket.internal.server import SocketServer
from app.db.facade.database_facade import DatabaseFacade
from app.domain.device.facade.device_facade import DeviceFacade

lprint("启动后端")

def create_app() -> FastAPI:
    """创建FastAPI应用实例
    
    Returns:
        FastAPI: FastAPI应用实例
    """
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
    
    try:
        lprint("开始初始化应用...")
        
        # 创建并初始化容器
        container = Container()
        set_container(container)
        lprint("容器初始化完成")
        
        # 创建核心门面
        core_facade = CoreFacade(container)
        
        # 获取数据库门面并初始化
        database_facade = DatabaseFacade()
        
        # 初始化数据库连接
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        database_facade.init_sync(database_url)
        
        # 注册核心服务（包括数据库和认证服务）
        core_facade.register_core_services()
        
        # 注册设备服务
        device_facade = DeviceFacade(db_facade=database_facade)
        container.register_singleton(DeviceFacade, device_facade)
        
        # 注册WebSocket服务
        register_websocket_services(container)
        
        # 初始化Socket.IO服务器
        sio = SocketServer.init_server(container)
        app.mount("/ws", socketio.ASGIApp(sio))
        
        lprint("应用初始化完成")
        
    except Exception as e:
        lprint(f"应用初始化失败: {str(e)}")
        raise
    
    # 导入路由
    from app.domain.group.router import router as group_router
    from app.core.auth.router import router as auth_router
    from app.domain.user.router import router as user_router
    from app.domain.message.router import router as message_router
    from app.domain.common.router import router as enum_router
    
    # 注册路由
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(group_router)
    app.include_router(message_router)
    app.include_router(enum_router)
    
    # 导入异常处理
    from app.core.exceptions.handlers import (
        chatroom_exception_handler,
        business_error_handler
    )
    
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Get SECRET_KEY and DATABASE_URL
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is not set")
    DATABASE_URL=os.getenv("DATABASE_URL")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # 初始化模板引擎
    templates = Jinja2Templates(directory="app/templates")
    
    # 挂载静态文件目录
    app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
    
    # 覆盖默认 /docs 端点以自定义 Swagger UI
    @app.get("/doc", include_in_schema=False)
    async def custom_swagger_ui_html(request: Request):
        lprint("custom_swagger_ui_html")    
        return templates.TemplateResponse("swagger_custom.html", {"request": request})
    
    # 注册异常处理器
    app.add_exception_handler(HTTPException, chatroom_exception_handler)
    app.add_exception_handler(Exception, business_error_handler)
    
    # 初始化设备状态
    async def init_device_status():
        """初始化所有设备的在线状态"""
        device_facade = core_facade.container.resolve(DeviceFacade)
        await device_facade.init_all_devices_status()
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动时的初始化操作"""
        try:
            lprint("后端服务启动...")
            
            # 初始化设备状态
            await init_device_status()
            
            lprint("后端服务启动完成")
        except Exception as e:
            lprint(f"后端服务启动失败: {traceback.format_exc()}")
            raise e
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时的清理操作"""
        try:
            lprint("后端服务关闭...")
            
            # 清理数据库资源
            await database_facade.cleanup()
            
            lprint("所有清理操作完成")
        except Exception as e:
            lprint(f"关闭清理失败: {str(e)}")
            traceback.print_exc()
            raise
    
    # 根路由
    @app.get("/", tags=["系统管理"])
    async def root():
        return {"message": "Welcome to ChatRoom API"}
    
    lprint("应用程序初始化完成")
    return app

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
