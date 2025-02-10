# ChatRoom

一个基于 PySide6 和 WebSocket 的聊天室应用。

## 功能特性

- 实时聊天功能
- 远程控制功能
- 文件传输
- 系统托盘集成
- 暗色主题
- 多用户支持
- 群组聊天
- 消息通知

## 技术栈

- Python 3.8+
- PySide6
- WebSocket
- asyncio
- aiohttp
- SQLAlchemy

## 项目结构

```
.
├── backend/                # 后端服务
│   ├── app/               # 应用代码
│   │   ├── core/         # 核心功能
│   │   ├── domain/       # 领域模型
│   │   └── routers/      # API路由
│   └── tests/            # 测试代码
│
├── clientend/            # 客户端
│   ├── modules/          # 模块目录
│   │   ├── ui/          # UI相关模块
│   │   ├── handlers/    # 消息处理模块
│   │   └── utils/       # 工具模块
│   ├── config/          # 配置文件
│   └── static/          # 静态资源
│
└── docs/                # 文档
```

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/chatroom.git
cd chatroom
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境：
- 复制 `.env.example` 到 `.env`
- 修改配置参数

## 运行

1. 启动后端服务：
```bash
python run_backend_server.py
```

2. 启动客户端：
```bash
python clientend/pyqt_chatroom.py
```

## 开发

- 遵循 PEP 8 编码规范
- 使用 Type Hints
- 编写单元测试
- 保持代码文档更新

## 贡献

欢迎提交 Pull Request 或创建 Issue。

## 许可证

MIT License 