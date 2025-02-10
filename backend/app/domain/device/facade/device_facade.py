"""
设备模块门面
提供设备相关功能的统一访问接口，包括设备注册、状态管理等功能
"""
import Lugwit_Module as LM
from typing import List, Optional, Dict, Any, Sequence
from datetime import datetime
import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import DatabaseFacade
from app.domain.device.internal.repository.device_repository import DeviceRepository
from app.domain.device.facade.dto.device_dto import DeviceDTO
from app.domain.base.facade.dto.base_dto import ResponseDTO
from app.core.exceptions.exceptions import BusinessError
from app.domain.common.models.tables import Device
from app.domain.common.enums.device import DeviceType, DeviceStatus
from datetime import timezone

class DeviceFacade:
    """设备模块对外接口
    
    提供设备相关的所有功能访问点，包括：
    - 设备注册
    - 设备状态管理
    - 设备信息查询等
    """
    def __init__(self, db_facade: Optional[DatabaseFacade] = None):
        """初始化设备门面
        
        Args:
            db_facade: 数据库门面实例，如果为None则创建新实例
        """
        self._db_facade = db_facade or DatabaseFacade()
        self._device_repository = None
        self.lprint = LM.lprint
        
    async def _init_repository(self):
        """初始化仓储"""
        self._device_repository = DeviceRepository()

    async def init_all_devices_status(self):
        """初始化所有设备状态"""
        try:
            await self._init_repository()
            await self._device_repository.init_all_devices_status()
            self.lprint("已重置所有设备的在线状态为离线")
        except Exception as e:
            self.lprint(f"初始化所有设备状态失败: {str(e)}")
            raise BusinessError("初始化设备状态失败") from e

    async def create_default_device(self, user_id: int, session: Optional[AsyncSession] = None) -> Device:
        """为用户创建默认设备
        
        Args:
            user_id: 用户ID
            session: 可选的数据库会话
            
        Returns:
            创建的默认设备
            
        Raises:
            ValueError: 设备创建失败
        """
        try:
            # 生成默认设备信息
            device_id = f"default_{user_id}"
            device_name = "默认设备"
            device_type = "default"
            
            # 创建设备
            device = await self.register_device(
                DeviceDTO(
                    device_id=device_id,
                    device_name=device_name,
                    device_type=device_type,
                    user_id=user_id
                )
            )
            
            self.lprint(f"[设备创建] 成功为用户 {user_id} 创建默认设备")
            return device.data
        except Exception as e:
            self.lprint(f"[设备创建] 为用户 {user_id} 创建默认设备失败: {traceback.format_exc()}")
            raise ValueError(f"创建默认设备失败: {str(e)}")

    async def register_device(self, device: DeviceDTO) -> ResponseDTO:
        """注册新设备
        
        Args:
            device: 设备信息
            
        Returns:
            ResponseDTO: 统一响应格式
        """
        try:
            await self._init_repository()
            
            # 检查设备是否已存在
            existing_device = await self._device_repository.get_by_device_id(device.device_id)
            if existing_device:
                raise ValueError(f"设备ID {device.device_id} 已存在")
            
            # 创建设备实例
            device_data = {
                'device_id': device.device_id,
                'device_name': device.device_name,
                'device_type': device.device_type,
                'user_id': device.user_id,
                'ip_address': device.ip_address
            }
            
            # 保存到数据库
            result = await self._device_repository.create(**device_data)
            return ResponseDTO(success=True, message="设备注册成功", data=result)
        except Exception as e:
            traceback.print_exc()
            return ResponseDTO(success=False, message=str(e))

    async def update_device_status(
        self,
        device_id: str,
        is_online: bool,
        user_id: Optional[int] = None,
        client_ip: Optional[str] = None,
        system_info: Optional[Dict[str, Any]] = None
    ) -> ResponseDTO:
        """更新设备状态
        
        Args:
            device_id: 设备ID
            is_online: 是否在线
            user_id: 用户ID（可选）
            client_ip: 客户端IP（可选）
            system_info: 系统信息（可选）
            
        Returns:
            ResponseDTO: 统一响应格式
        """
        try:
            await self._init_repository()
            
            # 获取设备信息
            device = await self._device_repository.get_by_device_id(device_id)
            
            # 如果设备不存在且提供了用户ID，则创建新设备
            if not device and user_id is not None:
                device_dto = DeviceDTO(
                    device_id=device_id,
                    device_name=f"设备_{device_id[:8]}",
                    device_type=DeviceType.other,
                    user_id=user_id,
                    ip_address=client_ip
                )
                result = await self.register_device(device_dto)
                if not result.success:
                    return result
                device = result.data
            
            # 如果设备存在，更新状态
            if device:
                # 更新设备状态
                device.status = DeviceStatus.online if is_online else DeviceStatus.offline
                device.login_status = is_online
                device.websocket_online = is_online
                device.last_login = datetime.now(timezone.utc)
                if is_online:
                    device.last_login = datetime.now(timezone.utc)
                    device.login_count += 1

                # 保存更新
                await self._device_repository.update(
                    device.id,
                    status=device.status,
                    login_status=device.login_status,
                    websocket_online=device.websocket_online,
                    last_login=device.last_login,
                    login_count=device.login_count
                )
                self.lprint(f"[设备状态] 成功更新设备 {device_id} 状态为 {'在线' if is_online else '离线'}")
                return ResponseDTO(success=True, message="设备状态更新成功", data=device)
            
            self.lprint(f"[设备状态] 设备 {device_id} 不存在且无法创建")
            return ResponseDTO(success=False, message="设备不存在且无法创建")
        except Exception as e:
            self.lprint(f"更新设备状态失败: {str(e)}")
            return ResponseDTO(success=False, message=str(e))

    async def get_device_info(self, device_id: str) -> ResponseDTO:
        """获取设备信息
        
        Args:
            device_id: 设备ID
            
        Returns:
            ResponseDTO: 统一响应格式
        """
        try:
            await self._init_repository()
            device = await self._device_repository.get_by_device_id(device_id)
            if device:
                return ResponseDTO(success=True, message="设备信息获取成功", data=device)
            return ResponseDTO(success=False, message="设备不存在")
        except Exception as e:
            self.lprint(f"获取设备信息失败: {str(e)}")
            return ResponseDTO(success=False, message=str(e))

    async def get_user_devices(
        self,
        user_id: int,
        include_offline: bool = True
    ) -> ResponseDTO:
        """获取用户的设备列表
        
        Args:
            user_id: 用户ID
            include_offline: 是否包含离线设备
            
        Returns:
            ResponseDTO: 统一响应格式
        """
        try:
            await self._init_repository()
            devices = await self._device_repository.get_user_devices(
                user_id=user_id,
                include_offline=include_offline
            )
            return ResponseDTO(success=True, message="设备列表获取成功", data=devices)
        except Exception as e:
            self.lprint(f"获取用户设备列表失败: {str(e)}")
            return ResponseDTO(success=False, message=str(e))

    async def get_device_stats(
        self,
        user_id: Optional[int] = None
    ) -> ResponseDTO:
        """获取设备统计信息
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            ResponseDTO: 统一响应格式
        """
        try:
            await self._init_repository()
            stats = await self._device_repository.get_device_stats(user_id=user_id)
            return ResponseDTO(success=True, message="设备统计信息获取成功", data=stats)
        except Exception as e:
            self.lprint(f"获取设备统计信息失败: {str(e)}")
            return ResponseDTO(success=False, message=str(e))

    async def cleanup_inactive_devices(
        self,
        inactive_hours: int = 24
    ) -> ResponseDTO:
        """清理不活跃设备
        
        Args:
            inactive_hours: 不活跃时间（小时）
            
        Returns:
            ResponseDTO: 统一响应格式
        """
        try:
            await self._init_repository()
            count = await self._device_repository.cleanup_inactive_devices(
                inactive_hours=inactive_hours
            )
            return ResponseDTO(success=True, message="不活跃设备清理成功", data={"cleaned_count": count})
        except Exception as e:
            self.lprint(f"清理不活跃设备失败: {str(e)}")
            return ResponseDTO(success=False, message=str(e))
