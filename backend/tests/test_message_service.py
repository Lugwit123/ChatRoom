"""
消息服务单元测试
"""
import pytest
from datetime import datetime
from app.domain.message.internal.models import Message
from app.domain.message.internal.services.message_service import MessageService
from app.domain.message.facade.dto.message_dto import MessageCreateDTO, MessageDTO

@pytest.fixture
def message_service():
    """创建消息服务实例"""
    return MessageService()

@pytest.fixture
def test_message():
    """创建测试消息"""
    return Message(
        id="test_msg_1",
        content="测试消息",
        sender_id="user1",
        receiver_id="user2",
        created_at=datetime.now()
    )

@pytest.mark.asyncio
async def test_send_private_message(message_service, test_message):
    """测试发送私聊消息"""
    result = await message_service.send(test_message)
    assert result.content == test_message.content
    assert result.sender_id == test_message.sender_id
    assert result.receiver_id == test_message.receiver_id
    assert result.group_id is None

@pytest.mark.asyncio
async def test_send_group_message(message_service):
    """测试发送群组消息"""
    group_message = Message(
        id="test_msg_2",
        content="群组测试消息",
        sender_id="user1",
        group_id="group1",
        created_at=datetime.now()
    )
    result = await message_service.send(group_message)
    assert result.content == group_message.content
    assert result.sender_id == group_message.sender_id
    assert result.group_id == group_message.group_id
    assert result.receiver_id is None

@pytest.mark.asyncio
async def test_get_private_messages(message_service, test_message):
    """测试获取私聊消息列表"""
    # 先发送一条测试消息
    await message_service.send(test_message)
    # 获取消息列表
    messages = await message_service.get_messages(test_message.receiver_id)
    assert len(messages) > 0
    assert any(msg.id == test_message.id for msg in messages)

@pytest.mark.asyncio
async def test_get_group_messages(message_service):
    """测试获取群组消息列表"""
    group_id = "group1"
    group_message = Message(
        id="test_msg_3",
        content="群组测试消息",
        sender_id="user1",
        group_id=group_id,
        created_at=datetime.now()
    )
    await message_service.send(group_message)
    messages = await message_service.get_messages("user1", group_id)
    assert len(messages) > 0
    assert any(msg.id == group_message.id for msg in messages)

@pytest.mark.asyncio
async def test_mark_message_as_read(message_service, test_message):
    """测试标记消息已读"""
    # 先发送一条测试消息
    sent_message = await message_service.send(test_message)
    # 标记为已读
    result = await message_service.mark_as_read(sent_message.id, test_message.receiver_id)
    assert result is True
    # 验证消息已读状态
    messages = await message_service.get_messages(test_message.receiver_id)
    read_message = next(msg for msg in messages if msg.id == sent_message.id)
    assert read_message.read_at is not None
