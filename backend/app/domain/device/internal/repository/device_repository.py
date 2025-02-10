"""设备仓库模块"""
# 标准库
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any, Sequence
from zoneinfo import ZoneInfo

# 第三方库
from sqlalchemy import select, and_, or_, update, func, cast, Integer, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# 本地模块
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from app.domain.common.models.tables import Device
from app.domain.common.enums.device import DeviceStatus
from app.domain.device.facade.dto.device_dto import DeviceDTO
from app.domain.base.internal.repository.base_repository import BaseRepository

class DeviceRepository(BaseRepository[Device]):
    """设备仓库类
    
    提供设备相关的数据库操作，包括：
    1. 基本的CRUD操作（继承自BaseRepository）
    2. 设备查询（按用户、状态等）
    3. 设备状态管理
    4. 设备统计
    """
    
    def __init__(self):
        """初始化设备仓库"""
        super().__init__(Device)

    async def get_by_device_id(self, device_id: str) -> Optional[Device]:
        """根据设备ID获取设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            Optional[Device]: 设备信息，如果不存在则返回None
        """
        try:
            query = select(self.model).where(self.model.device_id == device_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            self.lprint(f"[数据库查询] 查询设备ID {device_id} 失败: {traceback.format_exc()}")
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
                lprint(Device.login_status)
                query = query.where(Device.login_status == true())
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            lprint(f"获取用户设备列表失败: {traceback.format_exc()}")
            return []

    async def update_device_status(
        self,
        device_id: str,
        login_status: bool,
        websocket_online: bool,
        system_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新设备状态
        
        Args:
            device_id: 设备ID
            login_status: 登录状态
            websocket_online: WebSocket连接状态
            system_info: 系统信息（可选）
            
        Returns:
            是否成功
        """
        try:
            # 构建更新数据
            update_data = {
                "login_status": login_status,
                "websocket_online": websocket_online,
                "last_login": datetime.now(ZoneInfo("Asia/Shanghai"))
            }
            
            if system_info:
                update_data["system_info"] = system_info
            
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
                func.sum(cast(Device.login_status, Integer)).label("online_count")
            )
            
            if user_id:
                query = query.where(Device.user_id == user_id)
                
            result = await self.session.execute(query)
            row = result.first()
            
            if row is None:
                return {
                    "total_count": 0,
                    "online_count": 0,
                    "offline_count": 0
                }
            
            total_count = row.total_count or 0
            online_count = row.online_count or 0
            
            return {
                "total_count": total_count,
                "online_count": online_count,
                "offline_count": total_count - online_count
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
            cutoff_time = datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(hours=inactive_hours)
            query = select(Device).where(
                and_(
                    Device.login_status == true(),
                    Device.last_login < cutoff_time
                )
            )
            result = await self.session.execute(query)
            devices = result.scalars().all()
            
            for device in devices:
                device.set_offline()
            
            await self.session.commit()
            return len(devices)
        except Exception as e:
            lprint(f"清理不活跃设备失败: {traceback.format_exc()}")
            return 0

    async def init_all_devices_status(self) -> None:
        """初始化所有设备状态为离线"""
        try:
            devices = await self.session.execute(select(Device))
            devices = devices.scalars().all()
            
            for device in devices:
                device.set_offline()
            
            await self.session.commit()
        except Exception as e:
            self.lprint(f"初始化设备状态失败: {str(e)}")
            await self.session.rollback()
            raise
