# 技术规格说明
> 版本: 1.0 | 更新日期: 2026-05-12

## 项目信息

| 项目 | 内容 |
|------|------|
| 项目名称 | Check-In-Mini-Program |
| 项目类型 | 微信小程序 |
| 版本 | MVP v1.0 |

---

## 技术栈选型

| 层级 | 技术选型 | 选型理由 |
|------|---------|---------|
| 小程序前端 | 原生开发 | 项目页面少（3个），无需跨端框架，原生开发包体积最小、性能最优 |
| 后端框架 | Node.js + Koa 2 | 轻量级、异步友好、中间件生态成熟 |
| 数据库 | MySQL 8.0 | 成熟稳定、社区资源丰富、适合结构化数据 |
| 缓存 | 不需要 | MVP 阶段用户量小，数据库直接查询即可 |
| 认证方案 | 微信登录 + JWT | 小程序标配，无状态鉴权 |
| 部署方式 | Docker + docker-compose | 环境一致性、易于部署和扩展 |
| ORM | Prisma | 类型安全、迁移管理方便、开发体验好 |

---

## 微信登录方案

### 登录流程

```
小程序端                     后端                      微信服务器
   │                          │                          │
   ├─ wx.login() ──────────► │                          │
   │   返回 code             │                          │
   │                          ├─ code + appid + secret ─►│
   │                          │   POST /sns/jscode2session
   │                          │   返回 openid +          │
   │                          │   session_key            │
   │                          │                          │
   │                          ├─ 生成 JWT token          │
   │                          ├─ 创建/更新用户记录       │
   │                          │                          │
   │   ◄── token + 用户信息 ──┤                          │
   │                          │                          │
   │   后续请求携带 token     │                          │
   │   Authorization: Bearer  │                          │
```

### 登录接口设计原则

1. **code 一次性使用**：后端立即换取 openid，不缓存 code
2. **session_key 存后端**：不返回前端，用于后续解密敏感数据
3. **JWT token 鉴权**：后端生成自定义 JWT token 返回前端
4. **openid 不暴露**：存数据库做用户标识，不返回前端
5. **unionid 按需获取**：需绑定微信开放平台，MVP 阶段不使用

### JWT Token 设计

```
Payload:
{
  "userId": 123,           // 用户数据库 ID
  "iat": 1684567890,       // 签发时间
  "exp": 1685172690        // 过期时间（7天）
}
```

---

## 项目目录结构

### 小程序前端

```
miniprogram/
├── app.js                      # 小程序入口
├── app.json                    # 全局配置
├── app.wxss                    # 全局样式
├── project.config.json         # 项目配置
├── sitemap.json                # 站点地图
├── config/
│   └── env.js                  # 环境配置（API 地址等）
├── utils/
│   ├── request.js              # wx.request 封装
│   ├── auth.js                 # 登录态管理
│   └── util.js                 # 通用工具函数
├── styles/
│   └── variables.wxss          # 设计规范变量
├── components/                 # 自定义组件
│   ├── check-button/           # 打卡按钮组件
│   └── calendar/               # 日历组件
└── pages/                      # 页面
    ├── index/                  # 首页（打卡按钮 + 连续天数）
    │   ├── index.wxml
    │   ├── index.wxss
    │   ├── index.js
    │   └── index.json
    ├── history/                # 打卡记录/日历
    │   ├── history.wxml
    │   ├── history.wxss
    │   ├── history.js
    │   └── history.json
    └── profile/                # 个人中心
        ├── profile.wxml
        ├── profile.wxss
        ├── profile.js
        └── profile.json
```

### 后端

```
backend/
├── package.json
├── .env                        # 环境变量（不提交 git）
├── .env.example                # 环境变量模板
├── prisma/
│   └── schema.prisma           # Prisma Schema
├── src/
│   ├── app.js                  # Koa 应用入口
│   ├── routes/
│   │   ├── auth.js             # 认证路由
│   │   ├── checkin.js          # 打卡路由
│   │   └── user.js             # 用户路由
│   ├── controllers/
│   │   ├── authController.js   # 认证控制器
│   │   ├── checkinController.js # 打卡控制器
│   │   └── userController.js   # 用户控制器
│   ├── services/
│   │   ├── wxService.js        # 微信 API 服务
│   │   ├── authService.js      # 认证服务
│   │   └── checkinService.js   # 打卡业务逻辑
│   ├── middleware/
│   │   ├── auth.js             # JWT 鉴权中间件
│   │   └── errorHandler.js     # 错误处理中间件
│   └── utils/
│       ├── jwt.js              # JWT 工具
│       └── response.js         # 响应格式化
├── docker-compose.yml
└── Dockerfile
```

---

## 全局规范

| 规范项 | 规则 | 示例 |
|--------|------|------|
| JSON 字段命名 | camelCase | `userId`、`createdAt` |
| 数据库字段命名 | snake_case | `user_id`、`created_at` |
| 时间格式 | ISO 8601 | `2026-05-12T08:30:00Z` |
| 分页参数 | `page`（从1开始）、`pageSize`（默认20） | `?page=1&pageSize=20` |
| 统一错误格式 | `{ "error": "error_code", "message": "描述" } | — |

---

## 环境变量

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `WX_APPID` | 小程序 AppID | `wx1234567890abcdef` |
| `WX_SECRET` | 小程序 AppSecret | `[从微信后台获取]` |
| `JWT_SECRET` | JWT 签名密钥 | `your-secret-key-min-32-chars` |
| `JWT_EXPIRES_IN` | Token 有效期 | `7d` |
| `DATABASE_URL` | 数据库连接串 | `mysql://user:pass@localhost:3306/checkin` |
| `PORT` | 服务端口 | `3000` |

---

## API 基础 URL 配置规范

> 小程序不涉及 CORS 问题，但 API 地址必须可配置，禁止硬编码。

**小程序端配置方式：**

```javascript
// ✅ 正确 — 配置文件
const API_BASE = require('../config/env.js').API_BASE
wx.request({ url: `${API_BASE}/api/v1/auth/wx-login` })

// ❌ 禁止 — 硬编码
wx.request({ url: 'http://localhost:3000/api/v1/auth/wx-login' })
```

**config/env.js 文件约定：**

```javascript
// config/env.js
const ENV = {
  development: {
    API_BASE: 'http://localhost:3000'
  },
  production: {
    API_BASE: 'https://api.your-domain.com'
  }
}

// 小程序环境判断
const accountInfo = wx.getAccountInfoSync()
const env = accountInfo.miniProgram.envVersion === 'release' ? 'production' : 'development'

module.exports = ENV[env]
```

---

## 包大小管理策略

| 限制项 | 上限 | 说明 |
|--------|------|------|
| 主包 | 2MB | 包含所有首页和公共资源 |
| 单个分包 | 2MB | 每个分包独立限制 |
| 总包大小 | 20MB | 所有包合计 |

**本项目策略：**
- 页面数量少（3个），无需分包
- 主包包含所有页面和公共资源
- 图片资源使用 CDN（如有），不放入包内
- 预计主包大小：< 500KB

---

## 微信小程序特有安全规范

| 规范项 | 规则 | 原因 |
|--------|------|------|
| CORS | 禁止 `origin: '*'` | 微信会判定安全风险 |
| API 鉴权 | 所有非健康检查接口必须鉴权 | 防止接口被盗刷 |
| 限流 | 基于 userId，不基于 IP | 小程序场景 IP 不可靠 |
| openid | 不返回前端 | 防止用户身份泄露 |
| 隐私协议 | 收集用户信息前展示隐私协议 | 微信合规要求 |

---

## 完成标志

docs/TECH_SPEC.md 已创建，包含：
- 技术栈选型及理由
- 微信登录方案（code2Session 流程）
- 项目目录结构
- 环境变量定义
- API 基础 URL 配置规范
- 包大小管理策略
- 安全规范
