"""
用户模块门面
提供用户相关功能的统一访问接口，包括用户注册、登录、信息管理等功能
"""
import Lugwit_Module as LM
from typing import List, Optional, Dict, Any, Sequence
from datetime import datetime
from zoneinfo import ZoneInfo
import traceback

from app.domain.common.models.tables import User, Device
from app.domain.common.enums.user import UserRole, UserStatusEnum
from app.domain.user.internal.repository.user_repository import UserRepository
from app.domain.user.facade.dto import user_dto
from app.domain.base.facade.dto import base_dto
from app.utils.security import verify_password as security_verify_password
from app.utils.security import get_password_hash as security_get_password_hash
from app.db.facade.database_facade import DatabaseFacade
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.base.facade.base_facade import BaseFacade
from app.core.events.services import Services
from app.core.events.interfaces import (
    EventType, UserEvent, Event, MessageEvent
)

lprint = LM.lprint

class UserFacade(BaseFacade):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self._initialized = True
            self._repository = UserRepository()
            self._event_bus = Services.get_event_bus()
            
            # 立即注册事件处理器
            self._register_event_handlers()

    def _register_event_handlers(self):
        """注册事件处理器"""
        # 注册所有需要处理的用户事件
        pass
        # self._event_bus.subscribe(EventType.user_created, self._handle_user_created)
        # self._event_bus.subscribe(EventType.user_query, self._handle_user_query)
        # self._event_bus.subscribe(EventType.user_status_changed, self._handle_user_status_changed)
        

            
    async def _handle_user_created(self, event: Event) -> None:
        """处理用户创建事件"""
        if not isinstance(event, UserEvent):
            return None
            
        try:
            # 创建默认设备
            device_event = UserEvent(
                event_type=EventType.device_connected,
                user_id=event.user_id,
                username=event.username,
                data={
                    "device_id": f"default_{event.user_id}",
                    "device_name": "默认设备"
                }
            )
            await self._event_bus.publish_event(device_event)
            
        except Exception as e:
            lprint(f"处理用户创建事件失败: {str(e)}")
        return None

    async def _handle_user_query(self, event: Event) -> Optional[user_dto.UserBase]:
        """处理用户查询事件
        
        Args:
            event: 用户查询事件,可以接受的值可以是用户名或用户ID
            
        Returns:
            Optional[user_dto.UserBase]: 用户基本信息,不存在返回None
        """
        if not isinstance(event, UserEvent):
            return None
            
        try:
            # 从事件数据中获取用户标识
            username = None
            user_id = None
            lprint(locals())
            if isinstance(event, MessageEvent):
                username = event.data.get('username')
                user_id = event.data.get('user_id')
            else:
                data = getattr(event, 'data', {})
                username = data.get('username')
                user_id = data.get('user_id')
                
            if not username and not user_id:
                lprint("用户查询事件缺少必要参数")
                return None
                
            # 优先使用user_id查询
            if user_id:
                user = await self._repository.get_by_id(int(user_id))
                if user:
                    return user_dto.UserBase.from_internal(user)
            elif username and isinstance(username, str):
                user = await self._repository.get_by_username(username)
                if user:
                    return user_dto.UserBase.from_internal(user)
                    
            lprint(f"用户不存在: username={username}, user_id={user_id}")
            return None
            
        except Exception as e:
            lprint(f"处理用户查询事件失败: {str(e)}")
            traceback.print_exc()
            return None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        try:
            user = await self._repository.get_by_username(username)
            if not user:
                lprint(f"用户不存在: {username}")
            return user
        except Exception as e:
            lprint(f"获取用户失败: {str(e)}")
            traceback.print_exc()
            return None

    async def get_registered_users(self) -> Sequence[User]:
        """获取所有注册用户"""
        return await self._repository.get_registered_users()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            return security_verify_password(plain_password, hashed_password)
        except Exception as e:
            lprint(f"密码验证失败: {str(e)}")
            return False

    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return security_get_password_hash(password)

    async def get_users_map(self, current_user: User) -> user_dto.UsersInfoDictResponse:
        """获取用户映射信息"""
        try:
            if not current_user:
                raise ValueError("Current user is required")
                
            users = await self._repository.get_all_users_with_devices()
            user_map = {}
            
            current_user_id = self._repository._get_scalar_value(current_user.id)
            
            for user in users:
                user_id = self._repository._get_scalar_value(user.id)
                if user_id != current_user_id:
                    user_with_devices = await self._repository.get_user_with_devices(user_id)
                    if user_with_devices:
                        user_info = user_dto.UserMapInfo.from_internal(user_with_devices)
                        if user_info:
                            user_map[user.username] = user_info
                            
            current_user_with_devices = await self._repository.get_user_with_devices(current_user_id)
            if not current_user_with_devices:
                raise ValueError("Failed to get current user info")
            
            return user_dto.UsersInfoDictResponse(
                current_user=user_dto.UserResponse.from_internal(current_user_with_devices),
                user_map=user_map
            )
            
        except Exception as e:
            lprint(f"获取用户映射失败: {str(e)}")
            raise

    async def update_last_login(self, user_id: int) -> bool:
        """更新用户最后登录时间"""
        return await self._repository.update_last_login(user_id)

    async def update_status(self, username: str, status: str) -> bool:
        """更新用户状态"""
        try:
            status_enum = UserStatusEnum(status)
            return await self._repository.update_status(username, status_enum)
        except Exception as e:
            lprint(f"更新用户状态失败: {str(e)}")
            return False

    async def get_online_users(self) -> List[User]:
        """获取在线用户"""
        try:
            return await self._repository.get_online_users()
        except Exception as e:
            lprint(f"获取在线用户失败: {str(e)}")
            return []

    async def create_user(self, username: str, email: Optional[str] = None, 
                       password: Optional[str] = None,
                       nickname: Optional[str] = None, 
                       role: Optional[str] = None) -> User:
        """创建用户"""
        try:
            existing_user = await self.get_user_by_username(username)
            if existing_user:
                raise ValueError(f"用户名 {username} 已存在")
            
            hashed_password = self.get_password_hash(password) if password else None
            return await self._repository.create_user(
                username=username,
                email=email,
                password=hashed_password,
                nickname=nickname,
                role=role
            )
        except Exception as e:
            lprint(f"创建用户失败: {str(e)}")
            raise

    async def update_user_info(self, user_id: str, user_info: user_dto.UserUpdate) -> base_dto.ResponseDTO:
        """更新用户信息"""
        try:
            update_data = user_info.dict(exclude_unset=True)
            result = await self._repository.update_user(int(user_id), update_data)
            if result:
                return base_dto.ResponseDTO.success(data=user_dto.UserResponse.from_internal(result))
            return base_dto.ResponseDTO.error(message="更新用户信息失败")
        except Exception as e:
            lprint(f"更新用户信息失败: {str(e)}")
            return base_dto.ResponseDTO.error(message=str(e))

    async def _handle_user_status_changed(self, event: Event) -> None:
        """处理用户状态变更事件"""
        if not isinstance(event, UserEvent):
            return None
        
        try:
            user_id = event.user_id
            new_status = event.data.get('status')
            if new_status:
                await self.update_status(user_id, new_status)
        except Exception as e:
            lprint(f"处理用户状态变更事件失败: {str(e)}")
        return None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据用户ID获取用户"""
        try:
            user = await self._repository.get_by_id(user_id)
            if not user:
                lprint(f"用户不存在: {user_id}")
            return user
        except Exception as e:
            lprint(f"获取用户失败: {str(e)}")
            traceback.print_exc()
            return None

    async def get_online_user_ids(self) -> List[str]:
        """获取在线用户ID列表"""
        users = await self._repository.get_online_users()
        return [str(user.id) for user in users]

# 全局实例
_user_facade = None

def get_user_facade() -> UserFacade:
    """获取用户门面实例"""
    global _user_facade
    if _user_facade is None:
        _user_facade = UserFacade()
    return _user_facade
