"""
WebSocket事件处理器
负责处理Socket.IO的各种事件
"""
import Lugwit_Module as LM
from typing import Dict, Any, Optional
import traceback
import socketio
from jose import jwt

from app.core.auth.facade.auth_facade import AuthFacade
from ..interfaces import IWebSocketEventHandler, IConnectionManager, IRoomManager

lprint = LM.lprint

class WebSocketHandlers(IWebSocketEventHandler):
    """WebSocket事件处理器
    
    主要职责:
    1. 处理Socket.IO的连接、断开连接等事件
    2. 协调连接管理器和房间管理器
    3. 处理错误情况
    4. 处理认证和会话管理
    """
    
    def __init__(self, connection_manager: IConnectionManager, room_manager: IRoomManager, auth_facade: AuthFacade):
        """初始化事件处理器
        
        Args:
            connection_manager: 连接管理器
            room_manager: 房间管理器
            auth_facade: 认证门面
        """
        self._connection_manager = connection_manager
        self._room_manager = room_manager
        self._auth_facade = auth_facade
        lprint("事件处理器初始化完成")
        
    async def on_connect(self, sid: str, environ: dict, auth: Optional[dict] = None) -> None:
        """处理连接事件
        
        工作流程:
        1. 验证认证信息
        2. 添加新连接
        3. 自动加入相关房间
        
        Args:
            sid: Socket.IO会话ID
            environ: WSGI环境
            auth: 认证数据
        """
        try:
            # 验证认证信息
            if not auth or 'token' not in auth:
                lprint(f"认证失败: 未提供token, sid={sid}")
                return
                
            token = auth['token']
            
            # 验证token
            try:
                payload = await self._auth_facade.verify_token(token)
                user_id = payload.get('sub')
                if not user_id:
                    lprint(f"认证失败: token无效, sid={sid}")
                    return
            except jwt.JWTError:
                lprint(f"认证失败: token验证失败, sid={sid}")
                return
                
            # 获取设备信息
            device_id = environ.get('HTTP_X_DEVICE_ID', 'unknown')
            ip_address = environ.get('REMOTE_ADDR', '0.0.0.0')
            
            # 添加连接
            await self._connection_manager.add_connection(sid, user_id, device_id, ip_address)
            lprint(f"新连接已建立: sid={sid}, user_id={user_id}")
            
        except Exception as e:
            lprint(f"处理连接事件失败: {str(e)}")
            lprint(traceback.format_exc())
            await self.on_error(sid, e)
            
    async def on_disconnect(self, sid: str) -> None:
        """处理断开连接事件
        
        工作流程:
        1. 清理房间记录
        2. 移除连接
        
        Args:
            sid: Socket.IO会话ID
        """
        try:
            # 清理房间记录
            await self._room_manager.remove_sid(sid)
            
            # 移除连接
            await self._connection_manager.remove_connection(sid)
            
            lprint(f"连接已断开: sid={sid}")
            
        except Exception as e:
            lprint(f"处理断开连接事件失败: {str(e)}")
            lprint(traceback.format_exc())
            await self.on_error(sid, e)
            
    async def on_message(self, sid: str, data: dict) -> None:
        """处理消息事件
        
        工作流程:
        1. 获取发送者信息
        2. 验证消息格式
        3. 转发消息到目标房间
        
        Args:
            sid: Socket.IO会话ID
            data: 消息数据
        """
        try:
            # 获取发送者ID
            user_id = self._connection_manager.get_user_id(sid)
            if not user_id:
                lprint(f"无法获取发送者ID: sid={sid}")
                return
                
            # 验证消息格式
            if not isinstance(data, dict):
                lprint(f"无效的消息格式: {data}")
                return
                
            # 添加发送者信息
            data['sender_id'] = user_id
            
            lprint(f"消息已处理: {data}")
            
        except Exception as e:
            lprint(f"处理消息事件失败: {str(e)}")
            lprint(traceback.format_exc())
            await self.on_error(sid, e)
            
    async def on_error(self, sid: str, error: Exception) -> None:
        """处理错误事件
        
        工作流程:
        1. 记录错误信息
        2. 尝试清理相关资源
        
        Args:
            sid: Socket.IO会话ID
            error: 错误信息
        """
        try:
            lprint(f"发生错误: sid={sid}, error={str(error)}")
            lprint(traceback.format_exc())
            
            # 尝试清理资源
            await self._room_manager.remove_sid(sid)
            await self._connection_manager.remove_connection(sid)
            
        except Exception as e:
            lprint(f"处理错误事件失败: {str(e)}")
            lprint(traceback.format_exc())
