"""
认证管理器模块
处理所有登录相关的逻辑
"""
import os
import sys
import asyncio
import aiohttp
import traceback
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from PySide6.QtCore import QObject, Signal
import Lugwit_Module as LM
lprint = LM.lprint

class AuthManager(QObject):
    """认证管理器类"""
    
    # 定义信号
    login_success = Signal(str)  # 登录成功信号，传递token
    login_failed = Signal(str)   # 登录失败信号，传递错误信息
    logout_success = Signal()    # 登出成功信号
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化认证管理器"""
        super().__init__()
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.token: Optional[str] = None
            self.username: Optional[str] = None
            self.device_id: Optional[str] = None
            self.is_logged_in: bool = False
            self.nickname : Optional[str] = None
            self.current_user = None  # 初始化当前用户
            
            # 从环境变量获取服务器配置
            self.server_ip = os.getenv('SERVER_IP', 'localhost')
            self.server_port = int(os.getenv('SERVER_PORT', '1026'))
            self.base_url = f'http://{self.server_ip}:{self.server_port}'
            
            lprint(f"认证管理器初始化完成: server={self.server_ip}, port={self.server_port}")
        
    @classmethod
    def get_instance(cls) -> 'AuthManager':
        if not cls._instance:
            cls._instance = AuthManager()
        return cls._instance

    async def login(self, username: str, password: str = "666", nickname="") -> Tuple[bool, str]:
        """登录
        
        Args:
            username: 用户名
            password: 密码，默认为"666"
            
        Returns:
            Tuple[bool, str]: (是否成功, token或错误信息)
        """
        try:
            lprint(f"开始登录: username={username}")
            
            # 如果已经登录，先登出
            if self.is_logged_in:
                await self.logout()
            
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('username', username)
                data.add_field('password', password)
                data.add_field('grant_type', 'password')
                data.add_field('scope', '')
                data.add_field('client_id', '')
                data.add_field('client_secret', '')
                data.add_field('nickname', '')
                
                headers = {
                    'Accept': 'application/json',
                }
                
                async with session.post(
                    f'{self.base_url}/api/auth/login',
                    data=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.token = result.get('access_token')
                        if not self.token:
                            error_msg = "登录响应中没有access_token"
                            lprint(error_msg)
                            self.login_failed.emit(error_msg)
                            return False, error_msg
                            
                        # 直接从响应中获取设备ID
                        device_id = result.get('device_id', '')
                        lprint(f"获取到设备ID: {device_id}")
                            
                        self.username = username
                        self.is_logged_in = True
                        self.device_id = device_id  # 保存设备ID
                        lprint(f"登录成功: username={username}, device_id={device_id}")
                        self.login_success.emit(self.token)
                        return True, self.token
                    else:
                        error_msg = await response.text()
                        lprint(f"登录失败: {error_msg}")
                        self.login_failed.emit(error_msg)
                        return False, error_msg
                        
        except aiohttp.ClientError as e:
            error_msg = f"服务器连接失败: {str(e)}"
            lprint(error_msg)
            self.login_failed.emit(error_msg)
            return False, error_msg
        except asyncio.TimeoutError:
            error_msg = "登录请求超时"
            lprint(error_msg)
            self.login_failed.emit(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"登录过程中出错: {str(e)}"
            lprint(error_msg)
            traceback.print_exc()
            self.login_failed.emit(error_msg)
            return False, error_msg
            
    async def logout(self) -> bool:
        """登出
        
        Returns:
            bool: 是否成功登出
        """
        try:
            if not self.is_logged_in:
                return True
                
            self.token = None
            self.username = None
            self.device_id = None
            self.is_logged_in = False
            self.logout_success.emit()
            lprint("登出成功")
            return True
            
        except Exception as e:
            lprint(f"登出过程中出错: {str(e)}")
            traceback.print_exc()
            return False
            
    def get_token(self) -> Optional[str]:
        """获取当前token
        
        Returns:
            Optional[str]: 当前token，如果未登录则返回None
        """
        return self.token if self.is_logged_in else None
        

    def get_current_user(self):
        # 返回当前用户
        return self.username if self.is_logged_in else None


# 创建全局认证管理器实例
auth_manager = AuthManager() 