# Docker 命令参考手册

本项目使用 Docker + Docker Compose 进行容器化部署，涉及 3 个服务：`db`（PostgreSQL）、`backend`（Node.js）、`frontend`（Nginx）。

---

## 一、服务编排命令（docker compose）

### 1. `docker compose up db -d`

**用途**：仅启动数据库服务（开发环境用）

**参数解析**：
- `up` — 创建并启动容器
- `db` — 指定只启动 `db` 服务（PostgreSQL 15）
- `-d` — 后台运行（detached 模式）

**场景**：本地开发时，前端和后端在宿主机直接运行，只需要容器化数据库。

**效果**：PostgreSQL 在 `localhost:5432` 启动，用户 `todo`，密码 `todo`，数据库 `todoapp`。

---

### 2. `docker compose up -d --build`

**用途**：构建并启动所有服务（生产部署用）

**参数解析**：
- `up` — 创建并启动容器
- `-d` — 后台运行
- `--build` — 启动前重新构建镜像（不使用缓存镜像）

**场景**：首次部署或全量更新后重新部署。

**效果**：
1. 重新构建 `backend` 镜像（Dockerfile.backend，多阶段构建）
2. 重新构建 `frontend` 镜像（Dockerfile.frontend，多阶段构建 + Nginx）
3. 启动 `db` → `backend`（等 db 健康检查通过后启动） → `frontend`
4. 后端启动时自动执行 `prisma migrate deploy` 数据库迁移

---

### 3. `docker compose up -d --build frontend`

**用途**：仅重建并重启前端服务

**参数解析**：
- `up -d --build` — 同上
- `frontend` — 只操作 frontend 服务

**场景**：只修改了前端代码，不需要重建后端和数据库。

**效果**：重新执行 Dockerfile.frontend 构建流程，重启 frontend 容器，后端和数据库不受影响。

---

### 4. `docker compose up -d --build backend`

**用途**：仅重建并重启后端服务

**参数解析**：同上，限定 backend 服务。

**场景**：只修改了后端代码，不需要重建前端和数据库。

**效果**：重新执行 Dockerfile.backend 构建流程，重启 backend 容器，启动时自动执行数据库迁移。

---

### 5. `docker compose ps`

**用途**：查看所有容器的运行状态

**输出示例**：
```
NAME          STATUS          PORTS
todoapp-db     Up (healthy)    0.0.0.0:5432->5432/tcp
todoapp-backend  Up             0.0.0.0:3000->3000/tcp
todoapp-frontend Up             0.0.0.0:80->80/tcp
```

**场景**：部署后验证各服务是否正常运行。注意 `db` 服务有健康检查（`pg_isready`），需显示 `healthy` 才表示数据库就绪。

---

### 6. `docker compose logs backend`

**用途**：查看后端服务的日志输出

**参数解析**：
- `logs` — 输出容器日志
- `backend` — 只看 backend 服务的日志

**场景**：排查后端问题、确认数据库迁移是否成功。

---

### 7. `docker compose logs -f backend`

**用途**：实时追踪后端日志

**参数解析**：
- `-f` (follow) — 持续输出新日志，类似 `tail -f`

**场景**：重新部署后观察启动过程，确认迁移与服务启动正常。按 `Ctrl+C` 退出。

---

## 二、Dockerfile 指令说明

### Dockerfile.backend

采用**多阶段构建**，分为构建阶段和运行阶段：

| 指令 | 说明 |
|------|------|
| `FROM node:20-slim AS backend-builder` | 构建阶段：基于精简版 Node.js 20 |
| `RUN apt-get install -y openssl` | 安装 OpenSSL（Prisma 运行时依赖） |
| `COPY backend/package*.json ./` | 先复制依赖声明文件 |
| `RUN npm ci` | 安装全部依赖（含 devDependencies） |
| `COPY backend/ .` | 复制源代码 |
| `RUN npx prisma generate` | 生成 Prisma Client |
| `RUN npm run build` | 编译 TypeScript |
| `FROM node:20-slim` | 运行阶段：全新精简镜像 |
| `RUN npm ci --omit=dev` | 只安装生产依赖 |
| `COPY --from=backend-builder` | 从构建阶段复制编译产物 |
| `ENV NODE_ENV=production` | 设置生产环境 |
| `EXPOSE 3000` | 声明端口 3000 |
| `CMD ["sh", "scripts/start.sh"]` | 启动脚本（含 prisma migrate deploy） |

### Dockerfile.frontend

同样采用**多阶段构建**：

| 指令 | 说明 |
|------|------|
| `FROM node:20-alpine AS frontend-builder` | 构建阶段：基于 Alpine Node.js 20 |
| `RUN npm ci` | 安装依赖 |
| `RUN npm run build` | Vite 构建，输出到 dist/ |
| `FROM nginx:alpine` | 运行阶段：Nginx Alpine 镜像 |
| `COPY --from=frontend-builder /app/dist` | 将构建产物复制到 Nginx 静态目录 |
| `COPY nginx.conf` | 复制 Nginx 配置（含 API 反向代理） |
| `EXPOSE 80` | 声明端口 80 |
| `CMD ["nginx", "-g", "daemon off;"]` | 前台运行 Nginx |

---

## 三、docker-compose.yml 服务架构

```
┌─────────────────────────────────────────────┐
│              docker-compose.yml              │
├──────────┬──────────────┬────────────────────┤
│    db    │   backend    │     frontend       │
│ Postgres │  Node.js     │    Nginx           │
│ :5432    │  :3000       │     :80            │
│          │              │                    │
│  volumes │  depends_on  │   depends_on       │
│  pgdata  │    db        │   backend          │
│          │  (healthy)   │                    │
└──────────┴──────────────┴────────────────────┘
```

**启动顺序**：`db`（等待健康检查通过）→ `backend` → `frontend`

**数据持久化**：PostgreSQL 数据存储在 Docker Volume `pgdata` 中，容器重建后数据不丢失。

---

## 四、常用运维命令速查

| 操作 | 命令 |
|------|------|
| 启动所有服务 | `docker compose up -d --build` |
| 仅启动数据库 | `docker compose up db -d` |
| 重建前端 | `docker compose up -d --build frontend` |
| 重建后端 | `docker compose up -d --build backend` |
| 查看容器状态 | `docker compose ps` |
| 查看后端日志 | `docker compose logs backend` |
| 实时追踪日志 | `docker compose logs -f backend` |
| 停止所有服务 | `docker compose down` |
| 停止并清除数据 | `docker compose down -v` |
| 进入后端容器 | `docker compose exec backend sh` |
| 进入数据库容器 | `docker compose exec db psql -U todo -d todoapp` |
| 查看镜像大小 | `docker compose images` |
