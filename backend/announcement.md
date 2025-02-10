# LumenIM 部署总结

本总结详细描述了我们在部署 LumenIM 时所经历的各个步骤、遇到的各种问题及其解决方法。LumenIM 是一个基于 Web 的在线聊天项目，前端使用 Vue3 + Naive UI，后端使用 Go 语言开发的 `go-chat`。部署过程中，我们使用 Docker 启动了 MySQL、Redis 和 Nginx 容器，并手动配置了前后端项目。

## 环境准备与 Docker 部署

首先，我们确保 Docker 安装和服务正常运行，并使用 `docker-compose.yml` 文件来管理服务，包括 MySQL、Redis 和 Nginx。

### Docker Compose 配置

我们编写了 `docker-compose.yml` 文件，包含了 MySQL、Redis 和 Nginx 的配置，定义了各服务的端口、数据卷、网络等。例如：

```yaml
version: '3'

services:
  mysql:
    image: mysql:5.7
    environment:
      MYSQL_ROOT_PASSWORD: OC.123456
      MYSQL_DATABASE: go_chat
      MYSQL_USER: lumenuser
      MYSQL_PASSWORD: OC.123456
    ports:
      - "3306:3306"
    networks:
      - lumenim_network
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    networks:
      - lumenim_network
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:latest
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./LumenIM/dist:/usr/share/nginx/html
    networks:
      - lumenim_network

networks:
  lumenim_network:
    driver: bridge

volumes:
  mysql_data:
  redis_data:
```

## 前端项目配置与构建

1. **克隆前端项目**：将 LumenIM 前端项目克隆到服务器指定目录。
2. **安装依赖**：使用 `yarn install` 安装依赖。
3. **构建项目**：执行 `yarn build` 将前端项目构建为生产模式下的静态文件，并配置 Nginx 为静态文件提供服务。
4. **Nginx 配置**：修改 `nginx.conf`，确保正确的目录挂载，并将 `/usr/share/nginx/html` 指定为静态文件目录。

## 后端项目配置与启动

### 主要配置文件 config.yaml

在 `go-chat` 项目中，后端的主要配置文件是 `config.yaml`。该文件包含数据库、Redis、JWT 等必要的配置信息。例如：

```yaml
# MySQL 配置
mysql:
  host: 192.168.110.119
  port: 3306
  username: lumenuser
  password: OC.123456
  database: go_chat

# Redis 配置
redis:
  host: 192.168.110.119:6379
  auth: ""
```

### MySQL 用户名不能为 root 的问题

在部署过程中，MySQL 用户名不能设置为 `root`，因为这会引起权限问题并导致部署不安全。我们为此设置了一个名为 `lumenuser` 的用户，并为其分配了合适的权限。

### 数据库权限设置

在启动后端时遇到 MySQL 权限不足的问题：`Error 1044 (42000): Access denied for user 'lumenuser'@'%' to database 'go_chat'`。我们通过进入 MySQL 容器并执行以下命令解决此问题：

```sql
GRANT ALL PRIVILEGES ON go_chat.* TO 'lumenuser'@'%' IDENTIFIED BY 'OC.123456';
FLUSH PRIVILEGES;
```

### 数据库表缺失问题

解决权限问题后，发现数据库中缺少 `users` 等必要的表。为了解决此问题，运行以下命令进行数据库迁移：

```bash
go run ./cmd/lumenim migrate
```

此命令根据项目迁移脚本创建了所需的数据库表。

### 启动后端服务

完成配置后，我们使用以下命令启动 `go-chat` 后端服务：

```bash
go run ./cmd/lumenim http      # 启动 HTTP 服务
go run ./cmd/lumenim commet    # 启动 WebSocket 服务
```

## 移动端支持讨论

最后，我们探讨了 LumenIM 是否支持移动端应用。结论是该项目没有提供原生的移动端支持，但可以考虑以下几种方案：
- **移动浏览器**：可以直接在移动浏览器中访问 LumenIM 前端，作为简单的解决方案。
- **PWA**：将 LumenIM 配置为渐进式 Web 应用（PWA），使用户能够像安装原生应用一样将其添加到主屏幕。
- **开发原生移动应用**：使用 React Native 或 Flutter 这类跨平台框架，通过调用现有的 API 和 WebSocket 开发原生移动客户端。

## 问题汇总与解决方案

| 问题描述                                 | 解决方法                                                                                                                                               |
|------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| MySQL 用户名不能为 `root`                | 使用 `lumenuser` 作为 MySQL 用户名，以避免权限问题，并提高安全性                                                                                         |
| MySQL 权限不足，无法访问 `go_chat` 数据库 | 进入 MySQL 容器，授予 `lumenuser` 用户对 `go_chat` 数据库的权限                                                                                         |
| 数据库表缺失，导致服务启动失败           | 运行数据库迁移命令 `go run ./cmd/lumenim migrate` 以创建必要的表                                                                                        |
| Nginx 配置结构错误                       | 确保 `nginx.conf` 中 `server` 块位于 `http` 块内，挂载正确的静态文件路径                                                                                |
| Redis 和 MySQL 的连接配置问题             | 在 `config.yaml` 中正确配置 Redis 和 MySQL 的连接信息，包括主机、端口、用户名和密码                                                                     |
| 没有移动端支持                           | 使用 PWA 或开发原生移动端应用来扩展支持，或直接在移动浏览器中访问 LumenIM 的 Web 前端。 |

通过以上步骤和解决方案，我们成功部署了 LumenIM，并确保后端服务正常运行，前端能够正确访问后端数据和实时聊天功能。

