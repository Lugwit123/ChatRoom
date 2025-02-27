"""
消息模块门面
提供消息相关功能的统一访问接口，包括消息发送、接收、查询等功能
"""
import json
import Lugwit_Module as LM
from typing import List, Optional, Dict, Union, Sequence, Any
import socketio
from datetime import datetime, timedelta
import zoneinfo
import traceback
import asyncio
from sqlalchemy import select, or_

from app.domain.message.facade.dto.message_dto import (
    PrivateMessageCreateDTO,
    GroupMessageCreateDTO,
    PrivateMessageDTO,
    GroupMessageDTO,
    PrivateMessageExportDTO,
    PrivateMessageBackupDTO,
    PrivateMessageRestoreDTO,
    PrivateMessageRecallDTO,
    PrivateMessageCleanDTO,
    MessageResponse,
    MessageListResponse,
    MessageSearchResponse
)
from app.domain.base.facade.dto.base_dto import ResponseDTO
from app.domain.base.facade.base_facade import BaseFacade
from app.core.websocket.facade.websocket_facade import WebSocketFacade
from app.domain.common.models.tables import (
    BaseMessage, 
    PrivateMessage, 
    create_group_message_table,
    generate_public_id
)
from app.core.exceptions import BusinessError
from app.domain.message.internal.repository.private import PrivateMessageRepository
from app.domain.message.internal.repository.group import GroupMessageRepository
from app.domain.group.internal.repository.group_repository import GroupRepository
from app.domain.user.internal.repository import UserRepository
from app.domain.common.enums.message import MessageContentType, MessageType, MessageTargetType, MessageStatus
from app.core.di.container import get_container
from app.core.di.container import Container
from app.core.services.service_core import  get_websocket_facade,get_user_facade
from app.domain.common.models.tables import User
from app.domain.message.internal.handle.handler import (
    PrivateMessageHandler, GroupMessageHandler, RemoteControlMessageHandler
)

from app.core.websocket.internal.manager.private_room_manager import PrivateRoomManager

lprint = LM.lprint

class MessageFacade(BaseFacade):
    """消息门面类,处理所有消息相关操作"""
    
    def __init__(self):
        """初始化消息门面"""
        super().__init__(need_websocket=True)
        self._private_repo = PrivateMessageRepository()
        self._group_repo = GroupMessageRepository()
        # 从 service_core 获取 WebSocketFacade
        self._websocket_facade = get_websocket_facade()
        # 获取用户服务
        self._user_facade = get_user_facade()
        self._room_manager = PrivateRoomManager()
        
        # 直接初始化处理器
        self._handlers = {MessageTargetType.user:{
                MessageType.chat: PrivateMessageHandler(),
                MessageType.remote_control: RemoteControlMessageHandler(),
            },
            MessageTargetType.group:{
                MessageType.chat: GroupMessageHandler(),
                MessageType.remote_control: RemoteControlMessageHandler(),
            }
        }
        
    def get_handler(self,target_type:MessageTargetType,message_type:MessageType):
        return self._handlers.get(target_type,{}).get(message_type)
    
    @property
    def private_repo(self) -> PrivateMessageRepository:
        """获取私聊消息仓储"""
        return self._private_repo
    
    @property
    def group_repo(self) -> GroupMessageRepository:
        """获取群组消息仓储"""
        return self._group_repo

    @property
    def sio(self) -> Optional[socketio.AsyncServer]:
        """获取Socket.IO服务器实例"""
        return self._websocket_facade.sio

    async def register_handlers(self):
        """注册消息处理器的事件处理函数"""
        try:
            if not isinstance(self.sio, socketio.AsyncServer):
                lprint("Socket.IO服务器未初始化或类型不正确")
                return

            # 定义消息处理器
            async def message_handler(sid: str, data: dict):
                """处理消息事件"""
                try:
                    lprint(f"收到消息: {data}")
                    # 从消息数据中获取命名空间
                    namespace = data.get('namespace', '/chat/private')
                    
                    # 如果消息中缺少发送者或接收者ID，尝试从会话中获取
                    if not data.get('sender_id'):
                        # 从连接管理器中获取用户ID
                        user_id = self._websocket_facade._connection_manager.get_user_id_by_sid(sid)
                        if user_id:
                            data['sender_id'] = int(user_id)
                            lprint(f"从会话中获取发送者ID: {data['sender_id']}")
                    
                    # 如果是私聊消息且缺少接收者ID，尝试从消息内容中获取
                    if namespace == '/chat/private' and not data.get('recipient_id'):
                        # 尝试从消息内容中获取接收者用户名
                        recipient_username = data.get('recipient_username')
                        if recipient_username:
                            # 通过用户名获取用户ID
                            recipient = await self._user_facade.get_user_by_username(recipient_username)
                            if recipient:
                                data['recipient_id'] = recipient.id
                                lprint(f"从用户名获取接收者ID: {data['recipient_id']}")
                    
                    message = await self.handle_socket_message(data, sid, namespace)
                    if message:
                        # 返回消息处理结果
                        return {
                            "status": "success",
                            "message_id": message.id,
                            "public_id": message.public_id,
                            "timestamp": message.created_at.isoformat()
                        }
                    lprint(message)
                    return {"status": "error", "message": "消息处理失败"}
                except Exception as e:
                    lprint(f"处理消息失败: {str(e)}")
                    traceback.print_exc()
                    return {"status": "error", "message": str(e)}

            async def read_message_handler(sid: str, data: dict):
                await self.handle_read_message(sid, data)

            # 注册消息处理器
            for namespace in ['/chat/private', '/chat/group', '/chat/private/system']:
                self.sio.on("message", message_handler, namespace=namespace)
                # 为私聊和群聊注册read_message事件
                if namespace in ['/chat/private', '/chat/group']:
                    self.sio.on("read_message", read_message_handler, namespace=namespace)

            lprint("消息处理器注册完成")

        except Exception as e:
            lprint(f"注册消息处理器失败: {str(e)}")
            traceback.print_exc()

            
    def _get_message_namespace(self, message: Union[PrivateMessage, BaseMessage]) -> str:
        """获取消息的命名空间
        
        Args:
            message: 消息对象
            
        Returns:
            str: 命名空间
        """
        # 根据消息目标类型确定命名空间
        if hasattr(message, 'target_type'):
            target_type = int(str(message.target_type))  # 转换为整数进行比较
            if target_type == MessageTargetType.user.value:
                return '/chat/private'
            elif target_type == MessageTargetType.group.value:
                return '/chat/group'
        return '/chat/private/system'

    async def send_message_via_socket(self, message: Union[PrivateMessageDTO, BaseMessage], namespace: str = '/chat/private'):
        """通过WebSocket发送消息
        
        Args:
            message: 消息对象
            namespace: 命名空间
        """
        try:
            lprint(f"开始处理发送的消息{message}")
            # 将消息对象转换为可序列化的字典
            if hasattr(message, 'to_dict'):
                message_data = message.to_dict()
            else:
                message_data = message.model_dump()

            # 获取发送者和接收者信息
            sender = await self._user_facade.get_user_by_id(int(str(message_data.get('sender_id'))))
            recipient = None
            if message_data.get('recipient_id'):
                recipient = await self._user_facade.get_user_by_id(int(str(message_data.get('recipient_id'))))
                recipient = recipient.to_dict()
            sender=sender.to_dict()
            lprint(sender)
            # 根据消息类型处理房间
            if message_data.get('target_type') == MessageTargetType.group.value:
                group_id = message_data.get('group_id')
                if group_id:
                    room = f"group_{group_id}"
                    lprint(f"发送群组消息: {message_data},消息房间: {room}")
                    await self.sio.emit('message', message_data, room=room, namespace=namespace)
                else:
                    lprint(f"未找到群组: group_id={message_data.get('group_id')}")
            elif message_data.get('target_type') == MessageTargetType.user.value:
                if recipient:
                    # 使用房间管理器生成房间名称
                    user_ids = ([int(str(sender['id'])), int(str(recipient['id']))])
                    room = self._room_manager.generate_room_name(user_ids[0], user_ids[1])
                    lprint(f"发送私聊消息: {message_data},消息房间: {room}")
                    await self.sio.emit('message', message_data, room=room, namespace=namespace)
                else:
                    lprint(f"未找到接收者: recipient_id={message_data.get('recipient_id')}")
            
            lprint(f"消息发送完成: message_id={message_data.get('id')}")
        except Exception as e:
            lprint(f"发送消息失败: {str(e)}")
            traceback.print_exc()

    async def handle_read_message(self, sid: str, data: dict):
        """处理消息已读事件
        
        Args:
            sid: 会话ID
            data: 消息数据
        """
        try:
            # 获取用户ID
            user_id = data.get("user_id")
            if not user_id:
                return
                
            # 标记消息为已读
            message_id = data.get("message_id")
            if message_id:
                await self.mark_as_read(int(message_id), int(user_id))
                
        except Exception as e:
            lprint(f"处理消息已读事件失败: {str(e)}")
            
    async def send_message(
        self,
        content: str,
        sender_username: str,
        recipient: Optional[str] = None,
        group_name: Optional[str] = None,
        reply_to_id: Optional[str] = None,
        content_type: str = "text",
        mentioned_users: Optional[List[str]] = None
    ) -> ResponseDTO:
        """发送消息"""
        try:
            lprint(f"开始处理消息: content={content}, sender={sender_username}, recipient={recipient}, group={group_name}")
            
            # 获取发送者信息
            sender = await self._user_facade.get_user_by_username(sender_username)
            if not sender:
                return ResponseDTO.error(message=f"发送者不存在: {sender_username}")

            # 根据目标类型创建对应的DTO
            if group_name:
                # 群聊消息
                group = await self._get_group_by_name(group_name)
                if not group:
                    return ResponseDTO.error(message=f"群组不存在: {group_name}")
                    
                # 获取被@用户的ID列表
                mentioned_ids = []
                if mentioned_users:
                    for username in mentioned_users:
                        user = await self._user_facade.get_user_by_username(username)
                        if user:
                            mentioned_ids.append(int(user.get('id', 0)))
                            
                message_dto = GroupMessageCreateDTO(
                    sender_id=int(sender.get('id', 0)),
                    content=content,
                    message_type=MessageType.chat.value,
                    content_type=MessageContentType.plain_text.value,
                    group_id=int(group.get('id', 0)),
                    mentioned_users=mentioned_ids
                )
                result = await self.save_group_message(message_dto)
                
            elif recipient:
                # 私聊消息
                recipient_info = await self._user_facade.get_user_by_username(recipient)
                if not recipient_info:
                    return ResponseDTO.error(message=f"接收者不存在: {recipient}")
                    
                message_dto = PrivateMessageCreateDTO(
                    sender_id=int(sender.get('id', 0)),
                    content=content,
                    message_type=MessageType.chat.value,
                    content_type=MessageContentType.plain_text.value,
                    recipient_id=int(recipient_info.get('id', 0))
                )
                result = await self.save_private_message(message_dto)
                
            else:
                return ResponseDTO.error(message="必须指定接收者或群组")
                
            if not result:
                return ResponseDTO.error(message="消息发送失败")
                
            # 异步发送消息
            asyncio.create_task(self.send_message_via_socket(result))
            
            # 构造响应
            if hasattr(result, 'group_id') and result.group_id is not None:
                response = ResponseDTO.success(data=GroupMessageDTO.from_db(result))
            else:
                response = ResponseDTO.success(data=PrivateMessageDTO.from_db(result))
                
            lprint(f"消息处理完成: {response}")
            return response
            
        except Exception as e:
            lprint(f"消息处理失败: {str(e)}")
            traceback.print_exc()
            return ResponseDTO.error(message=str(e))

    async def get_messages(
        self,
        user_id: int,
        group_id: Optional[int] = None,
        limit: int = 20
    ) -> Sequence[BaseMessage]:
        """获取消息列表
        
        Args:
            user_id: 用户ID
            group_id: 群组ID,如果为None则获取私聊消息
            limit: 返回结果数量限制
            
        Returns:
            Sequence[BaseMessage]: 消息列表
        """
        try:
            if group_id is not None:
                lprint(f"获取群组 {group_id} 的消息")
                messages = await self.group_repo.get_messages(group_id)
                return [msg for msg in messages if isinstance(msg, BaseMessage)]
            else:
                lprint(f"获取用户 {user_id} 的私聊消息")
                messages = await self.private_repo.get_messages(user_id)
                return [msg.message for msg in messages if hasattr(msg, 'message')]
        except Exception as e:
            lprint(f"获取消息列表失败: {str(e)}")
            raise

    async def mark_as_read(self, message_id: int, user_id: int) -> bool:
        """标记消息为已读
        
        Args:
            message_id: 消息ID
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        try:
            # 先尝试标记私聊消息
            if await self.private_repo.mark_as_read(message_id):
                return True
            # 如果不是私聊消息，尝试标记群组消息
            return await self.group_repo.mark_as_read(message_id)
        except Exception as e:
            lprint(f"标记消息已读失败: {str(e)}")
            raise

    async def mark_as_unread(self, message_id: int) -> bool:
        """标记消息为未读
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否成功
        """
        try:
            # 先尝试标记私聊消息
            if await self.private_repo.mark_as_unread(message_id):
                return True
            # 如果不是私聊消息，尝试标记群组消息
            return await self.group_repo.mark_as_unread(message_id)
        except Exception as e:
            lprint(f"标记消息未读失败: {str(e)}")
            traceback.print_exc()
            return False

    async def get_user_messages_map(self, user_id: int) -> Dict[str, List[Union[PrivateMessageDTO, GroupMessageDTO]]]:
        """获取用户的消息映射
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, List[Union[PrivateMessageDTO, GroupMessageDTO]]]: 用户名到消息列表的映射
        """
        try:
            # 获取用户的所有私聊消息
            messages = await self.private_repo.get_messages(
                user_id=user_id,
                limit=100  # 限制消息数量
            )
            
            # 按照对方用户名分组
            messages_map = {}
            for msg_with_usernames in messages:
                other_username = msg_with_usernames.other_username
                if other_username not in messages_map:
                    messages_map[other_username] = []
                # 将 PrivateMessage 转换为字典
                message_dict = msg_with_usernames.message.__dict__
                message_dict.pop('_sa_instance_state', None)  # 移除 SQLAlchemy 的内部状态
                
                # 转换字段类型
                message_dict['id'] = str(message_dict['id'])
                message_dict['sender_id'] = str(message_dict['sender_id'])
                message_dict['recipient_id'] = str(message_dict['recipient_id'])
                if message_dict.get('read_at') is None:
                    message_dict['read_at'] = datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai"))
                
                messages_map[other_username].append(PrivateMessageDTO.model_validate(message_dict))

            return messages_map
            
        except Exception as e:
            lprint(f"获取用户消息映射失败: {str(e)}")
            traceback.print_exc()
            return {}

    async def delete_message(self, message_id: str, user_id: int, delete_for_all: bool = False) -> bool:
        """删除消息
        
        Args:
            message_id: 消息ID
            user_id: 用户ID
            delete_for_all: 是否为所有人删除
            
        Returns:
            bool: 是否成功
        """
        try:
            # TODO: 实现消息删除逻辑
            return True
        except Exception as e:
            lprint(f"删除消息失败: {str(e)}")
            return False
            
    async def forward_messages(
        self,
        message_ids: List[str],
        target_type: str,
        target_id: str,
        user_id: int
    ) -> bool:
        """转发消息
        
        Args:
            message_ids: 消息ID列表
            target_type: 目标类型(private/group)
            target_id: 目标ID
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        try:
            # TODO: 实现消息转发逻辑
            return True
        except Exception as e:
            lprint(f"转发消息失败: {str(e)}")
            return False
            
    async def add_reaction(self, message_id: str, emoji: str, user_id: int) -> bool:
        """添加表情回应
        
        Args:
            message_id: 消息ID
            emoji: 表情符号
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        try:
            # TODO: 实现添加表情回应逻辑
            return True
        except Exception as e:
            lprint(f"添加表情回应失败: {str(e)}")
            return False
            
    async def remove_reaction(self, message_id: str, emoji: str, user_id: int) -> bool:
        """移除表情回应
        
        Args:
            message_id: 消息ID
            emoji: 表情符号
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        try:
            # TODO: 实现移除表情回应逻辑
            return True
        except Exception as e:
            lprint(f"移除表情回应失败: {str(e)}")
            return False
            
    async def search_messages(
        self,
        query: str,
        user_id: int,
        chat_with: Optional[str] = None,
        group_id: Optional[str] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        limit: int = 20
    ) -> MessageSearchResponse:
        """搜索消息
        
        Args:
            query: 搜索关键词
            user_id: 用户ID
            chat_with: 在指定私聊中搜索
            group_id: 在指定群组中搜索
            before: 此消息之前
            after: 此消息之后
            limit: 返回结果数量限制
            
        Returns:
            MessageSearchResponse: 搜索结果
        """
        try:
            # TODO: 实现消息搜索逻辑
            return MessageSearchResponse(
                messages=[],
                total=0,
                has_more=False
            )
        except Exception as e:
            lprint(f"搜索消息失败: {str(e)}")
            raise
            
    async def get_unread_count(self, user_id: int) -> int:
        """获取未读消息数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 未读消息数量
        """
        try:
            # TODO: 实现获取未读消息数量逻辑
            return 0
        except Exception as e:
            lprint(f"获取未读消息数量失败: {str(e)}")
            return 0

    async def get_chat_partners(self, user_id: int) -> List[int]:
        """获取用户的所有聊天伙伴ID
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[int]: 聊天伙伴ID列表
        """
        try:
            # 使用仓储层的方法获取聊天伙伴
            return await self.private_repo.get_chat_partners(user_id)
                
        except Exception as e:
            lprint(f"获取聊天伙伴失败: {str(e)}")
            traceback.print_exc()
            return []

    async def handle_open_path(self, data: dict) -> None:
        """处理打开路径消息
        
        Args:
            data: 消息数据
        """
        try:
            # 获取消息内容
            content = data.get('content', {})
            if not isinstance(content, dict):
                lprint(f"无效的打开路径消息内容: {content}")
                return
                
            # 获取路径
            local_path = content.get('localPath')
            if not local_path:
                lprint("打开路径消息缺少路径参数")
                return
                
            lprint(f"处理打开路径消息: path={local_path}")
            
        except Exception as e:
            lprint(f"处理打开路径消息失败: {str(e)}")
            traceback.print_exc()

    async def save_private_message(self, message_dto: PrivateMessageCreateDTO) -> Optional[PrivateMessage]:
        """保存私聊消息"""
        try:
            # 验证发送者和接收者
            sender = await self._user_facade.get_user_by_id(message_dto.sender_id)
            if not sender:
                lprint(f"发送者不存在: {message_dto.sender_id}")
                return None
                
            recipient = await self._user_facade.get_user_by_id(message_dto.recipient_id)
            if not recipient:
                lprint(f"接收者不存在: {message_dto.recipient_id}")
                return None
                
            # 补充消息数据
            message_data = message_dto.to_db_dict()
            message_data.update({
                "public_id": generate_public_id("pm"),  # 生成私聊消息ID
                "created_at": datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai")),
                "updated_at": datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai"))
            })
            
            # 保存消息
            return await self.private_repo.save_message(message_data)
            
        except Exception as e:
            lprint(f"保存私聊消息失败: {str(e)}")
            traceback.print_exc()
            return None
            
    async def save_group_message(self, message_dto: GroupMessageCreateDTO) -> Optional[BaseMessage]:
        """保存群聊消息"""
        try:
            # 验证发送者和群组
            sender = await self._user_facade.get_user_by_id(message_dto.sender_id)
            if not sender:
                lprint(f"发送者不存在: {message_dto.sender_id}")
                return None
                
            group = await self._get_group(message_dto.group_id)
            if not group:
                lprint(f"群组不存在: {message_dto.group_id}")
                return None
                
            # 检查发送者是否是群成员
            is_member = await self._check_group_member(message_dto.group_id, message_dto.sender_id)
            if not is_member:
                lprint(f"发送者不是群成员: sender_id={message_dto.sender_id}, group_id={message_dto.group_id}")
                return None
                
            # 补充消息数据
            message_data = message_dto.to_db_dict()
            message_data.update({
                "public_id": generate_public_id("gm"),  # 生成群聊消息ID
                "created_at": datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai")),
                "updated_at": datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai"))
            })
            
            # 保存消息
            return await self.group_repo.save_message(message_data)
            
        except Exception as e:
            lprint(f"保存群聊消息失败: {str(e)}")
            traceback.print_exc()
            return None

    async def _get_group_by_name(self, group_name: str) -> Optional[Dict[str, Any]]:
        """通过群组名称获取群组信息"""
        return await self._user_facade.get_group_by_name(group_name)

    async def _check_group_member(self, group_id: int, user_id: int) -> bool:
        """通过用户服务检查用户是否是群组成员"""
        return await self._user_facade.check_group_member(group_id, user_id)

    async def handle_socket_message(self, data: Dict[str, Any], sid: str, namespace: str = '/chat/private') -> Optional[BaseMessage]:
        """处理WebSocket消息"""
        try:
            # 1. 获取发送者ID
            lprint(f"开始处理WebSocket消息: {data}")
            user_id = await self._websocket_facade.get_user_id_by_sid(sid)
            if not user_id:
                lprint(f"无法获取发送者ID, sid={sid}")
                return None
                
            # 2. 确保user_id是整数类型
            try:
                user_id = int(user_id)
            except (TypeError, ValueError):
                lprint(f"无效的用户ID格式: {user_id}")
                return None
                
            # 3. 添加发送者ID到消息数据
            data['sender_id'] = user_id
            
            # 4. 确保消息类型正确
            if 'message_type' not in data:
                data['message_type'] = MessageType.chat.value
            elif isinstance(data['message_type'], str):
                # 将字符串类型转换为枚举值
                message_type_map = {
                    'chat': MessageType.chat.value,
                    'remote_control': MessageType.remote_control.value,
                    'open_path': MessageType.open_path.value
                }
                data['message_type'] = message_type_map.get(data['message_type'], MessageType.chat.value)
            
            # 5. 设置目标类型
            data['target_type'] = MessageTargetType.user.value

            # 6. 根据命名空间设置消息类型和目标类型
            if 'private' in namespace:
                # 转换recipient为recipient_id
                if 'recipient_username' not in data:
                    lprint("缺少接收者信息")
                    return None
                    
                # 检查接收者信息是否已经是ID
                recipient_id = None
                if isinstance(data['recipient_username'], (int, str)):
                    if isinstance(data['recipient_username'], str) and not data['recipient_username'].isdigit():
                        # 如果是用户名，需要转换为ID
                        recipient = await self._user_facade.get_user_by_username(data['recipient_username'])
                        lprint(f"接收者recipient: {recipient}")
                        if not recipient:
                            lprint(f"接收者不存在: {data['recipient_username']}")
                            return None
                        recipient_id = recipient.id
                    else:
                        # 如果是ID，验证用户是否存在
                        try:
                            recipient_id = int(data['recipient_username'])
                            recipient = await self._user_facade.get_user_by_id(recipient_id)
                            if not recipient:
                                lprint(f"接收者不存在: ID={recipient_id}")
                                return None
                        except (ValueError, TypeError):
                            lprint(f"无效的接收者ID格式: {data['recipient_username']}")
                            return None
                else:
                    lprint(f"无效的接收者格式: {data['recipient_username']}")
                    return None
                    
                data['recipient_id'] = recipient_id
                lprint(f"接收者ID设置为: {recipient_id}")
                
            # 7. 获取对应消息类型的处理器
            handler = self.get_handler(MessageTargetType(data['target_type']),MessageType(data['message_type']))
            if not handler:
                lprint(f"未找到消息类型 {data['message_type']} 的处理器")
                return None
                
            # 8. 处理消息
            lprint(f"开始处理消息: {data},处理器是{handler}")
            message = await handler.handle(data, sid)
            await self.send_message_via_socket(message, namespace)
            return message
            
        except Exception as e:
            print(traceback.format_exc())
            print(f"处理消息失败: {str(e)}")
            return None
