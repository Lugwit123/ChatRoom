"""
端到端测试场景
"""
import pytest
import asyncio
from app.core.auth.service import AuthService
from app.domain.message.service import MessageService
from app.domain.group.service import GroupService
from Lugwit_Module import lprint

@pytest.mark.asyncio
async def test_complete_chat_flow(db_session):
    """测试完整的聊天流程"""
    try:
        # 1. 用户注册和登录
        auth_service = AuthService(db_session)
        user = await auth_service.register_user(
            username="test_user",
            email="test@example.com",
            password="password123"
        )
        token = await auth_service.login_user(
            email="test@example.com",
            password="password123"
        )
        assert token is not None
        
        # 2. 创建群组
        group_service = GroupService(db_session)
        group = await group_service.create_group(
            name="Test Group",
            creator_id=user.id,
            description="Test group for e2e testing"
        )
        assert group is not None
        
        # 3. 发送消息
        message_service = MessageService(db_session)
        message = await message_service.create_message(
            content="Hello, this is an e2e test message!",
            sender_id=user.id,
            group_id=group.id
        )
        assert message is not None
        
        # 4. 获取群组消息
        messages = await message_service.get_group_messages(group.id)
        assert len(messages) > 0
        assert messages[0].content == "Hello, this is an e2e test message!"
        
    except Exception as e:
        lprint(f"完整聊天流程测试失败: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_error_scenarios(db_session):
    """测试错误场景"""
    try:
        auth_service = AuthService(db_session)
        message_service = MessageService(db_session)
        
        # 1. 测试重复用户注册
        with pytest.raises(Exception):
            await auth_service.register_user(
                username="test_user",
                email="test@example.com",
                password="password123"
            )
            await auth_service.register_user(
                username="test_user",
                email="test@example.com",
                password="password123"
            )
        
        # 2. 测试无效消息
        with pytest.raises(Exception):
            await message_service.get_message(999999)
            
    except Exception as e:
        lprint(f"错误场景测试失败: {str(e)}")
        raise
