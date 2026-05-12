# API 契约文档 (API_CONTRACT) -- Todo App

> 版本：1.0
> 日期：2026-05-11
> 作者：software-architect
> 基于：PRD v1.0 / TECH_SPEC v1.0

---

## 通用约定

- 基础路径：`/api/v1`
- 鉴权方式：`Authorization: Bearer <token>`（注册/登录接口除外）
- 请求 Content-Type：`application/json`
- 响应格式统一为：
  - 成功：`{ "success": true, "data": { ... } }`
  - 失败：`{ "success": false, "error": { "code": "ERROR_CODE", "message": "描述" } }`
- 分页参数（本 MVP 阶段不涉及分页，所有列表一次返回）

---

## 1. 认证模块

### 1.1 POST /api/v1/auth/register

**功能**：用户注册（F01）

**是否需要鉴权**：否

**Request Body**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| email | string | 是 | 邮箱地址，格式校验 |
| password | string | 是 | 密码，最少 6 位 |
| nickname | string | 是 | 昵称，1-50 字符 |

**Response 200**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-string",
      "email": "user@example.com",
      "nickname": "张三",
      "createdAt": "2026-05-11T10:00:00.000Z"
    },
    "token": "jwt-token-string"
  }
}
```

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 400 | VALIDATION_FAILED | 请求参数校验失败 | email 格式错误 / password 不足 6 位 / nickname 为空 |
| 409 | USER_EMAIL_EXISTS | 该邮箱已注册 | email 已存在于 users 表 |

---

### 1.2 POST /api/v1/auth/login

**功能**：用户登录（F01）

**是否需要鉴权**：否

**Request Body**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码 |

**Response 200**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-string",
      "email": "user@example.com",
      "nickname": "张三",
      "createdAt": "2026-05-11T10:00:00.000Z"
    },
    "token": "jwt-token-string"
  }
}
```

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 400 | VALIDATION_FAILED | 请求参数校验失败 | email 或 password 缺失 |
| 401 | AUTH_INVALID_CREDENTIALS | 邮箱或密码错误 | email 不存在或 password 不匹配 |

---

## 2. 用户模块

### 2.1 GET /api/v1/users/me

**功能**：获取当前用户信息（F05）

**是否需要鉴权**：是

**Request Body**：无

**Response 200**

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "email": "user@example.com",
    "nickname": "张三",
    "createdAt": "2026-05-11T10:00:00.000Z"
  }
}
```

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 401 | AUTH_TOKEN_MISSING | 未提供认证令牌 | 请求头缺少 Authorization |
| 401 | AUTH_TOKEN_INVALID | 认证令牌无效 | Token 格式错误或签名校验失败 |
| 401 | AUTH_TOKEN_EXPIRED | 认证令牌已过期 | Token 超过有效期 |

---

### 2.2 PUT /api/v1/users/me

**功能**：修改当前用户昵称（F05）

**是否需要鉴权**：是

**Request Body**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| nickname | string | 是 | 新昵称，1-50 字符 |

**Response 200**

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "email": "user@example.com",
    "nickname": "新昵称",
    "createdAt": "2026-05-11T10:00:00.000Z"
  }
}
```

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 400 | VALIDATION_FAILED | 请求参数校验失败 | nickname 为空或超过 50 字符 |
| 401 | AUTH_TOKEN_MISSING | 未提供认证令牌 | 同上 |
| 401 | AUTH_TOKEN_INVALID | 认证令牌无效 | 同上 |
| 401 | AUTH_TOKEN_EXPIRED | 认证令牌已过期 | 同上 |

---

### 2.3 PUT /api/v1/users/me/password

**功能**：修改当前用户密码（F05）

**是否需要鉴权**：是

**Request Body**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| oldPassword | string | 是 | 旧密码 |
| newPassword | string | 是 | 新密码，最少 6 位 |

**Response 200**

```json
{
  "success": true,
  "data": {
    "message": "密码修改成功"
  }
}
```

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 400 | VALIDATION_FAILED | 请求参数校验失败 | newPassword 不足 6 位 |
| 401 | AUTH_TOKEN_MISSING | 未提供认证令牌 | 同上 |
| 401 | AUTH_TOKEN_INVALID | 认证令牌无效 | 同上 |
| 401 | AUTH_TOKEN_EXPIRED | 认证令牌已过期 | 同上 |
| 401 | AUTH_OLD_PASSWORD_WRONG | 旧密码错误 | oldPassword 与数据库不匹配 |

---

## 3. 待办列表模块

### 3.1 GET /api/v1/lists

**功能**：获取当前用户的所有列表（F02）

**是否需要鉴权**：是

**Request Body**：无

**Response 200**

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-string",
      "name": "工作",
      "color": "#E74C3C",
      "position": 0,
      "todoCount": 5,
      "createdAt": "2026-05-11T10:00:00.000Z",
      "updatedAt": "2026-05-11T10:00:00.000Z"
    }
  ]
}
```

> `todoCount` 为该列表下**未完成**待办的数量。

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 401 | AUTH_TOKEN_MISSING | 未提供认证令牌 | 请求头缺少 Authorization |
| 401 | AUTH_TOKEN_INVALID | 认证令牌无效 | Token 校验失败 |
| 401 | AUTH_TOKEN_EXPIRED | 认证令牌已过期 | Token 过期 |

---

### 3.2 POST /api/v1/lists

**功能**：创建列表（F02）

**是否需要鉴权**：是

**Request Body**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 是 | 列表名称，1-100 字符 |
| color | string | 是 | 颜色标识，HEX 格式如 #E74C3C |

**Response 201**

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "name": "工作",
    "color": "#E74C3C",
    "position": 3,
    "todoCount": 0,
    "createdAt": "2026-05-11T10:00:00.000Z",
    "updatedAt": "2026-05-11T10:00:00.000Z"
  }
}
```

> `position` 为当前用户已有列表数量（追加到末尾）。

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 400 | VALIDATION_FAILED | 请求参数校验失败 | name 为空或超长 / color 格式错误 |
| 401 | AUTH_TOKEN_MISSING | 未提供认证令牌 | 同上 |

---

### 3.3 PUT /api/v1/lists/:id

**功能**：更新列表（重命名 / 修改颜色）（F02）

**是否需要鉴权**：是

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 列表 UUID |

**Request Body**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 否 | 新列表名称，1-100 字符 |
| color | string | 否 | 新颜色标识，HEX 格式 |

> 至少提供一个字段。

**Response 200**

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "name": "新名称",
    "color": "#3498DB",
    "position": 0,
    "todoCount": 5,
    "createdAt": "2026-05-11T10:00:00.000Z",
    "updatedAt": "2026-05-11T11:00:00.000Z"
  }
}
```

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 400 | VALIDATION_FAILED | 请求参数校验失败 | name 和 color 均未提供 |
| 401 | AUTH_TOKEN_MISSING | 未提供认证令牌 | 同上 |
| 403 | LIST_FORBIDDEN | 无权操作此列表 | 列表不属于当前用户 |
| 404 | LIST_NOT_FOUND | 列表不存在 | id 对应的列表不存在 |

---

### 3.4 DELETE /api/v1/lists/:id

**功能**：删除列表及其下所有待办（F02）

**是否需要鉴权**：是

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 列表 UUID |

**Request Body**：无

**Response 200**

```json
{
  "success": true,
  "data": {
    "message": "列表已删除"
  }
}
```

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 401 | AUTH_TOKEN_MISSING | 未提供认证令牌 | 同上 |
| 403 | LIST_FORBIDDEN | 无权操作此列表 | 列表不属于当前用户 |
| 404 | LIST_NOT_FOUND | 列表不存在 | id 对应的列表不存在 |

---

## 4. 待办事项模块

### 4.1 GET /api/v1/todos

**功能**：获取待办列表（支持筛选和搜索）（F03, F04）

**是否需要鉴权**：是

**Query 参数**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| listId | string | 否 | 按列表筛选，UUID 格式；不传则返回所有列表的待办 |
| status | string | 否 | 筛选状态：`all`（默认）、`active`、`completed` |
| keyword | string | 否 | 搜索关键词，匹配待办标题（模糊匹配） |

**Response 200**

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-string",
      "title": "完成周报",
      "description": "本周工作总结",
      "priority": "high",
      "completed": false,
      "listId": "uuid-string",
      "listName": "工作",
      "listColor": "#E74C3C",
      "position": 0,
      "createdAt": "2026-05-11T10:00:00.000Z",
      "updatedAt": "2026-05-11T10:00:00.000Z"
    }
  ]
}
```

> 返回结果按 priority 降序（high > medium > low），同优先级按 position 升序。
> `listName` 和 `listColor` 为关联列表的冗余字段，便于前端展示。

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 400 | VALIDATION_FAILED | 请求参数校验失败 | status 值不合法 / listId 格式错误 |
| 401 | AUTH_TOKEN_MISSING | 未提供认证令牌 | 同上 |

---

### 4.2 POST /api/v1/todos

**功能**：创建待办事项（F03）

**是否需要鉴权**：是

**Request Body**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| title | string | 是 | 待办标题，1-255 字符 |
| description | string | 否 | 待办描述，最长 2000 字符 |
| listId | string | 是 | 所属列表 UUID |
| priority | string | 否 | 优先级：`high`/`medium`/`low`，默认 `medium` |

**Response 201**

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "title": "完成周报",
    "description": "本周工作总结",
    "priority": "high",
    "completed": false,
    "listId": "uuid-string",
    "listName": "工作",
    "listColor": "#E74C3C",
    "position": 0,
    "createdAt": "2026-05-11T10:00:00.000Z",
    "updatedAt": "2026-05-11T10:00:00.000Z"
  }
}
```

> `position` 为该列表下已有待办数量（追加到末尾）。

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 400 | VALIDATION_FAILED | 请求参数校验失败 | title 为空 / priority 值不合法 |
| 401 | AUTH_TOKEN_MISSING | 未提供认证令牌 | 同上 |
| 403 | LIST_FORBIDDEN | 无权在此列表创建待办 | listId 对应的列表不属于当前用户 |
| 404 | LIST_NOT_FOUND | 列表不存在 | listId 对应的列表不存在 |

---

### 4.3 PUT /api/v1/todos/:id

**功能**：更新待办事项（标题/描述/优先级/所属列表）（F03）

**是否需要鉴权**：是

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 待办 UUID |

**Request Body**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| title | string | 否 | 新标题，1-255 字符 |
| description | string | 否 | 新描述，最长 2000 字符；传 null 可清空 |
| priority | string | 否 | 新优先级：`high`/`medium`/`low` |
| listId | string | 否 | 移动到新列表，UUID 格式 |

> 至少提供一个字段。

**Response 200**

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "title": "更新后的标题",
    "description": "更新后的描述",
    "priority": "high",
    "completed": false,
    "listId": "uuid-string",
    "listName": "工作",
    "listColor": "#E74C3C",
    "position": 0,
    "createdAt": "2026-05-11T10:00:00.000Z",
    "updatedAt": "2026-05-11T11:00:00.000Z"
  }
}
```

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 400 | VALIDATION_FAILED | 请求参数校验失败 | 无字段更新 / priority 值不合法 |
| 401 | AUTH_TOKEN_MISSING | 未提供认证令牌 | 同上 |
| 403 | TODO_FORBIDDEN | 无权操作此待办 | 待办不属于当前用户 |
| 403 | LIST_FORBIDDEN | 无权访问目标列表 | 移动到的 listId 不属于当前用户 |
| 404 | TODO_NOT_FOUND | 待办不存在 | id 对应的待办不存在 |
| 404 | LIST_NOT_FOUND | 目标列表不存在 | 移动到的 listId 不存在 |

---

### 4.4 PATCH /api/v1/todos/:id/toggle

**功能**：切换待办完成状态（F03）

**是否需要鉴权**：是

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 待办 UUID |

**Request Body**：无

**Response 200**

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "title": "完成周报",
    "description": "本周工作总结",
    "priority": "high",
    "completed": true,
    "listId": "uuid-string",
    "listName": "工作",
    "listColor": "#E74C3C",
    "position": 0,
    "createdAt": "2026-05-11T10:00:00.000Z",
    "updatedAt": "2026-05-11T11:00:00.000Z"
  }
}
```

> `completed` 为切换后的状态。

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 401 | AUTH_TOKEN_MISSING | 未提供认证令牌 | 同上 |
| 403 | TODO_FORBIDDEN | 无权操作此待办 | 待办不属于当前用户 |
| 404 | TODO_NOT_FOUND | 待办不存在 | id 对应的待办不存在 |

---

### 4.5 DELETE /api/v1/todos/:id

**功能**：删除待办事项（F03）

**是否需要鉴权**：是

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 待办 UUID |

**Request Body**：无

**Response 200**

```json
{
  "success": true,
  "data": {
    "message": "待办已删除"
  }
}
```

**错误码**

| HTTP 状态码 | error.code | error.message | 触发条件 |
|-------------|-----------|---------------|---------|
| 401 | AUTH_TOKEN_MISSING | 未提供认证令牌 | 同上 |
| 403 | TODO_FORBIDDEN | 无权操作此待办 | 待办不属于当前用户 |
| 404 | TODO_NOT_FOUND | 待办不存在 | id 对应的待办不存在 |

---

## 5. 接口总览

| 方法 | 路径 | 功能编号 | 说明 |
|------|------|---------|------|
| POST | /api/v1/auth/register | F01 | 用户注册 |
| POST | /api/v1/auth/login | F01 | 用户登录 |
| GET | /api/v1/users/me | F05 | 获取当前用户信息 |
| PUT | /api/v1/users/me | F05 | 修改昵称 |
| PUT | /api/v1/users/me/password | F05 | 修改密码 |
| GET | /api/v1/lists | F02 | 获取所有列表 |
| POST | /api/v1/lists | F02 | 创建列表 |
| PUT | /api/v1/lists/:id | F02 | 更新列表 |
| DELETE | /api/v1/lists/:id | F02 | 删除列表 |
| GET | /api/v1/todos | F03, F04 | 获取待办（筛选/搜索） |
| POST | /api/v1/todos | F03 | 创建待办 |
| PUT | /api/v1/todos/:id | F03 | 更新待办 |
| PATCH | /api/v1/todos/:id/toggle | F03 | 切换完成状态 |
| DELETE | /api/v1/todos/:id | F03 | 删除待办 |
