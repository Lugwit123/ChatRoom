"""
群组模块门面
提供群组相关功能的统一访问接口，包括群组创建、管理、成员管理等功能
"""
import Lugwit_Module as LM
from typing import List, Optional
from app.domain.group.internal.services.group_service import GroupService
from app.domain.group.facade.dto.group_dto import GroupCreateDTO, GroupDTO, GroupMemberDTO
from app.domain.base.facade.dto.base_dto import ResponseDTO

class GroupFacade:
    """群组模块对外接口
    
    提供群组相关的所有功能访问点，包括：
    - 群组创建
    - 群组信息管理
    - 成员管理
    - 群组查询等
    """
    def __init__(self):
        self._group_service = GroupService()
        self.lprint = LM.lprint
        
    async def create_group(self, group: GroupCreateDTO) -> ResponseDTO:
        """创建新群组
        
        Args:
            group: 群组创建DTO对象
            
        Returns:
            ResponseDTO: 统一响应格式
        """
        try:
            result = await self._group_service.create_group(group.to_internal())
            return ResponseDTO.success(data=GroupDTO.from_internal(result))
        except Exception as e:
            self.lprint(f"创建群组失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def get_group_info(self, group_id: str) -> ResponseDTO:
        """获取群组信息
        
        Args:
            group_id: 群组ID
            
        Returns:
            ResponseDTO: 包含群组信息的响应
        """
        try:
            group = await self._group_service.get_group(group_id)
            return ResponseDTO.success(data=GroupDTO.from_internal(group))
        except Exception as e:
            self.lprint(f"获取群组信息失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def add_member(self, group_id: str, user_id: str) -> ResponseDTO:
        """添加群组成员
        
        Args:
            group_id: 群组ID
            user_id: 用户ID
            
        Returns:
            ResponseDTO: 添加结果响应
        """
        try:
            result = await self._group_service.add_member(group_id, user_id)
            return ResponseDTO.success(data=GroupMemberDTO.from_internal(result))
        except Exception as e:
            self.lprint(f"添加群组成员失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def remove_member(self, group_id: str, user_id: str) -> ResponseDTO:
        """移除群组成员
        
        Args:
            group_id: 群组ID
            user_id: 用户ID
            
        Returns:
            ResponseDTO: 移除结果响应
        """
        try:
            await self._group_service.remove_member(group_id, user_id)
            return ResponseDTO.success()
        except Exception as e:
            self.lprint(f"移除群组成员失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def get_user_groups(self, user_id: str) -> ResponseDTO:
        """获取用户加入的群组列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            ResponseDTO: 包含群组列表的响应
        """
        try:
            groups = await self._group_service.get_user_groups(user_id)
            return ResponseDTO.success(data=[GroupDTO.from_internal(g) for g in groups])
        except Exception as e:
            self.lprint(f"获取用户群组列表失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
