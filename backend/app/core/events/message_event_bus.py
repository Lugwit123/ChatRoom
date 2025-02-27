"""消息事件总线

提供统一的消息事件管理机制
"""
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
from typing import Dict, Set, Optional, Callable, Awaitable, Any
import traceback
from datetime import datetime

from .interfaces import MessageEvent, EventType, EventHandler
from app.core.websocket.facade.websocket_facade import WebSocketFacade

lprint = LM.lprint

class MessageEventBus:
    """消息事件总线，统一管理消息相关事件"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._handlers: Dict[EventType, list[EventHandler]] = {}
            self._processed_messages: Set[int] = set()  # 用于去重
            self._websocket_facade = WebSocketFacade()
            self._initialized = True
            
    async def publish_message_event(self, event: MessageEvent) -> None:
        """统一的消息事件发布入口
        
        Args:
            event: 消息事件
        """
        try:
            # 1. 检查是否已处理
            if event.message_id in self._processed_messages:
                lprint(f"消息 {event.message_id} 已处理，跳过")
                return
                
            # 2. 记录已处理
            self._processed_messages.add(event.message_id)
            
            # 3. 根据事件类型处理
            if event.event_type == EventType.private_message_sent:
                await self._handle_private_message(event)
            elif event.event_type == EventType.group_message_sent:
                await self._handle_group_message(event)
                
        except Exception as e:
            lprint(f"处理消息事件失败: {str(e)}")
            traceback.print_exc()
            
    async def _handle_private_message(self, event: MessageEvent) -> None:
        """处理私聊消息事件"""
        try:
            # 1. 获取接收者ID
            recipient_id = event.data.get('recipient_id')
            if not recipient_id:
                lprint(f"私聊消息缺少接收者ID: {event.message_id}")
                return
                
            # 2. 发送消息到接收者
            await self._websocket_facade.emit_to_user(
                str(recipient_id),
                "message",
                event.data
            )
            
            lprint(f"私聊消息已发送: message_id={event.message_id}, recipient_id={recipient_id}")
            
        except Exception as e:
            lprint(f"处理私聊消息事件失败: {str(e)}")
            traceback.print_exc()
            
    async def _handle_group_message(self, event: MessageEvent) -> None:
        """处理群聊消息事件"""
        try:
            # 1. 获取群组ID
            group_id = event.group_id
            if not group_id:
                lprint(f"群聊消息缺少群组ID: {event.message_id}")
                return
                
            # 2. 发送消息到群组
            room = f"group_{group_id}"
            await self._websocket_facade.broadcast_to_group(
                str(group_id),
                "message",
                event.data
            )
            
            lprint(f"群聊消息已发送: message_id={event.message_id}, group_id={group_id}")
            
        except Exception as e:
            lprint(f"处理群聊消息事件失败: {str(e)}")
            traceback.print_exc()
            
    def clear_processed_messages(self) -> None:
        """清理已处理消息记录"""
        self._processed_messages.clear() 