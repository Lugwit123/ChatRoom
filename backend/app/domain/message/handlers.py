"""消息处理器"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import traceback
from app.domain.message.schemas import MessageBase
from app.domain.message.enums import MessageType, MessageContentType, MessageStatus
from app.core.websocket.manager import ConnectionManager
from app.domain.message.repositories import PrivateMessageRepository, GroupMessageRepository
from app.domain.user.repository import UserRepository
from app.domain.group.repository import GroupRepository, GroupMemberRepository

class MessageHandlers:
    """消息处理器类
    
    处理各种类型的消息事件，包括：
    - 私聊消息
    - 群聊消息
    - 系统消息
    - 状态更新
    """
    
    def __init__(self, 
                 connection_manager: ConnectionManager,
                 private_repo: PrivateMessageRepository,
                 group_repo: GroupMessageRepository,
                 group_repository: GroupRepository,
                 user_repo: UserRepository,
                 member_repo: GroupMemberRepository):
        """初始化消息处理器
        
        Args:
            connection_manager: WebSocket连接管理器
            private_repo: 私聊消息仓储
            group_repo: 群组消息仓储
            group_repository: 群组仓储
            user_repo: 用户仓储
            member_repo: 群成员仓储
        """
        self.connection_manager = connection_manager
        self.private_repo = private_repo
        self.group_repo = group_repo
        self.group_repository = group_repository
        self.user_repo = user_repo
        self.member_repo = member_repo
        self.sio = connection_manager.sio

        # 注册事件处理器
        self.register_handlers()

    def register_handlers(self):
        """注册消息事件处理器"""
        self.sio.on("private_message", self.handle_private_message)
        self.sio.on("group_message", self.handle_group_message)
        
        # 监听用户状态事件
        self.sio.on("user_online", self.handle_user_online)
        self.sio.on("user_offline", self.handle_user_offline)

    async def handle_connect(self, sid: str, environ: Dict):
        """处理连接事件"""
        try:
            # 从环境中获取用户名
            username = environ.get("HTTP_USERNAME")
            if not username:
                lprint(f"连接失败: 未提供用户名")
                return False

            # 获取用户信息
            user = await self.user_repo.get_user_by_username(username)
            if not user:
                lprint(f"连接失败: 用户 {username} 不存在")
                return False

            # 添加连接
            await self.connection_manager.add_connection(sid, username)
            lprint(f"用户 {username} 已连接")

            # 广播用户在线状态
            await self.sio.emit("user_online", {"username": username})
            return True

        except Exception as e:
            lprint(f"处理连接事件失败: {str(e)}")
            return False

    async def handle_disconnect(self, sid: str):
        return
        """处理断开连接事件"""
        try:
            # 获取用户名
            username = await self.connection_manager.get_user_by_sid(sid)
            if not username:
                lprint(f"断开连接: 未找到关联的用户名, sid={sid}")
                return
            # 移除连接
            await self.connection_manager.remove_connection(sid)
            lprint(f"用户 {username} 已断开连接")

            # 广播用户离线状态
            await self.sio.emit("user_offline", {"username": username})

        except Exception as e:
            lprint(f"处理断开连接事件失败: {str(e)}")

    async def handle_private_message(self, sid: str, data: Dict):
        """处理私聊消息"""
        try:
            # 获取发送者用户名
            sender = await self.connection_manager.get_user_by_sid(sid)
            if not sender:
                lprint(f"发送私聊消息失败: 未找到发送者")
                return

            # 创建消息对象
            message = PrivateMessage(
                content=data["content"],
                sender_id=sender,
                recipient_id=data["recipient"],
                content_type=MessageContentType.text,
                status=MessageStatus.sent,
                extra_data=data.get("extra_data", {})
            )

            # 保存消息
            message_id = await self.private_repo.save_message(message)
            if not message_id:
                lprint(f"保存私聊消息失败")
                return

            # 发送消息给接收者
            recipient_sid = await self.connection_manager.get_sid(data["recipient"])
            if recipient_sid:
                await self.sio.emit(
                    "private_message",
                    {
                        "id": message_id,
                        "content": message.content,
                        "sender": sender,
                        "recipient": message.recipient_id,
                        "timestamp": datetime.now().isoformat(),
                        "content_type": message.content_type.value,
                        "extra_data": message.extra_data
                    },
                    room=recipient_sid
                )
                lprint(f"已发送私聊消息: {sender} -> {data['recipient']}")

                # 更新消息状态为已发送
                await self.private_repo.update_message_status(
                    message_id, 
                    MessageStatus.delivered,
                    MessageType.private_chat
                )
            else:
                lprint(f"接收者 {data['recipient']} 不在线")

        except Exception as e:
            lprint(f"处理私聊消息失败: {str(e)}")

    async def handle_group_message(self, sid: str, data: Dict):
        """处理群聊消息"""
        try:
            # 获取发送者用户名
            sender = await self.connection_manager.get_user_by_sid(sid)
            if not sender:
                lprint(f"发送群聊消息失败: 未找到发送者")
                return

            # 创建消息对象
            message = GroupMessage(
                content=data["content"],
                sender_id=sender,
                group_id=data["group_id"],
                content_type=MessageContentType.text,
                status=MessageStatus.sent,
                extra_data=data.get("extra_data", {})
            )

            # 保存消息
            message_id = await self.group_repo.save_message(message)
            if not message_id:
                lprint(f"保存群聊消息失败")
                return

            # 获取群组成员
            group = await self.group_repository.get_group(data["group_id"])
            if not group:
                lprint(f"群组 {data['group_id']} 不存在")
                return

            # 发送消息给群组成员
            delivered_count = 0
            for member in group.members:
                member_sid = await self.connection_manager.get_sid(member)
                if member_sid and member_sid != sid:  # 不发送给发送者自己
                    await self.sio.emit(
                        "group_message",
                        {
                            "id": message_id,
                            "content": message.content,
                            "sender": sender,
                            "group_id": message.group_id,
                            "timestamp": datetime.now().isoformat(),
                            "content_type": message.content_type.value,
                            "extra_data": message.extra_data
                        },
                        room=member_sid
                    )
                    delivered_count += 1

            # 更新消息状态
            new_status = MessageStatus.delivered if delivered_count > 0 else MessageStatus.sent
            await self.group_repo.update_message_status(
                message_id, 
                new_status,
                MessageType.group_chat
            )

            lprint(f"已发送群聊消息: {sender} -> 群组 {data['group_id']}, 送达 {delivered_count} 人")

        except Exception as e:
            lprint(f"处理群聊消息失败: {str(e)}")

    async def handle_user_online(self, data: Dict[str, Any]):
        """处理用户上线事件"""
        try:
            username = data.get("username")
            device_id = data.get("device_id")
            if not username or not device_id:
                return
                
            # 更新用户状态
            user = await self.user_repo.get_user_by_username(username)
            if user:
                # 这里可以添加用户上线的业务逻辑
                lprint(f"用户 {username} (设备 {device_id}) 上线")
                
        except Exception as e:
            lprint(f"处理用户上线事件失败: {str(e)}")
            lprint(traceback.format_exc())

    async def handle_user_offline(self, data: Dict[str, Any]):
        """处理用户离线事件"""
        try:
            username = data.get("username")
            if not username:
                return
                
            # 更新用户状态
            user = await self.user_repo.get_user_by_username(username)
            if user:
                # 这里可以添加用户离线的业务逻辑
                lprint(f"用户 {username} 离线")
                
        except Exception as e:
            lprint(f"处理用户离线事件失败: {str(e)}")
            lprint(traceback.format_exc())

    async def get_unread_messages(self, user_id: str, message_type: Optional[MessageType] = None) -> int:
        """获取用户未读消息数量"""
        try:
            return await self.private_repo.get_unread_count(user_id, message_type)
        except Exception as e:
            lprint(f"获取未读消息数量失败: {str(e)}")
            return 0

    async def mark_messages_as_read(self, user_id: str, message_ids: List[str], message_type: MessageType) -> bool:
        """标记消息为已读"""
        try:
            success = True
            for message_id in message_ids:
                if not await self.private_repo.mark_as_read(message_id, message_type):
                    success = False
            return success
        except Exception as e:
            lprint(f"标记消息已读失败: {str(e)}")
            return False
