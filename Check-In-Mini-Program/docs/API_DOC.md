# API 接口文档
> 基于 API_CONTRACT v1.0
> 基础路径: /api/v1

## 认证说明

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

微信登录，获取 JWT token。无需鉴权。

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | wx.login 获取的临时登录凭证 |
| userInfo | object | 否 | 用户信息 |
| userInfo.nickName | string | 否 | 用户昵称 |
| userInfo.avatarUrl | string | 否 | 用户头像 URL |

**成功响应** (200)：

| 字段 | 类型 | 说明 |
|------|------|------|
| data.token | string | JWT token |
| data.isNewUser | boolean | 是否为新注册用户 |
| data.userInfo.id | number | 用户 ID |
| data.userInfo.nickName | string | 用户昵称 |
| data.userInfo.avatarUrl | string | 用户头像 URL |

**错误响应**：

| HTTP 状态码 | error 字段 | 触发条件 |
|------------|-----------|---------|
| 400 | `missing_code` | 缺少 code 参数 |
| 400 | `invalid_code` | code 无效或已过期 |
| 502 | `wx_api_error` | 微信接口调用失败 |

---

## 打卡模块

### POST /api/v1/checkin

每日打卡签到。需要鉴权。

**请求体**：无

**成功响应** (200)：

| 字段 | 类型 | 说明 |
|------|------|------|
| data.checkinId | number | 打卡记录 ID |
| data.checkinDate | string | 打卡日期（YYYY-MM-DD） |
| data.consecutiveDays | number | 当前连续打卡天数 |
| data.maxConsecutiveDays | number | 历史最高连续打卡天数 |

**错误响应**：

| HTTP 状态码 | error 字段 | 触发条件 |
|------------|-----------|---------|
| 401 | `unauthorized` | 未登录或 token 过期 |
| 409 | `already_checked_in` | 今日已打卡 |

---

### GET /api/v1/checkin/status

获取今日打卡状态。需要鉴权。

**成功响应** (200)：

| 字段 | 类型 | 说明 |
|------|------|------|
| data.isCheckedIn | boolean | 今日是否已打卡 |
| data.checkinDate | string | 今日日期（YYYY-MM-DD） |
| data.consecutiveDays | number | 当前连续打卡天数 |
| data.maxConsecutiveDays | number | 历史最高连续打卡天数 |

---

### GET /api/v1/checkin/history

获取打卡历史记录。需要鉴权。

**查询参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| year | number | 否 | 年份，默认当前年 |
| month | number | 否 | 月份，默认当前月 |
| page | number | 否 | 页码，默认 1 |
| pageSize | number | 否 | 每页数量，默认 31 |

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

---

## 用户模块

### GET /api/v1/users/me

获取当前用户信息及统计数据。需要鉴权。

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

---

## 健康检查

### GET /api/v1/health

服务健康检查。无需鉴权。

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
