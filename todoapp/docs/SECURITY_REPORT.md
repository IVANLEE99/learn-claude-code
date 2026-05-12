# 安全审查报告 (SECURITY_REPORT) -- Todo App

> 版本：1.0
> 日期：2026-05-11
> 作者：security-engineer

---

## 1. 审查范围

- 后端源码：backend/src/（TypeScript）
- 前端源码：frontend/src/（Vue 3 + TypeScript）
- 配置文件：vite.config.ts、.env、.env.production

---

## 2. 审查结果总览

| 类别 | 高危 | 中危 | 低危 |
|------|------|------|------|
| SQL 注入 | 0 | 0 | 0 |
| XSS | 0 | 0 | 0 |
| CSRF | 0 | 0 | 0 |
| 鉴权缺失 | 0 | 0 | 0 |
| 硬编码密钥 | 0 | 0 | 1 |
| 文件上传 | 0 | 0 | 0 |

---

## 3. 详细审查

### 3.1 SQL 注入

- **结论**：无风险
- ORM 使用 Prisma，所有数据库操作通过 Prisma Client 的参数化查询执行，未发现原始 SQL 语句

### 3.2 XSS（跨站脚本）

- **结论**：无风险
- 前端未使用 v-html、innerHTML、document.write
- 所有动态内容通过 Vue 模板插值渲染，Vue 自动转义

### 3.3 CSRF（跨站请求伪造）

- **结论**：无风险
- 使用 JWT Bearer Token 鉴权方案，Token 存储在 localStorage
- CSRF 攻击依赖浏览器自动发送 Cookie，JWT 方案中 Token 需手动附加到 Authorization 头

### 3.4 接口鉴权

- **结论**：无风险
- 注册和登录接口无需鉴权，符合设计
- 所有其他接口均使用了 authMiddleware

### 3.5 硬编码密钥/密码

- **结论**：低危
- JWT_SECRET 和 DATABASE_URL 从环境变量读取，未硬编码
- 默认值 `dev-secret-change-me` 仅在 .env 中出现
- 建议：生产环境必须生成随机 JWT_SECRET

### 3.6 文件上传

- **结论**：不涉及

### 3.7 输入校验

- **结论**：覆盖完整
- 所有路由文件均使用 Zod schema 校验请求参数

### 3.8 密码存储

- **结论**：安全
- 使用 bcryptjs 加盐哈希，saltRounds = 10

---

## 4. 安全建议（非 Blocker）

1. 生产环境部署时，JWT_SECRET 必须使用随机 64 字符字符串
2. CORS_ORIGIN 必须配置为实际前端域名，不允许使用 `*`
3. 后续版本考虑添加请求速率限制，防止暴力破解
