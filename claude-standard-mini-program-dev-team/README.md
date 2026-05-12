# Claude Standard Mini Program Dev Team

> 让 Claude Code 拥有一支 12 人微信小程序 AI 开发团队 + 1 位总指挥，从需求到提审上线全流程自动跑通。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-blue.svg)](https://claude.com/claude-code)

---

## 这是什么

一套面向 [Claude Code](https://claude.com/claude-code) 的 **微信小程序 agent 团队配置**，基于 [claude-standard-dev-team](https://github.com/xuanbingbingo/claude-standard-dev-team) 改编，专为微信小程序开发优化：

- **不再是 1 个 AI 一锅煮**：12 个 agent 各司其职
- **契约驱动**：先定 PRD/API/Schema，再让所有人照契约写
- **微信生态内置**：微信登录、内容安全、隐私合规、包大小管理
- **任务级 QA 闭环**：实现一个接口，立刻独立验证

---

## 与原版标准团队的差异

| 维度 | 标准团队（Web） | 小程序团队 |
|------|---------------|-----------|
| 前端框架 | Vue/React + Vite | 微信原生 / Taro / uni-app |
| 前端单位 | vw/rem | rpx |
| 部署方式 | Docker + Nginx 网关 | 微信开发者工具上传 + 审核发布 |
| 部署角色 | devops-automator | mini-program-publisher |
| 登录方式 | 用户名密码 / OAuth | 微信登录（code2Session） |
| 跨域问题 | CORS + 子路径 | 无 CORS 问题 |
| 安全重点 | XSS/CSRF + 子路径404 | openid 泄露 + 内容安全 + 隐私合规 |
| 包大小 | 无限制 | 主包 2MB / 总包 20MB |
| 零容忍规则 | API 路径硬编码 | API 地址硬编码 + 包大小超限 + openid 泄露 |

---

## 团队架构

```
                    ┌─────────────────────────┐
                    │     orchestrator        │
                    │   总指挥，不写代码        │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼─────┐         ┌────────▼────────┐      ┌────────▼─────┐
│  规划层 2   │         │   实现层 5      │      │  质量层 4     │
├──────────── │         ├─────────────────│      ├──────────────│
│ pm          │         │ db-optimizer    │      │ ev-collector │
│ sw-architect│         │ backend-arch    │      │ sec-engineer │
│             │         │ ui-designer     │      │ code-reviewer│
│             │         │ mp-developer     │      │ reality-chk  │
│             │         │ mp-publisher     │      └──────────────┘
└─────────────┘         └─────────────────┘
                                                  ┌──────────────┐
                                                  │  文档层 1    │
                                                  │ tech-writer  │
                                                  └──────────────┘
```

| 层级 | Agent | 职责 |
|---|---|---|
| **总指挥** | orchestrator | 不写代码，只调度其他 agent |
| **规划** | product-manager | PRD + 微信生态需求（登录/支付/UGC） |
| **规划** | software-architect | 技术选型 + 微信登录方案 + 契约生成 |
| **实现** | ui-designer | 小程序设计规范（rpx 体系） |
| **实现** | database-optimizer | 数据库迁移（含 openid 字段） |
| **实现** | backend-architect | API 实现 + 微信登录接口 + 内容安全 |
| **实现** | mini-program-developer | WXML/WXSS/JS 页面开发 + 微信 API 对接 |
| **实现** | mini-program-publisher | 包大小检查 + 配置合规 + 发布准备 |
| **质量** | testing-evidence-collector | 任务级 QA（含包大小/真机验证） |
| **质量** | security-engineer | 安全扫描 + 微信合规检查 |
| **质量** | code-reviewer | 代码 review + 小程序性能审查 |
| **质量** | reality-checker | 最终验收 + 微信合规验收 |
| **文档** | technical-writer | README + API 文档 + 小程序发布说明 |

---

## 工作流程（11 个阶段）

```
Phase 0   orchestrator 创建项目目录
Phase 1   → product-manager      → PRD.md（含微信生态需求）
   ⏸ 人工检查点 #1：确认功能范围
Phase 2   → software-architect   → API_CONTRACT / DB_SCHEMA / TECH_SPEC（含微信登录方案）
   ⏸ 人工检查点 #2：确认接口契约 + 微信登录方案
Phase 2.5 → ui-designer          → DESIGN_SYSTEM.md / variables.wxss（rpx 体系）
Phase 3   orchestrator 自己拆任务清单
Phase 4   → database-optimizer   → migrations/（含 openid 字段）
Phase 5   → backend-architect    │ Dev-QA Loop
          → ev-collector         │ 逐任务循环
Phase 6   → mp-developer         │ Dev-QA Loop
          → ev-collector         │ 逐任务循环
Phase 7   → security-engineer    → SECURITY_REPORT.md（含微信合规）
Phase 8   → code-reviewer        → REVIEW_REPORT.md（含性能审查）
Phase 9   → mp-publisher         → 包大小检查 + 配置合规 + 发布准备
Phase 10  → reality-checker      → READY 或 NEEDS WORK（含微信合规验收）
Phase 11  → technical-writer     → README + API_DOC + 发布说明
完工 ✅
```

---

## 5 分钟上手

### 1. 装入 Claude Code

```bash
git clone https://github.com/your-username/claude-standard-mini-program-dev-team.git
cp claude-standard-mini-program-dev-team/agents/*.md ~/.claude/agents/
```

### 2. 在 Claude Code 里说一句话启动

```
使用小程序团队帮我开发一个打卡签到小程序
```

### 3. 看着它跑

整个过程**只在 Phase 1/2 后两次暂停**让你确认，其他全自动。

---

## 适合谁用

✅ 你正在用 Claude Code 开发**微信小程序**（需后端 + 数据库）  
✅ 你需要**微信登录、内容安全、隐私合规**的完整方案  
✅ 你被小程序**包大小超限、审核被拒**坑过  
✅ 你需要**真实可提审上线**的产物  

❌ **不适合**：纯前端小程序原型 / 无后端小程序 / H5 项目

---

## 设计哲学

| 设计原则 | 体现在哪 |
|---|---|
| **契约第一** | Phase 2 是最关键节点，包含微信登录方案 |
| **微信生态优先** | 使用微信原生能力，不重复造轮子 |
| **包大小零容忍** | 主包超 2MB 必须优化，不允许带超限提交 |
| **openid 零泄露** | openid/session_key 不返回前端（安全红线） |
| **内容安全必审** | UGC 必须接入 msgSecCheck/imgSecCheck |
| **评审者 ≠ 实现者** | QA agent 独立验证 |
| **打回有上限** | 重试 3 次不行就暂停问用户 |

---

## License

[MIT](LICENSE) © 2026

---

## 相关链接

- [Claude Code 官方](https://claude.com/claude-code)
- [原版标准团队](https://github.com/xuanbingbingo/claude-standard-dev-team)
- [微信小程序官方文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
