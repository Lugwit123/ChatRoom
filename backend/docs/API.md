# API 文档

## 1. 认证 API

### 1.1 用户注册
```http
POST /auth/register
Content-Type: application/json

{
    "username": "string",
    "email": "string",
    "password": "string"
}

Response: 200 OK
{
    "id": "integer",
    "username": "string",
    "email": "string",
    "created_at": "datetime"
}
```

### 1.2 用户登录
```http
POST /auth/login
Content-Type: application/json

{
    "username": "string",
    "password": "string"
}

Response: 200 OK
{
    "access_token": "string",
    "token_type": "string"
}
```

## 2. 消息 API

### 2.1 发送私聊消息
```http
POST /messages/private
Content-Type: application/json
Authorization: Bearer {token}

{
    "recipient": "string",
    "content": "string",
    "message_type": "string",
    "content_type": "string"
}

Response: 200 OK
{
    "id": "integer",
    "content": "string",
    "sender": "string",
    "recipient": "string",
    "timestamp": "datetime",
    "status": "string"
}
```

### 2.2 获取私聊消息
```http
GET /messages/private/{username}
Authorization: Bearer {token}

Response: 200 OK
[
    {
        "id": "integer",
        "content": "string",
        "sender": "string",
        "recipient": "string",
        "timestamp": "datetime",
        "status": "string"
    }
]
```

## 3. 群组 API

### 3.1 创建群组
```http
POST /groups
Content-Type: application/json
Authorization: Bearer {token}

{
    "name": "string",
    "description": "string"
}

Response: 200 OK
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "created_at": "datetime",
    "created_by": "string"
}
```

### 3.2 获取群组消息
```http
GET /groups/{group_id}/messages
Authorization: Bearer {token}

Response: 200 OK
[
    {
        "id": "integer",
        "content": "string",
        "sender": "string",
        "timestamp": "datetime",
        "message_type": "string"
    }
]
```

## 4. 设备 API

### 4.1 注册设备
```http
POST /devices
Content-Type: application/json
Authorization: Bearer {token}

{
    "device_id": "string",
    "device_name": "string",
    "device_type": "string"
}

Response: 200 OK
{
    "id": "integer",
    "device_id": "string",
    "device_name": "string",
    "device_type": "string",
    "registered_at": "datetime"
}
```

### 4.2 获取设备列表
```http
GET /devices
Authorization: Bearer {token}

Response: 200 OK
[
    {
        "id": "integer",
        "device_id": "string",
        "device_name": "string",
        "device_type": "string",
        "registered_at": "datetime",
        "last_seen": "datetime",
        "login_status": "boolean"
    }
]
```

## 5. 文件 API

### 5.1 上传文件
```http
POST /files/upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

file: binary

Response: 200 OK
{
    "file_id": "string",
    "filename": "string",
    "size": "integer",
    "upload_time": "datetime",
    "url": "string"
}
```

### 5.2 下载文件
```http
GET /files/{file_id}
Authorization: Bearer {token}

Response: 200 OK
Content-Type: application/octet-stream
```

## 6. WebSocket API

### 6.1 连接
```websocket
WS /ws/chat
Authorization: Bearer {token}
```

### 6.2 消息格式
```json
// 发送消息
{
    "type": "message",
    "recipient": "string",
    "content": "string",
    "message_type": "string"
}

// 接收消息
{
    "type": "message",
    "sender": "string",
    "content": "string",
    "timestamp": "datetime",
    "message_type": "string"
}

// 状态更新
{
    "type": "status",
    "user": "string",
    "status": "string",
    "timestamp": "datetime"
}
```

## 7. 错误处理

### 7.1 错误响应格式
```json
{
    "detail": "string",
    "code": "integer",
    "timestamp": "datetime"
}
```

### 7.2 常见错误码
- 400: 请求参数错误
- 401: 未认证
- 403: 权限不足
- 404: 资源不存在
- 409: 资源冲突
- 500: 服务器错误
