"""
认证门面类
提供统一的认证接口
"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

# 标准库
import os
from datetime import datetime, timedelta
from typing import Optional
import traceback
import uuid

# 第三方库
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

# 项目内部导入 - 只导入门面类和DTO
from app.domain.user.facade.user_facade import UserFacade
from app.domain.device.facade.device_facade import DeviceFacade
from app.domain.user.facade.dto.user_dto import Token, UserBaseAndStatus

# JWT相关配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")  # 从环境变量获取，如果没有则使用默认值
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class AuthFacade:
    """认证门面类"""
    
    def __init__(self):
        """初始化认证门面"""
        self.lprint = LM.lprint
        self.user_facade = UserFacade()
        self.device_facade = DeviceFacade()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.user_facade.verify_password(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return self.user_facade.get_password_hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> UserBaseAndStatus:
        """获取当前用户"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
            
        # 从用户门面获取用户信息
        user = await self.user_facade.get_user_by_username(username)
        if user is None:
            raise credentials_exception
        return user
    
    async def authenticate_user(self, username: str, password: str) -> Optional[UserBaseAndStatus]:
        """验证用户"""
        user = await self.user_facade.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    async def login(self, request: Request, form_data: OAuth2PasswordRequestForm) -> Token:
        """用户登录"""
        try:
            user = await self.authenticate_user(form_data.username, form_data.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # 获取客户端IP
            client_ip = request.client.host if request.client else "unknown"
            
            # 更新设备信息
            device_id = str(uuid.uuid4())
            await self.device_facade.update_device_status(user.id, device_id, client_ip)
            
            # 创建访问令牌
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = self.create_access_token(
                data={"sub": user.username, "device_id": device_id},
                expires_delta=access_token_expires
            )
            
            return Token(
                access_token=access_token,
                token_type="bearer",
                user_id=user.id,
                username=user.username,
                role=user.role,
                device_id=device_id
            )
            
        except Exception as e:
            self.lprint(f"登录失败: {str(e)}\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed"
            )
    
    async def register(self, username: str, password: str, email: str, 
                      role: str = "user", nickname: Optional[str] = None,
                      is_temporary: bool = False) -> UserBaseAndStatus:
        """注册新用户"""
        try:
            # 使用用户门面注册新用户
            return await self.user_facade.register(
                username=username,
                password=password,
                email=email,
                role=role,
                nickname=nickname,
                is_temporary=is_temporary
            )
                
        except HTTPException:
            raise
        except Exception as e:
            self.lprint(f"注册失败: {str(e)}\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
