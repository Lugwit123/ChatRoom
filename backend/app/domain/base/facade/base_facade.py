"""基础门面类

提供所有门面层共用的基础功能，包括:
1. 日志记录
2. 错误处理
3. 响应封装
"""
import traceback
from typing import TypeVar, Generic, Optional, Any
import Lugwit_Module as LM
from app.domain.base.facade.dto.base_dto import ResponseDTO
import socketio
from app.core.websocket.internal.server import SocketServer
from app.core.base.core_facade import CoreFacade
from app.core.di.container import Container

T = TypeVar('T')

class BaseFacade(CoreFacade, Generic[T]):
    """基础门面类
    
    为所有门面类提供基础功能:
    1. 日志记录
    2. 错误处理
    3. 响应封装
    4. WebSocket支持
    """
    
    def __init__(self, container: Optional[Container] = None, need_websocket: bool = False):
        """初始化基础门面
        
        Args:
            container: 可选的容器实例
            need_websocket: 是否需要WebSocket支持
        """
        super().__init__(container)
        self._sio: Optional[socketio.AsyncServer] = None
        if need_websocket:
            self._sio = SocketServer.get_server()
            if self._sio is None:
                raise RuntimeError("Socket.IO server not initialized")
        
    @property
    def sio(self) -> Optional[socketio.AsyncServer]:
        """获取Socket.IO服务器实例"""
        return self._sio
        
    def _handle_error(self, error: Exception, message: Optional[str] = None) -> ResponseDTO:
        """统一错误处理
        
        Args:
            error: 异常对象
            message: 错误消息,可选
            
        Returns:
            ResponseDTO: 包含错误信息的响应对象
        """
        error_message = message or str(error)
        self.lprint(f"错误: {error_message}")
        self.lprint(traceback.format_exc())
        return ResponseDTO.error(message=error_message)
        
    def _success_response(self, data: Optional[Any] = None, message: str = "操作成功") -> ResponseDTO:
        """生成成功响应
        
        Args:
            data: 响应数据,可选
            message: 成功消息
            
        Returns:
            ResponseDTO: 包含成功数据的响应对象
        """
        return ResponseDTO.success(data=data, message=message) 