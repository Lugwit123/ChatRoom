# utils.py
import random
import string
from datetime import datetime, timezone

def get_avatar_index(username: str) -> int:
    return (hash(username) % 5) + 1

def generate_random_string(length: int = 8) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_current_time() -> datetime:
    """获取当前时间（带时区）"""
    return datetime.now(timezone.utc)
