"""
群组模块门面
提供群组相关功能的统一访问接口，包括群组创建、管理、成员管理等功能
"""
import sys
import traceback
from datetime import datetime
from typing import Optional, List, Dict, Any
from zoneinfo import ZoneInfo

from app.domain.common.models.tables import User, Group, GroupMember
from app.domain.common.enums.group import GroupMemberRole, GroupStatus
from app.domain.group.internal.repository.group_repository import GroupRepository
from app.domain.group.facade.dto.group_dto import (
    GroupCreate, 
    GroupResponse, 
    GroupMemberInfo,
    GroupMemberCreate,
    GroupMemberUpdate,
    GroupListResponse,
    GroupMemberListResponse
)
from app.domain.base.facade.dto.base_dto import ResponseDTO
from app.db.facade.database_facade import DatabaseFacade

sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

# 群组门面单例
_group_facade = None

def get_group_facade() -> 'GroupFacade':
    """获取群组门面单例
    
    Returns:
        GroupFacade: 群组门面实例
    """
    global _group_facade
    if _group_facade is None:
        _group_facade = GroupFacade()
    return _group_facade

class GroupFacade:
    """群组模块对外接口
    
    提供群组相关的所有功能访问点，包括：
    - 群组创建
    - 群组管理
    - 成员管理
    - 群组查询等
    """
    
    def __init__(self):
        """初始化群组门面"""
        self._database_facade = DatabaseFacade()
        self._group_repository = GroupRepository()
        self.lprint = LM.lprint
        
    async def create_group(self, group: GroupCreate, current_user: User) -> ResponseDTO:
        """创建群组
        
        Args:
            group: 群组创建DTO
            current_user: 当前用户
            
        Returns:
            ResponseDTO: 统一响应格式
        """
        try:
            # 创建群组
            group_data = {
                "name": group.name,
                "description": group.description,
                "owner_id": current_user.id,
                "extra_data": group.extra_data
            }
            new_group = await self._group_repository.create(Group(**group_data))
            
            # 添加群主为成员
            await self._group_repository.add_member(
                new_group.id,
                current_user.id,
                GroupMemberRole.owner
            )
            
            # 添加初始成员
            for member_id in group.initial_members:
                await self._group_repository.add_member(
                    new_group.id,
                    int(member_id),
                    GroupMemberRole.member
                )
            
            return ResponseDTO.success(data=GroupResponse.from_orm(new_group))
            
        except Exception as e:
            self.lprint(f"创建群组失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def get_groups(self, current_user: User) -> ResponseDTO:
        """获取群组列表
        
        Args:
            current_user: 当前用户
            
        Returns:
            ResponseDTO: 包含群组列表的响应
        """
        try:
            groups = await self._group_repository.get_user_groups(current_user.id)
            return ResponseDTO.success(data=GroupListResponse(
                groups=[GroupResponse.from_orm(g) for g in groups],
                total=len(groups)
            ))
        except Exception as e:
            self.lprint(f"获取群组列表失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def get_group(self, group_id: str) -> ResponseDTO:
        """获取群组信息
        
        Args:
            group_id: 群组ID
            
        Returns:
            ResponseDTO: 包含群组信息的响应
        """
        try:
            group = await self._group_repository.get_by_id(int(group_id))
            if not group:
                return ResponseDTO.error(message="群组不存在")
            return ResponseDTO.success(data=GroupResponse.from_orm(group))
        except Exception as e:
            self.lprint(f"获取群组信息失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def add_member(self, group_id: str, member: GroupMemberCreate, current_user: User) -> ResponseDTO:
        """添加群组成员
        
        Args:
            group_id: 群组ID
            member: 成员创建DTO
            current_user: 当前用户
            
        Returns:
            ResponseDTO: 操作结果响应
        """
        try:
            # 检查权限
            group = await self._group_repository.get_by_id(int(group_id))
            if not group:
                return ResponseDTO.error(message="群组不存在")
                
            if group.owner_id != current_user.id:
                return ResponseDTO.error(message="只有群主可以添加成员")
                
            # 添加成员
            new_member = await self._group_repository.add_member(
                int(group_id),
                int(member.user_id),
                member.role
            )
            if not new_member:
                return ResponseDTO.error(message="添加成员失败")
                
            return ResponseDTO.success(data=GroupMemberInfo.from_orm(new_member))
            
        except Exception as e:
            self.lprint(f"添加群组成员失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def get_members(self, group_id: str) -> ResponseDTO:
        """获取群组成员列表
        
        Args:
            group_id: 群组ID
            
        Returns:
            ResponseDTO: 包含成员列表的响应
        """
        try:
            members = await self._group_repository.get_group_members(int(group_id))
            return ResponseDTO.success(data=GroupMemberListResponse(
                members=[GroupMemberInfo.from_orm(m) for m in members],
                total=len(members)
            ))
        except Exception as e:
            self.lprint(f"获取群组成员列表失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def update_member(self, group_id: str, user_id: str, member: GroupMemberUpdate, current_user: User) -> ResponseDTO:
        """更新群组成员信息
        
        Args:
            group_id: 群组ID
            user_id: 用户ID
            member: 成员更新DTO
            current_user: 当前用户
            
        Returns:
            ResponseDTO: 操作结果响应
        """
        try:
            # 检查权限
            group = await self._group_repository.get_by_id(int(group_id))
            if not group:
                return ResponseDTO.error(message="群组不存在")
                
            if group.owner_id != current_user.id:
                return ResponseDTO.error(message="只有群主可以更新成员信息")
                
            # 更新成员
            success = await self._group_repository.update_member_role(
                int(group_id),
                int(user_id),
                member.role
            )
            if not success:
                return ResponseDTO.error(message="更新成员信息失败")
                
            updated_member = await self._group_repository.get_member(int(group_id), int(user_id))
            return ResponseDTO.success(data=GroupMemberInfo.from_orm(updated_member))
            
        except Exception as e:
            self.lprint(f"更新群组成员信息失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def remove_member(self, group_id: str, user_id: str, current_user: User) -> ResponseDTO:
        """移除群组成员
        
        Args:
            group_id: 群组ID
            user_id: 用户ID
            current_user: 当前用户
            
        Returns:
            ResponseDTO: 操作结果响应
        """
        try:
            # 检查权限
            group = await self._group_repository.get_by_id(int(group_id))
            if not group:
                return ResponseDTO.error(message="群组不存在")
                
            if group.owner_id != current_user.id:
                return ResponseDTO.error(message="只有群主可以移除成员")
                
            # 移除成员
            success = await self._group_repository.remove_member(int(group_id), int(user_id))
            if not success:
                return ResponseDTO.error(message="移除成员失败")
                
            return ResponseDTO.success()
            
        except Exception as e:
            self.lprint(f"移除群组成员失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def join_group(self, group_id: str, current_user: User) -> ResponseDTO:
        """加入群组
        
        Args:
            group_id: 群组ID
            current_user: 当前用户
            
        Returns:
            ResponseDTO: 操作结果响应
        """
        try:
            # 检查群组是否存在
            group = await self._group_repository.get_by_id(int(group_id))
            if not group:
                return ResponseDTO.error(message="群组不存在")
                
            # 检查是否已经是成员
            is_member = await self._group_repository.is_member(int(group_id), current_user.id)
            if is_member:
                return ResponseDTO.error(message="已经是群组成员")
                
            # 添加成员
            new_member = await self._group_repository.add_member(
                int(group_id),
                current_user.id,
                GroupMemberRole.member
            )
            if not new_member:
                return ResponseDTO.error(message="加入群组失败")
                
            return ResponseDTO.success(data=GroupMemberInfo.from_orm(new_member))
            
        except Exception as e:
            self.lprint(f"加入群组失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def leave_group(self, group_id: str, current_user: User) -> ResponseDTO:
        """退出群组
        
        Args:
            group_id: 群组ID
            current_user: 当前用户
            
        Returns:
            ResponseDTO: 操作结果响应
        """
        try:
            # 检查群组是否存在
            group = await self._group_repository.get_by_id(int(group_id))
            if not group:
                return ResponseDTO.error(message="群组不存在")
                
            # 群主不能退出
            if group.owner_id == current_user.id:
                return ResponseDTO.error(message="群主不能退出群组")
                
            # 检查是否是成员
            is_member = await self._group_repository.is_member(int(group_id), current_user.id)
            if not is_member:
                return ResponseDTO.error(message="不是群组成员")
                
            # 移除成员
            success = await self._group_repository.remove_member(int(group_id), current_user.id)
            if not success:
                return ResponseDTO.error(message="退出群组失败")
                
            return ResponseDTO.success()
            
        except Exception as e:
            self.lprint(f"退出群组失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def delete_group(self, group_id: str, current_user: User) -> ResponseDTO:
        """删除群组
        
        Args:
            group_id: 群组ID
            current_user: 当前用户
            
        Returns:
            ResponseDTO: 操作结果响应
        """
        try:
            # 检查群组是否存在
            group = await self._group_repository.get_by_id(int(group_id))
            if not group:
                return ResponseDTO.error(message="群组不存在")
                
            # 检查权限
            if group.owner_id != current_user.id:
                return ResponseDTO.error(message="只有群主可以删除群组")
                
            # 删除群组
            success = await self._group_repository.delete(int(group_id))
            if not success:
                return ResponseDTO.error(message="删除群组失败")
                
            return ResponseDTO.success()
            
        except Exception as e:
            self.lprint(f"删除群组失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
