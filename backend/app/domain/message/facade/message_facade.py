"""
消息模块门面
提供消息相关功能的统一访问接口，包括消息发送、接收、查询等功能
"""
import Lugwit_Module as LM
from ..internal.services.message_service import MessageService
from .dto.message_dto import MessageCreateDTO
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
            return ResponseDTO.success(data=result)
        except Exception as e:
            self.lprint(f"发送消息失败: {str(e)}")
            return ResponseDTO.error(message=str(e))
