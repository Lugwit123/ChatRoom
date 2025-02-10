"""
WebSocket连接管理器
负责管理和维护所有WebSocket连接
"""
import Lugwit_Module as LM
from typing import Dict, Set, Optional

lprint = LM.lprint

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        """初始化连接管理器"""
        self._connections: Dict[str, str] = {}  # sid -> user_id
        self._user_connections: Dict[str, Set[str]] = {}  # user_id -> set of sids
        
    async def add_connection(self, sid: str, user_id: str) -> None:
        """添加新连接
        
        Args:
            sid: Socket.IO会话ID
            user_id: 用户ID
        """
        self._connections[sid] = user_id
        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(sid)
        
    async def remove_connection(self, sid: str) -> None:
        """移除连接
        
        Args:
            sid: Socket.IO会话ID
        """
        if sid in self._connections:
            user_id = self._connections[sid]
            del self._connections[sid]
            
            if user_id in self._user_connections:
                self._user_connections[user_id].discard(sid)
                if not self._user_connections[user_id]:
                    del self._user_connections[user_id]
                    
    def get_user_id(self, sid: str) -> Optional[str]:
        """获取连接对应的用户ID
        
        Args:
            sid: Socket.IO会话ID
            
        Returns:
            Optional[str]: 用户ID，如果连接不存在则返回None
        """
        return self._connections.get(sid)
        
    def get_user_connections(self, user_id: str) -> Set[str]:
        """获取用户的所有连接
        
        Args:
            user_id: 用户ID
            
        Returns:
            Set[str]: 用户的所有Socket.IO会话ID
        """
        return self._user_connections.get(user_id, set())
        
    def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 用户是否有活跃连接
        """
        return user_id in self._user_connections and bool(self._user_connections[user_id])
