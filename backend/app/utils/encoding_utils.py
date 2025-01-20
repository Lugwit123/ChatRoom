#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import io
import locale
import ctypes
from typing import Optional
sys.path.append(r"D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\trayapp\Lib")
import Lugwit_Module as LM

lprint = LM.lprint

def setup_encoding(force_utf8: bool = True) -> None:
    """设置系统编码为UTF-8
    
    Args:
        force_utf8: 是否强制使用UTF-8编码
    """
    if force_utf8:
        print ("set encoding>>>>>>>>>>>>>>>")
        # 设置Python环境编码
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['LANG'] = 'zh_CN.UTF-8'
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
            # 设置Windows控制台代码页
    print()
    if ctypes.windll.kernel32.GetConsoleOutputCP()!=65001:
        print(f"set as {65001}")
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)

def get_encoding_info() -> dict:
    """获取当前系统的编码信息"""
    return {
        'filesystem': sys.getfilesystemencoding(),
        'default': sys.getdefaultencoding(),
        'stdout': sys.stdout.encoding if hasattr(sys.stdout, 'encoding') else None,
        'stderr': sys.stderr.encoding if hasattr(sys.stderr, 'encoding') else None,
        'locale': locale.getpreferredencoding(),
        'PYTHONIOENCODING': os.environ.get('PYTHONIOENCODING'),
        'LANG': os.environ.get('LANG'),
        'console_output': '65001' if sys.platform == 'win32' else 'N/A'
    }

def print_encoding_info() -> None:
    """打印当前系统的编码信息"""
    info = get_encoding_info()
    lprint(f"文件系统编码: {info['filesystem']}")
    lprint(f"Python默认编码: {info['default']}")
    lprint(f"标准输出编码: {info['stdout']}")
    lprint(f"标准错误编码: {info['stderr']}")
    lprint(f"locale编码: {info['locale']}")
    lprint(f"环境变量PYTHONIOENCODING: {info['PYTHONIOENCODING']}")
    lprint(f"环境变量LANG: {info['LANG']}")
    lprint(f"控制台输出编码: {info['console_output']}")
setup_encoding()