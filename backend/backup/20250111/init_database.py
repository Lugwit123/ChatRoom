# backend/init_database.py

import asyncio
import logging
import os
import json
import traceback
from datetime import datetime, timezone, timedelta
from typing import List

import aiofiles
import sqlalchemy as sa

import schemas
from user_database import (
    create_tables,
    insert_user,
    insert_group,
    init_message_types,
    get_message_type_id,
    get_content_type_id,
    insert_message,
    engine,
    fetch_user,
    start_background_tasks,
    message_update_queue,
    async_session,
    UserResponse
)

# 初始化日志
logging.basicConfig(level=logging.INFO)

# 获取当前目录
curDir: str = os.path.dirname(os.path.abspath(__file__))


async def load_initial_users(json_path: str) -> None:
    """从 JSON 文件加载初始用户数据"""
    if not os.path.exists(json_path):
        logging.warning(f"初始用户文件未找到: {json_path}")
        return

    async with aiofiles.open(json_path, 'r', encoding='utf-8') as f:
        content = await f.read()
        data = json.loads(content)

    # 先创建所有群组
    groups = data.get("groups", [])
    for group in groups:
        try:
            await insert_group({"name": group["name"]})
            logging.info(f"已添加群组: {group['name']}")
        except Exception as e:
            logging.error(f"添加群组 '{group.get('name', '未知')}' 失败: {e}")

    # 创建所有用户
    users = data.get("users", [])

    for user_data in users:
        try:
            # 使用 Pydantic 模型解析用户数据，自动处理默认值
            user_create = schemas.UserCreate(**user_data)

            await insert_user(
                username=user_create.username,
                nickname=user_create.nickname,
                password=user_create.password,
                email=user_create.email,
                role=user_create.role,
                group_names=user_create.groups,
                is_temporary=user_create.is_temporary,
                online=user_create.online  # 传递 online 字段
            )
            logging.info(f"已添加用户: {user_create.username}")
        except Exception as e:
            logging.error(f"添加用户 '{user_data.get('username', '未知')}' 失败: {e}")
            traceback.print_exc()


async def load_initial_messages(json_path: str) -> None:
    """从 JSON 文件加载初始消息"""
    if not os.path.exists(json_path):
        logging.warning(f"初始消息文件未找到: {json_path}")
        return

    async with aiofiles.open(json_path, 'r', encoding='utf-8') as f:
        content = await f.read()
        data = json.loads(content)

    try:
        # 确保所需用户存在
        required_users = set()
        for msg in data.get("private_messages", []):
            required_users.add(msg["sender"])
            required_users.add(msg["recipient"])

        # 检查用户是否存在并初始化 message_ids
        missing_users = []
        async with async_session() as session:
            for username in required_users:
                user = await fetch_user(username)
                if not user:
                    logging.error(f"用户 '{username}' 不存在，跳过相关消息")
                    missing_users.append(username)
                else:
                    # 初始化用户的 message_ids
                    stmt = sa.update(UserResponse).where(
                        UserResponse.username == username
                    ).values(
                        message_ids=[]
                    )
                    await session.execute(stmt)
            await session.commit()

        # 只插入私聊消息
        for msg_data in data.get("private_messages", []):
            if msg_data["sender"] in missing_users or msg_data["recipient"] in missing_users:
                logging.warning(f"跳过消息: {msg_data['content']} 因为发送者或接收者不存在")
                continue
            try:
                message_create = schemas.MessageCreate(**msg_data)
                # 处理时间戳，确保正确的时区转换
                timestamp = message_create.timestamp
                if timestamp:
                    if not timestamp.tzinfo:
                        # 如果时间戳没有时区信息，假定为本地时间（UTC+8）
                        timestamp = timestamp.replace(tzinfo=timezone(timedelta(hours=8)))
                    # 将时间转换为 UTC 时间，然后去除时区信息
                    timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    # 如果没有时间戳，使用当前 UTC 时间（不带时区信息）
                    timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
                
                message = schemas.MessageBase(
                    sender=message_create.sender,
                    recipient=message_create.recipient,
                    content=message_create.content,
                    timestamp=timestamp,
                    recipient_type="private",
                    status=["unread"],
                    message_type=schemas.MessageType.PRIVATE_CHAT,
                    message_content_type=schemas.MessageContentType.HTML,
                    popup_message=message_create.popup_message,
                    direction=schemas.MessageDirection.RESPONSE
                )

                # 插入消息并获取消息ID
                inserted_message = await insert_message(message)
                if not inserted_message or not inserted_message.id:
                    continue

                # 更新发送者和接收者的 message_ids
                async with async_session() as session:
                    # 更新发送者
                    sender_stmt = sa.select(UserResponse).where(
                        UserResponse.username == message.sender
                    )
                    sender = (await session.execute(sender_stmt)).scalar_one_or_none()
                    if sender:
                        if not sender.message_ids:
                            sender.message_ids = []
                        sender.message_ids.append(inserted_message.id)
                        
                    # 更新接收者
                    recipient_stmt = sa.select(UserResponse).where(
                        UserResponse.username == message.recipient
                    )
                    recipient = (await session.execute(recipient_stmt)).scalar_one_or_none()
                    if recipient:
                        if not recipient.message_ids:
                            recipient.message_ids = []
                        recipient.message_ids.append(inserted_message.id)
                    
                    await session.commit()
                    
                    logging.info(f"消息 {inserted_message.id} 已添加到发送者和接收者的 message_ids")

            except Exception as e:
                logging.error(f"添加消息失败: {e}")
                logging.error(traceback.format_exc())
                continue

        logging.info("初始消息加载完成")
        
        # 验证最终结果
        async with async_session() as session:
            for username in required_users:
                if username not in missing_users:
                    user_stmt = sa.select(UserResponse).where(
                        UserResponse.username == username
                    )
                    user = (await session.execute(user_stmt)).scalar_one_or_none()
                    if user:
                        logging.info(f"用户 {username} 的最终 message_ids: {user.message_ids}")

    except Exception as e:
        logging.error(f"加载初始消息时出错: {e}")
        logging.error(traceback.format_exc())


async def initialize_db() -> None:
    """初始化数据库"""
    background_task = None  # 用于存储后台任务的引用
    try:
        logging.info("开始初始化数据库...")

        # 删除并重新创建所有表
        await create_tables(drop_existing=True)
        logging.info("数据库表创建完成")

        # 初始化消息类型
        await init_message_types()
        logging.info("消息类型初始化完成")

        # 启动后台消息ID更新任务
        background_task = await start_background_tasks()
        logging.info("后台消息ID更新任务启动完成")

        # 加载初始用户数据
        initial_users_path: str = os.path.join(curDir, "initial_users.json")
        await load_initial_users(initial_users_path)
        logging.info("用户数据加载完成")

        # 加载初始消息数据
        initial_messages_path: str = os.path.join(curDir, "initial_messages.json")
        await load_initial_messages(initial_messages_path)
        logging.info("消息数据加载完成")

        # 等待所有消息ID更新任务完成，添加超时��制
        try:
            await asyncio.wait_for(message_update_queue.join(), timeout=30.0)
            logging.info("所有消息ID更新任务已完成")
        except asyncio.TimeoutError:
            logging.warning(f"等待消息ID更新任务超时，当前队列中还有 {message_update_queue.qsize()} 个任务未完成")

        logging.info("数据库初始化完成。")
    except Exception as e:
        logging.error(f"初始化数据库时出错: {e}")
        logging.error(traceback.format_exc())
    finally:
        # 取消后台任务
        if background_task and not background_task.done():
            background_task.cancel()
            try:
                await background_task
            except asyncio.CancelledError:
                pass
        # 确保清理资源
        await engine.dispose()
        logging.info("数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(initialize_db())
