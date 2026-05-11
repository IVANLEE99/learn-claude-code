# Prisma 使用指南

## 一、Prisma 是什么

Prisma 是 Node.js/TypeScript 的下一代 ORM（对象关系映射）框架。与传统 ORM（如 Sequelize、TypeORM）不同，Prisma 不用类和装饰器定义模型，而是用 **声明式 Schema 文件**（`schema.prisma`）描述数据结构，然后自动生成类型安全的查询客户端。

### 核心组件

```
┌──────────────────────────────────────────────────────┐
│                    Prisma 工作流                       │
│                                                      │
│  schema.prisma  ──→  prisma generate  ──→  PrismaClient │
│  (定义数据模型)        (生成客户端代码)       (类型安全的查询API) │
│                                                      │
│  schema.prisma  ──→  prisma migrate dev  ──→  数据库表    │
│  (定义数据模型)        (生成并执行迁移SQL)       (真实表结构)  │
└──────────────────────────────────────────────────────┘
```

| 组件 | 作用 |
|------|------|
| `schema.prisma` | 数据模型定义文件（唯一的真相来源） |
| `PrismaClient` | 自动生成的类型安全查询客户端 |
| Prisma CLI | 执行迁移、生成客户端等命令行工具 |
| Migration Engine | 将 Schema 变更转换为 SQL 迁移文件 |

### 与传统 ORM 对比

| 特性 | Prisma | Sequelize / TypeORM |
|------|--------|---------------------|
| 模型定义方式 | 独立 `.prisma` 文件 | JS/TS 类 + 装饰器 |
| 类型安全 | 自动生成，100% 类型覆盖 | 需手动定义接口 |
| 查询语法 | 链式对象 API | 链式 / QueryBuilder |
| 迁移管理 | 内置 `prisma migrate` | 需额外工具 |
| 关系查询 | `include` / `select` 嵌套 | `include` / `eager loading` |

---

## 二、项目中的 Prisma 结构

```
backend/
├── prisma/
│   └── schema.prisma          # 数据模型定义（核心文件）
├── src/
│   └── config/
│       └── prisma.ts          # PrismaClient 单例
├── scripts/
│   └── start.sh               # 生产启动脚本（含 db push + generate）
└── package.json               # 含 prisma 相关依赖和脚本
```

### 依赖说明

```json
{
  "dependencies": {
    "@prisma/client": "^5.0.0"    // 运行时查询客户端
  },
  "devDependencies": {
    "prisma": "^5.0.0"            // CLI 工具（迁移、生成等）
  }
}
```

- `prisma`：开发依赖，提供 CLI 命令（`prisma migrate`、`prisma generate` 等）
- `@prisma/client`：运行时依赖，项目代码中 import 的查询客户端

---

## 三、Schema 文件详解

本项目 `backend/prisma/schema.prisma` 完整解析：

### 3.1 基础配置

```prisma
generator client {
  provider = "prisma-client-js"    // 生成 JavaScript/TypeScript 客户端
}

datasource db {
  provider = "postgresql"           // 数据库类型
  url      = env("DATABASE_URL")   // 从环境变量读取连接字符串
}
```

- `generator`：指定生成什么客户端，`prisma-client-js` 是默认且最常用的
- `datasource`：指定数据库类型和连接方式，`env()` 从环境变量读取，不硬编码密码

### 3.2 User 模型

```prisma
model User {
  id           String    @id @default(uuid())           // 主键，自动生成 UUID
  email        String    @unique @db.VarChar(255)       // 唯一约束，数据库字段类型 VarChar(255)
  passwordHash String    @map("password_hash") @db.VarChar(255)  // 字段名映射：JS 中用 passwordHash，DB 中是 password_hash
  nickname     String    @db.VarChar(100)
  createdAt    DateTime  @default(now()) @map("created_at") @db.Timestamp(3)  // 自动填充创建时间
  updatedAt    DateTime  @updatedAt @map("updated_at") @db.Timestamp(3)       // 自动更新修改时间

  todoLists TodoList[]   // 一对多关系：一个用户有多个列表
  todos     Todo[]       // 一对多关系：一个用户有多个待办

  @@map("users")         // 表名映射：模型叫 User，数据库表叫 users
}
```

**关键概念**：

| 语法 | 含义 |
|------|------|
| `@id` | 主键 |
| `@default(uuid())` | 自动生成 UUID 作为默认值 |
| `@unique` | 唯一约束 |
| `@map("xxx")` | 字段名映射——JS 代码用驼峰，数据库用下划线 |
| `@@map("xxx")` | 表名映射——模型名用单数，表名用复数 |
| `@db.VarChar(255)` | 指定数据库列的精确类型 |
| `@default(now())` | 创建时自动填入当前时间 |
| `@updatedAt` | 记录更新时自动更新为当前时间 |
| `TodoList[]` | 关系字段，不对应数据库列，表示一对多 |

### 3.3 TodoList 模型

```prisma
model TodoList {
  id        String   @id @default(uuid())
  userId    String   @map("user_id") @db.VarChar(36)
  name      String   @db.VarChar(100)
  color     String   @default("#4A90D9") @db.VarChar(7)   // 默认颜色
  position  Int                                                    // 排序位置
  createdAt DateTime @default(now()) @map("created_at") @db.Timestamp(3)
  updatedAt DateTime @updatedAt @map("updated_at") @db.Timestamp(3)

  user  User   @relation(fields: [userId], references: [id], onDelete: Cascade)  // 多对一：属于某个用户
  todos Todo[]                                                              // 一对多：包含多个待办

  @@unique([userId, position], name: "idx_todo_lists_user_position")  // 复合唯一约束
  @@index([userId], name: "idx_todo_lists_user_id")                   // 单列索引
  @@map("todo_lists")
}
```

**关系定义**：

```prisma
user  User   @relation(fields: [userId], references: [id], onDelete: Cascade)
```

- `fields: [userId]` — 本模型的哪个字段作为外键
- `references: [id]` — 引用目标模型的哪个字段
- `onDelete: Cascade` — 用户被删除时，其所有列表也自动删除

**约束与索引**：

| 语法 | 含义 |
|------|------|
| `@@unique([userId, position])` | 复合唯一约束：同一用户的列表 position 不可重复 |
| `@@index([userId])` | 普通索引：加速按 userId 查询 |

### 3.4 Todo 模型

```prisma
model Todo {
  id          String   @id @default(uuid())
  userId      String   @map("user_id") @db.VarChar(36)
  listId      String   @map("list_id") @db.VarChar(36)
  title       String   @db.VarChar(255)
  description String?  @db.Text                    // 可选字段（nullable）
  priority    String   @default("medium") @db.VarChar(10)
  completed   Boolean  @default(false)
  position    Int
  createdAt   DateTime @default(now()) @map("created_at") @db.Timestamp(3)
  updatedAt   DateTime @updatedAt @map("updated_at") @db.Timestamp(3)

  user User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  list TodoList @relation(fields: [listId], references: [id], onDelete: Cascade)

  @@unique([listId, position], name: "idx_todos_list_position")
  @@index([userId], name: "idx_todos_user_id")
  @@index([listId], name: "idx_todos_list_id")
  @@index([completed], name: "idx_todos_completed")
  @@map("todos")
}
```

### 3.5 模型关系图

```
User ──1:N──> TodoList ──1:N──> Todo
  │              │                  │
  │              │                  │
  └──────────────┘──────────────────┘
      (onDelete: Cascade)    (onDelete: Cascade)

删除 User → 自动删除其所有 TodoList → 自动删除其所有 Todo
```

---

## 四、PrismaClient 初始化

本项目采用**单例模式**，避免在多个 service 文件中各创建一个 PrismaClient 导致连接池耗尽：

```typescript
// backend/src/config/prisma.ts
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

export default prisma
```

在 service 中使用：

```typescript
import prisma from '../config/prisma'

const user = await prisma.user.findUnique({ where: { id } })
```

---

## 五、常用查询操作（结合项目实例）

### 5.1 查询单条 — `findUnique`

通过唯一字段（主键或 `@unique` 字段）查询：

```typescript
// auth.service.ts — 按邮箱查找用户
const user = await prisma.user.findUnique({ where: { email } })

// user.service.ts — 按 ID 查找用户，只返回指定字段
const user = await prisma.user.findUnique({
  where: { id: userId },
  select: {
    id: true, email: true, nickname: true, createdAt: true,
  },
})
```

> `findUnique` 要求 `where` 中的字段必须有唯一约束（`@id` 或 `@unique`）。
> 如果要用非唯一字段查询，用 `findFirst`。

### 5.2 查询多条 — `findMany`

```typescript
// list.service.ts — 查询用户的所有列表
const lists = await prisma.todoList.findMany({
  where: { userId },
  orderBy: { position: 'asc' },
  include: {
    _count: {
      select: { todos: { where: { completed: false } } },
    },
  },
})

// todo.service.ts — 带条件查询
const todos = await prisma.todo.findMany({
  where: {
    userId,
    listId: params.listId,                // 等值过滤
    completed: false,                      // 布尔过滤
    title: { contains: '关键词', mode: 'insensitive' },  // 模糊搜索
  },
  include: {
    list: { select: { name: true, color: true } },  // 关联查询
  },
})
```

**常用 where 条件**：

| 操作 | 示例 |
|------|------|
| 等值 | `{ userId }` 或 `{ userId: "xxx" }` |
| 模糊搜索 | `{ title: { contains: "关键词" } }` |
| 不区分大小写 | `{ title: { contains: "key", mode: "insensitive" } }` |
| 大于/小于 | `{ position: { gt: 5 } }` |
| IN 查询 | `{ priority: { in: ["high", "medium"] } }` |
| AND | `{ AND: [{ userId }, { completed: false }] }` |
| OR | `{ OR: [{ title: { contains: "a" } }, { title: { contains: "b" } }] }` |

### 5.3 创建 — `create`

```typescript
// auth.service.ts — 创建用户
const user = await prisma.user.create({
  data: {
    email,
    passwordHash,
    nickname,
  },
})

// todo.service.ts — 创建待办，同时获取关联数据
const todo = await prisma.todo.create({
  data: {
    userId,
    listId: data.listId,
    title: data.title,
    description: data.description || null,
    priority: data.priority || 'medium',
    position: count,
  },
  include: {
    list: { select: { name: true, color: true } },
  },
})
```

### 5.4 更新 — `update`

```typescript
// todo.service.ts — 更新待办
const updated = await prisma.todo.update({
  where: { id: todoId },
  data: { title: '新标题', completed: true },
  include: { list: { select: { name: true, color: true } } },
})

// user.service.ts — 更新并指定返回字段
const user = await prisma.user.update({
  where: { id: userId },
  data: { nickname },
  select: { id: true, email: true, nickname: true },
})
```

### 5.5 删除 — `delete`

```typescript
// todo.service.ts
await prisma.todo.delete({ where: { id: todoId } })

// list.service.ts — 删除列表时，关联的 todos 会被级联删除（schema 中 onDelete: Cascade）
await prisma.todoList.delete({ where: { id: listId } })
```

### 5.6 计数 — `count`

```typescript
// todo.service.ts — 获取待办数量作为新待办的 position
const count = await prisma.todo.count({ where: { listId: data.listId } })
```

### 5.7 关联查询 — `include` vs `select`

```typescript
// include：返回关联模型的全部字段 + 主模型全部字段
await prisma.todo.findMany({
  include: { list: true },
})
// 结果：{ id, title, ..., list: { id, name, color, ... } }

// select：精确控制返回字段（更推荐，避免过度查询）
await prisma.todo.findMany({
  include: {
    list: { select: { name: true, color: true } },
  },
})
// 结果：{ id, title, ..., list: { name: "xxx", color: "#xxx" } }
```

### 5.8 关联计数 — `_count`

```typescript
// list.service.ts — 统计每个列表中未完成的待办数
await prisma.todoList.findMany({
  include: {
    _count: {
      select: { todos: { where: { completed: false } } },
    },
  },
})
// 结果：{ id, name, ..., _count: { todos: 3 } }
```

---

## 六、迁移管理

### 6.1 开发环境：`prisma migrate dev`

```bash
cd backend
npx prisma migrate dev --name init
```

**执行流程**：
1. 读取 `schema.prisma`
2. 对比当前数据库结构，计算差异
3. 在 `prisma/migrations/` 目录下生成 SQL 迁移文件
4. 执行迁移，更新数据库
5. 自动运行 `prisma generate` 更新 PrismaClient

**每次修改 Schema 后都要执行此命令**，Prisma 会生成增量迁移文件。

### 6.2 生产环境：`prisma migrate deploy`

```bash
cd backend
npx prisma migrate deploy
```

**与 `migrate dev` 的区别**：
- 只执行迁移，不会重新生成迁移文件
- 适用于已有迁移文件的场景（CI/CD、生产部署）
- 不会重置数据库

### 6.3 本项目的生产部署策略

```bash
# scripts/start.sh
npx prisma db push --skip-generate    # 将 schema 直接同步到数据库（不生成迁移文件）
npx prisma generate                    # 生成 PrismaClient
exec node dist/index.js               # 启动服务
```

> 项目使用 `db push` 而非 `migrate deploy`。`db push` 直接将 Schema 推送到数据库，跳过迁移文件管理，适合单人开发或简单项目。

### 6.4 `migrate dev` vs `db push` 对比

| 特性 | `migrate dev` | `db push` |
|------|---------------|-----------|
| 生成迁移文件 | 是 | 否 |
| 可回滚 | 是（迁移文件有记录） | 否 |
| 数据安全 | 保护现有数据 | 可能丢数据（需确认） |
| 适用场景 | 团队协作、生产环境 | 快速原型、单人开发 |

---

## 七、完整开发流程

### 首次搭建

```bash
cd backend
npm install                  # 安装依赖（含 prisma 和 @prisma/client）
npx prisma generate          # 生成 PrismaClient（从 schema.prisma）
npx prisma migrate dev       # 创建数据库表 + 生成迁移文件
npm run dev                  # 启动后端开发服务器
```

### 修改数据模型后

```bash
# 1. 编辑 prisma/schema.prisma（添加/修改 model）

# 2. 生成迁移并更新数据库
npx prisma migrate dev --name add_new_field

# 3. PrismaClient 会自动重新生成，TypeScript 类型自动更新

# 4. 在 service 中使用新字段
import prisma from '../config/prisma'
const result = await prisma.user.findMany()
```

### 生产部署

```bash
# Docker 容器启动时自动执行（start.sh）
npx prisma db push --skip-generate
npx prisma generate
node dist/index.js
```

---

## 八、package.json 中的 Prisma 脚本速查

| 脚本 | 命令 | 用途 |
|------|------|------|
| `npm run generate` | `prisma generate` | 生成/更新 PrismaClient |
| `npm run migrate` | `prisma migrate dev` | 开发环境迁移 |
| `npm run migrate:deploy` | `prisma migrate deploy` | 生产环境迁移 |
| `npm run migrate:status` | `prisma migrate status` | 查看迁移状态 |
| `npm run db:push` | `prisma db push` | 直接推送 Schema 到数据库 |
| `npm run seed` | `tsx scripts/seed.ts` | 填充种子数据 |

---

## 九、常见问题

### Q: 修改了 schema.prisma 但查询报错找不到新字段？

需要重新生成客户端：`npx prisma generate`

### Q: `findUnique` 报错说字段不是唯一的？

`findUnique` 只能用于 `@id` 或 `@unique` 字段。非唯一字段用 `findFirst`。

### Q: 关联查询返回的数据太大了？

用 `select` 精确指定需要的字段，替代 `include: true`：

```typescript
prisma.user.findMany({
  include: { todos: { select: { id: true, title: true } } }
})
```

### Q: 如何查看 Prisma 实际执行的 SQL？

开发时开启日志：

```typescript
const prisma = new PrismaClient({
  log: ['query'],   // 打印所有 SQL 查询
})
```

### Q: `@map` 和 `@@map` 有什么区别？

- `@map("xxx")` — 字段级映射：JS 中驼峰命名，数据库中下划线命名
- `@@map("xxx")` — 表级映射：模型名单数，表名复数

这样 JS 代码用 `passwordHash`，数据库列是 `password_hash`，两边都符合各自命名规范。
