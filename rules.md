# 项目配置

## 环境配置
- python解释器路径: D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\python_env\lugwit_chatroom.exe
- 控制台编码: 65001
- 时间戳格式: 带时区
- Python包管理: requirements.txt
- 禁止启动后端服务器,请从日志文件读取报错信息,每次出现错误都要读取报错日志文件
- 请每次都把后端的修改记录到backend\docs\CHANGELOG.md
- 禁止修改测试文件和日志配置文件
- 编译.py文件时,文件并不写上一些该代码文件的功能和拥有的函数的功能

## 目录结构
backend/
├── app/                    # 应用主目录
│   ├── core/              # 核心功能
│   │   ├── auth/         # 认证相关
│   │   │   ├── __init__.py
│   │   │   ├── models.py       # 认证模型
│   │   │   ├── service.py      # 认证服务
│   │   │   └── auth.py         # JWT认证实现
│   │   ├── exceptions/   # 异常处理
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # 基础异常类
│   │   │   └── handlers.py     # 异常处理器
│   │   └── websocket/    # WebSocket处理
│   │       ├── __init__.py
│   │       ├── manager.py      # 连接管理器
│   │       └── events.py       # 事件处理
│   ├── domain/           # 领域模块
│   │   ├── base/        # 基础设施
│   │   │   ├── __init__.py
│   │   │   ├── models.py       # 基础模型
│   │   │   └── repository.py   # 基础仓储
│   │   ├── device/      # 设备管理
│   │   │   ├── __init__.py
│   │   │   ├── models.py       # 设备模型
│   │   │   ├── repository.py   # 设备仓储
│   │   │   ├── service.py      # 设备服务
│   │   │   └── router.py       # 设备路由
│   │   ├── file/        # 文件管理
│   │   │   ├── __init__.py
│   │   │   ├── models.py       # 文件模型
│   │   │   ├── repository.py   # 文件仓储
│   │   │   ├── service.py      # 文件服务
│   │   │   ├── router.py       # 文件路由
│   │   │   └── abc_check/      # ABC文件检查
│   │   │       ├── __init__.py
│   │   │       ├── config.py   # 检查配置
│   │   │       ├── models.py   # 检查模型
│   │   │       ├── service.py  # 检查服务
│   │   │       └── utils.py    # 检查工具
│   │   ├── group/       # 群组管理
│   │   │   ├── __init__.py
│   │   │   ├── models.py       # 群组模型
│   │   │   ├── repository.py   # 群组仓储
│   │   │   ├── service.py      # 群组服务
│   │   │   ├── router.py       # 群组路由
│   │   │   ├── schemas.py      # 数据验证
│   │   │   └── handlers/       # 事件处理
│   │   │       ├── __init__.py
│   │   │       ├── member.py   # 成员处理
│   │   │       └── message.py  # 消息处理
│   │   ├── message/     # 消息管理
│   │   │   ├── __init__.py
│   │   │   ├── models.py       # 消息模型
│   │   │   ├── enums.py        # 消息枚举
│   │   │   ├── schemas.py      # 数据验证
│   │   │   ├── router.py       # 消息路由
│   │   │   ├── facade/        # 外观模式
│   │   │   │   ├── __init__.py
│   │   │   │   ├── message_facade.py  # 消息门面
│   │   │   │   └── dto/              # 数据传输
│   │   │   │       ├── __init__.py
│   │   │   │       └── message_dto.py
│   │   │   ├── internal/      # 内部实现
│   │   │   │   ├── __init__.py
│   │   │   │   ├── handlers/  # 事件处理
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── message_handler.py
│   │   │   │   └── services/  # 业务服务
│   │   │   │       ├── __init__.py
│   │   │   │       ├── message_service.py
│   │   │   │       └── message_archive_service.py
│   │   │   └── repositories/  # 数据仓储
│   │   │       ├── __init__.py
│   │   │       ├── base.py    # 基础仓储
│   │   │       ├── group.py   # 群组消息
│   │   │       ├── private.py # 私聊消息
│   │   │       └── archive/   # 归档相关
│   │   │           ├── __init__.py
│   │   │           ├── manager.py  # 归档管理
│   │   │           └── utils.py    # 归档工具
│   │   └── user/        # 用户管理
│   │       ├── __init__.py
│   │       ├── models.py       # 用户模型
│   │       ├── repository.py   # 用户仓储
│   │       ├── service.py      # 用户服务
│   │       ├── router.py       # 用户路由
│   │       ├── schemas.py      # 数据验证
│   │       └── handlers.py     # 事件处理
│   ├── db/              # 数据库相关
│   │   ├── __init__.py
│   │   ├── database.py        # 数据库配置
│   │   ├── migrations/        # 数据迁移
│   │   │   ├── __init__.py
│   │   │   └── versions/      # 迁移版本
│   │   └── base.py           # 基础定义
│   ├── utils/           # 工具函数
│   │   ├── __init__.py
│   │   ├── common.py          # 通用工具
│   │   ├── encoding.py        # 编码工具
│   │   ├── security.py        # 安全工具
│   │   └── logging/          # 日志相关
│   │       ├── __init__.py
│   │       ├── config.py     # 日志配置
│   │       └── handlers.py   # 日志处理
│   ├── static/          # 静态资源
│   │   ├── css/             # 样式文件
│   │   ├── js/              # 脚本文件
│   │   └── images/          # 图片资源
│   ├── templates/       # 模板文件
│   │   ├── base.html        # 基础模板
│   │   ├── auth/           # 认证相关
│   │   └── chat/           # 聊天相关
│   └── main.py         # 应用入口
├── tests/              # 测试目录
│   ├── __init__.py
│   ├── conftest.py          # 测试配置
│   ├── unit/               # 单元测试
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_message.py
│   │   └── test_group.py
│   ├── integration/        # 集成测试
│   │   ├── __init__.py
│   │   └── test_chat.py
│   └── e2e/               # 端到端测试
│       ├── __init__.py
│       └── test_chat_flow.py
├── docs/               # 文档目录
│   ├── README.md           # 项目说明
│   ├── CHANGELOG.md        # 变更日志
│   ├── API.md             # 接口文档
│   └── guides/            # 使用指南
│       ├── setup.md       # 环境配置
│       ├── development.md # 开发指南
│       └── deployment.md  # 部署指南
├── scripts/            # 脚本目录
│   ├── setup.py           # 安装脚本
│   ├── run_server.bat     # 启动服务
│   └── run_tests.bat      # 运行测试
├── .env               # 环境变量
├── .gitignore        # Git忽略
├── requirements.txt   # 依赖清单
└── setup.cfg         # 项目配置

# 开发规范

## 代码组织
1. 领域模块基本结构：
   - models.py: 数据模型定义
   - repository.py: 数据访问层
   - service.py: 业务逻辑层
   - router.py: 路由定义
   - handlers.py: 事件处理器
   - schemas.py: 数据验证
   - enums.py: 枚举定义

2. 特殊模块结构：
   a. 消息模块：
      - facade/: 外观模式实现
      - internal/: 内部实现
      - repositories/: 数据仓储
   
   b. 文件模块：
      - abc_check/: ABC文件检查

## 代码规范
1. 导入规范：
   - 使用绝对导入
   - 标准库 > 第三方库 > 本地模块
   - 避免循环导入

2. 数据库规范：
   - 禁止使用SqlModel
   - 使用异步SQLAlchemy
   - 每个群组独立消息表
   - 每个群组独立归档表
   - 消息表分区策略：
     * 按时间分区
     * 按状态分区（活跃/归档）
   - 索引策略：
     * 消息ID索引
     * 发送时间索引
     * 发送者索引
     * 全文搜索索引
   - 使用BaseRepository基类
   - 统一事务处理

3. 异常处理：
   - 使用自定义异常类
   - 统一使用lprint记录日志
   - 包含完整堆栈信息
   - 异常信息要详细明确

4. 类型注解：
   - 所有函数必须有类型注解
   - 使用typing模块的类型
   - 复杂类型使用类型别名

## 日志规范
1. 日志配置：
   - 使用lprint而不是logger
   - 导入方式：import Lugwit_Module as LM, lprint=LM.lprint
   - 在backend_main.py中使用from logging_config import setup_logging

2. 日志检查：
   - 不要仅通过view_file工具判断文件是否为空
   - 必须先用list_dir检查文件大小
   - 使用python查看后端日志,注意是utf8编码

## 测试规范
1. 测试结构：
   - unit/: 单元测试
   - integration/: 集成测试
   - e2e/: 端到端测试

2. 测试规则：
   - 命名规范：
     * test_*.py: 测试文件
     * test_*: 测试函数
     * Test*: 测试类
   - 覆盖率要求：
     * 核心功能必须有单元测试
     * 关键流程必须有集成测试
   - 工具使用：
     * pytest
     * pytest-asyncio
     * pytest-cov
     * pytest-mock

## 错误处理
1. 常见错误预防：
   - 'AsyncEngine' object has no attribute 'execute'
   - 'coroutine' object is not iterable
   - 'coroutine' object has no attribute 'first'

2. 错误记录：
   - 使用lprint记录
   - 包含时间和堆栈信息
   - 错误信息要明确具体

3. 错误预防：
   - 代码修改前检查ERROR_GUIDE.md
   - 使用类型检查器
   - 编写单元测试

# 运行说明
1. 环境准备：
   - 安装依赖: pip install -r requirements.txt
   - 配置.env文件
   - 初始化数据库

2. 启动服务：
   - 运行run_server.bat
   - 检查日志输出
   - 验证服务状态

3. 测试运行：
   - 运行run_tests.bat
   - 检查测试报告
   - 分析覆盖率报告

# 安全规范
1. 认证授权：
   - 使用JWT令牌
   - 实现角色权限
   - 加密敏感数据
   - 防止越权访问

2. 数据安全：
   - 加密存储密码
   - 防止SQL注入
   - 输入数据验证
   - 防止XSS攻击

3. 日志安全：
   - 脱敏敏感信息
   - 记录关键操作
   - 定期清理日志
   - 保护日志文件

# 文档维护
1. 文档位置：
   - README.md: 项目总览
   - docs/: 详细文档
   - ERROR_GUIDE.md: 错误指南
   - API.md: 接口文档

2. 文档更新：
   - 代码变更同步更新文档
   - 定期检查文档准确性
   - 保持文档格式统一
   - 记录重要决策