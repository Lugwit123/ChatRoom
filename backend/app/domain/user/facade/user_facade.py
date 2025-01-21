"""
用户模块门面
提供用户相关功能的统一访问接口，包括用户注册、登录、信息管理等功能
"""
import Lugwit_Module as LM
from typing import List, Optional
from app.domain.user.internal.services.user_service import UserService
from app.domain.user.facade.dto.user_dto import UserCreateDTO, UserDTO, UserLoginDTO
from app.domain.base.facade.dto.base_dto import ResponseDTO

class UserFacade:
    """用户模块对外接口
    
    提供用户相关的所有功能访问点，包括：
    - 用户注册
    - 用户登录
    - 用户信息查询
    - 用户信息更新等
    """
    def __init__(self):
        self._user_service = UserService()
        self.lprint = LM.lprint
        
    async def register(self, user: UserCreateDTO) -> ResponseDTO:
        """注册新用户
        
        Args:
            user: 用户创建DTO对象
            
        Returns:
            ResponseDTO: 统一响应格式
        """
        try:
            result = await self._user_service.create_user(user.to_internal())
            return ResponseDTO.success(data=UserDTO.from_internal(result))
        except Exception as e:
            self.lprint(f"用户注册失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def login(self, login_data: UserLoginDTO) -> ResponseDTO:
        """用户登录
        
        Args:
            login_data: 登录信息DTO
            
        Returns:
            ResponseDTO: 包含用户信息和token的响应
        """
        try:
            result = await self._user_service.login(login_data.to_internal())
            return ResponseDTO.success(data=result)
        except Exception as e:
            self.lprint(f"用户登录失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def get_user_info(self, user_id: str) -> ResponseDTO:
        """获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            ResponseDTO: 包含用户信息的响应
        """
        try:
            user = await self._user_service.get_user(user_id)
            return ResponseDTO.success(data=UserDTO.from_internal(user))
        except Exception as e:
            self.lprint(f"获取用户信息失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def update_user_info(self, user_id: str, user_info: UserDTO) -> ResponseDTO:
        """更新用户信息
        
        Args:
            user_id: 用户ID
            user_info: 用户信息DTO
            
        Returns:
            ResponseDTO: 更新结果响应
        """
        try:
            result = await self._user_service.update_user(user_id, user_info.to_internal())
            return ResponseDTO.success(data=UserDTO.from_internal(result))
        except Exception as e:
            self.lprint(f"更新用户信息失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
