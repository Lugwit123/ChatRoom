"""
核心门面模块
提供应用程序的核心服务管理和初始化功能
"""
from typing import Optional
import Lugwit_Module as LM
from app.core.di.container import Container

lprint = LM.lprint

class CoreFacade:
    """核心门面类
    
    负责：
    1. 容器管理
    2. 核心服务初始化
    3. 全局配置管理
    """
    def __init__(self, container: Container):
        """初始化核心门面
        
        Args:
            container: 容器实例
        """
        self._container = container
        self.lprint = LM.lprint
        self.lprint("核心门面初始化完成")
            
    @property
    def container(self) -> Container:
        """获取容器实例"""
        return self._container
        
    def register_core_services(self):
        """注册核心服务
        
        包括：
        1. 数据库服务
        2. 认证服务
        3. WebSocket服务等
        """
        try:
            self.lprint("开始注册核心服务...")
            
            from app.db.facade.database_facade import DatabaseFacade
            from app.core.auth.facade.auth_facade import AuthFacade
            from app.core.websocket.facade.websocket_facade import WebSocketFacade
            
            # 创建并注册基础服务
            database_facade = DatabaseFacade()
            auth_facade = AuthFacade()
            
            # 注册到容器
            self.container.register_singleton(DatabaseFacade, database_facade)
            self.container.register_singleton(AuthFacade, auth_facade)
            
            self.lprint("核心服务注册完成")
            
        except Exception as e:
            self.lprint(f"注册核心服务失败: {str(e)}")
            raise 