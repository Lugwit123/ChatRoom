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
import asyncio
from asyncpg.exceptions import ConnectionDoesNotExistError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.domain.common.models.tables import User
from app.domain.common.enums import UserRole, UserStatusEnum
from app.core.base.internal.repository.core_repository import CoreRepository
from app.db.facade.database_facade import DatabaseFacade
from app.utils.security import verify_password
from app.core.services.service_core import get_user_facade

class AuthRepository(CoreRepository[User]):
    """认证仓库类"""
    
    def __init__(self):
        """初始化认证仓库"""
        super().__init__(User)
        self._user_facade = get_user_facade()
    
    async def login_user(self, username: str, password: str) -> Optional[User]:
        """处理用户登录逻辑"""
        try:
            user = await self._user_facade.get_user_by_username(username)
            if user and verify_password(password, str(user.hashed_password)):
                return user
            return None
        except Exception as e:
            lprint(f"用户登录失败: {str(e)}")
            traceback.print_exc()
            return None

    async def update_login_status(self, user_id: int, status: UserStatusEnum) -> bool:
        """更新用户状态"""
        try:
            await self.update(user_id, status=status, updated_at=datetime.now())
            return True
        except Exception as e:
            lprint(f"更新用户状态失败: {str(e)}")
            traceback.print_exc()
            return False
    
    async def update_user_role(self, user_id: int, role: UserRole) -> bool:
        """更新用户角色"""
        try:
            await self.update(user_id, role=role, updated_at=datetime.now())
            return True
        except Exception as e:
            lprint(f"更新用户角色失败: {str(e)}")
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