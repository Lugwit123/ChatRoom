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
from typing import Optional, cast, Any, Dict
import traceback
import uuid
import hashlib
from zoneinfo import ZoneInfo
import time
import random
import socket

# 第三方库
from fastapi import Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt, ExpiredSignatureError
from jose.exceptions import ExpiredSignatureError  # 确保导入此异常

# 项目内部导入
from app.domain.common.models.tables import User
from app.domain.user.facade.dto.user_dto import UserBaseAndDevices
from app.domain.common.enums import UserRole, UserStatusEnum
from .dto.auth_dto import Token, UserAuthDTO, UserAuthInternalDTO, LoginResponseDTO
from ..internal.repository.auth_repository import get_auth_repository
from app.core.base.core_facade import CoreFacade
from app.core.events.services import TokenService, PasswordService
from app.domain.base.facade.dto.base_dto import ResponseDTO
from app.core.events.services import Services
from app.core.events.interfaces import (
    EventType, UserEvent, Event, BaseEvent
)
from app.core.auth.internal.repository.auth_repository import AuthRepository
from app.core.services.service_core import get_device_facade, get_user_facade
from app.utils.common import generate_device_id
from app.utils.security import verify_password
# 自定义异常
class AuthenticationError(Exception):
    """认证错误"""
    def __init__(self, message: str, error_type: str = "authentication_error"):
        self.message = message
        self.error_type = error_type
        super().__init__(message)

# JWT相关配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")  # 从环境变量获取，如果没有则使用默认值
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 改为24小时

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class AuthFacade(CoreFacade):
    """认证门面类"""
    
    def __init__(self):
        """初始化认证门面"""
        super().__init__()
        self._repository = AuthRepository()
        self._token_service = Services.resolve(TokenService) or TokenService()
        self._password_service = Services.resolve(PasswordService) or PasswordService()
        self._event_bus = Services.get_event_bus()
        self._user_facade = get_user_facade()  # 直接初始化，不使用延迟加载
        self.client_ip = ""
        self._device_facade = get_device_facade()
        
        # 注册服务
        if not Services.resolve(TokenService):
            Services.register_service(TokenService.__name__, self._token_service)
        if not Services.resolve(PasswordService):
            Services.register_service(PasswordService.__name__, self._password_service)
    
    @property
    def device_facade(self):
        """延迟加载设备门面"""
        if self._device_facade is None:
            from app.domain.device.facade.device_facade import DeviceFacade
            self._device_facade = DeviceFacade()
        return self._device_facade


    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return self._password_service.get_password_hash(password)
    
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
    
    def extract_token_from_header(self, auth_header: str) -> Optional[str]:
        """从认证头中提取token"""
        if auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        return None

    def extract_token_from_environ(self, environ: dict) -> Optional[str]:
        """从environ中提取token"""
        auth_header = environ.get('HTTP_AUTHORIZATION', '')
        return self.extract_token_from_header(auth_header)

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except ExpiredSignatureError:
            # 令牌过期时尝试刷新
            try:
                return await self.refresh_token(token)
            except Exception:
                raise AuthenticationError("令牌已过期且无法刷新", "token_expired")
        except JWTError:
            raise AuthenticationError("无效的令牌", "invalid_token")

    async def refresh_token(self, expired_token: str) -> Dict[str, Any]:
        """刷新过期的令牌"""
        try:
            # 即使令牌过期也尝试解码获取用户信息
            payload = jwt.decode(expired_token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
            username = payload.get("sub")
            if not username:
                raise AuthenticationError("无效的令牌", "invalid_token")
                
            # 创建新的访问令牌
            new_token = self.create_access_token(data={"sub": username})
            return jwt.decode(new_token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception as e:
            raise AuthenticationError(f"令牌刷新失败: {str(e)}", "refresh_failed")

    async def get_current_user(self, token: str) -> Optional[User]:
        """获取当前用户"""
        try:
            lprint(f"开始验证token: {token[:10]}...")
            
            # 解码token
            payload = await self.decode_token(token)
            if not payload:
                lprint("Token解码失败")
                return None
                
            lprint(f"Token解码成功，payload: {payload}")
            
            # 获取用户名
            username = payload.get('sub')
            if not username:
                lprint("Token中缺少用户名(sub)")
                return None
                
            lprint(f"从Token中获取到用户名: {username}")
            
            # 获取用户
            user = await self._user_facade.get_user_by_username(username)
            if not user:
                lprint(f"未找到用户: {username}")
                return None
                
            lprint(f"成功获取用户信息: id={user.id}, username={user.username}")
            return user
            
        except AuthenticationError as e:
            lprint(f"认证错误: {e.message}")
            # 这里可以返回一个特定的响应，提示用户重新登录
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token已过期，请重新登录"
            )
        except Exception as e:
            lprint(f"验证当前用户时发生错误: {str(e)}")
            print(f"错误详情: {traceback.format_exc()}")
            return None


    async def decode_token(self, token: str) -> dict:
        """解码JWT token"""
        try:
            lprint(f"开始解码token: {token[:10]}...")
            payload = await self.verify_token(token)
            return payload
        except ExpiredSignatureError:
            lprint("解码token时发生错误: 令牌已过期")
            raise AuthenticationError("令牌已过期", "token_expired")
        except Exception as e:
            lprint(f"解码token时发生错误: {str(e)}")
            traceback.print_exc()
            raise

    async def get_user_from_environ(self, environ: dict) -> UserAuthDTO:
        """从environ获取用户信息（用于WebSocket等场景）"""
        token = self.extract_token_from_environ(environ)
        if not token:
            raise AuthenticationError("未提供认证令牌", "token_missing")
        return await self.get_current_user(token)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[UserAuthInternalDTO]:
        """验证用户"""
        user = await self._repository.get_user_by_username(username)
        if not user or not self.verify_password(password, str(user.hashed_password)):
            return None
            
        return UserAuthInternalDTO.from_internal(user)
    
    async def login(self, request: Request, form_data: OAuth2PasswordRequestForm) -> LoginResponseDTO:
        """处理用户登录逻辑"""
        try:
            
            # 从请求中提取客户端IP和环境信息
            self.client_ip = request.client.host
            if self.client_ip=="127.0.0.1":
                self.client_ip="192.168.112.233"
            
            environ = dict(request.headers)  # Convert headers to a dictionary

            # 从表单数据中提取用户名和密码
            username = form_data.username
            password = form_data.password
            lprint(f"username: {username},ip:{self.client_ip}开始登录")
            user_agent = next(
                (value for key, value in environ.items() 
                 if key.lower() == "user-agent"),
                "unknown_device"
            )
            lprint(self.client_ip,environ)
            lprint(user_agent)
            # 生成设备ID
            device_id = generate_device_id(self.client_ip, username, user_agent)

            user = await self._repository.login_user(username, password)
            
            # 如果用户不存在，则自动注册并登录
            if not user:
                lprint(f"用户 {username} 不存在，尝试自动注册")
                try:
                    # 从表单获取nickname，获取不到使用username
                    nickname = form_data.nickname if hasattr(form_data, 'nickname') and form_data.nickname else username
                    lprint(f"使用nickname: {nickname} 进行注册")

                    
                    # 创建新用户
                    user = await self._user_facade.create_user(
                        username=username,
                        password=password,
                        email=f"{username}@example.com",  # 使用默认邮箱
                        nickname=nickname,  # 使用nickname或默认为username
                        role=UserRole.user.value  # 使用UserRole枚举值
                    )
                    
                    if user:
                        lprint(f"用户 {username} 自动注册成功")
                    else:
                        lprint(f"用户 {username} 自动注册失败")
                        raise AuthenticationError("自动注册失败，请联系管理员")
                except Exception as e:
                    lprint(f"自动注册失败: {str(e)}")
                    # 如果是因为用户名已存在等原因注册失败，则提示密码错误
                    raise AuthenticationError("用户名或密码错误")
            
            if not user:
                lprint(f"登录失败: 用户名或密码错误")
                raise AuthenticationError("用户名或密码错误")
            
            lprint(f"用户 {username} 登录成功")
            user_dict = user.to_dict()

            # 更新设备状态
            result = await self._device_facade.update_device_status(
                device_id=device_id,
                is_online=True,
                user_id=user_dict.get('id'),
                client_ip=self.client_ip,
                device_name=user_agent
            )
            if not result.success:
                lprint("更新设备状态失败")

            # 生成访问令牌
            access_token = self.create_access_token(data={"sub": username})
            lprint("登录成功")
            # 返回包含访问令牌和用户信息的响应
            return LoginResponseDTO(
                access_token=access_token,
                token_type="bearer",
                user_id=user_dict.get('id'),
                device_id=device_id,
                username=user_dict.get('username'),
                role=UserRole(user_dict.get('role'))  # 使用枚举值
            )
        except Exception as e:
            lprint(f"登录失败: {str(e)}")
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error"
            )
    
    async def register(self, username: str, password: str, email: str, 
                      role: str = "user", nickname: Optional[str] = None) -> UserAuthDTO:
        """注册新用户"""
        try:
            # 使用认证仓库创建新用户
            user = await self._repository.create_user(
                username=username,
                hashed_password=self.get_password_hash(password),
                email=email,
                role=role,
                nickname=nickname
            )
            
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Registration failed"
                )
                
            # 发布用户创建事件
            created_event = UserEvent(
                event_type=EventType.user_created,
                user_id=convert_column_to_value(user.id),
                username=convert_column_to_value(user.username),
                data={"email": email},
                created_at=datetime.now(ZoneInfo("UTC"))
            )
            await self._event_bus.publish_event(created_event)
                
            return UserAuthDTO.from_internal(user)
                
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )

    @staticmethod
    def get_local_ip() -> str:
        """
        获取本机IP地址
        
        Returns:
            str: 本机IP地址
        """
        try:
            # 创建一个UDP套接字
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 连接一个外部地址（不需要真实连接）
            s.connect(("8.8.8.8", 80))
            # 获取本地IP
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            lprint(f"获取本机IP失败: {str(e)}")
            return "127.0.0.1"

# 创建全局的 AuthFacade 实例
_auth_facade = None

def get_auth_facade() -> AuthFacade:
    """获取AuthFacade实例"""
    global _auth_facade
    if _auth_facade is None:
        _auth_facade = AuthFacade()
    return _auth_facade

# 导出 get_current_user 函数
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserAuthDTO:
    """获取当前用户"""
    return await get_auth_facade().get_current_user(token)

def convert_column_to_value(value: Any) -> Any:
    """将SQLAlchemy Column转换为Python原生类型"""
    if value is None:
        return None
    if hasattr(value, '_value'):
        return value._value()
    if hasattr(value, 'value'):
        return value.value
    if hasattr(value, 'scalar'):
        return value.scalar()
    if hasattr(value, '__str__'):
        return str(value)
    return value

def convert_to_user(user_base: UserBaseAndDevices) -> User:
    """将UserBaseAndDevices转换为User"""
    user_dict = user_base.__dict__
    return User(
        id=convert_column_to_value(user_dict.get('id')),
        username=convert_column_to_value(user_dict.get('username')),
        hashed_password=convert_column_to_value(user_dict.get('hashed_password')),
        email=convert_column_to_value(user_dict.get('email')),
        role=UserRole(convert_column_to_value(user_dict.get('role'))),
        status=UserStatusEnum(convert_column_to_value(user_dict.get('status'))),
        nickname=convert_column_to_value(user_dict.get('nickname')),
        is_temporary=bool(convert_column_to_value(user_dict.get('is_temporary', False))),
        created_at=convert_column_to_value(user_dict.get('created_at', datetime.now())),
        updated_at=convert_column_to_value(user_dict.get('updated_at', datetime.now()))
    )

def convert_to_auth_dto(user: User) -> UserAuthDTO:
    """将User转换为UserAuthDTO"""
    nickname_value = convert_column_to_value(user.nickname)
    is_temp_value = convert_column_to_value(user.is_temporary) if hasattr(user, 'is_temporary') else False
    
    return UserAuthDTO(
        id=int(convert_column_to_value(user.id)),
        username=str(convert_column_to_value(user.username)),
        email=str(convert_column_to_value(user.email)),
        role=UserRole(int(convert_column_to_value(user.role))),
        status=UserStatusEnum(int(convert_column_to_value(user.status))),
        nickname=str(nickname_value) if nickname_value is not None else None,
        is_temporary=bool(is_temp_value)
    )

def convert_to_auth_internal_dto(user: User) -> UserAuthInternalDTO:
    """将User转换为UserAuthInternalDTO"""
    base = convert_to_auth_dto(user)
    return UserAuthInternalDTO(
        **base.model_dump(),
        hashed_password=str(convert_column_to_value(user.hashed_password))
    )

def convert_to_token(user: User, access_token: str, device_id: str) -> Token:
    """将User转换为Token"""
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=int(convert_column_to_value(user.id)),
        username=str(convert_column_to_value(user.username)),
        role=UserRole(int(convert_column_to_value(user.role))),
        device_id=device_id
    )

async def login_user(self, username: str, password: str) -> Optional[User]:
    """处理用户登录逻辑"""
    try:
        async with self._repository.session.begin():
            result = await self._user_facade.get_user_by_username(username)
            if result.success and result.data:
                user = result.data
                if verify_password(password, str(user.hashed_password)):
                    return user
        return None
    except Exception as e:
        lprint(f"用户登录失败: {str(e)}")
        traceback.print_exc()
        return None
