"""用户路由"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.domain.user.service import UserService
from app.domain.user.repository import UserRepository
from app.core.auth import get_current_user
from app.db.schemas import User, UserResponse

router = APIRouter()

@router.get("/users/", response_model=List[UserResponse])
async def get_users(current_user: User = Depends(get_current_user)):
    """获取用户列表"""
    try:
        user_repo = UserRepository()
        return await user_repo.get_all_users()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{username}", response_model=UserResponse)
async def get_user(username: str, current_user: UserResponse = Depends(get_current_user)):
    """获取指定用户信息"""
    try:
        user_repo = UserRepository()
        user = await user_repo.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{username}")
async def update_user(
    username: str,
    nickname: str = None,
    email: str = None,
    current_user: User = Depends(get_current_user)
):
    """更新用户信息"""
    try:
        if current_user.username != username and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
        
        user_repo = UserRepository()
        user = await user_repo.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        update_data = {}
        if nickname is not None:
            update_data["nickname"] = nickname
        if email is not None:
            update_data["email"] = email
            
        await user_repo.update_user(username, update_data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
