"""
消息模块门面
提供消息相关功能的统一访问接口，包括消息发送、接收、查询等功能
"""
import Lugwit_Module as LM
from typing import List, Optional
import socketio

from app.domain.message.internal.services.message_service import MessageService
from app.domain.message.facade.dto.message_dto import MessageCreateDTO, MessageDTO
from app.domain.base.facade.dto.base_dto import ResponseDTO
from app.core.websocket.facade.websocket_facade import WebSocketFacade

class MessageFacade:
    """消息模块对外接口
    
    提供消息相关的所有功能访问点，包括：
    - 消息发送
    - 消息接收
    - 消息查询
    - 消息归档等
    """
    def __init__(self, websocket_facade: WebSocketFacade, sio: socketio.AsyncServer):
        """初始化消息门面
        
        Args:
            websocket_facade: WebSocket门面实例
            sio: Socket.IO服务器实例
        """
        self._message_service = MessageService()
        self._websocket_facade = websocket_facade
        self._sio = sio
        self.lprint = LM.lprint
        
    def register_handlers(self):
        """注册消息处理器的事件处理函数"""
        self._sio.on("message", self.handle_message)
        self._sio.on("read_message", self.handle_read_message)
        
    async def handle_message(self, sid: str, data: dict):
        """处理新消息事件
        
        Args:
            sid: 会话ID
            data: 消息数据
        """
        try:
            # 获取发送者ID
            sender_id = self._websocket_facade.get_user_id(sid)
            if not sender_id:
                return
                
            # 创建消息
            message = MessageCreateDTO(
                sender_id=sender_id,
                content=data.get("content"),
                group_id=data.get("group_id"),
                receiver_id=data.get("receiver_id")
            )
            
            # 发送消息
            result = await self.send_message(message)
            if result.success:
                # 通过WebSocket发送消息
                await self._websocket_facade.broadcast_message(result.data)
                
        except Exception as e:
            self.lprint(f"处理消息事件失败: {str(e)}")
            
    async def handle_read_message(self, sid: str, data: dict):
        """处理消息已读事件
        
        Args:
            sid: 会话ID
            data: 消息数据
        """
        try:
            # 获取用户ID
            user_id = self._websocket_facade.get_user_id(sid)
            if not user_id:
                return
                
            # 标记消息为已读
            message_id = data.get("message_id")
            if message_id:
                await self.mark_as_read(message_id, user_id)
                
        except Exception as e:
            self.lprint(f"处理消息已读事件失败: {str(e)}")
            
    async def send_message(self, message: MessageCreateDTO) -> ResponseDTO:
        """发送消息
        
        Args:
            message: 消息创建DTO对象
            
        Returns:
            ResponseDTO: 统一响应格式
        """
        try:
            result = await self._message_service.send(message.to_internal())
            return ResponseDTO.success(data=MessageDTO.from_internal(result))
        except Exception as e:
            self.lprint(f"发送消息失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
            
    async def get_messages(self, user_id: str, group_id: Optional[str] = None) -> ResponseDTO:
        """获取消息列表
        
        Args:
            user_id: 用户ID
            group_id: 群组ID，如果为None则获取私聊消息
            
        Returns:
            ResponseDTO: 包含消息列表的响应
        """
        try:
            messages = await self._message_service.get_messages(user_id, group_id)
            return ResponseDTO.success(data=[MessageDTO.from_internal(msg) for msg in messages])
        except Exception as e:
            self.lprint(f"获取消息列表失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
    
    async def mark_as_read(self, message_id: str, user_id: str) -> ResponseDTO:
        """标记消息为已读
        
        Args:
            message_id: 消息ID
            user_id: 用户ID
            
        Returns:
            ResponseDTO: 操作结果响应
        """
        try:
            result = await self._message_service.mark_as_read(message_id, user_id)
            return ResponseDTO.success(data=result)
        except Exception as e:
            self.lprint(f"标记消息已读失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
