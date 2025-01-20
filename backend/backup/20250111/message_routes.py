from typing import Dict, List
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException
import sqlalchemy as sa

import schemas
import user_database
from dependencies import get_current_user_db as get_current_user
import Lugwit_Module as LM
lprint=LM.lprint
router = APIRouter()

def parse_indices(index_string):
    """
    将索引字符串解析为列表。
    支持切片格式 [start:end] 和单独的索引值。
    
    参数:
        index_string (str): 索引字符串，例如 "[1:10,4,5]"
        
    返回:
        list: 包含所有解析的索引值
    """
    import re
    
    # 移除括号
    index_string = index_string.strip("[]")
    
    indices = []
    parts = index_string.split(",")
    
    for part in parts:
        if ":" in part:  # 处理切片
            start, end = map(str.strip, part.split(":"))
            start = int(start) if start else 0  # 默认为 0
            end = int(end)  # 切片需要结束值
            indices.extend(range(start, end))
        else:  # 处理单个值
            indices.append(int(part.strip()))
    
    return indices

@router.delete("/delete_messages", response_model=Dict[str, bool])
async def delete_messages(
    request: schemas.DeleteMessagesRequest,
    current_user: schemas.UserBase = Depends(get_current_user)
) -> Dict[str, bool]:
    """
    删除指定的消息：
    1. 通过message_ids列表指定具体的消息ID,使用切边的形式,比如[1:10,4,5]
    """
    lprint(locals())
    try:
        # 收集所有要删除的消息ID
        all_message_ids = set()
        
        # 添加具体的消息ID
        if request.message_ids:
            all_message_ids.update(set(request.message_ids))
        # 转换为列表
        message_ids = list(all_message_ids)
        lprint(message_ids)
        # 验证权限
        is_admin = await user_database.is_user_admin(current_user.username)
        if not is_admin:
            # 非管理员只能删除自己发送的消息
            # 先获取所有要删除的消息
            async with user_database.async_session() as session:
                messages_stmt = sa.select(user_database.Message).where(
                    user_database.Message.id.in_(message_ids)
                )
                result = await session.execute(messages_stmt)
                messages = result.scalars().all()
                
                # 检查是否都是自己发送的消息
                for message in messages:
                    if message.sender != current_user.username:
                        raise HTTPException(
                            status_code=403,
                            detail="你只能删除自己发送的消息"
                        )

        # 执行删除操作
        success = await user_database.delete_messages(message_ids)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="删除消息失败，可能是消息不存在"
            )

        return {"success": True}

    except HTTPException as e:
        raise traceback.format_exc()
    except Exception as e:
        logging.error(f"删除消息时出错: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail="删除消息时发生错误"
        )
