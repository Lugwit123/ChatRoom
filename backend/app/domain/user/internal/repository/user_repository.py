"""用户仓库模块"""
# 标准库
from typing import Optional, Dict, Any, Sequence, List, Tuple, cast, Type
from zoneinfo import ZoneInfo
from sqlalchemy import Select, select, and_, or_, update, delete, text, inspect, true, Column, Boolean, Integer
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import expression
from datetime import datetime

# 第三方库
from sqlalchemy.ext.asyncio import AsyncSession

import Lugwit_Module as LM
lprint = LM.lprint
import traceback

from app.db.internal.session import SessionManager
from app.domain.base.internal.repository.base_repository import BaseRepository
from app.domain.common.models.tables import User, Device
from app.domain.common.enums.user import UserRole, UserStatusEnum

class UserRepository(BaseRepository[User]):
    """用户仓储
    
    主要功能：
    1. 用户基本信息的CRUD操作
    2. 用户状态管理
    3. 用户查询
    4. 角色管理
    """
    
    def __init__(self):
        """初始化用户仓储"""
        super().__init__(User)
        self.model: Type[User] = User  # 显式声明类型

    def _get_scalar_value(self, value: Any) -> Any:
        """获取 SQLAlchemy Column 的标量值"""
        if hasattr(value, '_value'):
            return value._value()
        if hasattr(value, 'value'):
            return value.value
        if hasattr(value, 'scalar'):
            return value.scalar()
        return value

    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            Optional[User]: 找到的用户或None
        """
        try:
            lprint(f"[数据库查询{self.model.__tablename__}] 开始查询用户名: {username}")
            # 使用 selectinload 加载设备关联
            query: Select = select(self.model).options(
                selectinload(self.model.devices)
            ).where(self.model.username == username)
            lprint(f"[数据库查询{self.model.__tablename__}] SQL查询: {query}")
            
            result = await self.session.execute(query)
            user: Optional[User] = result.scalar_one_or_none()
            
            if user:
                lprint(f"[数据库查询{self.model.__tablename__}] 找到用户: {user.username}")
                # 记录设备信息
                devices_info: List[str] = [
                    f"设备ID: {device.device_id}, 在线状态: {device.is_online}"
                    for device in user.devices
                ] if user.devices else []
                lprint(f"[数据库查询{self.model.__tablename__}] 用户设备信息: {devices_info}")
            else:
                lprint(f"[数据库查询{self.model.__tablename__}] 未找到用户: {username}")
            return user
            
        except Exception as e:
            lprint(f"[数据库查询{self.model.__tablename__}] 查询失败: {str(e)}")
            traceback.print_exc()
            return None

    async def create_user(self, 
                       username: str, 
                       email: Optional[str] = None, 
                       password: Optional[str] = None,
                       nickname: Optional[str] = None,
                       role: Optional[str] = None) -> Optional[User]:
        """创建用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            nickname: 昵称
            role: 角色
            
        Returns:
            Optional[User]: 创建的用户或None
            
        Raises:
            ValueError: 用户名已存在
        """
        try:
            # 检查用户名是否已存在
            existing_user = await self.get_by_username(username)
            if existing_user:
                raise ValueError(f"用户名 {username} 已存在")
            
            # 创建用户实例
            user = User(
                username=username,
                email=email,
                hashed_password=password,
                nickname=nickname,
                role=role,
                status=UserStatusEnum.normal,
                created_at=datetime.now(ZoneInfo("Asia/Shanghai")),
                updated_at=datetime.now(ZoneInfo("Asia/Shanghai"))
            )
            
            # 使用父类的 create 方法创建用户
            return await super().create(**user.__dict__)
        except Exception as e:
            print(f"[用户创建] 创建用户 {username} 失败: {traceback.format_exc()}")
            raise

    async def get_all_users_with_devices(self) -> List[User]:
        """获取所有用户(包含devices)
        
        Returns:
            List[User]: 所有用户列表
        """
        try:
            async with self.session as session:
                query = select(User).options(selectinload(User.devices))
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            self.lprint(f"获取所有用户失败: {str(e)}")
            traceback.print_exc()
            raise

    async def get_user_with_devices(self, user_id: int) -> Optional[User]:
        """获取用户信息(包含devices)
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[User]: 用户信息
        """
        try:
            async with self.session as session:
                query = select(User).options(selectinload(User.devices)).where(User.id == user_id)
                result = await session.execute(query)
                return result.scalar_one_or_none()
        except Exception as e:
            self.lprint(f"获取用户信息失败: {str(e)}")
            traceback.print_exc()
            raise

    async def update_last_login(self, user_id: int) -> bool:
        """更新用户最后登录时间
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        try:
            await self.update(
                user_id,
                last_login=datetime.now(ZoneInfo("Asia/Shanghai"))
            )
            return True
        except Exception as e:
            self.lprint(f"更新最后登录时间失败: {str(e)}")
            return False

    async def update_status(self, username: str, status: UserStatusEnum) -> bool:
        """更新用户状态
        
        Args:
            username: 用户名
            status: 新状态
            
        Returns:
            bool: 是否成功
        """
        try:
            stmt = (
                update(User)
                .where(User.username == username)
                .values(
                    status=status,
                    updated_at=datetime.now(ZoneInfo("Asia/Shanghai"))
                )
            )
            await self.session.execute(stmt)
            await self.session.commit()
            return True
        except Exception as e:
            self.lprint(f"更新用户状态失败: {str(e)}")
            return False

    async def get_online_users(self) -> List[User]:
        """获取在线用户
        
        Returns:
            List[User]: 在线用户列表
        """
        try:
            # 查询至少有一个在线设备的用户
            query = (
                select(User)
                .join(User.devices)
                .where(
                    and_(
                        expression.true() == Device.login_status,  # 设备在线
                        User.status == UserStatusEnum.normal  # 用户状态正常
                    )
                )
                .group_by(User.id)
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            self.lprint(f"获取在线用户失败: {str(e)}")
            return []

    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """更新用户信息
        
        Args:
            user_id: 用户ID
            update_data: 要更新的字段
            
        Returns:
            Optional[User]: 更新后的用户信息
        """
        try:
            # 更新用户
            update_data['updated_at'] = datetime.now(ZoneInfo("Asia/Shanghai"))
            await self.update(user_id, **update_data)
            
            # 获取更新后的用户信息
            return await self.get_user_with_devices(user_id)
        except Exception as e:
            self.lprint(f"更新用户信息失败: {str(e)}")
            return None

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            Optional[User]: 找到的用户或None
        """
        try:
            print(f"[数据库查询] 开始查询邮箱: {email}")
            query = select(self.model).where(self.model.email == email)
            result = await self.session.execute(query)
            user = result.scalar_one_or_none()
            if not user:
                print(f"[数据库查询] 邮箱 {email} 不存在")
            else:
                print(f"[数据库查询] 找到邮箱 {email}")
            return user
        except Exception as e:
            print(f"[数据库查询] 异常: {str(e)}\n{traceback.format_exc()}")
            raise

    async def get_users_by_status(self, status: UserStatusEnum) -> List[User]:
        """根据状态获取用户
        
        Args:
            status: 用户状态
            
        Returns:
            List[User]: 指定状态的用户列表
        """
        try:
            query = select(self.model).where(self.model.status == status)
            result = await self.session.execute(query)
            users = list(result.scalars().all())
            print(f"获取到 {len(users)} 个状态为 {status} 的用户")
            return users
        except Exception as e:
            print(f"根据状态获取用户失败: {traceback.format_exc()}")
            return []

    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """根据角色获取用户
        
        Args:
            role: 用户角色
            
        Returns:
            List[User]: 指定角色的用户列表
        """
        try:
            query = select(self.model).where(self.model.role == role)
            result = await self.session.execute(query)
            users = list(result.scalars().all())
            print(f"获取到 {len(users)} 个角色为 {role} 的用户")
            return users
        except Exception as e:
            print(f"根据角色获取用户失败: {traceback.format_exc()}")
            return []

    async def get_registered_users(self) -> List[User]:
        """获取所有注册用户
        
        Returns:
            List[User]: 用户列表
        """
        try:
            query = (
                select(self.model)
                .options(
                    selectinload(User.devices),
                    selectinload(User.sent_private_messages),
                    selectinload(User.received_private_messages)
                )
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            lprint(traceback.format_exc())
            raise Exception(f"获取注册用户失败: {str(e)}")

    async def get_all_users(self) -> List[User]:
        """获取所有用户
        
        Returns:
            List[User]: 用户对象列表
        """
        try:
            users = await self.get_all_records()
            return list(users)
        except Exception:
            print(f"获取所有用户失败: {traceback.format_exc()}")
            return []
        
    async def get_username_to_user_map(self) -> Dict[str, User]:
        """获取用户名到用户对象的映射
        
        Returns:
            Dict[str, User]: 用户名到用户对象的映射字典
        """
        try:
            users = await self.get_all_records()
            return {str(user.username): user for user in users}
        except Exception:
            print(f"获取用户名到用户映射失败: {traceback.format_exc()}")
            return {}

    async def get_user_devices(self, user_id: int) -> List[Device]:
        """获取用户的设备列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Device]: 设备列表
        """
        try:
            self.lprint(f"查询用户 {user_id} 的设备列表")
            query = select(Device).where(Device.user_id == user_id)
            result = await self.session.execute(query)
            devices = list(result.scalars().all())
            self.lprint(f"查询到设备列表: {devices}")
            return devices
        except Exception as e:
            self.lprint(f"查询用户设备失败: {str(e)}\n{traceback.format_exc()}")
            return []

    async def search_users(self, query: str) -> List[User]:
        """搜索用户
        
        根据用户名、昵称或邮箱搜索用户
        
        Args:
            query: 搜索关键词
            
        Returns:
            List[User]: 匹配的用户列表
        """
        try:
            stmt = select(self.model).where(
                and_(
                    self.model.status != UserStatusEnum.deleted,
                    or_(
                        self.model.username.ilike(f"%{query}%"),
                        self.model.nickname.ilike(f"%{query}%"),
                        self.model.email.ilike(f"%{query}%")
                    )
                )
            )
            result = await self.session.execute(stmt)
            users = list(result.scalars().all())
            print(f"搜索到 {len(users)} 个匹配的用户")
            return users
        except Exception as e:
            print(f"搜索用户失败: {traceback.format_exc()}")
            raise
    async def get_all_users_with_devices(self) -> List[User]:
        """获取所有用户(包含devices)
        
        Returns:
            List[User]: 所有用户列表
        """
        try:
            async with self.session as session:
                query = select(User).options(selectinload(User.devices))
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            self.lprint(f"获取所有用户失败: {str(e)}")
            traceback.print_exc()
            raise

    async def get_user_with_devices(self, user_id: int) -> Optional[User]:
        """获取用户信息(包含devices)
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[User]: 用户信息
        """
        try:
            async with self.session as session:
                query = select(User).options(selectinload(User.devices)).where(User.id == user_id)
                result = await session.execute(query)
                return result.scalar_one_or_none()
        except Exception as e:
            self.lprint(f"获取用户信息失败: {str(e)}")
            traceback.print_exc()
            raise

