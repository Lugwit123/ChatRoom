"""
用户相关的路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select, update, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import pytz
import Lugwit_Module as LM
import json

from ..core.auth import get_current_user
from ..db import database
from ..db.schemas import (
    User, UserBaseAndStatus, UsersInfoDictResponse,
    DeviceResponse, Device, PrivateMessage, MessageBase,
    MessageTypeModel, MessageContentTypeModel
)

router = APIRouter()
lprint = LM.lprint

# 设备在线超时时间（分钟）
DEVICE_ONLINE_TIMEOUT = 5

async def update_device_status(session: AsyncSession, device: Device, login_status: bool):
    """更新设备在线状态"""
    try:
        device.login_status = login_status
        device.last_seen = datetime.now(ZoneInfo("Asia/Shanghai"))
        session.add(device)
        await session.commit()
        lprint(f"设备 {device.device_id} 状态更新为: {'在线' if login_status else '离线'}")
    except Exception as e:
        lprint(f"更新设备状态失败: {str(e)}")
        await session.rollback()
        raise

def is_device_online(device) -> bool:
    """判断设备是否在线"""
    try:
        if not device or not device.last_seen:
            return False
        
        # 获取当前时间
        now = datetime.now(ZoneInfo("Asia/Shanghai"))
        
        # 计算最后在线时间和当前时间的差值（分钟）
        minutes_diff = (now - device.last_seen).total_seconds() / 60
        
        # 如果最后在线时间在10分钟内，认为设备在线
        login_status = minutes_diff <= 10
        
        lprint(f"设备 {device.device_id} - 最后在线: {device.last_seen}, 当前时间戳: {now}, 时间差: {minutes_diff:.2f}分钟, 在线状态: {login_status}")
        return login_status
    except Exception as e:
        lprint(f"检查设备在线状态失败: {str(e)}")
        return False

async def get_group_unread_count(session: AsyncSession, group_name: str, user_id: int) -> int:
    """获取群组未读消息数"""
    # TODO: 实现获取群组未读消息数的逻辑
    return 0

@router.get("/api/users_map", response_model=UsersInfoDictResponse)
async def get_users_map(current_user: User = Depends(get_current_user)):
    """获取所有用户的映射信息"""
    try:
        lprint(f"获取用户映射 - 当前用户: {current_user.username}")
        async with database.async_session() as session:
            # 重新获取当前用户，确保绑定到当前会话
            current_user_result = await session.execute(
                select(User)
                .options(selectinload(User.groups))
                .where(User.id == current_user.id)
            )
            current_user = current_user_result.scalar_one()
            
            # 查询所有用户，预加载 groups 关系
            result = await session.execute(
                select(User).options(selectinload(User.groups))
            )
            users = result.scalars().all()
            lprint(f"查询到 {len(users)} 个用户")
            
            # 构建用户映射
            user_map = {}
            for user in users:
                if user.username != current_user.username:  # 排除当前用户
                    # 查询用户的设备
                    devices_result = await session.execute(
                        select(Device).where(Device.user_id == user.id)
                    )
                    devices = devices_result.scalars().all()
                    lprint(f"用户 {user.username} 有 {len(devices)} 个设备")
                    
                    # 检查每个设备的详细信息
                    for device in devices:
                        lprint(f"设备信息 - ID: {device.device_id}, 名称: {device.device_name}, 最后在线: {device.last_seen}, is_online标志: {device.login_status}")
                        # 检查并更新设备状态
                        device_online = is_device_online(device)
                        await update_device_status(session, device, device_online)
                    
                    # 检查是否有在线设备
                    online_devices = [
                        DeviceResponse(
                            id=d.id,
                            device_id=d.device_id,
                            device_name=d.device_name,
                            device_type=d.device_type,
                            login_status=d.login_status,
                            last_seen=d.last_seen,
                            ip_address=d.ip_address,
                            user_agent=d.user_agent
                        )
                        for d in devices if d.login_status
                    ]
                    login_status = len(online_devices) > 0
                    lprint(f"用户 {user.username} 在线状态: {login_status} (在线设备: {len(online_devices)})")

                    # 查询与该用户的最近聊天记录
                    messages_result = await session.execute(
                        select(PrivateMessage)
                        .where(
                            or_(
                                and_(PrivateMessage.sender_id == current_user.id, 
                                     PrivateMessage.recipient_id == user.id),
                                and_(PrivateMessage.sender_id == user.id, 
                                     PrivateMessage.recipient_id == current_user.id)
                            )
                        )
                        .order_by(PrivateMessage.timestamp.desc())
                        .limit(20)  # 限制返回最近20条消息
                    )
                    messages = messages_result.scalars().all()
                    lprint(f"获取到与用户 {user.username} 的 {len(messages)} 条聊天记录")

                    # 转换消息为MessageBase格式
                    message_list = []
                    for msg in messages:
                        try:
                            # 获取发送者信息
                            sender = current_user.username if msg.sender_id == current_user.id else user.username
                            
                            # 获取消息类型和内容类型
                            message_type_result = await session.execute(
                                select(MessageTypeModel).where(MessageTypeModel.id == msg.message_type_id)
                            )
                            message_type = message_type_result.scalar_one()
                            
                            content_type_result = await session.execute(
                                select(MessageContentTypeModel).where(MessageContentTypeModel.id == msg.message_content_type_id)
                            )
                            content_type = content_type_result.scalar_one()
                            
                            # 构建消息对象
                            message_list.append(
                                MessageBase(
                                    id=msg.id,
                                    content=msg.content,
                                    recipient=user.username,
                                    sender=sender,
                                    message_type=message_type.type_code if message_type else MessageType.private_chat,
                                    message_content_type=content_type.type_code if content_type else MessageContentType.plain_text,
                                    status=msg.status,
                                    popup_message=bool(msg.popup_message),
                                    timestamp=msg.timestamp,
                                    sender_info=None,  # 这里可以根据需要添加发送者信息
                                    extra_data=json.loads(msg.extra_data) if msg.extra_data != "{}" else {}
                                )
                            )
                        except Exception as e:
                            lprint(f"转换消息失败: {str(e)}")
                    
                    user_map[user.username] = UserBaseAndStatus(
                        username=user.username,
                        nickname=user.nickname,
                        email=user.email,
                        role=user.role,
                        online_devices=online_devices,
                        total_devices=len(devices),
                        online=login_status,
                        messages=message_list
                    )
            
            # 获取当前用户的设备
            current_user_devices_result = await session.execute(
                select(Device).where(Device.user_id == current_user.id)
            )
            current_user_devices = current_user_devices_result.scalars().all()
            lprint(f"当前用户 {current_user.username} 有 {len(current_user_devices)} 个设备")
            
            # 检查当前用户的每个设备
            for device in current_user_devices:
                lprint(f"当前用户设备信息 - ID: {device.device_id}, 名称: {device.device_name}, 最后在线: {device.last_seen}, is_online标志: {device.login_status}")
                # 检查并更新设备状态
                device_online = is_device_online(device)
                await update_device_status(session, device, device_online)
            
            # 检查当前用户的在线设备
            current_user_online_devices = [
                DeviceResponse(
                    id=d.id,
                    device_id=d.device_id,
                    device_name=d.device_name,
                    device_type=d.device_type,
                    login_status=d.login_status,
                    last_seen=d.last_seen,
                    ip_address=d.ip_address,
                    user_agent=d.user_agent
                )
                for d in current_user_devices if d.login_status
            ]
            current_user_is_online = len(current_user_online_devices) > 0
            lprint(f"当前用户 {current_user.username} 在线状态: {current_user_is_online} (在线设备: {len(current_user_online_devices)})")
            
            # 构建当前用户响应
            current_user_response = UserBaseAndStatus(
                username=current_user.username,
                nickname=current_user.nickname,
                email=current_user.email,
                role=current_user.role,
                online_devices=current_user_online_devices,
                total_devices=len(current_user_devices),
                online=current_user_is_online,
                messages=[]  # 当前用户不需要显示自己的消息
            )
            
            # 提交所有设备状态更新
            await session.commit()
            
            lprint(f"返回用户映射 - {len(user_map)} 个其他用户")
            return UsersInfoDictResponse(
                current_user=current_user_response,
                user_map=user_map
            )
            
    except Exception as e:
        lprint(f"获取用户映射失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户映射失败"
        )
