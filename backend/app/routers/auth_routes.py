"""认证路由"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.core.auth import (
    authenticate_user, create_access_token,
    get_current_user, get_password_hash
)
from app.domain.user.repository import UserRepository
from app.db.schemas import User, Token, UserResponse

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """获取访问令牌"""
    try:
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

@router.post("/register/")
async def register(
    username: str,
    password: str,
    email: str,
    role: str = "user",
    nickname: str = None,
    is_temporary: bool = False
):
    """注册新用户"""
    try:
        user_repo = UserRepository()
        
        # 检查用户名是否已存在
        existing_user = await user_repo.get_by_username(username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
            
        # 创建新用户
        hashed_password = get_password_hash(password)
        user_data = {
            "username": username,
            "hashed_password": hashed_password,
            "email": email,
            "role": role,
            "nickname": str(nickname) if nickname else username,
            "is_temporary": is_temporary
        }
        
        await user_repo.create(User(**user_data))
        return {"status": "success", "message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
