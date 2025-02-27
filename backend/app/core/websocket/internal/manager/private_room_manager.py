"""房间管理器模块"""
from typing import Dict, Set, Optional, List, NamedTuple
from dataclasses import dataclass
from datetime import datetime
from ...interfaces import IRoomManager

import Lugwit_Module as LM
lprint = LM.lprint

@dataclass
class RoomInfo:
    """房间信息"""
    name: str                    # 房间名称
    members: Set[str]           # 成员ID集合
    created_at: datetime        # 创建时间
    last_active: datetime       # 最后活跃时间
    message_count: int = 0      # 消息数量
    
    def add_member(self, user_id: str) -> None:
        """添加成员"""
        self.members.add(user_id)
        self.last_active = datetime.now()
        
    def remove_member(self, user_id: str) -> None:
        """移除成员"""
        self.members.discard(user_id)
        self.last_active = datetime.now()
        
    def is_member(self, user_id: str) -> bool:
        """检查是否为成员"""
        return user_id in self.members
        
    def update_activity(self) -> None:
        """更新活跃时间"""
        self.last_active = datetime.now()
        
    def increment_message_count(self) -> None:
        """增加消息计数"""
        self.message_count += 1
        self.update_activity()

def generate_private_room_name(user_id1: str, user_id2: str) -> str:
    """生成私聊房间名称"""
    # 确保ID是字符串类型
    user_id1 = str(user_id1)
    user_id2 = str(user_id2)
    # 按数字大小排序
    room_users = sorted([user_id1, user_id2], key=lambda x: int(x))
    return f"private_{room_users[0]}_{room_users[1]}"

def is_private_room(room_name: str) -> bool:
    """检查是否为私聊房间"""
    try:
        return room_name.startswith('private_') and len(room_name.split('_')) == 3
    except Exception:
        return False

class RoomManager(IRoomManager):
    """房间管理器"""
    
    def __init__(self):
        self._rooms: Dict[str, Set[str]] = {}  # room_name -> Set[sid]
        self._sid_rooms: Dict[str, Set[str]] = {}  # sid -> Set[room_name]
        self._user_rooms: Dict[str, Set[str]] = {}  # user_id -> Set[room_name]
        
    async def join_room(self, sid: str, room: str) -> None:
        """加入房间"""
        if room not in self._rooms:
            self._rooms[room] = set()
        self._rooms[room].add(sid)
        
        if sid not in self._sid_rooms:
            self._sid_rooms[sid] = set()
        self._sid_rooms[sid].add(room)
        
    async def leave_room(self, sid: str, room: str) -> None:
        """离开房间"""
        if room in self._rooms:
            self._rooms[room].discard(sid)
            if not self._rooms[room]:
                del self._rooms[room]
                
        if sid in self._sid_rooms:
            self._sid_rooms[sid].discard(room)
            if not self._sid_rooms[sid]:
                del self._sid_rooms[sid]
                
    async def get_rooms(self, sid: str) -> Set[str]:
        """获取会话加入的所有房间"""
        return self._sid_rooms.get(sid, set())
        
    async def get_room_members(self, room: str) -> Set[str]:
        """获取房间中的所有会话"""
        return self._rooms.get(room, set())
        
    async def remove_sid(self, sid: str) -> None:
        """移除会话"""
        rooms = self._sid_rooms.get(sid, set()).copy()
        for room in rooms:
            await self.leave_room(sid, room)
            
    async def get_user_rooms(self, user_id: str) -> Set[str]:
        """获取用户加入的所有房间"""
        return self._user_rooms.get(user_id, set())

    def generate_room_name(self, user1_id: int, user2_id: int) -> str:
        """生成私聊房间名称
        按照房间命名规则生成私聊房间名称，确保两个用户ID按升序排列
        """
        user_ids = sorted([user1_id, user2_id])
        return f"private_{user_ids[0]}_{user_ids[1]}"

class PrivateRoomManager(RoomManager):
    """私聊房间管理器"""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not self._initialized:
            super().__init__()
            self._room_info: Dict[str, RoomInfo] = {}  # 房间名称 -> 房间信息
            self._user_rooms: Dict[str, Set[str]] = {}  # 用户ID -> 房间名称集合
            self._initialized = True
            
    def create_room(self, user_id1: str, user_id2: str) -> str:
        """创建私聊房间"""
        room_name = generate_private_room_name(user_id1, user_id2)
        
        if room_name not in self._room_info:
            self._room_info[room_name] = RoomInfo(
                name=room_name,
                members=set(),
                created_at=datetime.now(),
                last_active=datetime.now()
            )
            
        for user_id in (user_id1, user_id2):
            if user_id not in self._user_rooms:
                self._user_rooms[user_id] = set()
                
        lprint(f"创建私聊房间: {room_name}")
        return room_name
        
    async def join_room(self, sid: str, room: str) -> None:
        """加入私聊房间"""
        if not is_private_room(room):
            return
            
        await super().join_room(sid, room)
        
        # 更新房间信息
        if room in self._room_info:
            self._room_info[room].add_member(sid)
            
    async def leave_room(self, sid: str, room: str) -> None:
        """离开私聊房间"""
        await super().leave_room(sid, room)
        
        if room in self._room_info:
            self._room_info[room].remove_member(sid)
            
    async def get_rooms(self, sid: str) -> Set[str]:
        """获取会话加入的所有房间"""
        return await super().get_rooms(sid)
        
    async def get_room_members(self, room: str) -> Set[str]:
        """获取房间中的所有会话"""
        return await super().get_room_members(room)
        
    async def remove_sid(self, sid: str) -> None:
        """移除会话"""
        await super().remove_sid(sid)
        
    def get_room_info(self, room_name: str) -> Optional[RoomInfo]:
        """获取房间信息"""
        return self._room_info.get(room_name)
        
    def record_message(self, room_name: str) -> None:
        """记录新消息"""
        if room_name in self._room_info:
            self._room_info[room_name].increment_message_count()
            
    async def get_user_rooms(self, user_id: str) -> Set[str]:
        """获取用户加入的所有私聊房间"""
        return self._user_rooms.get(user_id, set()) 