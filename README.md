# Lugwit ChatRoom

基于Python的企业级实时聊天应用，支持私聊、群聊和远程控制功能。

## 功能特点

### 核心功能
- 实时聊天
  - 私聊和群聊支持
  - 消息历史记录
  - 消息状态追踪（已发送/已读）
  - 实时状态更新
  - 文件传输功能

- 远程控制
  - VNC远程桌面集成
  - 自动安装VNC服务
  - 权限管理和安全控制
  - 远程协助请求

- 系统集成
  - 系统托盘集成
  - 消息通知
  - 暗色主题支持
  - 多语言支持

### 技术特点
- 高性能WebSocket通信
- 异步IO和事件驱动
- 数据库实时同步
- 安全的用户认证
- 可扩展的插件系统

## 技术栈

### 后端
- Python 3.8+
- SQLAlchemy
- Socket.IO (python-socketio)
- asyncio
- aiohttp
- alembic (数据库迁移)

### 前端
- React 18
- React Query v5
- TypeScript
- TailwindCSS
- Socket.IO Client
- Vite

### 客户端
- PySide6 (Qt for Python)
- qasync (异步支持)
- python-socketio (WebSocket客户端)
- CSS3 (暗色主题)

### 数据库
- PostgreSQL

### 工具和服务
- VNC Server (远程控制)
- Git (版本控制)
- pytest (测试框架)

## 项目结构

```
ChatRoom/
├── backend/                # 后端服务
│   ├── app/               # 应用代码
│   │   ├── core/         # 核心功能
│   │   │   ├── auth/     # 认证模块
│   │   │   ├── websocket/# WebSocket服务
│   │   │   └── events/   # 事件系统
│   │   ├── domain/       # 领域模型
│   │   │   ├── user/     # 用户模块
│   │   │   ├── message/  # 消息模块
│   │   │   └── group/    # 群组模块
│   │   └── routers/      # API路由
│   └── tests/            # 测试代码
│
├── frontend/             # Web前端
│   ├── src/             # 源代码
│   │   ├── components/  # React组件
│   │   ├── hooks/       # 自定义Hooks
│   │   ├── pages/       # 页面组件
│   │   ├── services/    # API服务
│   │   ├── store/       # 状态管理
│   │   └── utils/       # 工具函数
│   ├── public/          # 静态资源
│   └── styles/          # 样式文件
│       ├── themes/      # 主题样式
│       └── components/  # 组件样式
│
├── clientend/            # 客户端
│   ├── modules/          # 模块目录
│   │   ├── ui/          # UI相关模块
│   │   ├── handlers/    # 消息处理模块
│   │   ├── events/      # 事件处理
│   │   └── types/       # 类型定义
│   ├── icons/           # 图标资源
│   └── static/          # 静态资源
│
└── scripts/             # 脚本文件
    ├── run_backend.bat  # 启动后端
    └── run_client.bat   # 启动客户端
```

## 安装说明

### 环境要求
- Python 3.8 或更高版本
- pip 包管理器
- Git
- VNC Server (可选，用于远程控制功能)

### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/Lugwit123/ChatRoom.git
cd ChatRoom
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
# Windows
venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境：
- 复制 `.env.example` 到 `.env`
- 修改配置参数（数据库连接、服务器地址等）

5. 初始化数据库：
```bash
cd backend
alembic upgrade head
```

## 运行说明

1. 启动后端服务：
```bash
run_backend_server.bat
```

2. 启动客户端：
```bash
run_client.bat
```

## 开发指南

### 代码规范
- 遵循 PEP 8 编码规范
- 使用 Type Hints 进行类型注解
- 编写详细的文档字符串
- 保持代码覆盖率在 80% 以上

### 测试
- 单元测试：使用 pytest
- 集成测试：测试关键功能流程

### 分支管理
- main: 主分支，用于发布
- develop: 开发分支
- feature/*: 功能分支
- bugfix/*: 修复分支

### 提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试相关
- chore: 构建过程或辅助工具的变动

## 常见问题

### 1. 连接问题
- 检查WebSocket服务器状态
- 验证网络连接
- 确认防火墙设置

### 2. 远程控制
- 确保VNC服务已安装
- 检查端口是否开放
- 验证用户权限

### 3. 性能优化
- 使用连接池
- 启用缓存
- 优化数据库查询
- 减少不必要的网络请求

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 作者

- Lugwit123 - [GitHub](https://github.com/Lugwit123)

## 致谢

- 感谢所有贡献者的付出
- 特别感谢使用到的开源项目
  - PySide6
  - SQLAlchemy
  - Socket.IO 