"""用户服务"""
from typing import Optional, List, Dict, Any, Sequence
from datetime import datetime
from zoneinfo import ZoneInfo
import traceback

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user.repository import UserRepository
from app.domain.user.models import User
from app.domain.user.enums import UserRole, UserStatusEnum
from app.utils.security import get_password_hash
import Lugwit_Module as LM
lprint = LM.lprint

class UserService:
    """用户服务"""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_by_username(self, username: str, session: Optional[AsyncSession] = None) -> Optional[User]:
        """通过用户名获取用户"""
        return await self.repository.get_by_username(username, session)

    async def get_registered_users(self, session: Optional[AsyncSession] = None) -> Sequence[User]:
        """获取所有注册用户
        
        Args:
            session: 可选的数据库会话
            
        Returns:
            Sequence[User]: 所有注册用户列表
        """
        return await self.repository.get_registered_users(session)

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
            existing_user = await self.get_by_username(username, session)
            if existing_user:
                raise ValueError(f"用户名 {username} 已存在")
            
            # 创建用户
            hashed_password = get_password_hash(password) if password else None
            return await self.repository.create_user(
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
            lprint(f"[用户创建] 创建用户失败: {traceback.format_exc()}")
            raise

    async def get_by_email(self, email: str, session: Optional[AsyncSession] = None) -> Optional[User]:
        """通过邮箱获取用户"""
        try:
            return await self.repository.get_by_email(email, session)
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

            return await self.repository.update_status(username, status_enum, session)
        except Exception as e:
            lprint(f"更新用户状态失败: {str(e)}")
            return False

    async def get_online_users(self, session: Optional[AsyncSession] = None) -> List[User]:
        """获取在线用户"""
        try:
            return await self.repository.get_online_users(session)
        except Exception as e:
            lprint(f"获取在线用户失败: {str(e)}")
            return []

    async def bulk_create_users(self, users_data: List[dict], session: Optional[AsyncSession] = None) -> List[User]:
        """批量创建用户
        
        Args:
            users_data: 用户数据列表，每个用户数据包含 username, email, password 等字段
            session: 可选的数据库会话
            
        Returns:
            List[User]: 创建的用户列表
        """
        try:
            users = []
            for user_data in users_data:
                # 检查必要字段
                if not all(k in user_data for k in ["username", "email", "password"]):
                    lprint(f"用户数据缺少必要字段: {user_data}")
                    continue

                # 检查用户名是否已存在
                if await self.get_by_username(user_data["username"], session):
                    lprint(f"用户名已存在: {user_data['username']}")
                    continue

                # 创建用户
                hashed_password = get_password_hash(user_data["password"])
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=hashed_password,
                    nickname=user_data.get("nickname"),
                    role=user_data.get("role", "user"),
                    avatar_index=user_data.get("avatar_index", 0),
                    created_at=datetime.now(ZoneInfo("Asia/Shanghai"))
                )
                created_user = await self.repository.create(user, session)
                users.append(created_user)

            return users
        except Exception as e:
            lprint(f"批量创建用户失败: {str(e)}")
            raise
