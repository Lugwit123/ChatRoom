"""
消息模块门面
提供消息相关功能的统一访问接口，包括消息发送、接收、查询等功能
"""
import Lugwit_Module as LM
from typing import List, Optional
from ..internal.services.message_service import MessageService
from .dto.message_dto import MessageCreateDTO, MessageDTO
from ...base.facade.dto.base_dto import ResponseDTO

class MessageFacade:
    """消息模块对外接口
    
    提供消息相关的所有功能访问点，包括：
    - 消息发送
    - 消息接收
    - 消息查询
    - 消息归档等
    """
    def __init__(self):
        self._message_service = MessageService()
        self.lprint = LM.lprint
        
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
