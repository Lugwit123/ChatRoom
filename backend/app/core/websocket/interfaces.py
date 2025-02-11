"""
WebSocket模块的接口定义
定义了WebSocket相关组件的抽象接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Set, Optional
from datetime import datetime
from .facade.dto.websocket_dto import DeviceSession

class IConnectionManager(ABC):
    """连接管理器接口"""
    
    @abstractmethod
    async def add_connection(self, sid: str, user_id: str, device_id: str, ip_address: str) -> None:
        """添加新的WebSocket连接"""
        pass
        
    @abstractmethod
    async def remove_connection(self, sid: str) -> None:
        """移除WebSocket连接"""
        pass
        
    @abstractmethod
    def get_user_id(self, sid: str) -> Optional[str]:
        """获取会话对应的用户ID"""
        pass
        
    @abstractmethod
    def get_user_connections(self, user_id: str) -> Set[str]:
        """获取用户的所有活跃连接"""
        pass
        
    @abstractmethod
    def get_device_session(self, sid: str) -> Optional[DeviceSession]:
        """获取设备会话信息"""
        pass
        
    @abstractmethod
    def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        pass

class IRoomManager(ABC):
    """房间管理器接口"""
    
    @abstractmethod
    async def join_room(self, sid: str, room: str) -> None:
        """用户加入房间"""
        pass
        
    @abstractmethod
    async def leave_room(self, sid: str, room: str) -> None:
        """用户离开房间"""
        pass
        
    @abstractmethod
    def get_room_members(self, room: str) -> Set[str]:
        """获取房间的所有成员"""
        pass
        
    @abstractmethod
    def get_user_rooms(self, sid: str) -> Set[str]:
        """获取用户加入的所有房间"""
        pass
        
    @abstractmethod
    async def remove_sid(self, sid: str) -> None:
        """清理用户的所有房间记录"""
        pass

class IWebSocketEventHandler(ABC):
    """WebSocket事件处理器接口"""
    
    @abstractmethod
    async def on_connect(self, sid: str, environ: dict, auth: Optional[dict] = None) -> None:
        """处理连接事件"""
        pass
        
    @abstractmethod
    async def on_disconnect(self, sid: str) -> None:
        """处理断开连接事件"""
        pass
        
    @abstractmethod
    async def on_message(self, sid: str, data: dict) -> None:
        """处理消息事件"""
        pass
        
    @abstractmethod
    async def on_error(self, sid: str, error: Exception) -> None:
        """处理错误事件"""
        pass 