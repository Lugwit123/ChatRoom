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

from app.db.facade.database_facade import DatabaseFacade
from app.core.auth.facade.auth_facade import AuthFacade
from app.core.auth.facade.auth_facade import get_auth_facade
from app.domain.common.models.tables import User
from app.domain.common.enums.user import UserRole, UserStatusEnum
from app.domain.user.internal.repository import UserRepository
from app.domain.user.facade.dto.user_dto import (
    UserCreate, UserUpdate, UserResponse, 
    UsersInfoDictResponse, UserMessageInfo, UserBase, UserMapInfo
)
from app.domain.user.facade.user_facade import UserFacade, get_user_facade
from app.domain.message.facade import get_message_facade
from app.domain.message.facade.message_facade import MessageFacade
from app.core.auth import get_current_user

auth_facade = get_auth_facade()
database_facade = DatabaseFacade()

# 路由器
router = APIRouter(
    prefix="/api/users",
    tags=["用户管理"],
    responses={404: {"description": "Not found"}},
)

get_current_user = auth_facade.get_current_user

@router.get("/online", response_model=List[UserBase])
async def get_online_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database_facade.get_session)
):
    """获取在线用户列表"""
    try:
        user_repo = UserRepository(db)
        users = await user_repo.get_online_users()
        return [UserBase.model_validate(user) for user in users]
    except Exception as e:
        lprint(f"获取在线用户列表失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("", response_model=List[UserBase])
async def get_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database_facade.get_session)
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
    user_facade: UserFacade = Depends(get_user_facade),
    message_facade: MessageFacade = Depends(get_message_facade)
) -> UsersInfoDictResponse:
    """获取用户映射信息
    
    Args:
        current_user: 当前登录用户，从token中获取
        user_facade: 用户门面类实例
        message_facade: 消息门面类实例
        
    Returns:
        UsersInfoDictResponse: 用户映射信息，包含当前用户信息和其他用户的信息及消息记录
    """
    try:
        if not current_user:
            lprint("当前用户为空")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current user is required"
            )
            
        # 获取用户映射和消息记录
        users_map = await user_facade.get_users_map(current_user)
        
        # 获取用户ID并转换为整数
        user_id = getattr(current_user, 'id', None)
        if user_id is None:
            raise ValueError("User ID is required")
            
        # 获取消息映射并添加到现有的用户映射中
        messages_map = await message_facade.get_user_messages_map(int(user_id))
        for username, user_info in users_map.user_map.items():
            user_info.messages = [msg.model_dump() for msg in messages_map.get(username, [])]
            
        return users_map
        
    except Exception as e:
        lprint(f"获取用户映射信息失败: {str(e)}", level=logging.ERROR)
        lprint(traceback.format_exc(), level=logging.ERROR)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户映射信息失败"
        )

@router.get("/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database_facade.get_session)
):
    """获取用户信息"""
    try:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        lprint(f"获取用户信息失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.put("/{username}", response_model=UserResponse)
async def update_user(
    username: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database_facade.get_session)
):
    """更新用户信息"""
    try:
        if current_user.username != username:
            raise HTTPException(status_code=403, detail="无权修改其他用户信息")
        
        user_repo = UserRepository(db)
        user = await user_repo.update_user(username, user_update)
        return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        lprint(f"更新用户信息失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.put("/{username}/status", response_model=UserResponse)
async def update_user_status(
    username: str,
    status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database_facade.get_session)
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
            
        return UserResponse.model_validate(await user_repo.get_by_username(username))
    except HTTPException:
        raise
    except Exception as e:
        lprint(f"更新用户状态失败: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户状态失败: {str(e)}"
        ) from e