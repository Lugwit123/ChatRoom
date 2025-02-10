from typing import Dict, Any, Optional
import traceback
import socketio
import Lugwit_Module as LM
from jose import jwt

from app.core.auth.facade.auth_facade import get_auth_facade
from app.core.websocket.facade.websocket_facade import WebSocketFacade

lprint = LM.lprint

class WebSocketHandlers:
    """WebSocket事件处理器，负责核心的Socket.IO连接管理和设备状态更新"""
    
    def __init__(self, websocket_facade: WebSocketFacade, sio: socketio.AsyncServer):
        """初始化处理器
        
        Args:
            websocket_facade: WebSocket门面类实例
            sio: Socket.IO服务器实例
        """
        self._websocket_facade = websocket_facade
        self._sio = sio
        self._auth_facade = get_auth_facade()
        
    async def handle_connect(self, sid: str, environ: Dict[str, Any]) -> bool:
        """处理新的连接请求
        
        Args:
            sid: 会话ID
            environ: WSGI环境变量
            
        Returns:
            bool: 是否允许连接
        """
        try:
            # 获取token
            headers = environ.get('asgi.scope', {}).get('headers', {})
            token = None
            for name, value in headers:
                if name == b'authorization':
                    token = value.decode('utf-8').split(' ')[1]
                    break
            
            if not token:
                lprint(f"WebSocket连接失败: 未提供token")
                return False
                
            # 验证token
            try:
                payload = await self._auth_facade.verify_token(token)
                user_id = payload.get('sub')
                if not user_id:
                    lprint(f"WebSocket连接失败: token无效")
                    return False
            except jwt.JWTError:
                lprint(f"WebSocket连接失败: token验证失败")
                return False
                
            # 保存连接信息
            await self._websocket_facade.add_connection(sid, user_id)
            lprint(f"WebSocket连接成功: user_id={user_id}, sid={sid}")
            return True
            
        except Exception as e:
            lprint(f"WebSocket连接处理异常: {str(e)}")
            traceback.print_exc()
            return False
            
    async def handle_disconnect(self, sid: str) -> None:
        """处理连接断开
        
        Args:
            sid: 会话ID
        """
        try:
            # 移除连接信息
            await self._websocket_facade.remove_connection(sid)
            lprint(f"WebSocket连接断开: sid={sid}")
        except Exception as e:
            lprint(f"WebSocket断开连接处理异常: {str(e)}")
            traceback.print_exc()
            
    async def handle_error(self, sid: str, e: Exception) -> None:
        """处理错误
        
        Args:
            sid: 会话ID
            e: 异常对象
        """
        lprint(f"WebSocket错误: sid={sid}, error={str(e)}")
        traceback.print_exc()
