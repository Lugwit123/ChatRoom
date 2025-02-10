"""认证路由模块"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from app.core.auth.facade.auth_facade import AuthFacade
from app.core.auth.facade.dto.auth_dto import Token
from app.domain.user.facade.dto.user_dto import UserBaseAndStatus, UserLoginDTO
from app.core.auth.facade.auth_facade import get_auth_facade

router = APIRouter(prefix="/api/auth", tags=["认证"])
auth_facade = get_auth_facade()


@router.post("/login", response_model=Token)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    
    return await auth_facade.login(request, form_data)

@router.post("/register", response_model=UserBaseAndStatus)
async def register(
    username: str,
    password: str,
    email: str = None,
    role: str = "user",
    nickname: str = None,
    is_temporary: bool = False
):
    """用户注册"""
    return await auth_facade.register(
        username=username,
        password=password,
        email=email,
        role=role,
        nickname=nickname,
        is_temporary=is_temporary
    )

@router.get("/me", response_model=UserBaseAndStatus)
async def read_users_me(current_user: UserBaseAndStatus = Depends(auth_facade.get_current_user)):
    """获取当前用户信息"""
    return current_user