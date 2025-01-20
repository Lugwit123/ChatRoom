# routers/check_file/abc_router.py
import json
import re
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Path as FastAPIPath, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from routers.check_file.config import BASE_PATH, templates, ABC_CHECK_DATA_DIR
from fastapi.templating import Jinja2Templates
from Lugwit_Module import lprint
# 获取脚本目录
cur_dir = Path(__file__).resolve().parent

router = APIRouter(
    prefix="/check_file",
    tags=["ABC Check"]  # 这里设置标签
)


# 正则表达式用于输入验证
VALID_INPUT_REGEX = re.compile(r'^[-\w:/\\]+$')  # 允许斜杠以支持路径
# 定义模板目录，相对于当前脚本文件所在的目录
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")



    
def validate_input(value: str) -> bool:
    return bool(VALID_INPUT_REGEX.match(value))

@router.get("/", include_in_schema=False, name="root")
async def root():
    """
    默认重定向到 /docs
    """
    return RedirectResponse(url="/docs")

@router.get("/abc_check_show/{json_file:path}", name="show_results")
async def show_results(
    json_file: str = FastAPIPath(
        ..., 
        description="JSON文件路径",
        example="ZTS/06.CFX/EP001/ep001_sc001_shot0010/ep001_sc001_shot0010_check.json"
    ),
    *,
    request: Request
):
    """
    渲染 validation_abc_cache_ani.html 并传递生成的路径
    """
    
    # 构建完整的文件路径
    file_path = ABC_CHECK_DATA_DIR / json_file
    logging.info(f"访问的文件路径: {file_path}")
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"{file_path} 文件未找到")

    # 读取 JSON 数据
    try:
        with open(file_path, "r", encoding='utf8') as f:
            json_data = json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"JSON 解码错误: {e}")
        raise HTTPException(status_code=400, detail="无效的 JSON 文件")
    SERVER_IP=os.getenv("SERVER_IP")
    # lprint(json_data,file_path)
    return templates.TemplateResponse(
        "validation_abc_cache_ani.html",
        {"request": request, 
        "json_data": json.dumps(json_data), 'json_file_path': str(file_path),
        "SERVER_IP":SERVER_IP}
    )

@router.get("/abc_check_generate_path/{project}/{ep}/{sc}/{shot}", name="generate_path")
async def generate_path(
    project: str = FastAPIPath(..., description="项目名称"),
    ep: str = FastAPIPath(..., description="EP编号"),
    sc: str = FastAPIPath(..., description="SC编号"),
    shot: str = FastAPIPath(..., description="Shot编号")
):
    """
    生成检查文件的路径
    """
    # 输入验证
    for param in [project, ep, sc, shot]:
        if not validate_input(param):
            raise HTTPException(status_code=400, detail="无效的路径参数")

    # 构建文件路径
    check_filename = f"{ep}_{sc}_{shot}{ep}_{sc}_{shot}_check.json"
    check_file = BASE_PATH / project / "06.CFX" / ep / check_filename

    if not check_file.exists():
        raise HTTPException(status_code=404, detail="检查文件未找到")

    return {"check_file": str(check_file.resolve())}

@router.get("/abc_check/{project}/{ep}", name="list_check_files")
async def list_check_files(
    project: str = FastAPIPath(..., description="项目名称", example="ZTS"),
    ep: str = FastAPIPath(..., description="EP编号", example="EP001"),
    *,
    request: Request
):
    """
    列出指定项目和 EP 下的所有 JSON 文件，并生成可点击的链接
    """
    # 输入验证
    for param in [project, ep]:
        if not validate_input(param):
            raise HTTPException(status_code=400, detail="无效的路径参数")

    base_dir = BASE_PATH / project / "06.CFX" / ep

    if not base_dir.exists() or not base_dir.is_dir():
        raise HTTPException(status_code=404, detail="项目或EP目录不存在")

    try:
        json_files = []
        for file in base_dir.rglob("*.json"):
            # 获取相对于 BASE_PATH 的路径
            relative_path = file.relative_to(BASE_PATH)
            # 生成指向 show_results 的 URL
            url = router.url_path_for("show_results", json_file=str(relative_path))
            json_files.append({"file_name": file.name, "url": url})

        return templates.TemplateResponse(
            "list_files.html",
            {"request": request, "json_files": json_files}
        )
    except Exception as e:
        logging.error(f"列出 JSON 文件时出错: {e}")
        raise HTTPException(status_code=500, detail="无法列出文件")
    
    
__all__ = ['router']
