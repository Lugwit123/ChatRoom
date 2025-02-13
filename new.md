# 全局交互规则
- 使用中文回答
- 每次回答前告诉我征询了哪个规则文件及具体的路径
- 每次回答时补充数据库的基础知识,最好使用比较的方式来讲解
- 每次回答前描述问题是否合理及原因
- React Query版本是v5
- 代码修改后检查新问题
- 文件未保存时自动保存
- 打印信息使用`lprint`,不使用`logger`
- 导入方式：`import Lugwit_Module as LM, lprint=LM.lprint`
- 对于文件的修改不需要用户同意,直接修改
- 使用Windows命令,不使用Linux命令
- 发现问题先说明后修改
- 修改代码前分析结构和依赖
- 使用占位符时注意保护重要代码
- 修改后检查遗漏和误删
- 说明删除的函数和原因
- 保持最小修改原则
- 运行bat文件使用`cmd /c 文件.bat`格式
- 看不到日志文件使用python查看
- 创建文件前检查类似文件
- 不读取日志文件,从终端获取
- 使用traceback时直接使用trace.print_exc()

# 后端项目架构
## 整体架构
- 项目采用分层架构设计：
  1. Core层：提供基础设施服务
     - auth: 认证和授权
     - websocket: WebSocket服务
     - base: 基础组件
     - exceptions: 异常处理
  
  2. Domain层：业务领域模块
     - message: 消息处理
     - user: 用户管理
     - group: 群组管理
     - file: 文件处理
     - device: 设备管理
     - common: 公共组件
     - base: 基础设施
  
  3. DB层：数据库访问层
     - 统一的数据库连接管理
     - 事务控制
     - 迁移管理
  
  4. Utils层：工具类

## 架构原则
- 使用门面模式（Facade Pattern）封装复杂子系统
- 所有仓库继承自基础仓库
- 遵循依赖倒置原则
- 避免跨层直接访问
- 不要轻易创建新文件
- 使用继承自基础仓库的方式处理对话

# 模块结构规范
## Core模块结构
- facade/: 外观层接口
- internal/: 内部实现
  - repository/: 数据访问
  - service/: 业务逻辑
- schemas/: 数据模型
- config/: 配置

## Domain模块结构
每个领域模块应包含：
- facade/: 外观层
  - dto/: 数据传输对象
  - *_facade.py: 外观类
- internal/: 内部实现
  - repository/: 数据仓储
  - service/: 业务逻辑（可选）
- models/: 数据模型
- schemas/: 验证模式
- enums/: 枚举定义

# 环境配置
- python解释器路径: D:\TD_Depot\Software\Lugwit_syncPlug\lugwit_insapp\python_env\lugwit_chatroom.exe
- 控制台编码: 65001
- 时间戳格式: 带时区
- Python包管理: requirements.txt
- 运行后端使用"cmd /c run_backend_server.bat",运行前结束"lugwit_chatroom.exe"
- 禁止主动启动后端服务器,除非是用户指令
- 每次后端修改记录到backend\docs\CHANGELOG.md
- 禁止修改测试文件和日志配置文件
- 禁止修改backend\.env
- 不应搜索备份目录和前端代码目录
- 编译.py文件时不写文件功能和函数功能说明

# 开发规范
## 代码组织
1. 导入规范：
   - 使用绝对导入
   - 标准库 > 第三方库 > 本地模块
   - 避免循环导入
   - 相关导入应该分组并用空行分隔

2. 异步编程规范：
   - 所有IO操作必须是异步的
   - 使用async/await语法
   - 正确处理异步上下文
   - 避免阻塞操作

3. WebSocket规范：
   - 实现心跳机制
   - 处理连接异常
   - 实现重连机制
   - 消息队列处理

## 数据库规范
1. 基础规范：
   - 禁止使用SqlModel
   - 使用异步SQLAlchemy
   - 每个群组独立消息表和归档表
   - 使用分区表策略
   - 实现连接池管理
   - 统一的事务处理机制

2. 表设计规范：
   - 必须包含创建时间和更新时间
   - 使用UUID作为主键
   - 适当的索引策略
   - 合理的字段类型选择

3. 查询优化：
   - 使用适当的索引
   - 避免N+1查询问题
   - 使用批量操作
   - 实现查询缓存机制

4. SQLAlchemy使用规范：
   - 使用sql_cast进行类型转换
   - 使用.is_()进行布尔值比较
   - 使用.any()和.contains()进行数组操作
   - 使用and_和or_组合条件
   - 正确处理查询结果（scalars().all()和scalar_one_or_none()）

## 异常处理规范
1. 异常分类：
   - 业务异常
   - 系统异常
   - 数据库异常
   - 网络异常

2. 日志记录：
   - 使用lprint而不是logger
   - 导入方式：`import Lugwit_Module as LM, lprint=LM.lprint`
   - 使用traceback时直接使用trace.print_exc()
   - 记录完整的上下文信息
   - 日志文件检查：
     * 不要仅通过view_file工具判断文件是否为空
     * 必须先用list_dir检查文件大小
     * 使用python查看后端日志(utf8编码)

## 测试规范
1. 测试分类：
   - 单元测试：测试独立组件
   - 集成测试：测试组件交互
   - 端到端测试：测试完整流程
   - 性能测试：测试系统性能

2. WebSocket测试：
   - 连接建立测试
   - 消息发送接收测试
   - 异常处理测试
   - 性能和负载测试

3. 数据库测试：
   - 使用测试数据库
   - 事务回滚机制
   - 模拟数据生成
   - 并发测试

# 安全规范
1. 认证授权：
   - JWT令牌验证
   - 角色权限控制
   - 会话管理
   - 访问控制列表

2. WebSocket安全：
   - 连接认证
   - 消息加密
   - 速率限制
   - 防止DOS攻击

3. 数据安全：
   - 敏感数据加密
   - SQL注入防护
   - XSS防护
   - CSRF防护

# 性能优化指南
1. 数据库优化：
   - 合理的索引设计
   - 查询优化
   - 连接池配置
   - 分区策略

2. WebSocket优化：
   - 消息压缩
   - 批量处理
   - 心跳间隔调优
   - 连接池管理

3. 缓存策略：
   - 多级缓存
   - 缓存失效策略
   - 缓存同步机制
   - 分布式缓存

# 常见错误预防
1. 异步相关错误：
   - 'AsyncEngine' object has no attribute 'execute'
   - 'coroutine' object is not iterable
   - 'coroutine' object has no attribute 'first'
   - 正确使用await关键字

2. WebSocket错误：
   - 连接断开处理
   - 消息序列化错误
   - 并发连接限制
   - 心跳超时处理

3. 数据库错误：
   - 连接泄漏
   - 死锁处理
   - 事务超时
   - 并发访问冲突

# 文档维护
1. 文档位置：
   - README.md: 项目概览
   - docs/: 详细文档
   - API.md: 接口文档
   - CHANGELOG.md: 变更日志
   - ERROR_GUIDE.md: 错误指南

2. 文档更新要求：
   - 代码变更同步更新文档
   - 记录重要决策
   - 保持文档格式统一
   - 定期审查和更新 