# routers/check_file/config.py
from pathlib import Path
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# 加载环境变量（如果需要）
load_dotenv()

# 获取当前文件所在目录
cur_dir = Path(__file__).resolve().parent.parent.parent  # 返回到项目根目录

# 基础路径，确保这个路径存在并且可访问
BASE_PATH = Path(os.getenv("BASE_PATH", "G:/"))
ABC_CHECK_DATA_DIR = Path('B:/TD/fileCheck/')
# 设置 Jinja2 模板目录
templates = Jinja2Templates(directory=str(cur_dir / "templates"))

def add_check_file_static(app: FastAPI):
    """添加检查文件相关的静态文件路由"""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/check_file/static", StaticFiles(directory=static_dir), name="check_file_static")
