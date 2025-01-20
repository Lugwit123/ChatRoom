# 项目配置
## 环境配置
- python解释器路径: D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\python_env\lugwit_python.exe
- 控制台编码: 65001
- 时间戳格式: 带时区
- Python包管理: requirements.txt

## 目录结构
backend/
├── app/                    # 应用主目录
│   ├── core/              # 核心功能
│   │   ├── auth/         # 认证相关
│   │   │   ├── __init__.py  # 模块初始化
│   │   │   ├── models.py    # 认证相关数据模型
│   │   │   └── auth.py      # JWT认证和权限验证实现
│   │   ├── exceptions/   # 异常处理
│   │   │   ├── __init__.py  # 异常模块初始化
│   │   │   └── handlers.py  # 全局异常处理器
│   │   └── websocket/    # WebSocket处理
│   │       ├── __init__.py  # WebSocket模块初始化
│   │       └── manager.py   # WebSocket连接管理器
│   ├── domain/           # 领域模块
│   │   ├── device/      # 设备管理
│   │   │   ├── __init__.py     # 设备模块初始化
│   │   │   ├── models.py       # 设备数据模型
│   │   │   └── repository.py   # 设备数据访问层
│   │   ├── file/        # 文件管理
│   │   │   ├── __init__.py     # 文件模块初始化
│   │   │   ├── models.py       # 文件数据模型
│   │   │   ├── repository.py   # 文件数据访问层
│   │   │   ├── router.py       # 文件路由定义
│   │   │   ├── service.py      # 文件业务逻辑
│   │   │   └── abc_check/      # ABC文件检查
│   │   │       ├── __init__.py    # ABC检查模块初始化
│   │   │       ├── config.py      # ABC检查配置
│   │   │       ├── models.py      # ABC检查数据模型
│   │   │       ├── repository.py  # ABC检查数据访问
│   │   │       └── service.py     # ABC检查业务逻辑
│   │   ├── group/       # 群组管理
│   │   │   ├── __init__.py     # 群组模块初始化
│   │   │   ├── models.py       # 群组数据模型
│   │   │   ├── repository.py   # 群组数据访问层
│   │   │   ├── router.py       # 群组路由定义
│   │   │   ├── schemas.py      # 群组数据验证
│   │   │   ├── service.py      # 群组业务逻辑
│   │   │   └── handlers.py     # 群组事件处理
│   │   ├── message/     # 消息管理
│   │   │   ├── __init__.py     # 消息模块初始化
│   │   │   ├── enums.py        # 消息相关枚举
│   │   │   ├── models.py       # 消息数据模型
│   │   │   ├── schemas.py      # 消息数据验证
│   │   │   ├── router.py       # 消息路由定义
│   │   │   ├── handlers.py     # 消息事件处理
│   │   │   ├── service.py      # 消息业务逻辑
│   │   │   ├── repositories/   # 消息仓储
│   │   │   │   ├── __init__.py           # 仓储模块初始化
│   │   │   │   ├── base.py               # 基础消息仓储
│   │   │   │   ├── group.py              # 群组消息仓储
│   │   │   │   ├── private.py            # 私聊消息仓储
│   │   │   │   ├── group_message_manager.py  # 群消息管理器
│   │   │   │   └── group_message_utils.py    # 群消息工具类
│   │   └── user/        # 用户管理
│   │       ├── __init__.py     # 用户模块初始化
│   │       ├── models.py       # 用户数据模型
│   │       ├── repository.py   # 用户数据访问层
│   │       ├── router.py       # 用户路由定义
│   │       ├── schemas.py      # 用户数据验证
│   │       ├── service.py      # 用户业务逻辑
│   │       └── handlers.py     # 用户事件处理
│   ├── db/              # 数据库相关
│   │   ├── __init__.py        # 数据库模块初始化
│   │   ├── database.py        # 数据库连接配置
│   │   └── base.py           # 基础仓储类定义
│   ├── utils/           # 工具函数
│   │   ├── __init__.py        # 工具模块初始化
│   │   ├── common.py          # 通用工具函数
│   │   ├── encoding_utils.py  # 编码处理工具
│   │   ├── logging_config.py  # 日志配置
│   │   └── security.py        # 安全相关工具
│   ├── static/          # 静态资源目录
│   ├── templates/       # 模板文件目录
│   └── main.py         # 应用入口和配置

# 开发规范
## 代码组织
1. 领域模块基本结构：
   - models.py: 数据模型定义
   - repository.py: 数据访问层
   - service.py: 业务逻辑层
   - router.py: 路由定义
   - handlers.py: 事件处理器（如果需要）
   - schemas.py: 数据验证模式（如果需要）
   - enums.py: 枚举定义（如果需要）

2. 特殊模块结构：
   a. 消息模块：
      - repositories/: 消息仓储实现
        - base.py: 基础消息仓储接口
        - group.py: 群组消息仓储实现
        - private.py: 私聊消息仓储实现
        - group_message_manager.py: 群消息管理器（归档、迁移、清理）
        - group_message_utils.py: 群消息工具（导出、备份、恢复）
   
   b. 文件模块：
      - abc_check/: ABC文件检查子模块
        - config.py: 检查配置
        - models.py: 检查模型
        - repository.py: 检查数据访问
        - service.py: 检查业务逻辑

## 代码规范
1. 导入规范：
   - backend根目录下不使用相对导入
   - 按标准库、第三方库、本地模块顺序导入
   - 使用绝对导入路径

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

## 测试规范
1. 测试结构：
   - unit/: 单元测试
   - integration/: 集成测试
   - e2e/: 端到端测试

2. 测试命名：
   - test_*.py: 测试文件
   - test_*: 测试函数
   - Test*: 测试类

3. 测试覆盖：
   - 使用pytest-cov生成覆盖率报告
   - 核心功能必须有单元测试
   - 关键流程必须有集成测试

4. 测试工具：
   - pytest
   - pytest-asyncio
   - pytest-cov
   - pytest-mock

## 错误处理
1. 错误记录：
   - 使用lprint记录
   - 包含时间和堆栈信息
   - 错误信息要明确具体

2. 错误预防：
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

# 数据库规范
1. 初始化顺序：
   - 清空数据库
   - 创建用户表
   - 创建设备表
   - 创建文件表
   - 创建群组表
   - 创建消息表
   - 创建关联表
   - 插入初始数据

2. 表设计规范：
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
   - 使用外键保证引用完整性
   - 使用枚举类型约束

3. 事务处理：
   - 使用async with处理事务
   - 合理设置隔离级别
   - 正确处理回滚
   - 避免长事务

4. 性能优化：
   - 避免N+1查询
   - 使用适当的索引
   - 合理使用延迟加载
   - 定期维护数据库
   - 消息优化：
     * 使用表分区
     * 定期归档旧消息
     * 批量处理大量消息
     * 异步处理非关键操作

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
   - 消息系统文档：
     * 分表策略说明
     * 归档策略说明
     * 备份恢复流程
     * 性能优化指南

3. 错误文档：
   - 记录常见错误
   - 提供解决方案
   - 更新预防措施
   - 分析根本原因

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