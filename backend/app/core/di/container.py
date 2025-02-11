"""
依赖注入容器
管理所有依赖的注册和解析，并提供全局访问点
"""
from typing import Dict, Type, TypeVar, Any, Optional, cast
import Lugwit_Module as LM

lprint = LM.lprint

T = TypeVar('T')

class Container:
    """依赖注入容器"""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not self._initialized:
            self._services: Dict[Type, Any] = {}
            self._singletons: Dict[Type, Any] = {}
            self._initialized = True
            lprint("依赖注入容器初始化完成")
            
    def register(self, interface: Type[T], implementation: Type[T]) -> None:
        """注册服务
        
        Args:
            interface: 接口类型
            implementation: 实现类型
        """
        self._services[interface] = implementation
        lprint(f"注册服务: {interface.__name__} -> {implementation.__name__}")
        
    def register_singleton(self, interface: Type[T], instance: T) -> None:
        """注册单例服务
        
        Args:
            interface: 接口类型
            instance: 单例实例
        """
        self._singletons[interface] = instance
        lprint(f"注册单例服务: {interface.__name__}")
        
    def resolve(self, interface: Type[T]) -> T:
        """解析服务
        
        Args:
            interface: 要解析的接口类型
            
        Returns:
            接口的实现实例
            
        Raises:
            KeyError: 如果接口未注册
        """
        # 先检查是否有单例实例
        if interface in self._singletons:
            return cast(T, self._singletons[interface])
            
        # 检查是否有注册的实现
        if interface not in self._services:
            raise KeyError(f"服务未注册: {interface.__name__}")
            
        implementation = self._services[interface]
        instance = implementation()
        return cast(T, instance)

# 全局容器实例
_global_container: Optional[Container] = None

def set_container(container: Container) -> None:
    """设置全局容器实例
    
    Args:
        container: 容器实例
    """
    global _global_container
    _global_container = container
    lprint("全局容器已设置")
    
def get_container() -> Container:
    """获取全局容器实例
    
    Returns:
        Container: 容器实例
        
    Raises:
        RuntimeError: 如果容器未初始化
    """
    if _global_container is None:
        raise RuntimeError("容器未初始化，请先调用set_container")
    return _global_container 