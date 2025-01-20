from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import Lugwit_Module as LM

lprint = LM.lprint

abc_router = APIRouter()
templates = Jinja2Templates(directory="templates")

def add_check_file_static(app):
    """添加静态文件挂载点"""
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@abc_router.get("/check_file/{check_id}", response_class=HTMLResponse)
async def check_file(request: Request, check_id: str):
    """检查文件页面"""
    try:
        return templates.TemplateResponse(
            "check_file.html",
            {"request": request, "check_id": check_id}
        )
    except Exception as e:
        lprint(f"检查文件页面出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@abc_router.get("/check_file_result/{check_id}")
async def get_check_file_result(check_id: str):
    """获取文件检查结果"""
    try:
        # 这里应该从数据库或其他存储中获取检查结果
        # 为了示例，我们返回一个模拟的结果
        return {
            "check_id": check_id,
            "status": "completed",
            "result": "文件检查通过"
        }
    except Exception as e:
        lprint(f"获取文件检查结果出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
