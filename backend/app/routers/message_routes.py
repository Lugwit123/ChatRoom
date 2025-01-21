"""
消息相关的路由
"""
from typing import Dict, Any, List, Optional
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException
import sqlalchemy as sa
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.db.schemas as schemas
from app.core.auth import get_current_user
from app.db.db_connection import async_session
import Lugwit_Module as LM

lprint = LM.lprint
router = APIRouter(prefix="/api/messages", tags=["消息管理"])

# ============================
# 私聊消息路由
# ============================

@router.get("/private", response_model=List[Dict[str, Any]])
async def get_private_messages(
    sender: str,
    recipient: str,
    limit: int = 50,
    before_id: Optional[int] = None,
    after_id: Optional[int] = None,
    current_user: schemas.UserBase = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """获取私聊消息历史
    
    Args:
        sender: 发送者用户名
        recipient: 接收者用户名
        limit: 返回的最大消息数量
        before_id: 获取ID小于此值的消息（向前翻页）
        after_id: 获取ID大于此值的消息（向后翻页）
        current_user: 当前登录用户
    """
    try:
        lprint(f"[开始] 获取私聊消息 - 发送者: {sender}, 接收者: {recipient}, 限制: {limit}, before_id: {before_id}, after_id: {after_id}")
        
        # 验证权限
        if current_user.username not in [sender, recipient]:
            lprint(f"[错误] 权限不足 - 当前用户: {current_user.username}")
            raise HTTPException(
                status_code=403,
                detail="没有权限查看这些消息"
            )
            
        async with async_session() as session:
            # 构建查询
            stmt = text("""
                SELECT id, content, sender_id, recipient, timestamp, 
                       status, message_type_id, message_content_type_id
                FROM private_messages
                WHERE (sender_id = :sender AND recipient = :recipient)
                   OR (sender_id = :recipient AND recipient = :sender)
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            
            # 执行查询
            lprint("[Step 1] 执行私聊消息查询...")
            result = await session.execute(
                stmt,
                {
                    "sender": sender,
                    "recipient": recipient,
                    "limit": limit
                }
            )
            messages = result.fetchall()
            lprint(f"[成功] 查询完成 - 获取到 {len(messages)} 条消息")
            
            # 转换为字典列表
            lprint("[Step 2] 开始处理消息数据...")
            message_list = []
            for i, msg in enumerate(messages, 1):
                try:
                    message_dict = {
                        "id": msg.id,
                        "content": msg.content,
                        "sender": msg.sender_id,
                        "recipient": msg.recipient,
                        "timestamp": msg.timestamp.isoformat(),
                        "status": msg.status,
                        "message_type": msg.message_type_id,
                        "message_content_type": msg.message_content_type_id
                    }
                    message_list.append(message_dict)
                    lprint(f"[处理] 消息 {i}/{len(messages)} - ID: {msg.id}, 发送者: {msg.sender_id}")
                except Exception as msg_err:
                    lprint(f"[警告] 处理消息 {i} 时出错: {str(msg_err)}")
                    lprint(f"消息原始数据: {msg}")
                    continue
                
            lprint(f"[完成] 成功处理 {len(message_list)}/{len(messages)} 条消息")
            return message_list
            
    except Exception as e:
        lprint(f"[严重错误] 获取私聊消息失败: {str(e)}")
        lprint("详细错误信息:")
        lprint(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"获取消息失败: {str(e)}"
        )

# ============================
# 群聊消息路由
# ============================

@router.get("/group/{group_name}", response_model=List[Dict[str, Any]])
async def get_group_messages(
    group_name: str,
    limit: int = 50,
    current_user: schemas.UserBase = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """获取群聊消息历史
    
    Args:
        group_name: 群组名称
        limit: 返回的最大消息数量
        current_user: 当前登录用户
    """
    try:
        lprint(f"[开始] 获取群聊消息 - 群组: {group_name}, 限制: {limit}, 当前用户: {current_user.username}")
        
        async with async_session() as session:
            # 获取群组信息
            lprint(f"[Step 1] 查询群组信息 - 群组名: {group_name}")
            group_stmt = select(schemas.Group).where(
                schemas.Group.name == group_name
            )
            group_result = await session.execute(group_stmt)
            group = group_result.scalar_one_or_none()
            
            if not group:
                lprint(f"[错误] 找不到群组: {group_name}")
                raise HTTPException(
                    status_code=404,
                    detail=f"找不到群组: {group_name}"
                )
            
            lprint(f"[成功] 找到群组 - ID: {group.id}, 名称: {group.name}, 成员数: {len(group.members)}")
                
            # 验证用户是否在群组中或是管理员
            lprint(f"[Step 2] 验证用户权限 - 用户: {current_user.username}")
            
            # 检查用户是否是管理员
            user_stmt = select(schemas.User).where(
                schemas.User.username == current_user.username
            )
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            is_admin = user and user.role == schemas.UserRole.admin
            lprint(f"[权限] 用户角色: {user.role if user else 'unknown'}, 是否管理员: {is_admin}")
            
            if not is_admin and current_user.username not in group.members:
                lprint(f"[错误] 用户不在群组中且不是管理员 - 用户: {current_user.username}, 群组: {group_name}")
                lprint(f"群组成员列表: {group.members}")
                raise HTTPException(
                    status_code=403,
                    detail="没有权限查看群组消息"
                )
            lprint(f"[成功] 用户权限验证通过 - {'管理员权限' if is_admin else '群组成员'}")
            
            # 获取群组消息表名
            table_name = schemas.get_group_message_table_name(group_name)
            lprint(f"[Step 3] 准备查询消息 - 表名: {table_name}")
            
            # 构建查询
            stmt = text(f"""
                SELECT id, content, sender_id, timestamp, 
                       status, message_type_id, message_content_type_id,
                       group_name, popup_message, extra_data
                FROM {table_name}
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            lprint(f"[SQL] 查询语句: {stmt}")
            lprint(f"[SQL] 参数: limit={limit}")
            
            # 执行查询
            lprint("[Step 4] 执行消息查询...")
            result = await session.execute(stmt, {"limit": limit})
            messages = result.fetchall()
            lprint(f"[成功] 查询完成 - 获取到 {len(messages)} 条消息")
            
            # 转换为字典列表
            message_list = []
            for i, msg in enumerate(messages, 1):
                try:
                    message_dict = {
                        "id": msg.id,
                        "content": msg.content,
                        "sender": msg.sender_id,
                        "group_name": msg.group_name,
                        "timestamp": msg.timestamp.isoformat(),
                        "status": msg.status,
                        "message_type": msg.message_type_id,
                        "message_content_type": msg.message_content_type_id,
                        "popup_message": msg.popup_message,
                        "extra_data": msg.extra_data
                    }
                    message_list.append(message_dict)
                    lprint(f"[处理] 消息 {i}/{len(messages)} - ID: {msg.id}, 发送者: {msg.sender_id}")
                except Exception as msg_err:
                    lprint(f"[警告] 处理消息 {i} 时出错: {str(msg_err)}")
                    lprint(f"消息原始数据: {msg}")
                    continue
            
            lprint(f"[完成] 成功处理 {len(message_list)}/{len(messages)} 条消息")
            return message_list
            
    except Exception as e:
        lprint(f"[严重错误] 获取群聊消息失败: {str(e)}")
        lprint("详细错误信息:")
        lprint(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"获取消息失败: {str(e)}"
        )

# ============================
# 消息管理路由
# ============================

@router.post("/delete")
async def delete_messages(
    request: schemas.DeleteMessagesRequest,
    current_user: schemas.UserBase = Depends(get_current_user)
):
    """删除指定的消息
    
    Args:
        request: 删除消息请求
        current_user: 当前登录用户
    """
    try:
        lprint(f"[开始] 删除消息 - 用户: {current_user.username}")
        
        async with async_session() as session:
            # 验证用户权限
            user_stmt = select(schemas.User).where(
                schemas.User.username == current_user.username
            )
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="用户不存在"
                )
                
            is_admin = user.role == schemas.UserRole.admin
            
            # 根据消息类型执行删除
            if request.message_type == "private":
                # 构建删除语句
                stmt = text("""
                    DELETE FROM private_messages
                    WHERE id = :message_id
                    AND (sender_id = :user_id OR recipient = :username OR :is_admin)
                """)
                
                # 执行删除
                result = await session.execute(
                    stmt,
                    {
                        "message_id": request.message_id,
                        "user_id": user.id,
                        "username": user.username,
                        "is_admin": is_admin
                    }
                )
                
            elif request.message_type == "group":
                if not request.group_name:
                    raise HTTPException(
                        status_code=400,
                        detail="删除群消息时必须指定群组名称"
                    )
                    
                # 获取群组信息
                group_stmt = select(schemas.Group).where(
                    schemas.Group.name == request.group_name
                )
                group_result = await session.execute(group_stmt)
                group = group_result.scalar_one_or_none()
                
                if not group:
                    raise HTTPException(
                        status_code=404,
                        detail=f"找不到群组: {request.group_name}"
                    )
                
                # 验证权限
                if not is_admin and current_user.username not in group.members:
                    raise HTTPException(
                        status_code=403,
                        detail="没有权限删除群组消息"
                    )
                
                # 获取群组消息表名
                table_name = schemas.get_group_message_table_name(request.group_name)
                
                # 构建删除语句
                stmt = text(f"""
                    DELETE FROM {table_name}
                    WHERE id = :message_id
                    AND (sender_id = :user_id OR :is_admin)
                """)
                
                # 执行删除
                result = await session.execute(
                    stmt,
                    {
                        "message_id": request.message_id,
                        "user_id": user.id,
                        "is_admin": is_admin
                    }
                )
            
            await session.commit()
            lprint("[完成] 消息删除成功")
            
            return {"status": "success", "message": "消息已删除"}
            
    except Exception as e:
        lprint(f"[严重错误] 删除消息失败: {str(e)}")
        lprint("详细错误信息:")
        lprint(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"删除消息失败: {str(e)}"
        )
