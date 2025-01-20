from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path
import Lugwit_Module as LM

lprint = LM.lprint
router = APIRouter()

# 获取当前文件所在目录
cur_dir = Path(__file__).resolve().parent  # 返回到项目根目录

# 设置 Jinja2 模板目录
templates = Jinja2Templates(directory=str(cur_dir / "templates"))

@router.get("/files/{path:path}")
async def file_server(request: Request, path: str = ""):
    """
    文件服务器路由，支持文件和目录浏览
    """
    # 获取当前工作目录
    server_root = os.path.abspath(os.getcwd())
    # 将用户提供的路径与根目录拼接，并规范化路径
    safe_path = os.path.normpath(os.path.join(server_root, path))
    
    # 确保文件在服务器根目录下，防止目录遍历攻击
    if not os.path.commonpath([server_root, safe_path]).startswith(server_root):
        raise HTTPException(status_code=400, detail="Invalid file path")

    # 检查路径是否存在
    if os.path.exists(safe_path):
        if os.path.isfile(safe_path):
            # 如果是文件，返回文件响应
            return FileResponse(safe_path)
        elif os.path.isdir(safe_path):
            # 如果是目录，生成目录中的文件和子目录的链接列表
            items = os.listdir(safe_path)
            links = []
            for item in items:
                item_path = os.path.join(path, item).replace("\\", "/")
                if os.path.isdir(os.path.join(safe_path, item)):
                    # 目录图标
                    icon = "📁"
                else:
                    # 文件图标
                    icon = "📄"
                links.append(f'<li>{icon} <a href="/files/{item_path}">{item}</a></li>')
            links_html = "<ul>" + "\n".join(links) + "</ul>"
            return HTMLResponse(content=f"<html><body>{links_html}</body></html>")
    else:
        return templates.TemplateResponse("reviews.html", {"request": request, "message": "File or directory not found"})

@router.get("/files_server")
def file_server_old(request: Request, path: str = ""):
    """
    旧版文件服务器路由，保留兼容性
    """
    # 获取当前工作目录
    server_root = os.path.abspath(os.getcwd())
    # 将用户提供的路径与根目录拼接，并规范化路径
    safe_path = os.path.normpath(os.path.join(server_root, path))
    
    # 确保文件在服务器根目录下，防止目录遍历攻击
    if not safe_path.startswith(server_root):
        lprint(safe_path, server_root)
        raise HTTPException(status_code=400, detail="Invalid file path")
        
    # 检查路径是否存在
    if os.path.exists(safe_path):
        if os.path.isfile(safe_path):
            # 如果是文件，返回文件响应
            return FileResponse(safe_path)
        elif os.path.isdir(safe_path):
            # 如果是目录，生成目录中的文件和子目录的链接列表
            items = os.listdir(safe_path)
            links = []
            for item in items:
                if os.path.isdir(os.path.join(safe_path, item)):
                    # 目录图标
                    icon = "📁"
                else:
                    # 文件图标
                    icon = "📄"
                link = f'<li>{icon} <a href="/files_server?path={os.path.join(path, item)}">{item}</a></li>'
                links.append(link)
            links_html = "<ul>" + "\n".join(links) + "</ul>"
            return HTMLResponse(content=f"<html><body>{links_html}</body></html>")
    else:
        return templates.TemplateResponse("reviews.html", {"request": request, "message": "File or directory not found"})
