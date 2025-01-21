"""设备服务模块"""
# 标准库
from typing import List, Optional, Dict, Any, Sequence
import traceback
from datetime import datetime

# 第三方库
from sqlalchemy.ext.asyncio import AsyncSession

# 本地模块
from app.core.exceptions.exceptions import BusinessError
from app.domain.device.repository import DeviceRepository
from app.domain.device.models import Device
from Lugwit_Module import lprint

class DeviceService:
    """设备服务类"""
    
    def __init__(self, repository: DeviceRepository):
        """初始化设备服务
        
        Args:
            repository: 设备仓储
        """
        self.repository = repository

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
                device_id=device_id,
                device_name=device_name,
                device_type=device_type,
                user_id=user_id,
                session=session
            )
            
            lprint(f"[设备创建] 成功为用户 {user_id} 创建默认设备")
            return device
        except Exception as e:
            lprint(f"[设备创建] 为用户 {user_id} 创建默认设备失败: {traceback.format_exc()}")
            raise ValueError(f"创建默认设备失败: {str(e)}")

    async def register_device(
        self,
        device_id: str,
        device_name: str,
        device_type: str,
        user_id: int,
        session: Optional[AsyncSession] = None,
        **kwargs
    ) -> Device:
        """注册设备
        
        Args:
            device_id: 设备ID
            device_name: 设备名称
            device_type: 设备类型
            user_id: 用户ID
            session: 可选的数据库会话
            **kwargs: 其他参数
            
        Returns:
            注册的设备
            
        Raises:
            ValueError: 设备ID已存在
        """
        try:
            # 检查设备是否已存在
            existing_device = await self.repository.get_device_by_id(device_id, session)
            if existing_device:
                raise ValueError(f"设备ID {device_id} 已存在")
            
            # 创建设备实例
            device = Device(
                device_id=device_id,
                device_name=device_name,
                device_type=device_type,
                user_id=user_id,
                **kwargs
            )
            
            # 保存到数据库
            return await self.repository.create(device, session)
        except Exception as e:
            lprint(f"[设备注册] 注册设备失败: {traceback.format_exc()}")
            raise

    async def get_user_devices(
        self,
        user_id: int,
        include_offline: bool = True
    ) -> Sequence[Device]:
        """获取用户的设备列表
        
        Args:
            user_id: 用户ID
            include_offline: 是否包含离线设备
            
        Returns:
            设备列表
        """
        try:
            return await self.repository.get_user_devices(
                user_id=user_id,
                include_offline=include_offline
            )
        except Exception as e:
            lprint(f"获取用户设备列表失败: {traceback.format_exc()}")
            return []

    async def get_user_devices(self, user_id: int) -> Sequence[Device]:
        """获取用户的所有设备
        
        Args:
            user_id: 用户ID
            
        Returns:
            设备列表
        """
        try:
            return await self.repository.get_by_user_id(user_id)
        except Exception as e:
            lprint(f"获取用户设备失败: {traceback.format_exc()}")
            return []

    async def update_device_status(
        self,
        device_id: str,
        login_status: bool,
        system_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新设备状态
        
        Args:
            device_id: 设备ID
            login_status: 是否在线
            system_info: 系统信息
            
        Returns:
            是否成功
        """
        try:
            return await self.repository.update_device_status(
                device_id=device_id,
                login_status=login_status,
                system_info=system_info
            )
        except Exception as e:
            lprint(f"更新设备状态失败: {traceback.format_exc()}")
            return False

    async def get_device_stats(
        self,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取设备统计信息
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            统计信息
        """
        try:
            return await self.repository.get_device_stats(user_id=user_id)
        except Exception as e:
            lprint(f"获取设备统计信息失败: {traceback.format_exc()}")
            return {
                "total_count": 0,
                "online_count": 0,
                "offline_count": 0
            }

    async def cleanup_inactive_devices(
        self,
        inactive_hours: int = 24
    ) -> int:
        """清理不活跃设备
        
        Args:
            inactive_hours: 不活跃时间（小时）
            
        Returns:
            清理的设备数量
        """
        try:
            return await self.repository.cleanup_inactive_devices(
                inactive_hours=inactive_hours
            )
        except Exception as e:
            lprint(f"清理不活跃设备失败: {traceback.format_exc()}")
            return 0

    async def create_device(self, device: Device) -> Device:
        """创建设备
        
        Args:
            device: 要创建的设备实例
            
        Returns:
            创建的设备
        """
        try:
            return await self.repository.create_device(device)
        except Exception as e:
            lprint(f"创建设备失败: {traceback.format_exc()}")
            raise
