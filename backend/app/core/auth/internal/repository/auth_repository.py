"""
认证仓库类
处理所有与认证相关的数据库操作
"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from datetime import datetime
from typing import Optional, List
import traceback

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.common.models.tables import User
from app.domain.common.enums import UserRole, UserStatusEnum
from app.core.base.internal.repository.base_repository import CoreBaseRepository

class AuthRepository(CoreBaseRepository[User]):
    """认证仓库类"""
    
    def __init__(self):
        """初始化认证仓库"""
        super().__init__(User)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            Optional[User]: 用户对象,不存在返回None
        """
        try:
            # 使用独立的会话
            async with self.get_session() as session:
                # 构建查询
                stmt = select(self.model).where(self.model.username == username)
                # 执行查询
                result = await session.execute(stmt)
                # 获取第一个结果
                user = result.scalar_one_or_none()
                
                if user:
                    self.lprint(f"找到用户: {user.username}")
                else:
                    self.lprint(f"用户不存在: {username}")
                    
                return user
                
        except Exception as e:
            self.lprint(f"获取用户失败: {str(e)}")
            self.lprint(traceback.format_exc())
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据用户ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[User]: 用户对象,不存在返回None
        """
        try:
            # 使用独立的会话
            async with self.get_session() as session:
                # 构建查询
                stmt = select(self.model).where(self.model.id == user_id)
                # 执行查询
                result = await session.execute(stmt)
                # 获取第一个结果
                user = result.scalar_one_or_none()
                
                if user:
                    self.lprint(f"找到用户: {user.username}")
                else:
                    self.lprint(f"用户不存在: id={user_id}")
                    
                return user
                
        except Exception as e:
            self.lprint(f"获取用户失败: {str(e)}")
            self.lprint(traceback.format_exc())
            return None
    
    async def create_user(self, username: str, hashed_password: str, email: str,
                         role: str = "user", nickname: Optional[str] = None) -> Optional[User]:
        """创建新用户"""
        try:
            # 检查用户名是否已存在
            existing_user = await self.get_user_by_username(username)
            if existing_user:
                raise ValueError("用户名已存在")
            
            # 创建新用户
            user = await self.create(
                username=username,
                hashed_password=hashed_password,
                email=email,
                role=UserRole[role.upper()],
                status=1,  # 1 表示激活状态
                nickname=nickname,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            return user
            
        except ValueError as e:
            raise
        except Exception as e:
            self.lprint(f"创建用户失败: {str(e)}")
            traceback.print_exc()
            return None
    
    async def update_user_status(self, user_id: int, status: UserStatusEnum) -> bool:
        """更新用户状态"""
        try:
            await self.update(user_id, status=status, updated_at=datetime.now())
            return True
        except Exception as e:
            self.lprint(f"更新用户状态失败: {str(e)}")
            traceback.print_exc()
            return False
    
    async def update_user_role(self, user_id: int, role: UserRole) -> bool:
        """更新用户角色"""
        try:
            await self.update(user_id, role=role, updated_at=datetime.now())
            return True
        except Exception as e:
            self.lprint(f"更新用户角色失败: {str(e)}")
            traceback.print_exc()
            return False

# 创建全局的 AuthRepository 实例
_auth_repository = None

def get_auth_repository() -> AuthRepository:
    """获取AuthRepository实例"""
    global _auth_repository
    if _auth_repository is None:
        _auth_repository = AuthRepository()
    return _auth_repository 