# API 接口契约
> 版本: 1.0 | 基础路径: /api/v1
> 本文件是唯一权威接口定义，前后端实现必须严格遵守

## 认证说明

### 微信登录鉴权

需要鉴权的接口，请求头携带：

```
Authorization: Bearer {JWT_TOKEN}
```

Token 过期返回 401，前端需重新调用 wx.login 刷新。

---

## 统一响应格式

**成功响应** (200)：

```json
{
  "data": { ... },
  "message": "success"
}
```

**失败响应**：

```json
{
  "error": "error_code",
  "message": "人类可读的错误描述"
}
```

**分页响应**：

```json
{
  "data": {
    "list": [ ... ],
    "total": 100,
    "page": 1,
    "pageSize": 20
  },
  "message": "success"
}
```

---

## 错误码定义

| HTTP 状态码 | error 字段 | 说明 |
|------------|-----------|------|
| 400 | `bad_request` | 请求参数错误 |
| 401 | `unauthorized` | 未登录或 token 过期 |
| 403 | `forbidden` | 无权限访问 |
| 404 | `not_found` | 资源不存在 |
| 409 | `already_checked_in` | 今日已打卡 |
| 500 | `internal_error` | 服务器内部错误 |
| 502 | `wx_api_error` | 微信接口调用失败 |

---

## 认证模块

### POST /api/v1/auth/wx-login

**用途**：微信登录，获取 JWT token
**鉴权**：不需要

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | wx.login 获取的临时登录凭证 |
| userInfo | object | 否 | 用户信息（头像、昵称） |
| userInfo.nickName | string | 否 | 用户昵称 |
| userInfo.avatarUrl | string | 否 | 用户头像 URL |

**请求示例**：

```json
{
  "code": "abc123def456",
  "userInfo": {
    "nickName": "张三",
    "avatarUrl": "https://thirdwx.qlogo.cn/mmopen/..."
  }
}
```

**成功响应** (200)：

| 字段 | 类型 | 说明 |
|------|------|------|
| data.token | string | JWT token，后续请求携带 |
| data.isNewUser | boolean | 是否为新注册用户 |
| data.userInfo | object | 用户信息 |
| data.userInfo.id | number | 用户 ID |
| data.userInfo.nickName | string | 用户昵称 |
| data.userInfo.avatarUrl | string | 用户头像 URL |

**响应示例**：

```json
{
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "isNewUser": false,
    "userInfo": {
      "id": 1,
      "nickName": "张三",
      "avatarUrl": "https://thirdwx.qlogo.cn/mmopen/..."
    }
  },
  "message": "success"
}
```

**错误响应**：

| HTTP 状态码 | error 字段 | 触发条件 |
|------------|-----------|---------|
| 400 | `missing_code` | 缺少 code 参数 |
| 400 | `invalid_code` | code 无效或已过期 |
| 502 | `wx_api_error` | 微信接口调用失败 |

---

## 打卡模块

### POST /api/v1/checkin

**用途**：每日打卡签到
**鉴权**：需要

**请求体**：无

**成功响应** (200)：

| 字段 | 类型 | 说明 |
|------|------|------|
| data.checkinId | number | 打卡记录 ID |
| data.checkinDate | string | 打卡日期（YYYY-MM-DD） |
| data.consecutiveDays | number | 当前连续打卡天数 |
| data.maxConsecutiveDays | number | 历史最高连续打卡天数 |

**响应示例**：

```json
{
  "data": {
    "checkinId": 42,
    "checkinDate": "2026-05-12",
    "consecutiveDays": 7,
    "maxConsecutiveDays": 15
  },
  "message": "success"
}
```

**错误响应**：

| HTTP 状态码 | error 字段 | 触发条件 |
|------------|-----------|---------|
| 401 | `unauthorized` | 未登录或 token 过期 |
| 409 | `already_checked_in` | 今日已打卡 |

---

### GET /api/v1/checkin/status

**用途**：获取今日打卡状态
**鉴权**：需要

**请求参数**：无

**成功响应** (200)：

| 字段 | 类型 | 说明 |
|------|------|------|
| data.isCheckedIn | boolean | 今日是否已打卡 |
| data.checkinDate | string | 今日日期（YYYY-MM-DD） |
| data.consecutiveDays | number | 当前连续打卡天数 |
| data.maxConsecutiveDays | number | 历史最高连续打卡天数 |

**响应示例**：

```json
{
  "data": {
    "isCheckedIn": true,
    "checkinDate": "2026-05-12",
    "consecutiveDays": 7,
    "maxConsecutiveDays": 15
  },
  "message": "success"
}
```

**错误响应**：

| HTTP 状态码 | error 字段 | 触发条件 |
|------------|-----------|---------|
| 401 | `unauthorized` | 未登录或 token 过期 |

---

### GET /api/v1/checkin/history

**用途**：获取打卡历史记录
**鉴权**：需要

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| year | number | 否 | 年份，默认当前年 |
| month | number | 否 | 月份，默认当前月 |
| page | number | 否 | 页码，默认 1 |
| pageSize | number | 否 | 每页数量，默认 31 |

**请求示例**：

```
GET /api/v1/checkin/history?year=2026&month=5&page=1&pageSize=31
```

**成功响应** (200)：

| 字段 | 类型 | 说明 |
|------|------|------|
| data.list | array | 打卡记录列表 |
| data.list[].id | number | 记录 ID |
| data.list[].checkinDate | string | 打卡日期（YYYY-MM-DD） |
| data.list[].createdAt | string | 打卡时间（ISO 8601） |
| data.total | number | 当月打卡总天数 |
| data.year | number | 查询年份 |
| data.month | number | 查询月份 |

**响应示例**：

```json
{
  "data": {
    "list": [
      {
        "id": 42,
        "checkinDate": "2026-05-12",
        "createdAt": "2026-05-12T08:30:00Z"
      },
      {
        "id": 41,
        "checkinDate": "2026-05-11",
        "createdAt": "2026-05-11T09:15:00Z"
      }
    ],
    "total": 12,
    "year": 2026,
    "month": 5
  },
  "message": "success"
}
```

**错误响应**：

| HTTP 状态码 | error 字段 | 触发条件 |
|------------|-----------|---------|
| 401 | `unauthorized` | 未登录或 token 过期 |

---

## 用户模块

### GET /api/v1/users/me

**用途**：获取当前用户信息及统计数据
**鉴权**：需要

**请求参数**：无

**成功响应** (200)：

| 字段 | 类型 | 说明 |
|------|------|------|
| data.id | number | 用户 ID |
| data.nickName | string | 用户昵称 |
| data.avatarUrl | string | 用户头像 URL |
| data.totalCheckinDays | number | 总打卡天数 |
| data.consecutiveDays | number | 当前连续打卡天数 |
| data.maxConsecutiveDays | number | 历史最高连续打卡天数 |
| data.createdAt | string | 注册时间（ISO 8601） |

**响应示例**：

```json
{
  "data": {
    "id": 1,
    "nickName": "张三",
    "avatarUrl": "https://thirdwx.qlogo.cn/mmopen/...",
    "totalCheckinDays": 45,
    "consecutiveDays": 7,
    "maxConsecutiveDays": 15,
    "createdAt": "2026-04-01T10:00:00Z"
  },
  "message": "success"
}
```

**错误响应**：

| HTTP 状态码 | error 字段 | 触发条件 |
|------------|-----------|---------|
| 401 | `unauthorized` | 未登录或 token 过期 |
| 404 | `not_found` | 用户不存在 |

---

## 健康检查

### GET /api/v1/health

**用途**：服务健康检查
**鉴权**：不需要

**成功响应** (200)：

```json
{
  "data": {
    "status": "ok",
    "timestamp": "2026-05-12T08:30:00Z"
  },
  "message": "success"
}
```

---

## 接口汇总

| 方法 | 路径 | 鉴权 | 用途 |
|------|------|------|------|
| POST | /api/v1/auth/wx-login | 否 | 微信登录 |
| POST | /api/v1/checkin | 是 | 每日打卡 |
| GET | /api/v1/checkin/status | 是 | 获取今日打卡状态 |
| GET | /api/v1/checkin/history | 是 | 获取打卡历史 |
| GET | /api/v1/users/me | 是 | 获取用户信息 |
| GET | /api/v1/health | 否 | 健康检查 |

---

## 完成标志

docs/API_CONTRACT.md 已创建，包含：
- 6 个接口的完整定义
- 每个字段的类型、必填项、说明
- 所有错误码和触发条件
- 请求/响应示例
- 微信登录接口（POST /api/v1/auth/wx-login）
