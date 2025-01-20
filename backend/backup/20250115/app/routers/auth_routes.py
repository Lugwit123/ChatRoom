"""
认证相关的路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, List, Optional
from ..db import database
from ..db.schemas import User, Token
from ..core.auth import (
    authenticate_user, create_access_token,
    get_current_user, get_password_hash
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import Lugwit_Module as LM

lprint = LM.lprint

router = APIRouter()

@router.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    try:
        lprint(f"收到登录请求 - 用户名: {form_data.username}")
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            lprint(f"用户验证失败: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        access_token = create_access_token(data={"sub": user.username})
        lprint(f"用户登录成功: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        lprint(f"登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败"
        )
