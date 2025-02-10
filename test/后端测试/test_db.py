import psycopg2
from sqlalchemy import create_engine, text
from Lugwit_Module import lprint

def test_db_connection():
    """测试数据库连接"""
    try:
        # 创建同步引擎
        engine = create_engine(
            "postgresql://postgres:OC.123456@192.168.110.27:5432/chatroom",
            echo=True,
            future=True,
            pool_size=5,
            max_overflow=10,
            pool_timeout=60,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            lprint(f"查询结果: {row}")
            
        lprint("数据库连接测试成功")
        return True
        
    except Exception as e:
        lprint(f"数据库连接测试失败: {e}")
        return False

if __name__ == '__main__':
    test_db_connection()
