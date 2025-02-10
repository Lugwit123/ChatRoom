"""日期时间相关的工具函数"""
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

def to_timestamp(dt: Optional[datetime]) -> Optional[float]:
    """转换datetime为时间戳
    
    Args:
        dt: datetime对象
        
    Returns:
        时间戳，如果输入为None则返回None
    """
    if dt is None:
        return None
    return dt.timestamp()


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """转换datetime为ISO 8601格式字符串
    
    将datetime对象转换为严格的 ISO 8601 格式，包含：
    - 日期部分：YYYY-MM-DD
    - 时间部分：HH:mm:ss.ffffff
    - 时区部分：+HH:MM 或 Z (UTC)
    
    Args:
        dt: 要转换的datetime对象
        
    Returns:
        ISO 8601格式字符串，如：2024-02-07T15:30:45.123456+08:00
        如果输入为None，则返回None
        
    Examples:
        >>> from datetime import datetime
        >>> from zoneinfo import ZoneInfo
        >>> dt = datetime(2024, 2, 7, 15, 30, 45, 123456, tzinfo=ZoneInfo("Asia/Shanghai"))
        >>> format_datetime(dt)
        '2024-02-07T15:30:45.123456+08:00'
        >>> format_datetime(None)
        None
    """
    if dt is None:
        return None
        
    # 确保datetime有时区信息
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        
    # 使用 isoformat() 并确保包含微秒
    # 如果微秒为0，手动添加 .000000
    iso_str = dt.isoformat()
    if '+' in iso_str:
        time_part, tz_part = iso_str.split('+')
        if '.' not in time_part:
            time_part += '.000000'
        return f"{time_part}+{tz_part}"
    else:
        if '.' not in iso_str:
            iso_str = f"{iso_str}.000000"
        return iso_str
