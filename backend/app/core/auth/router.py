"""认证路由模块"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
import sys
import uuid
from datetime import datetime, timezone
import hashlib

sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from sqlalchemy import select, update
from app.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash
)
from app.db.database import AsyncSessionLocal
from app.domain.user.schemas import Token, UserBase
from app.domain.user.models import User
from app.domain.device.models import Device
from app.domain.device.repository import DeviceRepository

router = APIRouter(
    prefix="/api/auth",
    tags=["认证管理"],
    responses={404: {"description": "Not found"}},
)

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """用户登录"""
    try:
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 获取设备信息
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent", "")

        # 根据user-agent和username生成设备ID
        device_id_source = f"{user.username}:{user_agent}"
        device_id = hashlib.md5(device_id_source.encode()).hexdigest()

        lprint(f"生成设备ID: username={user.username}, user_agent={user_agent}, device_id={device_id}")

        # 创建或更新设备记录
        async with AsyncSessionLocal() as session:
            device_repo = DeviceRepository(session)
            # 检查设备是否存在
            device = await device_repo.get_device_by_id(device_id)

            if device:
                # 更新设备信息
                await device_repo.update_device_status(
                    device_id=device_id,
                    login_status=True,
                    system_info={
                        "ip_address": ip_address,
                        "user_agent": user_agent,
                        "last_login": datetime.now(timezone.utc).isoformat()
                    }
                )
            else:
                # 创建新设备记录
                device = Device(
                    device_id=device_id,
                    user_id=user.id,
                    device_name=f"{user_agent[:30]}...",  # 截断过长的设备名
                    login_status=True,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                session.add(device)

            await session.commit()

        # 创建访问令牌
        access_token = create_access_token(
            data={
                "sub": user.username,
                "device_id": device_id
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": user.username,
            "role": str(user.role.value),
            "nickname": user.nickname,
            "avatar_index": user.avatar_index,
            "device_id": device_id  # 返回设备ID给客户端保存
        }

    except Exception as e:
        lprint(f"登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register", response_model=UserBase)
async def register(
    username: str,
    password: str,
    email: str,
    role: str = "user",
    nickname: Optional[str] = None,
    is_temporary: bool = False
):
    """注册新用户"""
    try:
        async with AsyncSessionLocal() as session:
            # 检查用户名是否已存在
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已存在"
                )

            # 创建新用户
            hashed_password = get_password_hash(password)
            user = User(
                username=username,
                hashed_password=hashed_password,
                email=email,
                role=role,
                nickname=nickname or username,
                is_temporary=is_temporary
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            return UserBase.model_validate(user)

    except HTTPException as e:
        raise e
    except Exception as e:
        lprint(f"注册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=UserBase)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserBase.model_validate(current_user)