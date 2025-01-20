from typing import Dict, Any, Optional
import traceback
import socketio
import Lugwit_Module as LM
from jose import jwt
from .manager import ConnectionManager
from app.core.auth.auth import SECRET_KEY, ALGORITHM
lprint = LM.lprint

class WebSocketHandlers:
    """WebSocket事件处理器，负责核心的Socket.IO连接管理和设备状态更新"""
    
    def __init__(self, connection_manager: ConnectionManager, sio: socketio.AsyncServer):
        """初始化处理器
        
        Args:
            connection_manager: 连接管理器实例
            sio: Socket.IO服务器实例
        """
        self.connection_manager = connection_manager
        self.sio = sio
        
        # 注册Socket.IO事件处理器
        self.setup_handlers()
        
    def setup_handlers(self):
        """注册Socket.IO事件处理器"""
        self.sio.on('connect', self.handle_connect)
        self.sio.on('disconnect', self.handle_disconnect)
        
    def _decode_token(self, token: str) -> Dict[str, Any]:
        """解码JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Dict[str, Any]: 解码后的数据
            
        Raises:
            jwt.JWTError: 令牌无效
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except Exception as e:
            lprint(f"解码JWT令牌失败: {str(e)}")
            raise
        
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
            
            # 从JWT令牌中获取用户名和设备ID
            try:
                payload = self._decode_token(token)
                username = payload.get('sub')  # JWT标准用sub字段存储用户标识
                device_id = payload.get('device_id')
                if not username or not device_id:
                    lprint(f"JWT令牌中缺少必要信息: sid={sid}, payload={payload}")
                    return False
            except Exception as e:
                lprint(f"解析JWT令牌失败: {str(e)}")
                return False
            
            # 获取客户端信息
            scope = environ.get('asgi.scope', {})
            client = scope.get('client', None)
            client_ip = client[0] if client else 'unknown'
            
            # 添加连接
            success = await self.connection_manager.add_connection(
                sid=sid,
                username=username,
                device_id=device_id,
                ip_address=client_ip
            )
            
            if success:
                lprint(f"WebSocket连接成功: sid={sid}, username={username}, device_id={device_id}")
                # 广播用户在线状态
                await self.sio.emit("user_online", {
                    "username": username,
                    "device_id": device_id
                })
                return True
            else:
                lprint(f"WebSocket连接失败: sid={sid}, username={username}")
                return False
            
        except Exception as e:
            lprint(f"处理WebSocket连接时发生错误: {str(e)}")
            lprint(traceback.format_exc())
            return False
            
    async def handle_disconnect(self, sid: str):
        """处理Socket.IO断开连接
        
        Args:
            sid: 会话ID
        """
        try:
            # 获取用户信息
            username = self.connection_manager.get_username_by_sid(sid)
            if not username:
                lprint(f"断开连接: 未找到关联的用户名, sid={sid}")
                return
                
            # 移除连接
            await self.connection_manager.remove_connection(sid)
            lprint(f"WebSocket连接断开: sid={sid}, username={username}")
            
            # 广播用户离线状态
            await self.sio.emit("user_offline", {"username": username})
            
        except Exception as e:
            lprint(f"处理WebSocket断开连接时发生错误: {str(e)}")
            lprint(traceback.format_exc())
