"""
WebSocket管理模块
包含两个主要组件:
1. ConnectionManager: 负责管理WebSocket连接的生命周期
2. RoomManager: 负责管理WebSocket房间的创建、加入和离开

设计说明:
1. 连接管理:
   - 维护会话ID(sid)到用户ID的映射
   - 维护用户ID到会话集合的映射
   - 管理设备会话信息
   
2. 房间管理:
   - 维护房间到成员的映射
   - 维护会话到房间的映射
   - 支持私聊和群聊房间
"""
import Lugwit_Module as LM
from typing import Dict, Set, Optional
from datetime import datetime
import pytz
from ..facade.dto.websocket_dto import UserSession, DeviceSession, ConnectionInfo
from ..interfaces import IConnectionManager, IRoomManager

lprint = LM.lprint

class ConnectionManager(IConnectionManager):
    """WebSocket连接管理器
    
    主要职责:
    1. 管理WebSocket连接的生命周期
    2. 维护用户和会话的映射关系
    3. 提供设备会话信息的存储和查询
    
    数据结构:
    - _connections: Dict[str, str] - 会话ID到用户ID的映射
    - _user_connections: Dict[str, Set[str]] - 用户ID到会话集合的映射
    - _device_sessions: Dict[str, DeviceSession] - 会话ID到设备会话的映射
    """
    
    def __init__(self):
        """初始化连接管理器，创建必要的数据结构"""
        self._connections: Dict[str, str] = {}  # sid -> user_id
        self._user_connections: Dict[str, Set[str]] = {}  # user_id -> set of sids
        self._device_sessions: Dict[str, DeviceSession] = {}  # sid -> DeviceSession
        lprint("连接管理器初始化完成")
        
    async def add_connection(self, sid: str, user_id: str, device_id: str, ip_address: str) -> None:
        """添加新的WebSocket连接
        
        工作流程:
        1. 建立基础连接映射(sid -> user_id)
        2. 更新用户的会话集合
        3. 创建并存储设备会话信息
        
        Args:
            sid: Socket.IO会话ID
            user_id: 用户ID
            device_id: 设备ID
            ip_address: IP地址
        """
        # 基础连接映射
        self._connections[sid] = user_id
        
        # 更新用户的会话集合
        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(sid)
        
        # 创建设备会话信息
        self._device_sessions[sid] = DeviceSession(
            user_id=user_id,
            device_id=device_id,
            sid=sid,
            ip_address=ip_address
        )
        
        lprint(f"新连接已添加: sid={sid}, user_id={user_id}, device_id={device_id}")
        
    async def remove_connection(self, sid: str) -> None:
        """移除WebSocket连接
        
        工作流程:
        1. 清理基础连接映射
        2. 更新用户的会话集合
        3. 移除设备会话信息
        
        Args:
            sid: Socket.IO会话ID
        """
        if sid in self._connections:
            user_id = self._connections[sid]
            
            # 清理基础连接映射
            del self._connections[sid]
            
            # 更新用户的会话集合
            if user_id in self._user_connections:
                self._user_connections[user_id].discard(sid)
                if not self._user_connections[user_id]:
                    del self._user_connections[user_id]
            
            # 移除设备会话信息
            if sid in self._device_sessions:
                del self._device_sessions[sid]
                
            lprint(f"连接已移除: sid={sid}, user_id={user_id}")
                    
    def get_user_id(self, sid: str) -> Optional[str]:
        """获取会话对应的用户ID
        
        Args:
            sid: Socket.IO会话ID
            
        Returns:
            Optional[str]: 用户ID，如果连接不存在则返回None
        """
        return self._connections.get(sid)
        
    def get_user_connections(self, user_id: str) -> Set[str]:
        """获取用户的所有活跃连接
        
        Args:
            user_id: 用户ID
            
        Returns:
            Set[str]: 用户的所有Socket.IO会话ID
        """
        return self._user_connections.get(user_id, set())
        
    def get_device_session(self, sid: str) -> Optional[DeviceSession]:
        """获取设备会话信息
        
        Args:
            sid: Socket.IO会话ID
            
        Returns:
            Optional[DeviceSession]: 设备会话信息，不存在则返回None
        """
        return self._device_sessions.get(sid)
        
    def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线
        
        判断依据: 用户是否有任何活跃的WebSocket连接
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 用户是否有活跃连接
        """
        return user_id in self._user_connections and bool(self._user_connections[user_id])

class RoomManager(IRoomManager):
    """WebSocket房间管理器
    
    主要职责:
    1. 管理房间的创建和销毁
    2. 处理用户加入和离开房间
    3. 维护房间成员关系
    
    数据结构:
    - _room_members: Dict[str, Set[str]] - 房间到成员集合的映射
    - _sid_rooms: Dict[str, Set[str]] - 会话ID到房间集合的映射
    
    房间命名规则:
    - 私聊房间: private_{user1_id}_{user2_id} (ID按升序排列)
    - 群聊房间: group_{group_id}
    """
    
    def __init__(self):
        """初始化房间管理器，创建必要的数据结构"""
        self._room_members: Dict[str, Set[str]] = {}  # room -> set of sids
        self._sid_rooms: Dict[str, Set[str]] = {}     # sid -> set of rooms
        lprint("房间管理器初始化完成")
        
    async def join_room(self, sid: str, room: str) -> None:
        """用户加入房间
        
        工作流程:
        1. 确保房间存在
        2. 将用户添加到房间成员列表
        3. 更新用户的房间列表
        
        Args:
            sid: Socket.IO会话ID
            room: 房间名称
        """
        # 确保房间存在
        if room not in self._room_members:
            self._room_members[room] = set()
        self._room_members[room].add(sid)
        
        # 更新用户的房间列表
        if sid not in self._sid_rooms:
            self._sid_rooms[sid] = set()
        self._sid_rooms[sid].add(room)
        
        lprint(f"SID {sid} 加入房间 {room}")
        
    async def leave_room(self, sid: str, room: str) -> None:
        """用户离开房间
        
        工作流程:
        1. 从房间成员列表中移除用户
        2. 如果房间为空，删除房间
        3. 更新用户的房间列表
        
        Args:
            sid: Socket.IO会话ID
            room: 房间名称
        """
        # 从房间成员列表中移除用户
        if room in self._room_members:
            self._room_members[room].discard(sid)
            if not self._room_members[room]:
                del self._room_members[room]
                
        # 更新用户的房间列表
        if sid in self._sid_rooms:
            self._sid_rooms[sid].discard(room)
            if not self._sid_rooms[sid]:
                del self._sid_rooms[sid]
                
        lprint(f"SID {sid} 离开房间 {room}")
        
    def get_room_members(self, room: str) -> Set[str]:
        """获取房间的所有成员
        
        Args:
            room: 房间名称
            
        Returns:
            Set[str]: 房间内的所有会话ID
        """
        return self._room_members.get(room, set())
        
    def get_user_rooms(self, sid: str) -> Set[str]:
        """获取用户加入的所有房间
        
        Args:
            sid: Socket.IO会话ID
            
        Returns:
            Set[str]: 用户加入的所有房间名称
        """
        return self._sid_rooms.get(sid, set())
        
    async def remove_sid(self, sid: str) -> None:
        """清理SID的所有房间记录
        
        Args:
            sid: 会话ID
        """
        try:
            # 创建房间列表的副本进行遍历
            rooms = list(self._sid_rooms.get(sid, set()))
            for room in rooms:
                await self.leave_room(sid, room)
            
            # 清理记录
            if sid in self._sid_rooms:
                del self._sid_rooms[sid]
                
            lprint(f"已清理SID {sid} 的所有房间记录")
            
        except Exception as e:
            lprint(f"清理SID {sid} 的房间记录失败: {str(e)}")
            raise
