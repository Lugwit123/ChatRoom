"""后端主程序"""
# 标准库导入
import os
import sys
import uuid
import logging
import traceback
import asyncio
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from viztracer import VizTracer
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

# 标准库导入
import json
import time
from zoneinfo import ZoneInfo

# 第三方库导入
import socketio
from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, update
from passlib.context import CryptContext
from sqlalchemy.orm import Session, declarative_base, scoped_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\ChatRoom\backend')
from app.utils import encoding_utils
# 获取 site-packages 目录路径

import site
site_packages_path = site.getsitepackages()[0]
aa=r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\Lugwit_Module'
tracer = VizTracer(ignore_c_function=True, ignore_frozen=True,exclude_files=[site_packages_path,aa])
tracer.start()
# 项目内部导入
from app.db.database import engine, AsyncSessionLocal as SessionLocal, init_db, cleanup_db, DatabaseManager

from app.domain.device.models import Device
from app.domain.group.models import Group
from app.domain.message.repository import MessageRepository
from app.core.websocket.handlers import WebSocketHandlers
from app.domain.group.repository import GroupRepository
from app.domain.user.service import UserService
from app.domain.user.repository import UserRepository
from app.domain.group.router import router as group_router
from app.core.auth.router import router as auth_router
from app.domain.user.router import router as user_router
from app.domain.message.router import router as message_router
from app.core.exceptions.handlers import (
    chatroom_exception_handler,
    business_error_handler
)
from app.domain.user.models import User
from app.domain.user.schemas import Token, UserResponse, UserBaseAndStatus, UsersInfoDictResponse, UserDevice, UserMapInfo
from app.core.websocket.manager import ConnectionManager
from app.domain.message.handlers import MessageHandlers
from app.domain.group.repository import GroupMemberRepository
from app.domain.file.abc_check import abc_router

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Load environment variables
load_dotenv()

# Get SECRET_KEY
SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

ALGORITHM: str = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 初始化 Socket.IO 服务器配置
lprint(os.getcwd())
lprint("初始化Socket.IO服务器")

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,
    engineio_logger=False
)

# 初始化数据库管理器
DatabaseManager.init()

# 初始化仓储类
message_repo = MessageRepository()
group_repo = GroupRepository(SessionLocal)
user_repo = UserRepository(SessionLocal)
member_repo = GroupMemberRepository(SessionLocal)

# 初始化服务类
user_service = UserService(user_repo)

# 初始化连接管理器和处理器
connection_manager = ConnectionManager(sio)
websocket_handlers = WebSocketHandlers(connection_manager, sio)
message_handlers = MessageHandlers(
    connection_manager=connection_manager,
    private_repo=message_repo.private_repository,
    group_repo=message_repo._get_group_repository("default"),
    group_repository=group_repo,
    user_repo=user_repo,
    member_repo=member_repo
)
from app.domain.user.handlers import UserStatusHandler

# 在应用初始化部分
user_status_handler = UserStatusHandler(sio, connection_manager, user_repo)
user_status_handler.register_handlers()
# 注册消息处理器的事件处理函数
message_handlers.register_handlers()

# 初始化 FastAPI 应用
app = FastAPI(
    title="ChatRoom API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 初始化模板引擎
templates = Jinja2Templates(directory="app/templates")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化设备状态
async def init_device_status():
    """初始化所有设备的在线状态"""
    try:
        async with SessionLocal() as session:
            # 更新所有设备的在线状态为离线
            await session.execute(
                update(Device).values(login_status=False, 
                                    websocket_online=False)
            )
            await session.commit()
            lprint("已重置所有设备的在线状态为离线")
    except Exception as e:
        lprint(f"初始化设备状态失败: {str(e)}")
        raise e

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    try:
        lprint("后端服务启动...")
        
        # 初始化设备状态
        await init_device_status()
        
        lprint("所有初始化操作完成")
    except Exception as e:
        lprint(f"启动初始化失败: {str(e)}")
        traceback.print_exc()
        raise

# 覆盖默认 /docs 端点以自定义 Swagger UI
@app.get("/doc", include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    lprint("custom_swagger_ui_html")    
    return templates.TemplateResponse("swagger_custom.html", {"request": request})

# 获取数据库会话的依赖函数
async def get_db():
    """获取数据库会话"""
    async with SessionLocal() as session:
        yield session





async def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# 注册异常处理器
app.add_exception_handler(HTTPException, chatroom_exception_handler)
app.add_exception_handler(Exception, business_error_handler)

# 注册路由
app.include_router(group_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(message_router)
app.include_router(abc_router)

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
tracer.stop()
tracer.save("trace.json")
