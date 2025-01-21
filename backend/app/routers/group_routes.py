"""
群组相关的路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
from ..db import database
from ..db.schemas import User, Group, GroupResponse
from ..core.auth import get_current_user
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import Lugwit_Module as LM

lprint = LM.lprint

router = APIRouter()

@router.get("/api/groups", response_model=List[GroupResponse])
async def get_user_groups(current_user: User = Depends(get_current_user)):
    """获取用户的群组列表"""
    try:
        lprint(f"获取用户群组 - 用户: {current_user.username}")
        async with database.async_session() as session:
            # 查询用户所在的群组
            result = await session.execute(
                select(Group).where(Group.members.contains([current_user.username]))
            )
            groups = result.scalars().all()
            lprint(f"找到 {len(groups)} 个群组")
            return groups
            
    except Exception as e:
        lprint(f"获取用户群组失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户群组失败"
        )
