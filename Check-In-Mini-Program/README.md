# Check-In-Mini-Program

每日打卡签到微信小程序，帮助用户养成每日签到习惯，记录打卡历史，显示连续打卡天数。

## 技术栈

| 层级 | 技术 |
|------|------|
| 小程序前端 | 原生开发（WXML/WXSS/JS） |
| 后端 | Node.js + Koa 2 |
| 数据库 | MySQL 8.0 |
| ORM | Prisma |
| 认证 | 微信登录 + JWT |
| 部署 | Docker + docker-compose |

## 本地开发

### 前置条件

- 微信开发者工具（[下载](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)）
- Node.js 18+
- MySQL 8.0（或使用 Docker）

### 启动后端

```bash
cd backend
npm install
cp .env.example .env  # 编辑 .env 填写数据库和微信配置
npm run migrate        # 运行数据库迁移
npm run dev            # 启动开发服务器
```

### 启动小程序

1. 打开微信开发者工具
2. 导入项目，选择 `miniprogram/` 目录
3. 填入 AppID（测试可使用测试号）
4. 编译运行

### 使用 Docker 启动后端

```bash
cd backend
cp .env.example .env  # 编辑配置
docker-compose up -d
```

## 环境变量

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `WX_APPID` | 小程序 AppID | `wx1234567890abcdef` |
| `WX_SECRET` | 小程序 AppSecret | 从微信公众平台获取 |
| `JWT_SECRET` | JWT 签名密钥（最少 32 字符） | `your-secret-key-min-32-chars` |
| `JWT_EXPIRES_IN` | Token 有效期 | `7d` |
| `DATABASE_URL` | 数据库连接串 | `mysql://user:pass@localhost:3306/checkin` |
| `PORT` | 服务端口 | `3000` |

## 项目结构

```
Check-In-Mini-Program/
├── miniprogram/              # 小程序前端
│   ├── app.js                # 入口文件
│   ├── app.json              # 全局配置
│   ├── app.wxss              # 全局样式
│   ├── project.config.json   # 项目配置
│   ├── sitemap.json          # 站点地图
│   ├── config/
│   │   └── env.js            # 环境配置（API 地址）
│   ├── utils/
│   │   ├── request.js        # wx.request 统一封装
│   │   └── auth.js           # 登录态管理
│   ├── styles/
│   │   └── variables.wxss    # 设计规范变量
│   ├── components/
│   │   ├── check-button/     # 打卡按钮组件
│   │   └── calendar/         # 日历组件
│   ├── pages/
│   │   ├── index/            # 首页（打卡）
│   │   ├── history/          # 打卡记录
│   │   └── profile/          # 个人中心
│   └── assets/               # 图片资源
├── backend/                  # 后端 API
│   ├── package.json
│   ├── .env.example          # 环境变量模板
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── prisma/
│   │   └── schema.prisma     # 数据库 Schema
│   ├── scripts/
│   │   ├── migrate.js        # 迁移脚本
│   │   └── start.sh          # 启动脚本
│   └── src/
│       ├── app.js            # Koa 应用入口
│       ├── routes/           # 路由
│       ├── controllers/      # 控制器
│       ├── services/         # 服务层
│       ├── middleware/        # 中间件
│       └── utils/            # 工具函数
├── docs/                     # 项目文档
│   ├── PRD.md                # 产品需求文档
│   ├── TECH_SPEC.md          # 技术规格说明
│   ├── API_CONTRACT.md       # API 接口契约
│   ├── API_DOC.md            # API 接口文档
│   ├── DB_SCHEMA.md          # 数据库 Schema
│   ├── DESIGN_SYSTEM.md      # UI 设计规范
│   ├── BACKEND_STATUS.md     # 后端实现状态
│   ├── SECURITY_REPORT.md    # 安全审计报告
│   ├── REVIEW_REPORT.md      # 代码审查报告
│   └── ACCEPTANCE_REPORT.md  # 最终验收报告
└── project-tasks/            # 任务清单
    ├── backend-tasklist.md   # 后端任务（全部完成）
    └── frontend-tasklist.md  # 前端任务（全部完成）
```

## 发布流程

1. 确认生产环境配置
   - 编辑 `miniprogram/config/env.js`，确认 production 的 API_BASE 正确
   - 编辑 `backend/.env`，填写生产环境配置

2. 部署后端
   ```bash
   cd backend
   docker-compose up -d
   ```

3. 上传小程序
   - 打开微信开发者工具
   - 点击"上传"按钮
   - 填写版本号（如 1.0.0）和更新说明

4. 提交审核
   - 登录微信公众平台
   - 进入"版本管理"
   - 将开发版设为体验版（可选）
   - 提交审核

5. 发布上线
   - 审核通过后点击"发布"
   - 可选择全量发布或灰度发布

## 功能说明

| 功能 | 说明 |
|------|------|
| 微信登录 | 一键登录，无需注册 |
| 每日打卡 | 每天一次签到，记录坚持天数 |
| 连续天数 | 实时计算连续打卡天数，激励坚持 |
| 打卡日历 | 日历视图查看打卡历史 |
| 个人中心 | 查看统计数据，退出登录 |

## 微信相关配置

- AppID: 需要在微信公众平台注册小程序获取
- 类目: 工具 > 信息查询
- 隐私协议: MVP 阶段不涉及用户隐私信息收集

## License

MIT
