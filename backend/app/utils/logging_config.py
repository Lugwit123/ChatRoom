import logging
import os
from logging.handlers import RotatingFileHandler
from Lugwit_Module import lprint

# 创建logs目录（如果不存在）
log_dir = r'D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib\ChatRoom\backend\logs'
os.makedirs(log_dir, exist_ok=True)

# 配置日志格式
formatter = logging.Formatter(
    '%(message)s'
)

# 设置文件处理器
log_file = os.path.join(log_dir, 'server.log')
if os.path.exists(log_file):
    os.remove(log_file)
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*248,  # 2MB
    backupCount=0,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# 设置控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

