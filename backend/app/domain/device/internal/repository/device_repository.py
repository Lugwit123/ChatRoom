"""设备仓库模块"""
# 标准库
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any, Sequence
from zoneinfo import ZoneInfo
from datetime import timedelta

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
            async with self.get_session() as session:
                query = select(self.model).where(self.model.device_id == device_id)
                result = await session.execute(query)
                return result.scalar_one_or_none()
        except Exception as e:
            lprint(f"[数据库查询] 查询设备ID {device_id} 失败: {traceback.format_exc()}")
            return None

    async def get_by_user_id(self, user_id: int) -> Sequence[Device]:
        """根据用户ID获取设备列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            设备列表
        """
        try:
            async with self.get_session() as session:
                query = select(self.model).where(self.model.user_id == user_id)
                result = await session.execute(query)
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
            async with self.get_session() as session:
                query = select(Device).where(Device.user_id == user_id)
                if not include_offline:
                    lprint(Device.login_status)
                    query = query.where(Device.login_status == true())
                result = await session.execute(query)
                return result.scalars().all()
        except Exception as e:
            lprint(f"获取用户设备列表失败: {traceback.format_exc()}")
            return []

    async def update_device_status(
        self,
        device_id: str,
        login_status: bool,
        websocket_online: bool,
        status: Optional[str] = None
    ) -> bool:
        """更新设备状态
        
        Args:
            device_id: 设备ID
            login_status: 登录状态
            websocket_online: WebSocket在线状态
            status: 设备状态
            
        Returns:
            bool: 是否更新成功
        """
        try:
            async with self.transaction() as session:
                # 获取设备
                query = select(self.model).where(self.model.device_id == device_id)
                result = await session.execute(query)
                device = result.scalar_one_or_none()
                
                if not device:
                    lprint(f"设备不存在: {device_id}")
                    return False
                
                # 更新状态
                update_data = {
                    'login_status': login_status,
                    'websocket_online': websocket_online,
                    'updated_at': datetime.now(ZoneInfo("Asia/Shanghai"))
                }
                
                if status:
                    update_data['status'] = status
                
                update_stmt = (
                    update(self.model)
                    .where(self.model.device_id == device_id)
                    .values(**update_data)
                )
                await session.execute(update_stmt)
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
            async with self.get_session() as session:
                query = select(
                    func.count(Device.device_id).label("total_count"),
                    func.sum(cast(Device.login_status, Integer)).label("online_count")
                )
                
                if user_id:
                    query = query.where(Device.user_id == user_id)
                    
                result = await session.execute(query)
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
            async with self.transaction() as session:
                query = select(Device).where(
                    and_(
                        Device.login_status == true(),
                        Device.last_login < cutoff_time
                    )
                )
                result = await session.execute(query)
                devices = result.scalars().all()
                
                for device in devices:
                    device.set_offline()
                
                return len(devices)
        except Exception as e:
            lprint(f"清理不活跃设备失败: {traceback.format_exc()}")
            return 0

    async def init_all_devices_status(self) -> bool:
        """初始化所有设备状态为离线"""
        try:
            async with self.transaction() as session:
                update_stmt = (
                    update(self.model)
                    .values({
                        'status': DeviceStatus.offline,
                        'login_status': False,
                        'websocket_online': False,
                        'last_login': datetime.now(ZoneInfo("Asia/Shanghai"))
                    })
                )
                await session.execute(update_stmt)
                return True
        except Exception as e:
            lprint(f"初始化设备状态失败: {traceback.format_exc()}")
            return False

    async def create(self, **kwargs) -> Device:
        """创建新设备
        
        Args:
            **kwargs: 设备属性
            
        Returns:
            Device: 创建的设备
        """
        try:
            # 移除 id 字段，让数据库自动生成
            if 'id' in kwargs:
                del kwargs['id']
                
            # 创建新设备实例
            device = Device(**kwargs)
            async with self.transaction() as session:
                session.add(device)
                await session.flush()  # 刷新会话以获取生成的ID
            return device
            
        except Exception as e:
            lprint(f"创建设备失败: {str(e)}")
            raise

    async def get_online_devices(self) -> Sequence[Device]:
        """获取所有在线设备"""
        try:
            async with self.get_session() as session:
                query = select(self.model).where(self.model.login_status == true())
                result = await session.execute(query)
                return result.scalars().all()
        except Exception as e:
            lprint(f"获取在线设备失败: {traceback.format_exc()}")
            return []

    async def get_device_count(self) -> Dict[str, int]:
        """获取设备统计信息
        
        Returns:
            Dict[str, int]: 设备统计，包含总数和在线数
        """
        try:
            async with self.get_session() as session:
                # 获取总数
                total_query = select(func.count()).select_from(self.model)
                total_result = await session.execute(total_query)
                total = total_result.scalar()

                # 获取在线数
                online_query = select(func.count()).select_from(self.model).where(
                    self.model.login_status == true()
                )
                online_result = await session.execute(online_query)
                online = online_result.scalar()

                return {
                    'total': total,
                    'online': online
                }
        except Exception as e:
            lprint(f"获取设备统计失败: {traceback.format_exc()}")
            return {'total': 0, 'online': 0}
