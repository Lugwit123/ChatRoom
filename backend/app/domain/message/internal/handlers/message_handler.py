"""
消息WebSocket处理器
处理实时消息的发送和接收
"""
import json
import Lugwit_Module as LM
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime
from ...facade.dto.message_dto import MessageDTO
from ..services.message_service import MessageService

class MessageHandler:
    """消息WebSocket处理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.message_service = MessageService()
        self.lprint = LM.lprint
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """处理WebSocket连接
        
        Args:
            websocket: WebSocket连接
            user_id: 用户ID
        """
        try:
            await websocket.accept()
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            self.lprint(f"用户 {user_id} WebSocket连接成功")
        except Exception as e:
            self.lprint(f"WebSocket连接失败: {str(e)}")
            raise
            
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """处理WebSocket断开连接
        
        Args:
            websocket: WebSocket连接
            user_id: 用户ID
        """
        try:
            if user_id in self.active_connections:
                self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            self.lprint(f"用户 {user_id} WebSocket断开连接")
        except Exception as e:
            self.lprint(f"WebSocket断开连接失败: {str(e)}")
            
    async def broadcast_to_group(self, group_id: str, message: dict):
        """向群组广播消息
        
        Args:
            group_id: 群组ID
            message: 消息内容
        """
        # TODO: 获取群组成员列表
        group_members = await self._get_group_members(group_id)
        for member_id in group_members:
            await self.send_to_user(member_id, message)
            
    async def send_to_user(self, user_id: str, message: dict):
        """向指定用户发送消息
        
        Args:
            user_id: 用户ID
            message: 消息内容
        """
        if user_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    self.lprint(f"发送消息到用户 {user_id} 失败: {str(e)}")
                    disconnected.add(websocket)
            
            # 清理断开的连接
            for websocket in disconnected:
                await self.disconnect(websocket, user_id)
                
    async def _get_group_members(self, group_id: str) -> Set[str]:
        """获取群组成员列表
        
        Args:
            group_id: 群组ID
            
        Returns:
            Set[str]: 群组成员ID集合
        """
        # TODO: 实现从群组服务获取成员列表
        return set()  # 临时返回空集合
        
    async def handle_message(self, websocket: WebSocket, user_id: str):
        """处理接收到的消息
        
        Args:
            websocket: WebSocket连接
            user_id: 用户ID
        """
        try:
            while True:
                data = await websocket.receive_json()
                message = await self.message_service.send(data)
                message_dto = MessageDTO.from_internal(message)
                
                if message.group_id:
                    # 群组消息
                    await self.broadcast_to_group(message.group_id, message_dto.dict())
                else:
                    # 私聊消息
                    await self.send_to_user(message.receiver_id, message_dto.dict())
                    # 同时发送给发送者
                    await self.send_to_user(user_id, message_dto.dict())
                    
        except Exception as e:
            self.lprint(f"处理消息失败: {str(e)}")
            await self.disconnect(websocket, user_id)
