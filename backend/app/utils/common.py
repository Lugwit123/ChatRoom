"""通用工具函数"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json
import random
import string
from Lugwit_Module import lprint
import traceback

def get_utc_now() -> datetime:
    """获取当前UTC时间
    
    Returns:
        当前UTC时间
    """
    return datetime.now(timezone.utc)

def format_datetime(dt: datetime) -> str:
    """格式化日期时间
    
    Args:
        dt: 日期时间对象
        
    Returns:
        格式化后的字符串
    """
    try:
        return dt.isoformat()
    except Exception as e:
        lprint(f"日期时间格式化失败: {traceback.format_exc()}")
        return str(dt)

def parse_datetime(dt_str: str) -> Optional[datetime]:
    """解析日期时间字符串
    
    Args:
        dt_str: 日期时间字符串
        
    Returns:
        日期时间对象，解析失败返回None
    """
    try:
        return datetime.fromisoformat(dt_str)
    except Exception as e:
        lprint(f"日期时间解析失败: {traceback.format_exc()}")
        return None

def safe_json_loads(json_str: str) -> Dict[str, Any]:
    """安全的JSON解析
    
    Args:
        json_str: JSON字符串
        
    Returns:
        解析后的字典，失败返回空字典
    """
    try:
        return json.loads(json_str)
    except Exception as e:
        lprint(f"JSON解析失败: {traceback.format_exc()}")
        return {}

def safe_json_dumps(obj: Any) -> str:
    """安全的JSON序列化
    
    Args:
        obj: 要序列化的对象
        
    Returns:
        JSON字符串，失败返回空对象字符串
    """
    try:
        return json.dumps(obj, ensure_ascii=False)
    except Exception as e:
        lprint(f"JSON序列化失败: {traceback.format_exc()}")
        return "{}"

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """将列表分块
    
    Args:
        lst: 要分块的列表
        chunk_size: 块大小
        
    Returns:
        分块后的列表的列表
    """
    try:
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    except Exception as e:
        lprint(f"列表分块失败: {traceback.format_exc()}")
        return []

def flatten_list(lst: List[List[Any]]) -> List[Any]:
    """展平嵌套列表
    
    Args:
        lst: 嵌套列表
        
    Returns:
        展平后的列表
    """
    try:
        return [item for sublist in lst for item in sublist]
    except Exception as e:
        lprint(f"列表展平失败: {traceback.format_exc()}")
        return []

def remove_duplicates(lst: List[Any]) -> List[Any]:
    """移除列表中的重复项，保持顺序
    
    Args:
        lst: 输入列表
        
    Returns:
        去重后的列表
    """
    try:
        return list(dict.fromkeys(lst))
    except Exception as e:
        lprint(f"列表去重失败: {traceback.format_exc()}")
        return lst

def generate_random_string(length: int = 8) -> str:
    """生成指定长度的随机字符串
    
    Args:
        length: 字符串长度
        
    Returns:
        随机字符串
    """
    try:
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
    except Exception as e:
        lprint(f"生成随机字符串失败: {traceback.format_exc()}")
        return ''.join(random.choice(string.ascii_letters) for _ in range(length))

def get_avatar_index(username: str) -> int:
    """根据用户名生成头像索引
    
    Args:
        username: 用户名
        
    Returns:
        头像索引(0-9)
    """
    try:
        return hash(username) % 10  # 假设有10个头像可选
    except Exception as e:
        lprint(f"生成头像索引失败: {traceback.format_exc()}")
        return 0
