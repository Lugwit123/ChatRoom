"""消息相关路由定义"""
from typing import Optional, List, Union
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import get_current_user, authenticate_token
from app.db import DatabaseManager
from app.domain.message.repositories import PrivateMessageRepository, GroupMessageRepository
from app.domain.group.repository import GroupRepository, GroupMemberRepository
from app.domain.user.repository import UserRepository
from .service import MessageService
from .schemas import (
    MessageCreate,
    MessageStatusUpdate,
    MessageDelete,
    MessageForward,
    MessageReactionCreate,
    MessageSearch,
    MessageListResponse,
    MessageSearchResponse,
    PrivateMessageResponse,
    GroupMessageResponse
)

router = APIRouter(prefix="/messages", tags=["messages"])

async def get_message_service():
    """获取消息服务"""
    session = DatabaseManager.get_session()
    try:
        private_repo = PrivateMessageRepository(session)
        group_repo = GroupMessageRepository(session)
        group_repository = GroupRepository(session)
        user_repo = UserRepository(session)
        member_repo = GroupMemberRepository(session)
        yield MessageService(
            private_repo=private_repo,
            group_repo=group_repo,
            group_repository=group_repository,
            user_repo=user_repo,
            member_repo=member_repo
        )
    finally:
        await session.close()

@router.post("/send", response_model=Union[PrivateMessageResponse, GroupMessageResponse])
async def send_message(
    message: MessageCreate,
    current_user: str = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    """发送消息
    
    支持发送私聊消息和群组消息
    """
    try:
        return await message_service.create_message(message, current_user)
    except Exception as e:
        lprint(f"发送消息失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=MessageListResponse)
async def get_messages(
    before: Optional[str] = Query(None, description="获取此消息ID之前的消息"),
    chat_with: Optional[str] = Query(None, description="私聊对象的用户ID"),
    group_id: Optional[str] = Query(None, description="群组ID"),
    limit: int = Query(50, ge=1, le=100),
    current_user: str = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    """获取消息列表
    
    支持获取私聊历史或群聊历史，使用 cursor 分页
    """
    try:
        return await message_service.get_messages(
            current_user,
            chat_with=chat_with,
            group_id=group_id,
            before=before,
            limit=limit
        )
    except Exception as e:
        lprint(f"获取消息列表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{message_id}/status", response_model=dict)
async def update_message_status(
    message_id: str,
    status_update: MessageStatusUpdate,
    current_user: str = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    """更新消息状态
    
    用于标记消息为已读/已送达
    """
    try:
        await message_service.update_status(message_id, status_update, current_user)
        return {"message": "状态更新成功"}
    except Exception as e:
        lprint(f"更新消息状态失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{message_id}", response_model=dict)
async def delete_message(
    message_id: str,
    delete_request: MessageDelete,
    current_user: str = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    """删除（撤回）消息
    
    可以选择为自己删除或为所有人删除
    """
    try:
        await message_service.delete_message(message_id, delete_request, current_user)
        return {"message": "消息已删除"}
    except Exception as e:
        lprint(f"删除消息失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/forward", response_model=dict)
async def forward_messages(
    forward_request: MessageForward,
    current_user: str = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    """转发消息
    
    支持批量转发到私聊或群聊
    """
    try:
        await message_service.forward_messages(forward_request, current_user)
        return {"message": "消息已转发"}
    except Exception as e:
        lprint(f"转发消息失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{message_id}/reactions", response_model=dict)
async def add_reaction(
    message_id: str,
    reaction: MessageReactionCreate,
    current_user: str = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    """添加消息表情回应"""
    try:
        await message_service.add_reaction(message_id, reaction, current_user)
        return {"message": "表情回应已添加"}
    except Exception as e:
        lprint(f"添加表情回应失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{message_id}/reactions/{reaction}", response_model=dict)
async def remove_reaction(
    message_id: str,
    reaction: str,
    current_user: str = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    """移除消息表情回应"""
    try:
        await message_service.remove_reaction(message_id, reaction, current_user)
        return {"message": "表情回应已移除"}
    except Exception as e:
        lprint(f"移除表情回应失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/search", response_model=MessageSearchResponse)
async def search_messages(
    search_request: MessageSearch,
    current_user: str = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    """搜索消息
    
    支持在私聊或群聊中搜索，支持时间范围
    """
    try:
        return await message_service.search_messages(search_request, current_user)
    except Exception as e:
        lprint(f"搜索消息失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/unread/count", response_model=dict)
async def get_unread_count(
    current_user: str = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    """获取未读消息数量"""
    try:
        count = await message_service.get_unread_count(current_user)
        return {"count": count}
    except Exception as e:
        lprint(f"获取未读消息数量失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    message_service: MessageService = Depends(get_message_service)
):
    """WebSocket 连接
    
    用于实时接收消息更新
    """
    try:
        # 验证用户
        user = await authenticate_token(token)
        if not user:
            await websocket.close(code=4001)
            return
        
        # 等待客户端连接
        await websocket.accept()
        
        # 将连接添加到连接管理器
        await message_service.add_websocket(user.id, websocket)
        
        try:
            while True:
                # 等待消息
                data = await websocket.receive_json()
                # 处理消息
                await message_service.handle_websocket_message(user.id, data)
        except WebSocketDisconnect:
            # 客户端断开连接
            await message_service.remove_websocket(user.id)
    except Exception as e:
        lprint(f"WebSocket连接失败: {str(e)}")
        await websocket.close(code=4000)
