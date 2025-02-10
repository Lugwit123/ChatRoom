"""用户仓库模块"""
# 标准库
from typing import Optional, Dict, Any, Sequence, List, Tuple
from zoneinfo import ZoneInfo
from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

# 第三方库
from sqlalchemy import and_, or_, update, delete, text
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
                       email: str = None, 
                       password: str = None,
                       nickname: str = None,
                       role: str = None,
                       avatar_index: int = 0,
                       extra_data: Dict[str, Any] = None) -> Optional[User]:
        """创建用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            nickname: 昵称
            role: 角色
            avatar_index: 头像索引
            extra_data: 额外数据
            
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
                hashed_password=password,  # 注意：这里已经在 service 层进行了哈希处理
                nickname=nickname,
                role=role,
                avatar_index=avatar_index,
                extra_data=extra_data
            )
            
            # 使用父类的 create 方法创建用户
            return await super().create(user)
        except Exception as e:
            print(f"[用户创建] 创建用户 {username} 失败: {traceback.format_exc()}")
            raise

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            Optional[User]: 找到的用户或None
            
        Raises:
            Exception: 数据库操作失败
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

    async def get_online_users(self) -> Sequence[User]:
        """获取在线用户
        
        Returns:
            Sequence[User]: 在线用户列表
            
        Raises:
            Exception: 数据库操作失败
        """
        try:
            # 查询至少有一个在线设备的用户
            query = (
                select(self.model)
                .join(self.model.devices)
                .where(
                    and_(
                        Device.login_status == True,  # 设备在线
                        self.model.status == UserStatusEnum.normal  # 用户状态正常
                    )
                )
                .group_by(self.model.id)
            )
            result = await self.session.execute(query)
            users = result.scalars().all()
            print(f"获取到 {len(users)} 个在线用户")
            return users
        except Exception as e:
            print(f"获取在线用户失败: {traceback.format_exc()}")
            raise

    async def get_users_by_status(self, status: UserStatusEnum) -> Sequence[User]:
        """根据状态获取用户
        
        Args:
            status: 用户状态
            
        Returns:
            Sequence[User]: 指定状态的用户列表
            
        Raises:
            Exception: 数据库操作失败
        """
        try:
            query = select(self.model).where(self.model.status == status)
            result = await self.session.execute(query)
            users = result.scalars().all()
            print(f"获取到 {len(users)} 个状态为 {status} 的用户")
            return users
        except Exception as e:
            print(f"根据状态获取用户失败: {traceback.format_exc()}")
            raise

    async def get_users_by_role(self, role: UserRole) -> Sequence[User]:
        """根据角色获取用户
        
        Args:
            role: 用户角色
            
        Returns:
            Sequence[User]: 指定角色的用户列表
            
        Raises:
            Exception: 数据库操作失败
        """
        try:
            query = select(self.model).where(self.model.role == role)
            result = await self.session.execute(query)
            users = result.scalars().all()
            print(f"获取到 {len(users)} 个角色为 {role} 的用户")
            return users
        except Exception as e:
            print(f"根据角色获取用户失败: {traceback.format_exc()}")
            raise

    async def get_registered_users(self) -> Sequence[User]:
        """获取所有注册用户
        
        Returns:
            Sequence[User]: 用户列表
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
            return result.scalars().all()
        except Exception as e:
            lprint(traceback.format_exc(), level=LM.logging.ERROR)
            raise Exception(f"获取注册用户失败: {str(e)}")

    async def get_all_users(self) -> Sequence[User]:
        """获取所有用户
        
        Returns:
            Sequence[User]: 用户对象列表
        """
        try:
            users = await self.get_all_records()
            return users
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
            return {user.username: user for user in users}
        except Exception:
            print(f"获取用户名到用户映射失败: {traceback.format_exc()}")
            return {}

    async def get_user_devices(self, user_id: int) -> Sequence[Device]:
        """获取用户的设备列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            Sequence[Device]: 设备列表
        """
        try:
            self.lprint(f"查询用户 {user_id} 的设备列表")
            query = select(Device).where(Device.user_id == user_id)
            result = await self.session.execute(query)
            devices = result.scalars().all()
            self.lprint(f"查询到设备列表: {devices}")
            return devices
        except Exception as e:
            self.lprint(f"查询用户设备失败: {str(e)}\n{traceback.format_exc()}")
            return []

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户信息

        Args:
            username: 用户名

        Returns:
            Optional[User]: 用户信息，如果不存在则返回 None
        """
        query = (
            select(self.model)
            .options(selectinload(self.model.devices))
            .where(self.model.username == username)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_status(self, username: str, status: UserStatusEnum) -> bool:
        """更新用户状态
        
        Args:
            username: 用户名
            status: 新状态
            
        Returns:
            bool: 更新是否成功
            
        Raises:
            Exception: 数据库操作失败
        """
        try:
            await self.session.execute(
                update(self.model)
                .where(self.model.username == username)
                .values(status=status)
            )
            await self.session.commit()
            print(f"更新用户 {username} 状态为 {status} 成功")
            return True
        except Exception as e:
            await self.session.rollback()
            print(f"更新用户状态失败: {traceback.format_exc()}")
            raise

    async def search_users(self, query: str) -> Sequence[User]:
        """搜索用户
        
        根据用户名、昵称或邮箱搜索用户
        
        Args:
            query: 搜索关键词
            
        Returns:
            Sequence[User]: 匹配的用户列表
            
        Raises:
            Exception: 数据库操作失败
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
            users = result.scalars().all()
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
