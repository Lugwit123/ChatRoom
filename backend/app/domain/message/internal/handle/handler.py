"""
消息处理器模块
提供不同类型消息的处理逻辑
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, cast, Type, TypeVar
import traceback
import json
from datetime import datetime
import zoneinfo

import Lugwit_Module as LM
lprint = LM.lprint

from app.core.events.services import Services
from app.core.events.interfaces import EventType, MessageEvent
from app.core.websocket.facade.websocket_facade import WebSocketFacade
from app.domain.common.enums.message import (MessageDirection, MessageType, MessageTargetType, 
MessageContentType, MessageStatus, RemoteControlResponseStatus, RemoteControlResponse)
from app.domain.message.facade.dto.message_dto import (
    PrivateMessageCreateDTO,
    GroupMessageCreateDTO
)
from app.domain.common.models.tables import (
    BaseMessage, 
    PrivateMessage, 
    GroupMessage, 
    create_group_message_table,
    generate_public_id
)
from app.domain.message.internal.repository.private import PrivateMessageRepository
from app.domain.message.internal.repository.group import GroupMessageRepository
from app.core.services.service_core import get_websocket_facade,get_auth_facade,get_user_facade

# 定义返回类型
ReturnType = TypeVar('ReturnType', bound=BaseMessage)

# 获取 WebSocketFacade 实例


class MessageHandler(ABC):
    """消息处理器基类"""
    
    def __init__(self):
        self._private_repo = PrivateMessageRepository()
        self._group_repo = GroupMessageRepository()
        self.websocket_facade = get_websocket_facade()
        self.auth_facade = get_auth_facade()
        self.user_facade = get_user_facade()
    @property
    def namespace(self) -> str:
        """获取处理器的命名空间"""
        return '/chat/private'  # 默认命名空间
    
    @abstractmethod
    async def handle(self, data: Dict[str, Any], sid: str) -> Optional[BaseMessage]:
        """处理消息
        
        Args:
            data: 原始消息数据
            sid: 会话ID
            
        Returns:
            Optional[BaseMessage]: 处理后的消息对象，None表示处理失败
        """
        pass

class PrivateMessageHandler(MessageHandler):
    """私聊消息处理器"""
    
    def __init__(self):
        super().__init__()
        
    @property
    def namespace(self) -> str:
        return '/chat/private'
        
    async def handle(self, data: Dict[str, Any], sid: str) -> Optional[BaseMessage]:
        """处理私聊消息"""
        try:
            # 使用 _is_connected 方法检查会话ID
            if not await self.websocket_facade._is_connected(sid):
                lprint(f"无效的会话ID: sid={sid}")
                return None
                
            lprint(f"会话ID有效: {sid}")
            
            # 验证目标类型
            if data.get('target_type') != MessageTargetType.user.value:
                lprint("私聊消息必须是用户类型")
                return None
                
            # 准备消息数据
            now = datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai"))
            message_data = {
                'sender_id': data['sender_id'],
                'recipient_id': data['recipient_id'],
                'content': json.dumps(data['content']) if isinstance(data['content'], dict) else data['content'],
                'message_type': MessageType.chat.value,
                'content_type': data.get('content_type', MessageContentType.plain_text.value),
                'target_type': MessageTargetType.user.value,
                'status': [MessageStatus.unread.value],
                'public_id': generate_public_id("pm"),  # 生成私聊消息ID
                'created_at': now,
                'updated_at': now,
                'extra_data': data.get('extra_data', {})
            }
            
            # 创建消息DTO
            message_dto = PrivateMessageCreateDTO(**message_data)
            
            # 保存消息
            message = await self._private_repo.save_message(message_dto.model_dump(exclude_unset=True))
            
            if message is not None and getattr(message, 'id', None) is not None:
                await self._private_repo.session.commit()
                return message
            
            lprint("消息保存失败或未生成有效ID")
            return None
            
        except Exception as e:
            lprint(f"处理私聊消息失败: {str(e)}")
            traceback.print_exc()
            return None

class GroupMessageHandler(MessageHandler):
    """群聊消息处理器"""
    
    def __init__(self):
        super().__init__()
        
    @property
    def namespace(self) -> str:
        return '/chat/group'
        
    async def handle(self, data: Dict[str, Any], sid: str) -> Optional[BaseMessage]:
        """处理群聊消息"""
        try:
            # 使用 _is_connected 方法检查会话ID
            if not await self.websocket_facade._is_connected(sid):
                lprint(f"无效的会话ID: sid={sid}")
                return None
                
            lprint(f"会话ID有效: {sid}")
            
            # 验证目标类型
            if data.get('target_type') != MessageTargetType.group.value:
                lprint("群聊消息必须是群聊类型")
                return None
                
            # 准备消息数据
            now = datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai"))
            message_data = {
                'sender_id': data['sender_id'],
                'group_id': data['group_id'],
                'content': json.dumps(data['content']) if isinstance(data['content'], dict) else data['content'],
                'message_type': MessageType.chat.value,
                'content_type': data.get('content_type', MessageContentType.plain_text.value),
                'target_type': MessageTargetType.group.value,
                'status': [MessageStatus.unread.value],
                'public_id': generate_public_id("gm"),  # 生成群聊消息ID
                'created_at': now,
                'updated_at': now,
                'extra_data': data.get('extra_data', {}),
                'mentioned_users': data.get('mentioned_users', [])
            }
            
            # 创建消息DTO
            message_dto = GroupMessageCreateDTO(**message_data)
            
            # 保存消息
            message = await self._group_repo.save_message(message_dto.model_dump(exclude_unset=True))
            
            if message is not None and getattr(message, 'id', None) is not None:
                await self._group_repo.session.commit()
                return message
            
            lprint("消息保存失败或未生成有效ID")
            return None
            
        except Exception as e:
            lprint(f"处理群聊消息失败: {str(e)}")
            traceback.print_exc()
            return None

class RemoteControlMessageHandler(MessageHandler):
    """远程控制消息处理器"""
    
    def __init__(self):
        super().__init__()
    @property
    def namespace(self) -> str:
        return '/chat/private'  # 使用统一的私聊命名空间
        
    async def handle(self, data: Dict[str, Any], sid: str) -> Optional[BaseMessage]:
        """处理远程控制消息"""
        try:
            # 使用 _is_connected 方法检查会话ID
            if not await self.websocket_facade._is_connected(sid):
                lprint(f"无效的会话ID: sid={sid}")
                return None
                
            lprint(f"会话ID有效: {sid},{data}")
            
            # 验证消息类型
            if data.get('message_type') != MessageType.remote_control.value:
                lprint("消息类型必须是远程控制")
                return None
                
            # 准备消息数据
            now = datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai"))
            
            # 从websocket连接中获取用户IP
            user_ip = await self.websocket_facade.get_client_ip(sid)
            user = await self.user_facade.get_user_by_id(data['sender_id'])
            
            # 将状态映射到 RemoteControlResponseStatus
            response_status = None
            message_id = -1  # 默认为-1表示新消息
            if data.get('content',{}).get("status") == "wait_server_return_message_id":
                response_status = RemoteControlResponseStatus.wait_server_return_message_id
            elif data.get('content',{}).get("status") == "rejected":
                response_status = RemoteControlResponseStatus.rejected
                reference_id = data.get("reference_id")
                if reference_id:
                    message_id = reference_id
                    lprint(f"使用reference_id作为message_id: {message_id}")
            elif data.get('content',{}).get("status") == "accepted":
                response_status = RemoteControlResponseStatus.accepted
                reference_id = data.get("reference_id")
                if reference_id:
                    message_id = reference_id
                    lprint(f"使用reference_id作为message_id: {message_id}")
            
            reason = data.get('content',{}).get("reason", "")

            # 创建 RemoteControlResponse 对象
            response = RemoteControlResponse(
                status=response_status,
                reason=reason,
                nickname=user.nickname,
                ip=user_ip
            )
            
            # 转换为字典格式
            content = response.to_dict()

            # 构建消息数据
            message_data = {
                'id': int(message_id),
                'sender_id': data['sender_id'],
                'recipient_id': data['recipient_id'],
                'content': json.dumps(content),
                'message_type': MessageType.remote_control.value,
                'target_type': MessageTargetType.user.value,
                'status': [MessageStatus.sent.value],  # 使用列表形式
                'direction': MessageDirection.response.value,  # 使用字符串值
                'content_type': MessageContentType.plain_text.value,
                'extra_data': data.get('extra_data', {})
            }
            
            # 记录消息数据
            lprint(f"远程控制消息数据: {message_data}")
            
            # 创建消息DTO
            message_dto = PrivateMessageCreateDTO(**message_data)
            
            # 保存消息，使用exclude_unset=True忽略未设置的字段
            message = await self._private_repo.save_message(message_dto.model_dump(exclude_unset=True))
            lprint(message)
            message_dto.id=int(message.id)
            message_dto.direction=MessageDirection.request.value
            message_dto.sender_id=message.sender_id    
            message_dto.recipient_id=message.recipient_id  
            message_dto.direction=MessageDirection.request.value
            message_dto.sender_username=(await self.user_facade.get_user_by_id(message.sender_id)).username
            message_dto.recipient_username=(await self.user_facade.get_user_by_id(message.recipient_id)).username
            # 设置created_at字段，避免在message_facade.py中调用isoformat()时出错
            message_dto.created_at = message.created_at if hasattr(message, 'created_at') else now
            return message_dto
            
            lprint("消息保存失败或未生成有效ID")
            return None
            
        except Exception as e:
            lprint(f"处理远程控制消息失败: {str(e)}")
            traceback.print_exc()
            return None
