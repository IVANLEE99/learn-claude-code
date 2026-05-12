# 技术规格文档 (TECH_SPEC) -- Todo App

> 版本：1.0
> 日期：2026-05-11
> 作者：software-architect
> 基于：PRD v1.0

---

## 1. 技术栈

| 层级 | 技术选型 | 版本 | 选型理由 |
|------|---------|------|---------|
| 前端框架 | Vue 3 (Composition API) | 3.4+ | 轻量、移动端友好、生态成熟 |
| 构建工具 | Vite | 5.x | 快速 HMR、原生 ESM |
| 状态管理 | Pinia | 2.x | Vue 3 官方推荐、TypeScript 友好 |
| 路由 | Vue Router | 4.x | 支持导航守卫、query 参数 |
| 后端框架 | Express.js | 4.x | 轻量、中间件丰富、社区成熟 |
| 数据库 | PostgreSQL | 15+ | 支持 JSON 字段、事务完整、Docker 部署方便 |
| ORM | Prisma | 5.x | 类型安全、迁移管理、自动生成类型 |
| 认证 | JWT (jsonwebtoken) | 9.x | 无状态鉴权，适合单页应用 |
| 密码哈希 | bcryptjs | 2.x | 纯 JS 实现，跨平台 |
| 参数校验 | Zod | 3.x | 前后端共享 schema、类型推断 |
| 容器化 | Docker + docker-compose | - | 一键启动、环境一致 |

---

## 2. 项目目录结构

```
todoapp/
├── docs/                          # 契约文档（不部署）
│   ├── PRD.md
│   ├── TECH_SPEC.md
│   ├── API_CONTRACT.md
│   ├── DB_SCHEMA.md
│   ├── DESIGN_SYSTEM.md
│   └── ...
├── project-tasks/                 # 任务清单
│   ├── backend-tasklist.md
│   └── frontend-tasklist.md
├── backend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── prisma/
│   │   ├── schema.prisma          # Prisma 数据模型
│   │   └── migrations/            # 数据库迁移文件
│   ├── src/
│   │   ├── index.ts               # 入口、Express 启动
│   │   ├── config/
│   │   │   └── env.ts             # 环境变量加载与校验
│   │   ├── middleware/
│   │   │   ├── auth.ts            # JWT 鉴权中间件
│   │   │   └── errorHandler.ts    # 统一错误处理
│   │   ├── routes/
│   │   │   ├── auth.routes.ts     # /api/v1/auth/*
│   │   │   ├── users.routes.ts    # /api/v1/users/*
│   │   │   ├── lists.routes.ts    # /api/v1/lists/*
│   │   │   └── todos.routes.ts    # /api/v1/todos/*
│   │   ├── services/
│   │   │   ├── auth.service.ts
│   │   │   ├── user.service.ts
│   │   │   ├── list.service.ts
│   │   │   └── todo.service.ts
│   │   └── utils/
│   │       └── ApiError.ts        # 统一错误类
│   └── scripts/
│       ├── migrate.ts             # 迁移执行脚本
│       └── seed.ts                # 初始数据脚本
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── .env                        # 本地开发环境变量
│   ├── .env.production             # 生产环境变量
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.ts           # 路由定义 + 导航守卫
│   │   ├── stores/
│   │   │   ├── auth.store.ts
│   │   │   ├── list.store.ts
│   │   │   ├── todo.store.ts
│   │   │   └── user.store.ts
│   │   ├── api/
│   │   │   ├── client.ts          # axios 实例（baseURL 来自环境变量）
│   │   │   ├── auth.api.ts
│   │   │   ├── user.api.ts
│   │   │   ├── list.api.ts
│   │   │   └── todo.api.ts
│   │   ├── views/
│   │   │   ├── LoginView.vue
│   │   │   ├── RegisterView.vue
│   │   │   ├── HomeView.vue
│   │   │   └── SettingsView.vue
│   │   ├── components/
│   │   │   ├── TodoCard.vue
│   │   │   ├── TodoForm.vue
│   │   │   ├── ListNav.vue
│   │   │   ├── ListItem.vue
│   │   │   ├── FilterBar.vue
│   │   │   └── EmptyState.vue
│   │   ├── composables/
│   │   │   └── useAuth.ts
│   │   └── styles/
│   │       └── variables.css      # CSS 变量（设计系统）
│   └── public/
│       └── favicon.ico
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.conf                     # 前端反向代理 + API 代理
└── .env.example                   # 环境变量模板
```

---

## 3. 环境变量

### 3.1 后端环境变量

| 变量名 | 说明 | 本地默认值 | 生产值 | 必填 |
|--------|------|-----------|--------|------|
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql://todo:todo@localhost:5432/todoapp` | 实际连接串 | 是 |
| `JWT_SECRET` | JWT 签名密钥 | `dev-secret-change-me` | 随机 64 字符 | 是 |
| `JWT_EXPIRES_IN` | Token 有效期 | `7d` | `7d` | 是 |
| `PORT` | 后端监听端口 | `3000` | `3000` | 是 |
| `CORS_ORIGIN` | 允许的前端来源 | `http://localhost:5173` | 实际域名 | 是 |

### 3.2 前端环境变量

| 变量名 | 说明 | 本地默认值 | 生产值 | 必填 |
|--------|------|-----------|--------|------|
| `VITE_API_BASE` | API 请求基础路径 | `/api/v1` | `/todoapp/api/v1` | 是 |
| `VITE_BASE_URL` | 前端部署基础路径 | `/` | `/todoapp/` | 是 |

---

## 4. 部署路径规范

### 4.1 核心约定

- **APP_PATH**：`todoapp`（不含前后斜杠）
- 生产环境下，应用部署在 `https://domain.com/todoapp/` 下
- 本地开发时无前缀，直接 `http://localhost:5173/`

### 4.2 前端 API 调用层规范

**禁止硬编码 `/api/...` 路径。** 所有 API 请求必须通过 `frontend/src/api/client.ts` 中的 axios 实例发送，该实例的 `baseURL` 从 `VITE_API_BASE` 读取：

```typescript
// frontend/src/api/client.ts
import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：自动附加 JWT
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：401 时清除 token 并跳转登录
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = `${import.meta.env.VITE_BASE_URL}login`
    }
    return Promise.reject(error)
  },
)

export default client
```

### 4.3 Vite 配置规范

```typescript
// vite.config.ts
export default defineConfig({
  base: process.env.VITE_BASE_URL || '/',
  // ... 其他配置
})
```

### 4.4 Nginx 配置要点

- `/todoapp/` 指向前端静态文件
- `/todoapp/api/` 代理到后端 `http://backend:3000/api/`
- SPA 回退：`try_files $uri $uri/ /todoapp/index.html`

### 4.5 .env / .env.production 模板

**frontend/.env**（本地开发）
```
VITE_API_BASE=/api/v1
VITE_BASE_URL=/
```

**frontend/.env.production**（生产部署）
```
VITE_API_BASE=/todoapp/api/v1
VITE_BASE_URL=/todoapp/
```

---

## 5. 编码规范

### 5.1 通用

- 缩进：2 空格
- 文件编码：UTF-8
- 换行符：LF
- 命名：camelCase（变量/函数）、PascalCase（类/组件/Vue 文件）、kebab-case（CSS 类名）

### 5.2 后端

- 语言：TypeScript（strict 模式）
- 错误处理：统一使用 `ApiError` 类，通过 `errorHandler` 中间件统一返回
- 响应格式：所有接口返回 `{ success: boolean, data?: any, error?: { code: string, message: string } }`
- 路由定义：每个资源独立路由文件，在 `index.ts` 中挂载
- 服务层：业务逻辑放在 `services/` 目录，路由层只做参数校验和服务调用

### 5.3 前端

- 语言：TypeScript
- 组件风格：`<script setup lang="ts">` + `<style scoped>`
- 状态管理：Pinia store，按资源拆分
- API 调用：统一通过 `src/api/client.ts` 实例，禁止在组件中直接使用 `fetch` 或裸 `axios`
- 样式：全部使用 `src/styles/variables.css` 中定义的 CSS 变量，禁止硬编码颜色值、字号、间距值
- 路由跳转：使用 Vue Router 的 `router.push` / `router.replace`，不使用 `window.location`

---

## 6. API 前缀与版本

- 所有后端接口前缀：`/api/v1/`
- Nginx 代理规则：`/todoapp/api/v1/` -> `http://backend:3000/api/v1/`
- 前端 axios baseURL：读取 `VITE_API_BASE` 环境变量

---

## 7. 认证流程

1. 用户注册/登录 -> 后端返回 JWT Token
2. 前端存储 Token 到 `localStorage`（key: `token`）
3. 每个 API 请求通过 axios 拦截器自动附加 `Authorization: Bearer <token>`
4. 后端 `auth` 中间件校验 Token，将 `userId` 注入 `req.userId`
5. Token 过期或无效 -> 返回 401 -> 前端拦截器清除 Token 并跳转登录页

---

## 8. 错误处理规范

### 8.1 后端统一错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "邮箱或密码错误"
  }
}
```

### 8.2 错误码分类

| 前缀 | 类别 | 示例 |
|------|------|------|
| `AUTH_` | 认证相关 | `AUTH_INVALID_CREDENTIALS`, `AUTH_TOKEN_EXPIRED` |
| `USER_` | 用户相关 | `USER_NOT_FOUND`, `USER_EMAIL_EXISTS` |
| `LIST_` | 列表相关 | `LIST_NOT_FOUND`, `LIST_NAME_EMPTY` |
| `TODO_` | 待办相关 | `TODO_NOT_FOUND`, `TODO_TITLE_EMPTY` |
| `VALIDATION_` | 参数校验 | `VALIDATION_FAILED` |
| `SERVER_` | 服务端错误 | `SERVER_INTERNAL_ERROR` |
