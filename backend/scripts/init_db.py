"""数据库初始化脚本"""

import sys
import os
import asyncio

# 添加项目根目录到Python路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

import Lugwit_Module as LM
lprint = LM.lprint

# 导入初始化函数
from app.db.init.base import init_db

if __name__ == "__main__":
    asyncio.run(init_db())
