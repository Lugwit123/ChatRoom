"""
消息模块门面
提供消息相关功能的统一访问接口，包括消息发送、接收、查询等功能
"""
import Lugwit_Module as LM
from typing import List, Optional, Dict, Union, Sequence
import socketio
from datetime import datetime, timedelta
import zoneinfo
import traceback
import asyncio
from sqlalchemy import select, or_

from app.domain.message.facade.dto.message_dto import (
    MessageCreateDTO, 
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
from app.domain.common.models.tables import BaseMessage, PrivateMessage
from app.core.exceptions import BusinessError
from app.domain.message.internal.repository.private import PrivateMessageRepository
from app.domain.message.internal.repository.group import GroupMessageRepository
from app.domain.group.internal.repository.group_repository import GroupRepository
from app.domain.user.internal.repository import UserRepository
from app.domain.common.enums.message import MessageContentType, MessageType, MessageTargetType

class MessageFacade(BaseFacade):
    """消息门面类,处理所有消息相关操作"""
    
    def __init__(self):
        """初始化消息门面"""
        super().__init__(need_websocket=True)
        self._private_repo: Optional[PrivateMessageRepository] = None
        self._group_repo: Optional[GroupMessageRepository] = None
        self._group_repository: Optional[GroupRepository] = None
        self._user_repository: Optional[UserRepository] = None
        self._websocket_facade = WebSocketFacade()  # 使用单例
        
    @property
    def private_repo(self) -> PrivateMessageRepository:
        """延迟加载私聊消息仓储"""
        if self._private_repo is None:
            self._private_repo = PrivateMessageRepository()
        return self._private_repo
    
    @property
    def group_repo(self) -> GroupMessageRepository:
        """延迟加载群组消息仓储"""
        if self._group_repo is None:
            self._group_repo = GroupMessageRepository()
        return self._group_repo
    
    @property
    def group_repository(self) -> GroupRepository:
        """延迟加载群组仓储"""
        if self._group_repository is None:
            self._group_repository = GroupRepository()
        return self._group_repository
    
    @property
    def user_repository(self) -> UserRepository:
        """延迟加载用户仓储"""
        if self._user_repository is None:
            self._user_repository = UserRepository()
        return self._user_repository

    @property
    def sio(self) -> Optional[socketio.AsyncServer]:
        """获取Socket.IO服务器实例"""
        return self._websocket_facade.sio

    async def register_handlers(self):
        """注册消息处理器的事件处理函数"""
        self.lprint("注册消息处理器事件")
        if self.sio:
            self.sio.on("message", self.handle_message)
            self.sio.on("read_message", self.handle_read_message)
            self.lprint("消息处理器事件注册完成")
        else:
            self.lprint("Socket.IO服务器未初始化,无法注册事件处理器")

    async def send(self, message: BaseMessage) -> Optional[BaseMessage]:
        """保存消息到数据库
        
        Args:
            message: 消息实体
            
        Returns:
            Optional[BaseMessage]: 保存成功的消息，失败返回None
        """
        try:
            if message.group_id is not None:
                self.lprint(f"保存群组消息: {message.content} 到群组 {message.group_id}")
                return await self.group_repo.save_message(message)
            else:
                self.lprint(f"保存私聊消息: {message.content} 到用户 {message.recipient_id}")
                return await self.private_repo.save_message(message)
        except Exception as e:
            self.lprint(f"保存消息失败: {str(e)}")
            self.lprint(traceback.format_exc())
            return None

    async def save_message_to_db(self, data: dict) -> Optional[BaseMessage]:
        """保存消息到数据库
        
        Args:
            data: 消息数据
            
        Returns:
            Optional[BaseMessage]: 保存的消息对象，如果失败则返回None
        """
        try:
            # 获取发送者ID
            sender_id = data.get("sender_id")
            if not sender_id:
                self.lprint("消息缺少发送者ID")
                return None

            # 确定消息类型
            group_id = data.get("group_id")
            is_group_message = group_id is not None
            
            # 验证枚举值
            try:
                content_type = int(data.get("content_type", 0))
                message_type = int(data.get("message_type", 0))
                target_type = int(data.get("target_type", 0))
                
                # 验证枚举值是否合法
                if content_type not in [e.value for e in MessageContentType]:
                    self.lprint(f"无效的content_type值: {content_type}")
                    return None
                    
                if message_type not in [e.value for e in MessageType]:
                    self.lprint(f"无效的message_type值: {message_type}")
                    return None
                    
                if target_type not in [e.value for e in MessageTargetType]:
                    self.lprint(f"无效的target_type值: {target_type}")
                    return None
                    
            except (TypeError, ValueError) as e:
                self.lprint(f"类型字段转换失败: {str(e)}")
                return None
                
            # 创建消息实体
            message_data = {
                "sender_id": int(sender_id),
                "content": data.get("content", ""),
                "content_type": content_type,
                "message_type": message_type,
                "target_type": target_type,
                "status": data.get("status", ["unread"])
            }
            
            if is_group_message:
                # 群聊消息
                message_data["group_id"] = int(group_id)
                message = await self.group_repo.save_message(message_data)
                self.lprint(f"群聊消息保存成功: {message}")
            else:
                # 私聊消息
                recipient_username = data.get("recipient_id")
                if not recipient_username:
                    self.lprint("私聊消息缺少接收者ID")
                    return None
                    
                # 通过用户名查找用户ID
                recipient = await self.user_repository.get_by_username(recipient_username)
                if not recipient:
                    self.lprint(f"找不到接收者: {recipient_username}")
                    return None
                    
                message_data["recipient_id"] = recipient.id
                message = await self.private_repo.save_message(message_data)
                self.lprint(f"私聊消息保存成功: {message}")
            
            return message
            
        except Exception as e:
            self.lprint(f"保存消息失败: {str(e)}")
            traceback.print_exc()
            return None

    async def send_message_via_socket(self, message: BaseMessage):
        """通过WebSocket发送消息
        
        Args:
            message: 消息对象
        """
        try:
            if not self.sio:
                self.lprint("Socket.IO服务器未初始化")
                return
                
            # 获取发送者信息
            sender = await self.user_repository.get_by_id(message.sender_id)
            if not sender:
                self.lprint(f"未找到发送者: id={message.sender_id}")
                return
            self.lprint(f"发送者信息: id={sender.id}, username={sender.username}")

            # 准备消息数据
            message_data = message.to_dict()
            message_data['sender_username'] = sender.username

            # 根据消息类型处理
            if message.group_id is not None:
                # 群聊消息
                group = await self.group_repository.get_by_id(message.group_id)
                if group:
                    message_data["group_name"] = group.name
                    self.lprint(f"群组信息: id={group.id}, name={group.name}")
                else:
                    self.lprint(f"未找到群组信息: group_id={message.group_id}")
                room = f"group_{message.group_id}"
                self.lprint(f"发送群组消息到房间: {room}")
            else:
                # 私聊消息
                recipient = await self.user_repository.get_by_id(message.recipient_id)
                if recipient:
                    self.lprint(f"接收者信息: id={recipient.id}, username={recipient.username}")
                    # 使用两个用户ID的组合作为房间名
                    user_ids = sorted([sender.id, recipient.id])
                    room = f"private_{user_ids[0]}_{user_ids[1]}"
                    self.lprint(f"发送私聊消息到房间: {room}")
                    
                    # 获取房间内的所有会话
                    if hasattr(self.sio, 'manager') and hasattr(self.sio.manager, 'rooms'):
                        room_sids = self.sio.manager.rooms.get(room, set())
                        self.lprint(f"房间 {room} 内的所有会话ID: {room_sids}")
                    
                    message_data['recipient_username'] = recipient.username
                    # 发送到组合房间
                    await self.sio.emit('message', message_data, room=room, namespace='/chat')
                    self.lprint(f"私聊消息已发送到房间: {room}, 消息内容: {message_data}")
                else:
                    self.lprint(f"未找到接收者信息: recipient_id={message.recipient_id}")
                
            self.lprint(f"消息发送成功确认已发送到客户端, message_id={message.id}")
        except Exception as e:
            self.lprint(f"发送消息失败: {str(e)}")
            self.lprint(traceback.format_exc())

    async def handle_message(self, message: BaseMessage):
        """处理消息
        
        Args:
            message: 要处理的消息
        """
        try:
            # 保存消息到数据库
            await self.send(message)
            
            # 通过WebSocket广播消息
            await self.send_message_via_socket(message)
            
            # 在/chat命名空间下发送消息
            if message.group_id is not None:
                room = f"group_{message.group_id}"
                await self.sio.emit("message", message.dict(), room=room, namespace='/chat')
            else:
                await self.sio.emit("message", message.dict(), room=f"private_{message.sender_id}_{message.recipient_id}", namespace='/chat')
                
        except Exception as e:
            self.lprint(f"处理消息失败: {str(e)}")
            self.lprint(traceback.format_exc())

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
            self.lprint(f"处理消息已读事件失败: {str(e)}")
            
    async def send_message(
        self,
        content: str,
        sender_username: str,
        recipient_username: Optional[str] = None,
        group_name: Optional[str] = None,
        reply_to_id: Optional[str] = None,
        content_type: str = "text",
        mentioned_users: List[str] = None
    ) -> ResponseDTO:
        """发送消息
        
        Args:
            content: 消息内容
            sender_username: 发送者用户名
            recipient_username: 接收者用户名(私聊)
            group_name: 群组名称(群聊)
            reply_to_id: 回复的消息ID
            content_type: 消息类型
            mentioned_users: @提到的用户列表
            
        Returns:
            ResponseDTO: 统一响应格式
        """
        try:
            self.lprint(f"开始处理消息: content={content}, sender={sender_username}, recipient={recipient_username}, group={group_name}")
            
            # 获取发送者ID
            sender = await self.user_repository.get_by_username(sender_username)
            if not sender:
                return ResponseDTO.error(message=f"发送者不存在: {sender_username}")
                
            # 创建基础消息对象
            message = BaseMessage(
                sender_id=sender.id,
                content=content,
                reply_to_id=reply_to_id
            )
            
            if recipient_username:
                # 私聊消息
                recipient = await self.user_repository.get_by_username(recipient_username)
                if not recipient:
                    return ResponseDTO.error(message=f"接收者不存在: {recipient_username}")
                message.recipient_id = recipient.id
                
            elif group_name:
                # 群聊消息
                group = await self.group_repository.get_by_name(group_name)
                if not group:
                    return ResponseDTO.error(message=f"群组不存在: {group_name}")
                message.group_id = group.id
                
                # 处理@提醒
                if mentioned_users:
                    mentioned_ids = []
                    for username in mentioned_users:
                        user = await self.user_repository.get_by_username(username)
                        if user:
                            mentioned_ids.append(str(user.id))
                    message.extra_data = {"mentioned_users": mentioned_ids}
            else:
                return ResponseDTO.error(message="必须指定接收者或群组")
                
            # 保存消息
            result = await self.send(message)
            self.lprint(f"消息保存结果: {result}")
            
            # 异步发送消息
            if result:
                asyncio.create_task(self.send_message_via_socket(result))
            
            # 构造响应
            if result.group_id is not None:
                response = ResponseDTO.success(data=GroupMessageDTO.from_db(result))
            else:
                response = ResponseDTO.success(data=PrivateMessageDTO.from_db(result))
                
            self.lprint(f"消息处理完成: {response}")
            return response
            
        except Exception as e:
            self.lprint(f"消息处理失败: {str(e)}")
            self.lprint(traceback.format_exc())
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
                self.lprint(f"获取群组 {group_id} 的消息")
                messages = await self.group_repo.get_messages(group_id)
                return [msg for msg in messages if isinstance(msg, BaseMessage)]
            else:
                self.lprint(f"获取用户 {user_id} 的私聊消息")
                messages = await self.private_repo.get_messages(user_id)
                return [msg.message for msg in messages if hasattr(msg, 'message')]
        except Exception as e:
            self.lprint(f"获取消息列表失败: {str(e)}")
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
            self.lprint(f"标记消息已读失败: {str(e)}")
            raise

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
            self.lprint(f"获取用户消息映射失败: {str(e)}")
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
            self.lprint(f"删除消息失败: {str(e)}")
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
            self.lprint(f"转发消息失败: {str(e)}")
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
            self.lprint(f"添加表情回应失败: {str(e)}")
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
            self.lprint(f"移除表情回应失败: {str(e)}")
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
            self.lprint(f"搜索消息失败: {str(e)}")
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
            self.lprint(f"获取未读消息数量失败: {str(e)}")
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
            self.lprint(f"获取聊天伙伴失败: {str(e)}")
            self.lprint(traceback.format_exc())
            return []
