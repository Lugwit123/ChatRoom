"""认证路由模块"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.param_functions import Form
from sqlalchemy.ext.asyncio import AsyncSession

import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from app.core.auth.facade.auth_facade import AuthFacade
from app.core.auth.facade.dto.auth_dto import Token
from app.domain.user.facade.dto.user_dto import UserBaseAndDevices, UserLoginDTO
from app.core.auth.facade.auth_facade import get_auth_facade
from app.domain.common.enums.user import UserRole

# 自定义OAuth2PasswordRequestForm，添加nickname字段
class OAuth2PasswordRequestFormWithNickname(OAuth2PasswordRequestForm):
    def __init__(
        self,
        username: str = Form(...),
        password: str = Form(...),
        grant_type: Optional[str] = Form(None, regex="password"),
        scope: str = Form(""),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
        nickname: Optional[str] = Form(None),  # 添加nickname字段
    ):
        super().__init__(
            username=username,
            password=password,
            grant_type=grant_type,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
        )
        self.nickname = nickname  # 保存nickname

router = APIRouter(prefix="/api/auth", tags=["认证"])
auth_facade = get_auth_facade()


@router.post("/login", response_model=Token)
async def login(request: Request, form_data: OAuth2PasswordRequestFormWithNickname = Depends()):
    """用户登录"""
    
    return await auth_facade.login(request, form_data)

@router.post("/register", response_model=UserBaseAndDevices)
async def register(
    username: str,
    password: str,
    email: str = None,
    role: int = UserRole.user.value,
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

@router.get("/me", response_model=UserBaseAndDevices)
async def read_users_me(current_user: UserBaseAndDevices = Depends(auth_facade.get_current_user)):
    """获取当前用户信息"""
    return current_user