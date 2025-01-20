"""认证逻辑"""
import sys
import os
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

# 标准库
from datetime import datetime, timedelta
from typing import Optional
import base64
import traceback
import json

# 第三方库
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# 本地模块
from app.domain.user.models import User
from app.utils.security import verify_password, get_password_hash

# 认证相关配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")  # 从环境变量获取，如果没有则使用默认值
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        lprint(f"创建访问令牌失败: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建访问令牌失败"
        )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # 从数据库获取用户
    user = await get_user(username)
    if user is None:
        raise credentials_exception
    return user

async def authenticate_user(username: str, password: str):
    """验证用户"""
    try:
        lprint(f"[用户认证] 开始验证用户: {username}")
        user = await get_user(username)
        if not user:
            lprint(f"[用户认证] 失败: 用户 {username} 不存在")
            return None
        if not verify_password(password, user.hashed_password):
            lprint(f"[用户认证] 失败: 用户 {username} 密码错误")
            return None
        lprint(f"[用户认证] 成功: 用户 {username} 验证通过")
        return user
    except Exception as e:
        lprint(f"[用户认证] 异常: {str(e)}\n{traceback.format_exc()}")
        return None

async def get_user(username: str):
    """从数据库获取用户"""
    try:
        lprint(f"[用户查询] 开始查询用户: {username}")
        from app.domain.user.service import UserService
        from app.domain.user.repository import UserRepository
        from app.db.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            user_service = UserService(user_repo)
            user = await user_service.get_by_username(username)
            if user:
                lprint(f"[用户查询] 成功: 找到用户 {username}")
            else:
                lprint(f"[用户查询] 失败: 未找到用户 {username}")
            return user
    except Exception as e:
        lprint(f"[用户查询] 异常: {str(e)}\n{traceback.format_exc()}")
        return None

async def authenticate_token(token: str):
    """验证令牌"""
    try:
        return await get_current_user(token)
    except Exception as e:
        lprint(f"验证令牌失败: {traceback.format_exc()}")
        return None
