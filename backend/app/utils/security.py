"""安全相关工具"""
import hashlib
import secrets
from typing import Optional
from passlib.context import CryptContext
from Lugwit_Module import lprint
import traceback

# 密码上下文配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
        
    Returns:
        是否验证通过
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        lprint(f"密码验证失败: {traceback.format_exc()}")
        return False

def get_password_hash(password: str) -> str:
    """获取密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        密码哈希值
        
    Raises:
        Exception: 哈希失败
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:
        lprint(f"密码哈希失败: {traceback.format_exc()}")
        raise

def generate_token(length: int = 32) -> str:
    """生成安全令牌
    
    Args:
        length: 令牌长度
        
    Returns:
        安全令牌
    """
    return secrets.token_hex(length)

def hash_content(content: str, salt: Optional[str] = None) -> str:
    """哈希内容
    
    Args:
        content: 要哈希的内容
        salt: 盐值
        
    Returns:
        哈希值
    """
    try:
        if salt:
            content = f"{content}{salt}"
        return hashlib.sha256(content.encode()).hexdigest()
    except Exception as e:
        lprint(f"内容哈希失败: {traceback.format_exc()}")
        raise
