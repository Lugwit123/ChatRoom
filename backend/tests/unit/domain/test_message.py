"""
消息服务单元测试
"""
import pytest
from app.domain.message.service import MessageService
from app.domain.message.models import Message
from Lugwit_Module import lprint

@pytest.mark.asyncio
async def test_create_message(db_session, test_user, test_group):
    """测试创建消息"""
    try:
        service = MessageService(db_session)
        message = await service.create_message(
            content="Test message",
            sender_id=test_user.id,
            group_id=test_group.id
        )
        
        assert message.content == "Test message"
        assert message.sender_id == test_user.id
        assert message.group_id == test_group.id
    except Exception as e:
        lprint(f"创建消息测试失败: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_get_message(db_session, test_message):
    """测试获取消息"""
    try:
        service = MessageService(db_session)
        message = await service.get_message(test_message.id)
        
        assert message is not None
        assert message.id == test_message.id
        assert message.content == test_message.content
    except Exception as e:
        lprint(f"获取消息测试失败: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_get_group_messages(db_session, test_message, test_group):
    """测试获取群组消息"""
    try:
        service = MessageService(db_session)
        messages = await service.get_group_messages(test_group.id)
        
        assert len(messages) > 0
        assert any(m.id == test_message.id for m in messages)
    except Exception as e:
        lprint(f"获取群组消息测试失败: {str(e)}")
        raise
