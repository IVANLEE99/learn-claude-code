# 代码评审报告 (REVIEW_REPORT) -- Todo App

> 版本：1.0
> 日期：2026-05-11
> 作者：code-reviewer

---

## 1. 评审范围

- 后端：backend/src/（TypeScript + Express）
- 前端：frontend/src/（Vue 3 + TypeScript）

---

## 2. 评审结果总览

| 级别 | 数量 | 说明 |
|------|------|------|
| MUST FIX | 1 | 已修复 |
| SHOULD FIX | 0 | - |
| SUGGESTION | 3 | 建议优化 |

---

## 3. MUST FIX（已修复）

### 3.1 PrismaClient 多实例化

- **问题**：4 个 service 文件各自实例化了 `new PrismaClient()`，可能导致连接池耗尽
- **文件**：auth.service.ts、user.service.ts、list.service.ts、todo.service.ts
- **修复**：创建 `config/prisma.ts` 单例，所有 service 导入共享实例
- **状态**：已修复

---

## 4. SUGGESTION（建议优化，非阻塞）

### 4.1 Prisma where 条件使用 any 类型

- **文件**：todo.service.ts 第 28 行、第 147 行
- **说明**：`const where: any` 和 `const updateData: any` 使用了 any 类型
- **建议**：后续使用 Prisma 生成的类型替代（如 `Prisma.TodoWhereInput`），MVP 阶段可接受

### 4.2 auth 中间件 catch 中的 err 使用 any 类型

- **文件**：middleware/auth.ts 第 30 行
- **说明**：`catch (err: any)` 是 TypeScript 中 catch 的常见模式
- **建议**：后续可使用 `unknown` 类型并添加类型守卫，MVP 阶段可接受

### 4.3 后端启动日志

- **文件**：src/index.ts 第 35 行
- **说明**：`console.log` 用于启动提示，属于正常用途
- **建议**：生产环境可替换为正式日志库（如 winston）

---

## 5. 代码规范检查

| 检查项 | 结果 |
|--------|------|
| 缩进：2 空格 | 通过 |
| 文件编码：UTF-8 | 通过 |
| 命名：camelCase / PascalCase | 通过 |
| TypeScript strict 模式 | 通过 |
| 错误处理覆盖 | 通过（所有路由均含 try/catch） |
| 前端无 console.log | 通过 |
| CSS 变量使用 | 通过（无硬编码颜色/字号/间距） |
| API 调用规范 | 通过（均通过 api/client.ts 实例） |

---

## 6. 结论

MUST FIX 项已修复，代码质量达标，可以继续进入下一阶段。
