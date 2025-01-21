import traceback
from datetime import datetime
from typing import Dict, Optional, Any, Tuple

import socketio
from socketio.exceptions import SocketIOError

import Lugwit_Module as LM
from app.core.websocket.manager import ConnectionManager
from app.domain.group.repository import GroupRepository
from app.domain.message.models import PrivateMessage
from app.domain.message.enums import MessageType, MessageContentType, MessageStatus
from app.domain.message.repository.private import PrivateMessageRepository
from app.domain.message.repository.group import GroupMessageRepository

lprint = LM.lprint

class MessageHandlers:
    def __init__(
        self,
        sio: socketio.AsyncServer,
        connection_manager: ConnectionManager,
        private_repo: PrivateMessageRepository,
        group_repo: GroupMessageRepository,
        group_repository: GroupRepository,
    ):
        self.sio = sio
        self.connection_manager = connection_manager
        self.private_repo = private_repo
        self.group_repo = group_repo
        self.group_repository = group_repository

    def register_handlers(self):
        """注册所有消息处理器"""
        self.sio.on("message", self.handle_message)

    async def handle_message(self, sid: str, data: Dict):
        """统一处理消息事件"""
        try:
            # 获取发送者用户名
            sender = await self.connection_manager.get_user_by_sid(sid)
            if not sender:
                lprint(f"发送消息失败: 未找到发送者")
                return

            message_type = data.get("message_type")
            if message_type == MessageType.private_chat:
                await self._handle_private_message(sender, data)
            elif message_type == MessageType.group_chat:
                await self._handle_group_message(sender, data)
            else:
                lprint(f"未知的消息类型: {message_type}")

        except Exception as e:
            lprint(f"处理消息失败: {str(e)}")
            lprint(traceback.format_exc())

    async def _create_message(self, message_type: MessageType, data: Dict, sender: str) -> Optional[Tuple[Any, int]]:
        """创建消息对象并保存
        
        Args:
            message_type: 消息类型
            data: 消息数据
            sender: 发送者
            
        Returns:
            Tuple[Message, int]: 消息对象和消息ID
        """
        try:
            if message_type == MessageType.private_chat:
                message = PrivateMessage(
                    content=data["content"],
                    sender_id=sender,
                    recipient_id=data["recipient"],
                    content_type=MessageContentType.text,
                    status=MessageStatus.sent,
                    extra_data=data.get("extra_data", {})
                )
                message_id = await self.private_repo.save_message(message)
                return message, message_id
            else:  # MessageType.group_chat
                # 群组消息使用字典格式
                message_data = {
                    "content": data["content"],
                    "sender_id": sender,
                    "group_id": data["group_id"],
                    "content_type": MessageContentType.text,
                    "status": MessageStatus.sent,
                    "extra_data": data.get("extra_data", {})
                }
                message_id = await self.group_repo.save_message(message_data)
                return message_data, message_id

        except Exception as e:
            lprint(f"创建消息失败: {str(e)}")
            return None

    async def _send_message(self, message_type: MessageType, message: Any, message_id: int, 
                          recipient_sid: str, sender: str) -> bool:
        """发送消息
        
        Args:
            message_type: 消息类型
            message: 消息对象
            message_id: 消息ID
            recipient_sid: 接收者的会话ID
            sender: 发送者
            
        Returns:
            bool: 是否发送成功
        """
        try:
            message_data = {
                "id": message_id,
                "content": message["content"] if isinstance(message, dict) else message.content,
                "sender": sender,
                "message_type": message_type,
                "timestamp": datetime.now().isoformat(),
                "content_type": message["content_type"] if isinstance(message, dict) else message.content_type.value,
                "extra_data": message["extra_data"] if isinstance(message, dict) else message.extra_data
            }
            
            if message_type == MessageType.private_chat:
                message_data["recipient"] = message.recipient_id if not isinstance(message, dict) else message["recipient_id"]
            else:  # MessageType.group_chat
                message_data["group_id"] = message.group_id if not isinstance(message, dict) else message["group_id"]
                
            await self.sio.emit("message", message_data, room=recipient_sid)
            return True
        except Exception as e:
            lprint(f"发送消息失败: {str(e)}")
            return False

    async def _update_message_status(self, message_type: MessageType, message_id: int, 
                                   status: MessageStatus) -> bool:
        """更新消息状态
        
        Args:
            message_type: 消息类型
            message_id: 消息ID
            status: 新状态
            
        Returns:
            bool: 是否更新成功
        """
        try:
            if message_type == MessageType.private_chat:
                await self.private_repo.update_message_status(
                    message_id, status, message_type
                )
            else:  # MessageType.group_chat
                await self.group_repo.update_message_status(
                    message_id, status, message_type
                )
            return True
        except Exception as e:
            lprint(f"更新消息状态失败: {str(e)}")
            return False

    async def _handle_private_message(self, sender: str, data: Dict):
        """处理私聊消息"""
        try:
            # 创建并保存消息
            result = await self._create_message(MessageType.private_chat, data, sender)
            if not result:
                return
            message, message_id = result

            # 发送消息给接收者
            recipient_sid = await self.connection_manager.get_sid(data["recipient"])
            if recipient_sid:
                if await self._send_message(MessageType.private_chat, message, message_id, 
                                          recipient_sid, sender):
                    lprint(f"已发送私聊消息: {sender} -> {data['recipient']}")
                    # 更新消息状态为已发送
                    await self._update_message_status(
                        MessageType.private_chat, 
                        message_id,
                        MessageStatus.delivered
                    )
            else:
                lprint(f"接收者 {data['recipient']} 不在线")

        except Exception as e:
            lprint(f"处理私聊消息失败: {str(e)}")
            lprint(traceback.format_exc())

    async def _handle_group_message(self, sender: str, data: Dict):
        """处理群聊消息"""
        try:
            # 创建并保存消息
            result = await self._create_message(MessageType.group_chat, data, sender)
            if not result:
                return
            message, message_id = result

            # 获取群组成员
            group = await self.group_repository.get_group(data["group_id"])
            if not group:
                lprint(f"群组 {data['group_id']} 不存在")
                return

            # 发送消息给群组成员
            delivered_count = 0
            for member in group.members:
                member_sid = await self.connection_manager.get_sid(member)
                if member_sid and member_sid != sender:  # 不发送给发送者自己
                    if await self._send_message(MessageType.group_chat, message, message_id, 
                                              member_sid, sender):
                        delivered_count += 1

            # 更新消息状态
            new_status = MessageStatus.delivered if delivered_count > 0 else MessageStatus.sent
            await self._update_message_status(
                MessageType.group_chat,
                message_id,
                new_status
            )

            lprint(f"已发送群聊消息: {sender} -> 群组 {data['group_id']}, 送达 {delivered_count} 人")

        except Exception as e:
            lprint(f"处理群聊消息失败: {str(e)}")
            lprint(traceback.format_exc())
