# 后端任务清单
> 基于 API_CONTRACT v1.0，每任务对应一个接口
> 契约文件：docs/API_CONTRACT.md
> 数据库 Schema：docs/DB_SCHEMA.md
> 状态：全部完成

---

### [x] TASK-B01：项目基础架构搭建

- 对应契约：TECH_SPEC.md 项目目录结构
- 验收标准：
  - 创建 backend/ 目录结构（routes / controllers / services / middleware / utils）
  - package.json 存在，依赖正确（koa, prisma, jsonwebtoken, axios）
  - .env.example 存在，包含所有环境变量模板
  - app.js 入口文件存在，Koa 应用初始化完成
  - 错误处理中间件实现
  - 健康检查端点 GET /api/v1/health 返回 { data: { status: "ok", timestamp }, message: "success" }

---

### [x] TASK-B02：数据库 Schema 与迁移

- 对应契约：DB_SCHEMA.md
- 验收标准：
  - prisma/schema.prisma 存在，字段与 DB_SCHEMA.md 完全一致
  - users 表包含：id, openid, unionid, nick_name, avatar_url, created_at, updated_at, deleted_at
  - checkins 表包含：id, user_id, checkin_date, created_at
  - 唯一索引 uk_users_openid 和 uk_checkins_user_date 存在
  - 外键关系 user_id -> users.id 正确设置

---

### [x] TASK-B03：JWT 工具与鉴权中间件

- 对应契约：TECH_SPEC.md JWT Token 设计
- 验收标准：
  - utils/jwt.js 存在，实现 generateToken / verifyToken
  - Token payload 包含 userId, iat, exp
  - Token 有效期 7 天
  - middleware/auth.js 存在，实现 JWT 验证中间件
  - 401 响应格式：{ error: "unauthorized", message: "请先登录" }
  - 非健康检查接口必须经过鉴权中间件

---

### [x] TASK-B04：微信登录服务

- 对应契约：API_CONTRACT.md POST /api/v1/auth/wx-login
- 验收标准：
  - services/wxService.js 实现 code2Session 函数
  - 调用微信 jscode2session 接口
  - 处理微信接口错误（errcode 非 0）
  - 不缓存 code，不存储 session_key
  - openid 不返回给前端

---

### [x] TASK-B05：实现 POST /api/v1/auth/wx-login

- 对应契约：API_CONTRACT.md #认证模块
- 验收标准：
  - 路径：POST /api/v1/auth/wx-login
  - 请求体：{ code: string, userInfo?: { nickName, avatarUrl } }
  - 响应体：{ data: { token, isNewUser, userInfo: { id, nickName, avatarUrl } }, message: "success" }
  - 错误码覆盖：400 missing_code, 400 invalid_code, 502 wx_api_error
  - 新用户自动创建，已有用户更新信息
  - openid 不出现在响应中

---

### [x] TASK-B06：实现 POST /api/v1/checkin

- 对应契约：API_CONTRACT.md #打卡模块
- 验收标准：
  - 路径：POST /api/v1/checkin
  - 鉴权：需要（Bearer token）
  - 响应体：{ data: { checkinId, checkinDate, consecutiveDays, maxConsecutiveDays }, message: "success" }
  - 错误码覆盖：401 unauthorized, 409 already_checked_in
  - user_id + checkin_date 唯一约束防止重复打卡
  - 连续打卡天数实时计算（不存储）

---

### [x] TASK-B07：实现 GET /api/v1/checkin/status

- 对应契约：API_CONTRACT.md #打卡模块
- 验收标准：
  - 路径：GET /api/v1/checkin/status
  - 鉴权：需要
  - 响应体：{ data: { isCheckedIn, checkinDate, consecutiveDays, maxConsecutiveDays }, message: "success" }
  - checkinDate 格式 YYYY-MM-DD
  - 错误码覆盖：401 unauthorized

---

### [x] TASK-B08：实现 GET /api/v1/checkin/history

- 对应契约：API_CONTRACT.md #打卡模块
- 验收标准：
  - 路径：GET /api/v1/checkin/history
  - 鉴权：需要
  - 查询参数：year(可选), month(可选), page(默认1), pageSize(默认31)
  - 响应体包含：{ data: { list: [{ id, checkinDate, createdAt }], total, year, month }, message: "success" }
  - checkinDate 格式 YYYY-MM-DD，createdAt 格式 ISO 8601
  - 错误码覆盖：401 unauthorized

---

### [x] TASK-B09：实现 GET /api/v1/users/me

- 对应契约：API_CONTRACT.md #用户模块
- 验收标准：
  - 路径：GET /api/v1/users/me
  - 鉴权：需要
  - 响应体：{ data: { id, nickName, avatarUrl, totalCheckinDays, consecutiveDays, maxConsecutiveDays, createdAt }, message: "success" }
  - totalCheckinDays 从 checkins 表 COUNT 查询
  - consecutiveDays 实时计算
  - 错误码覆盖：401 unauthorized, 404 not_found

---

### [x] TASK-B10：Docker 配置与启动脚本

- 对应契约：TECH_SPEC.md 部署方式
- 验收标准：
  - backend/Dockerfile 存在
  - backend/docker-compose.yml 存在，包含 MySQL + Node.js 服务
  - 启动脚本能正常启动服务
  - 环境变量通过 .env 文件注入
