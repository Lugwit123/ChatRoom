"""群组服务"""
# 标准库
from datetime import datetime
from typing import List, Optional
import traceback

# 第三方库
from sqlalchemy.ext.asyncio import AsyncSession

# 本地模块
from app.domain.group.models import Group, GroupMember
from app.domain.group.repository import GroupRepository, GroupMemberRepository
from app.domain.user.repository import UserRepository
from app.core.exceptions import BusinessError
import Lugwit_Module as LM
lprint = LM.lprint

class GroupService:
    """群组服务"""
    def __init__(self, group_repo: GroupRepository, member_repo: GroupMemberRepository, user_repo: UserRepository):
        self.group_repo = group_repo
        self.member_repo = member_repo
        self.user_repo = user_repo

    async def create_group(self, name: str, owner_id: int, description: Optional[str] = None) -> Group:
        """创建群组"""
        try:
            # 检查群组名是否已存在
            if await self.group_repo.get_by_name(name):
                raise BusinessError("群组名已存在")
            
            # 创建群组
            group = Group(
                name=name,
                description=description,
                owner_id=owner_id
            )
            group = await self.group_repo.create(group)
            
            # 添加创建者为群组成员
            await self.member_repo.add_member(group.id, owner_id)
            
            return group
        except Exception as e:
            lprint(f"创建群组失败: {traceback.format_exc()}")
            raise BusinessError("创建群组失败")

    async def add_member(self, group_id: int, user_id: int) -> GroupMember:
        """添加群组成员"""
        try:
            # 检查群组是否存在
            group = await self.group_repo.get_by_id(group_id)
            if not group:
                raise BusinessError("群组不存在")
            
            # 检查是否已经是成员
            if await self.member_repo.is_member(group_id, user_id):
                return True
            
            # 添加成员
            return await self.member_repo.add_member(group_id, user_id)
        except Exception as e:
            lprint(f"添加群组成员失败: {traceback.format_exc()}")
            raise BusinessError("添加群组成员失败")

    async def remove_member(self, group_id: int, user_id: int) -> bool:
        """移除群组成员"""
        try:
            # 检查群组是否存在
            group = await self.group_repo.get_by_id(group_id)
            if not group:
                raise BusinessError("群组不存在")
            
            # 不能移除群主
            if user_id == group.owner_id:
                raise BusinessError("不能移除群主")
            
            # 检查是否是成员
            member = await self.member_repo.is_member(group_id, user_id)
            if not member:
                raise BusinessError("用户不是群组成员")
            
            # 移除成员
            return await self.member_repo.delete(member.id)
        except Exception as e:
            lprint(f"移除群组成员失败: {traceback.format_exc()}")
            raise BusinessError("移除群组成员失败")

    async def get_group_members(self, group_id: int) -> List[GroupMember]:
        """获取群组成员"""
        try:
            return await self.member_repo.get_group_members(group_id)
        except Exception as e:
            lprint(f"获取群组成员失败: {traceback.format_exc()}")
            raise BusinessError("获取群组成员失败")

    async def get_user_groups(self, user_id: int) -> List[Group]:
        """获取用户的群组"""
        try:
            return await self.group_repo.get_user_groups(user_id)
        except Exception as e:
            lprint(f"获取用户群组失败: {traceback.format_exc()}")
            raise BusinessError("获取用户群组失败")

    async def bulk_create_groups(self, groups_data: List[dict]) -> List[Group]:
        """批量创建群组
        
        Args:
            groups_data: 群组数据列表，每个群组数据包含 name, owner 等字段
            
        Returns:
            List[Group]: 创建的群组列表
        """
        try:
            groups = []
            for group_data in groups_data:
                # 检查必要字段
                if not all(k in group_data for k in ["name", "owner"]):
                    lprint(f"群组数据缺少必要字段: {group_data}")
                    continue

                # 检查群组名是否已存在
                if await self.group_repo.get_by_name(group_data["name"]):
                    lprint(f"群组名已存在: {group_data['name']}")
                    continue

                # 通过用户名获取用户ID
                owner = await self.user_repo.get_by_username(group_data["owner"])
                if not owner:
                    lprint(f"找不到群主用户: {group_data['owner']}")
                    continue

                # 创建群组
                group = Group(
                    name=group_data["name"],
                    description=group_data.get("description", ""),
                    owner_id=owner.id
                )
                created_group = await self.group_repo.create(group)
                
                # 添加创建者为群组成员
                await self.add_member(created_group.id, owner.id)
                
                groups.append(created_group)

            return groups
        except Exception as e:
            lprint(f"批量创建群组失败: {str(e)}")
            raise
