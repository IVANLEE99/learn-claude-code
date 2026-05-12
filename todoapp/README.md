# Todo App

> 一款极简高效的待办事项管理应用，3 秒完成待办创建，通过列表分类与优先级排序帮你聚焦真正重要的事。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Vue 3 + Composition API | `<script setup>` 风格 |
| 构建工具 | Vite 5.x | 原生 ESM + 快速 HMR |
| 状态管理 | Pinia 2.x | 按资源拆分 Store |
| 路由 | Vue Router 4.x | 导航守卫 + query 参数 |
| 后端框架 | Express.js 4.x | TypeScript strict 模式 |
| 数据库 | PostgreSQL 15+ | Docker 部署 |
| ORM | Prisma 5.x | 类型安全 + 迁移管理 |
| 认证 | JWT (Bearer Token) | 无状态鉴权，7 天有效期 |
| 参数校验 | Zod 3.x | 前后端共享 schema |
| 容器化 | Docker + docker-compose | 一键启动全部服务 |

---

## 本地开发

### 前提条件

- Node.js 20+
- npm 9+
- Docker & Docker Compose（用于运行 PostgreSQL）

### 1. 启动数据库

```bash
docker compose up db -d
```

数据库将在 `localhost:5432` 启动，默认用户 `todo`，密码 `todo`，数据库 `todoapp`。

### 2. 启动后端

```bash
cd backend
npm install
npx prisma generate
npx prisma migrate dev
npm run dev
```

后端运行在 `http://localhost:3000`，支持热重载（tsx watch）。

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 `http://localhost:5173`，API 请求代理到后端 `http://localhost:3000`。

> 前端开发时使用 `frontend/.env` 中的环境变量，`VITE_API_BASE=/api/v1`，需在 `vite.config.ts` 中配置 proxy 将 `/api` 代理到后端。

---

## 环境变量

### 后端环境变量

| 变量名 | 说明 | 本地默认值 | 生产值 | 必填 |
|--------|------|-----------|--------|------|
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql://todo:todo@localhost:5432/todoapp` | 实际连接串（Docker 中为 `postgresql://todo:todo@db:5432/todoapp`） | 是 |
| `JWT_SECRET` | JWT 签名密钥 | `dev-secret-change-me` | 随机 64 字符字符串 | 是 |
| `JWT_EXPIRES_IN` | Token 有效期 | `7d` | `7d` | 是 |
| `PORT` | 后端监听端口 | `3000` | `3000` | 是 |
| `CORS_ORIGIN` | 允许的前端来源 | `http://localhost:5173` | 实际域名（如 `https://example.com`） | 是 |

### 前端环境变量

| 变量名 | 说明 | 本地开发值 | 生产值 | 必填 |
|--------|------|-----------|--------|------|
| `VITE_API_BASE` | API 请求基础路径 | `/api/v1` | `/todoapp/api/v1` | 是 |
| `VITE_BASE_URL` | 前端部署基础路径 | `/` | `/todoapp/` | 是 |

---

## 首次部署

以下步骤在服务器上执行，使用 Docker Compose 一键启动全部服务。

### 1. 创建项目目录并上传代码

```bash
mkdir -p /opt/todoapp
# 将项目代码上传到 /opt/todoapp，确保目录中包含：
#   docker-compose.yml, Dockerfile.backend, Dockerfile.frontend, nginx.conf
#   backend/, frontend/
```

### 2. 创建 .env 文件

```bash
cd /opt/todoapp
cp .env.example .env
```

编辑 `.env`，填入生产环境值：

```bash
# 必须修改这两项
JWT_SECRET=<随机 64 字符字符串>
CORS_ORIGIN=https://your-domain.com
```

生成随机密钥的方式：

```bash
openssl rand -hex 32
```

### 3. 配置 Nginx 反向代理

如果服务器上已有 Nginx，在站点配置中添加 location 指向 Todo App 容器：

```nginx
# 在已有的 server 块中添加
location /todoapp/ {
    proxy_pass http://127.0.0.1:80/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

如果不需要外部 Nginx 层，Todo App 自带的 `nginx.conf` 已包含完整的路由规则，直接暴露容器的 80 端口即可。

### 4. 启动服务

```bash
docker compose up -d --build
```

首次启动时后端容器会自动执行数据库迁移（`prisma migrate deploy`），然后启动服务。

验证部署状态：

```bash
# 检查容器状态
docker compose ps

# 查看后端日志
docker compose logs backend

# 测试 API
curl http://localhost/todoapp/api/v1/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123456"}'
```

---

## 代码更新后重新部署

当代码有更新需要重新部署时：

```bash
cd /opt/todoapp

# 拉取最新代码（如果使用 Git）
git pull

# 重新构建并启动（数据库迁移在后端启动时自动执行）
docker compose up -d --build

# 查看启动日志确认迁移与启动正常
docker compose logs -f backend
```

如果只更新了前端代码，可以单独重建前端：

```bash
docker compose up -d --build frontend
```

如果只更新了后端代码：

```bash
docker compose up -d --build backend
```

---

## 数据库迁移

项目使用 Prisma Migrate 管理数据库迁移。所有迁移文件存放在 `backend/prisma/migrations/` 目录。

### 本地开发：新增迁移

当你修改了 `backend/prisma/schema.prisma` 中的模型定义后，执行以下命令创建迁移文件：

```bash
cd backend
npx prisma migrate dev --name 描述性名称
```

示例：

```bash
npx prisma migrate dev --name add-due-date-to-todos
```

该命令会：

1. 根据 schema 变更自动生成 SQL 迁移文件
2. 在本地数据库上执行迁移
3. 重新生成 Prisma Client 类型

### 迁移文件命名规范

Prisma 自动生成迁移目录，格式为 `YYYYMMDDHHMMSS_描述`，例如：

```
prisma/migrations/
  20260511100000_init/
    migration.sql
  20260511150000_add-due-date-to-todos/
    migration.sql
```

**不可修改或删除已有的迁移文件**，只能新增。

### 生产环境：执行迁移

生产环境通过 Docker 容器启动脚本自动执行 `npx prisma migrate deploy`，该命令只应用尚未执行的迁移，不会创建新迁移。

手动执行迁移（如需单独操作）：

```bash
cd backend
npx prisma migrate deploy
```

查看迁移状态：

```bash
npx prisma migrate status
```

### 常用 Prisma 命令速查

| 命令 | 用途 |
|------|------|
| `npx prisma migrate dev --name <名称>` | 创建并应用新迁移（开发环境） |
| `npx prisma migrate deploy` | 应用未执行的迁移（生产环境） |
| `npx prisma migrate status` | 查看迁移状态 |
| `npx prisma generate` | 重新生成 Prisma Client 类型 |
| `npx prisma db push` | 将 schema 直接推送到数据库（不创建迁移文件，慎用） |

---

## 项目目录结构

```
todoapp/
├── docs/                              # 项目文档
│   ├── PRD.md                         # 产品需求文档
│   ├── TECH_SPEC.md                   # 技术规格文档
│   ├── API_CONTRACT.md                # API 契约文档
│   ├── DB_SCHEMA.md                   # 数据库 Schema 文档
│   ├── DESIGN_SYSTEM.md               # 设计系统文档
│   ├── SECURITY_REPORT.md             # 安全审查报告
│   ├── REVIEW_REPORT.md               # 代码评审报告
│   └── API_DOC.md                     # API 参考文档（面向开发者）
├── project-tasks/                     # 任务清单
│   ├── backend-tasklist.md
│   └── frontend-tasklist.md
├── backend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── prisma/
│   │   ├── schema.prisma              # Prisma 数据模型定义
│   │   └── migrations/               # 数据库迁移文件（自动生成）
│   ├── src/
│   │   ├── index.ts                   # 入口，Express 启动
│   │   ├── config/
│   │   │   ├── env.ts                 # 环境变量加载与校验
│   │   │   └── prisma.ts             # Prisma Client 单例
│   │   ├── middleware/
│   │   │   ├── auth.ts                # JWT 鉴权中间件
│   │   │   └── errorHandler.ts       # 统一错误处理
│   │   ├── routes/
│   │   │   ├── auth.routes.ts         # /api/v1/auth/*
│   │   │   ├── users.routes.ts        # /api/v1/users/*
│   │   │   ├── lists.routes.ts        # /api/v1/lists/*
│   │   │   └── todos.routes.ts        # /api/v1/todos/*
│   │   ├── services/
│   │   │   ├── auth.service.ts        # 认证业务逻辑
│   │   │   ├── user.service.ts        # 用户业务逻辑
│   │   │   ├── list.service.ts        # 列表业务逻辑
│   │   │   └── todo.service.ts        # 待办业务逻辑
│   │   └── utils/
│   │       └── ApiError.ts            # 统一错误类
│   └── scripts/
│       ├── start.sh                   # Docker 容器启动脚本
│       ├── migrate.ts                 # 迁移执行脚本
│       └── seed.ts                    # 初始数据脚本
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── .env                           # 本地开发环境变量
│   ├── .env.production                # 生产环境变量
│   ├── src/
│   │   ├── main.ts                    # 应用入口
│   │   ├── App.vue                    # 根组件
│   │   ├── router/
│   │   │   └── index.ts              # 路由定义 + 导航守卫
│   │   ├── stores/
│   │   │   ├── auth.store.ts          # 认证状态
│   │   │   ├── list.store.ts          # 列表状态
│   │   │   ├── todo.store.ts          # 待办状态
│   │   │   └── user.store.ts          # 用户状态
│   │   ├── api/
│   │   │   ├── client.ts             # axios 实例（baseURL + 拦截器）
│   │   │   ├── auth.api.ts           # 认证 API
│   │   │   ├── user.api.ts           # 用户 API
│   │   │   ├── list.api.ts           # 列表 API
│   │   │   └── todo.api.ts           # 待办 API
│   │   ├── views/
│   │   │   ├── LoginView.vue         # 登录页
│   │   │   ├── RegisterView.vue      # 注册页
│   │   │   ├── HomeView.vue          # 待办主页
│   │   │   └── SettingsView.vue      # 个人设置页
│   │   ├── components/
│   │   │   ├── TodoCard.vue           # 待办卡片
│   │   │   ├── TodoForm.vue           # 待办表单
│   │   │   ├── ListNav.vue            # 列表导航
│   │   │   ├── ListItem.vue           # 列表导航项
│   │   │   ├── FilterBar.vue          # 筛选栏
│   │   │   └── EmptyState.vue         # 空状态
│   │   ├── composables/
│   │   │   └── useAuth.ts            # 认证组合函数
│   │   └── styles/
│   │       └── variables.css          # CSS 变量（设计系统）
│   └── public/
│       └── favicon.ico
├── docker-compose.yml                 # Docker Compose 编排
├── Dockerfile.backend                 # 后端镜像构建
├── Dockerfile.frontend                # 前端镜像构建
├── nginx.conf                         # Nginx 反向代理配置
├── .env.example                       # 环境变量模板
└── README.md                          # 项目说明（本文件）
```

---

## License

MIT
