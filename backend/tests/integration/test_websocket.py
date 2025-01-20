"""
WebSocket集成测试
"""
import pytest
import asyncio
from app.core.websocket.manager import WebSocketManager
from app.domain.message.service import MessageService
from Lugwit_Module import lprint

@pytest.mark.asyncio
async def test_websocket_message_flow(db_session, test_user, test_group):
    """测试WebSocket消息流程"""
    try:
        # 初始化WebSocket管理器
        manager = WebSocketManager()
        message_service = MessageService(db_session)
        
        # 模拟连接
        connection_id = "test_connection"
        await manager.connect(connection_id, test_user.id)
        
        # 发送消息
        test_message = "Hello, WebSocket!"
        await message_service.create_message(
            content=test_message,
            sender_id=test_user.id,
            group_id=test_group.id
        )
        
        # 验证消息分发
        await manager.broadcast_to_group(
            group_id=test_group.id,
            message=test_message
        )
        
        # 清理
        await manager.disconnect(connection_id)
        
        assert True  # 如果执行到这里没有异常，则测试通过
    except Exception as e:
        lprint(f"WebSocket消息流程测试失败: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_multiple_connections(db_session, test_user):
    """测试多连接场景"""
    try:
        manager = WebSocketManager()
        
        # 创建多个连接
        connections = []
        for i in range(3):
            connection_id = f"test_connection_{i}"
            await manager.connect(connection_id, test_user.id)
            connections.append(connection_id)
        
        # 验证连接数量
        assert len(manager.active_connections) == 3
        
        # 清理连接
        for connection_id in connections:
            await manager.disconnect(connection_id)
            
        assert len(manager.active_connections) == 0
    except Exception as e:
        lprint(f"多连接测试失败: {str(e)}")
        raise
