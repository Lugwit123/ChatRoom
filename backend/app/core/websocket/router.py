"""WebSocket路由模块"""
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from app.core.auth.facade.auth_facade import get_current_user
from app.domain.common.models.tables import User
from app.core.websocket.facade.websocket_facade import WebSocketFacade
import Lugwit_Module as LM

lprint = LM.lprint

router = APIRouter(
    prefix="/websocket",
    tags=["WebSocket"],
    responses={404: {"description": "Not found"}},
)

@router.get("/metrics", response_class=PlainTextResponse)
async def get_metrics(current_user: User = Depends(get_current_user)):
    """获取WebSocket指标(Prometheus格式)"""
    try:
        facade = WebSocketFacade()
        metrics = await facade.get_metrics()
        return metrics
        
    except Exception as e:
        lprint(f"获取指标失败: {str(e)}")
        return "# Error collecting metrics"

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
    """获取WebSocket统计信息"""
    try:
        facade = WebSocketFacade()
        return await facade.get_stats()
        
    except Exception as e:
        lprint(f"获取统计信息失败: {str(e)}")
        return {"error": str(e)} 