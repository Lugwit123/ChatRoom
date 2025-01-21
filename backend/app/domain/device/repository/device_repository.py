"""设备仓储模块"""
# 标准库
from datetime import datetime
from typing import List, Optional, Dict, Any, Sequence
import traceback

# 第三方库
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Integer
from datetime import timedelta
from datetime import timezone

# 本地模块
from app.db.base_repository import BaseRepository
from app.domain.device.models import Device
import Lugwit_Module as LM
lprint = LM.lprint

class DeviceRepository(BaseRepository[Device]):
    """设备仓储类
    
    提供设备相关的数据库操作，包括：
    1. 基本的CRUD操作（继承自BaseRepository）
    2. 设备查询（按用户、状态等）
    3. 设备状态管理
    4. 设备统计
    """
    
    def __init__(self, session: AsyncSession):
        """初始化设备仓储
        
        Args:
            session: 数据库会话
        """
        super().__init__(Device, session)

    async def create_device(self, device: Device) -> Device:
        """创建设备
        
        Args:
            device: 要创建的设备实例
            
        Returns:
            创建的设备
        """
        try:
            return await self.create(device)
        except Exception as e:
            lprint(f"创建设备失败: {traceback.format_exc()}")
            raise

    async def get_device_by_id(self, device_id: str) -> Optional[Device]:
        """根据设备ID获取设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            找到的设备或None
        """
        try:
            query = select(self.model).where(self.model.device_id == device_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            lprint(f"根据设备ID获取设备失败: {traceback.format_exc()}")
            return None

    async def get_by_user_id(self, user_id: int) -> Sequence[Device]:
        """根据用户ID获取设备列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            设备列表
        """
        try:
            query = select(self.model).where(self.model.user_id == user_id)
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            lprint(f"根据用户ID获取设备失败: {traceback.format_exc()}")
            return []

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
            query = select(Device).where(Device.user_id == user_id)
            if not include_offline:
                query = query.where(Device.login_status == True)
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            lprint(f"获取用户设备列表失败: {traceback.format_exc()}")
            return []

    async def update_device_status(
        self,
        device_id: str,
        login_status: bool = None,
        websocket_online: bool = None,
        system_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新设备状态
        
        Args:
            device_id: 设备ID
            login_status: 是否在线
            websocket_online: WebSocket是否在线
            system_info: 系统信息
            
        Returns:
            是否成功
        """
        try:
            # 构建更新数据
            update_data = {}
            if login_status is not None:
                update_data["login_status"] = login_status
            if websocket_online is not None:
                update_data["websocket_online"] = websocket_online
            if system_info:
                update_data["system_info"] = system_info
            
            if not update_data:
                return True
                
            # 更新last_seen
            update_data["last_seen"] = datetime.now(timezone.utc)
            
            # 执行更新
            stmt = (
                update(self.model)
                .where(self.model.device_id == device_id)
                .values(**update_data)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            return True
            
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
            query = select(
                func.count(Device.device_id).label("total_count"),
                func.sum(Device.login_status.cast(Integer)).label("online_count")
            )
            
            if user_id:
                query = query.where(Device.user_id == user_id)
                
            result = await self.session.execute(query)
            row = result.first()
            
            return {
                "total_count": row.total_count or 0,
                "online_count": row.online_count or 0,
                "offline_count": (row.total_count or 0) - (row.online_count or 0)
            }
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
            cutoff_time = datetime.now() - timedelta(hours=inactive_hours)
            query = select(Device).where(
                and_(
                    Device.login_status == True,
                    Device.last_login < cutoff_time
                )
            )
            result = await self.session.execute(query)
            devices = result.scalars().all()
            
            for device in devices:
                await self.update_device_status(device.device_id, False)
                
            return len(devices)
        except Exception as e:
            lprint(f"清理不活跃设备失败: {traceback.format_exc()}")
            return 0

    async def reset_all_devices_status(self, session: AsyncSession):
        """重置所有设备的在线状态为离线"""
        await session.execute(
            update(Device).values(
                login_status=False,
                websocket_online=False
            )
        )
