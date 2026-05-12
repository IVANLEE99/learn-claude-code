# 数据库 Schema 文档 (DB_SCHEMA) -- Todo App

> 版本：1.0
> 日期：2026-05-11
> 作者：software-architect
> 基于：PRD v1.0 / API_CONTRACT v1.0

---

## 1. 数据库概述

- 数据库：PostgreSQL 15+
- ORM：Prisma 5.x
- 字符集：UTF-8
- 时区：所有时间戳存储为 UTC，ISO 8601 格式返回
- 主键策略：UUID v4，由应用层生成（Prisma `@default(uuid())`）
- 软删除：不采用，直接物理删除（MVP 阶段简化）

---

## 2. 表结构定义

### 2.1 users -- 用户表

| 字段名 | 类型 | 约束 | 默认值 | 索引 | 说明 |
|--------|------|------|--------|------|------|
| id | UUID | PK | uuid() | 主键索引 | 用户唯一标识 |
| email | VARCHAR(255) | NOT NULL, UNIQUE | - | 唯一索引 | 邮箱地址，用于登录 |
| password_hash | VARCHAR(255) | NOT NULL | - | - | bcrypt 加盐哈希后的密码 |
| nickname | VARCHAR(100) | NOT NULL | - | - | 用户昵称 |
| created_at | TIMESTAMP(3) | NOT NULL | now() | - | 创建时间 |
| updated_at | TIMESTAMP(3) | NOT NULL | now() | - | 更新时间 |

**索引**

| 索引名 | 类型 | 字段 | 原因 |
|--------|------|------|------|
| users_email_key | UNIQUE | email | 登录查询 + 邮箱唯一性保证 |

**关联**

| 关联 | 类型 | 说明 |
|------|------|------|
| users.id -> todo_lists.user_id | 一对多 | 一个用户拥有多个列表 |
| users.id -> todos.user_id | 一对多 | 一个用户拥有多个待办 |

---

### 2.2 todo_lists -- 待办列表表

| 字段名 | 类型 | 约束 | 默认值 | 索引 | 说明 |
|--------|------|------|--------|------|------|
| id | UUID | PK | uuid() | 主键索引 | 列表唯一标识 |
| user_id | UUID | NOT NULL, FK | - | 普通索引 | 所属用户 |
| name | VARCHAR(100) | NOT NULL | - | - | 列表名称 |
| color | VARCHAR(7) | NOT NULL | '#4A90D9' | - | 颜色标识，HEX 格式 #RRGGBB |
| position | INTEGER | NOT NULL | - | - | 排序位置，数值越小越靠前 |
| created_at | TIMESTAMP(3) | NOT NULL | now() | - | 创建时间 |
| updated_at | TIMESTAMP(3) | NOT NULL | now() | - | 更新时间 |

**外键**

| 外键名 | 字段 | 引用 | 删除策略 | 说明 |
|--------|------|------|---------|------|
| fk_todo_lists_user_id | user_id | users.id | CASCADE | 用户删除时，其所有列表一并删除 |

**索引**

| 索引名 | 类型 | 字段 | 原因 |
|--------|------|------|------|
| idx_todo_lists_user_id | 普通索引 | user_id | 按用户查询列表 |
| idx_todo_lists_user_position | 复合索引（UNIQUE） | (user_id, position) | 同一用户内列表排序位置唯一 |

---

### 2.3 todos -- 待办事项表

| 字段名 | 类型 | 约束 | 默认值 | 索引 | 说明 |
|--------|------|------|--------|------|------|
| id | UUID | PK | uuid() | 主键索引 | 待办唯一标识 |
| user_id | UUID | NOT NULL, FK | - | 普通索引 | 所属用户（冗余，便于跨列表查询） |
| list_id | UUID | NOT NULL, FK | - | 普通索引 | 所属列表 |
| title | VARCHAR(255) | NOT NULL | - | - | 待办标题 |
| description | TEXT | NULL | - | - | 待办描述（可选） |
| priority | VARCHAR(10) | NOT NULL | 'medium' | - | 优先级：high / medium / low |
| completed | BOOLEAN | NOT NULL | false | 普通索引 | 是否完成 |
| position | INTEGER | NOT NULL | - | - | 列表内排序位置 |
| created_at | TIMESTAMP(3) | NOT NULL | now() | - | 创建时间 |
| updated_at | TIMESTAMP(3) | NOT NULL | now() | - | 更新时间 |

**外键**

| 外键名 | 字段 | 引用 | 删除策略 | 说明 |
|--------|------|------|---------|------|
| fk_todos_user_id | user_id | users.id | CASCADE | 用户删除时，其所有待办一并删除 |
| fk_todos_list_id | list_id | todo_lists.id | CASCADE | 列表删除时，其下所有待办一并删除 |

**索引**

| 索引名 | 类型 | 字段 | 原因 |
|--------|------|------|------|
| idx_todos_user_id | 普通索引 | user_id | 按用户查询待办 |
| idx_todos_list_id | 普通索引 | list_id | 按列表查询待办 |
| idx_todos_completed | 普通索引 | completed | 筛选已完成/未完成 |
| idx_todos_list_position | 复合索引（UNIQUE） | (list_id, position) | 同一列表内待办排序位置唯一 |
| idx_todos_title_keyword | GIN (pg_trgm) | title | 关键词模糊搜索 |

---

## 3. Prisma Schema 定义

以下为 Prisma schema 文件的完整定义，字段与上述表格严格一致：

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id           String      @id @default(uuid())
  email        String      @unique @db.VarChar(255)
  passwordHash String      @map("password_hash") @db.VarChar(255)
  nickname     String      @db.VarChar(100)
  createdAt    DateTime    @default(now()) @map("created_at") @db.Timestamp(3)
  updatedAt    DateTime    @updatedAt @map("updated_at") @db.Timestamp(3)

  todoLists TodoList[]
  todos     Todo[]

  @@map("users")
}

model TodoList {
  id        String   @id @default(uuid())
  userId    String   @map("user_id") @db.VarChar(36)
  name      String   @db.VarChar(100)
  color     String   @default("#4A90D9") @db.VarChar(7)
  position  Int
  createdAt DateTime @default(now()) @map("created_at") @db.Timestamp(3)
  updatedAt DateTime @updatedAt @map("updated_at") @db.Timestamp(3)

  user  User   @relation(fields: [userId], references: [id], onDelete: Cascade)
  todos Todo[]

  @@unique([userId, position], name: "idx_todo_lists_user_position")
  @@index([userId], name: "idx_todo_lists_user_id")
  @@map("todo_lists")
}

model Todo {
  id          String   @id @default(uuid())
  userId      String   @map("user_id") @db.VarChar(36)
  listId      String   @map("list_id") @db.VarChar(36)
  title       String   @db.VarChar(255)
  description String?  @db.Text
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

---

## 4. 数据完整性约束说明

| 约束 | 说明 |
|------|------|
| users.email UNIQUE | 防止同一邮箱重复注册 |
| (todo_lists.user_id, position) UNIQUE | 同一用户内列表排序位置不重复 |
| (todos.list_id, position) UNIQUE | 同一列表内待办排序位置不重复 |
| todos.user_id 冗余 | 虽然 list_id -> todo_lists.user_id 可推导，但为跨列表查询性能直接存储 |
| FK CASCADE | 删除用户级联删除列表和待办；删除列表级联删除其下待办 |
| priority CHECK | 应用层校验，只允许 high / medium / low 三个值 |
| color CHECK | 应用层校验，HEX 格式 #RRGGBB |

---

## 5. 初始数据

无预置数据。用户注册后系统不自动创建列表，前端引导用户创建第一个列表。

---

## 6. 迁移策略

- 使用 Prisma Migrate 管理迁移
- 首次部署执行 `npx prisma migrate deploy`
- 后续表结构变更：创建新迁移文件，不可修改已有迁移
- 迁移文件命名规范：`YYYYMMDDHHMMSS_描述`（Prisma 自动生成）
