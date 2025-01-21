"""
消息WebSocket处理器
处理实时消息的发送和接收
"""
import json
import Lugwit_Module as LM
from typing import Dict, Set
import socketio
from datetime import datetime
from app.domain.message.facade.dto.message_dto import MessageDTO
from app.domain.message.internal.services.message_service import MessageService
from app.core.websocket.manager import ConnectionManager

class MessageHandler:
    """消息WebSocket处理器"""
    
    def __init__(self, connection_manager: ConnectionManager, sio: socketio.AsyncServer):
        """初始化消息处理器
        
        Args:
            connection_manager: WebSocket连接管理器
            sio: Socket.IO服务器实例
        """
        self.message_service = MessageService()
        self.connection_manager = connection_manager
        self.sio = sio
        self.lprint = LM.lprint
        
    def register_handlers(self):
        """注册Socket.IO事件处理函数"""
        @self.sio.on('send_message')
        async def handle_message(sid: str, data: dict):
            """处理发送消息事件"""
            try:
                user_id = self.connection_manager.get_username_by_sid(sid)
                if not user_id:
                    self.lprint(f"未找到用户: {sid}")
                    return
                    
                await self.handle_message(data, user_id)
            except Exception as e:
                self.lprint(f"处理消息失败: {str(e)}")
                raise
                
    async def handle_message(self, data: dict, user_id: str):
        """处理接收到的消息
        
        Args:
            data: 消息数据
            user_id: 用户ID
        """
        try:
            message = await self.message_service.send(data)
            message_dto = MessageDTO.from_internal(message)
            
            if message.group_id:
                # 群组消息
                await self.connection_manager.emit_to_group(
                    message.group_id,
                    "new_message",
                    message_dto.dict()
                )
            else:
                # 私聊消息
                # 发送给接收者
                await self.connection_manager.emit(
                    "new_message",
                    message_dto.dict(),
                    to=message.receiver_id
                )
                # 同时发送给发送者
                await self.connection_manager.emit(
                    "new_message",
                    message_dto.dict(),
                    to=user_id
                )
                    
        except Exception as e:
            self.lprint(f"处理消息失败: {str(e)}")
            raise
