from typing import Dict, Type, TypeVar, Any, cast
from abc import ABC, abstractmethod

T = TypeVar('T')

class Container:
    """依赖注入容器，管理所有依赖的注册和解析"""
    _instance = None  # 存储唯一实例
    _initialized = False

    def __new__(cls):
        """确保只创建一个 Container 实例（单例模式）"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化存储依赖的字典"""
        if not self._initialized:
            self._services: Dict[Type, Any] = {}     # 普通服务（接口 -> 实现类）
            self._singletons: Dict[Type, Any] = {}  # 单例服务（接口 -> 实例）
            self._initialized = True
            print("✅ 依赖注入容器初始化完成")

    def register(self, interface: Type[T], implementation: Type[T]) -> None:
        """注册普通服务（接口 -> 实现类）"""
        self._services[interface] = implementation
        print(f"🔹 注册普通服务: {interface.__name__} -> {implementation.__name__}")

    def register_singleton(self, interface: Type[T], instance: T) -> None:
        """注册单例服务（接口 -> 实例）"""
        self._singletons[interface] = instance
        print(f"🔸 注册单例服务: {interface.__name__}")

    def resolve(self, interface: Type[T]) -> T:
        """解析依赖"""
        # 1️⃣ 先查找单例
        if interface in self._singletons:
            print(f"🔄 解析单例服务: {interface.__name__}")
            return cast(T, self._singletons[interface])

        # 2️⃣ 再查找普通服务
        if interface not in self._services:
            raise KeyError(f"❌ 依赖未注册: {interface.__name__}")

        print(f"🔄 解析普通服务: {interface.__name__}")
        implementation = self._services[interface]
        instance = implementation()  # 创建实例
        return cast(T, instance)


# ==================== 🎯 依赖注入示例 ====================

# 1️⃣ 定义接口（抽象基类）
class Logger(ABC):
    @abstractmethod
    def log(self, message: str):
        pass

# 2️⃣ 定义不同的实现类
class ConsoleLogger(Logger):
    def log(self, message: str):
        print(f"🖥️ ConsoleLogger: {message}")

class FileLogger(Logger):
    def log(self, message: str):
        print(f"📁 FileLogger: {message}")

# 3️⃣ 创建容器 & 注册依赖
container = Container()
container.register(Logger, ConsoleLogger)  # 注册普通服务
container.register_singleton(str, "🌍 这是一个单例字符串")  # 注册单例

# 4️⃣ 解析依赖并使用
logger = container.resolve(Logger)  # 获取 Logger 的实例
logger.log("Hello Dependency Injection!")  # 🖥️ ConsoleLogger: Hello Dependency Injection!

singleton_str = container.resolve(str)  # 获取单例
print(singleton_str)  # 🌍 这是一个单例字符串
