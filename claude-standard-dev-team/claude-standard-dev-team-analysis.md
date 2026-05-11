# Claude Standard Dev Team 功能与实现详解

> 基于 [xuanbingbingo/claude-standard-dev-team](https://github.com/xuanbingbingo/claude-standard-dev-team) 仓库的完整分析

---

## 一、项目概述

### 1.1 这是什么

Claude Standard Dev Team 是一套面向 [Claude Code](https://claude.com/claude-code) CLI 工具的 **多 Agent 协作配置系统**。它将"软件开发"拆分为 12 个专业岗位 + 1 位总指挥（orchestrator），按照真实研发团队的协作链路串联起来，实现从需求到上线的全流程自动化。

核心理念：

- **不再 1 个 AI 一锅煮**：每个 Agent 只干一类事，互不交叉
- **契约驱动**：先定 PRD / API / Schema，再让所有人照契约写
- **任务级 QA 闭环**：实现一个接口，立刻独立验证，FAIL 自动打回重做
- **零容忍硬编码**：API 路径硬编码必须打回——来自真实部署翻车教训

### 1.2 技术本质

从技术角度看，这个项目由 **13 个 Markdown 文件**（另有 3 个基建层 Agent）组成，每个 `.md` 文件定义一个 Claude Code Sub-Agent。这些文件被复制到 `~/.claude/agents/` 目录后，Claude Code 在运行时可以自动识别并调度这些 Agent。

每个 Agent 文件包含：

| 字段 | 说明 |
|------|------|
| `name` | Agent 标识名，用于调度时引用 |
| `description` | 描述何时激活该 Agent |
| `tools` | 该 Agent 可使用的工具集（Read / Write / Edit / Bash / Glob / Grep / Task） |
| `model` | 指定使用的模型（opus / sonnet），控制成本与能力的平衡 |

Agent 文件的剩余部分是自然语言 Prompt，定义了该 Agent 的角色、原则、执行步骤、输出模板、禁止行为等。

### 1.3 适用场景

| 适合 | 不适合 |
|------|--------|
| 用 Claude Code 写中型应用（前后端 + DB + 部署） | 纯前端原型 / 单文件脚本 / 一次性小工具 |
| 想要契约驱动 + QA 闭环而非一把梭 | 还在评估 Claude Code 是否值得用 |
| 被 AI 写出"看起来对、跑起来错"的代码坑过 | |
| 需要真实可上线的产物，不只是 demo | |

---

## 二、团队架构

### 2.1 组织结构

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
│             │         │ frontend-dev    │      │ reality-chk  │
│             │         │ devops-automator│      └──────────────┘
└─────────────┘         └─────────────────┘
                                                  ┌──────────────┐
                                                  │  文档层 1    │
                                                  │ tech-writer  │
                                                  └──────────────┘
```

### 2.2 各 Agent 详解

#### 2.2.1 orchestrator（总指挥）

| 属性 | 值 |
|------|-----|
| 模型 | opus（最强推理能力） |
| 工具 | Task, Read, Write, Glob, Bash |
| 职责 | 不写任何业务代码，只调度其他 Agent、传递契约、决策打回 |

**核心设计**：整合两种质量保障机制：
- **契约层**（事前）：强迫所有 Agent 在动手前对齐接口和数据结构
- **Dev-QA Loop**（事中）：每个任务实现后立即由 testing-evidence-collector 验证

**两种工作模式**：
1. **标准模式**：从需求到上线的 11 阶段全流程
2. **Audit 模式**：已有代码审查（code-reviewer → security-engineer → reality-checker）

**工具使用**：orchestrator 使用 `Task` 工具来调度子 Agent——这是 Claude Code 的 Sub-Agent 机制。每次调用 `Task` 会创建一个独立的 LLM 会话，子 Agent 在其中工作，完成后将结果返回给 orchestrator。

---

#### 2.2.2 product-manager（产品经理）

| 属性 | 值 |
|------|-----|
| 模型 | sonnet（成本效率平衡） |
| 工具 | Read, Write |
| 职责 | 把模糊需求拆成结构化 PRD + 用户故事 + 验收标准 |

**核心原则**：
- 范围保守：MVP 宁少勿多
- 数据说话：非功能性需求必须量化
- 假设透明：模糊时做合理假设但必须标注 `[假设]`
- 可验收：每个功能都有明确验收标准

**输出产物**：`docs/PRD.md`，包含用户故事、功能清单（F01/F02/...）、验收标准、非功能需求、MVP 范围划定。

**实现方式**：通过 Read 工具读取用户原始需求，通过 Write 工具按模板生成 PRD 文件。模板定义了完整的结构：项目概述、目标用户、功能范围、用户故事与验收标准、非功能性需求、假设与待确认项。

---

#### 2.2.3 software-architect（软件架构师）

| 属性 | 值 |
|------|-----|
| 模型 | opus（需要最强推理能力做架构决策） |
| 工具 | Read, Write |
| 职责 | 技术选型、系统设计、生成 API 契约和数据库 Schema |

**这是整个流程最关键的 Agent**——其产出的契约文件决定所有后续实现的方向。

**输出产物**（4 个文件）：
1. `docs/TECH_SPEC.md` — 技术栈、目录结构、环境变量、编码规范、部署路径规范
2. `docs/API_CONTRACT.md` — 所有接口的完整定义（路径/方法/字段/错误码）
3. `docs/DB_SCHEMA.md` — 所有表结构、字段类型、索引、外键关系
4. `docs/DYNAMIC_CONTENT_MAP.md` — 动态内容映射表，防止前端硬编码

**被打回时的行为**：仅修正有问题的部分，不重写整个文件，并记录变更历史（版本号 v1.0 → v1.1 + 变更记录）。

**契约硬性要求**：
- 每个字段必须标注：类型 + 是否必填 + 说明
- 数组类型必须展示完整元素结构
- 错误码必须穷举所有已知场景
- 不得出现"等字段"、"其他参数"等模糊表述

**子路径部署防护**：TECH_SPEC.md 中包含"部署路径规范"章节，明确 `VITE_API_BASE` 的生产值和本地值，前端 API 调用层规范（禁止硬编码 `/api/...`），以及跳转/重定向规范。

---

#### 2.2.4 ui-designer（UI 设计师）

| 属性 | 值 |
|------|-----|
| 模型 | sonnet |
| 工具 | Read, Write, Edit, Glob, Grep |
| 职责 | 视觉规范 / 设计系统 / variables.css |

**两种工作模式**：
- **模式 A**：审查并优化现有项目（扫描现有样式 → 识别问题 → 生成设计规范 → 生成重构报告）
- **模式 B**：新项目建立设计规范（供 frontend-developer 读取后按规范实现）

**输出产物**：
1. `docs/DESIGN_SYSTEM.md` — 颜色/字体/间距/圆角/阴影/组件规范
2. `src/styles/variables.css` — 可直接引入的 CSS 变量文件

**设计体系**：基于 375px 设计稿基准，采用 vw 适配方案，4px 基础间距单位，5 级字号梯度，移动端正文最小 16px。

---

#### 2.2.5 database-optimizer（数据库工程师）

| 属性 | 值 |
|------|-----|
| 模型 | sonnet |
| 工具 | Read, Write, Edit, Bash, Glob, Grep |
| 职责 | 数据库迁移文件 + Model 层 + 索引设计 |

**核心纪律**：DB_SCHEMA.md 定义什么结构，就实现什么结构，字段名和类型不得擅自修改。发现 Schema 有歧义，写入 `DB_ISSUES.md` 并停止。

**输出产物**：
1. `migrations/` — 迁移文件（含 UP 和 DOWN）
2. Model / Entity 文件
3. `scripts/migrate.js` — 迁移运行器
4. `scripts/start.sh` — 启动脚本

**迁移运行基础设施**：必须创建 `schema_migrations` 跟踪表，确保增量迁移可追踪。init.sql/init_db.py 只执行一次，生产环境表结构变更必须有独立迁移机制。

**MySQL 乱码防范**：强制配置 `--character-set-server=utf8mb4`、`--init-connect='SET NAMES utf8mb4'`、`--skip-character-set-client-handshake`，并要求 Node.js 连接显式声明 `charset: "utf8mb4"`。

---

#### 2.2.6 backend-architect（后端工程师）

| 属性 | 值 |
|------|-----|
| 模型 | sonnet |
| 工具 | Read, Write, Edit, Bash, Glob, Grep |
| 职责 | 严格按照 API_CONTRACT.md 实现接口 |

**核心纪律**：API_CONTRACT.md 是唯一行动指南，路径、方法、字段名必须与契约完全一致。遇到歧义写入 `BACKEND_STATUS.md` 的 ISSUES 章节，不得自行决定。

**分层结构**：Router → Controller → Service → Model

**生产级规范**：
1. 健康检查端点（`GET /api/health`）——供部署验收使用
2. `waitForDB()` 数据库就绪等待——防止容器启动时数据库未就绪导致崩溃

**小程序安全规范**：
- 禁止 CORS `origin: '*'`（安全风险，会导致封号）
- 必须实现 API 鉴权（校验 X-WX-Code / JWT）
- 频率限制必须基于 openid / userId（IP 在小程序场景下不可靠）
- 涉及用户上传时必须做内容安全审核

---

#### 2.2.7 frontend-developer（前端工程师）

| 属性 | 值 |
|------|-----|
| 模型 | sonnet |
| 工具 | Read, Write, Edit, Bash, Glob, Grep |
| 职责 | 像素级 Figma 稿件还原 + API 对接 |

**双模式工作**：
- **Figma 读取模式**：通过 Figma MCP 读取设计稿的精确数值（颜色、间距、字体）
- **实现模式**：读取 API_CONTRACT + 设计数据清单，实现页面

**API 路径零容忍规则**：
```ts
// ✅ 唯一正确写法
const API_BASE = import.meta.env.VITE_API_BASE ?? ''
axios.get(`${API_BASE}/api/v1/todos`)

// ❌ 禁止硬编码
axios.get('/api/v1/todos')  // ← 生产 404
```

**前端容器 nginx.conf**：Vite/SPA 项目必须生成 `frontend/nginx.conf`，处理子路径部署的路径重写和 SPA 刷新不 404。

**跳转/重定向规范**：Vue Router / React Router 跳转只写应用内路径，Next.js 服务端重定向必须用 `new URL(req.url)` + `NEXT_PUBLIC_BASE_PATH` 显式拼接。

---

#### 2.2.8 testing-evidence-collector（QA 验证专家）

| 属性 | 值 |
|------|-----|
| 模型 | 未指定（使用默认） |
| 工具 | 所有工具 |
| 职责 | 任务级 QA，独立验证每个接口字段路径 |

**核心信念**：
- "截图不说谎"——视觉证据是唯一重要的真相
- "默认找问题"——第一版实现总有 3-5+ 个问题
- "证明一切"——每个声明都需要截图证据

**自动 FAIL 触发器**：
- 任何 Agent 声称"零问题"
- 第一次实现就拿满分
- 没有视觉证据的"luxury/premium"声明
- 没有完整测试证据的"production ready"

**报告格式**：包含现实核查结果、视觉证据分析、交互测试结果、找到的问题（至少 3-5 个）、诚实质量评估（禁止 A+ 幻想）、必需的下一步。

**在 Dev-QA Loop 中的关键作用**：QA Agent 是单独的 LLM session，它不知道 backend-architect / frontend-developer 内部怎么写的，只对照 API_CONTRACT 看产出代码。"评审者不是实现者"的设计，比让一个 Agent 自己写自己测可靠得多。

---

#### 2.2.9 security-engineer（安全工程师）

| 属性 | 值 |
|------|-----|
| 模型 | 未指定 |
| 工具 | 所有工具 |
| 职责 | 威胁建模 + 漏洞扫描 + OWASP 检查 |

**核心使命**：把安全融入 SDLC 每一阶段——从设计到部署。

**工作流程**：
1. 侦察与威胁建模（STRIDE 分析）
2. 安全评估（OWASP Top 10 复核代码）
3. 修复与加固（提供代码级修复）
4. 验证与监测

**输出产物**：`docs/SECURITY_REPORT.md`，包含高危漏洞清单（必须修）、中低危建议（可暂缓）。

**关键规则**：
- 绝不把"禁用安全控制"作为解决方案
- 始终假设用户输入是恶意的
- 优先使用经过充分测试的库
- 默认拒绝——白名单优于黑名单

---

#### 2.2.10 code-reviewer（代码评审专家）

| 属性 | 值 |
|------|-----|
| 模型 | 未指定 |
| 工具 | 所有工具 |
| 职责 | 正确性 / 可维护性 / 安全性 / 性能复审 |

**评审维度**（按优先级）：
1. **正确性**——它是不是做了它该做的事？
2. **安全性**——有没有漏洞？
3. **可维护性**——6 个月后还有人能看懂吗？
4. **性能**——有没有明显瓶颈？
5. **测试**——重要路径是否被测试覆盖？

**评审级别**：
- 🔴 Blocker（必须修）——安全漏洞、数据丢失风险、破坏 API 契约、子路径部署前缀丢失、硬编码 API 请求路径
- 🟡 Suggestion（应该修）——缺失输入校验、命名不清晰、性能问题
- 💭 Nit（建议改）——风格不一致、命名小改进

**输出产物**：`docs/REVIEW_REPORT.md`。

---

#### 2.2.11 reality-checker（最终验收官）

| 属性 | 值 |
|------|-----|
| 模型 | opus（需要最强推理做最终判断） |
| 工具 | Read, Bash, Glob, Grep |
| 职责 | 对照原始需求和契约文件做整体验收 |

**核心信条**：默认判决是 NEEDS WORK（需要返工），只有压倒性证据才会判 READY。

**READY 判决条件**（必须全部满足）：
- 所有任务清单项均为 `[x]`
- BACKEND_STATUS.md 的 ISSUES 章节为空
- SECURITY_REPORT.md 无高危问题
- REVIEW_REPORT.md 无必须修复项
- PRD 中所有 P0 功能验收标准已满足
- 服务可以正常启动
- 核心接口可以正常响应
- 子路径部署下重定向和 API 请求路径正确

**验证方式**：实际运行 `docker-compose up -d`、`curl` 健康检查和核心接口，不是"看代码觉得没问题"。

---

#### 2.2.12 devops-automator（DevOps 工程师）

| 属性 | 值 |
|------|-----|
| 模型 | 未指定 |
| 工具 | 所有工具 |
| 职责 | Docker / CI/CD / 部署配置 |

**输出产物**：
1. `Dockerfile`（前端两阶段构建：node → nginx；后端非 root 用户运行）
2. `docker-compose.yml`
3. CI/CD 配置

**部署路径前缀检查**（Phase 9 必须验证，不得跳过）：
1. 确认 `frontend/.env.production` 存在且包含 `VITE_API_BASE=/{APP_PATH}`
2. 确认 `frontend/.env.production` 包含 `VITE_BASE_URL=/{APP_PATH}/`
3. 确认 `vite.config.ts` 中 base 使用环境变量
4. grep 扫描 `frontend/src/` 确认无硬编码 `/api/` 调用路径

**Vite/SPA vs Next.js 区分处理**：前端框架不同，Dockerfile 和 nginx 处理方式完全不同。Vite 项目需要 nginx 静态服务 + nginx.conf，Next.js 项目自带路由不需要 nginx。

---

#### 2.2.13 technical-writer（技术文档专家）

| 属性 | 值 |
|------|-----|
| 模型 | 未指定 |
| 工具 | 所有工具 |
| 职责 | README / API 文档 / 教程 |

**输出产物**：
1. `README.md`（必须包含：项目说明 + 技术栈、本地开发启动方式、环境变量说明表格、首次部署步骤、代码更新后再次部署流程、数据库迁移使用说明、项目目录结构）
2. `docs/API_DOC.md`（基于 API_CONTRACT 的可读版文档）

**核心原则**：
- 代码示例必须能跑
- 不预设上下文——每篇文档独立成立
- 5 秒测试：README 必须让人 5 秒内知道这是什么、为什么要在意、如何开始

---

### 2.3 基建层 Agent（可选）

#### 2.3.1 infra-bootstrap-agent（服务器初始化）

一次性服务器初始化 Agent，7 个阶段：

| Phase | 内容 |
|-------|------|
| Phase 1 | 环境探测（SSH 连通性、操作系统检测、幂等检查） |
| Phase 2 | 安装 Docker（Ubuntu / CentOS 分支处理） |
| Phase 3 | 建立 Docker 网络 `gateway-net` |
| Phase 4 | 部署中央 Nginx 网关 `nginx-gateway` |
| Phase 4.5 | 部署共享 MySQL `infra-mysql` |
| Phase 5 | 安装 Certbot（HTTPS 可选） |
| Phase 6 | 基础安全加固（UFW / firewalld / 时区 / Docker 日志限制） |
| Phase 7 | 验收 |

**关键设计**：
- 幂等保障：每步先检查是否已完成，已完成则跳过
- 共享架构：所有应用容器加入 `gateway-net`，通过容器名路由，不暴露宿主机端口
- Nginx 网关约定：各应用部署时只向 `conf.d/locations/` 添加自己的 location 文件，不修改 `main.conf`

#### 2.3.2 app-deploy-agent（应用部署）

通用应用部署 Agent，8 个阶段：

| Phase | 内容 |
|-------|------|
| Phase 0 | 读取 `deploy.yaml` 决定部署策略 |
| Phase 0.5 | 前缀 404 预检（扫描硬编码 API 路径） |
| Phase 1 | 部署前检查 |
| Phase 2 | 修正 docker-compose.yml |
| Phase 3 | 传输代码（rsync） |
| Phase 4 | 生产环境配置（.env 生成 + 数据库建库建账号） |
| Phase 5 | 构建 & 启动 |
| Phase 6 | 注册到 Nginx 网关 |
| Phase 7 | 验收 |
| Phase 8 | 生成 GitHub Actions CI/CD 工作流 |

**三种数据库模式**（由 `deploy.yaml` 的 `db_mode` 字段决定）：

| 模式 | 说明 |
|------|------|
| `shared` | 使用基础设施层的 `infra-mysql`（推荐普通业务） |
| `dedicated` | 应用自带独立 MySQL 容器（敏感数据、特殊版本） |
| `none` | 无数据库（纯前端 / 纯静态） |

**Phase 0.5 前缀预检**是最关键的防护：在推送代码到生产前，确认前端 API 路径已正确使用环境变量前缀。发现硬编码 `/api` 路径会立即停止，禁止带此问题部署。

#### 2.3.3 deploy-yaml-schema（部署配置 Schema）

不是 Agent，而是一份 `deploy.yaml` 的字段契约文档。定义了应用部署时需要提供的所有参数，包括 `app_name`、`app_path`、`db_mode`、`db_name`、`frontend_container`、`backend_container` 等。

---

## 三、工作流程详解

### 3.1 11 阶段主流程

```
Phase 0   orchestrator 创建项目目录                       （10 秒）
Phase 1   → product-manager      → PRD.md
   ⏸ 人工检查点 #1：确认功能范围
Phase 2   → software-architect   → API_CONTRACT.md / DB_SCHEMA.md / TECH_SPEC.md
   ⏸ 人工检查点 #2：确认接口契约（最关键节点）
Phase 2.5 → ui-designer          → DESIGN_SYSTEM.md / variables.css
Phase 3   orchestrator 自己拆任务清单
Phase 4   → database-optimizer   → migrations/
Phase 5   → backend-architect    │ ┐ Dev-QA Loop
          → ev-collector         │ │ 逐任务循环
Phase 6   → frontend-developer   │ ┐ Dev-QA Loop
          → ev-collector         │ │ 逐任务循环
Phase 7   → security-engineer    → SECURITY_REPORT.md
Phase 8   → code-reviewer        → REVIEW_REPORT.md
Phase 9   → devops-automator     → Dockerfile + 部署
Phase 10  → reality-checker      → READY 或 NEEDS WORK
Phase 11  → technical-writer     → README + API_DOC
完工 ✅
```

### 3.2 Dev-QA Loop（核心创新）

这是整套系统最关键的质量保障机制——**每个任务都有任务级 QA 闭环**。

```
FOR 每个 backend-tasklist.md 中的 [ ] 任务：

  STEP 1 → 调用 backend-architect 实现该任务
            （必须先读 API_CONTRACT.md + DB_SCHEMA.md）
            产出：该接口的实现代码

  STEP 2 → 调用 testing-evidence-collector 验证
            （对照 API_CONTRACT 检查路径/字段名/错误处理）
            产出：PASS 或 FAIL + 具体原因

  STEP 3 → 决策
            PASS   → 任务标 [x]，进入下一任务
            FAIL（重试 < 3）→ QA 反馈传给 backend-architect 重做
            FAIL（重试 ≥ 3）→ 暂停，向用户报告卡点

ALL 任务 PASS 后 → 检查 BACKEND_STATUS.md ISSUES 章节
  有未解决 → 打回 software-architect 改契约 → 重跑受影响任务
```

**关键洞察**：QA Agent 是单独 LLM session，它不知道实现者内部怎么写的，只对照 API_CONTRACT 看产出代码。这种"评审者 ≠ 实现者"的设计，比让一个 Agent 自己写自己测可靠得多。

### 3.3 打回机制（重试树）

```
任意 Phase 出问题：
                    ┌─────────────────────────────────┐
                    │  问题分类                        │
                    └────────────┬────────────────────┘
                                 │
    ┌────────────────────────────┼────────────────────────────┐
    │                            │                            │
    ▼                            ▼                            ▼
契约有问题                   实现有问题                    评审有问题
(DB_ISSUES /                 (任务级 QA FAIL)              (REVIEW MUST FIX
 BACKEND ISSUES)              (安全高危)                    reality-checker
    │                            │                          NEEDS WORK)
    ▼                            ▼                            ▼
打回 software-architect      打回对应实现 agent           打回对应 agent
修改契约 → 重跑后续          重做该任务                   修复
(重试上限 2)                 (重试上限 3/任务)             (重试上限 1-2)
    │                            │                            │
    └────────────────────────────┴────────────────────────────┘
                                 │
                                 ▼
                          超限 → 暂停 → 向用户报告卡点
```

### 3.4 人工检查点

整个 11 阶段只在 2 个地方让用户介入：

| 检查点 | 位置 | 目的 |
|--------|------|------|
| #1 | Phase 1 完成后 | 确认 PRD 功能范围（否则 Phase 2 之后改一个字段就要重跑 Phase 4-6） |
| #2 | Phase 2 完成后 | 确认 API 契约（契约一旦确认，任何字段名变更都是大事故） |

其他阶段自动执行，因为有 Dev-QA Loop 和打回机制能自愈。

### 3.5 串行 vs 并行

orchestrator 选择**严格串行**执行，即使某些阶段理论上可以并行：

- Phase 5（后端）和 Phase 6（前端）理论上可并行 → 选择了串行（前端需要后端 API 跑通才能联调）
- Phase 7（安全）和 Phase 8（review）理论上可并行 → 选择了串行（安全修复可能改了代码，review 需要看最新代码）

**设计哲学**：质量 > 速度，宁可慢一点串行跑，也不让两个 Agent 同时改代码。

---

## 四、实现机制深度分析

### 4.1 Claude Code Sub-Agent 机制

Claude Code 的 Sub-Agent 是一个**独立 LLM 会话**机制。当 orchestrator 使用 `Task` 工具调用 `product-manager` 时：

1. Claude Code 创建一个新的 LLM 会话
2. 将 `product-manager.md` 的内容作为系统 Prompt 加载
3. 传入 orchestrator 指定的输入（如"用户需求是开发 todo app"）
4. 子 Agent 在独立会话中工作，拥有自己的工具权限（Read/Write 等）
5. 完成后将结果返回给 orchestrator

**关键特性**：
- 每个 Agent 在独立会话中运行，互不干扰
- 主对话 token 消耗极低（几千 token 就跑完一个完整项目）
- 子 Agent 之间通过文件系统（契约文件）通信，不直接交互

### 4.2 契约文件作为通信协议

各 Agent 之间不直接通信，而是通过**共享文件系统**间接协作：

```
docs/PRD.md           ← product-manager 写，software-architect 读
docs/API_CONTRACT.md  ← software-architect 写，backend-architect / frontend-developer / ev-collector 读
docs/DB_SCHEMA.md     ← software-architect 写，database-optimizer / backend-architect 读
docs/TECH_SPEC.md     ← software-architect 写，所有实现层 Agent 读
docs/DESIGN_SYSTEM.md ← ui-designer 写，frontend-developer 读
docs/BACKEND_STATUS.md← backend-architect 写，orchestrator 读
docs/DB_ISSUES.md     ← database-optimizer 写，orchestrator / software-architect 读
```

这种设计确保了：
- **解耦**：Agent 之间无需知道彼此的存在，只需知道文件格式
- **可追溯**：所有中间产物都有文件记录，可审计
- **可恢复**：任何阶段出问题，可以从上一个成功的文件重新开始

### 4.3 模型选择策略

| Agent | 模型 | 原因 |
|-------|------|------|
| orchestrator | opus | 需要最强推理做调度决策和打回判断 |
| software-architect | opus | 需要最强推理做架构设计和契约生成 |
| reality-checker | opus | 需要最强推理做最终验收判断 |
| product-manager | sonnet | PRD 生成不需要最强推理 |
| backend-architect | sonnet | 按契约实现，不需要额外推理 |
| frontend-developer | sonnet | 按契约和设计稿实现 |
| database-optimizer | sonnet | 按 Schema 实现迁移文件 |
| ui-designer | sonnet | 生成设计规范 |

opus 用于需要复杂推理和判断的场景，sonnet 用于执行性工作。这是成本与能力的平衡策略。

### 4.4 工具权限控制

每个 Agent 只能使用被授权的工具集：

| Agent | 工具 | 原因 |
|-------|------|------|
| product-manager | Read, Write | 只需读需求写 PRD |
| software-architect | Read, Write | 只需读 PRD 写契约 |
| backend-architect | Read, Write, Edit, Bash, Glob, Grep | 需要读写代码、搜索文件 |
| database-optimizer | Read, Write, Edit, Bash, Glob, Grep | 需要读写迁移文件、搜索代码 |
| reality-checker | Read, Bash, Glob, Grep | 只需读取验证、运行命令 |
| orchestrator | Task, Read, Write, Glob, Bash | 需要调度 Agent、写任务清单 |

**orchestrator 拥有 Task 工具**是关键——这是唯一能调度其他 Agent 的能力。其他 Agent 没有 Task 工具，不能创建子 Agent，防止了 Agent 链式调用导致的失控。

### 4.5 文件产物的生命周期

```
Phase 0: docs/ 目录创建（占位文件）
Phase 1: PRD.md 生成
Phase 2: API_CONTRACT.md / DB_SCHEMA.md / TECH_SPEC.md / DYNAMIC_CONTENT_MAP.md 生成
Phase 2.5: DESIGN_SYSTEM.md / variables.css 生成
Phase 3: backend-tasklist.md / frontend-tasklist.md 生成
Phase 4: migrations/ 目录 / start.sh / migrate.js 生成
         可能生成: DB_ISSUES.md（有问题时）
Phase 5: 后端代码实现
         更新: BACKEND_STATUS.md
Phase 6: 前端代码实现 + nginx.conf + .env 文件
Phase 7: SECURITY_REPORT.md 生成
Phase 8: REVIEW_REPORT.md 生成
Phase 9: Dockerfile / docker-compose.yml 生成
Phase 10: 验收报告生成
Phase 11: README.md / API_DOC.md 生成
```

---

## 五、设计哲学

### 5.1 七大设计原则

| 原则 | 体现在哪 |
|------|---------|
| **契约第一** | Phase 2 是最关键节点，后面 9 个 Phase 全都依赖契约 |
| **评审者 ≠ 实现者** | ev-collector 独立验证 backend/frontend 产出，不让一个 Agent 自己写自己测 |
| **打回有上限** | 重试 3 次还不行就暂停问用户，不死循环 |
| **人工介入点要少** | 只在 Phase 1/2 暂停，避免每步都打扰用户 |
| **职责单一** | 每个 Agent 只干一类事，互不交叉 |
| **质量 > 速度** | 宁可串行也不并行（前后端不能同时改代码） |
| **零容忍硬编码** | API 路径硬编码必须打回（来自部署翻车的真实教训） |

### 5.2 零容忍规则的来源

每一条零容忍规则背后都是一次真实事故：

| 零容忍规则 | 来源事故 |
|-----------|---------|
| 前端硬编码 `/api/...` 路径必须打回 | 部署到子路径后所有 API 请求 404 |
| CORS `origin: '*'` 禁止 | 微信小程序判定安全风险导致封号 |
| Phase 9 部署路径前缀检查 | 生产环境 API 全部 404 |
| Agent 自己写自己测说 OK | 代码实际没写完但 AI 声称完成 |
| AI 改了字段名前端不知道 | 前后端字段名不一致导致联调失败 |

### 5.3 与"裸 Claude Code"的区别

| 维度 | 裸 Claude Code | 标准团队 |
|------|---------------|---------|
| 角色边界 | 1 个 AI 全干 | 12 个 Agent 各司其职 |
| 契约约束 | 无（边写边改） | 必须先定 PRD/API/Schema |
| QA 验证 | 写完了说"应该 OK" | 任务级 QA Agent 独立验证 |
| 打回机制 | 没有 | 4 类规则 + 重试上限 |
| 部署路径检查 | 容易硬编码翻车 | Phase 9 强制检查 basePath |
| Token 消耗 | 主对话消耗高 | 主对话消耗低（子 Agent 在独立会话运行） |

---

## 六、安装与使用

### 6.1 安装

```bash
# 克隆仓库
git clone https://github.com/xuanbingbingo/claude-standard-dev-team.git

# 复制全部 Agent 到 Claude Code 目录
mkdir -p ~/.claude/agents
cp claude-standard-dev-team/agents/*.md ~/.claude/agents/

# 验证
ls ~/.claude/agents/ | grep -E "orchestrator|product-manager|software-architect"
```

### 6.2 启动

在 Claude Code 对话中输入：

```
使用标准团队帮我开发一个 todo app
```

orchestrator 会自动接管整个流程。

### 6.3 卸载

```bash
cd ~/.claude/agents/
rm orchestrator.md product-manager.md software-architect.md ui-designer.md \
   database-optimizer.md backend-architect.md frontend-developer.md \
   devops-automator.md testing-evidence-collector.md security-engineer.md \
   code-reviewer.md reality-checker.md technical-writer.md
```

### 6.4 Audit 模式

对已有代码做审查：

```
使用标准团队审查 xxx 项目
```

orchestrator 会进入 Audit 模式：code-reviewer → security-engineer →（可选）reality-checker。

---

## 七、典型时序

用户说"使用标准团队开发一个 todo app"后的完整流程：

```
T=0:00    用户发起需求
T=0:01    orchestrator → mkdir -p docs project-tasks
T=0:01    orchestrator → Task → product-manager → PRD.md
T=0:08    ⏸ 展示 PRD 功能列表，等用户确认
T=2:00    用户确认"继续"
T=2:00    orchestrator → Task → software-architect → 3 个契约文件
T=2:15    ⏸ 展示 API 接口列表 + 表结构，等用户确认
T=5:00    用户确认"继续"
T=5:00    orchestrator → Task → ui-designer → DESIGN_SYSTEM.md
T=5:08    orchestrator 自己拆任务清单
T=5:09    orchestrator → Task → database-optimizer → migrations/
T=5:15    Phase 5 后端 Dev-QA Loop 开始（逐任务循环）
T=8:00    Phase 5 全部 PASS
T=8:00    Phase 6 前端 Dev-QA Loop 开始
T=12:00   Phase 6 全部 PASS
T=12:00   Phase 7 → security-engineer → SECURITY_REPORT.md
T=12:30   Phase 8 → code-reviewer → REVIEW_REPORT.md
T=13:00   Phase 9 → devops-automator → Dockerfile + 路径检查
T=13:15   Phase 10 → reality-checker → READY
T=13:30   Phase 11 → technical-writer → README + API_DOC
T=13:30   完工 ✅
```

整个过程大约 30-90 分钟（取决于应用复杂度），主对话 token 消耗极低（几千 token），加起来约 50-200k token。

---

## 八、基建层：从代码到上线

12 个核心 Agent 跑完 Phase 11 后，代码库已经完整可上线。但如果要"真正部署到一台云服务器"，还需要基建层 3 个 Agent：

### 8.1 典型部署架构

```
Internet
    │
    ▼ :80
nginx-gateway (gateway-net)
    ├── /todo/      → todo-frontend:80
    ├── /todo/api/  → todo-backend:3000
    ├── /blog/      → blog-frontend:80
    └── /blog/api/  → blog-backend:3000
```

### 8.2 使用流程

```
新服务器 → infra-bootstrap-agent（一次）
新应用   → 仓库根目录写 deploy.yaml → app-deploy-agent
```

### 8.3 deploy.yaml 示例

```yaml
app_name: todo
app_path: todo
db_mode: shared
db_name: todo_db
frontend_container: todo-frontend
backend_container: todo-backend
enable_https: true
```

---

## 九、局限性与适用范围

### 9.1 技术局限

| 局限 | 说明 |
|------|------|
| 仅支持 Claude Code | 依赖 Claude Code 的 Sub-Agent 机制，Cursor / Cline 等不可用 |
| QA 依赖 LLM 判断 | testing-evidence-collector 没有真实浏览器环境，部分视觉验证依赖推理 |
| 无真实测试执行 | Dev-QA Loop 的验证是代码审查式而非真实运行测试 |
| 串行执行 | 所有 Phase 串行执行，中大型项目耗时较长 |

### 9.2 场景局限

| 不适合 | 原因 |
|--------|------|
| 纯前端原型 | 杀鸡用牛刀 |
| 单文件脚本 | 不需要 12 人团队 |
| 一次性小工具 | 流程过重 |
| 评估阶段 | 先用裸 Claude Code 跑通一遍再说 |

---

## 十、文件清单

| 文件 | 说明 |
|------|------|
| `README.md` | 项目概览与 5 分钟上手 |
| `WORKFLOW.md` | 11 阶段工作流详解 |
| `INSTALL.md` | 安装/卸载/排错指南 |
| `agents/orchestrator.md` | 总指挥 Agent 定义 |
| `agents/product-manager.md` | 产品经理 Agent 定义 |
| `agents/software-architect.md` | 软件架构师 Agent 定义 |
| `agents/ui-designer.md` | UI 设计师 Agent 定义 |
| `agents/database-optimizer.md` | 数据库工程师 Agent 定义 |
| `agents/backend-architect.md` | 后端工程师 Agent 定义 |
| `agents/frontend-developer.md` | 前端工程师 Agent 定义 |
| `agents/devops-automator.md` | DevOps 工程师 Agent 定义 |
| `agents/testing-evidence-collector.md` | QA 验证专家 Agent 定义 |
| `agents/security-engineer.md` | 安全工程师 Agent 定义 |
| `agents/code-reviewer.md` | 代码评审专家 Agent 定义 |
| `agents/reality-checker.md` | 最终验收官 Agent 定义 |
| `agents/technical-writer.md` | 技术文档专家 Agent 定义 |
| `agents/infra-bootstrap-agent.md` | 服务器初始化 Agent（基建层） |
| `agents/app-deploy-agent.md` | 应用部署 Agent（基建层） |
| `agents/deploy-yaml-schema.md` | deploy.yaml Schema 文档（基建层） |

---

## 十一、总结

Claude Standard Dev Team 的核心创新在于：

1. **契约驱动开发**：所有 Agent 围绕同一份 API 契约工作，消除了"AI 改了字段名前端不知道"的问题
2. **Dev-QA Loop**：每个任务都有独立的 QA Agent 验证，PASS 才继续，FAIL 自动打回，3 次重试上限防止死循环
3. **评审者 ≠ 实现者**：QA Agent 在独立 LLM session 中运行，只看契约和产出代码，不知道实现者的内部思考
4. **零容忍硬编码**：API 路径硬编码必须打回，这是从真实部署翻车事故中总结出来的
5. **最少人工介入**：只在 Phase 1（PRD）和 Phase 2（API 契约）两个关键节点暂停，其他全自动
6. **基建层闭环**：从代码到真正上线，3 个基建层 Agent 补齐最后一步

这套系统的设计思想对任何多 Agent 协作场景都有参考价值：通过契约文件解耦 Agent 之间的通信、通过独立 QA 防止自我验证、通过重试上限防止死循环、通过零容忍规则防止常见错误模式。
