# authenticate.py
from functools import lru_cache
from datetime import datetime, timedelta
import jwt
import logging
from typing import Optional
from fastapi import HTTPException, status
from user_database import fetch_user
from dotenv import load_dotenv
import os
from jwt import PyJWTError
import traceback
import Lugwit_Module as LM
import asyncio
import schemas

# 加载环境变量
load_dotenv()
SECRET_KEY: str = os.getenv("SECRET_KEY", "")
ALGORITHM: str = "HS256"

# 添加缓存装饰器，缓存用户认证结果
@lru_cache(maxsize=100)
def decode_token(token: str) -> dict:
    """解码并验证 token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证信息",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except PyJWTError as e:
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 添加用户缓存
user_cache = {}

async def authenticate_token(token: str) -> schemas.UserBase:
    """验证 token 并返回用户信息"""
    try:
        # 先解码 token
        payload = decode_token(token)
        username = payload.get("sub")
        
        # 检查缓存
        cached_user = user_cache.get(username)
        if cached_user:
            # 检查缓存是否过期
            if cached_user.get("timestamp", 0) > datetime.now().timestamp() - 300:  # 5分钟缓存
                return cached_user["user"]
        
        # 如果没有缓存或缓存过期，从数据库获取
        user = await fetch_user(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 更新缓存
        user_cache[username] = {
            "user": user,
            "timestamp": datetime.now().timestamp()
        }
        
        return user
        
    except Exception as e:
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=1500000)
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logging.error(f"创建 token 失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token 创建失败"
        )

# 定期清理过期缓存
async def cleanup_cache():
    """清理过期的用户缓存"""
    while True:
        try:
            current_time = datetime.now().timestamp()
            expired_keys = [
                key for key, value in user_cache.items()
                if value["timestamp"] < current_time - 300  # 5分钟过期
            ]
            for key in expired_keys:
                del user_cache[key]
            await asyncio.sleep(60)  # 每分钟检查一次
        except Exception as e:
            logging.error(f"清理缓存时出错: {e}")
            await asyncio.sleep(60)

# 在应用启动时启动清理任务
def start_cleanup_task():
    asyncio.create_task(cleanup_cache())
