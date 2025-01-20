import logging
import os
from logging.handlers import RotatingFileHandler

def :
    # 创建logs目录（如果不存在）
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(message)s'
    )
    
    # 设置文件处理器
    log_file = os.path.join(log_dir, 'server.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*5048,  # 2MB
        backupCount=2,
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

    return root_logger
