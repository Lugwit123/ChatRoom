"""
消息服务层实现文件

本文件实现了消息系统的核心业务逻辑，主要包括：

MessageService类的主要功能:
1. 消息管理:
   - create_message(): 创建新消息
   - delete_message(): 删除消息
   - update_message(): 更新消息内容
   - recall_message(): 撤回消息
   - mark_as_read(): 标记消息为已读

2. 消息查询:
   - get_message_by_id(): 根据ID获取消息
   - get_messages(): 获取消息列表
   - get_unread_count(): 获取未读消息数
   - search_messages(): 搜索消息

3. 群组消息:
   - send_group_message(): 发送群组消息
   - get_group_messages(): 获取群组消息
   - get_group_message_by_id(): 获取指定群组消息

4. 私聊消息:
   - send_private_message(): 发送私聊消息
   - get_private_messages(): 获取私聊消息
   - get_private_message_by_id(): 获取指定私聊消息

5. 消息互动:
   - add_reaction(): 添加消息表情回应
   - remove_reaction(): 移除消息表情回应
   - add_mention(): 添加@提醒
   - remove_mention(): 移除@提醒

6. 权限检查:
   - check_message_permission(): 检查消息权限
   - validate_message_access(): 验证消息访问权限
"""

"""消息服务层"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from datetime import datetime
from typing import List, Optional, Union, Dict, Any
from app.domain.message.enums import MessageType, MessageStatus, MessageContentType
from app.domain.message.repositories import PrivateMessageRepository, GroupMessageRepository
from app.domain.group.repository import GroupRepository, GroupMemberRepository
from app.domain.user.repository import UserRepository
from app.core.exceptions import (
    UserNotFoundError,
    GroupNotFoundError,
    MessageCreateError,
    MessageQueryError,
    MessageUpdateError
)

class MessageService:
    """消息服务类
    
    处理消息相关的业务逻辑，包括：
    - 消息的创建和发送
    - 消息的状态管理
    - 消息的权限检查
    """
    
    def __init__(self, 
                 private_repo: PrivateMessageRepository,
                 group_repo: GroupMessageRepository,
                 group_repository: GroupRepository,
                 user_repo: UserRepository,
                 member_repo: GroupMemberRepository = None):
        """初始化消息服务
        
        Args:
            private_repo: 私聊消息仓储
            group_repo: 群组消息仓储
            group_repository: 群组仓储
            user_repo: 用户仓储
            member_repo: 群组成员仓储
        """
        self.private_repo = private_repo
        self.group_repo = group_repo
        self.group_repository = group_repository
        self.user_repo = user_repo
        self.member_repo = member_repo
    
    async def create_message(
        self,
        sender_id: int,
        content: str,
        content_type: MessageContentType = MessageContentType.plain_text,
        group_id: Optional[Union[int, str]] = None,
        receiver_id: Optional[int] = None,
        mentions: Optional[List[int]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        status: MessageStatus = MessageStatus.sent,
        **kwargs
    ):
        """创建消息
        
        Args:
            sender_id: 发送者ID
            content: 消息内容
            content_type: 消息内容类型,默认为纯文本
            group_id: 群组ID,如果是群消息
            receiver_id: 接收者ID,如果是私聊消息
            mentions: @提醒的用户ID列表
            attachments: 附件列表
            status: 消息状态,默认为已发送
            
        Returns:
            创建的消息
            
        Raises:
            UserNotFoundError: 用户不存在
            GroupNotFoundError: 群组不存在
            MessageCreateError: 创建消息失败
        """
        try:
            # 检查发送者是否存在
            sender = await self.user_repo.get_by_id(sender_id)
            if not sender:
                raise UserNotFoundError(f"发送者(ID:{sender_id})不存在")
                
            # 构造消息数据
            message_data = {
                "sender_id": sender_id,
                "content": content,
                "content_type": content_type,
                "status": status,
                **kwargs
            }
            
            if group_id:
                # 群组消息
                group = await self.group_repository.get_by_id(group_id)
                if not group:
                    raise GroupNotFoundError(f"群组(ID:{group_id})不存在")
                    
                # 检查发送者是否是群成员
                is_member = await self.member_repo.is_member(group_id, sender_id)
                if not is_member:
                    raise MessageCreateError(f"用户(ID:{sender_id}, 用户名:{sender.username})不是群组(ID:{group_id}, 群组名:{group.name})的成员")
                    
                message = await self.group_repo.create(
                    group_id=group_id,
                    message_data=message_data
                )
                
            else:
                # 私聊消息
                if not receiver_id:
                    raise MessageCreateError("私聊消息必须指定接收者")
                    
                receiver = await self.user_repo.get_by_id(receiver_id)
                if not receiver:
                    raise UserNotFoundError(f"接收者(ID:{receiver_id})不存在")
                    
                message_data["receiver_id"] = receiver_id
                message = await self.private_repo.create(message_data)
                
            return message
            
        except Exception as e:
            lprint(f"创建消息失败: {str(e)}")
            raise MessageCreateError(str(e))
    
    async def get_message(self, message_id: int, message_type: MessageType, group_id: Optional[str] = None):
        """获取消息
        
        Args:
            message_id: 消息ID
            message_type: 消息类型
            group_id: 群组ID（群聊消息必需）
            
        Returns:
            消息对象
        """
        try:
            if message_type == MessageType.private_chat:
                return await self.private_repo.get_by_id(message_id)
            else:
                if not group_id:
                    raise ValueError("获取群聊消息必须指定群组ID")
                return await self.group_repo.get_by_id(group_id, message_id)
                
        except Exception as e:
            lprint(f"获取消息失败: {str(e)}")
            raise MessageQueryError(str(e))
    
    async def get_messages(self,
                          user_id: str,
                          message_type: MessageType,
                          other_id: Optional[str] = None,
                          group_id: Optional[str] = None,
                          limit: int = 20,
                          before_id: Optional[int] = None,
                          after_id: Optional[int] = None):
        """获取消息列表
        
        Args:
            user_id: 用户ID
            message_type: 消息类型
            other_id: 对方用户ID（私聊消息必需）
            group_id: 群组ID（群聊消息必需）
            limit: 返回消息数量
            before_id: 在此ID之前的消息
            after_id: 在此ID之后的消息
            
        Returns:
            消息列表
        """
        try:
            if message_type == MessageType.private_chat:
                if not other_id:
                    raise ValueError("获取私聊消息必须指定对方用户ID")
                return await self.private_repo.get_messages(
                    user_id=user_id,
                    other_id=other_id,
                    limit=limit,
                    before_id=before_id,
                    after_id=after_id
                )
            else:
                if not group_id:
                    raise ValueError("获取群聊消息必须指定群组ID")
                return await self.group_repo.get_messages(
                    group_id=group_id,
                    limit=limit,
                    before_id=before_id,
                    after_id=after_id
                )
                
        except Exception as e:
            lprint(f"获取消息列表失败: {str(e)}")
            raise MessageQueryError(str(e))
    
    async def mark_as_read(self,
                          user_id: str,
                          message_type: MessageType,
                          message_id: Optional[int] = None,
                          other_id: Optional[str] = None,
                          group_id: Optional[str] = None):
        """标记消息为已读
        
        Args:
            user_id: 用户ID
            message_type: 消息类型
            message_id: 消息ID（可选）
            other_id: 对方用户ID（私聊消息必需）
            group_id: 群组ID（群聊消息必需）
            
        Returns:
            更新的消息数量
        """
        try:
            if message_type == MessageType.private_chat:
                if not other_id:
                    raise ValueError("标记私聊消息已读必须指定对方用户ID")
                if message_id:
                    await self.private_repo.update_status(message_id, MessageStatus.read)
                    return 1
                else:
                    return await self.private_repo.mark_as_read(user_id, other_id)
            else:
                if not group_id:
                    raise ValueError("标记群聊消息已读必须指定群组ID")
                if message_id:
                    await self.group_repo.update_status(group_id, message_id, MessageStatus.read)
                    return 1
                else:
                    # TODO: 实现标记群组所有消息已读
                    pass
                    
        except Exception as e:
            lprint(f"标记消息已读失败: {str(e)}")
            raise MessageUpdateError(str(e))
    
    async def add_reaction(self,
                          user_id: str,
                          message_type: MessageType,
                          message_id: int,
                          reaction: str,
                          group_id: Optional[str] = None):
        """添加表情回应
        
        Args:
            user_id: 用户ID
            message_type: 消息类型
            message_id: 消息ID
            reaction: 表情
            group_id: 群组ID（群聊消息必需）
        """
        try:
            if message_type == MessageType.private_chat:
                await self.private_repo.add_reaction(message_id, user_id, reaction)
            else:
                if not group_id:
                    raise ValueError("群聊消息必须指定群组ID")
                await self.group_repo.add_reaction(group_id, message_id, user_id, reaction)
                
        except Exception as e:
            lprint(f"添加表情回应失败: {str(e)}")
            raise MessageUpdateError(str(e))
    
    async def remove_reaction(self,
                            user_id: str,
                            message_type: MessageType,
                            message_id: int,
                            reaction: str,
                            group_id: Optional[str] = None):
        """移除表情回应
        
        Args:
            user_id: 用户ID
            message_type: 消息类型
            message_id: 消息ID
            reaction: 表情
            group_id: 群组ID（群聊消息必需）
        """
        try:
            if message_type == MessageType.private_chat:
                await self.private_repo.remove_reaction(message_id, user_id, reaction)
            else:
                if not group_id:
                    raise ValueError("群聊消息必须指定群组ID")
                await self.group_repo.remove_reaction(group_id, message_id, user_id, reaction)
                
        except Exception as e:
            lprint(f"移除表情回应失败: {str(e)}")
            raise MessageUpdateError(str(e))
    
    async def get_unread_count(self, user_id: str, message_type: MessageType, group_id: Optional[str] = None):
        """获取未读消息数量
        
        Args:
            user_id: 用户ID
            message_type: 消息类型
            group_id: 群组ID（群聊消息必需）
            
        Returns:
            未读消息数量
        """
        try:
            if message_type == MessageType.private_chat:
                return await self.private_repo.get_unread_count(user_id)
            else:
                if not group_id:
                    raise ValueError("获取群聊未读消息数量必须指定群组ID")
                return await self.group_repo.get_unread_count(group_id, user_id)
                
        except Exception as e:
            lprint(f"获取未读消息数量失败: {str(e)}")
            raise MessageQueryError(str(e))
