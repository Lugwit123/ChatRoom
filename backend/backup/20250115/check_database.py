"""数据库检查脚本"""
import os
import asyncio
import sys
import traceback
import Lugwit_Module as LM
from app.db.database import async_session
from app.db.init.check_tables import check_tables, check_group_tables
from app.utils.encoding_utils import setup_encoding, print_encoding_info


lprint = LM.lprint

async def check_database():
    """检查数据库状态"""
    try:
        # 设置编码
        setup_encoding()
        print_encoding_info()
        
        # 设置日志
        setup_logging()
        
        lprint("开始检查数据库状态...")
        
        async with async_session() as session:
            # 1. 检查所有表
            await check_tables(session)
            
            # 2. 检查群组消息表
            await check_group_tables(session)
        
        lprint("数据库状态检查完成")
    except Exception as e:
        lprint(f"数据库状态检查失败: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    # 如果提供了群组ID参数,则只检查该群组的消息表
    if len(sys.argv) > 1:
        try:
            group_id = int(sys.argv[1])
            asyncio.run(check_group_tables(group_id))
        except ValueError:
            lprint(f"无效的群组ID: {sys.argv[1]}")
    else:
        # 否则检查所有表
        asyncio.run(check_database())
