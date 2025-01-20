"""用户仓储类"""
from typing import Optional, List, Union, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, and_, or_
from passlib.context import CryptContext
import re
from datetime import timedelta

from app.db.repositories.base import BaseRepository
from app.db.schemas import User, UserRole, Group
from app.db.schemas import UserCreate, UserUpdate
from app.core.utils import get_current_time
import Lugwit_Module as LM

lprint = LM.lprint

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def validate_username(username: str) -> bool:
    """验证用户名"""
    # 用户名长度在3-20之间，只能包含字母、数字和下划线
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return False
    return True

def validate_nickname(nickname: str) -> bool:
    """验证昵称"""
    # 昵称长度在1-30之间
    if not nickname or len(nickname) > 30:
        return False
    return True

async def fetch_user(username: str) -> Optional[User]:
    """根据用户名获取用户"""
    async with async_session() as session:
        query = select(User).where(User.username == username)
        result = await session.execute(query)
        return result.scalar_one_or_none()

async def set_user_online_status(username: str, online: bool) -> Optional[User]:
    """设置用户在线状态"""
    async with async_session() as session:
        user = await fetch_user(username)
        if not user:
            return None
        
        user.online = online
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

async def fetch_registered_users(exclude_roles: List[str] = None) -> List[User]:
    """获取所有注册用户（非临时用户）"""
    async with async_session() as session:
        query = select(User).where(User.is_temporary == False)
        if exclude_roles:
            query = query.where(User.role.not_in_(exclude_roles))
        result = await session.execute(query)
        return result.scalars().all()

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """用户仓储类，提供用户相关的数据库操作方法"""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_username(self, session: AsyncSession, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return await self.get_by_field(session, "username", username)
    
    async def get_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return await self.get_by_field(session, "email", email)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)
    
    async def authenticate(self, session: AsyncSession, username: str, password: str) -> Optional[User]:
        """验证用户凭据"""
        user = await self.get_by_username(session, username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    async def create_with_groups(
        self,
        session: AsyncSession,
        *,
        obj_in: UserCreate,
        group_names: List[str]
    ) -> User:
        """创建用户并关联群组"""
        # 创建用户
        db_obj = User(
            username=obj_in.username,
            nickname=obj_in.nickname,
            email=obj_in.email,
            role=obj_in.role,
            hashed_password=self.get_password_hash(obj_in.password),
            is_temporary=obj_in.is_temporary,
            online=obj_in.online
        )
        
        # 关联群组
        from app.db.repositories.group import GroupRepository
        group_repo = GroupRepository()
        for group_name in group_names:
            group = await group_repo.get_by_name(session, group_name)
            if group:
                db_obj.groups.append(group)
        
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
    
    async def update_message_ids(
        self,
        session: AsyncSession,
        *,
        username: str,
        message_ids: Dict[str, List[str]]
    ) -> Optional[User]:
        """更新用户的消息ID列表"""
        user = await self.get_by_username(session, username)
        if not user:
            return None
        
        user.message_ids = message_ids
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    
    async def set_online_status(
        self,
        session: AsyncSession,
        *,
        username: str,
        online: bool
    ) -> Optional[User]:
        """设置用户在线状态"""
        user = await self.get_by_username(session, username)
        if not user:
            return None
        
        user.online = online
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    
    async def get_registered_users(
        self,
        session: AsyncSession,
        *,
        exclude_roles: List[str] = None
    ) -> List[User]:
        """获取所有注册用户（非临时用户）"""
        query = select(User).where(User.is_temporary == False)
        if exclude_roles:
            query = query.where(User.role.not_in_(exclude_roles))
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_recent_message_ids(self, session: AsyncSession, days: int = 7) -> Dict[str, List[str]]:
        """获取最近的消息ID"""
        cutoff_date = get_current_time() - timedelta(days=days)
        query = select(User.message_ids).where(
            and_(
                User.last_active >= cutoff_date,
                User.message_ids.is_not(None)
            )
        )
        result = await session.execute(query)
        message_ids = {}
        for row in result.scalars():
            for status, ids in row.items():
                if status not in message_ids:
                    message_ids[status] = []
                message_ids[status].extend(ids)
        return message_ids
    
    async def get_all_message_ids(self, session: AsyncSession) -> Dict[str, List[str]]:
        """获取所有消息ID"""
        query = select(User.message_ids).where(User.message_ids.is_not(None))
        result = await session.execute(query)
        message_ids = {}
        for row in result.scalars():
            for status, ids in row.items():
                if status not in message_ids:
                    message_ids[status] = []
                message_ids[status].extend(ids)
        return message_ids
    
    def safe_id(self, user_id: int) -> str:
        """安全地转换用户ID为字符串"""
        return str(user_id) if user_id else ""
    
    def safe_username(self, username: str) -> str:
        """安全地处理用户名"""
        return username if username else ""
    
    async def is_user_admin(self, session: AsyncSession, username: str) -> bool:
        """检查用户是否是管理员"""
        user = await self.get_by_username(session, username)
        return user is not None and user.role == UserRole.ADMIN
    
    async def get_user_by_id(self, session: AsyncSession, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return await self.get(session, user_id)
    
    async def fetch_users_by_condition(
        self,
        session: AsyncSession,
        *,
        role: Optional[UserRole] = None,
        is_temporary: Optional[bool] = None,
        online: Optional[bool] = None
    ) -> List[User]:
        """根据条件获取用户列表"""
        conditions = []
        if role is not None:
            conditions.append(User.role == role)
        if is_temporary is not None:
            conditions.append(User.is_temporary == is_temporary)
        if online is not None:
            conditions.append(User.online == online)
            
        query = select(User)
        if conditions:
            query = query.where(and_(*conditions))
            
        result = await session.execute(query)
        return result.scalars().all()
    
    async def update_user_last_message(
        self,
        session: AsyncSession,
        username: str,
        message_id: str
    ) -> Optional[User]:
        """更新用户最后一条消息"""
        user = await self.get_by_username(session, username)
        if not user:
            return None
            
        user.last_message_id = message_id
        user.last_active = get_current_time()
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    
    async def process_message_updates(
        self,
        session: AsyncSession,
        updates: List[Dict[str, Any]]
    ) -> None:
        """批量处理消息更新"""
        for update in updates:
            username = update.get("username")
            message_id = update.get("message_id")
            if username and message_id:
                await self.update_user_last_message(session, username, message_id)
