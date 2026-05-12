# 数据库 Schema
> 数据库: MySQL 8.0 | 字符集: utf8mb4 | 排序规则: utf8mb4_unicode_ci
> ORM: Prisma

## 命名规范

| 规范项 | 规则 | 示例 |
|--------|------|------|
| 表名 | 复数蛇形 | `users`、`checkins` |
| 字段名 | 蛇形 | `created_at`、`user_id` |
| 主键 | 统一命名 `id` | `BIGINT UNSIGNED AUTO_INCREMENT` |
| 外键 | `{关联表单数}_id` | `user_id` |
| 时间字段 | `DATETIME`，存 UTC | `CURRENT_TIMESTAMP` |
| 索引 | `idx_{表名}_{字段}` | `idx_users_openid` |
| 唯一索引 | `uk_{表名}_{字段}` | `uk_users_openid` |

---

## 表：users

**用途**：用户信息（微信小程序用户）

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT | — | 主键 |
| openid | VARCHAR(64) | NOT NULL, UNIQUE | — | 微信 openid（用户唯一标识） |
| unionid | VARCHAR(64) | NULL, INDEX | NULL | 微信 unionid（跨小程序标识，MVP 不使用） |
| nick_name | VARCHAR(100) | NOT NULL | '' | 用户昵称 |
| avatar_url | VARCHAR(500) | NOT NULL | '' | 用户头像 URL |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted_at | DATETIME | NULL | NULL | 软删除时间 |

**索引**：

```sql
PRIMARY KEY (id)
UNIQUE INDEX uk_users_openid (openid)
INDEX idx_users_unionid (unionid)
```

**说明**：
- openid 是微信用户唯一标识，用于登录鉴权
- unionid 用于跨小程序用户识别，MVP 阶段可为 NULL
- 不存储 session_key，每次登录重新获取
- 不存储手机号（MVP 阶段不涉及手机号登录）

---

## 表：checkins

**用途**：打卡记录

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | BIGINT UNSIGNED | PK, AUTO_INCREMENT | — | 主键 |
| user_id | BIGINT UNSIGNED | NOT NULL, FK | — | 关联用户 ID |
| checkin_date | DATE | NOT NULL | — | 打卡日期 |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 打卡时间 |

**索引**：

```sql
PRIMARY KEY (id)
UNIQUE INDEX uk_checkins_user_date (user_id, checkin_date)
INDEX idx_checkins_user_id (user_id)
INDEX idx_checkins_date (checkin_date)
```

**外键**：

```sql
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
```

**说明**：
- user_id + checkin_date 联合唯一索引，确保每天只能打卡一次
- checkin_date 使用 DATE 类型，只存储日期不存储时间
- 不存储连续天数，通过查询计算得出（保证数据一致性）

---

## ER 关系图

```
┌─────────────┐       ┌─────────────┐
│   users     │       │   checkins  │
├─────────────┤       ├─────────────┤
│ id (PK)     │──┐    │ id (PK)     │
│ openid (UQ) │  │    │ user_id (FK)│
│ unionid     │  │    │ checkin_date│
│ nick_name   │  └───►│ created_at  │
│ avatar_url  │       └─────────────┘
│ created_at  │
│ updated_at  │
│ deleted_at  │
└─────────────┘

关系：users 1 ──── N checkins
（一个用户有多条打卡记录）
```

---

## Prisma Schema

```prisma
// prisma/schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "mysql"
  url      = env("DATABASE_URL")
}

model User {
  id         BigInt     @id @default(autoincrement()) @db.UnsignedBigInt
  openid     String     @unique @db.VarChar(64)
  unionid    String?    @db.VarChar(64)
  nickName   String     @map("nick_name") @db.VarChar(100)
  avatarUrl  String     @map("avatar_url") @db.VarChar(500)
  createdAt  DateTime   @default(now()) @map("created_at")
  updatedAt  DateTime   @updatedAt @map("updated_at")
  deletedAt  DateTime?  @map("deleted_at")

  checkins   Checkin[]

  @@index([unionid])
  @@map("users")
}

model Checkin {
  id          BigInt   @id @default(autoincrement()) @db.UnsignedBigInt
  userId      BigInt   @map("user_id") @db.UnsignedBigInt
  checkinDate DateTime @map("checkin_date") @db.Date
  createdAt   DateTime @default(now()) @map("created_at")

  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([userId, checkinDate])
  @@index([userId])
  @@index([checkinDate])
  @@map("checkins")
}
```

---

## 连续打卡天数计算逻辑

连续打卡天数不存储在数据库中，通过查询实时计算：

```sql
-- 计算用户连续打卡天数
WITH RECURSIVE consecutive AS (
  SELECT checkin_date
  FROM checkins
  WHERE user_id = ? AND checkin_date = CURDATE()
  
  UNION ALL
  
  SELECT c.checkin_date
  FROM checkins c
  INNER JOIN consecutive con ON c.checkin_date = DATE_SUB(con.checkin_date, INTERVAL 1 DAY)
  WHERE c.user_id = ?
)
SELECT COUNT(*) as consecutive_days FROM consecutive;
```

**Prisma 实现方式**：

```javascript
async function getConsecutiveDays(userId) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  let consecutiveDays = 0
  let checkDate = new Date(today)
  
  while (true) {
    const checkin = await prisma.checkin.findUnique({
      where: {
        userId_checkinDate: {
          userId: BigInt(userId),
          checkinDate: checkDate
        }
      }
    })
    
    if (!checkin) break
    
    consecutiveDays++
    checkDate.setDate(checkDate.getDate() - 1)
  }
  
  return consecutiveDays
}
```

---

## 完成标志

docs/DB_SCHEMA.md 已创建，包含：
- 2 张表的完整定义（users、checkins）
- 每个字段的类型、约束、默认值、说明
- 索引定义（主键、唯一索引、普通索引）
- 外键关系
- Prisma Schema 代码
- 连续打卡天数计算逻辑
