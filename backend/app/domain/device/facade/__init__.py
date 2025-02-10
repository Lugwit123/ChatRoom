"""设备门面模块"""
from functools import lru_cache
from app.domain.device.facade.device_facade import DeviceFacade

@lru_cache()
def get_device_facade() -> DeviceFacade:
    """获取设备门面实例
    
    Returns:
        DeviceFacade: 设备门面实例
    """
    return DeviceFacade()
