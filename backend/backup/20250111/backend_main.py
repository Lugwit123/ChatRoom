# backend/backend_main.py

import os
import json
import logging
import sys
from logging_config import setup_logging
from pathlib import Path

import time

import uuid
import traceback
from datetime import datetime, timedelta
from typing import Optional, List, Set, Dict, Any

import socketio  # python-socketio
from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    Depends,
    status,
    BackgroundTasks,
    Request,
    Response,
    WebSocket
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from passlib.context import CryptContext
from dotenv import load_dotenv

import aiofiles


import schemas

from dependencies import get_current_user_response, get_current_user_db
from authenticate import create_access_token, authenticate_token, start_cleanup_task
from utils import generate_random_string, get_avatar_index
from connection_manager import ConnectionManager
from exception_handlers import http_exception_handler, general_exception_handler
from routers.check_file import add_check_file_static,abc_router  # 导入子路由

import user_database
import Lugwit_Module as LM


from ipaddress import ip_address

from message_handlers import MessageHandlers
from message_routes import router as message_router
from file_routes import router as file_router  # 新增导入

# Load environment variables
load_dotenv()

# Initialize logging

logging.info("Starting Chat App API")

API_URL = os.getenv("API_URL")
lprint = LM.lprint
lprint("Starting Chat App API", level=logging.error)
# Get SECRET_KEY
SECRET_KEY: str = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 6000

# Password hash configuration
pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*",logger=False)

# Initialize FastAPI app
app = FastAPI(
    title="Chat App API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
    debug=False
)

# Mount Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)


# Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_check_file_static(app)
# Bind template directory
templates = Jinja2Templates(directory="templates")
# 获取当前文件所在目录
cur_dir = Path(__file__).resolve().parent
# Mount static files (if needed)
app.mount("/static", StaticFiles(directory="static"), name="static")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
# 挂载静态文件
static_dir = cur_dir / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="abc_static")
# 包含子路由
from routers.check_file.abc_router import router
app.include_router(router)
app.include_router(message_router, prefix="/api")
app.include_router(file_router)  # 新增文件服务器路由，不加前缀
# Override default /docs endpoint with custom Swagger UI
@app.get("/doc", include_in_schema=True)
async def custom_swagger_ui_html(request: Request):
    return templates.TemplateResponse("swagger_custom.html", {"request": request})

# Initialize Connection Manager with sio_instance

manager = ConnectionManager(sio_instance=sio)

# 初始化消息处理器
message_handlers = MessageHandlers(manager, sio)


# Register user
@app.post("/register", response_model=schemas.Token)
async def register(user: schemas.UserRegistrationRequest) -> schemas.Token:
    valid_roles: Set[schemas.UserRole] = {schemas.UserRole.admin, schemas.UserRole.user, schemas.UserRole.system, schemas.UserRole.test}
    if user.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Valid roles include: {[role.value for role in valid_roles]}"
        )
    
    all_groups: List[str] = await user_database.get_all_groups()
    for group in user.groups:
        if group.name not in all_groups:
            raise HTTPException(
                status_code=400,
                detail=f"Group '{group.name}' does not exist"
            )
    
    try:
        await user_database.insert_user(
            username=user.username,
            nickname=user.nickname,
            password=user.password,
            email=user.email,
            role=user.role,
            group_names=[group.name for group in user.groups],
            is_temporary=False
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    access_token_expires: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token: str = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return schemas.Token(access_token=access_token, token_type="bearer")

# User login
@app.post("/api/auth/login", response_model=schemas.Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
) -> schemas.Token:
    # 添加详细的日志记录
    lprint(f"收到登录请求 - 用户名: {form_data.username}", level=logging.info)
    
    # 验证客户端 IP
    client_host = request.client.host
    lprint(f"客户端 IP: {client_host}", level=logging.info)
    
    try:
        client_ip = ip_address(client_host)
        # if not (
        #     client_ip.is_loopback or  # localhost/127.0.0.1
        #     str(client_ip) == "192.168.112.73"  # 本机 IP
        # ):
        #     lprint(f"IP 地址验证失败: {client_ip}", level=logging.warning)
        #     raise HTTPException(
        #         status_code=403,
        #         detail="只允许本机登录"
        #     )
    except ValueError:
        lprint(f"无效的 IP 地址: {client_host}", level=logging.error)
        raise HTTPException(
            status_code=400,
            detail="无效的 IP 地址"
        )

    # 原有的登录逻辑
    lprint("开始验证用户凭据...", level=logging.info)
    user: Optional[schemas.UserBase] = await user_database.fetch_user(form_data.username)
    
    if not user:
        lprint(f"用户不存在: {form_data.username}", level=logging.warning)
        raise HTTPException(status_code=400, detail="用户名或密码错误")
        
    if not pwd_context.verify(form_data.password, user.hashed_password):
        lprint(f"密码验证失败: {form_data.username}", level=logging.warning)
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    
    lprint(f"用户验证成功: {form_data.username}", level=logging.info)
    
    # 生成 token
    access_token_expires: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token: str = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    lprint(f"生成访问令牌成功 - 用户: {user.username}, 过期时间: {access_token_expires}", level=logging.info)
    
    # 返回 token
    response = schemas.Token(access_token=access_token, token_type="bearer")
    lprint(f"登录成功 - 用户: {user.username}", level=logging.info)
    
    return response

@app.get("/")
def read_root() -> dict:
    return {"message": "Hello, World!"}

# Delete user
@app.delete("/api/delete_user")
async def delete_user_endpoint(
    user_delete: schemas.DeleteUserRequest,
    current_user: schemas.UserBase = Depends(get_current_user_db)
) -> dict:
    if current_user.role != schemas.UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to delete user")

    try:
        await user_database.delete_user(user_delete.username)
        return {"status": "success", "detail": f"User {user_delete.username} has been deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting user")

# Get user list
@app.get("/api/users", response_model=schemas.UserListResponse)
async def get_user_list(
    current_user: schemas.UserBase = Depends(get_current_user_db)
) -> schemas.UserListResponse:
    try:
        users_in_db: List[schemas.UserBaseAndStatus] = \
            await user_database.fetch_registered_users(
                    current_username=current_user.username,
                    exclude_types=[])
        
        # 添加日志记录
        lprint(f"获取到用户列表: {users_in_db}", level=logging.info)
        
        for user_detail in users_in_db:
            user_detail.online = user_detail.username in manager.active_connections
            # 添加获取20条消息记录的代码
            user_detail.messages = await user_database.get_chat_history(user_detail.username, current_user, 1)
            
    
        current_user_info = schemas.UserResponse(
            id=current_user.id,
            username=current_user.username,
            nickname=current_user.nickname,
            email=current_user.email,
            groups=current_user.groups,
            role=current_user.role,
            avatar_index=current_user.avatar_index
        )
        
        response = schemas.UserListResponse(
            current_user=current_user_info, 
            users=users_in_db
        )
        
        # 验证响应数据
        lprint(f"get_user_list_返回的响应数据: {response}", level=logging.info)
        return response
        
    except Exception as e:
        lprint(traceback.format_exc(), level=logging.error)
        raise HTTPException(
            status_code=500,
            detail=f"获取用户列表失败: {str(e)}"
        )

@app.get("/api/users_map", response_model=schemas.UsersInfoDictResponse)
async def get_user_map(
    current_user: schemas.UserBase = Depends(get_current_user_db)
) -> schemas.UsersInfoDictResponse:
    try:
        users_in_db: List[schemas.UserBaseAndStatus] = \
            await user_database.fetch_registered_users(
                    current_username=current_user.username,
                    exclude_types=[])
        
        # 添加日志记录
        lprint(f"获取到用户列表: {users_in_db}", level=logging.info)
        users_dict={}
        for user_detail in users_in_db:
            user_detail.online = user_detail.username in manager.active_connections
            # 添加获取20条消息记录的代码
            user_detail.messages = await user_database.get_chat_history(user_detail.username, current_user, 100)
            users_dict[user_detail.username]=user_detail

    
        current_user_info = schemas.UserResponse(
            id=current_user.id,
            username=current_user.username,
            nickname=current_user.nickname,
            email=current_user.email,
            groups=current_user.groups,
            role=current_user.role,
            avatar_index=current_user.avatar_index
        )
        user_map_response=schemas.UsersInfoDictResponse(
            user_map=users_dict,
            current_user=current_user_info)
        

        return user_map_response
        
    except Exception as e:
        lprint(traceback.format_exc(), level=logging.error,popui=False)
        raise HTTPException(
            status_code=500,
            detail=traceback.format_exc()
        )

    
# Send message via API
@app.post("/send_message")
async def send_message(
    request : schemas.SendMessageRequest ,
    current_user: schemas.UserBase = Depends(get_current_user_db)
    )->dict:
    # 构建消息数据
    lprint(locals(),popui=False)
    message_data = schemas.MessageBase(**(request.model_dump()))
    message_data.direction = schemas.MessageDirection.REQUEST
    # 使用 Socket.IO 发送消息
    try:
        await sio.emit('message', message_data.model_dump_json(),)
    except:
        lprint(traceback.format_exc(),popui=False)

    return {"status": "success", "detail": "Message sent via Socket.IO"}

# Get all group information
@app.get("/get_all_groups")
async def get_groups() -> dict:
    """获取所有群组的详细信息"""
    try:
        groups: List[schemas.GroupResponse] = await user_database.get_all_groups_info()
        return {
            "status": "success",
            "data": [group.model_dump() for group in groups]
        }
    except Exception as e:
        lprint(traceback.format_exc(),popui=False)
        raise HTTPException(
            status_code=500,
            detail="获取群组信息时出错"
        )

# 获取所有组的基本信息
@app.get("/api/groups", response_model=List[schemas.GroupResponse])
async def get_all_groups_endpoint():
    try:
        # 获取所有群组信息
        groups = await user_database.get_all_groups_info()
        return groups
    except Exception as e:
        logging.error(f"获取群组信息失败: {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail="获取群组信息失败"
        )

@app.get("/api/groups/{group_id}/members", response_model=List[schemas.UserBase])
async def get_members_of_group(group_id: int):
    try:
        members = await user_database.get_group_members(group_id)
        if members is None:
            raise HTTPException(status_code=404, detail="Group not found")
        return members
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error fetching members for group_id {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 获取特定组的成员

    
# Announcement route
@app.get("/announcement")
async def get_announcement() -> dict:
    markdown_path: str = os.path.join(os.path.dirname(__file__), 'announcement.md')
    if not os.path.exists(markdown_path):
        return {"error": "Announcement file does not exist"}
    async with aiofiles.open(markdown_path, 'r', encoding='utf-8') as f:
        content: str = await f.read()
    return {"content": content}

# Get chat history
@app.post("/api/get_messages", response_model=schemas.MessageBase)
async def get_messages(
    request: schemas.MessagesRequest,
    current_user: schemas.UserBase = Depends(get_current_user_db),
) -> schemas.MessageBase:
    '''
    当 message_type 为 GET_USERS 时:
    - content 字段应为 UserListResponse 类型
    - recipient_type 应为 'private'
    - status 应为 'unread'
    - message_content_type 应为 MessageContentType.PLAIN_TEXT
    如果chat_id为数字自动转换���用户名'''
    messages_nums=request.messages_nums
    if isinstance(request.chat_id, int):
        user = (await user_database.fetch_user(request.chat_id))
        request.chat_id  = user.username
    try:
        messages_data: List[schemas.MessageBase] = \
            await user_database.get_chat_history(request.chat_id, 
                                                current_user, 
                                                messages_nums)
        # 修改返回空消息的情况
        if not messages_data:
            return schemas.MessageBase(
                sender="system",
                recipient=request.chat_id,
                content=[],  # 返回空数组而不是字符串
                id="no_messages",
                timestamp=datetime.now(),
                message_type=schemas.MessageType.CHAT_HISTORY
            )

        # 有消息的情况
        return schemas.MessageBase(
            sender="system",
            recipient=request.chat_id,
            content=[{**x.model_dump(), "content": str(x.content)} for x in messages_data],  # 创建新字典并转换content为字符串
            timestamp=datetime.now(),
            id="chat_history",
            message_type=schemas.MessageType.CHAT_HISTORY,
            direction=schemas.MessageDirection.RESPONSE,
            status=[schemas.MessageStatus.SUCCESS]
        )
    except Exception as e:
        lprint(traceback.format_exc(), popui=False)
        raise HTTPException(status_code=500, detail=traceback.format_exc()
                            , headers={"Content-Type": "text/plain"})



# File upload
@app.post("/upload")
async def uploads(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        ext = file.filename.split('.')[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        async with aiofiles.open(filepath, "wb") as buffer:
            await buffer.write(contents)

        image_url = f"http://192.168.112.73:1026/uploads/{filename}"
        response = {
            "errno": 0,
            "data":  {
                "url": image_url
            },
        }

        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"errno": 1, "message": str(e)}, status_code=500)

# 提供检查结果的页面
@app.get("/check/{validation_type}/{check_id}")
async def get_check_result(validation_type: str, check_id: int, request: Request):
    # 假设每个检查结果对应一个JSON文件，命名为 {validation_type}_{check_id}.json
    check_file = os.path.join("A:/temp/", f"{validation_type}_{check_id}.json")
    if not os.path.exists(check_file):
        raise HTTPException(status_code=404, detail="检查结果文件不在")
    
    # 读取JSON数据
    async with aiofiles.open(check_file, "r", encoding="utf-8") as f:
        try:
            check_data = json.loads(await f.read())
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="检查结果文件格式错误")
    
    # 渲染检查结果到HTML模板
    return templates.TemplateResponse("check_result.html", {"request": request, "check_data": check_data})

# 批量删除用户
@app.delete("/users/batch_delete")
async def batch_delete_users(
    current_user: schemas.UserBase = Depends(get_current_user_db)
) -> dict:
    # 检查权限：系统用户或管理员可以删除
    if current_user.role not in [schemas.UserRole.admin, schemas.UserRole.system]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="只有系统用户或管理员可以批量删除用户"
        )

    try:
        # 获取所有 id > 20 的用户
        users_to_delete = await user_database.fetch_users_by_condition(
            condition="id > 20"
        )
        
        # 记录删除的用户名
        deleted_usernames = []
        
        # 批量删除用户
        for user in users_to_delete:
            try:
                # 不允许删除系统用户和管理员
                if user.role in [schemas.UserRole.admin, schemas.UserRole.system]:
                    logging.warning(f"跳过删除系统用户或管理员: {user.username}")
                    continue
                    
                await user_database.delete_user(user.username)
                deleted_usernames.append(user.username)
                logging.info(f"已删除用户: {user.username}")
            except Exception as e:
                logging.error(f"删除用户 {user.username} 失败: {e}")
                continue

        return {
            "status": "success",
            "detail": f"成功删除 {len(deleted_usernames)} 个用户",
            "deleted_users": deleted_usernames
        }
        
    except Exception as e:
        logging.error(f"批量删除用户时出错: {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"批量删除用户时出错: {str(e)}"
        )

@app.get("/api/click/{check_id}")
async def message_clicked(check_id:int):
    lprint(check_id)
    return check_id
    
# 在 backend_main.py 中添加验证 token 的端点
@app.get("/verify-token")
async def verify_token(
    current_user: schemas.UserBase = Depends(get_current_user_db)
) -> dict:
    """
    验证 token 的有效性
    如果 token 无效会由 get_current_user_db 抛出 401 错误
    """
    return {
        "status": "success",
        "detail": "Token is valid",
        "user": {
            "username": current_user.username,
            "role": current_user.role
        }
    }

# 在应用启动时启动清理任务
@app.on_event("startup")
async def startup_event():
    start_cleanup_task()
