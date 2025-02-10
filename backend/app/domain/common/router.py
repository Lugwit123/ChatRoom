"""公共路由模块，提供枚举值等基础数据的API"""
from fastapi import APIRouter
from typing import Dict, Any

from app.domain.common.enums.message import get_all_enums as get_message_enums
from app.domain.common.enums.user import get_all_enums as get_user_enums
from app.domain.common.enums.group import get_all_enums as get_group_enums

router = APIRouter(
    prefix="/api/enums",
    tags=["枚举值"],
    responses={404: {"description": "Not found"}},
)

@router.get("/message")
async def get_message_enum_values() -> Dict[str, Dict[str, Any]]:
    """获取消息相关的所有枚举值定义"""
    return get_message_enums()

@router.get("/user")
async def get_user_enum_values() -> Dict[str, Dict[str, Any]]:
    """获取用户相关的所有枚举值定义"""
    return get_user_enums()

@router.get("/group")
async def get_group_enum_values() -> Dict[str, Dict[str, Any]]:
    """获取群组相关的所有枚举值定义"""
    return get_group_enums()

@router.get("")
async def get_all_enum_values() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """获取所有枚举值定义"""
    return {
        "message": get_message_enums(),
        "user": get_user_enums(),
        "group": get_group_enums()
    } 