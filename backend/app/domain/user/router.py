"""用户管理路由模块"""
import sys
import traceback
import logging
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from app.db.database import get_db
from app.core.auth.auth import get_current_user
from app.domain.user.models import User
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import (
    UserResponse,
    UserBaseAndStatus,
    UsersInfoDictResponse,
    UserUpdate,
    UserCreate,
    UserBase
)

router = APIRouter(
    prefix="/api/users",
    tags=["用户管理"],
    responses={404: {"description": "Not found"}},
)

@router.get("/online", response_model=List[UserBase])
async def get_online_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取在线用户列表"""
    try:
        user_repo = UserRepository(db)
        users = await user_repo.get_online_users()
        return [UserBase.model_validate(user) for user in users]
    except Exception as e:
        lprint(f"获取在线用户列表失败: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取在线用户列表失败: {str(e)}"
        ) from e

@router.get("", response_model=List[UserBase])
async def get_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表"""
    try:
        user_repo = UserRepository(db)
        users = await user_repo.get_users()
        return [UserBase.model_validate(user) for user in users]
    except Exception as e:
        lprint(f"获取用户列表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.get("/users_map", response_model=UsersInfoDictResponse)
async def get_users_map(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UsersInfoDictResponse:
    """获取用户映射信息"""
    lprint("开始获取用户映射信息")
    try:
        # 获取当前用户和所有用户信息
        user_repo = UserRepository(db)
        current_user = await user_repo.get_by_username(current_user.username)
        users = await user_repo.get_registered_users()
        
        # 构建用户映射，不包含当前用户
        user_map = {}
        for user in users:
            if user.id != current_user.id:  # 排除当前用户
                user_dict = user.to_dict(current_user_id=current_user.id)  # 传入当前用户ID以获取消息记录
                user_map[user.username] = UserBaseAndStatus(**user_dict)
        
        # 当前用户不需要消息记录
        current_user_dict = current_user.to_dict()
        current_user_response = UserResponse(**current_user_dict)
        
        lprint(f"成功获取用户映射信息，当前用户: {current_user.username}, 总用户数: {len(users)}")
        
        return UsersInfoDictResponse(
            current_user=current_user_response,
            user_map=user_map
        )
        
    except Exception as e:
        lprint(f"获取用户映射信息失败: {str(e)}", level=logging.ERROR)
        lprint(traceback.format_exc(), level=logging.ERROR)
        raise HTTPException(
            status_code=500,
            detail="获取用户映射信息失败"
        ) from e

@router.get("/{username}", response_model=UserBase)
async def get_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户信息"""
    try:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return UserBase.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        lprint(f"获取用户信息失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.put("/{username}", response_model=UserBase)
async def update_user(
    username: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户信息"""
    try:
        if current_user.username != username:
            raise HTTPException(status_code=403, detail="无权修改其他用户信息")
        
        user_repo = UserRepository(db)
        user = await user_repo.update_user(username, user_update)
        return UserBase.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        lprint(f"更新用户信息失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.put("/{username}/status", response_model=dict)
async def update_user_status(
    username: str,
    status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户状态"""
    try:
        # 检查权限
        if current_user.role != UserRole.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以修改用户状态"
            )
            
        # 更新状态
        user_repo = UserRepository(db)
        success = await user_repo.update_status(username, status)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新用户状态失败"
            )
            
        return {"message": "用户状态更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        lprint(f"更新用户状态失败: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户状态失败: {str(e)}"
        ) from e