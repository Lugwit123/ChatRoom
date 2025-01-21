from typing import Dict, Any, Optional
import traceback
import socketio
import Lugwit_Module as LM
from jose import jwt

from app.core.auth.auth_facade import AuthFacade
from .websocket_facade import WebSocketFacade

lprint = LM.lprint

class WebSocketHandlers:
    """WebSocket事件处理器，负责核心的Socket.IO连接管理和设备状态更新"""
    
    def __init__(self, websocket_facade: WebSocketFacade, sio: socketio.AsyncServer):
        """初始化处理器
        
        Args:
            websocket_facade: WebSocket门面类实例
            sio: Socket.IO服务器实例
        """
        self.websocket_facade = websocket_facade
        self.sio = sio
        self.auth_facade = AuthFacade()
        
        # 注册Socket.IO事件处理器
        self.setup_handlers()
        
    def setup_handlers(self):
        """注册Socket.IO事件处理器"""
        self.sio.on('connect', self.handle_connect)
        self.sio.on('disconnect', self.handle_disconnect)
        
    async def handle_connect(self, sid: str, environ: dict, auth: dict):
        """处理Socket.IO连接请求
        
        Args:
            sid: 会话ID
            environ: 环境变量
            auth: 认证数据，必须包含token
            
        Returns:
            bool: 连接是否成功
        """
        try:
            # 验证认证数据
            lprint(f"处理WebSocket连接: sid={sid}, auth={auth}")
            if not auth or 'token' not in auth:
                lprint(f"认证数据无效: sid={sid}, auth={auth}")
                return False
                
            token = auth['token']
            
            try:
                # 使用auth_facade验证令牌
                user = await self.auth_facade.get_current_user(token)
                if not user:
                    lprint(f"用户验证失败: sid={sid}")
                    return False
                    
                username = user.username
                device_id = user.device_id
                
            except Exception as e:
                lprint(f"解析JWT令牌失败: {str(e)}")
                return False
            
            # 获取客户端信息
            scope = environ.get('asgi.scope', {})
            client = scope.get('client', None)
            client_ip = client[0] if client else 'unknown'
            
            # 添加连接
            await self.websocket_facade.connect(sid, str(user.id), device_id, client_ip)
            
            # 广播用户在线状态
            await self.sio.emit("user_online", {
                "username": username,
                "device_id": device_id
            })
            
            return True
            
        except Exception as e:
            lprint(f"WebSocket连接失败: {str(e)}\n{traceback.format_exc()}")
            return False
            
    async def handle_disconnect(self, sid: str):
        """处理Socket.IO断开连接
        
        Args:
            sid: 会话ID
        """
        try:
            # 移除连接
            await self.websocket_facade.disconnect(sid)
            
        except Exception as e:
            lprint(f"处理断开连接失败: {str(e)}\n{traceback.format_exc()}")
