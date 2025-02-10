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
# 获取 site-packages 目录路径
import site
site_packages_path = site.getsitepackages()[0]
aa=r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\Lugwit_Module'

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

lprint("启动后端")

# 创建 FastAPI 应用
app = FastAPI(
    title="聊天室后端服务",
    description="提供聊天室相关功能的后端服务",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建 Socket.IO 服务器
from app.core.websocket.internal.server import SocketServer
from app.core.websocket.facade.websocket_facade import WebSocketFacade

sio = SocketServer.init_server()
websocket_facade = WebSocketFacade()
websocket_facade.init_server(sio)

# 导入门面类
from app.db.facade.database_facade import DatabaseFacade
from app.domain.user.facade.user_facade import UserFacade
from app.domain.group.facade.group_facade import GroupFacade
from app.domain.device.facade.device_facade import DeviceFacade
from app.domain.message.facade.message_facade import MessageFacade
from app.core.auth.facade.auth_facade import AuthFacade

# 全局门面实例
database_facade = DatabaseFacade()

# 初始化数据库连接
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set")
database_facade.init_sync(database_url)

# 初始化其他门面类
auth_facade = AuthFacade()
user_facade = UserFacade()
group_facade = GroupFacade()
device_facade = DeviceFacade(database_facade)
message_facade = MessageFacade()

# 注册消息处理器
@app.on_event("startup")
async def register_message_handlers():
    await message_facade.register_handlers()

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
    await device_facade.init_all_devices_status()



@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    try:
        lprint("后端服务启动...")
        
        # 初始化设备状态
        await device_facade.init_all_devices_status()
        
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

# 创建 Socket.IO 应用
socket_app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=app,
    socketio_path='socket.io'
)

# 将 Socket.IO 应用作为主应用
app = socket_app
