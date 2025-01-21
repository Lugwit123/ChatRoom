"""用户仓储"""
# 标准库
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any, Sequence
from zoneinfo import ZoneInfo

# 第三方库
from sqlalchemy import select, and_, update, delete, text, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# 本地模块
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from app.db.database import AsyncSessionLocal
from app.db.base_repository import BaseRepository
from app.domain.user.models import User
from app.domain.user.enums import UserRole, UserStatusEnum

class UserRepository(BaseRepository[User]):
    """用户仓储
    
    主要功能：
    1. 用户基本信息的CRUD操作
    2. 用户状态管理
    3. 用户查询
    4. 角色管理
    """
    
    def __init__(self, session: AsyncSession = None):
        """初始化用户仓储
        
        Args:
            session: 数据库会话
        """
        super().__init__(User, session)
        self._session = session

    @property
    def session(self) -> AsyncSession:
        """获取数据库会话"""
        return self._session

    @session.setter
    def session(self, value: AsyncSession):
        """设置数据库会话"""
        self._session = value

    async def get_by_username(self, username: str, session: Optional[AsyncSession] = None) -> Optional[User]:
        """根据用户名获取用户
        
        Args:
            username: 用户名
            session: 可选的数据库会话
            
        Returns:
            找到的用户或None
        """
        try:
            if session:
                self.session = session
                
            lprint(f"[数据库查询] 开始查询用户名: {username}")
            query = select(User).where(User.username == username)
            result = await self.session.execute(query)
            user = result.scalar_one_or_none()
            
            if user is None:
                lprint(f"[数据库查询] 未找到用户名 {username}")
            else:
                lprint(f"[数据库查询] 找到用户名 {username}")
                
            return user
        except Exception as e:
            lprint(f"[数据库查询] 查询用户名 {username} 失败: {traceback.format_exc()}")
            return None

    async def create_user(self, 
                       username: str, 
                       email: str = None, 
                       password: str = None,
                       nickname: str = None,
                       role: str = None,
                       avatar_index: int = 0,
                       extra_data: Dict[str, Any] = None,
                       session: Optional[AsyncSession] = None) -> Optional[User]:
        """创建用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            nickname: 昵称
            role: 角色
            avatar_index: 头像索引
            extra_data: 额外数据
            session: 可选的数据库会话
            
        Returns:
            创建的用户或None
            
        Raises:
            ValueError: 用户名已存在
        """
        try:
            if session:
                self.session = session
                
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
            lprint(f"[用户创建] 创建用户 {username} 失败: {traceback.format_exc()}")
            raise

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            找到的用户或None
            
        Raises:
            Exception: 数据库操作失败
        """
        try:
            lprint(f"[数据库查询] 开始查询邮箱: {email}")
            query = select(self.model).where(self.model.email == email)
            result = await self.session.execute(query)
            user = result.scalar_one_or_none()
            if not user:
                lprint(f"[数据库查询] 邮箱 {email} 不存在")
            else:
                lprint(f"[数据库查询] 找到邮箱 {email}")
            return user
        except Exception as e:
            lprint(f"[数据库查询] 异常: {str(e)}\n{traceback.format_exc()}")
            raise

    async def get_online_users(self) -> Sequence[User]:
        """获取在线用户
        
        Returns:
            在线用户列表
            
        Raises:
            Exception: 数据库操作失败
        """
        try:
            query = select(self.model).where(
                and_(
                    self.model.login_status == True,
                    self.model.status == UserStatusEnum.normal
                )
            )
            result = await self.session.execute(query)
            users = result.scalars().all()
            lprint(f"获取到 {len(users)} 个在线用户")
            return users
        except Exception as e:
            lprint(f"获取在线用户失败: {traceback.format_exc()}")
            raise

    async def get_users_by_status(self, status: UserStatusEnum) -> Sequence[User]:
        """根据状态获取用户
        
        Args:
            status: 用户状态
            
        Returns:
            指定状态的用户列表
            
        Raises:
            Exception: 数据库操作失败
        """
        try:
            query = select(self.model).where(self.model.status == status)
            result = await self.session.execute(query)
            users = result.scalars().all()
            lprint(f"获取到 {len(users)} 个状态为 {status} 的用户")
            return users
        except Exception as e:
            lprint(f"根据状态获取用户失败: {traceback.format_exc()}")
            raise

    async def get_users_by_role(self, role: UserRole) -> Sequence[User]:
        """根据角色获取用户
        
        Args:
            role: 用户角色
            
        Returns:
            指定角色的用户列表
            
        Raises:
            Exception: 数据库操作失败
        """
        try:
            query = select(self.model).where(self.model.role == role)
            result = await self.session.execute(query)
            users = result.scalars().all()
            lprint(f"获取到 {len(users)} 个角色为 {role} 的用户")
            return users
        except Exception as e:
            lprint(f"根据角色获取用户失败: {traceback.format_exc()}")
            raise

    async def get_registered_users(self, session: Optional[AsyncSession] = None) -> Sequence[User]:
        """获取所有注册用户
        
        Args:
            session: 可选的数据库会话
            
        Returns:
            Sequence[User]: 所有注册用户列表
        """
        try:
            lprint("[数据库查询] 开始获取所有注册用户")
            stmt = (
                select(User)
                .where(User.status == UserStatusEnum.normal)  # 只获取正常状态的用户
                .options(
                    selectinload(User.devices),  # 预加载设备信息
                    selectinload(User.sent_messages),  # 预加载发送的消息
                    selectinload(User.received_messages)  # 预加载接收的消息
                )
            )
            
            # 使用提供的会话或仓储自身的会话
            session_to_use = session or self.session
            if not session_to_use:
                raise Exception("数据库会话未初始化")
                
            result = await session_to_use.execute(stmt)
            users = result.scalars().all()
            lprint(f"[数据库查询] 成功获取所有注册用户，共 {len(users)} 个")
            return users
        except Exception as e:
            lprint(f"[数据库查询] 获取注册用户失败: {str(e)}")
            lprint(traceback.format_exc())
            raise Exception(f"获取注册用户失败: {str(e)}")

    async def update_online_status(self, username: str, login_status: bool) -> bool:
        """更新用户在线状态
        
        Args:
            username: 用户名
            login_status: 是否在线
            
        Returns:
            更新是否成功
            
        Raises:
            Exception: 数据库操作失败
        """
        try:
            await self.session.execute(
                update(self.model)
                .where(self.model.username == username)
                .values(login_status=login_status)
            )
            await self.session.commit()
            lprint(f"更新用户 {username} 在线状态为 {login_status} 成功")
            return True
        except Exception as e:
            await self.session.rollback()
            lprint(f"更新用户在线状态失败: {traceback.format_exc()}")
            raise

    async def update_status(self, username: str, status: UserStatusEnum) -> bool:
        """更新用户状态
        
        Args:
            username: 用户名
            status: 新状态
            
        Returns:
            更新是否成功
            
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
            lprint(f"更新用户 {username} 状态为 {status} 成功")
            return True
        except Exception as e:
            await self.session.rollback()
            lprint(f"更新用户状态失败: {traceback.format_exc()}")
            raise

    async def search_users(self, query: str) -> Sequence[User]:
        """搜索用户
        
        根据用户名、昵称或邮箱搜索用户
        
        Args:
            query: 搜索关键词
            
        Returns:
            匹配的用户列表
            
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
            lprint(f"搜索到 {len(users)} 个匹配的用户")
            return users
        except Exception as e:
            lprint(f"搜索用户失败: {traceback.format_exc()}")
            raise
