"""群组路由模块"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
import sys

sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from app.core.auth import get_current_user
from app.domain.user.models import User
from app.domain.group.schemas import GroupBase, GroupCreate, GroupResponse, GroupMemberResponse
from .repository import GroupRepository
from app.db import DatabaseManager

router = APIRouter(
    prefix="/api/groups",
    tags=["群组管理"],
    responses={404: {"description": "Not found"}},
)

async def get_group_repo():
    """获取群组仓储"""
    session = DatabaseManager.get_session()
    try:
        yield GroupRepository(session)
    finally:
        await session.close()

@router.post("", response_model=GroupResponse)
async def create_group(
    group: GroupCreate,
    current_user: User = Depends(get_current_user),
    group_repo: GroupRepository = Depends(get_group_repo)
):
    """创建群组"""
    try:
        group_db = await group_repo.create_group(group.name, group.description, current_user.id)
        return GroupResponse.model_validate(group_db)
    except Exception as e:
        lprint(f"创建群组失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[GroupResponse])
async def get_groups(
    current_user: User = Depends(get_current_user),
    group_repo: GroupRepository = Depends(get_group_repo)
):
    """获取群组列表"""
    try:
        groups = await group_repo.get_user_groups(current_user.id)
        return [GroupResponse.model_validate(group) for group in groups]
    except Exception as e:
        lprint(f"获取群组列表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    group_repo: GroupRepository = Depends(get_group_repo)
):
    """获取群组详情"""
    try:
        # 验证用户是否是群组成员
        if not await group_repo.is_group_member(group_id, current_user.id):
            raise HTTPException(status_code=403, detail="您不是该群组的成员")
        
        group = await group_repo.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="群组不存在")
        
        return GroupResponse.model_validate(group)
    except HTTPException:
        raise
    except Exception as e:
        lprint(f"获取群组详情失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{group_id}/members/{username}", response_model=GroupMemberResponse)
async def add_group_member(
    group_id: int,
    username: str,
    current_user: User = Depends(get_current_user),
    group_repo: GroupRepository = Depends(get_group_repo)
):
    """添加群组成员"""
    try:
        member = await group_repo.add_member(group_id, username, current_user.id)
        return GroupMemberResponse.model_validate(member)
    except Exception as e:
        lprint(f"添加群组成员失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{group_id}/members/{username}", response_model=dict)
async def remove_group_member(
    group_id: int,
    username: str,
    current_user: User = Depends(get_current_user),
    group_repo: GroupRepository = Depends(get_group_repo)
):
    """移除群组成员"""
    try:
        await group_repo.remove_member(group_id, username, current_user.id)
        return {"message": "成员已移除"}
    except Exception as e:
        lprint(f"移除群组成员失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
