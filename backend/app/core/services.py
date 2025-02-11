"""
核心服务注册器
提供全局服务访问点，避免循环依赖
"""
import Lugwit_Module as LM
from typing import Dict, Any, Optional, TypeVar, Type
import socketio
from .events.event_bus_service import EventBusService
import hashlib
import jwt
from datetime import datetime, timedelta
import os
from app.utils.security import verify_password, get_password_hash

lprint = LM.lprint

T = TypeVar('T')

class TokenService:
    """令牌服务"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 24 * 60  # 24小时
        
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
        
    def verify_token(self, token: str) -> dict:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.exceptions.ExpiredSignatureError:
            raise ValueError("令牌已过期")
        except jwt.exceptions.InvalidTokenError:
            raise ValueError("无效的令牌")

class PasswordService:
    """密码服务"""
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return get_password_hash(password)
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return verify_password(plain_password, hashed_password)

class Services:
    """全局服务注册器"""
    
    _instance = None
    _services: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register_socketio(cls, sio: socketio.AsyncServer):
        """注册Socket.IO服务器"""
        cls._services['socketio'] = sio
        
    @classmethod
    def get_socketio(cls) -> Optional[socketio.AsyncServer]:
        """获取Socket.IO服务器"""
        return cls._services.get('socketio')

    @classmethod
    def register_event_bus(cls) -> None:
        """注册事件总线服务"""
        cls._services['event_bus'] = EventBusService()
        
    @classmethod
    def get_event_bus(cls) -> EventBusService:
        """获取事件总线服务"""
        if 'event_bus' not in cls._services:
            cls.register_event_bus()
        return cls._services['event_bus']
        
    @classmethod
    def register_service(cls, name: str, service: Any):
        """注册服务"""
        cls._services[name] = service
        
    @classmethod
    def get_service(cls, name: str) -> Optional[Any]:
        """获取服务"""
        return cls._services.get(name)

    @classmethod
    def resolve(cls, service_type: Type[T]) -> Optional[T]:
        """解析服务
        
        Args:
            service_type: 服务类型
            
        Returns:
            Optional[T]: 服务实例
        """
        service_name = service_type.__name__
        return cls._services.get(service_name)

# 全局服务实例
services = Services() 