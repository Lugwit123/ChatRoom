"""
核心门面模块
提供应用程序的核心服务管理和初始化功能
"""
from typing import Optional, TypeVar, Type, Any
import Lugwit_Module as LM
from app.core.di.container import Container, get_container

lprint = LM.lprint

T = TypeVar('T')

class CoreFacade:
    """核心门面类
    
    负责：
    1. 容器管理
    2. 核心服务初始化
    3. 全局配置管理
    """
    def __init__(self, container: Optional[Container] = None):
        """初始化核心门面
        
        Args:
            container: 容器实例，如果为None则使用全局容器
        """
        self._container = container or get_container()
        lprint = LM.lprint
        lprint("核心门面初始化完成")
            
    @property
    def container(self) -> Container:
        """获取容器实例"""
        return self._container

    def resolve(self, interface: Type[T]) -> T:
        """从容器中解析服务
        
        Args:
            interface: 要解析的接口类型
            
        Returns:
            接口的实现实例
        """
        return self.container.resolve(interface)
        
    def register_core_services(self):
        """注册核心服务
        
        包括：
        1. 数据库服务
        2. 认证服务
        3. WebSocket服务等
        """
        try:
            lprint("开始注册核心服务...")
            
            from app.db.facade.database_facade import DatabaseFacade
            from app.core.auth.facade.auth_facade import AuthFacade
            from app.core.websocket.facade.websocket_facade import WebSocketFacade
            
            # 创建并注册基础服务
            database_facade = DatabaseFacade()
            auth_facade = AuthFacade()
            
            # 注册到容器
            self.container.register_singleton(DatabaseFacade, database_facade)
            self.container.register_singleton(AuthFacade, auth_facade)
            
            lprint("核心服务注册完成")
            
        except Exception as e:
            lprint(f"注册核心服务失败: {str(e)}")
            raise 