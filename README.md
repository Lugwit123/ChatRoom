# ChatRoom Application

一个基于Python和PySide6的聊天室应用程序，支持系统托盘、远程控制等功能。

## 功能特点

- 系统托盘集成
- 用户登录/登出
- 远程控制支持（VNC）
- 实时消息通知
- 暗色主题界面
- 多用户聊天

## 技术栈

- Python 3.8+
- PySide6
- Socket.IO
- aiohttp
- asyncio
- QSS样式

## 安装说明

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/chatroom.git
cd chatroom
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
- 复制`.env.example`为`.env`
- 修改配置参数

4. 运行程序：
```bash
python clientend/pyqt_chatroom.py
```

## 目录结构

```
chatroom/
├── clientend/           # 客户端代码
│   ├── modules/         # 模块目录
│   │   ├── handlers/   # 处理器
│   │   ├── ui/        # UI组件
│   │   └── ...
│   ├── static/         # 静态资源
│   ├── icons/          # 图标文件
│   └── config/         # 配置文件
├── backend/            # 后端代码
└── docs/              # 文档
```

## 开发说明

- 使用PySide6进行UI开发
- 采用异步编程模式
- 遵循PEP 8编码规范
- 使用QSS进行样式定制

## 许可证

MIT License 