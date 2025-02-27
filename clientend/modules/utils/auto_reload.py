"""
自动重载模块，用于监控文件变化并自动重启PyQt客户端程序
"""
import os
import sys
import time
import subprocess
import signal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import Lugwit_Module as LM

lprint = LM.lprint

class CodeChangeHandler(FileSystemEventHandler):
    """监控代码变化的处理器"""
    
    def __init__(self, restart_callback):
        """初始化处理器
        
        Args:
            restart_callback: 重启回调函数
        """
        self.restart_callback = restart_callback
        self.last_modified = time.time()
        self.debounce_seconds = 1  # 防抖时间(秒)
        
    def on_modified(self, event):
        """文件修改事件处理
        
        Args:
            event: 文件系统事件
        """
        if event.is_directory:
            return
            
        # 检查是否是Python文件
        if not event.src_path.endswith('.py'):
            return
            
        # 防抖处理
        current_time = time.time()
        if current_time - self.last_modified < self.debounce_seconds:
            return
            
        self.last_modified = current_time
        lprint(f"检测到文件变化: {event.src_path}")
        self.restart_callback()

class PyQtAutoReloader:
    """PyQt程序自动重载器"""
    
    def __init__(self, app_path: str):
        """初始化重载器
        
        Args:
            app_path: PyQt应用程序路径
        """
        self.app_path = app_path
        self.process = None
        self.observer = None
        
    def start(self):
        """启动自动重载器"""
        try:
            # 启动文件监控
            self.observer = Observer()
            handler = CodeChangeHandler(self.restart_app)
            
            # 获取clientend目录
            client_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            # 监控clientend目录
            self.observer.schedule(handler, client_dir, recursive=True)
            self.observer.start()
            
            lprint(f"开始监控目录: {client_dir}")
            
            # 首次启动程序
            self.start_app()
            
            try:
                while True:
                    if self.process:
                        # 检查进程是否还在运行
                        if self.process.poll() is not None:
                            lprint("程序已退出，重新启动...")
                            self.start_app()
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()
                
        except Exception as e:
            lprint(f"启动自动重载器失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.stop()
            
    def start_app(self):
        """启动PyQt应用程序"""
        try:
            if self.process:
                # 使用系统信号优雅地终止进程
                if sys.platform == 'win32':
                    self.process.send_signal(signal.CTRL_C_EVENT)
                else:
                    self.process.send_signal(signal.SIGTERM)
                    
                try:
                    self.process.wait(timeout=5)  # 等待最多5秒
                except subprocess.TimeoutExpired:
                    self.process.kill()  # 如果超时，强制终止
                    
            # 获取clientend目录
            client_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            # 启动程序进程
            self.process = subprocess.Popen(
                [sys.executable, self.app_path],
                cwd=client_dir,  # 使用clientend作为工作目录
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            lprint(f"PyQt程序已启动: {self.app_path}")
            lprint(f"工作目录: {client_dir}")
            
            # 启动日志监控线程
            self._start_log_monitor()
            
        except Exception as e:
            lprint(f"启动程序失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def _start_log_monitor(self):
        """启动日志监控"""
        def monitor_output(pipe, prefix):
            try:
                with pipe:
                    for line in iter(pipe.readline, ''):
                        # 提取实际的日志内容
                        if '----code_context' in line:
                            line = line.split('----code_context')[0]
                        
                        line = line.strip()
                        if not line:
                            continue
                            
                        # 过滤掉无用信息
                        if any(skip in line for skip in [
                            'WARNING:root',
                            'File:',
                            '-fn:',
                            'None',
                            '^'
                        ]):
                            continue
                            
                        # 处理引号包裹的内容
                        if line.startswith('"') and line.endswith('"'):
                            line = line[1:-1]

            except Exception as e:
                lprint(f"日志监控错误: {str(e)}")
                
        import threading
        if self.process and self.process.stdout:
            # 监控标准输出
            threading.Thread(
                target=monitor_output,
                args=(self.process.stdout, "输出"),
                daemon=True
            ).start()
            
        if self.process and self.process.stderr:
            # 监控标准错误
            threading.Thread(
                target=monitor_output,
                args=(self.process.stderr, "错误"),
                daemon=True
            ).start()
            
    def restart_app(self):
        """重启程序"""
        lprint("正在重启程序...")
        self.start_app()
        
    def stop(self):
        """停止自动重载器"""
        try:
            if self.process:
                # 优雅地终止进程
                if sys.platform == 'win32':
                    self.process.send_signal(signal.CTRL_C_EVENT)
                else:
                    self.process.send_signal(signal.SIGTERM)
                    
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                
            if self.observer:
                self.observer.stop()
                self.observer.join()
                
            lprint("自动重载器已停止")
            
        except Exception as e:
            lprint(f"停止自动重载器失败: {str(e)}")
            import traceback
            traceback.print_exc()

def start_auto_reload(app_path: str):
    """启动自动重载
    
    Args:
        app_path: PyQt应用程序路径
    """
    reloader = PyQtAutoReloader(app_path)
    reloader.start() 