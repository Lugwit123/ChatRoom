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
from typing import Optional, cast, Any
import traceback
import uuid
import hashlib
from zoneinfo import ZoneInfo

# 第三方库
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt, ExpiredSignatureError

# 项目内部导入
from app.domain.common.models.tables import User
from app.domain.user.facade.dto.user_dto import UserBaseAndStatus
from app.domain.common.enums import UserRole, UserStatusEnum
from .dto.auth_dto import Token, UserAuthDTO, UserAuthInternalDTO
from ..internal.repository.auth_repository import get_auth_repository
from app.core.base.core_facade import CoreFacade
from app.core.services import TokenService, PasswordService
from app.domain.base.facade.dto.base_dto import ResponseDTO
from app.core.services import Services
from app.core.events.interfaces import (
    EventType, UserEvent, Event
)
from app.domain.common.events import DomainEventType, UserEvent
from app.core.auth.events.auth_events import LoginEvent, LogoutEvent, LoginFailedEvent

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
        self._repository = get_auth_repository()
        self._token_service = Services.resolve(TokenService) or TokenService()
        self._password_service = Services.resolve(PasswordService) or PasswordService()
        self._event_bus = Services.get_event_bus()
        self._user_facade = None  # 延迟加载
        self._device_facade = None  # 延迟加载
        
        # 注册服务
        if not Services.resolve(TokenService):
            Services.register_service(TokenService.__name__, self._token_service)
        if not Services.resolve(PasswordService):
            Services.register_service(PasswordService.__name__, self._password_service)
            
        # 初始化事件处理器
        from ..internal.event_handlers import get_auth_event_handler
        self._event_handler = get_auth_event_handler()
    
    @property
    def device_facade(self):
        """延迟加载设备门面"""
        if self._device_facade is None:
            from app.domain.device.facade.device_facade import DeviceFacade
            self._device_facade = DeviceFacade()
        return self._device_facade
    
    @property
    def user_facade(self):
        """延迟加载用户门面"""
        if self._user_facade is None:
            from app.domain.user.facade.user_facade import UserFacade
            self._user_facade = UserFacade()
        return self._user_facade
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self._password_service.verify_password(plain_password, hashed_password)
    
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

    async def verify_token(self, token: str) -> dict:
        """验证token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except ExpiredSignatureError:
            raise AuthenticationError("令牌已过期", "token_expired")
        except JWTError:
            raise AuthenticationError("无效的令牌", "invalid_token")

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> UserAuthDTO:
        """获取当前用户"""
        try:
            payload = await self.verify_token(token)
            username = payload.get("sub")
            if not username:
                raise AuthenticationError("无效的令牌内容", "invalid_token_content")
                
            user = await self._repository.get_user_by_username(username)
            if not user:
                raise AuthenticationError("用户不存在", "user_not_found")
                
            return UserAuthDTO.from_internal(user)
            
        except AuthenticationError:
            raise
        except Exception as e:
            lprint(f"获取当前用户失败: {str(e)}")
            raise AuthenticationError("认证失败", "auth_failed")

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
    
    async def login(self, request: Request, form_data: OAuth2PasswordRequestForm) -> Token:
        """用户登录"""
        try:
            # 验证用户
            lprint(f"开始验证用户: {form_data.username}")
            user = await self._repository.get_user_by_username(form_data.username)
            if not user:
                lprint(f"用户不存在: {form_data.username}")
                # 发布登录失败事件
                login_failed_event = LoginFailedEvent(
                    username=form_data.username,
                    ip_address=request.client.host if request.client else "unknown",
                    reason="用户不存在"
                )
                await self._event_bus.publish_event(login_failed_event)
                raise AuthenticationError("用户名或密码错误")
            
            if not self.verify_password(form_data.password, str(user.hashed_password)):
                lprint(f"密码验证失败,用户名: {form_data.username}")
                # 发布登录失败事件
                login_failed_event = LoginFailedEvent(
                    username=form_data.username,
                    ip_address=request.client.host if request.client else "unknown",
                    reason="密码错误"
                )
                await self._event_bus.publish_event(login_failed_event)
                raise AuthenticationError("用户名或密码错误")
            
            lprint(f"密码验证成功,用户名: {form_data.username}")

            # 获取客户端IP
            client_ip = request.client.host if request.client else "unknown"
            lprint(f"客户端IP: {client_ip}")
            
            # 生成设备ID: IP地址和用户名的组合的哈希值
            device_id_str = f"{client_ip}_{form_data.username}"
            device_id = hashlib.md5(device_id_str.encode()).hexdigest()
            lprint(f"开始更新设备信息,设备ID: {device_id}")
            
            # 更新设备信息
            await self.device_facade.update_device_status(
                device_id=device_id,
                is_online=True,
                user_id=convert_column_to_value(user.id),
                client_ip=client_ip
            )
            
            # 发布登录事件
            login_event = LoginEvent(
                user_id=convert_column_to_value(user.id),
                username=convert_column_to_value(user.username),
                device_id=device_id,
                ip_address=client_ip
            )
            await self._event_bus.publish_event(login_event)
            
            # 创建访问令牌
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = self.create_access_token(
                data={"sub": convert_column_to_value(user.username)},
                expires_delta=access_token_expires
            )
            lprint(f"创建访问令牌成功,用户名: {form_data.username}")
            
            # 获取用户角色
            role_value = convert_column_to_value(user.role)
            try:
                role = UserRole(int(role_value))
            except ValueError:
                lprint(f"无效的用户角色值: {role_value}, 使用默认角色: user")
                role = UserRole.user
            
            return Token(
                access_token=access_token,
                token_type="bearer",
                user_id=convert_column_to_value(user.id),
                username=convert_column_to_value(user.username),
                role=role,
                device_id=device_id
            )
            
        except AuthenticationError as e:
            lprint(f"认证错误: {str(e)}")
            raise e
        except Exception as e:
            traceback.print_exc()
            raise AuthenticationError(f"登录失败: {str(e)}")
    
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
                event_type=EventType.USER_CREATED,
                user_id=user.id,
                username=user.username,
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

def convert_to_user(user_base: UserBaseAndStatus) -> User:
    """将UserBaseAndStatus转换为User"""
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
    return UserAuthDTO(
        id=int(convert_column_to_value(user.id)),
        username=str(convert_column_to_value(user.username)),
        email=str(convert_column_to_value(user.email)),
        role=UserRole(int(convert_column_to_value(user.role))),
        status=UserStatusEnum(int(convert_column_to_value(user.status))),
        nickname=str(convert_column_to_value(user.nickname)) if user.nickname else None,
        is_temporary=bool(convert_column_to_value(user.is_temporary)) if hasattr(user, 'is_temporary') else False
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
