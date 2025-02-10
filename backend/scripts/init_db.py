"""数据库初始化脚本"""

import sys
import os
import asyncio
import time
import traceback
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # backend目录
sys.path.append(PROJECT_ROOT)

import Lugwit_Module as LM
lprint = LM.lprint

# 导入初始化函数
from app.db.init.base import init_db

async def main():
    max_retries = 3
    retry_delay = 2  # 秒
    
    for attempt in range(max_retries):
        try:
            # 加载环境变量
            env_file = Path(PROJECT_ROOT) / ".env"
            if not env_file.exists():
                lprint(f"[错误] 环境配置文件不存在: {env_file}")
                return
            load_dotenv(env_file)
            
            # 检查数据库URL
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                lprint("[错误] 数据库连接URL未设置")
                return
            lprint(f"[信息] 使用数据库连接: {database_url}")
            
            # 初始化数据库
            success = await init_db()
            if success:
                lprint("[成功] 数据库初始化完成")
                return
            else:
                lprint(f"[警告] 数据库初始化失败，尝试次数: {attempt + 1}/{max_retries}")
                
        except Exception as e:
            error_msg = str(e)
            tb = traceback.format_exc()
            lprint(f"[错误] 数据库初始化失败: {error_msg}")
            lprint(f"[错误] 详细错误信息:\n{tb}")
            
            if attempt < max_retries - 1:
                lprint(f"[信息] 等待 {retry_delay} 秒后重试...")
                await asyncio.sleep(retry_delay)
            else:
                lprint("[错误] 已达到最大重试次数，初始化失败")
                raise

if __name__ == "__main__":
    asyncio.run(main())
