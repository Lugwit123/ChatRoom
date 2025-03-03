# PC端开发规范

## 项目结构
```
clientend/
├── modules/           # 模块目录
│   ├── ui/           # UI相关模块
│   ├── handlers/     # 消息处理模块
│   ├── utils/        # 工具模块
│   └── message.py    # 消息基类
├── config/           # 配置文件目录
├── tests/            # 测试目录
└── docs/            # 文档目录
```

## 技术栈规范
- Python 3.8+
- PySide6
- asyncio
- aiohttp
- WebSocket

## 模块开发规范

### UI模块规范
1. 窗口组件:
   - 继承自QMainWindow或QWidget
   - 使用setupUi方法初始化UI
   - 实现closeEvent处理关闭事件
   - 使用QSS样式表

2. 浏览器组件:
   - 使用QWebEngineView
   - 实现页面加载和JS交互
   - 处理WebChannel通信
   - 支持调试功能

3. 菜单组件:
   - 继承自QMenu
   - 实现鼠标事件处理
   - 支持动画效果
   - 统一的样式设置

### 消息处理规范
1. 消息类型:
   - 使用Enum定义消息类型
   - 实现消息序列化
   - 处理消息验证
   - 支持错误处理

2. WebSocket通信:
   - 实现自动重连
   - 处理心跳检测
   - 消息队列管理
   - 错误恢复机制

### 远程控制规范
1. VNC连接:
   - 版本检测
   - 自动安装
   - 连接管理
   - 错误处理

2. 权限控制:
   - 用户验证
   - 操作授权
   - 会话管理
   - 安全策略

## 代码规范

### 导入规范
```python
# 标准库
import os
import sys
import asyncio

# 第三方库
from PySide6.QtCore import *
from PySide6.QtWidgets import *

# 本地模块
import Lugwit_Module as LM
from modules.ui.browser import Browser
```

### 异常处理规范
```python
try:
    # 业务代码
    result = await async_operation()
except Exception as e:
    lprint(f"操作失败: {str(e)}")
    traceback.print_exc()
```

### 日志规范
```python
import Lugwit_Module as LM
lprint = LM.lprint

lprint("操作信息")
```

### 类型注解规范
```python
from typing import Optional, Dict, Any

def process_message(message: Dict[str, Any]) -> Optional[str]:
    pass
```

## 测试规范
1. 单元测试:
   - 使用pytest
   - 测试关键功能
   - 模拟外部依赖
   - 覆盖异常情况

2. 集成测试:
   - 测试模块交互
   - 测试UI操作
   - 测试网络通信
   - 测试性能指标

## 文档规范
1. 代码注释:
   - 类和方法必须有文档字符串
   - 复杂逻辑需要行内注释
   - 使用TODO标记待办项
   - 及时更新注释

2. 项目文档:
   - README.md项目说明
   - CHANGELOG.md变更记录
   - API文档
   - 开发指南

## 版本控制
1. 分支管理:
   - main: 主分支
   - develop: 开发分支
   - feature: 功能分支
   - hotfix: 修复分支

2. 提交规范:
   - feat: 新功能
   - fix: 修复bug
   - docs: 文档更新
   - style: 代码格式
   - refactor: 重构

## 性能优化
1. UI优化:
   - 避免阻塞主线程
   - 使用异步操作
   - 实现延迟加载
   - 优化渲染性能

2. 内存管理:
   - 及时释放资源
   - 避免内存泄漏
   - 控制对象生命周期
   - 使用弱引用

## 安全规范
1. 数据安全:
   - 加密敏感信息
   - 安全存储凭证
   - 清理临时文件
   - 防止信息泄露

2. 通信安全:
   - 使用HTTPS
   - WebSocket加密
   - 防止重放攻击
   - 实现超时机制

## 部署规范
1. 环境配置:
   - 使用虚拟环境
   - 管理依赖版本
   - 配置文件分离
   - 环境变量管理

2. 打包发布:
   - 使用pyinstaller
   - 资源文件处理
   - 版本号管理
   - 自动化构建

## 常见问题处理
1. 异步相关:
   - 'AsyncEngine' object has no attribute 'execute'
   - 'coroutine' object is not iterable
   - 'coroutine' object has no attribute 'first'

2. UI相关:
   - 窗口闪烁
   - 事件循环阻塞
   - 内存占用过高
   - 渲染性能问题

3. 网络相关:
   - 连接断开
   - 超时处理
   - 并发限制
   - 重试机制 