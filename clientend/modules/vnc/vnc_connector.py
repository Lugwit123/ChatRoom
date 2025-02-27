"""
VNC连接器模块，处理所有VNC相关的连接逻辑
"""
import os
import sys
import subprocess
import psutil
import winreg
import time
import re
import Lugwit_Module as LM
from dotenv import load_dotenv
from pywinauto import Application, WindowSpecification
from pywinauto.timings import TimeoutError
from PySide6.QtWidgets import QMessageBox
import traceback

lprint = LM.lprint

# 加载环境变量
load_dotenv()

# VNC配置
VNC_VIEWER_PATH = os.getenv('VNC_VIEWER_PATH', r'C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe')
VNC_SERVER_PATH = os.getenv('VNC_SERVER_PATH', r'C:\Program Files\RealVNC\VNC Server\vncserver.exe')
VNC_DEFAULT_PORT = int(os.getenv('VNC_DEFAULT_PORT', '5900'))
VNC_DEFAULT_PASSWORD = os.getenv('VNC_DEFAULT_PASSWORD', '')

# 认证窗口等待配置
AUTH_WINDOW_TIMEOUT = 10  # 等待认证窗口的超时时间(秒)
AUTH_WINDOW_CHECK_INTERVAL = 0.5  # 检查认证窗口的间隔时间(秒)

class VNCConnector:
    """VNC连接器类"""
    
    def __init__(self):
        """初始化VNC连接器"""
        self.vnc_path = VNC_VIEWER_PATH 
        
    def check_vnc_version(self) -> tuple[bool, str]:
        """检查VNC版本
        Returns:
            tuple[bool, str]: (是否是7.x版本, 版本号)
        """
        try:
            # 检查64位程序
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            
            # 遍历所有子键查找VNC Server
            index = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, index)
                    subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                    
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        if "VNC Server" in display_name:
                            version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                            winreg.CloseKey(subkey)
                            winreg.CloseKey(key)
                            return version.startswith("7."), version
                    except WindowsError:
                        pass
                    finally:
                        winreg.CloseKey(subkey)
                    
                    index += 1
                except WindowsError:
                    break
            
            # 如果64位没找到，检查32位程序
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
            index = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, index)
                    subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
                    
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        if "VNC Server" in display_name:
                            version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                            winreg.CloseKey(subkey)
                            winreg.CloseKey(key)
                            return version.startswith("7."), version
                    except WindowsError:
                        pass
                    finally:
                        winreg.CloseKey(subkey)
                    
                    index += 1
                except WindowsError:
                    break
            
            winreg.CloseKey(key)
            return False, ""
            
        except Exception as e:
            lprint(f"检查VNC版本出错: {str(e)}")
            return False, ""
            
    def is_vnc_running(self) -> bool:
        """检查VNC服务是否运行
        
        Returns:
            bool: 是否运行
        """
        try:
            # 运行sc query命令检查服务状态
            result = subprocess.run(['sc', 'query', 'vncserver'], capture_output=True, text=True)
            
            # 检查输出中是否包含RUNNING状态
            return 'RUNNING' in result.stdout
            
        except Exception as e:
            lprint(f"检查VNC服务状态失败: {str(e)}")
            traceback.print_exc()
            return False

    def start_vnc_service(self) -> bool:
        """启动VNC服务
        
        Returns:
            bool: 是否成功启动
        """
        try:
            # 检查服务是否已经在运行
            if self.is_vnc_running():
                return True

            # 尝试启动服务
            result = subprocess.run(['net', 'start', 'vncserver'], check=True, capture_output=True, text=True)
            return True

        except subprocess.CalledProcessError as e:
            lprint(f"启动VNC服务失败: {e.stderr}")
            return False
        except Exception as e:
            lprint(f"启动VNC服务时发生错误: {str(e)}")
            traceback.print_exc()
            return False

    def ensure_vnc_ready(self, parent_widget=None) -> bool:
        """确保VNC服务已准备就绪
        
        Args:
            parent_widget: 父窗口部件，用于显示消息框
            
        Returns:
            bool: 是否准备就绪
        """
        try:
            # 检查版本
            is_v7, version = self.check_vnc_version()
            if not is_v7:
                # 不是7.x版本，提示安装
                if parent_widget:
                    reply = QMessageBox.question(
                        parent_widget,
                        "安装VNC Server",
                        f"当前{'未安装VNC Server' if not version else f'VNC版本为{version}'}\n"
                        "需要安装VNC Server 7.x版本才能使用远程控制功能。\n"
                        "是否现在安装？",
                        QMessageBox.StandardButton.Yes,
                        QMessageBox.StandardButton.No
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        return False

                # 安装VNC
                from .vnc_installer import install_vnc
                if not install_vnc():
                    if parent_widget:
                        QMessageBox.warning(
                            parent_widget,
                            "安装失败",
                            "VNC服务安装失败，请检查安装日志获取详细信息",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.Ok
                        )
                    return False

            # 检查并启动服务
            if not self.is_vnc_running():
                if not self.start_vnc_service():
                    if parent_widget:
                        QMessageBox.warning(
                            parent_widget,
                            "启动服务失败",
                            "VNC服务启动失败，请手动启动服务或重新安装。",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No
                        )
                    return False

            return True

        except Exception as e:
            lprint(f"准备VNC服务失败: {str(e)}")
            traceback.print_exc()
            return False

    def wait_for_window(self ,app: Application, title: str, timeout: float = AUTH_WINDOW_TIMEOUT) -> WindowSpecification:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                window = app.window(title=title)
                if window.exists():
                    lprint(f"找到窗口: {title}")
                    return window
            except Exception:
                pass
            time.sleep(AUTH_WINDOW_CHECK_INTERVAL)
            
        raise TimeoutError(f"等待窗口超时: {title}")
    def connect(self,ip: str, port: int = VNC_DEFAULT_PORT, password: str = VNC_DEFAULT_PASSWORD) -> bool:
        """连接到VNC服务器
        
        Args:
            ip (str): 服务器IP地址
            port (int, optional): 端口号. Defaults to VNC_DEFAULT_PORT.
            password (str, optional): 密码. Defaults to VNC_DEFAULT_PASSWORD.
            
        Returns:
            bool: 连接是否成功
        """
        try:
            lprint(f"尝试连接VNC服务器: {ip}:{port}")
            
            if not os.path.exists(VNC_VIEWER_PATH):
                lprint(f"找不到VNC客户端: {VNC_VIEWER_PATH}")
                return False
                
            # 启动VNC客户端并连接到指定地址
            pywinauto_app = Application().start(f'"{VNC_VIEWER_PATH}" {ip}:{port}')
            
            # 等待认证窗口加载
            try:
                # 等待认证窗口出现
                lprint("等待认证窗口出现...")
                dlg = self.wait_for_window(pywinauto_app, 'Authentication')
                
                # 等待密码输入框和确定按钮出现
                lprint("等待控件加载...")
                start_time = time.time()
                while time.time() - start_time < AUTH_WINDOW_TIMEOUT:
                    try:
                        password_input = dlg.child_window(class_name="Edit", found_index=1)
                        ok_button = dlg.child_window(title="OK", class_name="Button")
                        if password_input.exists() and ok_button.exists():
                            break
                    except Exception:
                        pass
                    time.sleep(AUTH_WINDOW_CHECK_INTERVAL)
                
                # 输入密码并点击确定
                lprint("输入密码...")
                password_input.type_keys(password, with_spaces=True)
                time.sleep(0.5)  # 等待密码输入完成
                
                lprint("点击确定按钮...")
                ok_button.click()
                
                lprint("VNC客户端已启动并完成认证")
                return True
                
            except TimeoutError as e:
                lprint(f"等待认证窗口超时: {str(e)}")
                return False
            except Exception as e:
                lprint(f"VNC认证失败: {str(e)}")
                return False
            
        except Exception as e:
            lprint(f"VNC连接失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

# 创建全局VNC连接器实例
vnc_connector = VNCConnector() 