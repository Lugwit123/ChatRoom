"""
用户模块门面
提供用户相关功能的统一访问接口，包括用户注册、登录、信息管理等功能
"""
import Lugwit_Module as LM
from typing import List, Optional, Dict, Any, Sequence
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domain.common.models.tables import User, Device
from app.domain.common.enums.user import UserRole, UserStatusEnum
from app.domain.user.internal.repository.user_repository import UserRepository
from app.domain.user.facade.dto import user_dto
from app.core.auth.facade.dto import auth_dto
from app.domain.base.facade.dto import base_dto
from app.utils.security import verify_password as security_verify_password
from app.utils.security import get_password_hash as security_get_password_hash
from app.db.facade.database_facade import DatabaseFacade
from sqlalchemy.ext.asyncio import AsyncSession
import traceback
lprint = LM.lprint

# 用户门面单例
_user_facade = None

def get_user_facade() -> 'UserFacade':
    """获取用户门面单例
    
    Returns:
        UserFacade: 用户门面实例
    """
    global _user_facade
    if _user_facade is None:
        _user_facade = UserFacade()
    return _user_facade

class UserFacade:
    """用户模块对外接口
    
    提供用户相关的所有功能访问点，包括：
    - 用户注册
    - 用户登录
    - 用户信息查询
    - 用户信息更新等
    """
    def __init__(self):
        """初始化认证门面"""
        self._database_facade = DatabaseFacade()
        self._user_repository = UserRepository()
        self.lprint = LM.lprint
        
    async def register(self, user: user_dto.UserCreate) -> base_dto.ResponseDTO:
        """注册新用户
        
        Args:
            user: 用户创建DTO对象
            
        Returns:
            ResponseDTO: 统一响应格式
        """
        try:
            result = await self._user_repository.create_user(user.to_internal())
            return base_dto.ResponseDTO.success(data=user_dto.UserResponse.from_internal(result))
        except Exception as e:
            self.lprint(f"用户注册失败: {str(e)}")
            return base_dto.ResponseDTO.error(message=str(e))
            
    async def login(self, login_data: user_dto.UserLoginDTO) -> base_dto.ResponseDTO:
        """用户登录
        
        Args:
            login_data: 登录信息DTO
            
        Returns:
            ResponseDTO: 包含用户信息和token的响应
        """
        try:
            result = await self._user_repository.login(login_data.to_internal())
            return base_dto.ResponseDTO.success(data=result)
        except Exception as e:
            self.lprint(f"用户登录失败: {str(e)}")
            return base_dto.ResponseDTO.error(message=str(e))
            
    async def get_user_info(self, user_id: str) -> base_dto.ResponseDTO:
        """获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            ResponseDTO: 包含用户信息的响应
        """
        try:
            user = await self._user_repository.get_user(user_id)
            return base_dto.ResponseDTO.success(data=user_dto.UserResponse.from_internal(user))
        except Exception as e:
            self.lprint(f"获取用户信息失败: {str(e)}")
            return base_dto.ResponseDTO.error(message=str(e))
            
    async def update_user_info(self, user_id: str, user_info: user_dto.UserResponse) -> base_dto.ResponseDTO:
        """更新用户信息
        
        Args:
            user_id: 用户ID
            user_info: 用户信息DTO
            
        Returns:
            ResponseDTO: 更新结果响应
        """
        try:
            result = await self._user_repository.update_user(user_id, user_info.to_internal())
            return base_dto.ResponseDTO.success(data=user_dto.UserResponse.from_internal(result))
        except Exception as e:
            self.lprint(f"更新用户信息失败: {str(e)}")
            return base_dto.ResponseDTO.error(message=str(e))

    async def get_user_by_username(self, username: str) -> Optional[user_dto.UserBaseAndStatus]:
        """根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            Optional[UserBaseAndStatus]: 用户信息，如果不存在则返回 None
        """
        try:
            # 查询用户
            user = await self._user_repository.get_user_by_username(username)
            if not user:
                self.lprint(f"用户不存在: {username}")
                return None
                
            # 转换为 DTO
            user_info = user_dto.UserBaseAndStatus.from_internal(user)
            self.lprint(f"成功获取用户信息: {user.username}")
            return user_info
            
        except Exception as e:
            traceback.print_exc()
            return None

    async def get_user_for_auth(self, username: str) -> Optional[auth_dto.UserAuthDTO]:
        """获取用户认证信息
        
        Args:
            username: 用户名
            
        Returns:
            Optional[UserAuthDTO]: 用户认证信息
        """
        try:
            self.lprint(f"开始获取用户认证信息: {username}")
            # 获取用户信息
            user = await self._user_repository.get_by_username(username)
            if not user:
                self.lprint(f"未找到用户: {username}")
                return None
                
            # 转换为认证 DTO
            user_dto = auth_dto.UserAuthDTO.from_internal(user)
            self.lprint(f"成功获取用户认证信息: {user.username}")
            return user_dto
            
        except Exception as e:
            self.lprint(f"获取用户认证信息失败: {str(e)}")
            traceback.print_exc()
            return None

    async def get_registered_users(self, session: Optional[AsyncSession] = None) -> Sequence[User]:
        """获取所有注册用户
        
        Args:
            session: 可选的数据库会话
            
        Returns:
            Sequence[User]: 所有注册用户列表
        """
        return await self._user_repository.get_registered_users(session)

    async def create_user(self, 
                       username: str, 
                       email: str = None, 
                       password: str = None,
                       nickname: str = None,
                       role: str = None,
                       avatar_index: int = 0,
                       extra_data: Dict[str, Any] = None,
                       session: Optional[AsyncSession] = None,
                       **kwargs) -> User:
        """创建用户
        
        Args:
            username: 用户名
            email: 邮箱（可选）
            password: 密码（可选）
            nickname: 昵称（可选）
            role: 角色（可选）
            avatar_index: 头像索引（可选）
            extra_data: 额外数据（可选）
            session: 数据库会话（可选）
            **kwargs: 其他参数
            
        Returns:
            User: 创建的用户
            
        Raises:
            ValueError: 用户名已存在
        """
        try:
            # 检查用户名是否已存在
            existing_user = await self.get_user_by_username(username)
            if existing_user:
                raise ValueError(f"用户名 {username} 已存在")
            
            # 创建用户
            hashed_password = self.get_password_hash(password) if password else None
            return await self._user_repository.create_user(
                username=username,
                email=email,
                password=hashed_password,
                nickname=nickname,
                role=role,
                avatar_index=avatar_index,
                extra_data=extra_data,
                session=session
            )
        except Exception as e:
            traceback.print_exc()
            raise

    async def get_by_email(self, email: str, session: Optional[AsyncSession] = None) -> Optional[User]:
        """通过邮箱获取用户"""
        try:
            return await self._user_repository.get_by_email(email, session)
        except Exception as e:
            lprint(f"获取用户失败: {str(e)}")
            return None

    async def update_status(self, username: str, status: str, session: Optional[AsyncSession] = None) -> bool:
        """更新用户状态"""
        try:
            # 将字符串状态转换为枚举
            try:
                status_enum = UserStatusEnum(status)
            except ValueError:
                lprint(f"无效的状态值: {status}")
                return False

            return await self._user_repository.update_status(username, status_enum, session)
        except Exception as e:
            lprint(f"更新用户状态失败: {str(e)}")
            return False

    async def get_online_users(self, session: Optional[AsyncSession] = None) -> List[User]:
        """获取在线用户"""
        try:
            return await self._user_repository.get_online_users(session)
        except Exception as e:
            lprint(f"获取在线用户失败: {str(e)}")
            return []

    async def get_users_map(self, current_user: User) -> user_dto.UsersInfoDictResponse:
        """获取用户映射信息"""
        try:
            if not current_user:
                raise ValueError("Current user is required")
                
            # 获取所有用户(包含devices)
            users = await self._user_repository.get_all_users_with_devices()
            
            # 构建用户映射
            user_map = {}
            for user in users:
                if user.id != current_user.id:  # 排除当前用户

                    
                    # 特别关注 admin01 用户
                    if user.username == 'admin01':
                        self.lprint(f"发现 admin01 用户!")
                        self.lprint(f"admin01 的 ID: {user.id}")
                        self.lprint(f"admin01 的设备列表: {user.devices}")
                        self.lprint(f"admin01 的设备数量: {len(user.devices) if user.devices else 0}")
                    
                    # 获取用户的完整信息（包括devices）
                    user_with_devices = await self._user_repository.get_user_with_devices(user.id)
                    if user_with_devices:
                        user_info = user_dto.UserMapInfo.from_internal(user_with_devices)
                        if user_info:  # 确保转换成功
                            user_map[user.username] = user_info

            # 获取当前用户的完整信息（包括devices）
            current_user_with_devices = await self._user_repository.get_user_with_devices(current_user.id)
            if not current_user_with_devices:
                raise ValueError("Failed to get current user info")
            
            # 构建响应
            response = user_dto.UsersInfoDictResponse(
                current_user=user_dto.UserResponse.from_internal(current_user_with_devices),
                user_map=user_map
            )
            
            return response
            
        except Exception as e:
            self.lprint(f"获取用户映射失败: {str(e)}")
            traceback.print_exc()
            raise e  # 向上传播异常,让调用者处理

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            bool: 密码是否匹配
        """
        try:
            self.lprint(f"开始验证密码")
            result = security_verify_password(plain_password, hashed_password)
            self.lprint(f"密码验证结果: {result}")
            return result
        except Exception as e:
            traceback.print_exc()
            return False

    def get_password_hash(self, password: str) -> str:
        """获取密码哈希值
        
        Args:
            password: 明文密码
            
        Returns:
            str: 密码哈希值
        """
        try:
            self.lprint(f"开始生成密码哈希")
            result = security_get_password_hash(password)
            self.lprint(f"密码哈希生成成功")
            return result
        except Exception as e:
            self.lprint(f"生成密码哈希出错: {str(e)}\n{traceback.format_exc()}")
            raise
