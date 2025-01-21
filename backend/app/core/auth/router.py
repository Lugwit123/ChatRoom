"""认证路由模块"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional

from app.core.auth.auth_facade import AuthFacade
from app.domain.user.facade.dto.user_dto import Token, UserBase, UserBaseAndStatus

router = APIRouter(
    prefix="/api/auth",
    tags=["认证管理"],
    responses={404: {"description": "Not found"}},
)

auth_facade = AuthFacade()

@router.post("/login", response_model=Token)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    return await auth_facade.login(request, form_data)

@router.post("/register", response_model=UserBaseAndStatus)
async def register(
    username: str,
    password: str,
    email: str,
    role: str = "user",
    nickname: Optional[str] = None,
    is_temporary: bool = False
):
    """注册新用户"""
    user = await auth_facade.register(
        username=username,
        password=password,
        email=email,
        role=role,
        nickname=nickname,
        is_temporary=is_temporary
    )
    return UserBaseAndStatus.from_orm(user)

@router.get("/me", response_model=UserBaseAndStatus)
async def read_users_me(current_user: UserBaseAndStatus = Depends(auth_facade.get_current_user)):
    """获取当前用户信息"""
    return current_user