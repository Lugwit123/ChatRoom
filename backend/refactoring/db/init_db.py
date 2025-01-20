"""数据库初始化脚本"""
import asyncio
import Lugwit_Module as LM
from datetime import datetime

from refactoring.db.database import init_db, async_session
from refactoring.db.crud import (
    create_user, create_group, add_user_to_group,
    create_device, create_message_type, create_message_content_type
)
from refactoring.db.schemas import UserRole, UserStatus, MessageType, MessageContentType

lprint = LM.lprint

async def init_message_types(session):
    """初始化消息类型"""
    for type_code in MessageType:
        await create_message_type(session, type_code)
    lprint("消息类型初始化完成")

async def init_message_content_types(session):
    """初始化消息内容类型"""
    for type_code in MessageContentType:
        await create_message_content_type(session, type_code)
    lprint("消息内容类型初始化完成")

async def init_test_data(session):
    """初始化测试数据"""
    # 创建管理员用户
    admin = await create_user(
        session,
        username="admin",
        password="admin123",
        role=UserRole.admin
    )
    lprint(f"创建管理员用户: {admin.username}")

    # 创建测试用户
    test_user = await create_user(
        session,
        username="test_user",
        password="test123"
    )
    lprint(f"创建测试用户: {test_user.username}")

    # 创建测试群组
    test_group = await create_group(
        session,
        name="测试群组",
        description="这是一个测试群组",
        created_by=admin.id
    )
    lprint(f"创建测试群组: {test_group.name}")

    # 添加用户到群组
    await add_user_to_group(session, admin.id, test_group.id, is_admin=True)
    await add_user_to_group(session, test_user.id, test_group.id)
    lprint("添加用户到群组完成")

    # 创建测试设备
    admin_device = await create_device(
        session,
        name="管理员设备",
        user_id=admin.id,
        description="管理员的测试设备"
    )
    test_device = await create_device(
        session,
        name="测试设备",
        user_id=test_user.id,
        description="测试用户的设备"
    )
    lprint("创建测试设备完成")

async def main():
    """主函数"""
    try:
        # 初始化数据库
        lprint("开始初始化数据库...")
        await init_db()
        lprint("数据库表创建完成")

        # 创建会话
        async with async_session() as session:
            # 初始化消息类型
            await init_message_types(session)
            # 初始化消息内容类型
            await init_message_content_types(session)
            # 初始化测试数据
            await init_test_data(session)

        lprint("数据库初始化完成")

    except Exception as e:
        lprint(f"数据库初始化失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
