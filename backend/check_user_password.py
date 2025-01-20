import asyncio
import sys
sys.path.append(r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib')
import Lugwit_Module as LM
lprint = LM.lprint

from app.db.database import AsyncSessionLocal
from app.domain.user.repository import UserRepository
from app.utils.security import get_password_hash, verify_password

async def check_user():
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get_by_username('admin01')
        if user:
            lprint(f'用户名: {user.username}')
            lprint(f'密码哈希: {user.hashed_password}')
            
            # 生成新的密码哈希用于比较
            test_hash = get_password_hash('666')
            lprint(f'测试密码哈希: {test_hash}')
            
            # 验证密码
            is_valid = verify_password('666', user.hashed_password)
            lprint(f'密码验证结果: {is_valid}')
        else:
            lprint('用户不存在')

if __name__ == '__main__':
    asyncio.run(check_user())
