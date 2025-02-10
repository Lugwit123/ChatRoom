"""消息相关路由"""
from typing import List, Optional, Dict, Any, cast
from fastapi import APIRouter, Depends, HTTPException, Query, Path, WebSocket, WebSocketDisconnect, Body
from sqlalchemy.ext.asyncio import AsyncSession
import Lugwit_Module as LM

from app.db.facade.database_facade import DatabaseFacade
from app.domain.message.facade import get_message_facade
from app.domain.message.facade.message_facade import MessageFacade
from app.domain.message.facade.dto.message_dto import (
    MessageCreateDTO,
    PrivateMessageDTO,
    GroupMessageDTO,
    MessageResponse,
    MessageListResponse,
    MessageStatusUpdate,
    MessageDelete,
    MessageForward,
    MessageReactionCreate,
    MessageSearchResponse,
    MessageSearch
)
from app.domain.base.facade.dto.base_dto import ResponseDTO
from app.core.auth.facade.auth_facade import get_current_user
from app.domain.common.models.tables import User, BaseMessage

lprint = LM.lprint

router = APIRouter(
    prefix="/api/messages",
    tags=["消息管理"],
    responses={404: {"description": "Not found"}},
)

@router.post("/send_private", response_model=ResponseDTO)
async def send_private_message(
    message: MessageCreateDTO,
    current_user: User = Depends(get_current_user),
    message_facade: MessageFacade = Depends(get_message_facade)
) -> ResponseDTO:
    """发送私聊消息
    
    Args:
        message: 消息创建DTO
        current_user: 当前用户
        message_facade: 消息门面实例
        
    Returns:
        ResponseDTO: 统一响应格式
    """
    try:
        # 验证接收者
        if not message.recipient_username:
            return ResponseDTO.error(message="接收者用户名不能为空")
            
        if message.recipient_username == str(current_user.username):
            return ResponseDTO.error(message="不能给自己发送消息")
            
        # 发送消息
        return await message_facade.send_message(**message.to_internal(str(current_user.username)))
        
    except Exception as e:
        lprint(f"发送私聊消息失败: {str(e)}")
        return ResponseDTO.error(message=f"发送私聊消息失败: {str(e)}")

@router.post("/send_group", response_model=ResponseDTO)
async def send_group_message(
    message: MessageCreateDTO,
    current_user: User = Depends(get_current_user),
    message_facade: MessageFacade = Depends(get_message_facade)
) -> ResponseDTO:
    """发送群组消息
    
    Args:
        message: 消息创建DTO
        current_user: 当前用户
        message_facade: 消息门面实例
        
    Returns:
        ResponseDTO: 统一响应格式
    """
    try:
        # 验证群组名称
        if not message.group_name:
            return ResponseDTO.error(message="群组名称不能为空")
            
        # 发送消息
        return await message_facade.send_message(**message.to_internal(str(current_user.username)))
        
    except Exception as e:
        lprint(f"发送群组消息失败: {str(e)}")
        return ResponseDTO.error(message=f"发送群组消息失败: {str(e)}")

@router.get("", response_model=MessageListResponse)
async def get_messages(
    chat_with: Optional[str] = Query(None, description="私聊对象ID"),
    group_id: Optional[int] = Query(None, description="群组ID"),
    before: Optional[str] = Query(None, description="获取此消息之前的消息"),
    limit: int = Query(20, ge=1, le=50, description="返回结果数量限制"),
    current_user: User = Depends(get_current_user),
    message_facade: MessageFacade = Depends(get_message_facade)
) -> MessageListResponse:
    """获取消息列表
    
    Args:
        chat_with: 私聊对象ID
        group_id: 群组ID
        before: 获取此消息之前的消息
        limit: 返回结果数量限制
        current_user: 当前用户
        message_facade: 消息门面实例
        
    Returns:
        MessageListResponse: 消息列表响应
    """
    try:
        # 获取用户ID
        user_id = getattr(current_user, 'id', None)
        if user_id is None:
            raise ValueError("无效的用户ID")
            
        # 获取消息列表
        messages = await message_facade.get_messages(
            user_id=int(user_id),
            group_id=group_id
        )
        
        # 转换消息为响应格式
        response_messages = []
        for msg in messages:
            if isinstance(msg, BaseMessage):
                if msg.group_id is not None:
                    response_messages.append(GroupMessageDTO.from_db(msg))
                else:
                    response_messages.append(PrivateMessageDTO.from_db(msg))
        
        return MessageListResponse(
            messages=response_messages,
            has_more=len(messages) >= limit,
            next_cursor=str(messages[-1].id) if messages else None,
            unread_count=0  # TODO: 实现未读消息计数
        )
    except Exception as e:
        lprint(f"获取消息列表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{message_id}/read", response_model=ResponseDTO)
async def mark_message_as_read(
    message_id: int = Path(..., description="消息ID"),
    current_user: User = Depends(get_current_user),
    message_facade: MessageFacade = Depends(get_message_facade)
) -> ResponseDTO:
    """标记消息为已读
    
    Args:
        message_id: 消息ID
        current_user: 当前用户
        message_facade: 消息门面实例
        
    Returns:
        ResponseDTO: 统一响应格式
    """
    try:
        # 获取用户ID
        user_id = getattr(current_user, 'id', None)
        if user_id is None:
            raise ValueError("无效的用户ID")
            
        # 标记消息为已读
        success = await message_facade.mark_as_read(
            message_id=message_id,
            user_id=int(user_id)
        )
        
        if success:
            return ResponseDTO.success(message="消息已标记为已读")
        return ResponseDTO.error(message="标记消息已读失败")
    except Exception as e:
        lprint(f"标记消息已读失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{message_id}/status", response_model=ResponseDTO)
async def update_message_status(
    message_id: int = Path(..., description="消息ID"),
    status_update: MessageStatusUpdate = Body(..., description="状态更新数据"),
    current_user: User = Depends(get_current_user),
    message_facade: MessageFacade = Depends(get_message_facade)
) -> ResponseDTO:
    """更新消息状态
    
    Args:
        message_id: 消息ID
        status_update: 状态更新DTO
        current_user: 当前用户
        message_facade: 消息门面实例
        
    Returns:
        ResponseDTO: 统一响应格式
    """
    try:
        if status_update.status == "read":
            success = await message_facade.mark_as_read(
                message_id=message_id,
                user_id=int(getattr(current_user, 'id', 0))
            )
            if success:
                return ResponseDTO.success(message="消息已标记为已读")
            return ResponseDTO.error(message="标记消息已读失败")
        else:
            return ResponseDTO.error(message=f"不支持的状态: {status_update.status}")
    except Exception as e:
        lprint(f"更新消息状态失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{message_id}", response_model=ResponseDTO)
async def delete_message(
    message_id: str,
    delete_request: MessageDelete,
    current_user: User = Depends(get_current_user),
    message_facade: MessageFacade = Depends(get_message_facade)
) -> ResponseDTO:
    """删除消息
    
    Args:
        message_id: 消息ID
        delete_request: 删除请求DTO
        current_user: 当前用户
        message_facade: 消息门面实例
        
    Returns:
        ResponseDTO: 统一响应格式
    """
    try:
        success = await message_facade.delete_message(
            message_id=message_id,
            user_id=int(getattr(current_user, 'id', 0)),
            delete_for_all=delete_request.delete_for_all
        )
        if success:
            return ResponseDTO.success(message="消息已删除")
        return ResponseDTO.error(message="删除消息失败")
    except Exception as e:
        lprint(f"删除消息失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/forward", response_model=ResponseDTO)
async def forward_messages(
    forward_request: MessageForward,
    current_user: User = Depends(get_current_user),
    message_facade: MessageFacade = Depends(get_message_facade)
) -> ResponseDTO:
    """转发消息
    
    Args:
        forward_request: 转发请求DTO
        current_user: 当前用户
        message_facade: 消息门面实例
        
    Returns:
        ResponseDTO: 统一响应格式
    """
    try:
        success = await message_facade.forward_messages(
            message_ids=forward_request.message_ids,
            target_type=forward_request.target_type,
            target_id=forward_request.target_id,
            user_id=int(getattr(current_user, 'id', 0))
        )
        if success:
            return ResponseDTO.success(message="消息已转发")
        return ResponseDTO.error(message="转发消息失败")
    except Exception as e:
        lprint(f"转发消息失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{message_id}/reactions", response_model=ResponseDTO)
async def add_reaction(
    message_id: str,
    reaction: MessageReactionCreate,
    current_user: User = Depends(get_current_user),
    message_facade: MessageFacade = Depends(get_message_facade)
) -> ResponseDTO:
    """添加消息表情回应
    
    Args:
        message_id: 消息ID
        reaction: 表情回应DTO
        current_user: 当前用户
        message_facade: 消息门面实例
        
    Returns:
        ResponseDTO: 统一响应格式
    """
    try:
        success = await message_facade.add_reaction(
            message_id=message_id,
            emoji=reaction.emoji,
            user_id=int(getattr(current_user, 'id', 0))
        )
        if success:
            return ResponseDTO.success(message="表情回应已添加")
        return ResponseDTO.error(message="添加表情回应失败")
    except Exception as e:
        lprint(f"添加表情回应失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{message_id}/reactions/{reaction}", response_model=ResponseDTO)
async def remove_reaction(
    message_id: str,
    reaction: str,
    current_user: User = Depends(get_current_user),
    message_facade: MessageFacade = Depends(get_message_facade)
) -> ResponseDTO:
    """移除消息表情回应
    
    Args:
        message_id: 消息ID
        reaction: 表情符号
        current_user: 当前用户
        message_facade: 消息门面实例
        
    Returns:
        ResponseDTO: 统一响应格式
    """
    try:
        success = await message_facade.remove_reaction(
            message_id=message_id,
            emoji=reaction,
            user_id=int(getattr(current_user, 'id', 0))
        )
        if success:
            return ResponseDTO.success(message="表情回应已移除")
        return ResponseDTO.error(message="移除表情回应失败")
    except Exception as e:
        lprint(f"移除表情回应失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/search", response_model=MessageSearchResponse)
async def search_messages(
    search_request: MessageSearch,
    current_user: User = Depends(get_current_user),
    message_facade: MessageFacade = Depends(get_message_facade)
) -> MessageSearchResponse:
    """搜索消息
    
    Args:
        search_request: 搜索请求DTO
        current_user: 当前用户
        message_facade: 消息门面实例
        
    Returns:
        MessageSearchResponse: 搜索结果响应
    """
    try:
        return await message_facade.search_messages(
            query=search_request.query,
            user_id=int(getattr(current_user, 'id', 0)),
            chat_with=search_request.chat_with,
            group_id=search_request.group_id,
            before=search_request.before,
            after=search_request.after,
            limit=search_request.limit
        )
    except Exception as e:
        lprint(f"搜索消息失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/unread/count", response_model=Dict[str, int])
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    message_facade: MessageFacade = Depends(get_message_facade)
) -> Dict[str, int]:
    """获取未读消息数量
    
    Args:
        current_user: 当前用户
        message_facade: 消息门面实例
        
    Returns:
        Dict[str, int]: 未读消息数量
    """
    try:
        count = await message_facade.get_unread_count(
            user_id=int(getattr(current_user, 'id', 0))
        )
        return {"count": count}
    except Exception as e:
        lprint(f"获取未读消息数量失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    message_facade: MessageFacade = Depends(get_message_facade)
):
    """WebSocket连接"""
    try:
        # 验证token
        user = await get_current_user(token)
        if not user:
            await websocket.close(code=4001)
            return
            
        # 接受连接
        await websocket.accept()
        
        # 使用基础门面的sio
        if message_facade.sio:
            # 使用客户端ID作为sid
            sid = str(id(websocket))  # 使用websocket对象的id作为唯一标识
            await message_facade.sio.emit('connection_established', {'user_id': user.id}, room=sid)
            
            try:
                while True:
                    data = await websocket.receive_json()
                    await message_facade.handle_message(sid, data)
            except WebSocketDisconnect:
                if message_facade.sio:
                    await message_facade.sio.emit('user_disconnected', {'user_id': user.id}, room=sid)
                    
    except Exception as e:
        lprint(f"WebSocket连接失败: {str(e)}")
        await websocket.close(code=4000)
