import sys,os
from pathlib import Path
from L_Tools import vnc_install
import traceback
import subprocess
import Lugwit_Module as LM

def install_vnc():
    """
    安装VNC服务并提供详细的安装过程反馈
    """
    subprocess.run(['robocopy','/MIR',LM.ProgramFilesLocal_Public+r'\VNC-Server',
    r'D:\TD_Depot\Temp\VNC-Server'])
    os.makedirs(r'D:\TD_Depot\Temp\VNC-Server',exist_ok=True)
    try:
        print("开始VNC安装流程...")
        print("1. 检查系统环境...")
        
        manager = vnc_install.VNCManager(
            install_threshold_version="7.0",
            installer_path=r"D:\TD_Depot\Temp\VNC-Server\Installer.exe",
            log_dir=r"D:\TD_Depot\Temp\VNC-Logs"
        )
        
        print("2. 开始安装/更新VNC...")
        result = manager.run()
        print("result",result)
        if result:
            print("\n✓ VNC安装成功完成！")
            print("  - 版本: 7.0")
            print("  - 安装路径: D:\\TD_Depot\\Temp\\VNC-Server")
            print("  - 日志路径: D:\\TD_Depot\\Temp\\VNC-Logs")
        else:
            print("\n✗ VNC安装失败")
            print("请检查安装日志获取详细信息")
        
        return result
        
    except Exception as e:
        traceback.print_exc()
        return False

if __name__ == "__main__":
    install_vnc()
