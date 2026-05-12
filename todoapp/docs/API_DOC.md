# API 参考文档 -- Todo App

> 版本：1.0
> 基础路径：`/api/v1`
> 协议：HTTP/HTTPS
> 数据格式：JSON

---

## 目录

- [认证方式](#认证方式)
- [通用约定](#通用约定)
- [认证模块](#认证模块)
  - [用户注册](#用户注册)
  - [用户登录](#用户登录)
- [用户模块](#用户模块)
  - [获取当前用户信息](#获取当前用户信息)
  - [修改昵称](#修改昵称)
  - [修改密码](#修改密码)
- [待办列表模块](#待办列表模块)
  - [获取所有列表](#获取所有列表)
  - [创建列表](#创建列表)
  - [更新列表](#更新列表)
  - [删除列表](#删除列表)
- [待办事项模块](#待办事项模块)
  - [获取待办列表](#获取待办列表)
  - [创建待办事项](#创建待办事项)
  - [更新待办事项](#更新待办事项)
  - [切换完成状态](#切换完成状态)
  - [删除待办事项](#删除待办事项)
- [错误码一览](#错误码一览)

---

## 认证方式

本 API 使用 **JWT Bearer Token** 认证。除注册和登录接口外，所有请求必须在 HTTP 请求头中携带 Token：

```
Authorization: Bearer <token>
```

### 获取 Token

通过 [用户注册](#用户注册) 或 [用户登录](#用户登录) 接口获取。响应中的 `data.token` 即为 JWT Token。

### Token 有效期

默认 7 天。Token 过期后接口返回 `401`，错误码 `AUTH_TOKEN_EXPIRED`，你需要重新登录获取新 Token。

### 认证失败行为

- 请求头缺少 `Authorization`：返回 `401 AUTH_TOKEN_MISSING`
- Token 格式错误或签名校验失败：返回 `401 AUTH_TOKEN_INVALID`
- Token 已过期：返回 `401 AUTH_TOKEN_EXPIRED`

---

## 通用约定

### 请求

- `Content-Type: application/json`
- 所有需要鉴权的接口必须携带 `Authorization: Bearer <token>` 请求头

### 响应格式

**成功响应**：

```json
{
  "success": true,
  "data": { ... }
}
```

**失败响应**：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "中文错误描述"
  }
}
```

### 时间格式

所有时间字段使用 UTC 时区，ISO 8601 格式，如 `2026-05-11T10:00:00.000Z`。

### ID 格式

所有实体 ID 使用 UUID v4 格式，如 `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"`。

---

## 认证模块

### 用户注册

创建新用户账号，同时返回 JWT Token。

```
POST /api/v1/auth/register
```

**是否需要鉴权**：否

#### 请求体

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `email` | string | 是 | 邮箱地址，需符合邮箱格式 |
| `password` | string | 是 | 密码，最少 6 位 |
| `nickname` | string | 是 | 昵称，1-50 字符 |

#### 请求示例

```bash
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "zhangsan@example.com",
    "password": "123456",
    "nickname": "张三"
  }'
```

#### 成功响应（200）

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "email": "zhangsan@example.com",
      "nickname": "张三",
      "createdAt": "2026-05-11T10:00:00.000Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 400 | `VALIDATION_FAILED` | 参数校验失败：email 格式错误 / password 不足 6 位 / nickname 为空 |
| 409 | `USER_EMAIL_EXISTS` | 该邮箱已注册 |

---

### 用户登录

使用邮箱和密码登录，返回 JWT Token。

```
POST /api/v1/auth/login
```

**是否需要鉴权**：否

#### 请求体

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `email` | string | 是 | 邮箱地址 |
| `password` | string | 是 | 密码 |

#### 请求示例

```bash
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "zhangsan@example.com",
    "password": "123456"
  }'
```

#### 成功响应（200）

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "email": "zhangsan@example.com",
      "nickname": "张三",
      "createdAt": "2026-05-11T10:00:00.000Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 400 | `VALIDATION_FAILED` | 参数校验失败：email 或 password 缺失 |
| 401 | `AUTH_INVALID_CREDENTIALS` | 邮箱或密码错误 |

---

## 用户模块

### 获取当前用户信息

获取当前登录用户的个人信息。

```
GET /api/v1/users/me
```

**是否需要鉴权**：是

#### 请求示例

```bash
curl http://localhost:3000/api/v1/users/me \
  -H "Authorization: Bearer <token>"
```

#### 成功响应（200）

```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "zhangsan@example.com",
    "nickname": "张三",
    "createdAt": "2026-05-11T10:00:00.000Z"
  }
}
```

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 401 | `AUTH_TOKEN_MISSING` | 请求头缺少 Authorization |
| 401 | `AUTH_TOKEN_INVALID` | Token 格式错误或签名校验失败 |
| 401 | `AUTH_TOKEN_EXPIRED` | Token 已过期 |

---

### 修改昵称

修改当前登录用户的昵称。

```
PUT /api/v1/users/me
```

**是否需要鉴权**：是

#### 请求体

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `nickname` | string | 是 | 新昵称，1-50 字符 |

#### 请求示例

```bash
curl -X PUT http://localhost:3000/api/v1/users/me \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "新昵称"
  }'
```

#### 成功响应（200）

```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "zhangsan@example.com",
    "nickname": "新昵称",
    "createdAt": "2026-05-11T10:00:00.000Z"
  }
}
```

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 400 | `VALIDATION_FAILED` | nickname 为空或超过 50 字符 |
| 401 | `AUTH_TOKEN_MISSING` | 未提供认证令牌 |
| 401 | `AUTH_TOKEN_INVALID` | 认证令牌无效 |
| 401 | `AUTH_TOKEN_EXPIRED` | 认证令牌已过期 |

---

### 修改密码

修改当前登录用户的密码，需验证旧密码。

```
PUT /api/v1/users/me/password
```

**是否需要鉴权**：是

#### 请求体

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `oldPassword` | string | 是 | 旧密码 |
| `newPassword` | string | 是 | 新密码，最少 6 位 |

#### 请求示例

```bash
curl -X PUT http://localhost:3000/api/v1/users/me/password \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "oldPassword": "123456",
    "newPassword": "654321"
  }'
```

#### 成功响应（200）

```json
{
  "success": true,
  "data": {
    "message": "密码修改成功"
  }
}
```

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 400 | `VALIDATION_FAILED` | newPassword 不足 6 位 |
| 401 | `AUTH_TOKEN_MISSING` | 未提供认证令牌 |
| 401 | `AUTH_TOKEN_INVALID` | 认证令牌无效 |
| 401 | `AUTH_TOKEN_EXPIRED` | 认证令牌已过期 |
| 401 | `AUTH_OLD_PASSWORD_WRONG` | 旧密码错误 |

---

## 待办列表模块

### 获取所有列表

获取当前用户的所有待办列表，按 `position` 升序排列。

```
GET /api/v1/lists
```

**是否需要鉴权**：是

#### 请求示例

```bash
curl http://localhost:3000/api/v1/lists \
  -H "Authorization: Bearer <token>"
```

#### 成功响应（200）

```json
{
  "success": true,
  "data": [
    {
      "id": "list-uuid-001",
      "name": "工作",
      "color": "#E74C3C",
      "position": 0,
      "todoCount": 5,
      "createdAt": "2026-05-11T10:00:00.000Z",
      "updatedAt": "2026-05-11T10:00:00.000Z"
    },
    {
      "id": "list-uuid-002",
      "name": "生活",
      "color": "#27AE60",
      "position": 1,
      "todoCount": 3,
      "createdAt": "2026-05-11T10:05:00.000Z",
      "updatedAt": "2026-05-11T10:05:00.000Z"
    }
  ]
}
```

`todoCount` 为该列表下**未完成**待办的数量。

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 401 | `AUTH_TOKEN_MISSING` | 未提供认证令牌 |
| 401 | `AUTH_TOKEN_INVALID` | 认证令牌无效 |
| 401 | `AUTH_TOKEN_EXPIRED` | 认证令牌已过期 |

---

### 创建列表

创建一个新的待办列表。

```
POST /api/v1/lists
```

**是否需要鉴权**：是

#### 请求体

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `name` | string | 是 | 列表名称，1-100 字符 |
| `color` | string | 是 | 颜色标识，HEX 格式如 `#E74C3C` |

#### 请求示例

```bash
curl -X POST http://localhost:3000/api/v1/lists \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "工作",
    "color": "#E74C3C"
  }'
```

#### 成功响应（201）

```json
{
  "success": true,
  "data": {
    "id": "list-uuid-003",
    "name": "工作",
    "color": "#E74C3C",
    "position": 2,
    "todoCount": 0,
    "createdAt": "2026-05-11T11:00:00.000Z",
    "updatedAt": "2026-05-11T11:00:00.000Z"
  }
}
```

`position` 为当前用户已有列表数量（追加到末尾）。

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 400 | `VALIDATION_FAILED` | name 为空或超长 / color 格式错误 |
| 401 | `AUTH_TOKEN_MISSING` | 未提供认证令牌 |

---

### 更新列表

更新列表的名称或颜色（至少提供一个字段）。

```
PUT /api/v1/lists/:id
```

**是否需要鉴权**：是

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string | 列表 UUID |

#### 请求体

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `name` | string | 否 | 新列表名称，1-100 字符 |
| `color` | string | 否 | 新颜色标识，HEX 格式 |

> 至少提供一个字段，否则返回 `VALIDATION_FAILED`。

#### 请求示例

```bash
curl -X PUT http://localhost:3000/api/v1/lists/list-uuid-001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "工作任务",
    "color": "#3498DB"
  }'
```

#### 成功响应（200）

```json
{
  "success": true,
  "data": {
    "id": "list-uuid-001",
    "name": "工作任务",
    "color": "#3498DB",
    "position": 0,
    "todoCount": 5,
    "createdAt": "2026-05-11T10:00:00.000Z",
    "updatedAt": "2026-05-11T11:00:00.000Z"
  }
}
```

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 400 | `VALIDATION_FAILED` | name 和 color 均未提供 |
| 401 | `AUTH_TOKEN_MISSING` | 未提供认证令牌 |
| 403 | `LIST_FORBIDDEN` | 无权操作此列表（列表不属于当前用户） |
| 404 | `LIST_NOT_FOUND` | 列表不存在 |

---

### 删除列表

删除列表及其下的所有待办事项。此操作不可恢复。

```
DELETE /api/v1/lists/:id
```

**是否需要鉴权**：是

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string | 列表 UUID |

#### 请求示例

```bash
curl -X DELETE http://localhost:3000/api/v1/lists/list-uuid-001 \
  -H "Authorization: Bearer <token>"
```

#### 成功响应（200）

```json
{
  "success": true,
  "data": {
    "message": "列表已删除"
  }
}
```

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 401 | `AUTH_TOKEN_MISSING` | 未提供认证令牌 |
| 403 | `LIST_FORBIDDEN` | 无权操作此列表 |
| 404 | `LIST_NOT_FOUND` | 列表不存在 |

---

## 待办事项模块

### 获取待办列表

获取当前用户的待办事项，支持按列表筛选、按状态过滤、按关键词搜索。

```
GET /api/v1/todos
```

**是否需要鉴权**：是

#### Query 参数

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `listId` | string | 否 | 按列表筛选，UUID 格式；不传则返回所有列表的待办 |
| `status` | string | 否 | 筛选状态：`all`（默认）、`active`（未完成）、`completed`（已完成） |
| `keyword` | string | 否 | 搜索关键词，匹配待办标题（模糊匹配） |

#### 请求示例

获取"工作"列表下所有未完成的待办：

```bash
curl "http://localhost:3000/api/v1/todos?listId=list-uuid-001&status=active" \
  -H "Authorization: Bearer <token>"
```

搜索标题包含"周报"的待办：

```bash
curl "http://localhost:3000/api/v1/todos?keyword=周报" \
  -H "Authorization: Bearer <token>"
```

#### 成功响应（200）

```json
{
  "success": true,
  "data": [
    {
      "id": "todo-uuid-001",
      "title": "完成周报",
      "description": "本周工作总结",
      "priority": "high",
      "completed": false,
      "listId": "list-uuid-001",
      "listName": "工作",
      "listColor": "#E74C3C",
      "position": 0,
      "createdAt": "2026-05-11T10:00:00.000Z",
      "updatedAt": "2026-05-11T10:00:00.000Z"
    },
    {
      "id": "todo-uuid-002",
      "title": "整理会议纪要",
      "description": null,
      "priority": "medium",
      "completed": false,
      "listId": "list-uuid-001",
      "listName": "工作",
      "listColor": "#E74C3C",
      "position": 1,
      "createdAt": "2026-05-11T10:05:00.000Z",
      "updatedAt": "2026-05-11T10:05:00.000Z"
    }
  ]
}
```

返回结果按 `priority` 降序排列（high > medium > low），同优先级按 `position` 升序。`listName` 和 `listColor` 为关联列表的冗余字段，便于前端展示。

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 400 | `VALIDATION_FAILED` | status 值不合法 / listId 格式错误 |
| 401 | `AUTH_TOKEN_MISSING` | 未提供认证令牌 |

---

### 创建待办事项

在指定列表中创建一条待办事项。

```
POST /api/v1/todos
```

**是否需要鉴权**：是

#### 请求体

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `title` | string | 是 | 待办标题，1-255 字符 |
| `description` | string | 否 | 待办描述，最长 2000 字符 |
| `listId` | string | 是 | 所属列表 UUID |
| `priority` | string | 否 | 优先级：`high` / `medium` / `low`，默认 `medium` |

#### 请求示例

```bash
curl -X POST http://localhost:3000/api/v1/todos \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "完成周报",
    "description": "本周工作总结",
    "listId": "list-uuid-001",
    "priority": "high"
  }'
```

#### 成功响应（201）

```json
{
  "success": true,
  "data": {
    "id": "todo-uuid-003",
    "title": "完成周报",
    "description": "本周工作总结",
    "priority": "high",
    "completed": false,
    "listId": "list-uuid-001",
    "listName": "工作",
    "listColor": "#E74C3C",
    "position": 2,
    "createdAt": "2026-05-11T12:00:00.000Z",
    "updatedAt": "2026-05-11T12:00:00.000Z"
  }
}
```

`position` 为该列表下已有待办数量（追加到末尾）。

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 400 | `VALIDATION_FAILED` | title 为空 / priority 值不合法 |
| 401 | `AUTH_TOKEN_MISSING` | 未提供认证令牌 |
| 403 | `LIST_FORBIDDEN` | 无权在此列表创建待办（列表不属于当前用户） |
| 404 | `LIST_NOT_FOUND` | 列表不存在 |

---

### 更新待办事项

更新待办事项的标题、描述、优先级或所属列表（至少提供一个字段）。

```
PUT /api/v1/todos/:id
```

**是否需要鉴权**：是

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string | 待办 UUID |

#### 请求体

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `title` | string | 否 | 新标题，1-255 字符 |
| `description` | string | 否 | 新描述，最长 2000 字符；传 `null` 可清空描述 |
| `priority` | string | 否 | 新优先级：`high` / `medium` / `low` |
| `listId` | string | 否 | 移动到新列表，UUID 格式 |

> 至少提供一个字段，否则返回 `VALIDATION_FAILED`。

#### 请求示例

修改标题并将待办移到另一个列表：

```bash
curl -X PUT http://localhost:3000/api/v1/todos/todo-uuid-001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "完成月度周报",
    "listId": "list-uuid-002"
  }'
```

清空描述：

```bash
curl -X PUT http://localhost:3000/api/v1/todos/todo-uuid-001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": null
  }'
```

#### 成功响应（200）

```json
{
  "success": true,
  "data": {
    "id": "todo-uuid-001",
    "title": "完成月度周报",
    "description": "本周工作总结",
    "priority": "high",
    "completed": false,
    "listId": "list-uuid-002",
    "listName": "生活",
    "listColor": "#27AE60",
    "position": 0,
    "createdAt": "2026-05-11T10:00:00.000Z",
    "updatedAt": "2026-05-11T13:00:00.000Z"
  }
}
```

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 400 | `VALIDATION_FAILED` | 无字段更新 / priority 值不合法 |
| 401 | `AUTH_TOKEN_MISSING` | 未提供认证令牌 |
| 403 | `TODO_FORBIDDEN` | 无权操作此待办 |
| 403 | `LIST_FORBIDDEN` | 无权访问目标列表（移动待办时） |
| 404 | `TODO_NOT_FOUND` | 待办不存在 |
| 404 | `LIST_NOT_FOUND` | 目标列表不存在（移动待办时） |

---

### 切换完成状态

切换待办事项的完成状态。未完成 -> 已完成，已完成 -> 未完成。

```
PATCH /api/v1/todos/:id/toggle
```

**是否需要鉴权**：是

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string | 待办 UUID |

#### 请求示例

```bash
curl -X PATCH http://localhost:3000/api/v1/todos/todo-uuid-001/toggle \
  -H "Authorization: Bearer <token>"
```

#### 成功响应（200）

```json
{
  "success": true,
  "data": {
    "id": "todo-uuid-001",
    "title": "完成周报",
    "description": "本周工作总结",
    "priority": "high",
    "completed": true,
    "listId": "list-uuid-001",
    "listName": "工作",
    "listColor": "#E74C3C",
    "position": 0,
    "createdAt": "2026-05-11T10:00:00.000Z",
    "updatedAt": "2026-05-11T14:00:00.000Z"
  }
}
```

`completed` 为切换后的状态。再次调用同一接口会将 `completed` 切换回 `false`。

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 401 | `AUTH_TOKEN_MISSING` | 未提供认证令牌 |
| 403 | `TODO_FORBIDDEN` | 无权操作此待办 |
| 404 | `TODO_NOT_FOUND` | 待办不存在 |

---

### 删除待办事项

删除一条待办事项。此操作不可恢复。

```
DELETE /api/v1/todos/:id
```

**是否需要鉴权**：是

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string | 待办 UUID |

#### 请求示例

```bash
curl -X DELETE http://localhost:3000/api/v1/todos/todo-uuid-001 \
  -H "Authorization: Bearer <token>"
```

#### 成功响应（200）

```json
{
  "success": true,
  "data": {
    "message": "待办已删除"
  }
}
```

#### 错误响应

| HTTP 状态码 | error.code | 说明 |
|-------------|-----------|------|
| 401 | `AUTH_TOKEN_MISSING` | 未提供认证令牌 |
| 403 | `TODO_FORBIDDEN` | 无权操作此待办 |
| 404 | `TODO_NOT_FOUND` | 待办不存在 |

---

## 错误码一览

### 认证相关（AUTH_）

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| `AUTH_INVALID_CREDENTIALS` | 401 | 邮箱或密码错误 |
| `AUTH_TOKEN_MISSING` | 401 | 请求头缺少 Authorization |
| `AUTH_TOKEN_INVALID` | 401 | Token 格式错误或签名校验失败 |
| `AUTH_TOKEN_EXPIRED` | 401 | Token 已过期 |
| `AUTH_OLD_PASSWORD_WRONG` | 401 | 修改密码时旧密码错误 |

### 用户相关（USER_）

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| `USER_NOT_FOUND` | 404 | 用户不存在 |
| `USER_EMAIL_EXISTS` | 409 | 该邮箱已注册 |

### 列表相关（LIST_）

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| `LIST_NOT_FOUND` | 404 | 列表不存在 |
| `LIST_FORBIDDEN` | 403 | 无权操作此列表（列表不属于当前用户） |
| `LIST_NAME_EMPTY` | 400 | 列表名称为空 |

### 待办相关（TODO_）

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| `TODO_NOT_FOUND` | 404 | 待办不存在 |
| `TODO_FORBIDDEN` | 403 | 无权操作此待办（待办不属于当前用户） |
| `TODO_TITLE_EMPTY` | 400 | 待办标题为空 |

### 通用错误

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| `VALIDATION_FAILED` | 400 | 请求参数校验失败，具体原因见 `error.message` |
| `SERVER_INTERNAL_ERROR` | 500 | 服务端内部错误 |

### 错误响应示例

**参数校验失败**：

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "password 至少需要 6 个字符"
  }
}
```

**认证失败**：

```json
{
  "success": false,
  "error": {
    "code": "AUTH_TOKEN_EXPIRED",
    "message": "认证令牌已过期"
  }
}
```

**权限不足**：

```json
{
  "success": false,
  "error": {
    "code": "LIST_FORBIDDEN",
    "message": "无权操作此列表"
  }
}
```

**资源不存在**：

```json
{
  "success": false,
  "error": {
    "code": "TODO_NOT_FOUND",
    "message": "待办不存在"
  }
}
```

---

## 接口总览

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/api/v1/auth/register` | 否 | 用户注册 |
| POST | `/api/v1/auth/login` | 否 | 用户登录 |
| GET | `/api/v1/users/me` | 是 | 获取当前用户信息 |
| PUT | `/api/v1/users/me` | 是 | 修改昵称 |
| PUT | `/api/v1/users/me/password` | 是 | 修改密码 |
| GET | `/api/v1/lists` | 是 | 获取所有列表 |
| POST | `/api/v1/lists` | 是 | 创建列表 |
| PUT | `/api/v1/lists/:id` | 是 | 更新列表 |
| DELETE | `/api/v1/lists/:id` | 是 | 删除列表 |
| GET | `/api/v1/todos` | 是 | 获取待办列表（筛选/搜索） |
| POST | `/api/v1/todos` | 是 | 创建待办事项 |
| PUT | `/api/v1/todos/:id` | 是 | 更新待办事项 |
| PATCH | `/api/v1/todos/:id/toggle` | 是 | 切换完成状态 |
| DELETE | `/api/v1/todos/:id` | 是 | 删除待办事项 |
