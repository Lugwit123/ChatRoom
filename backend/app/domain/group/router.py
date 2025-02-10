"""群组管理路由模块"""
import sys
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.facade.database_facade import DatabaseFacade
from app.domain.common.models.tables import User
from app.domain.common.enums.group import GroupMemberRole
from app.domain.group.facade.dto.group_dto import (
    GroupCreate, 
    GroupResponse, 
    GroupMemberInfo,
    GroupMemberCreate,
    GroupMemberUpdate,
    GroupListResponse,
    GroupMemberListResponse
)

sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from app.domain.group.facade.group_facade import GroupFacade, get_group_facade
from fastapi import APIRouter, Depends, HTTPException, status

database_facade = DatabaseFacade()

router = APIRouter(
    prefix="/api/groups",
    tags=["群组管理"],
    responses={404: {"description": "Not found"}},
)

@router.post("", response_model=GroupResponse)
async def create_group(
    group: GroupCreate,
    current_user: User = Depends(get_current_user),
    group_facade: GroupFacade = Depends(get_group_facade)
) -> GroupResponse:
    """创建新群组"""
    try:
        result = await group_facade.create_group(group, current_user)
        if result.success:
            return result.data
        raise HTTPException(status_code=400, detail=result.message)
    except Exception as e:
        lprint(f"创建群组失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=GroupListResponse)
async def get_groups(
    current_user: User = Depends(get_current_user),
    group_facade: GroupFacade = Depends(get_group_facade)
) -> GroupListResponse:
    """获取群组列表"""
    try:
        result = await group_facade.get_groups(current_user)
        if result.success:
            return result.data
        raise HTTPException(status_code=400, detail=result.message)
    except Exception as e:
        lprint(f"获取群组列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    group_facade: GroupFacade = Depends(get_group_facade)
) -> GroupResponse:
    """获取群组信息"""
    try:
        result = await group_facade.get_group(group_id)
        if result.success:
            return result.data
        raise HTTPException(status_code=400, detail=result.message)
    except Exception as e:
        lprint(f"获取群组信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{group_id}/members", response_model=GroupMemberInfo)
async def add_member(
    group_id: str,
    member: GroupMemberCreate,
    current_user: User = Depends(get_current_user),
    group_facade: GroupFacade = Depends(get_group_facade)
) -> GroupMemberInfo:
    """添加群组成员"""
    try:
        result = await group_facade.add_member(group_id, member, current_user)
        if result.success:
            return result.data
        raise HTTPException(status_code=400, detail=result.message)
    except Exception as e:
        lprint(f"添加群组成员失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}/members", response_model=GroupMemberListResponse)
async def get_members(
    group_id: str,
    current_user: User = Depends(get_current_user),
    group_facade: GroupFacade = Depends(get_group_facade)
) -> GroupMemberListResponse:
    """获取群组成员列表"""
    try:
        result = await group_facade.get_members(group_id)
        if result.success:
            return result.data
        raise HTTPException(status_code=400, detail=result.message)
    except Exception as e:
        lprint(f"获取群组成员列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{group_id}/members/{user_id}", response_model=GroupMemberInfo)
async def update_member(
    group_id: str,
    user_id: str,
    member: GroupMemberUpdate,
    current_user: User = Depends(get_current_user),
    group_facade: GroupFacade = Depends(get_group_facade)
) -> GroupMemberInfo:
    """更新群组成员信息"""
    try:
        result = await group_facade.update_member(group_id, user_id, member, current_user)
        if result.success:
            return result.data
        raise HTTPException(status_code=400, detail=result.message)
    except Exception as e:
        lprint(f"更新群组成员信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{group_id}/members/{user_id}")
async def remove_member(
    group_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    group_facade: GroupFacade = Depends(get_group_facade)
):
    """移除群组成员"""
    try:
        result = await group_facade.remove_member(group_id, user_id, current_user)
        if result.success:
            return {"message": "成员已移除"}
        raise HTTPException(status_code=400, detail=result.message)
    except Exception as e:
        lprint(f"移除群组成员失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{group_id}/join")
async def join_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    group_facade: GroupFacade = Depends(get_group_facade)
):
    """加入群组"""
    try:
        result = await group_facade.join_group(group_id, current_user)
        if result.success:
            return {"message": "已成功加入群组"}
        raise HTTPException(status_code=400, detail=result.message)
    except Exception as e:
        lprint(f"加入群组失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{group_id}/leave")
async def leave_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    group_facade: GroupFacade = Depends(get_group_facade)
):
    """退出群组"""
    try:
        result = await group_facade.leave_group(group_id, current_user)
        if result.success:
            return {"message": "已成功退出群组"}
        raise HTTPException(status_code=400, detail=result.message)
    except Exception as e:
        lprint(f"退出群组失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    group_facade: GroupFacade = Depends(get_group_facade)
):
    """删除群组"""
    try:
        result = await group_facade.delete_group(group_id, current_user)
        if result.success:
            return {"message": "群组已删除"}
        raise HTTPException(status_code=400, detail=result.message)
    except Exception as e:
        lprint(f"删除群组失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
