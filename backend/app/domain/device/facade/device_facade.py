"""
设备模块门面
提供设备相关功能的统一访问接口，包括设备注册、状态管理等功能
"""
import Lugwit_Module as LM
from typing import List, Optional
from app.domain.device.internal.services.device_service import DeviceService
from app.domain.device.facade.dto.device_dto import DeviceCreateDTO, DeviceDTO
from app.domain.base.facade.dto.base_dto import ResponseDTO

class DeviceFacade:
    """设备模块对外接口
    
    提供设备相关的所有功能访问点，包括：
    - 设备注册
    - 设备状态管理
    - 设备信息查询等
    """
    def __init__(self):
        self._device_service = DeviceService()
        self.lprint = LM.lprint
        
    async def register_device(self, device: DeviceCreateDTO) -> ResponseDTO:
        """注册新设备
        
        Args:
            device: 设备创建DTO对象
            
        Returns:
            ResponseDTO: 统一响应格式
        """
        try:
            result = await self._device_service.register_device(device.to_internal())
            return ResponseDTO.success(data=DeviceDTO.from_internal(result))
        except Exception as e:
            self.lprint(f"设备注册失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def get_device_info(self, device_id: str) -> ResponseDTO:
        """获取设备信息
        
        Args:
            device_id: 设备ID
            
        Returns:
            ResponseDTO: 包含设备信息的响应
        """
        try:
            device = await self._device_service.get_device(device_id)
            return ResponseDTO.success(data=DeviceDTO.from_internal(device))
        except Exception as e:
            self.lprint(f"获取设备信息失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def update_device_status(self, device_id: str, online: bool) -> ResponseDTO:
        """更新设备在线状态
        
        Args:
            device_id: 设备ID
            online: 是否在线
            
        Returns:
            ResponseDTO: 更新结果响应
        """
        try:
            result = await self._device_service.update_status(device_id, online)
            return ResponseDTO.success(data=DeviceDTO.from_internal(result))
        except Exception as e:
            self.lprint(f"更新设备状态失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def get_user_devices(self, user_id: str) -> ResponseDTO:
        """获取用户的设备列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            ResponseDTO: 包含设备列表的响应
        """
        try:
            devices = await self._device_service.get_user_devices(user_id)
            return ResponseDTO.success(data=[DeviceDTO.from_internal(d) for d in devices])
        except Exception as e:
            self.lprint(f"获取用户设备列表失败: {str(e)}")
            return ResponseDTO.error(message=str(e))

    async def init_all_devices_status(self):
        """初始化所有设备的在线状态为离线"""
        try:
            async with self.get_session() as session:
                await self.device_repo.reset_all_devices_status(session)
                await session.commit()
                self.lprint("已重置所有设备的在线状态为离线")
        except Exception as e:
            self.lprint(f"初始化设备状态失败: {str(e)}")
            raise e
