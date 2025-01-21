"""
消息路由模块
定义所有与消息相关的API路由，包括消息的发送、接收、查询等功能
"""
from fastapi import APIRouter, Depends
from ..facade.message_facade import MessageFacade
from ..facade.dto.message_dto import MessageCreateDTO

# 创建路由器并添加标签
router = APIRouter(
    prefix="/api/messages",
    tags=["消息管理"],
    responses={404: {"description": "未找到"}}
)

message_facade = MessageFacade()

@router.post("/send", 
    summary="发送消息",
    description="发送消息到指定用户或群组",
    response_description="消息发送结果")
async def send_message(message: MessageCreateDTO):
    """
    发送消息API
    
    Args:
        message: 消息创建DTO
        
    Returns:
        ResponseDTO: 包含发送结果的响应
    """
    return await message_facade.send_message(message)

@router.post("/send/legacy",
    summary="发送消息(旧版)",
    description="原有的消息发送接口，保留用于兼容",
    deprecated=True)
async def send_message_legacy(message: dict):
    """
    旧版发送消息API（已废弃）
    保留用于向后兼容
    """
    # 原有实现
    pass
