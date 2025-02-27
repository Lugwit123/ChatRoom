"""
启动带有自动重载功能的PyQt客户端程序
"""
import os
import sys
from dotenv import load_dotenv
from modules.utils.auto_reload import start_auto_reload
import Lugwit_Module as LM

lprint = LM.lprint

def setup_environment():
    """设置环境变量和Python路径"""
    try:
        # 获取clientend目录的绝对路径
        client_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 获取项目根目录
        root_dir = os.path.dirname(client_dir)
        
        # 添加必要的Python路径
        sys.path.extend([
            client_dir,
            root_dir,
            os.path.join(root_dir, 'backend')
        ])
        
        # 加载环境变量
        env_path = os.path.join(client_dir, '.env')
        load_dotenv(env_path)
        
        # 设置工作目录
        os.chdir(client_dir)
        
        lprint(f"工作目录: {client_dir}")
        lprint(f"Python路径: {sys.path}")
        
        return client_dir
        
    except Exception as e:
        lprint(f"环境设置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    try:
        # 设置环境
        client_dir = setup_environment()
        if not client_dir:
            return 1
            
        # 获取应用程序路径
        app_path = os.path.join(client_dir, 'pyqt_chatroom.py')
        
        if not os.path.exists(app_path):
            lprint(f"错误: 找不到程序文件 {app_path}")
            return 1
            
        lprint(f"应用程序路径: {app_path}")
        
        # 启动自动重载
        start_auto_reload(app_path)
        
    except Exception as e:
        lprint(f"启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 