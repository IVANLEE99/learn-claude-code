---
name: ai-news-factory
description: AI News Factory - 从日报/周报/月报 Markdown 自动生成短视频+图文的完整 Pipeline。触发词: "AI日报", "AI周报", "AI月报", "新闻工厂", "news factory", "日报视频", "周报视频", "月报视频", "AI news video"
version: 3.27.0
---

# AI News Factory — 日报/周报/月报短视频自动生成 v3.27.0

将 AI 日报/周报/月报 Markdown 自动转化为 B站风格短视频 + 多平台发布内容，完整 Pipeline：报告 → 去重/选材 → 事件切分 → 视频脚本 → 分镜 → 图片 → TTS → 字幕 → 视频合成 → 封面 → 多平台发布信息 → 公众号图文 → 多平台上传。支持三种模式：日报（单日去重）、周报（7天聚合）、月报（消费 linuxdo-daily v13 已聚合的月报 md，趋势级选材）。

**核心原则：语义 `group_caps` 先切行，再以真实音频为锚——faster-whisper 词级时间戳 + SequenceMatcher 对齐。字幕内容 100% 来自原始脚本、时间 100% 来自音频真实发音时刻。禁止逐标点切行，禁止按字硬切，禁止按字数比例切时间轴。**

### 🔴 全局规则：所有平台上传一律存草稿

**v2.8.0 新增**：无论日报还是周报，所有平台（B站/抖音/视频号/公众号）上传后一律**保存草稿**，不直接发布/投稿。

**原因**：
- 标题、封面、合集等可能需要用户二次确认
- 避免因自动发布导致的内容错误或违规风险
- 用户可在各平台草稿箱中检查后手动发布

**各平台存草稿方式**：
| 平台 | 存草稿操作 |
|------|-----------|
| B站 | 点击「存草稿」按钮（ref=e496） |
| 抖音 | 点击「暂存离开」或直接关闭标签页（视频自动保存） |
| 视频号 | 点击「保存草稿」按钮 |
| 公众号 | 点击「保存为草稿」按钮 |

### 🔴 浏览器与 Profile 全局铁律（v3.7.0 / 2026-07-18 实测）

**问题**：同日流水线里 MCP Playwright 与独立 `playwright-core` 脚本若**共用** `ms-playwright-mcp/mcp-chrome-*` 登录态，会互抢锁、被 `pkill`、或在视频号双 body 页触发 MCP 崩溃，表现像「浏览器老是退出」。

**铁律**：
1. **同一时刻只用一种浏览器驱动**：要么全程 MCP（`browser_*` 工具），要么全程独立脚本；禁止中途混用同一 `user-data-dir`。
2. **独立脚本启动前**才允许 `pkill -f "user-data-dir=.../mcp-chrome-..."`；**不要**对普通 Chrome / Chromium 全局 `pkill`。
3. **视频号页面**（`channels.weixin.qq.com`）存在 **wujie 双 body**（外层 + `wujie-app body`）。在此页调用 `browser_snapshot` / `browser_find` / `browser_file_upload` / `browser_tabs` 常报：
   `strict mode violation: locator('body') resolved to 2 elements`
   **处理**：所有探测与操作放进**一次** `browser_run_code_unsafe`；返回前 `page.goto('https://www.baidu.com')` 离开双 body 页；文件选择器用脚本内 `waitForEvent('filechooser') + setFiles`，勿拆成单独 `browser_file_upload`。
4. **beforeunload**：从编辑页离开时弹「将此次编辑保留？」→ 先 `browser_handle_dialog(accept=true)` 或脚本内点「保存/不保存」，否则 `net::ERR_ABORTED`。
5. 独立脚本结束若用户要核对 UI，可**不** `context.close()`，改为提示用户手动关窗（用户明确要求「不要关太快」时）。

## ⚡ 权限预授权（必须在执行前完成）

**在开始 Pipeline 之前，必须先获得用户的一次性预授权。执行过程中不再逐个询问权限。**

**🔴 重要：预授权覆盖所有阶段（内容生成 + 全部平台上传），一次确认后全程不再询问。**

### 预授权原则

1. **一次授权，全程执行**：用户确认后，后续所有操作（文件读写、API调用、浏览器操作）不再询问
2. **信息一并收集**：在预授权时同时收集 API URL、Key、上传平台等信息
3. **失败自动重试**：API 调用失败自动重试一次，不询问用户
4. **浏览器锁自动处理**：检测到浏览器锁时自动清理（删除 SingletonLock + kill 旧进程），不询问用户
5. **DNS 劫持自动绕过**：检测到 API 连接超时时，使用 `nslookup` 获取真实 IP + `curl --resolve` 绕过本地代理 DNS 劫持（198.18.x.x 网段），不询问用户

### 预授权检查清单

向用户展示以下清单，请求一次性确认：

```
🎬 AI News Factory 权限预授权

执行以下操作需要你的授权，确认后全程不再询问：

📁 文件操作
  ☐ 读取日报 Markdown 文件（含历史日报用于去重）
  ☐ 写入脚本、分镜、Prompt、字幕、公众号文章等文件
  ☐ 复制资源到 video-project/public/

🔧 Shell 执行
  ☐ 调用 mimo-tts.sh 生成配音（逐场景串行）
  ☐ 调用 ffprobe 获取音频时长
  ☐ 调用 npx remotion render 渲染视频
  ☐ kill 旧浏览器进程（如遇浏览器锁）

🌐 API 调用
  ☐ 图片生成 API（用户提供 URL + Key）
  ☐ TTS API（mimo-tts）

🖥️ 浏览器操作（全部平台上传，一律存草稿）
  ☐ B站：自动上传视频、封面、填写标题/简介/标签、选择合集、存草稿
  ☐ 抖音：自动上传视频、封面、填写描述、选择合集、存草稿
  ☐ 视频号：自动上传视频、封面、填写描述/短标题、选择合集、存草稿
  ☐ 公众号：自动创建文章、填写标题/正文、上传封面、声明原创、选择合集、存草稿

请回复「确认」或「全部授权」开始执行。
```

### 用户输入收集

在预授权时一并收集以下信息（避免中途打断）：

```
需要你提供：
1. 📄 日报文件路径（默认: data/reports/YYYY-MM-DD.md）
2. 🖼️ 图片生成 API URL
3. 🔑 图片生成 API Key
4. 📤 上传平台（默认: 全部；可指定如「B站+公众号」）
```

## 触发条件

- "AI日报", "新闻工厂", "news factory"
- "日报视频", "生成日报视频", "AI news video"
- "把日报做成视频", "日报转视频"
- "AI周报", "羊报AI周刊", "weekly report", "周报视频"
- "AI月报", "羊报AI月报", "monthly report", "月报视频", "把月报做成视频", "月报转视频"
- "破格模式", "破格元素", "破格风格", "元素破格"
- "精简模式", "精简", "排序", "精华版", "3W", "压新闻"

## 模式参数映射表（v3.1.0 新增，单一事实源）

本表是 daily/weekly/monthly 三模式字段对照的**唯一事实源**。Phase 0 依据 `REPORT_PATH` 或触发词判定 `REPORT_MODE` 后，所有下游 Phase 一律按本表读取参数，**禁止在脚本/封面/标题/合集里硬编码"今日羊报AI"或"YYYY-MM-DD"**。

| 字段 | 日报 daily | 周报 weekly | 月报 monthly |
|------|-----------|------------|-------------|
| `REPORT_PATH` 默认 | `data/reports/YYYY-MM-DD.md` | 7 份日报（程序读取最近7天） | `data/monthly/YYYY-MM.md` |
| 输出目录 | `news-pipeline/YYYY-MM-DD/` | `news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD/` | `news-pipeline/monthly/YYYY-MM/` |
| 是否重新聚合 | 否 | 是（读 7 天日报） | **否**（直接消费月报 md，linuxdo-daily v13 已聚合） |
| 去重策略 | 对比前 3 天日报 | 对比上一期周报 | **对比上一期月报**（`data/monthly/{上月}.md`，不扫日报） |
| 事件粒度 | 单日单帖事件 | 周内事件 | **月度趋势级**（4 趋势 + TOP 主题） |
| 事件数档位 | 4-6（精简 3-5） | **1深聊（TOP1≥20）+ 2-3快讯（≥15）** | **4 趋势主线**（精简 3 趋势） |
| 视频总时长 | 60-120s（≤150s） | **100-150s**（深聊型，替代旧 90-120s） | **180-240s（≤300s）** |
| 每段字数 | ≤80 字 | ≤80 字 | **≤100 字** |
| 标题前缀 B站 | `【{YYYY-MM-DD}】`（日期在前） | `【{MM-DD~MM-DD}】`（日期在前） | `【{YYYY-MM}】`（日期在前） |
| 标题后缀 B站 | `… \| 今日羊报AI`（报刊名在后） | `… \| 羊报AI周刊`（报刊名在后） | `… \| 羊报AI月报`（报刊名在后） |
| 抖音标题 | `今日羊报AI YYYY-MM-DD`（≤30字） | `羊报AI周刊 MM-DD~MM-DD`（≤30字） | `羊报AI月报 YYYY-MM`（≤30字） |
| 视频号标题 | `今日羊报AI M月D日`（≤16字） | `羊报AI周刊 M月D日至D日`（≤16字） | `羊报AI月报 YYYY年M月`（≤16字） |
| 日期字段 | `YYYY-MM-DD` | `MM-DD~MM-DD` | `YYYY-MM` |
| tags 首 tag | `今日羊报AI` | `羊报AI周刊` | `羊报AI月报` |
| tags 主题 tag | `AI日报` | `AI周报` | `AI月报` / `AI月度盘点` |
| 封面品牌名 | `今日羊报 AI` | `羊报AI周刊` | `羊报AI月报` |
| 封面日期字段 | `{YYYY-MM-DD}` | `{YYYY-MM-DD} ~ {YYYY-MM-DD}` | `{YYYY-MM}` |
| 视频渲染文件名 | `【{YYYY-MM-DD}】{核心标题}… \| 今日羊报AI.mp4` | `【{MM-DD~MM-DD}】{核心标题}… \| 羊报AI周刊.mp4` | `【{YYYY-MM}】{核心标题}… \| 羊报AI月报.mp4` |
| B站合集名 | `「今日羊报 AI」` | `「羊报AI周刊」` | `「羊报AI月报」` |
| 公众号合集名 | 同 B站 | 同 B站 | 同 B站 |
| 公众号作者 | `今日羊报AI`（≤8字） | `羊报AI周刊`（≤8字） | `羊报AI月报`（≤8字） |
| 公众号署名 | `今日羊报 AI · YYYY-MM-DD` | `羊报AI周刊 · MM-DD~MM-DD` | `羊报AI月报 · YYYY-MM` |
| 公众号结尾 CTA | `每天 9 点带你速览 AI 圈最热的 5 条新闻` | `每周带你盘点 AI 圈一周大事` | `每月带你回顾 AI 圈整月风向` |
| 简介数字规则 | 版本号简化 + 数字中文 | 同日报 | **强制全数字中文化**（见 B站简介数字中文化章节） |
| 精简模式可叠加 | 是 | 是 | 是（精简月报 = 3 趋势，≤180s） |
| **专业锚点** | **15s × 1**（`ai-concept-bank`） | **30–60s × 1** | **30–60s × 1** |
| **锚点库路径** | `ai-concept-bank/concepts.json` | 同左 | 同左 |
| **脚本默认结构** | **3W + 可信度** | **3W + 可信度** | 趋势内嵌 3W + 可信度 |
| **灰色渠道上限** | **每期 ≤1 条** | **每期 ≤1 条** | **每期 ≤1 条** |

**模式判定规则**（Phase 0 自动）：
- `REPORT_PATH` 含 `data/monthly/`，或触发词含"月报/monthly" → `REPORT_MODE=monthly`，`MONTH_LABEL=YYYY-MM`
- 触发词含"周报/weekly"，或 `REPORT_PATH` 含 `data/weekly/` → `REPORT_MODE=weekly`
- 否则 → `REPORT_MODE=daily`

**专业锚点（v3.4.0）**：每期默认 1 个，算法与写 log 见 `templates/professional-anchor.md`；主库为 submodule `ai-concept-bank/`（禁止另建 `news-pipeline/concept-bank`）。

## 周报模式

**当触发词包含"周报"或"weekly"时，进入周报模式：**

### 周报与日报的区别

| 项目 | 日报 | 周报 |
|------|------|------|
| 数据源 | 单日日报 | 7天日报汇总 |
| 输出目录 | `news-pipeline/YYYY-MM-DD/` | `news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD/` |
| 封面提示词 | 单日事件 | 本周多事件拼贴 |
| 视频脚本 | 3-5个当日事件 | **1件大事3W深聊50s + 2-3条一句话快讯**（见 `templates/script-template-weekly.md`，替代旧 5-6 条堆叠） |
| 过滤规则 | 无 | **过滤公益站/中转站/倒卖相关内容** |
| 标题格式 | `【{日期}】...| 今日羊报AI` | `【{日期}】...| 羊报AI周刊` |

### 周报生成流程

1. **读取本周日报**：读取 `data/reports/` 目录下最近7天的日报文件
2. **提取关键事件**：每天选出1-2个最重要事件，过滤公益站相关内容
3. **🔴 Step 1.4w 周报选材（本周1件大事选取）**：按五维评分卡（影响范围/新鲜度/实用性/话题性/争议性，1-5 分，满分 25）对周内事件打分——**TOP1（总分≥20）进深聊 50s**（讲周一到周五的时间线演变，日报做不到的差异点）；**第 2-4 名（总分≥15）降为快讯一句话**（What+SoWhat 合并）；**<15 一律不进脚本**
4. **生成周报 Markdown**：输出到 `news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD.md`
5. **生成周报封面**：使用周报专用封面提示词（多事件拼贴风格）
6. **生成视频脚本**：**1件大事3W深聊50s + 锚点15-20s + 2-3条一句话快讯20s + CTA，总时长100-150s**（见 `templates/script-template-weekly.md`，替代旧 5-6 条堆叠）
7. **后续流程**：与日报相同（分镜→图片→TTS→字幕→视频→上传）

> 🔴 **周报 Hook 约束**：只选本周最冲突的 1 件作反转/警告开场（套 4 主力公式之一）；**禁堆叠≥2事件**；禁"本期周刊把本周N件大事一次讲清"套话后缀；其余事件降为快讯。

### 周报封面提示词模板

```
A professional Chinese AI news studio weekly cover image. Empty modern curved news desk, NO human presenter, NO realistic human face or news anchor. Behind the desk are multiple large display screens showing: {本周核心事件相关视觉元素，产品/抽象图形}. The studio has dramatic blue and red neon lighting. In the top right corner, display the text "羊报AI周刊" in large white Chinese characters. In the center of the image, display the date range "{YYYY-MM-DD} ~ {YYYY-MM-DD}" in very large white bold text. Professional broadcast news photography style, photorealistic environment, highly detailed, cinematic lighting, 16:9 aspect ratio. No people, no faces.
```

### 周报过滤规则

**以下内容必须过滤掉：**
- 公益站相关（N1nEAPI、RawChat、PrismAI、Alpha、薄荷等）
- 中转站价格变动
- 倒卖/交易相关内容
- 兑换码/邀请码分享

**保留的内容：**
- 模型发布与更新
- 公司动态（IPO、融资、收购）
- 重大安全事件
- 开源模型发布
- 行业政策与监管
- 重大技术突破

## 月报模式（v3.1.0 新增）

**当触发词包含"月报"或"monthly"，或 `REPORT_PATH` 指向 `data/monthly/*.md` 时，进入月报模式。**

### 月报与日报/周报的区别

| 项目 | 日报 | 周报 | 月报 |
|------|------|------|------|
| 数据源 | 单日日报 | 7天日报汇总 | **linuxdo-daily v13 月报 md**（已聚合，不重算） |
| 输入路径 | `data/reports/YYYY-MM-DD.md` | `data/reports/*.md`（7天） | `data/monthly/YYYY-MM.md` |
| 输出目录 | `news-pipeline/YYYY-MM-DD/` | `news-pipeline/weekly/...` | `news-pipeline/monthly/YYYY-MM/` |
| 事件粒度 | 单日事件 | 本周事件 | **月度趋势**（一条趋势跨多日多帖） |
| 是否去重 | 对比前3天日报 | 对比上期周报 | **月报已聚合去重，跳过跨日去重**；仅对比上期月报避免重复趋势 |
| 脚本结构 | Hook+4段正文+CTA | **Hook + 本周深聊1件(50s) + 锚点 + 快讯2-3条 + CTA** | **Hook + 4趋势段 + 月度总结 + 下月展望 + CTA** |
| 总时长 | 60-150s | **100-150s**（深聊型） | 180-240s（≤300s） |
| 每段字数 | ≤80 字 | ≤80 字 | ≤100 字 |
| 封面品牌 | 今日羊报 AI | 羊报AI周刊 | 羊报AI月报 |
| 标题前缀 | 【{日期}】…（报刊名在后） | 【{日期}】…（报刊名在后） | 【{日期}】…（报刊名在后） |
| 日期字段 | YYYY-MM-DD | MM-DD~MM-DD | YYYY-MM |
| 简介数字规则 | 版本号简化 | 同日报 | **强制全数字中文化**（见 B站简介数字中文化章节） |

### 月报生成流程

1. **读取月报 md**：`data/monthly/{YYYY-MM}.md`（**不读取当月日报，不重新聚合**——linuxdo-daily v13 已完成跨日聚合与去重）
2. **对比上期月报**（去重）：读取 `data/monthly/{上一个月}.md`，对比 4 条趋势是否与上月高度重叠。重叠趋势标记「延续」并在脚本中合并表述，避免重复展开。
3. **选材**：按下方"月报选材规则"，从 4 条月度趋势 + TOP10 主题中选 4 条趋势主线 + 4-8 个支撑案例。
4. **生成月报视频脚本**：输出到 `news-pipeline/monthly/{YYYY-MM}/scripts/`，引用 `templates/script-template-monthly.md`。
5. **生成月报封面**：使用月报专用封面提示词（下方模板），引用 `templates/image-prompt-monthly.md`。
6. **后续流程**：与日报/周报相同（分镜→图片→TTS→字幕→视频→上传），但所有标题/品牌名/合集名/日期字段按模式参数映射表读取。

### 月报封面提示词模板

```
A professional Chinese AI news studio monthly cover image. Empty modern curved news desk, NO human presenter, NO realistic human face or news anchor. Behind the desk are multiple large display screens arranged in a grid showing: {本月4条趋势相关视觉元素}. The studio has dramatic blue and red neon lighting. In the top right corner, display the text "羊报AI月报" in large white Chinese characters. In the center of the image, display the month "{YYYY-MM}" in very large white bold text. Professional broadcast news photography style, photorealistic environment, highly detailed, cinematic lighting, {ratio} aspect ratio. No people, no faces.
```

### 月报选材规则（最关键，区别于周报）

> 月报的"事件"是**趋势级**，不是单帖级。选材以 4 条月度趋势为主线骨架，每条趋势配 1-2 个代表性 TOP 主题作为支撑案例。**禁止把 4 趋势拆成 8-10 个单日事件回退日报结构。**

1. **4 条月度趋势全部纳入骨架**（不砍趋势，砍则丢信息）。若某趋势与上月高度重叠（如上月也是 OpenAI 调度混乱），标记为"延续趋势"，配 1 个本月新进展案例，合并表述。
2. **每条趋势选 1-2 个代表主题**：优先选该趋势「代表主题」字段中浏览量最高的 1 条；TOP10 中归属该趋势的再选 1 条。总数 = 4 趋势 × 1-2 = **4-8 个支撑点**。
3. **二次过滤公益站/套利类 TOP 主题**：月报 md 本身已过滤公益站/中转站（151 条），但 TOP10 仍可能含套利账号帖（如"墨西哥18刀买一送一"）或渠道促销帖（如"Codex 渠道半价"）。这类帖必须用趋势代表主题替代，不得入选。
4. **脚本结构**：1 Hook + 4 趋势段（每段 = 趋势概述 + 1-2 案例支撑，约 100 字）+ 1 月度总结段 + 1 下月展望段 + 1 CTA = **8-9 段**。
5. **精简月报模式**：砍到 3 趋势（每趋势配 1 案例共 6-7 段），总时长 ≤180s。

### 月报过滤规则

沿用周报过滤规则（公益站/中转站/倒卖/兑换码）。月报 md 已做一轮过滤，Phase 1 选材时再做一次 TOP10 套利帖的二次过滤。

### 月报模式叠加

| 组合 | 触发词示例 | 说明 |
|------|-----------|------|
| 精简 + 月报 | "精简 月报" | 精简版月报，3 趋势，≤180s |
| 破格 + 月报 | "破格 月报" | 月报脚本 + 破格标记 |
| 精简 + 破格 + 月报 | "精简 破格 月报" | 全部叠加 |

## 精简模式

**当触发词包含"精简"或"3W"时，开启精简模式。可与周报模式、破格模式叠加使用。**

### 什么是精简模式

**v3.4：3W 已是全模式默认。** 精简模式 = 先按重要程度排序 + 更少条数 + 更短句。  
3W（What—So What—Now What）源自哈佛/麦肯锡分析框架；细则见 `templates/credibility-and-tone.md`。

### 3W 模型说明

| 3W 层 | 含义 | 脚本对应 | 核心目的 |
|--------|------|----------|---------|
| **What**（事实层） | 客观描述事件本身 | 发生了什么 | 剥离情绪和猜测 |
| **So What**（含义层） | 连锁反应、风险与机遇 | 影响啥 | 分析深层影响 |
| **Now What**（行动层） | 决策建议和优先级 | 值不值得跟进 | 推导行动建议 |

### 精简模式与标准模式的区别

| 项目 | 标准模式（v3.4 默认 3W） | 精简模式 |
|------|---------|---------|
| 事件筛选 | 用户选 4-6 个 | **AI 先排序，精选 3-5 个** |
| 脚本结构 | **Hook + 每条 3W + 可信度 + 锚点 + CTA** | **同结构，更短句；CTA 可省** |
| 每条时长 | 15-25s | **10-20s（更紧凑）** |
| 总时长 | 75-135s（≤160 含锚点） | **60-100s（含锚点）** |
| 其他阶段 | 不变 | 不变（分镜/图片/TTS/字幕/上传） |

### 精简模式规则

1. **Phase 1 排序步骤**：按 5 个维度给事件打分（1-5 分），展示排序结果供用户确认
2. **精选 3-5 条**：从排序结果中选最重要的 3-5 条
3. **每条仍用 3W + 可信度**（比标准模式更短：每段 1-2 句）
4. **其他阶段不变**：分镜、图片、TTS、字幕、渲染、上传与标准模式相同

### 模式叠加规则

| 组合 | 触发词示例 | 说明 |
|------|-----------|------|
| 精简 + 标准 | "精简模式" | 最常用，精简版日报 |
| 精简 + 破格 | "精简 破格" | 3W 脚本 + 破格标记叠加 |
| 精简 + 周报 | "精简 周报" | 精简版周报，3-5 条本周精华 |
| 精简 + 破格 + 周报 | "精简 破格 周报" | 全部叠加 |

## 破格模式

**当触发词包含"破格"时，开启破格模式。可与周报模式叠加使用。**

### 什么是元素破格

打破常规逻辑，制造**反差感**和**意外感**。6种维度：

| 维度 | 含义 | 示例 |
|------|------|------|
| 身份破格 | 谁在做（身份×行为反差） | 保安跳霹雳舞 |
| 场景破格 | 在哪做（行为×环境反差） | 农村走秀 |
| 道具破格 | 用什么做（工具×目的反差） | 方便面写字 |
| 语言破格 | 怎么说（风格×内容反差） | 英语卖农产品 |
| 对象破格 | 对谁做（目标×行为反差） | 给鸡开会 |
| 角色破格 | 谁是什么（设定×行为反差） | 猪会钓鱼 |

### 破格模式与标准模式的区别

| 项目 | 标准模式 | 破格模式 |
|------|---------|---------|
| 脚本风格 | 口播解说体 | 口播 + 破格标记 |
| Hook | 悬念/冲突 | 必须用一种破格类型开场 |
| 正文 | 纯信息传递 | 每个场景可标注破格类型 |
| 图片Prompt | 写实新闻摄影 | 写实 + 破格视觉关键词 |
| 分镜 | 标准镜头 | 增加倾斜构图/对比蒙太奇 |
| TTS | 统一风格 | 可按场景切换风格 |
| 其他阶段 | 不变 | 不变（TTS/字幕/渲染/上传） |

### 破格模式规则

1. **Hook 必须使用一种破格**（从6种中选）
2. **正文至少使用2种不同破格**（同一视频不重复同一类型）
3. **每种破格标注类型**（脚本中用 `[身份破格]` 标记）
4. **图片 Prompt 反映破格视觉**（在 prompt 中加入反差关键词）
5. **分镜增加破格镜头**（倾斜构图、对比蒙太奇等）
6. **TTS 可选多风格**（不同场景用不同语调）

## 前置依赖

- **mimo-tts skill**: 语音合成 (`~/Documents/learn-claude-code/skills/mimo-tts/`)
- **ffmpeg**: 音频格式转换（获取音频时长）
- **Remotion**: 视频渲染（`news-pipeline/video-project/`）
- **Playwright MCP**: B站自动上传
- **图片生成 API**: 用户提供 URL + Key（支持 OpenAI 兼容格式）

## 执行流程

### Phase 0: 获取用户输入

**在预授权阶段已收集以下信息，直接使用：**

- `REPORT_PATH`: 报告文件路径（日报 `data/reports/YYYY-MM-DD.md` / 周报 7 份日报 / 月报 `data/monthly/YYYY-MM.md`）
- `API_URL`: 图片生成 API URL
- `API_KEY`: 图片生成 API Key
- `UPLOAD_PLATFORMS`: 上传平台列表
- `STYLE_MODE`: 风格模式（standard / poge），默认 standard
- `CONDENSED`: 是否启用精简模式（true / false），默认 false
- `REPORT_MODE`: 报告模式（daily / weekly / monthly），按模式参数映射表"模式判定规则"自动判定
- `MONTH_LABEL`: 月报模式下的月份标签 YYYY-MM（如 2026-06），仅 monthly 模式使用

如信息不完整，在此处补充询问。

**🔴 月报前置检查**（仅当 `REPORT_MODE=monthly`）：
- 确认 `data/monthly/{YYYY-MM}.md` 存在；若不存在，提示用户先运行 linuxdo-daily 月报模式生成。
- 确认 B站/公众号后台已创建合集「羊报AI月报」（首次运行月报前必须人工创建，否则 Phase 11/12 合集选择失败）。

### Phase 1: 输入、去重与事件切分

**模式分派**：
- `daily`: 执行 Step 1.1 → 1.4 原流程（去重 + 排序 + 事件切分）
- `weekly`: 执行周报流程（读 7 天日报聚合）
- `monthly`: **跳过 Step 1.2 跨日去重**（月报已聚合），执行 Step 1.5 月报选材流程

**Step 1.1**: 读取今日日报内容（daily/weekly）；monthly 模式读取 `data/monthly/{YYYY-MM}.md`。

**Step 1.2**: 🔴 去重检查

读取前 3 天的日报文件（`data/reports/YYYY-MM-DD.md`），对比今日事件：

```bash
ls data/reports/*.md | sort -r | head -4  # 获取最近4天的文件
```

**去重规则**：
- 同一事件首次出现在之前的日报中 → 标记为「重复」
- 同一事件的后续进展（如新数据、新声明）→ 标记为「新进展」，可保留
- 纯回顾/总结性提及 → 标记为「重复」

向用户展示去重结果：
```
🔍 去重对比（vs 06-03, 06-04）

❌ 重复事件（建议去掉）：
  - [事件A] — 首次出现在 06-03
  - [事件B] — 首次出现在 06-04

✅ 今日新鲜事件：
  1. [事件1] — 全新，2.6k 浏览
  2. [事件2] — 全新，1.4k 浏览
  3. [事件3] — 新进展（06-03 首次报道，今天有新数据）
```

**Step 1.3**: 用户确认选择要制作视频的事件（建议 4-6 个）。

**⚡ 免确认模式（v3.8.0 / v3.9.0）**：用户消息含「事件按推荐自动选定 / 不用再确认 / 权限给足直接跑 / 不要中途确认」时：
- 自动按评分取 TOP 事件（日报 4–6 / 周报 **TOP1深聊（总分≥20）+ 2-3条快讯（总分≥15）** / 月报 4 趋势）
- **跳过** Step 1.3 人工确认与 Phase 2 脚本人工审核**展示等待**
- **仍须内部执行审核清单**（禁止词/黑名单/灰渠道/锚点 eligible/3W），结果写入 `news-pipeline/{date}/scripts/review-checklist.md`（或 script 文末自检表），**禁止**只口头说「结构合格」而不落盘
- 仍须：去重、灰渠道配额、Step 1.6 锚点选题、写 usage-log、平台一律存草稿

**Step 1.3b（v3.4.0 强制）**: 灰色渠道配额 + 传闻跟踪 + 上游字段 + **平台选题档（v3.13）**

1. **消费上游字段**：若报告条目含 `可信度：` / `技术锚点：` / `影响：`，在候选列表中一并展示，排序说明可引用。  
2. **灰色渠道配额**：命中封号/KYC/土尼菲区/反代/号池/白嫖/薅羊毛/接码/代充等 → 本期独立成段 **≤1 条**；措辞改「风控/账号资产风险」，**禁止**教绕法（见 `templates/credibility-and-tone.md`）。  
3. **传闻跟踪**：同一未确认事件前 3 天已报且无新事实 → 不单独成段或改一句状态更新。  
4. **🔴 平台选题 A/B 档（v3.13.0）**：按 `templates/platform-compliance.md` 划分。  
   - **A 档**（默认可上视频号/公众号）：产品发布、官方定价、开发者工具、开源项目、可复现实测  
   - **B 档**（默认**不上**公众号/视频号标题与主推段落）：融资/IPO/外泄/监管/政策联署/「切断」类对抗叙事  
   - 视频成片若保留 B 档：整期 ≤1 条，且标题禁止 B 档关键词；公众号图文默认删除全部 B 档  

**Step 1.4**: 🔴 重要程度排序（🔴 标准模式强制展示；精简模式必做）

对去重后的新鲜事件按以下维度打分（1-5 分），展示排序结果：

| 维度 | 权重 | 评分标准 |
|------|------|---------|
| 影响范围 | 高 | 5=全行业变革，1=单一公司内部 |
| 新鲜度 | 高 | 5=全球首发，1=已有报道的后续 |
| 实用性 | 中 | 5=直接影响用户/开发者，1=纯概念 |
| 话题性 | 中 | 5=引爆社交讨论，1=小众圈层 |
| 争议性 | 低 | 5=多方激烈争论，1=无争议 |

向用户展示排序结果：
```
📊 重要程度排序（总分满分 25）：

 1. [事件A] — 23分（影响5 新鲜5 实用5 话题5 争议3）
 2. [事件B] — 20分（影响5 新鲜4 实用4 话题4 争议3）
 3. [事件C] — 18分（影响4 新鲜4 实用3 话题4 争议3）
 4. [事件D] — 15分（影响3 新鲜3 实用3 话题3 争议3）
 5. [事件E] — 12分（影响3 新鲜2 实用2 话题3 争议2）

建议精选前 3-5 条制作视频。
```

用户确认选择后，**不要直接进入 Phase 2**——先执行 **Step 1.6 专业锚点选题**。

**Step 1.5（仅 `REPORT_MODE=monthly`）**: 月报选材流程

1. 解析 `data/monthly/{YYYY-MM}.md`：
   - 本月概览（覆盖天数 / 主题总数 / 最活跃日 / 日均 / 亮点文件数）
   - 4 条月度技术趋势（热度变化 / 关键驱动 / 代表主题 triple-bullet）
   - TOP10 主题（带浏览量）
   - 下月展望（4 条预测）

2. 对比上期月报 `data/monthly/{上一个月}.md`：4 条趋势是否与上月高度重叠（如 OpenAI 调度混乱连续两月）。重叠趋势标记「延续」，脚本中合并表述。

3. 按"月报选材规则"选材：4 趋势全纳入骨架；每趋势配 1-2 代表主题（过滤公益站/套利类）；输出 4-8 个支撑点。

4. 向用户展示选材结果并确认：

```
📊 月报选材（2026-06，覆盖 28/30 天）

🟢 趋势一：GPT-5.5/5.6 调度混乱与 Codex 额度震荡
   - 案例1: TOP10 #6 GPT-5.6 传闻（6.3k 浏览）✅保留
   - 案例2: 6/10 全月峰值 1698 主题 ✅保留

🟢 趋势二：国产模型集中爆发，GLM-5.2 贴脸输出
   - 案例1: TOP10 #5 AxonHub 1.0 开源（7.5k）✅
   - 案例2: 6/17 GLM-5.2 正式发布并开源 ✅

🔴 已过滤：TOP10 #2 墨西哥18刀（套利账号）、#10 Codex渠道促销（倒卖）

📐 脚本结构：1 Hook + 4 趋势段 + 1 总结 + 1 展望 + 1 CTA = 8-9 段
⏱️ 预计时长：约 200s
```

用户确认后，**先执行 Step 1.6**，再进入 Phase 2。

**Step 1.6（全模式强制，v3.4.0）**: 专业锚点自动选题

> 完整算法、降级、展示模板见 **`templates/professional-anchor.md`**。以下为必须执行的摘要。

1. **读库**：`ai-concept-bank/concepts.json`。仅 **eligible**：`status=ready` 且台词非空 且 `script_meta.authored_by=ai-concept-narrator` 且 `script_meta.reviewed=true`。库不存在则提示 `git submodule update --init`，本期可跳过。  
2. **匹配**：用用户已确认的事件/趋势标题+摘要，匹配各概念的 `news_keywords` / `aliases` / `name`。  
3. **冷却**：`last_used` 距今 < `reuse_gap_days`（默认 14）且同角度 → 不进默认推荐（可展示在「冷却跳过」）。  
4. **排序**：命中本期 +100；tier1 +40；从未用 +20；较久未用 +10；低 use_count +5。取 top 3。  
5. **时长**：daily → 15s（用 `script_15s`）；weekly/monthly → 30–60s（优先 `script_60s`，否则 15s 兜底并标注）。  
6. **向用户展示候选并确认**，写入会话变量：`ANCHOR_CONCEPT_ID` / `ANCHOR_ANGLE` / `ANCHOR_DURATION_SEC` / `ANCHOR_SKIP`。  

无强命中时走 P3：tier1 中 `last_used` 最旧或 null 的 **eligible** 概念。  
用户可选：用推荐 / 选编号 / 指定 id / **本期不要锚点**。

确认后进入 Phase 2。

### Phase 2: 视频脚本生成

对每个选中事件，按模板生成脚本。

**风格要求**:
- **🔴 说人话！** 像跟朋友聊天，不要播音腔；结论冷静
- 像 B站 AI 科技 UP 主
- 快节奏；**情绪词黑名单**见 `templates/credibility-and-tone.md`（炸了/大瓜/闹鬼/白嫖…）
- 总时长按 `REPORT_MODE`：daily 75-135s（≤160 含锚点）/ weekly 100-150s / **monthly 200-280s（≤320 含锚点）**
- 每段字数：daily/weekly ≤80 字 / **monthly ≤100 字**
- **🔴 默认 3W + 可信度**（全模式；精简仅更短更少条）
- **🔴 灰色渠道 ≤1 条**，改写为风控/资产风险
- **🔴 每期 1 个专业锚点**（除非 `ANCHOR_SKIP`）：仅 **eligible** 台词，见 `templates/professional-anchor.md`
- **🔴 画面/口播不展示数据来源**（v3.17.0）：视频正文、Hook、结尾 CTA **禁止**出现「数据来自 linux.do 社区精选」「来源于 linux.do」「新闻来自社区」等字样；来源仅供内部报告参考，不写进口播与字幕

**输出结构（默认 3W）**:
```
标题：{事件+影响，禁情绪词}
Hook：{5s 钩子，15-25 字，必须套 4 主力公式之一（社交共鸣/反转认知/否定警告/数据背书）；禁总结型（一句话堆≥2事件）；禁套话后缀（今天AI圈…动了/本期周刊把…一次讲清）；超 25 字砍数字，不足 15 字补冲突词；下一句落到事实}
对应封面大字：____（=Hook 前 12 字原词，强制封面大字核心名词与 0-2s 口播原词对齐，禁换同义词；封面主文案 14-18 字=Hook 前半句，副文案数字 4-8 字=Hook 里的数字原词）

## 选材排序（5维 1/3/5 三档，满分 25；标准模式强制展示，精简模式必做）
| 排名 | 事件 | 影响范围 | 新鲜度 | 实用性 | 话题性 | 争议性 | 总分 |
|------|------|---------|--------|--------|--------|--------|------|
阈值：≥18 进 Top3-5 单独 3W；<15 不单独成段，并入强事件一句 So What

正文（每条）：
What：{一句可验证事实}
So What：{影响}
Now What：{可执行建议，含操作动词（换/挪/配/备/查/避/开/砍/留兜底）；🔴 禁纯观察——"关注/留意/看/等/观望"单独出现且无操作动词=不通过；灰渠道须给"走官方渠道+X"而非只"走官方渠道"}
可信度：{五档之一}

{专业锚点场景 - 🔴 位置=总时长×0.7~0.8，直击中段尿点；命中概念在 55% 前出现的新闻后补桥句"这个词待会儿专门讲清"，再在 70-80% 集中解释；锚点 scene 起始秒/总秒须∈[0.7,0.8]，偏离>5% 须重排}

结尾：{CTA}
```
> 🔴 **4 主力钩子公式**（源 `social_media/爆款开头钩子.md`，Hook 必须套其一）：1.社交共鸣型"你身边有没有这样的人" 2.反转认知型"今天被上了一课" 3.否定警告型"千万不要" 4.数据背书型"99%的人都不知道"

细则：`templates/script-template.md`、`templates/credibility-and-tone.md`；周报见 `templates/script-template-weekly.md`

**🔴 专业锚点场景（v3.4.0，`ANCHOR_SKIP=false` 时强制）**：

1. 读取 `id == ANCHOR_CONCEPT_ID` 条目，必须 **eligible**：`ready` + 台词非空 + `authored_by=ai-concept-narrator` + `reviewed=true`。  
2. 口播正文 **原样使用** `script_15s`（或周/月的 `script_60s`）；**禁止**主会话手写/改写整段专业定义；**禁止**非 narrator 来源台词。  
3. 允许在锚点前加 ≤15 字过渡（如「刚才提到 MoE——」），不改动库内定义句。  
4. 锚点 = **独立 scene**（独立 TTS + 图），计入场景列表与 Phase 7/8 校验。  
5. 插入位置：命中该概念的新闻/趋势之后；无命中则 CTA 前（月报则在月度总结前）。  
6. 🔴 **位置硬约束（v3.21.0）**：锚点 scene 起始秒 / 总秒须 ∈ [0.7, 0.8]（直击诊断4 中段尿点，完播率 4.35%→6-8%）。命中概念在 55% 前出现的新闻后补 ≤15 字桥句"这个词待会儿专门讲清"，再在 70-80% 集中解释；偏离 >5% 须重排 scene 顺序（08-24 锚点 57% 即违反）。见 `templates/professional-anchor.md`。

若未 eligible 且用户仍要该概念：调 **`ai-concept-narrator`**（`ai-concept-bank/prompts/script-15s-request.md`）→ `reviewed=true` → `ready` → 再进脚本。见 concept-bank README。

**🔴 重要：保存每个场景的 TTS 文本**，Phase 7 字幕生成需要直接使用这些文本（不用 ASR 识别）。

**🔴 A/B 双 Hook 输出（v3.21.0，解"无公式轮换对照"）**：
每期 Phase 2 同时输出 **2 个 Hook 候选**（从 4 主力公式挑 2 个不同类型），标记 `[HookA:公式]` `[HookB:公式]`，随机选 1 发布。写入 `news-pipeline/{date}/hook-ab-log.md` 记录：`hook_a` / `hook_b` / `published` / `5s_completion` / `plays`（48h 回填）。2-3 周覆盖一轮 4 公式，筛选最适合本账号的公式。

**🔴 月报模式脚本模板**（仅当 `REPORT_MODE=monthly` 时生效，参考 `templates/script-template-monthly.md`）：

结构：1 Hook + 4 趋势段 + 1 月度总结 + 1 下月展望 + 1 CTA（共 8-9 段）

```
标题：{核心标题，如"2026年6月AI圈：GPT调度乱象与GLM开源逆袭"}
Hook：{一句话点出本月最大风向，如"这个6月，AI圈被GPT调度和GLM开源两件事刷屏了"}

正文：
{趋势一段} - {趋势名 + 热度变化时间线 + 1-2个代表案例，约100字}
{趋势二段} - {同上}
{趋势三段} - {同上}
{趋势四段} - {同上}
{月度总结段} - {TOP10归类 + 主题分布一句话，约60字}
{下月展望段} - {从下月展望选2-3条预测，约60字}

结尾：{CTA：关注羊报AI月报，每月带你回顾AI圈整月风向}
```

**月报脚本示例**（基于 2026-06 月报）：

```
标题：2026年6月AI圈：GPT调度乱象与GLM开源逆袭
Hook：这个6月，AI圈被两件事反复刷屏——OpenAI的GPT调度与额度反复震荡，和智谱GLM新版本的开源贴脸输出。

趋势一：GPT调度混乱与Codex额度震荡
六月三号起OpenAI大规模二验风暴，奥特曼连夜取消短信二验、新增passkey。中下旬降智争议持续，月末Codex灰度最新版并连续重置额度，全月话题峰值出现在六月十号。

趋势二：国产模型集中爆发，GLM贴脸输出
...
```

**月报脚本特殊要求**：
- 每段趋势必须含「时间线（什么时候）+ 驱动（为什么）+ 代表案例（具体帖）」三要素
- 月度总结段引用 TOP10 归类（如"OpenAI生态占TOP10五席"）
- 下月展望段只选 2-3 条最可能成真的预测
- **数字中文化**（见 B站简介数字中文化章节，月报脚本与简介均强制中文化，禁止阿拉伯数字连续出现）

**🔴 精简模式脚本模板**（CONDENSED=true：更短 3W，结构与默认相同）：

每条 3W + 可信度，每段 1-2 句，条内约 10-20s：

```
标题：{标题}
Hook：{核心事件，一句话抓住注意力，15-25 字，套 4 主力公式之一（社交共鸣/反转认知/否定警告/数据背书）；禁总结型堆≥2事件}

What（发生了什么）：{关键事实，2-3句}
So What（影响啥）：{对行业/用户的影响，1-2句}
Now What（值不值得跟进）：{结论/建议，1句，含操作动词，禁纯观察}
可信度：{五档之一}
```

**精简模式脚本示例**：
```
标题：Codex 后台写日志把 SSD 写报废
Hook：[否定警告] OpenAI 的 Codex 最近干了件离谱的事，千万别让它无人值守跑过夜
对应封面大字：Codex 把 SSD 写报废

What（发生了什么）：Codex 在后台疯狂写操作日志，连续运行几小时后，用户的 SSD 直接被写满报废。日志文件膨胀到几十 GB，完全失控。

So What（影响啥）：这暴露了 AI Agent 在自主执行任务时缺少资源监控的问题。如果在生产环境跑，可能直接把服务器搞挂。

Now What（值不值得跟进）：值得关注，这是 AI Agent 资源管理的典型案例，后续 OpenAI 大概率会加限制。
```

**精简模式要求**：
- 每段严格控制在 1-2 句，不超过 40 字
- 🔴 Hook 必须一句话抓住核心冲突，15-25 字，套 4 主力公式之一（社交共鸣/反转认知/否定警告/数据背书）；禁总结型堆≥2事件；禁套话后缀。上方示例"Hook：OpenAI 的 Codex 最近干了件离谱的事"为**反转认知正面样板**（TOP2，方案最核心公式）。4 公式各 1 条样板（无重复）：
  - **社交共鸣型**「你身边有没有跑长任务被掐断的」
  - **反转认知型**「OpenAI 的 Codex 最近干了件离谱的事」（上方示例，保留）
  - **否定警告型**「千万别让 Codex 无人值守跑过夜」
  - **数据背书型**「99%的人没注意 Codex 在偷写日志」
- What 要客观、So What 要有洞察、Now What 要有结论
- 🔴 Now What 禁纯观察——"关注/留意/看/等/观望"单独出现且无操作动词=不通过
- 整体风格仍然要"说人话"，不要播音腔
- 结尾 CTA 可省略（精简模式追求节奏紧凑）

**精简模式可与破格模式叠加**：当同时启用时，Hook 用破格类型标记，正文仍用 3W 结构：
```
标题：{标题}
Hook：[破格类型] {一句话抓住核心冲突}

What（发生了什么）：{关键事实}
So What（影响啥）：{影响}
Now What（值不值得跟进）：{建议}
```

**🔴 破格模式附加要求**（仅当 STYLE_MODE=poge 时生效）：

在脚本中为每个场景标注破格类型：

```
标题：{标题}
Hook：[破格类型] {开场，用破格制造意外感}

正文：
[身份破格] {段落1 - 引入事件}
{段落2 - 核心信息，正常叙述}
[语言破格] {段落3 - 争议/反转}
{段落4 - 延伸}

结尾：{CTA}
```

破格标记规范：
- 用方括号标注：`[身份破格]`、`[场景破格]`、`[道具破格]`、`[语言破格]`、`[对象破格]`、`[角色破格]`
- 标记放在段落开头
- 同一视频至少使用 3 种不同破格类型
- 参考模板：`templates/script-template.md`（破格模式模板）

**🔴 禁止使用的词汇**：
- 社区名：「佬友」→「大家」；「Linuxdo」「L站」→「社区」「论坛」
- **情绪黑名单**（见 `templates/credibility-and-tone.md`）：炸了/炸裂/大瓜/吃瓜/闹鬼/背刺/赢麻/白嫖/薅羊毛/彻底炸锅… → 专业替换词

**🔴 脚本审核检查清单**：展示脚本给用户前，必须逐句检查：
1. 禁止词汇 + 情绪黑名单是否清零  
2. 破格标记（非破格写 N/A）  
3. 口语化、非播音腔  
4. **每条是否有 What / So What / Now What / 可信度**  
5. **灰色渠道是否 ≤1 且无操作指南**  
6. **专业锚点**：仅 1 个（或 SKIP）且 **eligible**（ready+narrator+reviewed）  
7. **平台合规审查**（见下方 + **`templates/platform-compliance.md`**，必须落盘）  
8. **🔴 Hook 4 项（v3.21.0，缺一项不可发布）**：
   - `☐ Hook 15-25 字`
   - `☐ 套 4 主力公式之一（标明：社交共鸣A / 反转认知B / 否定警告C / 数据背书D）`
   - `☐ 禁≥2事件堆叠（周报禁≥2事件）`
   - `☐ 禁"一次讲清/今天AI圈…动了"套话后缀`
   - `☐ 已填"对应封面大字"字段并与 Hook 原词对齐`
9. **🔴 锚点位置（v3.21.0）**：`☐ 锚点位置=总时长 70-80% 处`（计算：锚点 scene 起始秒/总秒，偏离>5% 须重排）——08-24 锚点 57% 即此项不通过
10. **🔴 Now What 质量（v3.21.0）**：`☐ Now What 非纯观察`——扫每条 Now What，"关注/留意/看/等/观望"单独出现且无操作动词=不通过——08-26 Scene7/Scene5 即此项不通过
11. **🔴 选材排序表（v3.21.0）**：`☐ 选材排序表已展示`（5 维 1/3/5 三档，总分满分 25，≥18 进 Top3-5，<15 不单独成段）——08-24/08-26 无排序表即此项不通过
12. **🔴 周报结构（v3.21.0，仅 weekly 模式）**：`☐ 周报=本周1件大事3W深聊50s+2-3条一句话快讯，非5-6条堆叠各3W浅聊；深聊 What 层讲时间线（周一到周五演变，日报做不到的差异点）`——W33 5条堆叠即此项不通过

### 🔴 平台合规审查规则（v2.8.0 + **v3.13.0 强化**）

**完整细则（选题 A/B 档、封面铁律、公众号/视频号专项、落盘清单）**：  
→ **`templates/platform-compliance.md`**（Phase 1 选材 + Phase 2 脚本/标题/封面 + Phase 10 发布文案强制对照）

**依据文件**（skill 根目录）：

| 文件 | 平台 |
|------|------|
| `bilibili社区公约.md` | B站 |
| `抖音社区自律公约.md` | 抖音 |
| `微信公众平台运营规范.md` | 公众号 |
| `微信视频号运营规范.md` | 视频号 |
| **`微信视频号常见的不合规频道内容概述.md`** | **视频号限流/违规类型细目** |
| **`微信公众号互联网用户公众账号信息服务管理规定.md`** | **公众号删文常见法规依据** |

#### 禁止内容（所有平台通用）

| 类别 | 具体规则 | 示例 |
|------|---------|------|
| 🚫 政治敏感 | 不得危害国家安全、泄露国家秘密、颠覆国家政权 | 不评论政治事件 |
| 🚫 虚假信息 | 不得散播虚假、谣言等不实、误导性信息 | 新闻必须有来源依据；媒体内容禁止标题写成定论 |
| 🚫 暴力恐怖 | 不得展示血腥、惊悚、残忍等致人身心不适的内容 | 不描述暴力细节 |
| 🚫 低俗内容 | 不得含有性暗示、性挑逗等易使人产生性联想的内容 | 不使用低俗用语 |
| 🚫 侵权内容 | 不得侵犯他人名誉权、肖像权、隐私权、著作权等 | 引用需注明出处；**慎用 AI 写实真人主播封面** |
| 🚫 未成年人 | 不得发布有损未成年人身心健康的内容 | 不涉及未成年话题 |

#### 标题规范（所有平台通用）

| 规则 | 说明 | 违规示例 |
|------|------|---------|
| 🚫 标题党 | 标题必须与内容相符，不得使用夸张、惊悚、极端内容 | 「震惊！」「不看后悔！」 |
| 🚫 误导性 | 不得使用侮辱、脏话词汇，引人不适 | 不使用攻击性语言 |
| 🚫 文不对题 | 不得使用与实际内容不符的夸张、诱惑性词汇 | 标题与视频内容不匹配 |
| 🚫 敏感捆绑 | 勿把融资/政策/外泄与产品发布绑成「同日升温/博弈」标题 | 「…融资同日升温」「开源还要被切断吗」 |

#### 内容规范（各平台特殊要求）

**B站特别规则**：
- 🚫 不得使用轮播文字、大字覆盖、简单拼凑内容（低质内容）
- 🚫 不得发布画质模糊、内容不完整、音画不相关的内容
- 🚫 封面、标题突出展示违规内容将从严处置
- ✅ AI生成内容需符合社区规范

**视频号特别规则**（对照 `微信视频号常见的不合规频道内容概述.md` + 运营规范）：
- 🔴 **AI生成内容必须显著标识**：生成/合成非真实音视频须显著标识
- 🔴 **封面禁止写实 AI 主播/假新闻脸**（易触肖像/虚假类；v3.13 封面 prompt 禁用 news anchor 人像）
- 🚫 融资内幕、政策对抗、「切断/外泄」等话术默认不进短标题/描述（B 档，见 platform-compliance）
- 🚫 不得使用夸张标题，内容与标题严重不符
- 🚫 不得发布批量同质化、低质量内容
- 🚫 视频配音与画面不相关
- **2026-07-26 实测**：可出现「限制传播 + 存在敏感或者违规内容」且**不给细码** → 按封面 + 政策/融资话术优先整改

**抖音特别规则**：
- 🚫 不得借助社会负面事件、敏感事件进行商业营销宣传
- 🚫 不得发布哗众取宠、恶意审丑等博眼球内容
- 🚫 不得发布画质模糊、无完整内容、观感体验差的视频
- ✅ 鼓励原创、优质内容，建议真人出镜或讲解

**公众号特别规则**（对照 `微信公众号互联网用户公众账号信息服务管理规定.md` + 运营规范）：
- 🔴 **无互联网新闻信息服务许可时**：避免「每日要闻/采编通稿」体；账号定位用「产品与开发者观察笔记」
- 🔴 **B 档默认不上公众号**：融资/IPO/外泄/监管/政策联署/开源对抗叙事（见 platform-compliance 选题两档）
- 🚫 标题禁止把「据媒体报道」写成已官宣定论（对应规定第十八条虚假信息等风险）
- 🚫 不得发送垃圾信息并存在过度营销行为
- 🚫 不得发布与账号功能介绍不符的内容
- ✅ 提供具有价值的、持续性的并与该账号高度相关的内容
- **2026-07-26 实测**：可「接投诉 + 违反《互联网用户公众账号信息服务管理规定》+ 已删除」且**不写条款号** → 优先按第五条/第十八条（三）（六）整改选题与包装

#### AI News Video 合规检查清单

在生成脚本时，必须逐项检查（**完整勾选表见 `templates/platform-compliance.md` §5，须写入 review-checklist.md**）：

```
✅ 合规检查清单：
☐ 选题 A/B 档：公众号/视频号未强推融资·政策·外泄·监管类
☐ 新闻/产品信息是否有可靠来源？媒体内容是否标「据报道/未独立核实」？
☐ 标题是否与视频内容相符？是否避免「同日升温/切断/外泄/博弈/风暴」？
☐ 是否包含暴力、恐怖、低俗内容？（如有则删除或改写）
☐ 是否涉及政治敏感 / 舆论对抗叙事？（回避或降级，勿上标题）
☐ 是否侵犯他人权益？（引用注明出处；封面无写实假主播）
☐ 是否涉及未成年人？（如有则删除）
☐ 视频号：AI 生成标识将开启；封面无真人感主播
☐ 公众号：非新闻采编口吻；B 档已删或未进标题
☐ 描述/简介是否与视频内容一致？（避免误导）
☐ 是否有过度营销 / 强诱导内容？（避免广告与诱导刷量嫌疑）
☐ 整体内容符合平台生态要求（基本要求）

🔴 v3.21.0 新增 5 项必勾（数据驱动，缺一项不可发布，须写入 review-checklist.md）：
☐ Hook 15-25 字
☐ Hook 套 4 主力公式之一（标明：社交共鸣A / 反转认知B / 否定警告C / 数据背书D）
☐ Hook 禁≥2事件堆叠（周报禁≥2事件）
☐ Hook 禁"一次讲清/今天AI圈…动了"套话后缀
☐ Hook 已填"对应封面大字"字段并与原词对齐
☐ 锚点位置=总时长 70-80% 处（锚点 scene 起始秒/总秒，偏离>5% 须重排）
☐ Now What 非纯观察（"关注/留意/看/等/观望"单独出现且无操作动词=不通过）
☐ 选材排序表已展示（5维 1/3/5 三档，满分 25，≥18 进 Top3-5，<15 不单独成段）
☐ [周报] 本周1件大事3W深聊50s+2-3条一句话快讯，非5-6条堆叠；深聊 What 讲时间线
```

#### 违规后果

| 平台 | 处罚措施 |
|------|---------|
| B站 | 删除下线、限制传播、添加提醒标识、封禁账号 |
| 视频号 | 减少推荐、限制传播、删除内容、暂停/终止服务、封禁账号 |
| 抖音 | 删除/屏蔽内容、暂停/终止账号功能、封禁账号 |
| 公众号 | 删除内容、限制功能、封禁账号 |

**Why:** 四个平台都有严格公约/法规；2026-07-26 视频号限流 + 公众号删文；**同日周报**抖音「不适宜公开/仅自己可见（画面）」证明：内部审核清单通过 ≠ 平台过审，且 **画面与标题攻击词** 是独立维度  
**How to apply:** Phase 1 划分 A/B 档 → Phase 2–5 按 `platform-compliance.md`（含 §8 禁词 + 画面铁律）写脚本/标题/分镜/场景图 → 审核清单落盘 → 再进入渲染/上传

**🔴 用户审核步骤**：脚本生成后，必须将完整脚本展示给用户审核，获得确认后才能进入 Phase 3。用户可能要求修改某些场景的文案。

**🔴 用户确认脚本后、进入 Phase 3 前：写入专业锚点 usage-log（v3.4.0 强制）**

若 `ANCHOR_SKIP=true`，跳过。否则必须：

1. **Append** `ai-concept-bank/usage-log.json` 一条记录（字段见 `templates/professional-anchor.md`）：`date`, `concept_id`, `angle`, `mode`（daily/weekly/monthly）, `duration_sec`, `news_trigger`, `report_path`, `script_path`, `notes`。  
2. **更新** `ai-concept-bank/concepts.json` 对应概念：`last_used=date`，`use_count+=1`，`angles.used` 含本次 angle。  
3. **不要**静默 git commit 子模块；可提示用户稍后 bump submodule。  
4. 审核清单应能勾选：「已写 usage-log」。

**参考模板**: `templates/script-template.md`；`templates/credibility-and-tone.md`；专业锚点：`templates/professional-anchor.md`

### Phase 3: 分镜生成

根据视频脚本生成分镜表，每个脚本段落对应 1 个分镜。

| 镜号 | 时长 | 镜头类型 | 画面内容 | 字幕重点 | 转场 |
|------|------|----------|----------|----------|------|
| 1 | 3s | 特写 | AI 芯片电路 | Hook 文字 | 淡入 |
| 2 | 5s | 全景 | 科技新闻编辑室 | 事件标题 | 切换 |

**参考模板**: `templates/storyboard-template.md`

**🔴 画面合规（v3.14.0 · 抖音「画面」违规教训）**

分镜「画面内容」列禁止作为主视觉：

| 禁止 | 改为 |
|------|------|
| 隔离舱破裂 / cracked glass / security breach | 明亮机房 + 权限清单 / 监控仪表盘（绿灯） |
| 撬锁、入侵、黑客攻击特写 | 工程师审访问控制、配置 UI |
| 立法楼剪影、两党、法槌特写 | 会议室讨论订阅/合规文档（无法槌主视觉） |
| 红警报、武器、血腥 | 蓝青专业光、产品 UI |

安全事件口播已产品化时，**画面必须同步产品化**，否则只改标题仍会「限制自己可见 / 画面」。

**🔴 破格模式分镜**（仅当 STYLE_MODE=poge 时生效）：

在标准分镜基础上增加「破格镜头」列：

| 破格类型 | 镜头技巧 | Prompt关键词 |
|---------|---------|-------------|
| 身份破格 | 身份与环境对比构图 | unexpected role, contrast, juxtaposition |
| 场景破格 | 倾斜构图（Dutch angle） | dutch angle, tilted, surreal setting |
| 道具破格 | 道具特写+反差背景 | unconventional object close-up, repurposed |
| 语言破格 | （不影响镜头，影响TTS） | — |
| 对象破格 | 荒诞目标特写 | absurd target, unexpected audience |
| 角色破格 | 角色互换对比 | role reversal, character twist, split composition |

### Phase 4: 图片 Prompt 生成

使用填空即用模板为每个分镜生成图片 Prompt，输出到 `news-pipeline/YYYY-MM-DD/prompts/image-prompts-YYYY-MM-DD.json`。

**视频品牌**: 「今日羊报 AI」
**副标题**: 「AI 新闻」

#### 填空即用模板

```
Create a realistic editorial news image about:

{新闻内容}

The image should show:
- clear main subject
- real-world environment
- strong relation to the news event
- cinematic but realistic lighting
- professional news photography style
- modern AI technology atmosphere

Avoid:
- abstract AI concepts
- floating holograms
- random sci-fi elements
- text in image
- logos
- low-detail compositions

[新闻核心地点] with [主要人物/物体], [他们在做的关键动作]. [标志性环境细节], [时间/天气/光线]. [情绪与氛围描述]. [新闻摄影/编辑插图风格], photorealistic, highly detailed, shot on [镜头焦段] — no text, no watermark.

16:9 aspect ratio
「今日羊报 AI」
「AI 新闻」
分两行显示在右上角,充当背景
```

#### 输出格式

```json
[
  {
    "scene": 1,
    "news": "新闻标题",
    "prompt": "填充后的完整 Prompt"
  }
]
```

**🔴 图片-脚本映射铁律（v2.8.0 新增）**：

图片 prompt JSON 中的 `scene` 编号必须与脚本场景编号严格 1:1 对应！

常见错误：
- ❌ Hook 场景（scene1）单独生成一张图片，第一条新闻（scene2）又生成一张详细图 → 导致后续所有图片偏移 +1
- ❌ 图片按"新闻事件"编号而非"脚本场景"编号

正确做法：
- ✅ Hook 和第一条新闻合并为同一场景时，只生成 1 张图片（scene1）
- ✅ 图片 prompt JSON 数组长度 = 脚本场景数（如6个脚本场景 = 6张图片）
- ✅ `image-prompts.json` 中 scene 1-N 与 `voiceover-texts.json` 中 scene 1-N 一一对应
- ✅ Phase 8 校验时必须确认：`len(imagePrompts) == len(scriptScenes)`

**🔴 破格模式 Prompt 变体**（仅当 STYLE_MODE=poge 时生效）：

在标准 prompt 末尾追加反差视觉描述：

```
[标准 prompt] + The image conveys a sense of [破格类型]:
- [反差视觉元素1]
- [反差视觉元素2]
- unexpected contrast between [A] and [B]
```

破格类型→视觉关键词映射：

| 破格类型 | 视觉关键词 |
|---------|-----------|
| 身份破格 | unexpected role, identity contrast, juxtaposition of status |
| 场景破格 | surreal setting, environment mismatch, unexpected location |
| 道具破格 | repurposed object, unconventional tool, creative misuse |
| 语言破格 | (不影响图片) |
| 对象破格 | absurd audience, unexpected target, comical mismatch |
| 角色破格 | role reversal, character twist, reversed hierarchy |

参考模板：`templates/image-prompt-template.md`（破格模式 Prompt 变体）

### Phase 5: 图片生成

**主方案**: 使用 Python+curl 直接调用图片生成 API。

```python
import json, subprocess, base64, tempfile, os, time

API_URL = "用户提供的 API URL"  # 如 https://ai.prism.uno
API_KEY = "用户提供的 API Key"
MODEL = "gpt-image-2"  # 注意：不是 gpt-image-1

def generate_image(prompt, output_path):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run([
            "curl", "-s", "-X", "POST", f"{API_URL}/v1/images/generations",
            "-H", f"Authorization: Bearer {API_KEY}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"model": MODEL, "prompt": prompt, "size": "1536x1024", "n": 1}),
            "-o", tmp_path,
            "--max-time", "120"
        ], check=True, timeout=130)
        with open(tmp_path) as f:
            resp = json.load(f)
        if "error" in resp:
            return False, resp["error"].get("message", str(resp["error"]))
        img_b64 = resp["data"][0].get("b64_json", "")
        if img_b64:
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(img_b64))
            return True, "OK"
        # Try URL download
        img_url = resp["data"][0].get("url", "")
        if img_url:
            subprocess.run(["curl", "-s", "-o", output_path, img_url], timeout=60)
            if os.path.getsize(output_path) > 1000:
                return True, "OK (from URL)"
        return False, "No image data"
    except Exception as e:
        return False, str(e)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
```

**API 源列表（按优先级排序）**：

| 优先级 | 名称 | URL | 模型 | 说明 |
|--------|------|-----|------|------|
| 1 | 用户提供 | 用户提供 | gpt-image-2 | 优先使用用户提供的 API |
| 2 | luka77 | http://api.luka77.cc | gpt-image-2 | **最稳定**（HTTP，无 SSL 问题，2026-06-21 验证） |
| 3 | openrouter | https://eo.ioll.pp.ua | gpt-image-2 | 需要 DNS 绕过（198.18.x.x 劫持） |
| 4 | jiuuij | https://jiuuij.de5.net | gpt-image-2 | 需要 DNS 绕过，响应较慢 |
| 5 | prism | https://ai.prism.uno | gpt-image-2 | 需要 VPN，SSL 握手常超时 |

**🔴 DNS 劫持检测与绕过**：

如果 API 连接超时或 SSL 错误，检查 DNS 解析是否被本地代理工具劫持到 198.18.x.x 网段：

```bash
# 检查 DNS 解析
nslookup api.luka77.cc
# 如果返回 198.18.x.x，说明被劫持

# 获取真实 IP 后用 --resolve 绕过
REAL_IP=$(nslookup api.luka77.cc 8.8.8.8 | grep -A1 "Name:" | tail -1 | tr -d ' ')
curl -s --resolve api.luka77.cc:443:$REAL_IP ...
```

**HTTP API 优先**：如果 API 支持 HTTP（如 luka77），优先使用 HTTP 避免 SSL 问题。

**API 选择逻辑**：
1. 优先使用用户提供的 API
2. 如果报错（配额不足、渠道不存在），尝试下一个
3. 如果所有 API 都不可用，提示用户提供可用的 API

**注意事项**:
- 使用 `1536x1024` (16:9 横屏)
- **必须逐张生成**：API 有并发限制；**禁止**整段 7 张串行卡在一个 10 分钟 Bash 超时里——可按 scene 拆命令或仅生成缺失文件
- **必须从 JSON 文件读取 Prompt**，不能用简化版本
- 每张图片生成后重试一次（如果失败）
- **HTTP API 优先**：HTTP（如 luka77）比 HTTPS 更稳定，避免 SSL/DNS 问题
- **超时设置**：图片生成可能需要 30-180 秒，单张 curl `--max-time` 建议 90–180；整批脚本 timeout 按张数放大
- **DNS 劫持**：如遇连接超时，用 `nslookup` + `curl --resolve` 绕过
- **🔴 settings.env 多端点（v3.10 / 2026-07-21）**：从 `~/.claude/settings.json` 的 `env` 读取 `GEN_IMG_API_URL`/`GEN_IMG_API_KEY` 及 `_001`/`_002` fallback；日志**禁止**打印 key（只允许 set/empty/len）
- **🔴 部分成功续跑**：已存在且 >5KB 的 `sceneN.png` 跳过；失败端点记 http 状态后切下一端点
- **scene CTA 兜底**：最后 1 张若全端点失败，可用昨日同结构 CTA 图或 scene1 临时顶替，**封面竖图禁止**此兜底

### Phase 5.5: 异步生成封面（与 TTS 并行）

**🔴 重要优化：封面生成耗时较长（每个约 30-60s），应与 TTS 配音并行执行！**

在 Phase 5 图片生成完成后，使用 `Agent` 工具异步生成所有封面：

```python
# 使用 Agent 工具异步执行封面生成
# 这样可以与 Phase 6 TTS 配音并行，节省总时间

# 封面生成脚本（在 agent 中执行）
import json, subprocess, base64, tempfile, os, time

API_URL = "用户提供的 API URL"  # 优先使用 eo.ioll.pp.ua
API_KEY = "用户提供的 API Key"
MODEL = "gpt-image-2"

COVER_PROMPT = """A professional Chinese AI news studio cover image. Empty modern curved news desk in a high-tech studio, NO human presenter, NO realistic human face or news anchor. Behind the desk are multiple large display screens arranged in a grid showing: {本期核心新闻相关的视觉元素，产品/抽象图形，勿放可识别真人}. The studio has dramatic blue and red neon lighting, with red accent lights along the desk edges and blue ambient lighting. In the top right corner, display the text "今日羊报 AI" on the first line and "AI 新闻" on the second line in large white Chinese characters. In the center of the image, display the date "{YYYY-MM-DD}" in very large white bold text. Professional broadcast news photography style, photorealistic environment, highly detailed, cinematic lighting, {ratio} aspect ratio. No people, no faces."""

# 封面配置
COVERS = [
    {"name": "horizontal-4-3.png", "size": "1536x1152", "ratio": "4:3"},    # B站/通用（4:3 横版）
    {"name": "vertical-3-4.png", "size": "1152x1536", "ratio": "3:4"},   # 抖音/竖版（3:4）
]

def generate_cover(prompt, output_path, size):
    """生成单张封面，带重试机制"""
    for attempt in range(2):  # 最多重试1次
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            result = subprocess.run([
                "curl", "-s", "-X", "POST", f"{API_URL}/v1/images/generations",
                "-H", f"Authorization: Bearer {API_KEY}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"model": MODEL, "prompt": prompt, "size": size, "n": 1}),
                "-o", tmp_path,
                "--max-time", "120"
            ], capture_output=True, text=True, timeout=130)

            with open(tmp_path) as f:
                resp = json.load(f)

            if "error" in resp:
                if attempt == 0:
                    time.sleep(2)
                    continue
                return False, resp["error"].get("message", str(resp["error"]))

            img_b64 = resp["data"][0].get("b64_json", "")
            if img_b64:
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                return True, "OK"

            img_url = resp["data"][0].get("url", "")
            if img_url:
                subprocess.run(["curl", "-s", "-o", output_path, img_url], timeout=60)
                if os.path.getsize(output_path) > 1000:
                    return True, "OK (from URL)"

            return False, "No image data"
        except Exception as e:
            if attempt == 0:
                time.sleep(2)
                continue
            return False, str(e)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    return False, "Max retries exceeded"
```

**执行方式**：
```bash
# 🔴 重要：不要用 Agent 工具异步生成封面！Agent 会遇到 Bash 权限问题导致失败。
# 直接在主线程中用 Python 脚本生成封面，与 TTS 串行执行即可。
# 如果时间紧张，可以先生成封面再生成 TTS，或者反过来。

# 在主流程中直接执行封面生成 Python 脚本
python3 -c "
import json, subprocess, base64, tempfile, os, time
# ... 封面生成代码 ...
"
```

**封面生成验证**：
```bash
# 生成完成后验证所有封面文件
ls -la news-pipeline/YYYY-MM-DD/*.png | wc -l
# 应该输出 2（horizontal-4-3.png【4:3 横版，B站/通用】, vertical-3-4.png【3:4 竖版，抖音/视频号/公众号】）
```

**优势**：
- 封面生成（2个，约 1-2 分钟）与 TTS 配音（9个，约 2-3 分钟）并行
- 总时间从串行的 6-8 分钟缩短到并行的 3-5 分钟
- 每张封面自动重试一次，提高成功率

### Phase 5.6: 本地生图兜底（v3.19.0 新增，API 全挂 / 文字渲染不达标时）

**与 edge-tts 兜底 mimo-tts 同构**：当 GEN_IMG 多端点全部失败、或 API 出图但中文文字糊掉时，用 Pillow 本地生成 scene 图和封面，保证流水线不中断。

#### 触发条件（满足任一即切本地）

**Scene 图本地化（`gen_images_local.py`）**：
1. API 所有端点 401 / 余额耗尽 / SSL 握手超时 / `net::ERR_*` 全挂
2. 上一期遗留的 scene 图与本期脚本内容不匹配（新闻变了，图没变，需重画）

**封面本地化（`gen_covers_local.py`）**：
1. API 余额耗尽，无法生成封面
2. **或** API 有余额但 gpt-image-2 渲染的中文日期/品牌名糊掉、错字、变形——封面文字必须像素级准确，API 不可靠时直接本地叠加

#### 本地生图原理

**Scene 图**：用 Pillow 画 8 张主题化抽象背景（1920×1080），深色演播室 + 场景专属配色 + 几何 motif（数据流、发光球、上下文进度条、GPU 卡堆叠、领奖台等）。每张 `draw_sceneN()` 对应一期脚本的一个场景。

**封面**：拿已生成的 `scene1.png` 作底图，裁剪到目标比例，叠加：
- 底部 + 右上角深色渐变蒙版（保证文字可读性）
- 中央大字日期（`Arial Unicode.ttf`，带阴影）
- 右上角品牌块（`今日羊报 AI` / `AI 新闻`，`STHeiti Medium.ttc`）

#### 脚本模板

**封面本地生成 `gen_covers_local.py`**（关键变量）：

```python
#!/usr/bin/env python3
"""Generate covers from scene1.png with text overlay (API balance exhausted)."""
from PIL import Image, ImageDraw, ImageFont
import os

BASE = "news-pipeline/YYYY-MM-DD"          # 当期输出目录
SRC = os.path.join(BASE, "images/scene1.png")  # 底图（优先用 API 出的 scene1）
FONT_BOLD = "/System/Library/Fonts/STHeiti Medium.ttc"   # 品牌名中文字体
FONT_ARIAL = "/Library/Fonts/Arial Unicode.ttf"          # 日期数字字体
DATE = "YYYY-MM-DD"   # 🔴 按模式参数映射表读取，勿硬编码
BRAND = "今日羊报 AI"  # 按模式读取（日报/周报/月报不同）
SUB = "AI 新闻"

def draw_cover(out_name, target_w, target_h):
    src = Image.open(SRC).convert("RGB")
    # 裁剪到目标比例
    # 叠加深色渐变蒙版（底部 + 右上角品牌块）
    # 中央大字日期（带阴影）
    # 右上角品牌 + 副标
    canvas.save(os.path.join(BASE, out_name), "PNG", quality=95)

draw_cover("horizontal-4-3.png", 1536, 1152)  # B站/通用 4:3
draw_cover("vertical-3-4.png", 1152, 1536)    # 抖音/视频号 3:4
```

**Scene 图本地生成 `gen_images_local.py`** 结构：

```python
#!/usr/bin/env python3
"""Local scene-image generator (Pillow, no API). Replaces mismatched old images."""
import math, random
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
random.seed(20260821)   # 固定种子保证可复现

def base_gradient(top, bottom): ...      # 垂直渐变底
def radial_glow(img, cx, cy, radius, color, intensity): ...  # 径向发光
def draw_scene1(): ...   # Hook — 演播室全景 + 青色数据流
def draw_scene2(): ...   # 按当期新闻主题画（神秘模型→发光球+问号）
# ... 每个场景对应当期脚本内容
def draw_scene8(): ...   # CTA — 暖色演播室 + 订阅铃铛发光

SCENES = [draw_scene1, ..., draw_scene8]
# 输出到 news-pipeline/video-project/public/images/sceneN.png
```

#### 执行方式

```bash
# 1. Scene 图本地生成（仅当 API 全挂时）
cd /Users/youngsdream/Documents/learn-claude-code
python3 news-pipeline/YYYY-MM-DD/scripts/gen_images_local.py

# 2. 封面本地生成（API 余额耗尽或文字糊掉时）
python3 news-pipeline/YYYY-MM-DD/scripts/gen_covers_local.py
```

**🔴 注意**：
- 封面本地化优先用 **API 出的 `scene1.png` 作底图**（视觉质量更高）；若 scene 也本地化了，则用本地 scene1
- 日期/品牌名变量**必须按模式参数映射表读取**，禁止硬编码 `2026-08-21`——改日期时只改 `DATE` 一处
- 本地 scene 图是抽象几何风格，视觉质量低于 API 出图；**仅作兜底**，API 恢复后应切回 API
- 脚本依赖系统字体：`/System/Library/Fonts/STHeiti Medium.ttc`（品牌名）、`/Library/Fonts/Arial Unicode.ttf`（日期）；缺字体时换 `PingFang.ttc` / `Helvetica.ttc`
- 生成后**必须视觉校验**：`Read` 打开 PNG 确认日期/品牌文字清晰无糊无错字

#### 决策流程

```
Phase 5 scene 图生成
├─ API 任一端点出图成功 → 用 API 图（默认）
└─ 全端点失败 / 旧图不匹配 → gen_images_local.py 本地生成

Phase 5.5 封面生成
├─ API 出图且中文文字清晰 → 用 API 封面（默认）
└─ API 余额耗尽 / 文字糊掉 → gen_covers_local.py 本地叠加（优先用 API scene1 作底图）
```

### Phase 6: TTS 配音

根据视频脚本逐场景生成配音：

**🔴 重要：mimo-tts.sh 依赖 settings.json 中的 `MIMO_TTS_API_KEY` 配置。如果未配置，必须使用环境变量方式调用。**

#### 6.1 首选方案：环境变量直接调用 mimo-tts.sh（v3.2.0 新增）

**如果 settings.json 中没有 MIMO_TTS_API_KEY 配置，直接用环境变量方式调用：**

```bash
MIMO_TTS_API_URL="https://your-tts-api-url.com" MIMO_TTS_API_KEY="sk-your-tts-key" \
bash ~/Documents/learn-claude-code/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "配音文本" \
  --voice "白桦" \
  --style "新闻播报" \
  --output "news-pipeline/YYYY-MM-DD/voiceover/sceneN.wav"
```

**🔴 关键经验（v3.2.0 新增）**：
- settings.json 中可能没有 MIMO_TTS_API_KEY 配置，导致 mimo-tts.sh 报错 `MIMO_TTS_API_KEY not found`
- 环境变量方式可以绕过 settings.json 配置问题
- TTS API URL 和 Key 通常与图片 API 不同，需要单独收集
- 如果用户未提供 TTS API 信息，先检查 settings.json，再询问用户

**🔴 TTS 网关 503（v3.9.0 / 2026-07-20 实测）**：
- 响应 `gateway_error` / `没有可用的内网节点` / HTTP 503 时：**指数退避重试**（如 5s → 15s → 30s，最多 3–5 次）
- 仍失败：切换 settings.env 中的 fallback 节点（`MIMO_TTS_API_URL` 备选）
- **禁止**把空 wav / 半截 scene 当成功；每 scene 校验文件大小与时长
- 日志只记 status/body 摘要，**禁止打印 API key**

#### 6.2 备选方案：Python 直接调用 MiMo TTS API

如果 mimo-tts.sh 环境变量方式也失败，直接用 Python+curl 调用：

```python
import json, subprocess, base64, tempfile, os, time

API_URL = "https://your-tts-api-url.com/v1/chat/completions"
API_KEY = "sk-your-tts-key"
OUTPUT_DIR = "news-pipeline/YYYY-MM-DD/voiceover"

SCENES = [
    {"num": 1, "text": "场景1文本...", "style": "新闻播报"},
    # ... 每个场景
]

def generate_tts(scene):
    num = scene["num"]
    text = scene["text"]
    style = scene["style"]
    output_path = os.path.join(OUTPUT_DIR, f"scene{num}.wav")
    content = f"({style}){text}" if style else text
    body = {
        "model": "mimo-v2.5-tts",  # 预置音色用这个模型
        "messages": [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": content}
        ],
        "audio": {"format": "wav", "voice": "白桦"}  # 推荐白桦
    }
    # 用 curl 调用 API，解析 base64 音频数据
    # 详见 news-pipeline/2026-06-16 的实际实现
```

**🔴 重要**：预置音色用 `mimo-v2.5-tts` 模型 + `voice: "白桦"`。克隆音色用 `mimo-v2.5-tts-voiceclone` 模型 + base64 音频，但效果差，不推荐。

#### 6.3 兜底方案：edge-tts（v3.15.0 新增，mimo-tts 全部不可用时）

**当 mimo-tts 所有端点（含环境变量配置、settings.env 中的 _001/_002 fallback）均返回 `Gateway Error: 没有可用的内网节点` 或 HTTP 503/502 时，自动切换到 edge-tts（Microsoft Azure Neural TTS）。**

**edge-tts 优势**：
- 无 API Key 依赖，`pip install edge-tts` 即可使用
- 中文音色 `zh-CN-YunyangNeural`（男声，专业可靠，新闻风）效果接近 mimo-tts「白桦」
- 响应稳定，无配额限制

**切换条件**（满足任一即切换）：
1. mimo-tts 返回 `Gateway Error: 没有可用的内网节点`
2. mimo-tts 连续 3 次 HTTP 503/502
3. mimo-tts 所有 fallback 端点均失败

**执行步骤**：

```bash
# 安装 edge-tts
pip install edge-tts>=7.2.8

# 生成 MP3（edge-tts 原生输出 MP3）
edge-tts --text "配音文本" \
  --voice zh-CN-YunyangNeural \
  --write-media /tmp/sceneN_edge.mp3

# 转换为 WAV（24kHz PCM16LE 单声道，与 Phase 7 字幕生成兼容）
ffmpeg -y -i /tmp/sceneN_edge.mp3 -acodec pcm_s16le -ar 24000 -ac 1 \
  "news-pipeline/YYYY-MM-DD/voiceover/sceneN.wav"
```

**推荐音色**：
| 音色 | Voice ID | 说明 |
|------|----------|------|
| 云扬（推荐） | `zh-CN-YunyangNeural` | 男声，专业可靠，新闻风，最接近「白桦」 |
| 云健 | `zh-CN-YunjianNeural` | 男声，激情，适合快节奏 |
| 云希 | `zh-CN-YunxiNeural` | 男声，活泼阳光 |
| 晓伊 | `zh-CN-XiaoyiNeural` | 女声，活泼（卡通风） |

**注意**：
- edge-tts 输出为 MP3，必须用 ffmpeg 转为 WAV（24kHz）才能与 Phase 7 字幕流程兼容
- 转换后音频时长不变，无需调整 Composition.tsx 的 duration
- 重新生成 TTS 后必须同步更新：Composition.tsx sceneConfig → Root.tsx TOTAL_DURATION_SEC → 重算 captions.json → 重渲染

#### 6.3b atempo=1.4 加速（v3.18.0 / 2026-08-18 实测）

音色 `zh-CN-YunxiNeural`（云希）+ ffmpeg `atempo=1.4` 加速，可显著缩短总时长（8 场景实测 112.13s）。

**🔴 换期硬性前置（v3.24.0 / 2026-08-30 W35）**：atempo 有 SKIP 启发式——`out duration < raw*0.95` 视为已加速。`public/voiceover/scene*.wav` 若是**上期残留**（时长本身短于 raw），启发式会误判「已加速」直接保留旧音频 → 成片 0:52 后音画/字幕错位（W35 用户报 3 次）。

**换期 / 重跑 TTS 必须先清残留，再跑 atempo**：
```bash
# 优先：不可逆删除（可能被自动权限拒绝）
rm public/voiceover/scene*.wav
# 若 rm 被拒：shutil.move 到 .stale_archive/（见已知坑 138）
# python3 -c "import glob,shutil,os; os.makedirs('public/voiceover/.stale_archive',exist_ok=True); [shutil.move(f,'public/voiceover/.stale_archive/') for f in glob.glob('public/voiceover/scene*.wav')]"
```
修后必须 `ffprobe` 全部场景时长 + whisper 抽段验证才重渲染。禁止只看启发式 SKIP 就当本期音频。

```bash
# edge-tts 生成 → ffmpeg atempo=1.4 加速 → 24kHz PCM16LE 单声道 WAV
ffmpeg -y -i /tmp/sceneN_edge.mp3 -filter:a atempo=1.4 \
  -acodec pcm_s16le -ar 24000 -ac 1 sceneN.wav
```

**加速后必须重算**：
- `Composition.tsx` sceneConfig 各场景时长
- `Root.tsx` `TOTAL_DURATION_SEC`
- `captions.json` 字幕时间轴
- 然后重新渲染视频

### Phase 7: 字幕生成（语义 `group_caps` 切行 + whisper 词级对齐）

**v3.25.0 当前默认（2026-08-31 月报实测）**：先用语义 `group_caps` 切出字幕字符串，再用 faster-whisper `word_timestamps=True` + `SequenceMatcher` 把每条字幕对齐到音频真实发音时刻。内容 100% 来自脚本，时间 100% 来自音频。

> **规则全文**：`templates/captions.md`  
> **可运行脚本**：`templates/gen_captions.py`（`--report-dir` / `--dry-run` / `--extra-word`）

> **🔴 经验教训（2026-06-12）**：FunASR 对专业术语识别极差（GPT→GDP、DeepSeek→Deep triep、Claude Code→Claude coat、Fable-5→核酸efbo杠五、Codex→搞dex、Hermes→HMMI、MiMo→mini/明末），修正字典永远追不上新术语。**字幕内容必须用原始 TTS 脚本文本，绝不依赖 ASR 识别文字。**
>
> **🔴 经验教训（2026-07-15）**：纯等字符比例分配（v2.1.0）/ 加权字符估算 + silencedetect 吸附（v2.2.0）仍会漂移。**v2.3.0 放弃「估算每句时长」，改用音频真实发音时刻作锚——这一条仍有效。**
>
> **🔴 经验教训（2026-08-31）**：v2.3.0 的 `split_sentences` 把 `，。；！？：、` **所有标点一视同仁**切行，再叠加 16 字硬墙，会切出 `延期；`（3 字 0.5s 闪行）、`有效` / `主题近一万。`、`终止Cursor` / `官方直连`。**切行必须语义优先；whisper 只负责时间轴。**

#### 7.1 默认方案：语义切行 + whisper 对齐（`templates/gen_captions.py`）

> 🔴 **v3.21.0 字幕补丁（治 2s 跳出 44%）**：Hook 的 5s 文本须独立成段，字幕时间戳 0-5s，前 5s 字幕字号 +20%（`Subtitles.tsx` 已支持，基于字幕时间戳 `caption.startMs < 5000` 判断 Hook 段放大，`fontSize: enlarged ? 48 : 40`）。前 2s 视觉与口播同步兑现封面大字承诺。 Remotion 字幕 **单行**，不做双行长度平衡。

**物理下限**（先于语义；详见 `templates/captions.md`）：

| 项 | 规则 |
|----|------|
| 目标行长 | 15–20 汉字（空格不计） |
| `max_len` | 16：到此长度遇软标点才断 |
| `hard_max` | 20：允许略超 16 以保住专名/动宾/正反并列 |
| 无合法切点 | **整句保留**（可到 24–25），**禁止按字符下标硬切** |
| 最短显示 | 对齐后 `merge_short_dwell(min_sec=1.0)`，<1s 并回上一行 |
| 视觉 | Remotion `Subtitles.tsx` **单行**；不做双行长度平衡 |

**语义切点**：

| 标点 | 行为 |
|------|------|
| `。！？；`（`SENT_END`） | **强制断行** |
| `，、：`（`SOFT_PUNCT`） | 仅当当前行 ≥ `max_len` 才断 |
| 所有标点一视同仁 | **禁止**（旧 `split_sentences`，会切出 `延期；`） |

超 `hard_max`：黄金分割 40–60%（扩 30–70%）→ `WEAK_BEFORE` 弱连接 → 整句保留。

**禁切反例（2026-08 月报实测，切开即错）**：

| 类型 | 必须同一行 |
|------|-----------|
| 正反并列 | `稳不稳` |
| 偏正 | `硬新闻主轴` |
| 动宾 / 专名+动宾 | `规划步骤`、`编程 Agent`、`终止Cursor官方直连` |
| 专名连发 | `Hy四连发`、`羊报AI月报` |
| 品牌+宾语 | `整月风向` |
| 数量+名 | `主题近一万`（禁止 `有效` / `主题近一万。`） |
| 短尾巴 | `延期；` 不得单独成行 |

后处理：`GLUE_TAILS` + `BAD_ENDS`/`BAD_STARTS` + 当期 `jieba.add_word`。

**算法摘录**（完整实现 `templates/gen_captions.py`，禁止再贴 170 行硬编码 WEEKLY 路径）：

```python
SENT_END = set('。！？；')
SOFT_PUNCT = set('，、：')

def group_caps(tokens, max_len=16, min_len=6, hard_max=20):
    """语义优先切行：句末强制断；软标点在 ≥max_len 时断；
    允许略超 16 字（≤hard_max=20）以保住专名/动宾/正反并列；
    超 hard_max 才黄金分割。短尾巴并回上一行。无合法切点整句保留，绝不按字硬切。"""
    ...  # _split_overlong → 黄金分割 → WEAK_BEFORE → 整句保留
    ...  # GLUE_TAILS / min_len 并回上一行；BAD_ENDS+BAD_STARTS 二次粘合

# 时间轴：group_caps 先切 → whisper word_timestamps → SequenceMatcher 对齐
#        → merge_short_dwell(min_sec=1.0) → captions.json
# WhisperModel 必须在 --dry-run 提前 return 之后才 import，避免 dry-run 加载模型
```

> **脚本落盘**：复制 `templates/gen_captions.py` → 当期 `scripts/gen_captions.py`；按脚本补 `jieba.add_word` 专名；先 `--dry-run` 人工扫禁切反例，再全量 whisper。
>
> ```
> python3 templates/gen_captions.py --report-dir news-pipeline/monthly/2026-08 --dry-run
> python3 templates/gen_captions.py --report-dir news-pipeline/monthly/2026-08
> python3 templates/gen_captions.py --report-dir news-pipeline/2026-08-31 --extra-word 专名
> ```
>
> 旧 `gen_captions_v2.py` / `split_sentences`（所有标点一视同仁）**已废弃作切行器**；whisper 对齐仍是时间轴唯一锚。

#### 7.2 完整流程

```
视频脚本(Phase 2) → 提取每场景 TTS 文本存 scripts/voiceover-texts.json（或 scenes-meta.json）
    → 复制 templates/gen_captions.py → 当期 scripts/gen_captions.py，补 jieba 专名
    → --dry-run：jieba 分词 + 语义 group_caps 切行（不加载 whisper）
    → 人工扫禁切反例（稳不稳 / 硬新闻主轴 / 规划步骤 / 编程 Agent / 终止Cursor官方直连 / Hy四连发 / 羊报AI月报 / 整月风向 / 主题近一万 / 延期；）
    → faster-whisper(word_timestamps=True) 跑当期 wav
    → 每条字幕 SequenceMatcher 滑动窗口对齐到词级时间戳
    → merge_short_dwell(min_sec=1.0)
    → 场景间累加偏移 → captions.json + video-project/public/captions.json
```

**关键点**：
- **切行先于对齐**：`group_caps` 产出字幕字符串；whisper **只**负责时间轴。禁止 `split_sentences` 逐标点切行，禁止 16 字硬墙按字符下标切开专名/动宾
- **内容用原始脚本文本**，不依赖 ASR 识别文字，字幕文字 100% 准确
- **时间用音频真实发音时刻**：whisper 词级时间戳是唯一锚点，不再做任何「估算每句时长」；无 whisper 词时才允许比例兜底
- **SequenceMatcher 容忍 ASR 错字**：每条字幕对归一化词序列做滑动窗口模糊匹配，个别字识别错也能对上正确时间区间
- **最短显示 1s**：对齐后 `merge_short_dwell`，<1s 并回上一行（治 `延期；` 0.5s 闪行）
- **必须与 Phase 8 的 Composition/Root 时长同源**（同一批 atempo 后的 wav）
- **v2.3.0「按句聚合」已废弃作切行器**；whisper 对齐仍有效

**为什么放弃 v2.2.0 加权字符 + silencedetect**（历史，时间轴仍适用）：
- 加权系数（中文 1.0 / 数字 0.6 / 英文 0.35）是平均拟合，单句（尤其含大量版本号、英文术语）偏差大，仍逐句累积漂移
- silencedetect 只能在「正好有停顿」时吸附边界，无停顿的句子仍纯靠估算，后半段依旧偏
- v2.3.0 让时间戳直接取自音频，从根本上消除漂移；whisper small 模型 int8 CPU 单场景约 5–15s，可接受
- **v3.25.0 再修切行**：v2.3.0 的 `split_sentences` 把所有标点一视同仁，叠加 16 字硬墙会切开专名/动宾；改语义 `group_caps` + 黄金分割 + 禁切粘合

**字体使用规范**：
- 使用系统字体：`"PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif`
- 字幕：40-48px，加粗，白色，黑色半透明背景
- **禁止使用商用字体**（方正、汉仪、造字工房等）

### Phase 8: 渲染前校验（必须执行）

#### Step 8.0: 图片-脚本映射校验（v2.8.0 新增，必须首先执行）

```bash
# 校验图片数量与脚本场景数是否一致
IMAGES=$(ls news-pipeline/YYYY-MM-DD/images/scene*.png | wc -l)
AUDIO=$(ls news-pipeline/YYYY-MM-DD/voiceover/scene*.wav | wc -l)
echo "图片: $IMAGES, 音频: $AUDIO"
# 两者必须相等！不等则说明图片-脚本映射有误
```

**如果不等，检查原因**：
1. Hook 场景是否与第一条新闻共享了图片 → 合并图片 prompt
2. 是否有重复或多余的图片 → 删除多余图片
3. Composition.tsx 的 imageId 是否需要调整

#### Step 8.1: 梳理对应关系表

```
| 场景 | 图片 | 音频 | 内容 | 时长 |
|------|------|------|------|------|
| 1 | scene1.png | scene1.wav | Hook | Xs |
| 2 | scene2.png | scene2.wav | 第一条 | Xs |
```

**🔴 铁律：每个音频必须对应 1 张图，禁止 audioId=0 的无声场景！**

#### Step 8.2: 更新 Composition.tsx

```tsx
const sceneConfig = [
  { imageId: 1, audioId: 1, duration: 8.96 },   // Hook
  { imageId: 2, audioId: 2, duration: 24.64 },  // 第一条
  // ... 每个场景都必须明确指定 imageId、audioId、duration
];
```

**🔴 铁律：`duration` 必须来自 ffprobe 实测的音频时长，禁止手填估算值。** 用下面命令一次性打印全部实测时长，直接抄进 `sceneConfig`：

```bash
D=news-pipeline/YYYY-MM-DD/voiceover
for i in $(seq 1 8); do
  dur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$D/scene$i.wav")
  printf 'scene%d: %.2fs\n' "$i" "$dur"
done
```

> **🔴 经验教训（2026-07-12）：重跑 TTS 后必须同步更新 Composition.tsx 和 Root.tsx 的时长，否则字幕漂移。**
> 现象：只重新生成了音频 + 重算了 captions.json，但 `sceneConfig` 的 `duration` 还是旧音频的值。视频画面按旧时长排布、字幕按新音频时长对齐，两条时间轴从中段开始逐渐错位，到 1 分多钟处字幕与音频明显重叠、对不上。
> 铁律：**任何一次重跑 TTS（哪怕只改一个场景），都必须重新 ffprobe 全部音频 → 同步刷新 Composition.tsx 的 `sceneConfig` 时长 + 标题浮层 `NewsTitle` 的 `durationInFrames` + Root.tsx 的 `TOTAL_DURATION_SEC` → 再重算 captions.json → 最后渲染。**四者必须来自同一批音频，缺一步就会漂移。

#### Step 8.3: 更新 Root.tsx

```tsx
const TOTAL_DURATION_SEC = 场景1时长 + 场景2时长 + ... + 场景N时长;
```

**校验：渲染出的视频总时长必须 ≈ 音频总时长（`captions.json` 末条 `endMs`）。** 若两者相差超过 0.5s，说明 `sceneConfig`/`Root.tsx` 与音频不同步，字幕必然漂移，需回到 Step 8.2 修正后重渲染：

```bash
# 渲染后校验：视频时长 vs 音频总时长
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \
  "news-pipeline/YYYY-MM-DD/video/{文件名}.mp4"
```

#### Step 8.4: 复制资源到 public 目录

```bash
cp news-pipeline/YYYY-MM-DD/images/scene*.png video-project/public/images/
cp news-pipeline/YYYY-MM-DD/voiceover/scene*.wav video-project/public/voiceover/
cp news-pipeline/YYYY-MM-DD/captions/captions.json video-project/public/captions.json
```

### Phase 9: 视频合成

**🔴 重要：渲染目录和命令**

渲染视频时必须使用以下命令（从项目根目录执行）：

```bash
/Users/youngsdream/Documents/learn-claude-code/news-pipeline/video-project/node_modules/.bin/remotion render \
  /Users/youngsdream/Documents/learn-claude-code/news-pipeline/video-project/src/index.ts \
  AINewsVideo \
  "out/{按 REPORT_MODE 读取文件名前缀}.mp4" \
  --codec h264 --crf 18 \
  --public-dir /Users/youngsdream/Documents/learn-claude-code/news-pipeline/video-project/public
```

**文件名按模式参数映射表读取**：
- daily：`out/【YYYY-MM-DD】{核心标题}… | 今日羊报AI.mp4`
- weekly：`out/【MM-DD~MM-DD】{核心标题}… | 羊报AI周刊.mp4`
- **monthly**：`out/【YYYY-MM】{核心标题}… | 羊报AI月报.mp4`

**关键参数说明**：
- `node_modules/.bin/remotion`：使用 video-project 下的本地 remotion
- `src/index.ts`：必须指定入口点文件路径
- `--public-dir`：必须指定 public 目录的绝对路径

**🔴 渲染输出位置（必须记住）**：
- 视频渲染到：`/Users/youngsdream/Documents/learn-claude-code/out/`
- **不是** `news-pipeline/video-project/out/`

**🔴 视频合成后自动归档（必须执行）**：

视频渲染完成后，必须立即将视频从根目录 `out/` 复制到报告目录（按 `REPORT_MODE` 对应的输出目录）：

```bash
# 复制视频到报告目录（以 daily 为例；weekly 用 weekly/... ，monthly 用 monthly/YYYY-MM/）
cp "/Users/youngsdream/Documents/learn-claude-code/out/【YYYY-MM-DD】{核心标题}… | 今日羊报AI.mp4" \
   "/Users/youngsdream/Documents/learn-claude-code/news-pipeline/YYYY-MM-DD/video/"

# monthly 模式：
# cp "/Users/youngsdream/Documents/learn-claude-code/out/【YYYY-MM】{核心标题}… | 羊报AI月报.mp4" \
#    "/Users/youngsdream/Documents/learn-claude-code/news-pipeline/monthly/YYYY-MM/video/"

# 验证复制成功
ls -la "/Users/youngsdream/Documents/learn-claude-code/news-pipeline/{对应目录}/video/"
```

**⚠️ 常见错误**：
- 错误：从 `news-pipeline/video-project/out/` 复制（旧文件）
- 正确：从 `/Users/youngsdream/Documents/learn-claude-code/out/` 复制（新文件）

**归档时机**：视频合成完成后立即执行，不要等到上传阶段再复制。

### Phase 10: 封面、发布信息与公众号图文

> **注意**：如果已在 Phase 5.5 异步生成封面，此步骤可跳过封面生成，直接使用已生成的文件。

#### 10.1 生成多平台封面（如未异步生成）

使用图片生成 API 为各平台生成不同比例的封面：

| 平台 | 比例 | 尺寸 | 输出文件 | 用途 |
|------|------|------|----------|------|
| B站/通用 | 4:3 | 1536x1152 | `horizontal-4-3.png` | B站投稿封面、公众号/视频号横版 |
| 抖音/竖版 | 3:4 | 1152x1536 | `vertical-3-4.png` | 抖音封面、抖音个人主页卡片、公众号/视频号竖版 |

**封面模板 Prompt**（按 `REPORT_MODE` 读取品牌名与日期字段，**禁止硬编码**；周报用"羊报AI周刊"+日期范围，月报用"羊报AI月报"+`{YYYY-MM}` 见月报模式章节）：

**🔴 v3.13.0 封面铁律（视频号 2026-07-26 限流教训）**：
- 🚫 **禁止**写实真人主播 / news anchor / 假新闻脸出镜（易触肖像与虚假内容）
- ✅ 用抽象科技视觉、产品 UI、芯片/屏幕信息拼贴、无人演播室空镜
- 完整策略见 `templates/platform-compliance.md` §3.2

```
A professional Chinese AI news studio cover image. Empty modern curved news desk in a high-tech studio, NO human presenter, NO realistic human face or news anchor. Behind the desk are multiple large display screens arranged in a grid showing: {本期核心新闻相关的视觉元素，产品/抽象图形，勿放可识别真人}. The studio has dramatic blue and red neon lighting, with red accent lights along the desk edges and blue ambient lighting. In the top right corner, display the text "今日羊报 AI" on the first line and "AI 新闻" on the second line in large white Chinese characters. In the center of the image, display the date "{YYYY-MM-DD}" in very large white bold text. Professional broadcast news photography style, photorealistic environment, highly detailed, cinematic lighting, {ratio} aspect ratio. No people, no faces.
```

输出到 `{REPORT_MODE 对应的输出目录}`（daily `news-pipeline/YYYY-MM-DD/`；weekly `news-pipeline/weekly/...`；monthly `news-pipeline/monthly/YYYY-MM/`）

#### 10.2 生成多平台发布信息

生成 `{输出目录}/publish.json`，包含 B站、抖音、视频号、公众号四个平台（下方为 daily 模板，weekly/monthly 按模式参数映射表替换标题前缀/tags/日期字段）：

```json
{
  "title": "【YYYY-MM-DD】{核心标题}… | 今日羊报AI",
  "description": "视频简介，2-3句话概括本期内容",
  "tags": ["今日羊报AI", "AI日报", "..."],
  "platform": {
    "bilibili": {
      "title": "【YYYY-MM-DD】{核心标题}｜{N}条重磅AI新闻一次看完 | 今日羊报AI",
      "tags": ["今日羊报AI", "AI日报", "..."],
      "description": "B站简介，含 hashtag\n\n🔴 注意：简介中数字不能太多（会被检测为违规推广），版本号简化，数字用中文替代"
    },
    "douyin": {
      "title": "今日羊报AI YYYY-MM-DD",
      "tags": ["AI日报", "..."],
      "description": "抖音简介，含 hashtag"
    },
    "channels": {
      "title": "今日羊报AI M月D日",
      "tags": ["AI日报", "..."],
      "description": "视频号简介，含 hashtag"
    },
    "wechat": {
      "title": "【YYYY-MM-DD】{核心标题}… | 今日羊报AI",
      "article": "wechat-article-YYYY-MM-DD.md",
      "images": "wechat-images/"
    }
  }
}
```

**月报模式 publish.json 变体**（`REPORT_MODE=monthly` 时使用）：
- `title`：`【YYYY-MM】{核心标题}… | 羊报AI月报`
- `tags`：`["羊报AI月报", "AI月报", "AI月度盘点", "..."]`
- `bilibili.title`：`【YYYY-MM】{核心标题}｜本月{N}大AI趋势月度盘点 | 羊报AI月报`
- `douyin.title`：`羊报AI月报 YYYY-MM`
- `channels.title`：`羊报AI月报 YYYY年M月`
- `wechat.title`：`【YYYY-MM】{核心标题}… | 羊报AI月报`
- `bilibili.description`：**强制全数字中文化**（见 B站简介数字中文化章节）
- `wechat.article`：`wechat-article-YYYY-MM.md`

**标题规则（v3.17：日期在前、报刊名在后）**:
- 日报 B站：`【YYYY-MM-DD】{核心标题}｜{N}条重磅AI新闻一次看完 | 今日羊报AI`
- 日报 抖音：`今日羊报AI YYYY-MM-DD`（≤30字，纯报刊名+日期，无特殊符号）
- 日报 视频号：`今日羊报AI M月D日`（≤16字，仅支持中文、数字、空格、书名号、引号、冒号、加号、问号、百分号、摄氏度；`.` `~` 不在白名单）
- 日报 公众号：`【YYYY-MM-DD】{核心标题}… | 今日羊报AI`
- **周报 B站**：`【MM-DD~MM-DD】{核心标题}｜本周{N}大AI新闻一次看完 | 羊报AI周刊`
- **周报 抖音**：`羊报AI周刊 MM-DD~MM-DD`（≤30字）
- **周报 视频号**：`羊报AI周刊 M月D日至D日`（≤16字；用「至」连接，勿用 `~`/`.`）
- **周报 公众号**：`【MM-DD~MM-DD】{核心标题}… | 羊报AI周刊`
- **月报 B站**：`【YYYY-MM】{核心标题}｜本月{N}大AI趋势月度盘点 | 羊报AI月报`
- **月报 抖音**：`羊报AI月报 YYYY-MM`（≤30字）
- **月报 视频号**：`羊报AI月报 YYYY年M月`（≤16字）
- **月报 公众号**：`【YYYY-MM】{核心标题}… | 羊报AI月报`

**抖音标题规则（全部模式）**：
- 格式：`{报刊名} {日期字段}`，纯报刊名+日期，不加任何核心标题/副标题/特殊符号
- 日报：`今日羊报AI 2026-08-01`
- 周报：`羊报AI周刊 07-28~08-01`
- 月报：`羊报AI月报 2026-08`
- 总字符数 ≤30（含空格）
- 禁止加 `|`、`｜`、`：` 等分隔符，纯报刊名+空格+日期

**视频号标题规则（全部模式）**：
- 格式：`{报刊名} {日期字段}`，纯报刊名+日期
- 日报：`今日羊报AI 8月30日`（`今日羊报AI 2026年8月1日` 超 16 字，勿用）
- 周报：`羊报AI周刊 8月24日至30日`（16 字）
- 月报：`羊报AI月报 2026年8月`
- 总字符数 ≤16（含空格）
- 符号仅支持书名号、引号、冒号、加号、问号、百分号、摄氏度；**`.` `~` 不在白名单**
- 🔴 反例：`羊报AI周刊 8月24日~8月30日` 同时 18 字超限 + 含非法 `~` →保存草稿按钮 silent disabled
- 逗号可用空格代替
- 视频号短标题 = 视频号标题，两者使用同一格式

#### 10.3 生成公众号图文

从视频脚本中提取核心内容，去掉 Hook/CTA 等口语化部分，生成公众号文章：

**文章结构**：
```
# {标题}

> 今日羊报 AI · YYYY-MM-DD

---

## 1. {新闻标题1}

{正文内容，2-3段}

![配图描述](images/sceneN.png)

---

## 2. {新闻标题2}
...

---

**今日 AI 圈，又热闹又魔幻。**

---

👆 觉得有用就点个赞、转发给身边关注 AI 的朋友！
🔔 关注「今日羊报 AI」，每天 9 点带你速览 AI 圈最热的 5 条新闻。
💬 你最关心哪条？评论区聊聊！
```

**月报模式公众号图文变体**（`REPORT_MODE=monthly` 时使用，结构按月度趋势组织而非单事件）：
```
# {标题}

> 羊报AI月报 · YYYY-MM

---

## 趋势一：{趋势名}

{趋势正文，2-3段，含时间线 + 关键驱动 + 代表案例}

![配图描述](images/sceneN.png)

---

## 趋势二：{趋势名}
...

---

## 月度总结
{TOP10 归类 + 主题分布一句话}

## 下月展望
{2-3 条预测}

---

**这个月，AI 圈的风向已经变了。**

---

👆 觉得有用就点个赞、转发给关注 AI 的朋友！
🔔 关注「羊报AI月报」，每月带你回顾 AI 圈整月风向。
💬 你最看好哪条趋势？评论区聊聊！
```

**生成规则**：
- 标题使用视频标题
- daily/weekly：每个新闻事件一个 `##` 标题；monthly：每条趋势一个 `##` 标题 + 月度总结 + 下月展望
- 正文从脚本段落中提取，去掉口语化表达（"今天"、"我们"、"大家"等）
- 每个事件/趋势配一张场景图片（scene2.png ~ sceneN.png，跳过 Hook 场景）
- 结尾署名与 CTA 按模式参数映射表读取（daily"今日羊报 AI·每天9点带你速览AI圈最热的5条新闻"；monthly"羊报AI月报·每月带你回顾AI圈整月风向"）

输出到：
- 文章：`news-pipeline/YYYY-MM-DD/wechat-article-YYYY-MM-DD.md`
- 配图：`news-pipeline/YYYY-MM-DD/wechat-images/sceneN.png`

#### 10.4 归档资源

```bash
# 输出目录与视频文件名前缀按 REPORT_MODE 读取（此处为 daily；monthly 用 news-pipeline/monthly/YYYY-MM/ 与 【羊报AI月报】*.mp4）
mkdir -p news-pipeline/YYYY-MM-DD/{scripts,storyboards,prompts,images,voiceover,captions,video,wechat-images}
cp news-pipeline/video-project/out/【YYYY-MM-DD】*.mp4 news-pipeline/YYYY-MM-DD/video/
```

#### 10.5 🔴 周报砍掉决策（v3.21.0，诊断7兜底）

周报系列历史表现最差（均播 47、5s 25.3%、2s 跳出 48.8%，全站最低）。改造为深聊型后设此 stop-go gate：

- **Week 3 末**回填当期周报播放量到 `news-pipeline/weekly/{range}/weekly-performance.md`（字段：日期范围、均播、5s 完播率、2s 跳出率、分享、评论）
- **<80** → Week 4 起停周报，产能转给日报
- **改造后连续 2 期均播仍 <80** → 砍掉周报，产能全转日报
- **≥100** → 继续按 `templates/script-template-weekly.md` 新模板出周报

### Phase 11: B站自动上传（Playwright MCP）

**权限已在预授权阶段获得，直接执行。**

#### 11.0 处理浏览器锁（自动处理，不询问用户）

如果 Playwright MCP 报错 "Browser is already in use" 或 "Target page, context or browser has been closed"：

```bash
# 1. 关闭现有浏览器进程
pkill -f "mcp-chrome-*" 2>/dev/null
sleep 2

# 2. 删除锁文件
rm -f ~/Library/Caches/ms-playwright/mcp-chrome-*/SingletonLock
```

**🔴 重要：浏览器锁是常见问题，自动处理不需要询问用户。**

#### 11.1 打开上传页面

```
browser_navigate("https://member.bilibili.com/platform/upload/video/frame")
```

#### 11.2 上传视频

```
browser_click(target=e231)  # 点击上传区域，触发 file chooser
# 视频路径按 REPORT_MODE：daily news-pipeline/YYYY-MM-DD/video/【YYYY-MM-DD】*.mp4
#                       monthly news-pipeline/monthly/YYYY-MM/video/【羊报AI月报】*.mp4
browser_file_upload("news-pipeline/YYYY-MM-DD/video/【YYYY-MM-DD】*.mp4")
```

**🔴 重要**：`browser_click` 使用 `target` 参数（ref 编号）比 `element` 文本描述更可靠。

#### 11.3 上传封面（两步流程）

```
browser_click(target=e328)  # 点击「封面设置」→ 打开封面编辑弹窗
browser_click(target=e656)  # 点击「上传封面」→ 触发 file chooser
browser_file_upload("news-pipeline/YYYY-MM-DD/horizontal-4-3.png")
browser_click(target=e715)  # 点击「完成」→ 确认封面
```

**🔴 B站封面 file input 无 image accept（v3.3.0 更新）**：B站的 file input 不包含 image accept 属性，用 `input[accept*="image"]` 找不到。用位置索引：
```javascript
const inputs = await page.$$('input[type="file"]');
// inputs[0]: 视频 (.mp4)
// inputs[1]: 封面 (通过封面设置弹窗触发)
await inputs[1].setInputFiles('horizontal-4-3.png');
```

**⚠️ 实测经验（v3.3.0 / 被 v3.12.0 覆盖）**：旧文档建议「封面不稳就跳过」。**2026-07-25 实测可自动补封面**，见下方 v3.12 草稿编辑页流程；首次投稿若封面失败，可**打开草稿再补**，不要默认放弃。

#### 11.4 选择分区「人工智能」（v3.17 新增）

**🔴 分区选择器是自定义下拉框，必须用 JS evaluate。视频投稿必须选择「人工智能」分区。**

```javascript
// 1. 点击打开分区下拉框（textbox 或 当前分区占位）
browser_click(target=eXXX)  // 分区下拉框，通常显示「请选择分区」或当前分区

// 2. 用 JS 找到并点击「人工智能」选项（必须！）
browser_evaluate("""() => {
  const options = document.querySelectorAll('li, div, span, p');
  for (const opt of options) {
    const t = (opt.textContent || '').trim();
    if (t === '人工智能' && opt.offsetParent) {
      opt.click();
      return 'clicked 人工智能';
    }
  }
  return 'not found';
}""")

// 3. 校验分区已选中（确认输入框/占位文本变为「人工智能」）
browser_evaluate("""() => {
  const txt = document.body.innerText;
  const el = document.querySelector('[class*="select"], [class*="partition"], [class*="region"]');
  return txt.includes('人工智能') ? 'partition=人工智能' : 'partition NOT set';
}""")
```

**兜底**：若自定义下拉框无法展开，可尝试 `browser_run_code_unsafe` 触发点击分区元素后等待 500ms 再执行 JS 选选项。**分区未选对会导致投稿分类错误，必须验收。**

#### 11.5 设置创作声明（自定义下拉框）

**🔴 B站的创作声明是自定义下拉框组件，不是标准 `<select>`。`browser_click(listitem=...)` 不可靠，必须用 JS evaluate：**

```javascript
// 1. 点击打开下拉框
browser_click(target=e362)  // textbox "请选择符合您视频内容的创作声明"

// 2. 用 JS 找到并点击选项（必须！）
browser_evaluate("""() => {
  const options = document.querySelectorAll('li, div, span, p');
  for (const opt of options) {
    if (opt.textContent.trim() === '个人观点，仅供参考') {
      opt.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")
```

#### 11.6 填写简介（Quill 编辑器）

**🔴 B站简介使用 Quill 富文本编辑器，直接 `browser_type` 可能不生效。必须用 JS 注入：**

```javascript
browser_evaluate("""() => {
  const editor = document.querySelector('.ql-editor');
  if (editor) {
    editor.innerHTML = '<p>第一段简介内容</p><p><br></p><p>#标签1 #标签2 #标签3</p>';
    editor.dispatchEvent(new Event('input', { bubbles: true }));
    return 'description set';
  }
  return 'editor not found';
}""")
```

#### 11.7 填写标签

```
# 标签输入框: textbox "按回车键Enter创建标签"
# 最多 10 个标签，每个标签输入后按 Enter 确认
tags = ["DeepSeek", "Anthropic", "Ideogram", "英伟达", ...]
for tag in tags:
    browser_type(target=e399, text=tag)
    browser_press_key("Enter")
```

#### 11.8 加入合集（自定义下拉框）

**🔴 合集选择器也是自定义下拉框，必须用 JS evaluate。合集名按 `REPORT_MODE` 从模式参数映射表读取：daily `「今日羊报 AI」` / weekly `「羊报AI周刊」` / monthly `「羊报AI月报」`。**

**🔴 风险点**：合集必须由用户预先在 B站创作中心手动创建。若 monthly 模式合集「羊报AI月报」未创建，下方 JS 找不到选项会返回 `not found`，Phase 11.8 卡住——此时需提示用户去后台创建后再继续。

```javascript
// 1. 点击打开下拉框
browser_click(target=e525)  // "请选择合集"

// 2. 用 JS 找到并点击选项（合集名按 REPORT_MODE 读取）
browser_evaluate("""() => {
  const options = document.querySelectorAll('li, div, span, p');
  // 合集名按模式参数映射表：daily 「今日羊报 AI」/ weekly 「羊报AI周刊」/ monthly 「羊报AI月报」
  const targetName = '「今日羊报 AI」';
  for (const opt of options) {
    if (opt.textContent.trim() === targetName) {
      opt.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")
```

#### 11.9 存草稿（不直接投稿）

**🔴 重要：所有平台上传一律存草稿，不直接发布！用户确认后再手动发布。**

```
browser_click(target=e496)  # 点击「存草稿」
# 等待页面提示保存成功
browser_wait_for(time=3)
```

#### B站上传组件操作总结（v1.4.0 实测）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 视频上传 | file chooser | `browser_click(ref)` → `file_upload` | ✅ 高 |
| 封面设置 | 弹窗 | 点击封面设置 → 上传封面 → file_upload → 完成 | ✅ 高 |
| 分区「人工智能」 | **自定义下拉框** | 点击展开 → **JS evaluate 点击「人工智能」**（v3.17 新增，见 11.4） | ⚠️ 必须用 JS |
| 创作声明 | **自定义下拉框** | 点击 textbox → **JS evaluate 点击选项** | ⚠️ 必须用 JS |
| 标签 | 输入框 | `type` + `Enter`，最多 10 个 | ✅ 高 |
| 简介 | **Quill 编辑器** | **JS 注入 `.ql-editor`** | ⚠️ 必须用 JS |
| 合集 | **自定义下拉框** | 点击展开 → **JS evaluate 点击选项** | ⚠️ 必须用 JS |
| 投稿按钮 | 按钮 | `browser_click(ref)` | ✅ 高 |

**关键经验**：
1. **`browser_click(target=ref编号)` 比 `browser_click(element=文本描述)` 更可靠**
2. **所有自定义下拉框（分区、创作声明、合集）必须用 `browser_evaluate` + JS 点击**
3. **Quill 编辑器必须用 JS 注入 `innerHTML` + dispatch `input` 事件**
4. **`browser_file_upload` 必须在 file chooser 对话框打开后才能调用**
5. **封面上传是两步流程：先点「封面设置」打开弹窗，再点「上传封面」触发 file chooser**

### Phase 12: 微信公众号自动上传（Playwright MCP）

**权限已在预授权阶段获得，直接执行。**

**🔴 2026-08-13 日报视频实测流程优化（v3.17.0）**——公众号上传建议按以下**已验证顺序**执行，避免踩坑：

1. **标题/作者/正文先行**：先确保标题、作者、正文、视频号内容就位，再处理封面——封面不稳定不得阻塞草稿（v3.5.0 降级原则）
2. **正文图片用「本地上传」**：正文配图一律用工具栏「图片」→「本地上传」→ `setInputFiles(sceneN.png)`，不要用纯 innerHTML 注入（注入不落素材库，封面无法「从正文选择」）
3. **封面选图路径**：先用 `horizontal-4-3.png` 插入正文 → 再「从正文选择」设封面（v3.8.0 铁律：裁剪弹窗标题「编辑封面」、确认键是 enabled「确认」非灰「确定」、禁止弹窗内 Escape、轮询 `.js_cover_preview_new{display:block; bg 含 mmbiz}`）
4. **合集选择 try-catch 兜底**：合集失败时 `try-catch`（timeout 5000）跳过，不阻塞保存草稿（v3.3.0）
5. **最后保存草稿**：所有项目填完后点「保存为草稿」，以 URL `appmsgid=` 为准；弹窗阻挡时 Escape 关闭上传中挡层再保存
6. **验收**：`appmsgid=` 出现在 URL / 保存成功回执为准，勿只看「已保存」文案（常不出现）

**🔴 重要经验：公众号编辑器使用 ProseMirror + 自定义 Vue 组件，自动化难度较高。封面选择、合集选择等需要特殊处理。**

#### 12.0 完整上传流程（推荐顺序）

```
1. 打开公众号后台 → 点击「新的创作」→「文章」（新标签页打开）
2. 切换到新标签页
3. 填写作者（标准 input，固定 `羊报AI周刊` / `今日羊报AI` / `羊报AI月报`，≤8 字；勿填署名格式）
4. 点击正文区域获取 focus → 插入视频号内容
5. 填写正文内容（ProseMirror nth(1) + execCommand insertHTML，🔴 v3.23.0：禁直接 innerHTML）
6. 通过「图片」→「本地上传」插入封面图到正文
7. 上传封面（从正文选择 / 从图片库选择）
8. 填写标题（正文注入之后！`.ProseMirror`.first() + keyboard.type，回读 `#title.value`）
9. 设置原创声明
10. 设置赞赏
11. 选择合集
12. 保存草稿
```

#### 12.1 打开公众号后台

```
browser_navigate("https://mp.weixin.qq.com/cgi-bin/home?t=home/index&token={token}")
```

如果显示「请重新登录」，点击「登录」链接。登录后 token 会自动更新。

#### 12.2 创建新文章

```
# 点击「新的创作」→「文章」（会打开新标签页）
browser_run_code_unsafe("""async (page) => {
  const menuItem = page.locator('.new-creation__menu-item').first();
  await menuItem.click();
  await page.waitForTimeout(3000);
  // 获取所有页面，找到新打开的编辑页
  const pages = page.context().pages();
  return pages.length;
}""")

# 切换到最新标签页
browser_tabs(action="select", index={最新标签页索引})
```

#### 12.3 填写作者（标题放到 12.5b，正文注入之后）

**🔴 作者字段 ≤8 字（v3.24.0 / 2026-08-30 实测）**：映射表「公众号署名」只写进正文开头/文末，**禁止**填进作者栏。作者栏固定报刊名：

| 模式 | 作者字段 | 字数 |
|------|---------|------|
| 日报 | `今日羊报AI` | 6 |
| 周报 | `羊报AI周刊` | 5 |
| 月报 | `羊报AI月报` | 5 |

反例：`羊报AI周刊 · 08-24~08-30` → 保存被拦「作者不能超过8个字」。

```javascript
browser_run_code_unsafe("""async (page) => {
  const result = await page.evaluate(() => {
    const authorInput = document.querySelector('input[placeholder="请输入作者"]');
    if (!authorInput) return 'author input not found';
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(authorInput, '羊报AI周刊');  // 日报改 今日羊报AI；月报改 羊报AI月报
    authorInput.dispatchEvent(new Event('input', { bubbles: true }));
    return 'author=' + authorInput.value + ' len=' + authorInput.value.length;
  });
  return result;
}""")
```

**🔴 标题不要在这一步填。** `#title` 是 `h=0` 隐藏 TEXTAREA，直接 click 会 30s 超时；页面有**两个**可见 `.ProseMirror`（y≈194 标题代理 / y≈272 正文）。标题填写永远放到正文注入之后（12.5b）：

```javascript
// 12.5b 标题填写（正文注入之后）
await page.locator('.ProseMirror').first().click();
await page.keyboard.press('Meta+A');  // macOS；Linux/Windows 用 Control+A
await page.keyboard.type('【MM-DD~MM-DD】核心标题｜本周N大AI新闻一次看完 | 羊报AI周刊');
const titleVal = await page.evaluate(() => document.querySelector('#title')?.value || '');
if (!titleVal || titleVal.length < 8) return 'FAILED title not synced to #title';
```

#### 12.4 插入视频号内容

**🔴 公众号支持直接插入视频号视频，这是推荐的视频插入方式：**

```
# 1. 点击正文区域获取 focus
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const editors = document.querySelectorAll('.ProseMirror');
    if (editors[1]) editors[1].click();
  });
  return 'body clicked';
}""")

# 2. 点击工具栏「视频号」按钮（坐标方式）
browser_run_code_unsafe("""async (page) => {
  // 找到视频号按钮位置
  const result = await page.evaluate(() => {
    const allElements = document.querySelectorAll('a, button, span, div');
    for (const el of allElements) {
      const rect = el.getBoundingClientRect();
      if (rect.y < 50 && rect.y > 0 && el.textContent.trim() === '视频号') {
        return { x: rect.x, y: rect.y };
      }
    }
    return null;
  });
  if (result) {
    await page.mouse.click(result.x + 20, result.y + 10);
    await page.waitForTimeout(2000);
  }
  return 'clicked 视频号';
}""")

# 3. 在弹窗中选择「最近使用」的账号
browser_run_code_unsafe("""async (page) => {
  // 点击「最近使用」中的账号名
  const result = await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      const text = el.textContent.trim();
      const rect = el.getBoundingClientRect();
      if (text === '账号名' && el.offsetParent !== null && rect.x > 500 && rect.y > 300 && rect.y < 500) {
        el.click();
        return 'clicked';
      }
    }
    return 'not found';
  });
  await page.waitForTimeout(2000);
  return result;
}""")

# 4. 选择第一个视频
browser_run_code_unsafe("""async (page) => {
  await page.mouse.click(340, 320);  // 第一个视频缩略图位置
  await page.waitForTimeout(1000);
  return 'selected video';
}""")

# 5. 点击「插入」
browser_run_code_unsafe("""async (page) => {
  const insertBtn = page.locator('button:has-text("插入")');
  await insertBtn.first().click();
  await page.waitForTimeout(2000);
  return 'inserted';
}""")
```

#### 12.5 填写正文内容

**🔴 v3.23.0 / 2026-08-29 实测修正：禁止对 ProseMirror 正文直接 `innerHTML = ...` 赋值！**
0829 实测：赋值返回"ok"但编辑器立即回滚，验证 `pm.textContent.length === 1`——**内容被静默清空**（无任何报错）。唯一可靠方式是 `document.execCommand('insertHTML')`：

```javascript
browser_run_code_unsafe("""async (page) => {
  const htmlContent = `<h2>1. 新闻标题</h2><p>正文内容...</p>`; // 由外部传入
  const result = await page.evaluate((html) => {
    const editors = document.querySelectorAll('.ProseMirror');
    const bodyEditor = editors[1];  // 第二个 ProseMirror 是正文
    if (!bodyEditor) return 'body editor not found';
    bodyEditor.focus();
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(bodyEditor);
    sel.removeAllRanges();
    sel.addRange(range);
    document.execCommand('insertHTML', false, html);
    // 🔴 注入后必须回读验证，不达标视为失败
    const len = bodyEditor.textContent.trim().length;
    return `inserted, pmLen=${len}`;
  }, htmlContent);
  if (!result.includes('pmLen=') || parseInt(result.match(/pmLen=(\\d+)/)[1]) < 1000) {
    return `FAILED: ${result}`;  // 日报正文应 >1000 字，短文按实际阈值调整
  }
  return result;
}""")
```

**🔴 v3.23.0 新增坑：正文注入操作可能把标题框灌入整篇文章**（实测标题计数器变 1776/64、标题区显示正文全文）。恢复流程见 12.5b；**预防规则：标题填写永远放到正文注入之后**（调整 12.0 顺序：正文 → 图片 → 封面 → **再填标题** → 原创 → 合集 → 保存）。

#### 12.5b 标题被正文注入覆盖后的重置（v3.23.0 / 2026-08-29 实测）

用 `data-placeholder` 含「标题」定位（勿依赖编辑器索引——注入操作后索引可能漂移）：

```javascript
browser_run_code_unsafe("""async (page) => {
  const title = '【2026-08-29】... | 今日羊报AI'; // 由外部传入
  const result = await page.evaluate((t) => {
    let titleBox = null;
    for (const el of document.querySelectorAll('[contenteditable="true"]')) {
      if ((el.getAttribute('data-placeholder') || '').includes('标题')) { titleBox = el; break; }
    }
    if (!titleBox) return 'title box not found';
    titleBox.focus();
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(titleBox);
    sel.removeAllRanges();
    sel.addRange(range);
    document.execCommand('delete');
    document.execCommand('insertText', false, t);
    return `title set, len=${titleBox.textContent.length}`;
  }, title);
  return result; // 预期 len === 标题字符数
}""")
```

#### 12.6 上传图片到正文

**🔴 通过工具栏「图片」→「本地上传」插入图片：**

```
# 1. 点击正文区域获取 focus
# 2. 点击工具栏「图片」→「本地上传」
browser_run_code_unsafe("""async (page) => {
  // 点击图片按钮
  await page.mouse.click(530, 17);  // 图片按钮位置
  await page.waitForTimeout(1000);
  // 点击「本地上传」
  await page.mouse.click(550, 75);
  await page.waitForTimeout(1000);
  return 'clicked 本地上传';
}""")

# 3. 上传文件（等待 file chooser）
browser_file_upload("news-pipeline/YYYY-MM-DD/wechat-images/sceneN.png")

# 重复以上步骤插入多张图片
```

#### 12.7 上传封面（已验证流程 v3.8.0 / 2026-07-19 周报实测）

**🔴 完整推荐流程：先把封面图（横版 `horizontal-4-3.png`）插入正文，再「从正文选择」设封面。**  
**🔴 降级原则（v3.5.0）**：封面步骤不稳定时，**不得阻塞整篇草稿**——先保证标题/作者/正文/原创/「保存为草稿」成功；封面可留草稿箱手补。

**🔴 v3.8.0 铁律（今日踩坑总结）**：
1. 裁剪弹窗标题是 **「编辑封面」**，主按钮文案是 **「确认」**（不是「完成」；页面上另有 **disabled 的「确定」**，`getByRole/locator('确定')` 会点到灰按钮失败）
2. **裁剪弹窗打开期间禁止 `Escape`**——会关掉未确认的裁剪，封面不落库
3. 验收必须以 **`.js_cover_preview_new` 的 `display===block` 且 `background-image` 含 `mmbiz`/`qpic`** 为准；`#js_cover_area` 内文案可仍残留「拖拽或选择封面」
4. 点「确认」后 **轮询 3–8s**：`dialogOpen=false && previewDisplay=block && hasQpic` 才算成功；失败再点一次「确认」
5. 「从正文选择」节点常 `display:none`：先 hover `#js_cover_area .js_cover_btn_area`，再 **强制 style 显示** 后点 `.js_selectCoverFromContent`
6. 缩略图是 **`span.appmsg_content_img.cover` + background-image**，优先点带 `mmbiz` 背景的 `.appmsg_content_img_item`
7. 已有草稿可直接打开：`appmsg?…&appmsgid={id}&token=…`（比「新的创作」稳）

```
# 步骤1：上传封面图到正文（工具栏「图片」→「本地上传」）
browser_run_code_unsafe("""async (page) => {
  const cover = '/ABS/PATH/horizontal-4-3.png'; // 周报用 weekly/.../horizontal-4-3.png
  const prose = document.querySelectorAll('.ProseMirror');
  if (prose[1]) { prose[1].click(); }
  // 工具栏「图片」→「本地上传」
  await page.evaluate(() => {
    for (const item of document.querySelectorAll('li, a, span')) {
      if ((item.textContent || '').trim() === '图片' && item.offsetParent) {
        const r = item.getBoundingClientRect();
        if (r.y < 80 && r.y >= 0) { item.click(); return; }
      }
    }
  });
  await page.waitForTimeout(600);
  await page.evaluate(() => {
    for (const item of document.querySelectorAll('*')) {
      if ((item.textContent || '').trim() === '本地上传' && item.offsetParent) {
        item.click(); return;
      }
    }
  });
  await page.waitForTimeout(800);
  const input = await page.$('input[type="file"][accept*="image"]')
    || (await page.$$('input[type="file"]'))[0];
  if (input) await input.setInputFiles(cover);
  await page.waitForTimeout(8000); // 等上传完成
  await page.keyboard.press('Escape'); // 仅关「上传中」类挡层，此时还没开裁剪弹窗
  return 'body image ready';
}""")

# 步骤2+3+4：hover 封面 → 从正文选择 → 选图 → 下一步 → 等待「编辑封面」→ 点「确认」→ 轮询 preview
browser_run_code_unsafe("""async (page) => {
  const coverLoc = page.locator('#js_cover_area .js_cover_btn_area').first();
  await coverLoc.scrollIntoViewIfNeeded();
  await coverLoc.hover({ force: true });
  await page.waitForTimeout(700);
  // 强制显示「从正文选择」
  await page.evaluate(() => {
    const btn = document.querySelector('.js_selectCoverFromContent');
    if (btn) {
      btn.style.cssText = 'display:block!important;visibility:visible!important;opacity:1!important;pointer-events:auto!important;';
      btn.click();
    }
  });
  await page.waitForTimeout(1500);
  // 优先点带 mmbiz 背景的正文图
  await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.appmsg_content_img_item'));
    for (const el of items) {
      const span = el.querySelector('.appmsg_content_img.cover, span');
      const bg = span ? getComputedStyle(span).backgroundImage : '';
      if (bg.includes('mmbiz')) { el.click(); return; }
    }
    if (items[0]) items[0].click();
  });
  await page.waitForTimeout(500);
  // 下一步
  await page.evaluate(() => {
    for (const btn of document.querySelectorAll('button')) {
      if ((btn.textContent || '').trim() === '下一步' && btn.className.includes('primary') && btn.offsetParent) {
        btn.click(); return;
      }
    }
  });
  // 等裁剪弹窗「编辑封面」
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(500);
    const open = await page.evaluate(() =>
      Array.from(document.querySelectorAll('.weui-desktop-dialog__title'))
        .some(el => (el.textContent || '').includes('编辑封面') && el.getBoundingClientRect().width > 50));
    if (open) break;
  }
  await page.waitForTimeout(1200);
  // 等「确认」可点（非 disabled）再 click —— 禁止点「确定」灰按钮
  for (let i = 0; i < 20; i++) {
    const ok = await page.evaluate(() => {
      for (const btn of document.querySelectorAll('button')) {
        if ((btn.textContent || '').trim() === '确认'
          && btn.className.includes('weui-desktop-btn_primary')
          && !btn.className.includes('disabled') && !btn.disabled) {
          btn.click(); return true;
        }
      }
      return false;
    });
    if (ok) break;
    await page.waitForTimeout(400);
  }
  // 轮询验收（关键！点确认后可能要 1–4s 才写 preview）
  for (let i = 0; i < 10; i++) {
    await page.waitForTimeout(800);
    const st = await page.evaluate(() => {
      const dialogOpen = Array.from(document.querySelectorAll('.weui-desktop-dialog__title'))
        .some(el => (el.textContent || '').includes('编辑封面') && el.getBoundingClientRect().width > 50);
      const preview = document.querySelector('.js_cover_preview_new');
      const style = preview ? getComputedStyle(preview) : null;
      const bg = style ? style.backgroundImage : '';
      return {
        dialogOpen,
        display: style ? style.display : null,
        hasQpic: /mmbiz|qpic/.test(bg),
        bg: bg.slice(0, 120)
      };
    });
    if (st.hasQpic && st.display === 'block' && !st.dialogOpen) return { ok: true, st };
    if (st.dialogOpen) {
      // 再点一次确认，仍不要 Escape
      await page.evaluate(() => {
        for (const btn of document.querySelectorAll('button')) {
          if ((btn.textContent || '').trim() === '确认' && btn.className.includes('primary')
            && !btn.className.includes('disabled')) btn.click();
        }
      });
    }
  }
  return { ok: false };
}""")

# 步骤5：封面已生效后再保存草稿（此时才允许 Escape）
browser_run_code_unsafe("""async (page) => {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  await page.evaluate(() => {
    for (const btn of document.querySelectorAll('button')) {
      if ((btn.textContent || '').trim() === '保存为草稿' && btn.offsetParent) btn.click();
    }
  });
  await page.waitForTimeout(3000);
  const preview = document.querySelector('.js_cover_preview_new');
  const bg = preview ? getComputedStyle(preview).backgroundImage : '';
  return {
    appmsgid: page.url().includes('appmsgid='),
    coverOk: /mmbiz|qpic/.test(bg) && getComputedStyle(preview).display === 'block',
    bg: bg.slice(0, 160)
  };
}""")
```

**🔴 关键经验（v1.9.1 + v3.5.0 + v3.8.0 + v3.20.0）：**
1. **必须先「图片」→「本地上传」把封面图（横版 `horizontal-4-3.png`）插入正文**，「从正文选择」才可用  
2. **file chooser 不弹时**：`input[type=file][accept*=image].setInputFiles(path)` 可兜底  
3. **Hover 封面区**才出菜单；「从正文选择」用 **`.js_selectCoverFromContent` + 强制显示**  
4. **「图片上传中」弹窗会挡住保存**：等上传完 + Escape（仅此阶段）  
5. **封面失败不阻塞草稿**：标题/正文/原创/保存优先  
6. **保存成功判定**：`appmsgid=` 比「已保存」文案更稳  
7. **裁剪确认 =「确认」**；禁用点 disabled「确定」  
8. **验收 = preview `display:block` + `mmbiz` 背景**，勿被残留「拖拽或选择封面」文案误导  
9. **🔴 v3.26.0 保存后禁止重建**：`appmsgid=` 一旦出现即视为草稿已落盘。后续 snapshot 即使显示标题 `0/64`、正文「从这里开始写正文」、封面「拖拽或选择封面」，也**禁止**再点「新建」/再跑 Phase 12 全文注入。原因：编辑器 SPA 切 tab 或 snapshot 读到空壳，不等于草稿丢失（0901 实测 `appmsgid=100000882` 后空壳 UI，重建会重复稿）

#### 12.7b 从图片库选封面（v3.20.0 / 2026-08-23 W33 周报实测）

**适用场景**：封面图已提前上传到公众号素材库（如周报裁好的 `wechat-cover-2.35.png` 2.35:1 横图），想直接从图片库选，不再插正文。

**🔴 图片库选择器 DOM（踩坑要点）**：
1. 图片库弹窗是 `.weui-desktop-dialog`；图片**不是**直接渲染在 `.weui-desktop-img-picker__item` 上，**也不是 `<img>` 标签**——而是渲染在子元素 **`<i>`** 上，通过 **computed `backgroundImage: url("https://mmbiz.qpic.cn/...")`** 显示。
2. 旧探测（查 picker item 的 background 或找 `<img>`）会全部返回 `bg:"none"` / `hasImg:false`，误判「图库没图」。
3. **正确探测**：在 picker item 内 `querySelectorAll('i')`，找 `offsetParent!==null` 的 `i`，读 `getComputedStyle(iEl).backgroundImage`。
4. 缩略图统一渲染为 **110×110**，**无法从缩略图尺寸判断宽高比**——不能靠 thumbnail 尺寸挑封面；改用 URL 的 `mmbiz_png` / `mmbiz_jpg` 后缀或 `wx_fmt` 参数辅助区分（PNG 多为生成的封面图）。

**🔴 选图流程（无「确定」按钮，主按钮是「下一步」）**：
```
封面区 hover → 点「从图片库选择」开图库弹窗
  → 点左侧栏「上传 (N)」分组（.weui-desktop-menu__item），过滤到已上传图
  → 点目标缩略图选中（picker item 加 selected 态）
  → 点「下一步」（weui-desktop-btn_primary）—— 注意：此视图【没有】「确定」按钮
  → 进入裁剪/确认步骤 → 点「确认」（enabled，非 disabled「确定」）
  → 轮询 .js_cover_preview_new{display:block; bg 含 mmbiz} 验收
```

```js
// 探测图库当前分组的图（返回 url 列表 + 选中态）
async (page) => {
  return await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.weui-desktop-img-picker__item'));
    return items.map((el, idx) => {
      const iEl = Array.from(el.querySelectorAll('i')).find(i => i.offsetParent !== null);
      const bg = iEl ? getComputedStyle(iEl).backgroundImage : 'none';
      const m = bg.match(/url\(["']?(https:\/\/mmbiz[^"')]+)/);
      return { idx, url: m ? m[1] : '', selected: el.className.includes('selected') || el.getAttribute('aria-checked') === 'true' };
    }).filter(x => x.url);
  });
}

// 点「上传 (N)」分组过滤 → 选中目标图 → 点「下一步」
async (page) => {
  await page.evaluate(() => {
    for (const it of document.querySelectorAll('.weui-desktop-menu__item')) {
      if (/上传\s*\(/.test((it.textContent || '').trim())) { it.click(); return; }
    }
  });
  await page.waitForTimeout(800);
  // 选中第一个 PNG（生成封面通常为 PNG；按需改 idx）
  await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.weui-desktop-img-picker__item'));
    for (const el of items) {
      const iEl = Array.from(el.querySelectorAll('i')).find(i => i.offsetParent !== null);
      const bg = iEl ? getComputedStyle(iEl).backgroundImage : '';
      if (/mmbiz_png|wx_fmt=png/.test(bg)) { el.click(); return; }
    }
    if (items[0]) items[0].click();
  });
  await page.waitForTimeout(500);
  // 点「下一步」（此视图无「确定」按钮）
  await page.evaluate(() => {
    for (const btn of document.querySelectorAll('button')) {
      if ((btn.textContent || '').trim() === '下一步' && btn.className.includes('primary') && !btn.disabled) { btn.click(); return; }
    }
  });
  // 后续进入裁剪弹窗，按 12.7 的「确认 + 轮询 preview」流程收尾
}
```

**关键经验**：
- 图库缩略图 URL 形如 `https://mmbiz.qpic.cn/mmbiz_png/{prefix}/...?wx_fmt=png`；按 `mmbiz_png`/`mmbiz_jpg` 或 `wx_fmt` 区分格式，辅助定位生成的 PNG 封面。
- 「上传 (N)」分组的 N = 已上传图数量，点它过滤掉系统图，只剩自己上传的。
- 从图片库选完点「下一步」后，裁剪确认流程与 12.7「从正文选择」完全一致（「确认」非「确定」、轮询 preview）。

#### 12.7c 封面流程补充坑（v3.23.0 / 2026-08-29 日报实测，4 子坑）

1. **「从图片库选择」是 hover 弹出菜单**：封面区 hover 才出现，直接 `click()` 报 "element is not visible"。正确做法：`await page.mouse.move(coverBox.x, coverBox.y)`（evaluate 拿 `getBoundingClientRect()` 中心）触发 hover，再 evaluate 点可见链接。
2. **上传文件按钮被 `webuploader-pick` 内 `<label>` 拦截 pointer**：用 `Promise.all([page.waitForEvent('filechooser'), page.locator('.single_upload_btn_container, .webuploader-pick').first().click({force:true})])` + `fileChooser.setFiles([path])`。⚠️ **选择器勿用含点的动态 id**（`#upload_0.7739298874336278` 会被当 class 解析报 CSS 错误），用上面的 class 选择器。
3. **图库首击可能未选中**：点击后回读 `.weui-desktop-img-picker__item.selected` 类验证；无 selected 则 evaluate `items[0].click()` 再验（`className` 应变为 `weui-desktop-img-picker__item selected`）。
4. **2.35:1（消息列表）裁剪 radio 在视口外**：`page.locator(...).click()` 报 "element is outside of the viewport"——改 evaluate 点含 "2.35" 文本的 `label`/`span`，再点「确认」收尾（同 12.7 轮询 preview 验收）。

#### 12.8 设置原创声明（已验证 v1.9.1；🔴 v3.23.0 修正协议勾选行为）

**🔴 v3.23.0 / 2026-08-29 实测修正：「文字原创」默认选中，但「我已阅读并同意」协议 checkbox 并不会自动勾选**（实测 `checked:false`）——直接点「确定」是 no-op（弹窗不关）。必须先点协议 checkbox 的 **`closest('label')` 容器**（点 input 本体或文字 span 均可能不切换），验证 `checked === true` 后再点「确定」。

```
# 步骤1：点击「原创」区域打开弹窗
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent.trim() === '原创' && el.offsetParent !== null) {
        const rect = el.getBoundingClientRect();
        if (rect.y > 150 && rect.x > 500) {
          el.click();
          return;
        }
      }
    }
  });
  return 'clicked';
}""")

# 步骤2：等待弹窗出现
browser_wait_for(time=1)

# 步骤3：🔴 v3.23.0 实测——先勾选协议 checkbox（点 label 容器），验证 checked 后再点「确定」
browser_run_code_unsafe("""async (page) => {
  const r = await page.evaluate(() => {
    // 点「我已阅读并同意」所在 label 容器
    const inputs = document.querySelectorAll('input.weui-desktop-form__checkbox');
    for (const input of inputs) {
      const labelText = (input.closest('label')?.textContent || input.parentElement?.textContent || '');
      if (labelText.includes('阅读') || labelText.includes('同意')) {
        const target = input.closest('label') || input.parentElement;
        target.click();
        return `checkbox clicked, checked=${input.checked}`;
      }
    }
    return 'checkbox not found';
  });
  if (!r.includes('checked=true')) return `agree failed: ${r}`;
  await page.waitForTimeout(500);
  const r2 = await page.evaluate(() => {
    const btns = document.querySelectorAll('button');
    for (const btn of btns) {
      if (btn.textContent.trim() === '确定' && btn.offsetParent !== null) { btn.click(); return 'ok clicked'; }
    }
    return 'ok not found';
  });
  return `${r} | ${r2}`;
}""")

# 步骤4：验证成功标志 = 弹窗关闭 + 状态区出现「文字原创 · 已开启快捷转载」
browser_evaluate("""() => {
  const buttons = document.querySelectorAll('button, a');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '确定' && btn.offsetParent !== null) {
      btn.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")

# 步骤4：保存草稿
browser_evaluate("""() => {
  const buttons = document.querySelectorAll('button');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '保存为草稿' && btn.offsetParent !== null) {
      btn.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")
```

**关键经验（v1.9.1 验证；🔴 v3.23.0 / 2026-08-29 修正）：**
- 弹窗打开后「文字原创」已默认选中
- 🔴 「我已阅读并同意」checkbox **不会**自动勾选（实测 `checked:false`），必须点其 `closest('label')` 容器切换，验证 `checked === true` 后再点「确定」；直接点「确定」是 no-op
- 成功标志 = 弹窗关闭 + 原创状态区显示「文字原创 · 作者：… · 已开启快捷转载」
- 🔴 **v3.22.0 / 2026-08-28 实测**：「原创」标题实测在 `y=471`，旧条件 `rect.y < 400` 会**漏选**导致点不开弹窗；已去 y 上界改为 `rect.y > 150 && rect.x > 500`。优先用 `.setting-group__title` 文本 === '原创' 定位（`document.querySelectorAll('.setting-group__title')` 找文本「原创」的那个），比全 `*` 扫描 + y 范围更稳。
      }
    }
  });
  await page.waitForTimeout(2000);
  return 'original declaration set';
}""")
```

#### 12.9 设置赞赏（已验证 v1.9.1）

**🔴 弹窗打开后「赞赏作者」已选中，账户已填入，「我已阅读并同意」已勾选，直接点确定即可。**

```
# 步骤1：点击「赞赏」区域打开弹窗
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent.trim() === '赞赏' && el.offsetParent !== null) {
        const rect = el.getBoundingClientRect();
        if (rect.y > 300 && rect.y < 500 && rect.x > 500) {
          el.click();
          return;
        }
      }
    }
  });
  return 'clicked';
}""")

# 步骤2：等待弹窗出现
browser_wait_for(time=1)

# 步骤3：直接点击「确定」（弹窗已默认配置好）
browser_evaluate("""() => {
  const buttons = document.querySelectorAll('button, a');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '确定' && btn.offsetParent !== null) {
      btn.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")

# 步骤4：保存草稿
browser_evaluate("""() => {
  const buttons = document.querySelectorAll('button');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '保存为草稿' && btn.offsetParent !== null) {
      btn.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")
```

**关键经验（v1.9.1 验证）：**
- 弹窗打开后「赞赏作者」已默认选中
- 账户「Youngs羊示」已自动填入
- 「我已阅读并同意」checkbox 已默认勾选
- 直接点击「确定」即可，无需手动操作其他选项

#### 12.10 选择合集（已验证 v1.9.1）

**🔴 合集选择器是自定义 Vue 组件，必须用 Playwright locator 精确匹配：**

```
# 步骤1：点击「合集」→「未添加」打开弹窗
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent.trim() === '未添加' && el.offsetParent !== null) {
        const rect = el.getBoundingClientRect();
        if (rect.y > 400 && rect.y < 600 && rect.x > 600) {
          el.click();
          return;
        }
      }
    }
  });
  await page.waitForTimeout(1500);
  return 'dialog opened';
}""")

# 步骤2：点击输入框 focus（搜索关键词按 REPORT_MODE：daily「今日羊报」/ weekly「羊报AI周刊」/ monthly「羊报AI月报」）
browser_run_code_unsafe("""async (page) => {
  const input = page.getByRole('textbox', { name: '请选择合集' });
  await input.click();
  await page.waitForTimeout(500);
  await input.fill('今日羊报');
  await page.waitForTimeout(1000);
  return 'typed';
}""")
# 🔴 兜底（v3.22.0 / 2026-08-28 实测）：弹窗未开时 getByRole('textbox', {name:'请选择合集'}) 30s 超时。
# 须先 document.querySelector('.js_article_tags_content').scrollIntoView({block:'center'}) + click 开弹窗，
# 再用 page.locator('input[placeholder="请选择合集"]') 兜底定位输入框。

# 步骤3：hover 并点击选项（必须用 exact: true 精确匹配！合集名按 REPORT_MODE 从模式参数映射表读取）
browser_run_code_unsafe("""async (page) => {
  // daily 「今日羊报 AI」/ weekly 「羊报AI周刊」/ monthly 「羊报AI月报」
  const option = page.getByText('「今日羊报 AI」', { exact: true });
  await option.hover();
  await page.waitForTimeout(500);
  await option.click();
  await page.waitForTimeout(500);
  return 'clicked option';
}""")

# 步骤4：点击「确认」
browser_run_code_unsafe("""async (page) => {
  const confirmBtn = page.getByRole('button', { name: '确认' });
  await confirmBtn.click();
  await page.waitForTimeout(1000);
  return 'confirmed';
}""")
```

**关键经验（v1.9.1 验证）：**
1. **必须用 `page.getByText('「今日羊报 AI」', { exact: true })` 精确匹配**，否则会匹配到正文中的同名文本
2. **必须先 hover 再 click**，直接 click 可能不生效
3. **点击「确认」用 `page.getByRole('button', { name: '确认' })`**，不要用 JS evaluate

#### 12.11 保存草稿

**🔴 保存前必须处理弹窗（v3.3.0 更新）**：封面图上传后会弹出「图片上传中，请稍后」弹窗，阻挡保存按钮。必须先等待上传完成、关闭弹窗，再保存。

```
browser_run_code_unsafe("""async (page) => {
  // 等待上传完成（封面图可能需要10秒+）
  await page.waitForTimeout(10000);
  
  // 关闭可能的弹窗
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
  
  // 再等5秒确保上传完成
  await page.waitForTimeout(5000);
  
  // 保存草稿
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('button');
    for (const btn of buttons) {
      if (btn.textContent.trim() === '保存为草稿') {
        btn.click(); return;
      }
    }
  });
  await page.waitForTimeout(3000);
  
  // 验证保存成功
  const body = await page.evaluate(() => document.body.textContent);
  return body.includes('已保存') ? 'saved!' : 'URL: ' + page.url();
}""")
```

#### 微信公众号上传组件操作总结（v1.7.0 实测）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 标题 | **隐藏 `#title` TEXTAREA + 可见 `.ProseMirror` 代理** | 正文注入后 `.ProseMirror`.first() click → Ctrl/Meta+A → keyboard.type；回读 `#title.value`（禁 textContent 直写） | ✅ 高 |
| 作者 | 标准 input（≤8 字） | 原生 setter + dispatch `input`；固定 `羊报AI周刊`/`今日羊报AI`/`羊报AI月报`，勿填署名 | ✅ 高 |
| 正文 | **ProseMirror** | 🔴 v3.23.0 修正：`execCommand('insertHTML')`（直接 innerHTML 被静默清空） | ✅ 高 |
| 视频号 | 弹窗选择 | 工具栏「视频号」→ 选账号 → 选视频 → 插入 | ✅ 高 |
| 图片上传 | 工具栏菜单 | 「图片」→「本地上传」→ file_upload | ✅ 高 |
| 封面 | 拖拽区域 | 「从图片库选择」/ 「从正文选择」 | ⚠️ 需坐标点击（图库缩略图在子 `<i>` 的 backgroundImage，非 `<img>`）|
| 原创声明 | 弹窗 | 点击「原创」→ 确定 | ✅ 高 |
| 赞赏 | 弹窗 | 点击「赞赏」→ 不开启 → 勾选同意 → 确定 | ✅ 高 |
| 合集 | **自定义 Vue 组件** | 坐标点击下拉框 → 选择 → 确认 | ⚠️ 坐标方式 |
| 保存草稿 | 按钮 | `button:has-text("保存为草稿")` | ✅ 高 |

**关键经验**：
1. **公众号编辑器使用 ProseMirror**，不是 Quill，注入方式不同
2. **标题是隐藏 `#title` TEXTAREA + 可见 `.ProseMirror` 代理**（h=0，直接 click 超时）；页面两个 `.ProseMirror`：first()=标题代理、nth(1)=正文。标题填写永远放到正文注入之后（12.5b），回读 `#title.value`，禁 `textContent` 直写
3. **视频号插入是最可靠的视频方式**，通过工具栏「视频号」按钮 → 选择账号 → 选择视频 → 插入
4. **图片通过工具栏「图片」→「本地上传」插入**，会插入到正文光标位置
5. **「从正文选择」封面**：必须先通过工具栏上传图片到正文，然后用 `.js_selectCoverFromContent` class 选择器点击
6. **合集选择器是自定义 Vue 组件**，需要用坐标点击（约 x=730, y=355 点击「未添加」，x=690, y=375 打开下拉框）
7. **赞赏弹窗中「我已阅读并同意」需要手动勾选**，checkbox 在 `label > input[type="checkbox"]` 结构中
8. **原创声明弹窗默认选中「文字原创」，但协议 checkbox 不自动勾选**（🔴 v3.23.0 / 2026-08-29 实测 `checked:false`）——须点 checkbox 的 `closest('label')` 容器验证 `checked===true` 后再点确定
9. **保存草稿前不需要完成所有设置**，封面和合集可以后续手动添加
10. **新标签页打开**：点击「文章」会打开新标签页，需要切换到最新标签页

#### 12.3 填写作者（旧节，以 12.3 主节为准）

```javascript
// 作者是标准 input，≤8 字；周报固定「羊报AI周刊」，勿填「Youngs羊示」或署名格式
browser_click(target={作者输入框ref})
browser_type(target={作者输入框ref}, text="羊报AI周刊")
```

#### 12.4 填写正文

**🔴 v3.23.0 / 2026-08-29 实测修正：此节旧方案（直接 innerHTML）已被证伪**——赋值返回"ok"但编辑器立即回滚清空（pmLen=1）。**必须用 12.5 的 `execCommand('insertHTML')` 流程**（selectNodeContents + insertHTML + 回读字数验证），勿再使用本节的 dispatch input 方案。

#### 12.5 上传图片（复杂，建议手动）

**🔴 公众号图片上传机制特殊：**

1. 找到隐藏的 file input：`input[type="file"][accept*="image"]`
2. 用 `page.$('input[type="file"]').setInputFiles(path)` 设置文件
3. **但图片不会自动插入到文章中**，需要先定位光标位置

**推荐方案**：先保存草稿，然后手动在文章中定位光标 → 点击工具栏「图片」→「本地上传」→ 选择图片。

```javascript
// 如果要尝试自动上传（不保证成功）
browser_run_code_unsafe("""async (page) => {
  const fileInput = await page.$('input[type="file"][accept*="image"]');
  if (fileInput) {
    await fileInput.setInputFiles('/path/to/image.png');
    return 'file set';
  }
  return 'input not found';
}""")
```

#### 12.6 保存草稿

```javascript
browser_evaluate("""() => {
  const buttons = document.querySelectorAll('button, a, div');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '保存为草稿' && btn.offsetParent !== null) {
      btn.click();
      return 'saved';
    }
  }
  return 'not found';
}""")
```

#### 12.7 设置合集（困难，建议手动）

**🔴 公众号合集选择器是自定义 Vue/React 组件，自动化成功率低：**

```javascript
// 方法1：尝试点击「合集 未添加」行
browser_evaluate("""() => {
  const elements = document.querySelectorAll('*');
  for (const el of elements) {
    if (el.textContent.includes('合集') && el.textContent.includes('未添加') && el.offsetParent !== null) {
      el.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")

// 方法2：在弹出的对话框中选择合集
browser_click(target={下拉框ref})
browser_evaluate("""() => {
  const options = document.querySelectorAll('*');
  for (const opt of options) {
    if (opt.textContent.trim() === '「今日羊报 AI」' && opt.offsetParent !== null) {
      opt.click();
      return 'selected';
    }
  }
  return 'not found';
}""")

// 点击确认
browser_click(target={确认按钮ref})
```

**⚠️ 实测经验**：合集选择器的 JS click 经常不生效，可能需要手动完成。

#### 微信公众号上传组件操作总结（v1.5.0 实测）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 标题 | **隐藏 `#title` TEXTAREA + 可见 `.ProseMirror` 代理** | 正文注入后 `.ProseMirror`.first() click → Ctrl/Meta+A → keyboard.type；回读 `#title.value`（禁 textContent 直写） | ✅ 高 |
| 作者 | 标准 input（≤8 字） | 原生 setter + dispatch `input`；固定 `羊报AI周刊`/`今日羊报AI`/`羊报AI月报`，勿填署名 | ✅ 高 |
| 正文 | **ProseMirror** | 🔴 v3.23.0 修正：`execCommand('insertHTML')`（直接 innerHTML 被静默清空） | ✅ 高 |
| 图片上传 | **隐藏 file input** | `setInputFiles`（但不插入文章） | ⚠️ 需手动插入 |
| 封面 | 拖拽区域 | 需手动上传 | ❌ 建议手动 |
| 合集 | **自定义 Vue 组件** | JS click（不稳定） | ❌ 建议手动 |
| 保存草稿 | 按钮 | JS click | ✅ 高 |

**关键经验**：
1. **公众号编辑器使用 ProseMirror**，不是 Quill，注入方式不同
2. **标题是隐藏 `#title` TEXTAREA + 可见 `.ProseMirror` 代理**（h=0，直接 click 超时）；页面两个 `.ProseMirror`：first()=标题代理、nth(1)=正文。标题填写永远放到正文注入之后（12.5b），回读 `#title.value`，禁 `textContent` 直写
3. **图片上传到素材库成功，但不会自动插入文章**，需要手动定位光标后插入
4. **合集选择器是自定义 Vue 组件**，JS click 不稳定，建议手动
5. **保存草稿前不需要完成所有设置**，可以先保存再编辑

### Phase 13: 微信视频号自动上传（Playwright MCP）

**权限已在预授权阶段获得，直接执行。**

**🔴 重要经验（v3.24.0）：2026-08-30 版 UI 全部表单在 `wujie-app` open shadow root 内。进入发布页先跑 13.1 结构判定：`hasWujie=true` → 走 shadow 协议；仅当 `hasWujie=false` 且 `page.frames()` 有 `name="content"` 时才用旧 iframe 法。禁止一上来就 `page.frame({name:'content'})`。**

**🔴 v3.7.0 补充（2026-07-18）— 上传视频号「稳跑」协议**：
1. 优先 **MCP 单会话闭环**：打开 create → 上传 → 填描述/短标题 → 封面 → 存草稿 → 草稿箱验收；全过程避免另起独立 Playwright 抢 profile。
2. 若 MCP 在双 body 上已崩溃，再改用**独立脚本 + 同一 profile**，启动前 scoped `pkill` 仅杀该 profile。
3. 视频上传成功标志：出现「删除 / 重新上传 / 封面预览」，且「保存草稿」可点（非灰）。
4. 草稿验收：侧栏「草稿箱」条数 +1，标题含当日描述摘要与日期。
5. 封面 3:4 / 4:3：等 **「预览图生成中，请等待完成后再编辑」消失** 后再点对应「编辑」；DOM 可见 `input[accept*=image]` 在 `.single-cover-uploader-wrap`，但跨 frame 时 `setInputFiles` 易 detached——**已验证可用 CDP**：
   `DOM.performSearch` → `getSearchResults` → `describeNode` 过滤 image accept → `DOM.setFileInputFiles({ backendNodeId, files })`。
6. 竖封面文件必须**带日期**（如 `vertical-3-4.png` 含 `2026-07-18`）；生成失败勿用 scene 截图顶替。
7. 短标题 ≤16 中文字符（含空格）。格式：`{报刊名} {M月D日}` / `{报刊名} {M月D日至D日}`，纯报刊名+日期（如 `今日羊报AI 8月30日`），不加核心标题。禁 `.` `~`。

#### 13.0 结构判定（先 13.1 wujie，iframe 仅兜底）

**🔴 不要默认 iframe。** 先按 13.1 检测 `hasWujie`。仅当 `hasWujie=false` 且 `page.frames()` 含 `name="content"` 时，才用下面的旧 iframe 探测：

```javascript
// 仅 hasWujie=false 时检测 iframe 结构
browser_run_code_unsafe("""async (page) => {
  const frames = page.frames();
  const frameInfo = frames.map(f => ({ url: f.url().substring(0, 80), name: f.name() }));
  return JSON.stringify(frameInfo);
}""")
```

#### 13.0b 自主登录失败协议（v3.18.0 / 2026-08-18 实测）

`channels.weixin.qq.com` 会重定向到 `login.html`，QR iframe 来自 `open.weixin.qq.com`（**跨域**）。

**失败表现**：
- iframe 显示 **「加载失败，点击重试」**；点击重试 + 等 5s 仍不加载。
- 跨域 iframe **无法用 JS 访问**（`contentDocument` 为 null）。
- `page.reload` 1–2 次仍失败。

**🔴 v3.23.0 / 2026-08-29 升级为「复发模式」**：此失败已在 **2026-08-28 与 2026-08-29 连续两日**复现——「加载失败，点击重试」+ 重试无效，**非偶发**。标准止损流程（0829 已验证产出可用）：
1. 重试 **1 次**即放弃（勿多轮空转），标记 `channels: login_required`。
2. QR 截图落盘（如 `channels-login-{MMDD}.png`）供用户手动扫码。
3. `upload-status.md` 写 `⏭` + 「视频号待办」小节：列出 QR 截图路径 + 补跑 6 步清单（上传视频/封面 → 描述+短标题 → 合集 → 保存草稿），附双 body 铁律提示（单次 browser_run_code_unsafe + page.goto baidu 离开）。
4. Phase 13 结束，不阻塞其他平台。

**处理协议**（原始 v3.18.0，与上述复发协议合并使用）：
1. `page.reload` 1–2 次后仍失败 → 标记 `channels: login_required`。
2. 写 `upload-status.md` 为 `⏭`（跳过本平台），停止空转。
3. **明确**：自主流程无法完成视频号扫码登录，需用户手动扫码。Phase 13 结束并在 `upload-status.md` 注明「等待用户手动扫码后重跑」。

**🔴 v3.26.0 / 2026-09-01 补「QR 已加载仍需扫码」变体**：
`login.html` 上 QR **已成功加载**（console `qrcode loaded， duration: …`，截图可见「请使用微信扫描二维码登录」）**同样**走复发止损，**不要空等扫码、不要因 QR 可见就多轮 reload**。

与 v3.23.0「加载失败，点击重试」的区别：
- 本变体 QR 可见、iframe 未报加载失败；create URL 可能闪一下再 302 回 `login.html`。
- console 常见噪声**不是**继续重试的理由：
  - `网络错误，错误码：300334`
  - `fastLogin: false` / `fast_login: null`
  - `localhost.weixin.qq.com:14xxx/130xx/api/check-login` `ERR_CONNECTION_REFUSED`（微信桌面端 fast-login 探测端口，无桌面客户端时必然失败）
- Playwright `browser_snapshot` YAML 在 `login.html` 上可能为空 → **用截图判定**，勿因空 snapshot 再 reload。

**止损不变**：重试 1 次（navigate `/platform/post/create`）仍落 `login.html` → `channels: login_required` → QR 截图落盘（如 `channels-login-YYYY-MM-DD.png` + `channels-create-retry-YYYY-MM-DD.png`）→ `upload-status.md` 写 6 步补跑 → 不阻塞其他平台。

**常见 iframe 结构**：
- 主页面：`https://channels.weixin.qq.com/platform/post/...`
- 内容 iframe：`name="content"`, URL 包含 `/micro/content/post/...`

**仅 `hasWujie=false` 时**才用 `page.frame({ name: 'content' })`（`hasWujie=true` 时此调用拿不到表单）：
```javascript
browser_run_code_unsafe("""async (page) => {
  const frame = page.frame({ name: 'content' });
  if (!frame) return 'frame not found';
  const result = await frame.evaluate(() => {
    // 在 iframe 内操作 DOM（旧 UI 兜底）
    return document.querySelector('.some-class')?.textContent;
  });
  return result;
}""")
```

#### 13.1 🔴 wujie shadow DOM 全套操作协议（v3.24.0 / 2026-08-30 W35 实测，替代旧 iframe/坐标法）

**2026-08-30 版 UI：页面级 locator / 普通 evaluate / `page.frame({name:'content'})` 全部失效——页面 body 几乎为空（bodyLen≈81），全部表单内容渲染在 `wujie-app` 的 open shadow root 内。**

**结构判定**（进入发布页先做一次）：
```javascript
browser_run_code_unsafe("""async (page) => {
  return await page.evaluate(() => JSON.stringify({
    bodyLen: document.body.textContent.length,
    hasWujie: !!document.querySelector('wujie-app'),
    inShadow: document.querySelector('wujie-app')
      ? document.querySelector('wujie-app').shadowRoot.querySelectorAll('input,button,[contenteditable]').length
      : -1,
  }));
}""")
```
- `hasWujie=true` → 走本节 shadow 协议；旧 iframe 结构（`page.frames()` 有 `name="content"`）才用 13.6 的旧法。

**字段定位表（shadow root 内）**：

| 组件 | 定位与操作 |
|------|-----------|
| 视频上传 | `wujie-app input[type=file]`（`.ant-upload` 内）——**setInputFiles 直传 file input**，无需点「上传」按钮（filechooser 监听在 shadow 内不触发） |
| 封面上传 | `.single-cover-uploader-wrap input[type=file]`（Playwright CSS 可穿 open shadow，locator 直接 setInputFiles） |
| 描述 | `.input-editor`（contenteditable）——evaluate 内 `shadowRoot.querySelector` → dispatchEvent mousedown/click → focus → `page.keyboard.type` |
| 短标题 | `input[placeholder*="短标题"]`（**Vue 受控 input**，不是 contenteditable）——原生 setter 清空 + focus + `page.keyboard.type` |
| 合集 | 点「选择合集」→ `.option-item` 按「羊报AI周刊」前缀匹配点击 |
| 封面确认 | 封面弹窗内 `button.weui-desktop-btn_primary`「确认」（个人主页卡片 3:4 裁剪） |

**shadow 内 contenteditable / input 操作模板**：
```javascript
browser_run_code_unsafe("""async (page) => {
  // 描述：mousedown/click 激活 → focus → 逐字键入
  await page.evaluate(() => {
    const r = document.querySelector('wujie-app').shadowRoot;
    const ed = r.querySelector('.input-editor');
    ed.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
    ed.dispatchEvent(new MouseEvent('click', {bubbles: true}));
    ed.focus();
  });
  await page.keyboard.type('描述文本', {delay: 5});

  // 短标题：Vue 受控，须原生 value setter 清空再键入
  await page.evaluate(() => {
    const r = document.querySelector('wujie-app').shadowRoot;
    const inp = r.querySelector('input[placeholder*="短标题"]');
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(inp, '');
    inp.dispatchEvent(new Event('input', {bubbles: true}));
    inp.focus();
  });
  await page.keyboard.type('短标题文本', {delay: 5});
  return 'done';
}""")
```

**🔴 短标题硬约束（v3.24.0，Phase 13.4 补强）**：
- **≤16 字**（含空格）+ **特殊字符白名单**：仅 书名号/引号/冒号/加号/问号/百分号/摄氏度——`.` `~` 均被拒（实测 `8.24~8.30` 报「符号仅支持…」）
- 格式统一 **`{报刊名} {M月D日至D日}`**：日报 `今日羊报AI 8月30日`；周报 `羊报AI周刊 8月24日至30日`（16字 ✅；`8月24日~8月30日` 18字超限 ❌）；月报 `羊报AI月报 2026年8月`
- **超限/非法字符时「保存草稿」按钮 silent disabled**——无 toast、点击无反应。每次填完必须验证：
```javascript
// 回读 .error-title 可见错误项 + 保存按钮 disabled 状态
const r = document.querySelector('wujie-app').shadowRoot;
const errs = [...r.querySelectorAll('.error-title')]
  .filter(e => e.offsetParent !== null && e.textContent.trim());
const saveBtn = [...r.querySelectorAll('button')].find(b => b.textContent.includes('保存草稿'));
return JSON.stringify({errors: errs.map(e => e.textContent.trim()), saveDisabled: saveBtn?.disabled});
```

#### 13.1b 打开视频号发布页

```
# 直接导航到发布页（跳过首页）
browser_navigate("https://channels.weixin.qq.com/platform/post/create")

# 或从首页进入
browser_navigate("https://channels.weixin.qq.com/platform")
# 点击「发表视频」按钮
browser_run_code_unsafe("""async (page) => {
  const btn = page.getByRole('button', { name: '发表视频' });
  await btn.click();
  await page.waitForTimeout(3000);
  return 'clicked';
}""")
```

#### 13.2 上传视频

**🔴 `hasWujie=true`（当前默认）**：Playwright CSS 可穿 open shadow，直接 `setInputFiles` 到 `wujie-app input[type=file]`。filechooser 监听在 shadow 内**不触发**，勿点「上传」按钮。

```javascript
browser_run_code_unsafe("""async (page) => {
  const input = page.locator('wujie-app input[type=file]').first();
  await input.setInputFiles('news-pipeline/YYYY-MM-DD/video/【YYYY-MM-DD】*.mp4');
  return 'uploaded via wujie file input';
}""")
```

**仅 `hasWujie=false` 时**才用旧 filechooser 点击：

```
# 旧 UI：点击上传区域（+号按钮）触发 file chooser
browser_run_code_unsafe("""async (page) => {
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser', { timeout: 5000 }),
    page.locator('.finder-upload__add-btn, [class*="upload-btn"]').first().click({ force: true })
  ]);
  await fileChooser.setFiles('news-pipeline/YYYY-MM-DD/video/【YYYY-MM-DD】*.mp4');
  return 'uploaded';
}""")
```

# 等待上传完成（15MB 视频约需 10-15 秒）
browser_wait_for(time=15)

#### 13.3 填写视频描述

**🔴 按 13.1 shadow 协议操作 `.input-editor`（contenteditable）：mousedown/click 激活 → focus → `page.keyboard.type`。** 仅当页面仍是旧 iframe 结构时才用旧坐标法（坐标点击 + keyboard.type）。

#### 13.4 填写短标题

**🔴 按 13.1 shadow 协议操作 `input[placeholder*="短标题"]`（Vue 受控 input，原生 setter 清空 + focus + keyboard.type）。**

**短标题限制**：最多 **16 字**（含空格），超过会报「标题超过16字限制」。
**短标题格式**：`{报刊名} {M月D日至D日}`，纯报刊名+日期，不加核心标题/副标题。
- 日报：`今日羊报AI 8月30日`
- 周报：`羊报AI周刊 8月24日至30日`（🔴 用「至」连接，勿用 `~`/`.`——特殊字符白名单禁 `.` `~`；`8月24日~8月30日` 同时 18 字超限）
- 月报：`羊报AI月报 2026年8月`

**字符白名单**：符号仅支持书名号、引号、冒号、加号、问号、百分号、摄氏度。逗号可用空格代替。
**🔴 违规后果**：保存草稿按钮 **silent disabled**（无 toast、点击无反应）——填完必须按 13.1 的 `.error-title` + `button.disabled` 双验证。

#### 13.5 选择合集

按 13.1 shadow 协议：点「选择合集」→ 等下拉展开 → evaluate 内在 shadowRoot 找 `.option-item`，按「羊报AI周刊」前缀匹配点击（勿硬编码全名，防大小写差异）。仅旧 iframe 结构时才用坐标法。

#### 13.6 上传封面（shadow 协议优先）

**🔴 `hasWujie=true`（当前默认）**：按 13.1 字段表操作——`.single-cover-uploader-wrap input[type=file]` `setInputFiles` → 弹窗 `button.weui-desktop-btn_primary`「确认」。短标题走 13.4 Vue input，**不是** `.edit-shorttitle-content`。

**封面尺寸**：
- 个人主页卡片：3:4（1152×1536）→ `vertical-3-4.png`
- 分享卡片：4:3（1536×1152）→ `horizontal-4-3.png`

##### 13.6.1–13.6.3 旧 iframe 兜底（仅 `hasWujie=false`）

旧 UI 才检测 `name="content"` iframe、点 `.edit-btn` 触发 filechooser、以及 `.edit-shorttitle-content` contenteditable。**2026-08-30 版禁止当主路径**——短标题已是 Vue 受控 `input[placeholder*="短标题"]`，`textContent` 直写无效。旧示例标题 `今日羊报AI 2026年8月1日` 也已过期，改用 13.4 的 `M月D日` / `M月D日至D日`。

#### 13.7 保存草稿（不发布）

**🔴 保存成功无跳转、无可见 toast（textContent 长度也不变）——不能以 URL 变化判成败，必须去草稿箱列表页数条目验证（v3.24.0 实测）。**

**保存前两道拦截检查**：
1. **🔴 表单错误检查**（短标题超限/非法字符时按钮 silent disabled）：按 13.1 回读 `.error-title` 可见项 + 保存按钮 `disabled` 状态，有错误先修复再保存。
2. **🔴 「编辑个人主页卡片」弹窗拦截**：封面操作后此弹窗可能残留，点保存会被吞——点弹窗内 primary「确认」关弹窗后再保存。

```javascript
browser_run_code_unsafe("""async (page) => {
  // shadow 协议（wujie 结构）：
  await page.evaluate(() => {
    const r = document.querySelector('wujie-app').shadowRoot;
    const btn = [...r.querySelectorAll('button')].find(b => b.textContent.includes('保存草稿'));
    if (btn.disabled) return 'DISABLED: check .error-title';
    btn.click();
  });
  await page.waitForTimeout(3000);
  return 'clicked save';
}""")
// 旧 iframe 结构：page.frame({name:'content'}) 内点「保存草稿」，其余同
```

**草稿落库验收（强制）**：
- 🔴 **正确草稿箱 URL：`/platform/post/draftListManager`**（侧栏入口：**外层 body** 的「内容管理」→「草稿箱」；`post/record?tab=draft` 会 302 到别处，勿用）
- 导航后数草稿条目 / 找当日标题关键词（如「羊报AI周刊 8月24日至30日」）——条目出现即 ✅；反复点击保存无反应时先回 13.1 查 `.error-title`/`disabled`，勿空转
- beforeunload 弹窗：`browser_handle_dialog(accept=true)`；瞬时弹窗可能自愈（handle_dialog 报 no modal state 时直接继续）

#### 视频号上传组件操作总结（v3.24.0 更新）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 视频上传 | file input（shadow 内） | `wujie-app input[type=file]` setInputFiles 直传 | ✅ 高 |
| 视频描述 | **shadow 内 contenteditable** | shadowRoot.querySelector `.input-editor` → focus → keyboard.type | ✅ 高 |
| 短标题 | **shadow 内 Vue 受控 input** | 原生 setter 清空 + focus + keyboard.type（≤16字+白名单） | ✅ 高 |
| 位置 | 下拉框 | 已有默认值，一般不需改 | ✅ 高 |
| 合集 | 自定义下拉（shadow 内） | 「选择合集」→ `.option-item` 前缀匹配 | ✅ 高 |
| 封面上传 | `.single-cover-uploader-wrap input[type=file]` | setInputFiles → 3:4 裁剪弹窗 `weui-desktop-btn_primary` 确认 | ✅ 高 |
| 保存草稿 | shadow 内按钮 | 无错误 + 无弹窗拦截后点击；**无跳转无 toast** | ⚠️ 须草稿箱数条目验收 |

**关键经验**：
1. **🔴 wujie shadow DOM（2026-08-30 版 UI）**：全部表单在 `wujie-app` shadowRoot 内，页面级 locator/普通 evaluate/iframe 法失效；Playwright CSS 可穿 open shadow（file input 类），contenteditable/受控 input 须 evaluate 内 shadowRoot.querySelector + 事件派发（见 13.1 协议表）
2. **🔴 短标题 = Vue 受控 input**（不是 contenteditable）——textContent 直改无效，须原生 value setter
3. **🔴 短标题 ≤16 字 + 特殊字符白名单**（`.` `~` 禁用），违规时保存按钮 silent disabled
4. **🔴 保存成功无跳转无 toast**——验收只能去 `/platform/post/draftListManager` 数条目
5. **「编辑个人主页卡片」弹窗**未关会吞保存点击，先点确认关弹窗
6. **视频号支持两种封面比例**：3:4（个人主页卡片）和 4:3（分享卡片）
7. 旧 iframe 结构（`page.frame({name:'content'})`）仅当 13.1 结构判定 `hasWujie=false` 时才使用

## 目录结构

```
news-pipeline/
├── YYYY-MM-DD/                 # 按日期隔离的产出目录（daily）
│   ├── scripts/                # 视频脚本
│   ├── storyboards/            # 分镜表
│   ├── prompts/                # 图片 Prompt JSON
│   ├── images/                 # 生成的图片 (scene1.png ~ sceneN.png)
│   ├── voiceover/              # TTS 音频 (scene1.wav ~ sceneN.wav)
│   ├── captions/               # 字幕 JSON
│   ├── video/                  # 最终视频
│   │   └── 【YYYY-MM-DD】*.mp4
│   ├── horizontal-4-3.png        # 4:3 横版封面（B站/通用）
│   ├── vertical-3-4.png # 3:4 竖版封面（抖音/视频号/公众号）
│   ├── publish.json            # 多平台发布信息
│   ├── wechat-article-*.md     # 公众号图文
│   └── wechat-images/          # 公众号配图
├── weekly/                     # 周报产出目录（weekly，按日期范围隔离）
│   └── YYYY-MM-DD~YYYY-MM-DD/
│       └── （同 daily 子结构，视频 【羊报AI周刊】*.mp4，封面 horizontal-4-3.png）
├── monthly/                    # 月报产出目录（monthly，按月隔离）
│   └── YYYY-MM/
│       ├── scripts/            # 月报视频脚本（8-9段：Hook+4趋势+总结+展望+CTA）
│       ├── storyboards/        # 分镜表
│       ├── prompts/            # 图片 Prompt JSON
│       ├── images/             # 生成的图片
│       ├── voiceover/          # TTS 音频
│       ├── captions/           # 字幕 JSON
│       ├── video/
│       │   └── 【羊报AI月报】*.mp4
│       ├── horizontal-4-3.png    # 4:3 横版封面（B站/通用）
│       ├── vertical-3-4.png # 3:4 竖版封面（抖音/视频号/公众号）
│       ├── publish.json        # 多平台发布信息（月报变体：tags 含 AI月报）
│       ├── wechat-article-YYYY-MM.md   # 公众号图文（月报变体）
│       └── wechat-images/      # 公众号配图
├── video-project/              # Remotion 项目 (固定复用)
│   ├── public/
│   │   ├── images/             # 当期图片（复制）
│   │   ├── voiceover/          # 当期音频（复制）
│   │   └── captions.json       # 当期字幕（复制）
│   └── src/
│       ├── Composition.tsx     # 场景配置
│       ├── Root.tsx            # 总时长
│       └── components/
│           ├── Subtitles.tsx   # 字幕组件
│           └── NewsTitle.tsx   # 标题组件
└── sources/                    # 原始日报 Markdown
```

**月报输入**：`data/monthly/{YYYY-MM}.md`（项目根 data 目录，由 linuxdo-daily v13 生成，**不在 news-pipeline 下**）。

## 已知坑与经验教训

### 🔴 字幕与音频不同步（v2.0.0 → v2.1.0 → v2.2.0 → v2.3.0 → v3.25.0 演进）

**问题**：字幕时间轴与音频不齐——越到后面偏差越大，或某场景整体错位、口播与字幕对不上。**v3.25.0 再修切行**：时间轴对齐了，但切行把专名/动宾切开，出现 0.5s 闪行。

**v2.0.0 方案（已废弃）**：FunASR 语音识别 + ffprobe 比例调整
- FunASR 对专业术语识别极差：GPT→GDP、DeepSeek→Deep triep、Claude Code→Claude coat、Fable-5→核酸efbo杠五、Codex→搞dex、Hermes→HMMI、MiMo→mini/明末
- 修正字典永远追不上新术语，每次都要手动添加大量修正规则
- 识别错误导致字幕内容完全不可用

**v2.1.0 方案（已废弃）**：原始脚本文本 + ffprobe 纯字符比例对齐
- 解决了内容准确性问题（100% 用原始文本），但内部切分仍按纯字符数，长句/多数字场景仍会漂移

**v2.2.0 方案（已废弃）**：原始脚本文本 + 加权字符估算 + silencedetect 真实停顿点吸附
- 加权系数（中文 1.0 / 数字 0.6 / 英文 0.35）是平均拟合，含大量版本号/英文术语的单句偏差大
- silencedetect 只在「正好有停顿」时吸附边界，无停顿句仍纯估算，中后段仍逐句累积漂移

**v2.3.0 方案（时间轴仍有效；切行已废弃，2026-08-23 W33 周报实测）**：faster-whisper 词级时间戳 + 脚本字符强制对齐（旧 `gen_captions_v2.py`）
```python
# 1. 字幕文字：直接用 Phase 2 原始 TTS 脚本文本（内容 100% 准确，不依赖 ASR）
# 2. 时间锚：faster-whisper(word_timestamps=True) 跑 public/voiceover/sceneN.wav
# 3. 强制对齐：difflib.SequenceMatcher(脚本归一化字符, whisper 归一化字符)
# 4. 按句聚合：首句 start=0，末句 end=场景 ffprobe 时长；场景间累加偏移
#    ↑ 切行器已废弃：split_sentences 把 ，。；！？：、 所有标点一视同仁
```

**v3.25.0 方案（当前默认，2026-08-31 月报实测）**：语义 `group_caps` 先切行 + whisper 词级对齐（`templates/gen_captions.py`）
```python
# 1. 切行：jieba + group_caps（SENT_END 强制断；SOFT_PUNCT 仅 ≥max_len=16 才断；
#    允许略超 16 至 hard_max=20；超 hard_max 黄金分割 40–60% → WEAK_BEFORE → 整句保留）
#    禁止按字符下标硬切；GLUE_TAILS / BAD_ENDS+BAD_STARTS 粘合禁切结构
# 2. 时间锚：faster-whisper(word_timestamps=True) 跑当期 wav（WhisperModel 在 --dry-run return 之后才 import）
# 3. 对齐：每条字幕 SequenceMatcher 滑动窗口对齐到词级时间戳
# 4. merge_short_dwell(min_sec=1.0)：<1s 并回上一行
```

**新坑（2026-08 月报）**：v2.3.0 逐标点切行 + 16 字硬墙会切开专名/动宾：
- `延期；`（3 字 0.5s 闪行）
- `有效` / `主题近一万。`
- `终止Cursor` / `官方直连`、`硬新闻` / `主轴`、`稳` / `不稳`

**关键点**：
- **切行先于对齐**：`group_caps` 产出字幕字符串；whisper **只**负责时间轴
- **内容用原始脚本文本**，不需要 ASR 识别文字，字幕内容 100% 准确
- **时间用音频真实发音时刻**：whisper 词级时间戳是唯一锚点，不再「估算每句时长」
- **SequenceMatcher 容忍 ASR 错字**，单句偏差不累积
- **必须用 ffprobe 校验总时长对齐**（见 Step 8.3 校验）
- Remotion 字幕 **单行**，不做双行长度平衡

**Why:** 任何「估算每句时长」的方案都无法消除单句偏差累积（v2.3.0 已修时间轴）；但所有标点一视同仁 + 16 字硬墙会切开专名/动宾，必须语义切行。
**How to apply:** Phase 7 用 `templates/gen_captions.py`（`group_caps` + whisper），先 `--dry-run` 扫禁切反例。禁止逐标点切行、禁止按字硬切、禁止回退纯比例时间轴。旧 `gen_captions_v2.py` / `split_sentences` 已废弃作切行器。

### 🔴 旧音频残留导致整体 desync（v3.20.0 / 2026-08-23 W33 周报实测）

**问题**：重新渲染后字幕与音频仍整体对不上，且视频时长与脚本预期不符。

**根因（三重叠加）**：
1. **stale 音频**：`public/voiceover/sceneN.wav` 是上一期（日报）残留的旧音频，没被当期周报源音频覆盖；atempo 加速的是旧音频。
2. **stale 时长**：`Composition.tsx` 的 `sceneConfig.duration` + `Root.tsx` 的 `TOTAL_DURATION_SEC` 还是旧音频的时长，没随新音频刷新。
3. **v1 字幕估算器**：旧字幕用加权字符估算，本身就会漂移。

**修复链（必须按序，缺一步仍 desync）**：
1. **归档旧音频**：把 `public/voiceover/` 下的旧 wav 移到 `.stale_archive/` 子目录（用 Python `shutil.move`；**`rm` 会被自动权限模式判定为「不可逆本地删除」而拒绝**，改用归档挪移）。
2. **重新 atempo**：用当期周报源音频重新 atempo（scene1-5,7 atempo=1.25；锚点 scene6 atempo=1.4）→ 覆盖写入 `public/voiceover/sceneN.wav`。
3. **刷新时长**：ffprobe 实测每个新 wav → 同步刷新 `Composition.tsx` 的 `sceneConfig.duration` + `Root.tsx` 的 `TOTAL_DURATION_SEC`。
4. **重算字幕**：跑 `templates/gen_captions.py`（或当期 `scripts/gen_captions.py`：`group_caps` + whisper）→ 覆盖 `captions/captions.json` + `video-project/public/captions.json`。
5. **重新渲染**：`npx remotion render`。
6. **whisper 验证**：在视频里抽 3–4 个边界点（场景切点 / 长句起止），用 whisper 听对应音频段，确认字幕 startMs/endMs 与真实发音时刻一致（误差 < 200ms）。

**Why:** 旧音频 + 旧时长 + 旧字幕三者来自不同批次，三条时间轴互相错位；必须让音频/时长/字幕三者来自同一批新音频。
**How to apply:** 每次重跑 TTS 或换期前，先确认 `public/voiceover/` 是当期音频（看 mtime / 听内容），再走「atempo → 刷新时长 → templates/gen_captions.py → 渲染 → 验证」全链。`rm` 被拒时用 `shutil.move` 归档，不要硬删。

### 🔴 TTS 并发冲突
**问题**：`mimo-tts.sh` 内部使用 `mktemp /tmp/mimo-tts-request-XXXXXX.json` 生成临时文件。并行调用时多个进程竞争同一文件名，导致 `mktemp: mkstemp failed: File exists` 错误，TTS 静默失败不生成音频。

**解决**：**必须逐场景串行执行 TTS**，每个场景等待上一个完成后再启动下一个。

### 🔴 日报内容重复
**问题**：linux.do 日报中大量事件会连续多天出现（如 OpenAI 举报、Codex 额度等），直接制作视频会导致内容与前几期高度重复。

**解决**：Phase 1 中增加去重步骤，读取前 3 天日报对比，标记重复事件并展示给用户确认。

### 🔴 B站自定义下拉框
**问题**：B站的创作声明、合集选择器等使用自定义下拉框组件（bcc-select），不是标准 HTML `<select>`。`browser_click(listitem=...)` 或 `browser_click(element=文本)` 经常失败。

**解决**：先用 `browser_click` 打开下拉框，然后用 `browser_evaluate` + JS 遍历 DOM 找到选项并点击。

### 🔴 B站 Quill 编辑器
**问题**：B站简介使用 Quill 富文本编辑器，`browser_type` 无法直接输入内容。

**解决**：用 `browser_evaluate` 注入 `innerHTML` 到 `.ql-editor`，然后 dispatch `input` 事件。

### 🔴 B站上传 502/400 错误（v3.2.0 新增，2026-07-04）

**问题**：B站上传视频时，preupload 接口返回 502 Bad Gateway 或 400 Bad Request 错误，视频无法上传成功。Console 显示 `preupload接口失败` 和 `probe timeout`。

**原因**：B站服务器端问题，不是客户端或文件问题。可能是 B站 CDN 节点故障、上传接口限流、或临时维护。

**解决**：
1. 等待一段时间后重试（可能是临时故障）
2. 如果持续失败，提示用户手动上传到 B站
3. 视频文件已生成在 `news-pipeline/YYYY-MM-DD/video/` 目录，用户可直接拖拽上传

**Why:** B站上传接口不稳定，502/400 错误是服务器端问题，无法通过客户端修复
**How to apply:** Phase 11 B站上传失败时，不要反复重试，直接提示用户手动上传

### 🔴 B站上传文件路径中文字符问题（v3.2.0 新增，2026-07-04）

**问题**：视频文件名包含中文字符（如 `【2026-08-13】阿里禁用Claude...| 今日羊报AI.mp4`）时，B站上传接口返回 400 Bad Request 错误。

**原因**：B站上传接口对文件名中的中文字符处理有问题，可能导致 URL 编码错误。

**解决**：
1. 上传前将视频复制到简单路径（如 `/tmp/upload.mp4` 或 `news-pipeline/YYYY-MM-DD/video/upload.mp4`）
2. 使用简单文件名上传，上传成功后 B站会自动使用视频标题作为文件名

```bash
# 复制视频到简单路径
cp "news-pipeline/YYYY-MM-DD/video/【YYYY-MM-DD】*.mp4" \
   "news-pipeline/YYYY-MM-DD/video/upload-YYYY-MM-DD.mp4"
```

**Why:** B站上传接口对中文文件名兼容性差
**How to apply:** Phase 11 B站上传前，先复制视频到简单路径再上传

### 🔴 B站简介数字检测误判（v2.9.0 新增，2026-06-24）
**问题**：B站简介中包含大量数字（如 `21天37TB`、`2.5`、`2.1 Pro`、`4.6`、`5.6`、`5.2`）会被系统检测为「违规推广内容」（疑似QQ号/微信号），稿件直接被移除。

**解决**：B站简介必须减少数字密度：
- 版本号去掉或简化：`Seedance 2.5` → `Seedance`、`豆包2.1 Pro` → `豆包新模型`、`Opus 4.6` → `Opus`
- 数量用中文替代：`21天` → `二十一天`、`30秒` → `三十秒`、`37TB` → 不写具体数字
- 不要在简介区放 `#标签`（B站简介区的 hashtag 也容易触发检测）
- 结尾用频道引导语替代 hashtag：`今日羊报AI，每天带你速览AI圈最热新闻。`

**示例（安全版简介）**：
```
Codex后台疯狂写日志，SSD直接被写报废！

字节火山引擎大会连放大招，Seedance一次生成三十秒四K短片，豆包新模型编码能力对标Opus，特斯拉中国要用豆包。GPT新版本因Anthropic举报可能延期。GLM新版本实测好评，智谱市值破万亿。微信内测AI助手帮你操作微信。

今日羊报AI，每天带你速览AI圈最热新闻。
```

**Why:** B站的反垃圾系统对连续数字串非常敏感，`213756` 这样的模式会被误判为联系方式
**How to apply:** Phase 10 生成 B站简介时，自动将版本号简化、数字用中文替代、去掉 hashtag 行

#### 🔴 月报简介数字中文化（v3.1.0 新增，强制执行）

**问题**：月报数据天然大量数字（`6709` 主题、`28/30` 天、`1698` 峰值、`303` 日均、`52.6k` 浏览、`9650亿` 估值、`GPT-5.5/5.6`、`GLM-5.2`、`Opus 4.8` 等），密度是日报的数十倍。按 v2.9.0 规则只简化零星版本号远远不够，月报简介几乎必触发 B站违规推广检测。

**强制规则**：
1. 月报简介**禁止出现任何阿拉伯数字**（0-9），一律中文数字替代。包括浏览量、主题数、天数、token 数、估值、定价、版本号。
2. 大数模糊量化，避免连续数字串：`6709 → 近七千`、`6860 → 不写`、`1698 → 近一千七`、`303.1 → 三百出头`、`52.6k → 五万多`、`17.6k → 近一万八`、`9650亿 → 近万亿`、`70亿美元 → 数十亿美元`。
3. 天数/占比中文：`28/30 天 → 三十天里二十八天有数据`。
4. token 数模糊：`272k/353k → 近三十万token`、`516 → 五百多`。
5. 定价不写具体：`8/28元每百万Token → 几块钱`。
6. 版本号一律去数字：`GPT-5.5/5.6 → GPT新版本`、`gpt-5.6-sol → GPT最新灰度版`、`GLM-5.2 → GLM新版本`、`Opus 4.8 → Opus`、`Sonnet 4.6 → Sonnet`。
7. 该规则对月报**强制执行**，不得以"这个数字看起来安全"为由保留阿拉伯数字。

**月报安全版简介示例**（对照 v2.9.0 日报示例）：
```
本月AI圈月度盘点：OpenAI的GPT新版本调度全程翻车，二验风暴连夜取消，月末灰度版连续重置额度；智谱GLM新版本开源并登顶设计榜，国产模型集中爆发；Anthropic提交招股书估值近万亿，但服务中断、Mythos反复关闭；AI编程工具百花齐放。

本月三十天里二十八天有数据，日均新增主题三百出头，峰值近一千七。

羊报AI月报，每月带你回顾AI圈整月风向。
```

**Why:** 月报数据密度是日报的数十倍，不中文化几乎必触发 B站违规推广检测，稿件直接被移除。
**How to apply:** 月报模式 Phase 10 生成 B站简介时强制全数字中文化；月报脚本正文同样适用（避免字幕里出现连续数字串）。

### 🔴 TTS API 多节点故障转移（v2.9.0 新增，2026-06-24）
**问题**：MiMo TTS API 主节点（token-plan-cn.xiaomimimo.com）配额用完后返回 `quota exhausted` (429)。

**解决**：支持多节点故障转移：
1. 主节点 CN：`https://token-plan-cn.xiaomimimo.com/v1/chat/completions`
2. 备用节点 AMS：`https://token-plan-ams.xiaomimimo.com/v1/chat/completions`（2026-06-24 验证可用）
3. 如果主节点返回 429，自动切换到备用节点

**TTS API URL 修正**：settings.json 中的 `MIMO_TTS_API_URL` 可能包含 `/anthropic` 后缀，必须去掉再拼接 `/v1/chat/completions`：
```python
url = settings['MIMO_TTS_API_URL']
if url.endswith('/anthropic'):
    url = url[:-len('/anthropic')]
url = url.rstrip('/') + '/v1/chat/completions'
```

**Why:** 不同节点的配额是独立的，CN 节点用完后 AMS 节点可能还有余额
**How to apply:** Phase 6 TTS 生成时，先尝试主节点，429 错误自动切换备用节点

### 🟡 voiceover-texts.json 引号问题（v2.9.0 新增，2026-06-24）
**问题**：脚本中的中文引号（如 `"吃"硬盘`、`"卡脖子"`、`"小微"`）在 JSON 文件中会导致解析失败，因为 `"` 字符与 JSON 字符串分隔符冲突。

**解决**：生成 voiceover-texts.json 时：
- 将中文引号替换为无引号：`"吃"硬盘` → `吃硬盘`
- 或使用中文书名号：`「吃」硬盘`
- 生成后立即用 `python3 -c "import json; json.load(open(...))"` 验证

**Why:** Write 工具直接写入的文件中，中文引号 `""` 可能被转义为 ASCII `""` 导致 JSON 无效
**How to apply:** Phase 2 生成脚本后，保存 voiceover-texts.json 时自动处理引号，保存后立即验证

### 🟡 公众号 ProseMirror 编辑器索引（v2.9.0 更新，2026-06-24）
**问题**：公众号编辑器中 `document.querySelectorAll('.ProseMirror')` 只返回标题编辑器（index 0），正文编辑器需要用 `document.querySelectorAll('[contenteditable="true"]')` 获取，且正文在 index 2（不是 index 1）。

**正确索引**：
```javascript
const editables = document.querySelectorAll('[contenteditable="true"]');
// index 0: 标题（ProseMirror，placeholder="请在这里输入标题"）
// index 1: 原创声明输入框（original_primary_tips_input）
// index 2: 正文（ProseMirror ProseMirror-focused）
const titleEditor = editables[0];
const bodyEditor = editables[2];  // 不是 index 1！
```

**Why:** `.ProseMirror` 选择器可能只匹配部分编辑器，`[contenteditable="true"]` 更全面
**How to apply:** Phase 14 公众号上传时，用 `[contenteditable="true"]` 获取所有编辑器，正文在 index 2

### 🟡 抖音标题 fill() 方法（v2.9.0 新增，2026-06-24）
**问题**：抖音作品描述输入框用 JS `input.value = '...'` + `dispatchEvent('input')` 不生效，页面显示 0/30 字。

**解决**：使用 Playwright 的 `fill()` 方法：
```javascript
const titleInput = page.getByRole('textbox', { name: '填写作品标题，为作品获得更多流量' });
await titleInput.fill('代码偷吃SSD+豆包对标Opus｜今日羊报AI');
```

**Why:** 抖音的输入框使用 React 受控组件，直接修改 `value` 属性不会触发 React 的状态更新
**How to apply:** Phase 12 抖音上传时，标题用 `fill()` 而非 JS `value` 赋值
**问题**：不同用户可能使用不同的图片生成 API 服务，不能硬编码 API URL。

**解决**：Phase 0 中向用户收集 API URL + Key，优先使用用户提供的 API。

### 🟡 视频时长控制
**问题**：TTS 实际时长可能与脚本预估偏差较大（如 18s 预估实际生成 25-28s），导致总时长超出预期。

**解决**：脚本生成时保守预估，Phase 8 校验时以 TTS 实际时长为准。目标 60-120s，可适当放宽到 150s。

### 🟡 browser_click 文本匹配不稳定
**问题**：`browser_click(element=文本描述)` 有时会匹配到错误的元素（如匹配到侧边栏而非表单区域）。

**解决**：优先使用 `browser_click(target=ref编号)` 精确匹配。如果需要文本匹配，先 `browser_snapshot` 获取 ref 编号，再用 ref 点击。

### 🔴 微信公众号 ProseMirror 编辑器
**问题**：公众号标题和正文都使用 ProseMirror 编辑器（不是 Quill），`browser_type` 无法直接输入内容。

**解决**：用 `browser_evaluate` 注入内容：
- 标题：`editors[0].textContent = '标题'` + dispatch `input` 事件
- 🔴 v3.23.0 修正：正文禁直接 `innerHTML`（被静默清空）→ `execCommand('insertHTML')`（见 Phase 12.5）

### 🔴 微信公众号图片插入
**问题**：通过 `setInputFiles` 可以将图片上传到素材库，但图片不会自动插入到文章正文中。需要先在文章中定位光标，然后通过工具栏「图片」→「本地上传」手动插入。

**解决**：建议先保存草稿，然后手动完成图片插入。或者尝试：
1. 在文章中点击定位光标
2. 点击工具栏「图片」
3. 选择「本地上传」
4. 通过 `setInputFiles` 上传

### 🔴 微信公众号合集选择器
**问题**：公众号合集选择器是自定义 Vue/React 组件，不是标准 HTML 元素。JS click 不稳定，有时选择后不生效。

**解决**：建议手动完成合集选择。如果要尝试自动化：
1. 点击「合集 未添加」行打开对话框
2. 点击下拉框
3. 用 JS evaluate 找到并点击选项
4. 点击「确认」
5. 保存草稿后检查是否生效

### 🟡 微信公众号多标签页
**问题**：点击「文章」会打开多个新标签页（可能重复点击导致）。

**解决**：创建文章后，切换到最新标签页（index 最大的）。关闭其他重复标签页。

### 🔴 公众号封面上传正确流程（v1.9.1 / v3.7.0 / **v3.8.0 2026-07-19 闭环**）
**问题**：坐标点击、innerHTML 注入不可靠；弹窗缩略图常为 **background-image 的 span**，不是 `<img>`；裁剪页有 **disabled「确定」** 干扰；过早 Escape 会取消裁剪。

**已验证的正确流程（优先「从正文选择」）**：
1. Focus 正文：`.ProseMirror` 第二个
2. 工具栏「图片」→「本地上传」→ `setInputFiles(horizontal-4-3.png)`（横版封面）→ 等 8s → Escape 关上传挡层
3. `#js_cover_area` scrollIntoView → **hover** `.js_cover_btn_area`
4. **强制显示**后点 **`.js_selectCoverFromContent`**
5. 点带 `mmbiz` 背景的 **`.appmsg_content_img_item`** → **「下一步」**
6. 等待弹窗标题 **「编辑封面」** → 点 **enabled「确认」**（`weui-desktop-btn_primary` 且非 disabled）
7. **轮询**：`dialogOpen=false` 且 `.js_cover_preview_new{display:block; background-image: url(...mmbiz...)}`  
8. 再「保存为草稿」（`appmsgid=` 保留即可）

**验收（DOM，比肉眼稳）**：
- `.js_cover_preview_new`：`display === 'block'` 且 `background-image` 含 `mmbiz.qpic.cn` / `mmbiz_jpg`
- 允许 `#js_cover_area` 文案仍含「拖拽或选择封面」——**以 preview 背景为准**
- 失败信号：`previewDisplay:none` 或 bg 为空 / `url("")`

**禁止**：
- 裁剪弹窗打开时 `Escape` / 点「取消」
- 用 `locator('button:has-text("确定")')` 当确认（会命中 disabled）
- 只看「已保存」文案（常不出现）

**关键点**：
- 必须先把图插入正文，再「从正文选择」
- 缩略图不是 `<img>`，用 class + bg 筛选
- 裁剪确认按钮文案是 **「确认」**
- 封面失败不阻塞草稿（v3.5.0）

### 🔴 公众号赞赏弹窗 checkbox 结构（v1.7.0 新增）
**问题**：「我已阅读并同意」checkbox 在 `label > div` 结构中，不是标准 `input[type="checkbox"]`。

**解决**：用 JS 遍历找到包含「我已阅读并同意」的元素，然后找其父元素中的 checkbox：
```javascript
const parent = el.closest('label, div');
const checkbox = parent.querySelector('input[type="checkbox"], [role="checkbox"]');
if (checkbox) checkbox.click();
```

### 🔴 公众号合集选择器正确流程（v1.9.1 更新，v3.3.0 补充）
**问题**：合集选择器是自定义 Vue 组件，JS evaluate 和坐标点击都不可靠。

**已验证的正确流程**：
1. 点击「合集」→「未添加」打开弹窗
2. 点击「请选择合集」输入框 focus
3. 输入「今日羊报」或「羊报AI周刊」搜索
4. 用 `page.getByText('「今日羊报 AI」', { exact: true })` 精确匹配选项
5. **先 hover 再 click**（必须！）
6. 用 `page.getByRole('button', { name: '确认' })` 点击确认

**关键点**：
- 必须用 `exact: true` 精确匹配，否则会匹配到正文中的同名文本
- 必须先 hover 再 click，直接 click 不生效
- 不要用 JS evaluate，用 Playwright locator 更可靠
- **合集名按 REPORT_MODE 读取**：daily「今日羊报 AI」/ weekly「羊报AI周刊」/ monthly「羊报AI月报」
- **v3.3.0 补充**：合集选择失败时用 try-catch 跳过（timeout: 5000），不阻塞保存草稿

### 🟡 公众号原创声明弹窗自动填充（v1.7.0 新增）
**问题**：原创声明弹窗打开后，「文字原创」已默认选中，「我已阅读并同意」已默认勾选。

**解决**：直接点击「确定」即可，无需手动操作其他选项。

### 🟡 公众号工具栏按钮坐标（v1.7.0 新增）
**问题**：工具栏按钮（图片、视频号等）的位置会随页面滚动变化。

**解决**：
- 「图片」按钮：约 x=530, y=17（顶部工具栏）
- 「视频号」按钮：约 x=1074, y=17（顶部工具栏右侧）
- 使用 `browser_evaluate` 动态查找按钮位置更可靠

### 🔴 微信视频号描述字段（v3.24.0 改走 shadow 协议）
**问题**：页面级 `textarea` / `placeholder` / `contenteditable="true"` 选择器都找不到——描述在 `wujie-app` open shadow 的 `.input-editor` 里。
**解决（当前默认）**：按 13.1——`hasWujie=true` 时 evaluate 内 `shadowRoot.querySelector('.input-editor')` + focus + `page.keyboard.type`。**禁止**把坐标点击当主路径。
**旧 UI 兜底（仅 `hasWujie=false`）**：截图估坐标（约 x=760, y=310）→ `page.mouse.click` → `page.keyboard.type`。

### 🔴 微信视频号合集选择器
**问题**：合集选择器在 wujie shadow 内；页面级 locator 找不到。
**解决（当前默认）**：按 13.1 点 shadow 内「选择合集」→ `.option-item` 前缀匹配。
**旧 UI 兜底（仅 `hasWujie=false`）**：坐标点选项（约 x=860, y=180）；失败则手动。

### 🔴 微信视频号保存草稿限制
**问题**：如果「定时发表」设为「定时」，保存草稿按钮会显示警告「使用定时发表将无法保存草稿」。另：超 16 字短标题会 **silent disable** 保存（无 toast）。
**解决**：保存前确保「不定时」；短标题走 13.4（≤16 字、禁 `.` `~`）；保存无反应先查 `.error-title` 与 `button.disabled`。成功无跳转——必须去 `/platform/post/draftListManager` 数条目。

### 🟡 视频号描述自动填充失败（v3.24.0 降级）
**问题**：`getByPlaceholder` / `getByText` / `locator('textarea')` 找不到描述框——因为节点在 shadow 内，不是「只能坐标点」。
**解决**：走 13.1 `.input-editor` shadow 协议。坐标点击仅 `hasWujie=false` 兜底。

### 🔴 视频号 wujie shadow DOM（v3.24.0 替代 v1.7.0 iframe）
**问题**：2026-08-30 版全部表单在 `wujie-app` open shadow root 内；页面级 locator / 普通 evaluate / `page.frame({name:'content'})` 全部失效。v1.7.0 的 iframe + `.edit-shorttitle-content` 已不是主路径。

**解决**：先跑 13.1 结构判定。`hasWujie=true` → shadow 协议（`setInputFiles` 穿 shadow、描述 `.input-editor`、短标题 Vue `input[placeholder*="短标题"]`）。仅 `hasWujie=false` 且存在 `name="content"` iframe 时才用旧 `page.frame` 法。

### 🔴 视频号短标题是 Vue 受控 input（v3.24.0 修正 v1.7.0）
**问题**：旧文档称短标题是 `.edit-shorttitle-content` contenteditable；实测是 `input[placeholder*="短标题"]`（Vue 受控），`textContent` / `fill()` 不同步。

**解决**：按 13.1：原生 `HTMLInputElement.value` setter 清空 + focus + `page.keyboard.type`；填完回读 `.error-title` + 保存按钮 `disabled`。格式 `{报刊名} {M月D日至D日}`，≤16 字，禁 `.` `~`。

### 🔴 视频号封面修改限制（v1.7.0 新增）
**问题**：视频号修改封面和短标题有「仅支持修改一次，修改后不可撤回」限制。修改记录会展示在视频上。

**解决**：
1. 修改前确认所有内容（封面、短标题）都正确
2. 一次性完成所有修改再提交
3. 修改后显示「修改审核中，预计30分钟内审核完成」

### 🔴 视频号封面在 wujie shadow 内上传（v3.24.0 修正 v1.7.0）
**问题**：旧文档称封面弹窗在 iframe、需坐标点 `+` 触发 filechooser。实测 filechooser 监听在 shadow 内不触发。

**解决**：`hasWujie=true` 时 `page.locator('wujie-app .single-cover-uploader-wrap input[type=file]')` 直接 `setInputFiles`；弹窗点 `button.weui-desktop-btn_primary`「确认」。未关「编辑个人主页卡片」弹窗会吞掉保存。仅旧 iframe UI 才用 `.edit-btn` + filechooser。

### 🟡 B站封面隐藏 file input（v1.7.0 新增）
**问题**：B站封面上传的 file input 是隐藏的（`accept: "image/png, image/jpeg"`），且有多个 file input（视频、封面、字幕等）。

**解决**：
```javascript
const inputs = await page.$$('input[type="file"]');
// inputs[0]: 视频 (.mp4)
// inputs[1]: 封面 (image/png, image/jpeg)
// inputs[2]: 字幕 (.txt)
// inputs[3]: 素材 (.zip)
await inputs[1].setInputFiles('horizontal-4-3.png');  // 设置封面
```

### 周报多平台上传流程（v1.9.2 新增）

**周报上传流程与日报相同，但需要使用周报专用文件和合集：**

#### 周报 B站上传
1. 导航到 `https://member.bilibili.com/platform/upload/video/frame`
2. 上传周报视频：`news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD/video/【羊报AI周刊】*.mp4`
3. 标题自动填充：`【羊报AI周刊】... | YYYY-MM-DD~YYYY-MM-DD`
4. 上传封面：`news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD/horizontal-4-3.png`
5. 设置创作声明：个人观点，仅供参考
6. 添加标签：羊报AI周刊, AI周报, OpenAI, Anthropic, DeepSeek
7. 填写简介：本期热点...
8. 选择合集：「羊报AI周刊」
9. 点击「立即投稿」

#### 周报公众号上传
1. 打开公众号后台 → 点击「新的创作」→「文章」
2. 切换到新标签页
3. 填写标题：`OpenAI二验风暴、Anthropic IPO、DeepSeek 500亿融资｜羊报AI周刊 YYYY-MM-DD~YYYY-MM-DD`
4. 填写作者：`羊报AI周刊`（≤8 字；署名 `羊报AI周刊 · MM-DD~MM-DD` 写进正文，勿填作者栏）
5. 填写正文（ProseMirror execCommand insertHTML，🔴 v3.23.0）
6. 上传封面图到正文：
   - 点击正文区域获取 focus
   - 按回车创建新行
   - 点击工具栏「图片」→「本地上传」
   - 用 `input.setInputFiles()` 上传封面图（`horizontal-4-3.png` 横版）
7. 设置封面：
   - Hover「拖拽或选择封面」显示选项菜单
   - 用 `.js_selectCoverFromContent` class 选择器点击「从正文选择」
   - 在弹窗中点击图片（出现勾选标记）
   - 点击「下一步」
   - 点击「确认」确认裁剪
8. 设置原创声明：点击「原创」→ 确定（已默认选中）
9. 设置赞赏：点击「赞赏」→ 确定（已默认配置）
10. 选择合集：「羊报AI周刊」
11. 保存草稿

#### 周报封面文件

| 平台 | 文件 | 尺寸 |
|------|------|------|
| B站/通用（横版） | `horizontal-4-3.png` | 1536x1152 (4:3) |
| 抖音/竖版 | `vertical-3-4.png` | 1152x1536 (3:4) |

### Phase 14: 抖音自动上传（Playwright MCP）

**权限已在预授权阶段获得，直接执行。**

**🔴 重要经验：抖音创作者中心使用自定义组件，封面上传需要用 force click，发布需要短信验证码。**

#### 14.0-pre 用户手动上传跳过（v3.26.0 / 2026-09-01 实测）

用户明确说「抖音已手动上传 / 不要再自动传 / 记为已手动」时：
1. **立即停止** Phase 14，禁止再打开 `creator.douyin.com` 上传页，禁止点上传 / 暂存 / 重新上传。
2. 标记 `douyin: user-manual`（`upload-status.md` 写 `⏭ 用户手动`）。
3. 不把已打开的创作者页当失败重试；不阻塞其他平台。
4. 验收 URL 仍是 `https://creator.douyin.com/creator-micro/content/publish/record?tab=draft`——**仅当用户要求核验时**才打开，默认不核验、不改稿。

#### 14.0 草稿恢复弹窗处理（v3.18.0 / 2026-08-18 实测）

打开上传页（`creator.douyin.com/creator-micro/content/upload`）时，若上次有未发布草稿，会弹出 **「你还有上次未发布的视频，是否继续编辑？」**。

**❌ 错误做法**：点击合并文本「继续编辑放弃」——无法精确丢弃旧草稿，会落到 `enter_from=draft` 编辑页，混入旧素材。

**✅ 正确流程**：
1. 从草稿编辑页点「**重新上传**」→ 导航回 upload 页 → 重新触发 file chooser。
2. 离开草稿编辑页时会弹 **「将此次编辑保留？」**（beforeunload）→ `browser_handle_dialog(accept=true)`，否则触发 `net::ERR_ABORTED` 导致导航失败。
3. **弹窗若只显「放弃」按钮**（v3.22.0 / 2026-08-28 实测）：用 JS evaluate 精确点 `textContent.trim() === '放弃'` 的可见节点，**勿点合并文本「继续编辑放弃」**（会落到 `enter_from=draft` 编辑页混入旧素材）；点完弹窗消失即恢复 upload 页空白上传区。

```
# 草稿编辑页 → 点「重新上传」回到 upload 页
browser_run_code_unsafe("""async (page) => {
  const btn = page.getByRole('button', { name: '重新上传' });
  if (await btn.count()) await btn.first().click();
  return 'clicked';
}""")

# 若弹出 beforeunload「将此次编辑保留？」
browser_handle_dialog(accept=true)
```

#### 14.1 打开抖音创作者中心

```
browser_navigate("https://creator.douyin.com/creator-micro/content/upload")
```

#### 14.2 上传视频

```
# 点击「上传视频」按钮触发 file chooser
browser_run_code_unsafe("""async (page) => {
  const uploadBtn = page.locator('text=上传视频');
  await uploadBtn.first().click();
  await page.waitForTimeout(2000);
  return 'clicked';
}""")

# 上传视频文件
browser_file_upload("news-pipeline/YYYY-MM-DD/video/【YYYY-MM-DD】*.mp4")

# 等待上传完成
browser_wait_for(time=10)
```

#### 14.3 关闭提示弹窗

**🔴 上传视频后会弹出「视频预览功能」提示，必须先关闭：**

```
browser_click(target={我知道了按钮ref})
# 或用 JS
browser_run_code_unsafe("""async (page) => {
  await page.getByRole('button', { name: '我知道了' }).click();
  return 'closed';
}""")
```

#### 14.4 填写作品描述（30字）

**🔴 抖音作品描述是标准 input，但 placeholder 为「填写作品标题，为作品获得更多流量」。格式：`{报刊名} {日期字段}`，≤30字，纯报刊名+日期，不加核心标题/副标题：**

```
browser_run_code_unsafe("""async (page) => {
  // 日报：今日羊报AI 2026-08-01
  // 周报：羊报AI周刊 07-28~08-01
  // 月报：羊报AI月报 2026-08
  const titleInput = page.getByRole('textbox', { name: '填写作品标题，为作品获得更多流量' });
  await titleInput.fill('今日羊报AI 2026-08-01');
  return 'title filled';
}""")
```

#### 14.5 填写作品简介

**🔴 作品简介区域在描述下方，需要先滚动定位：**

```
browser_run_code_unsafe("""async (page) => {
  // 简介区域在 y=217 附近
  await page.mouse.click(690, 217);
  await page.waitForTimeout(500);
  await page.keyboard.type('简介内容');
  return 'intro typed';
}""")
```

#### 14.5b 描述与话题分离输入（v3.22.0 / 2026-08-28 实测）

**🔴 误用 `contenteditable.nth(1)` 会 30s 超时**：抖音编辑页通常只有 **1 个 `div[contenteditable="true"]`**（即描述/简介编辑器）。若按「描述 + 话题都在 contenteditable」的假设用 `nth(1)` 定位话题框，会超时；话题（#标签）**另有入口**，不在 contenteditable 里。

**✅ 分离输入**：
1. **描述/简介** → 填第 1 个 contenteditable（`nth(0)` 或 `page.locator('div[contenteditable="true"]').first()`）
2. **话题（#标签）** → 点 **「#添加话题」** 按钮 → `keyboard.type(tag)` + `keyboard.press('Enter')`，逐个加

```
# 话题逐个加（勿用 nth(1)）
browser_run_code_unsafe("""async (page) => {
  const tags = ['今日羊报AI', 'AI日报', '智谱GLM', 'Qwen', '英伟达', 'OpenAI'];
  for (const tag of tags) {
    // 点「#添加话题」入口
    const addBtn = page.locator('text=#添加话题').first();
    if (await addBtn.count()) await addBtn.click({ force: true });
    await page.waitForTimeout(300);
    await page.keyboard.type('#' + tag);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(400);
  }
  return 'tags added';
}""")
```

#### 14.5c 描述输入 editor-kit 编辑器（v3.23.0 / 2026-08-29 日报实测）

0829 实测：描述编辑器实际是 **`.editor-kit-editor-container [contenteditable="true"]`**（editor-kit 组件），且直接 `fill()` 可能不触发组件状态同步——用 `page.keyboard.type(text, {delay: 5})` 逐字输入最稳：

```js
browser_run_code_unsafe("""async (page) => {
  const desc = '...162字描述含7话题...'; // 由外部传入
  await page.locator('.editor-kit-editor-container [contenteditable="true"]').first().click();
  await page.waitForTimeout(300);
  await page.keyboard.type(desc, { delay: 5 });
  return 'desc typed';
}""")
```

> 与 14.5b 的关系：14.5b 的 `div[contenteditable="true"]` 通用定位在 0829 版编辑页失效时，用本节的 `.editor-kit-editor-container` 选择器兜底；话题仍走「#添加话题」+ keyboard.type 流程不变。

#### 14.6 上传封面（横封面4:3 + 竖封面3:4）（v3.6.0 更新）

**🔴 封面复用**：横封面用 `horizontal-4-3.png`（4:3）+ 竖封面用 `vertical-3-4.png`（3:4）。  
**文件名铁律**：用 Phase 5.5 产出的 `horizontal-4-3.png` / `vertical-3-4.png`，**不要**写成 `cover-horizontal.png` / `cover-vertical.png`。

**入口差异**：
- **首次投稿页**：横封面点「完成」后，常自动弹出「设置竖封面获更多流量」→ 点「设置竖封面」
- **草稿编辑页**（`post/video?enter_from=draft`）：「设置竖封面」弹窗**经常不出现**，必须**再点竖封面 3:4 区域**单独打开编辑器

**🔴 封面上传图标被 SVG 拦截（v3.23.0 / 2026-08-29 实测）**：点封面上传图标时 click 被 SVG 子元素截获（"element intercepts pointer events"）→ 改点上传容器本体 `.semi-upload.upload-BvM5FF`（+ waitForEvent('filechooser') + setFiles）。

**🔴 封面文件落盘位置（v3.23.0 / 2026-08-29 实测）**：封面图实际生成在**日期目录根**（如 `news-pipeline/2026-08-29/horizontal-4-3.png`），**没有 `covers/` 子目录**——脚本传路径时勿假设子目录结构，先 `ls` 确认实际路径再 setFiles。

**🔴 完成按钮坑（v3.6.0 / 2026-07-17 实测）**：
- `getByRole('button', { name: '完成' })` **经常 count=0**（弹窗粉按钮不是标准 button role）
- 必须用 **text 匹配 + evaluate click**，并在 **filechooser 成功后等 1.5–3s**（预览出现）再点完成
- 点完后若仍见「设置竖封面」标题 → 再点一次完成；**禁止**在未保存时点「取消/关闭」触发「封面未保存」确认框后点「确定」（会丢图）

**推荐完整流程（语义定位 + filechooser + 可靠完成）**：

```
# 共用：可靠点击弹窗内「完成」（优先 text，其次 evaluate）
# 返回 clicked / not_found
async function clickCoverDone(page) {
  await page.waitForTimeout(1500); // 等预览渲染
  // 1) text 定位（比 role 稳）
  try {
    const loc = page.locator('text=完成').last();
    if (await loc.count() && await loc.isVisible().catch(() => false)) {
      await loc.click({ force: true, timeout: 3000 });
      return 'clicked text=完成';
    }
  } catch (_) {}
  // 2) evaluate：点最靠下、宽度较大的「完成」（粉色主按钮）
  const ok = await page.evaluate(() => {
    const cands = [];
    for (const el of document.querySelectorAll('button, div, span, a')) {
      if ((el.textContent || '').trim() !== '完成' || !el.offsetParent) continue;
      const r = el.getBoundingClientRect();
      if (r.width > 40 && r.y > 300) cands.push({ el, y: r.y, w: r.width });
    }
    if (!cands.length) return false;
    cands.sort((a, b) => b.y - a.y);
    cands[0].el.click();
    return true;
  });
  return ok ? 'clicked evaluate 完成' : 'not_found';
}

# 步骤1：打开横封面编辑器——语义找「横封面4:3」→ 同卡「选择封面」
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => window.scrollTo(0, 0));
  return await page.evaluate(() => {
    for (const el of document.querySelectorAll('*')) {
      if ((el.textContent || '').trim() === '横封面4:3' && el.offsetParent) {
        let p = el.parentElement;
        for (let i = 0; i < 5 && p; i++, p = p.parentElement) {
          const sel = Array.from(p.querySelectorAll('*'))
            .find(n => (n.textContent || '').trim() === '选择封面');
          if (sel) { sel.click(); return 'opened horizontal via 选择封面'; }
        }
        el.click(); return 'clicked 横封面4:3';
      }
    }
    return 'horizontal label not found';
  });
}""")

**🔴 @好友 mention 浮层拦截「选择封面」（v3.22.0 / 2026-08-28 实测）**
- 现象：点「横封面4:3」同卡的「选择封面」无反应——点击被 `publish-mention-wrapper`（话题/`@好友` 自动补全浮层）拦截
- 修复：先 `keyboard.press('Escape')` 关浮层 → JS evaluate 找「设置封面」header → `parentElement` 攀爬到封面容器 → 点容器内第一个 `textContent === '选择封面'` 的 div

```
# 封面选择被 @好友 浮层拦截时的兜底
browser_run_code_unsafe("""async (page) => {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  await page.evaluate(() => {
    for (const el of document.querySelectorAll('*')) {
      if ((el.textContent || '').trim() === '设置封面' && el.offsetParent) {
        let p = el.parentElement;
        for (let i = 0; i < 6 && p; i++, p = p.parentElement) {
          const sel = Array.from(p.querySelectorAll('div, span, a'))
            .find(n => (n.textContent || '').trim() === '选择封面' && n.offsetParent);
          if (sel) { sel.click(); return; }
        }
      }
    }
  });
  return 'opened cover via 设置封面';
}""")
```

# 步骤2：横封面 filechooser（推荐）或 setInputFiles 兜底
browser_run_code_unsafe("""async (page) => {
  const path = 'news-pipeline/YYYY-MM-DD/horizontal-4-3.png';
  try {
    const [chooser] = await Promise.all([
      page.waitForEvent('filechooser', { timeout: 6000 }),
      page.locator('text=上传封面').first().click({ force: true })
    ]);
    await chooser.setFiles(path);
    return 'h chooser ok';
  } catch (e) {
    const inputs = await page.$$('input[type="file"]');
    if (inputs.length) {
      await inputs[inputs.length - 1].setInputFiles(path);
      return 'h setInput ok n=' + inputs.length;
    }
    return 'h fail';
  }
}""")
# 步骤3：完成横封面
# → clickCoverDone(page)；确认不再显示设置弹窗标题

# 步骤4：打开竖封面编辑器
browser_run_code_unsafe("""async (page) => {
  await page.waitForTimeout(800);
  const btn = page.getByRole('button', { name: '设置竖封面' });
  if (await btn.count() && await btn.first().isVisible().catch(() => false)) {
    await btn.first().click();
    return 'clicked 设置竖封面 popup';
  }
  // 草稿页：标签「竖封面3:4」上方封面框
  const r = await page.evaluate(() => {
    for (const el of document.querySelectorAll('*')) {
      if ((el.textContent || '').trim() === '竖封面3:4' && el.offsetParent) {
        const rect = el.getBoundingClientRect();
        return { x: rect.x + 40, y: Math.max(rect.y - 70, 120), labelY: rect.y };
      }
    }
    return null;
  });
  if (!r) return 'vertical label not found';
  await page.mouse.click(r.x, r.y);
  await page.waitForTimeout(400);
  await page.mouse.click(r.x, r.y + 25);
  // 同卡「选择封面」再兜底一次
  await page.evaluate(() => {
    for (const el of document.querySelectorAll('*')) {
      if ((el.textContent || '').trim() === '竖封面3:4' && el.offsetParent) {
        let p = el.parentElement;
        for (let i = 0; i < 6 && p; i++, p = p.parentElement) {
          const sel = Array.from(p.querySelectorAll('*'))
            .find(n => (n.textContent || '').trim() === '选择封面');
          if (sel) { sel.click(); return; }
        }
      }
    }
  });
  return 'opened vertical near ' + JSON.stringify(r);
}""")

# 步骤5：竖封面上传（必须确认打开了「设置竖封面」或出现「上传封面」）
browser_run_code_unsafe("""async (page) => {
  const path = 'news-pipeline/YYYY-MM-DD/vertical-3-4.png';
  const open = await page.evaluate(() =>
    document.body.innerText.includes('设置竖封面')
    || document.body.innerText.includes('上传封面'));
  if (!open) return 'editor not open — re-click vertical box';
  try {
    const [chooser] = await Promise.all([
      page.waitForEvent('filechooser', { timeout: 6000 }),
      page.locator('text=上传封面').first().click({ force: true })
    ]);
    await chooser.setFiles(path);
    return 'v chooser ok';
  } catch (e) {
    const inputs = await page.$$('input[type="file"]');
    if (inputs.length) {
      await inputs[inputs.length - 1].setInputFiles(path);
      return 'v setInput ok';
    }
    return 'v fail';
  }
}""")

# 步骤6：完成竖封面（等预览 → text/evaluate 点完成 → 再验弹窗是否关闭）
browser_run_code_unsafe("""async (page) => {
  await page.waitForTimeout(2000);
  // 可靠完成：见上方 clickCoverDone 逻辑
  let msg = 'not_found';
  try {
    const loc = page.locator('text=完成').last();
    if (await loc.count() && await loc.isVisible().catch(() => false)) {
      await loc.click({ force: true, timeout: 3000 });
      msg = 'clicked text=完成';
    }
  } catch (_) {}
  if (msg === 'not_found') {
    const ok = await page.evaluate(() => {
      const cands = [];
      for (const el of document.querySelectorAll('button, div, span, a')) {
        if ((el.textContent || '').trim() !== '完成' || !el.offsetParent) continue;
        const r = el.getBoundingClientRect();
        if (r.width > 40 && r.y > 300) cands.push({ el, y: r.y });
      }
      if (!cands.length) return false;
      cands.sort((a, b) => b.y - a.y);
      cands[0].el.click();
      return true;
    });
    msg = ok ? 'clicked evaluate 完成' : 'not_found';
  }
  await page.waitForTimeout(1500);
  const still = await page.evaluate(() => document.body.innerText.includes('设置竖封面'));
  if (still) {
    // 再点一次
    await page.evaluate(() => {
      for (const el of document.querySelectorAll('button, div, span, a')) {
        if ((el.textContent || '').trim() === '完成' && el.offsetParent) {
          const r = el.getBoundingClientRect();
          if (r.y > 400) { el.click(); return; }
        }
      }
    });
    await page.waitForTimeout(1500);
  }
  // 若弹出「封面未保存/是否关闭」——仅在已确认预览成功时再处理；默认点「取消」保留编辑
  return {
    done: msg,
    stillOpen: document.body.innerText.includes('设置竖封面')
  };
}""")

# 步骤7：验收（必须全部通过才暂存）
browser_run_code_unsafe("""async (page) => {
  const t = document.body.innerText;
  return {
    missingV: t.includes('竖封面缺失'),
    missingDual: t.includes('横/竖双封面缺失') || t.includes('双封面缺失'),
    hasSetDialog: t.includes('设置竖封面'),
    hasZancun: !!Array.from(document.querySelectorAll('button'))
      .find(b => (b.textContent || '').trim() === '暂存离开')
  };
}""")
# 通过标准：missingV=false && missingDual=false && hasSetDialog=false
# 然后滚动到底部点「暂存离开」
```

**🔴 关键经验（v3.5.0 / v3.6.0 实测）**：
1. **语义定位 > 硬编码坐标**：先找「横封面4:3」/「竖封面3:4」再点同卡「选择封面」  
2. **「上传封面」必须 `force: true`**，否则 SVG 拦截  
3. **草稿页没有「设置竖封面」弹窗是常态**；用标签 `getBoundingClientRect` 点 **y = label.y - 70**  
4. **完成 ≠ getByRole('button')**：用 `locator('text=完成').last()` 或 evaluate 点底部主按钮  
5. **setFiles 后必须等 1.5–3s** 再点完成，否则封面未写入状态  
6. **验收三件套**：无「竖封面缺失」+ 无「双封面缺失」+ 无「设置竖封面」弹窗 → 再「暂存离开」  
7. 合集/声明可与封面并行，但 **竖封面失败优先重试封面**，不要只关页  
8. 若 URL 已在 `enter_from=draft` 且横封面已有，可 **只补竖封面**（今天 2026-07-17 场景）


#### 14.7 添加合集「今日羊报AI」

**🔴 抖音合集选择器使用 listbox 组件，可以用 ref 精确点击：**

```
# 滚动到合集区域
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => window.scrollBy(0, 300));
  return 'scrolled';
}""")

# 点击「请选择合集」打开下拉框
browser_run_code_unsafe("""async (page) => {
  const elements = document.querySelectorAll('*');
  for (const el of elements) {
    if (el.textContent.trim() === '请选择合集' && el.offsetParent !== null) {
      el.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")

# 用 snapshot 找到合集选项的 ref
browser_snapshot(depth=5)
# 🔴 合集名大小写陷阱（v3.22.0 / 2026-08-28 实测）：抖音合集名可能与 B站/公众号不同
# 实测「「今日羊报Al」」是小写 L（非大写 I）+ 「共80个作品」——勿硬编码精确合集名
# 修复：探测下拉框可见文本，匹配「今日羊报」前缀（不分大小写）+ 「共N个作品」的选项点击；snapshot 验收按前缀模糊匹配
browser_click(target={ref编号})
```

#### 14.8 设置自主声明

```
# 点击「请选择自主声明」
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent.trim() === '请选择自主声明' && el.offsetParent !== null) {
        el.click();
        return;
      }
    }
  });
  return 'clicked';
}""")

# 选择「内容为个人观点或见解」
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent.trim() === '内容为个人观点或见解' && el.offsetParent !== null) {
        el.click();
        return;
      }
    }
  });
  return 'selected';
}""")

# 点击「确定」
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('button');
    for (const btn of buttons) {
      if (btn.textContent.trim() === '确定' && btn.offsetParent !== null) {
        btn.click();
        return;
      }
    }
  });
  return 'confirmed';
}""")
```

#### 14.8b Semi Design 组件拦截修复（v3.18.0 / 2026-08-18 实测）

抖音创作者中心部分控件基于 **Semi Design**（ByteDance），原生 `locator.click()` 常被外层包裹元素拦截而 30s 超时。

**自主声明 radio**：
- **原因**：`<label class="semi-radio">…</label>` 拦截 pointer events，`locator.click()` 超时 30s。
- **修复**：直接点击 `label.semi-radio` 元素。

```
const label = page.locator('label.semi-radio').filter({ hasText: '内容为个人观点或见解' });
await label.click();
```

**「暂存离开」按钮**：
- **原因**：`<div role="modal" class="semi-modal-wrap">` 拦截，按钮不可点。
- **修复**：关闭 modal `.semi-modal-close` → `Escape` → force click。

```
await page.keyboard.press('Escape');
await page.waitForTimeout(1000);
await page.locator('button:has-text("暂存离开")').click({ force: true });
```

**file chooser modal state**：
- `browser_run_code_unsafe` 触发 file chooser 后，工具层会停在 **"Modal state: File chooser"** 导致后续 tool call 阻塞。
- **修复**：用 `browser_file_upload(paths=[...])` 处理文件选择，**不要**在同一长脚本里串 `filechooser` 事件。

#### 14.9 添加标签

```
# 点击「#添加话题」
browser_run_code_unsafe("""async (page) => {
  const elements = document.querySelectorAll('*');
  for (const el of elements) {
    if (el.textContent.trim() === '#添加话题' && el.offsetParent !== null) {
      el.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")

# 输入标签并按 Enter
browser_run_code_unsafe("""async (page) => {
  await page.keyboard.type('今日羊报AI');
  await page.keyboard.press('Enter');
  return 'tag added';
}""")
```

#### 14.10 存草稿（不直接发布）

**🔴 重要：所有平台上传一律存草稿，不直接发布！用户确认后再手动发布。**

```
# 抖音没有"存草稿"按钮，使用「暂存离开」或直接关闭页面
# 视频会自动保存到草稿箱

# 方法1：点击「暂存离开」（如果有）
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  const buttons = document.querySelectorAll('button');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '暂存离开' && btn.offsetParent !== null) {
      btn.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")

# 方法2：如果没有「暂存离开」，直接关闭标签页（视频已自动保存）
```

**🔴 草稿落库验收（v3.9.0 / 2026-07-20 实测 — 不可省略）**

仅点「暂存离开」**不够**。0720 首次上传后用户在创作者中心**看不到草稿**，必须重传。

**成功信号（满足其一即可记 ✅）**：
1. 回到上传页出现 **「继续编辑」** / 「上次未发布」类恢复入口
2. 直接导航 `https://creator.douyin.com/creator-micro/content/publish/record?tab=draft`（**不要**去 `content/manage`——那页只显示已发布，看不到草稿，会误判上传失败），列表可见当日标题关键词（如 `Fable` / `通义` / `2026-07-20`）
3. 打开 `post/video?enter_from=draft` 时**表单非空**（标题长度 > 0，有视频预览）

**失败信号 → 必须整段重传（视频+标题+双封面+暂存）**：
- 内容管理无当日条目
- 上传页无「继续编辑」
- `enter_from=draft` 打开是空表单（标题 0/30）

**竖封面文件**：只使用本期 `news-pipeline/{date}/vertical-3-4.png`（含日期+品牌）。用户指定该文件时**禁止**用 scene 图或其它日期文件替代。

#### 14.10b 暂存离开 + 草稿落库验收（v3.18.0 / 2026-08-18 实测）

抖音 Semi Design modal（`semi-modal-wrap`）会拦截「暂存离开」按钮，需先 `Escape` 关闭残留弹窗再 force click（见 14.8b）。

```
# 1. 关闭可能残留的 modal
await page.keyboard.press('Escape');
await page.waitForTimeout(1000);

# 2. force click「暂存离开」
await page.locator('button:has-text("暂存离开")').click({ force: true });

# 3. 离开编辑页时若弹 beforeunload「将此次编辑保留？」
browser_handle_dialog(accept=true)
```

**草稿落库验收信号**（满足其一即 ✅）：
1. 回到上传页出现 **「继续编辑」** / 「上次未发布」恢复入口
2. 内容管理 / 草稿列表可见当日标题关键词
3. `post/video?enter_from=draft` 表单非空（标题长度 > 0，有视频预览）

#### 🔴 抖音违规审核与处理（v3.15.0 新增，2026-07-31 实测）

**常见违规原因**：

| 违规原因 | 触发条件 | 文案修改方向 |
|----------|---------|-------------|
| `引导至风险不可控渠道` | 描述/口播中出现「开放申请」「去XX体验」「下载XX」「申请试用」「去 Hugging Face」「跑杀毒扫描」「清 Cookie」等引导性表述；也可叠「画面」标签（账号事故帧） | 去掉「去」「申请」「体验」「下载」等引导动词，改为「上线」「推出」「发布」「已随仓库发布」等中性陈述；账号安全改「走官方账号安全页核对」；**若同时标「画面」必须重渲** |
| `画面` / `不适宜公开` | 视频帧中包含安全事件视觉（入侵/撬锁/隔离舱破裂）、政策/立法场景（法槌/两党剪影） | 重画场景图，改为产品化视觉（仪表盘/UI界面/机房）；修改口播避免攻击性动词 |
| `竖封面缺失` / `双封面缺失` | 未上传竖封面（3:4）或横封面（4:3） | 补传对应封面，验收确认无缺失提示 |
| `违规推广内容` | 简介中数字连续出现（疑似QQ号/微信号） | 数字中文化，版本号简化，去掉 hash tag 行 |

**违规处理流程**：

1. **查看违规详情**：打开抖音创作者中心 → 内容管理 → 找到违规作品 → 点击「违规详情」
2. **定位违规源**：
   - 先看违规原因描述（如「引导至风险不可控渠道」→ 检查描述/口播中的引导性动词）
   - 再检查描述文案中是否有「开放申请」「去XX体验」「下载」「申请试用」等关键词
   - 最后检查视频帧画面（安全事件场景需重画）
3. **修改方案**：
   - **文案违规**：修改 publish.json 中抖音的 title/description，去掉所有引导性表述
   - **画面违规**：重画对应场景图（prompt 改为产品化视觉），重写口播文本
   - **双封面缺失**：补传竖封面/横封面
4. **重传流程**：
   - 修改 publish.json 中抖音标题/描述
   - 如涉及画面违规：修改 voiceover-texts.json 中的口播文本 → 重新生成 TTS（scene 级别）→ 重算 captions.json → 重渲染视频
   - 打开 `https://creator.douyin.com/creator-micro/content/upload` → 上传新视频 → 填写标题/描述 → 上传双封面 → 暂存离开

**违规文案修改示例**：

| 原文 | 问题 | 修改后 |
|------|------|--------|
| 「符合条件的科研人可以**申请试用**」 | 引导至外部渠道 | 「学术科研领域的 AI 应用正在加速落地」 |
| 「想玩 AI 音乐的可以直接去 **Flow Music 体验**」 | 引导至第三方平台 | 「AI 音乐创作的门槛正在降低」 |
| 「OpenAI 学术科研版**开放申请**」 | 引导申请 | 「OpenAI 推出学术科研版」 |

**自检清单新增项**（Phase 2 审核检查清单中增加）：

```
☐ 抖音描述：检查「申请」「体验」「下载」「去」「试用」等引导性动词
☐ 抖音描述：去掉任何指向外部平台/产品的引导语句
☐ 口播文本：Scene 5/6 类场景（产品/服务介绍）禁止尾部引导行动
☐ 口播 Now What：禁止「去 Hugging Face / 清 Cookie / 跑杀毒 / 再下单」；账号安全只说官方安全页
☐ 画面：禁止断链、丢卡、入侵、杀毒扫描窗、第三方仓库站 UI（Star/Fork/Model card）
☐ 内部 review-checklist PASS ≠ 抖音过审；标签含「画面」必须 `*-safe.mp4`
```

#### 抖音上传组件操作总结（v3.6.0 实测）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 视频上传 | file chooser | `text=上传视频` → `file_upload` | ✅ 高 |
| 提示弹窗 | 按钮 | `getByRole('button', { name: '我知道了' })` | ✅ 高 |
| 作品描述 | 标准 input | **`fill()`** 或 placeholder 匹配（React 受控） | ✅ 高 |
| 作品简介 | 文本区域 | 坐标点击 + `keyboard.type` | ✅ 高 |
| 横封面4:3 | 自定义编辑器 | 语义「横封面4:3」→ force「上传封面」→ setFiles → **text/evaluate「完成」** | ⚠️ 需 force+等预览 |
| 竖封面3:4 | 自定义编辑器 | 弹窗或标签上方点击 → force 上传 → setFiles → **text/evaluate「完成」** | ⚠️ 草稿页无弹窗 |
| 完成按钮 | 非标准 role | **`locator('text=完成')` / evaluate**，**不要**依赖 `getByRole('button','完成')` | ⚠️ count 常为 0 |
| 合集 | listbox | 点击下拉框 → snapshot 找 ref → 精确点击 | ✅ 高 |
| 自主声明 | 弹窗 | 点击打开 → 选择选项 → 确定 | ✅ 高 |
| 标签 | 输入框 | 点击 `#添加话题` → `keyboard.type` + Enter | ✅ 高 |
| 存草稿 | 按钮 | 底部 **「暂存离开」**（非「存草稿」） | ✅ 高 |
| 发布 | 按钮 | 点击「发布」→ 短信验证码（需用户手动） | ⚠️ 需用户 |

**关键经验**：
1. **上传视频后必须关闭「视频预览功能」弹窗**，否则后续操作被阻挡
2. **封面上传需要 `force: true`**，SVG 会拦截点击
3. **完成按钮不要用 getByRole**，改用 text/evaluate + 等预览 2s
4. **验收三件套**通过后再「暂存离开」
5. **作品描述用 `fill()`**（React 受控，`value=` 不生效）
6. **草稿页只补竖封面**时从 `enter_from=draft` 继续即可

### 🟡 B站封面上传不可靠（v1.9.1 新增）
**问题**：B站隐藏 file input 的 accept 属性不包含图片类型（只有视频格式），且通过封面编辑弹窗上传的图片不一定被应用。

**解决**：B站封面建议手动上传，或跳过封面使用系统默认第一帧。

### 🟡 TTS 超时重试（v1.9.1 新增）
**问题**：mimo-tts.sh 首次调用可能超时（exit code 28），但重试后成功。

**解决**：TTS 调用失败后自动重试一次，不要立即报错。

### 🟡 视频号需要独立登录（v1.9.1 新增）
**问题**：视频号助手与公众号使用不同的登录会话，需要微信扫码登录，不能复用公众号的 cookie。

**解决**：视频号上传前必须先扫码登录，建议在 Phase 13 开始时提示用户。

### 🟡 抖音发布可能不需要验证码（v1.9.1 新增）
**问题**：抖音发布在某些情况下可以直接发布，不需要短信验证码（与账号信任度、设备指纹有关）。

**解决**：先尝试直接发布，如果弹出验证码再让用户手动输入。

### 🟡 周报封面上传到正文（v1.9.2 新增）
**问题**：周报封面上传到公众号正文时，file chooser 可能不触发。

**解决**：使用 `input.setInputFiles()` 直接设置文件：
```javascript
const input = await page.$('input[type="file"][accept*="image"]');
await input.setInputFiles('news-pipeline/weekly/.../horizontal-4-3.png');
```

### 🟡 周报B站合集自动选择（v1.9.2 新增）
**问题**：周报上传到B站时，合集「羊报AI周刊」可能不会自动选择。

**解决**：合集选择器是自定义 Vue 组件，建议手动选择或跳过。如果需要自动化，使用 `page.getByText('「羊报AI周刊」', { exact: true })` 精确匹配。

### 🔴 API 连接超时问题（v2.2.0 新增，2026-06-13）
**问题**：prism API（ai.prism.uno）在某些网络环境下连接超时，curl 显示 "Failed to connect to ai.prism.uno port 443 after 30001 ms: Timeout was reached"。

**原因**：可能是 DNS 解析问题或网络限制（GFW、企业防火墙等）。

**解决**：
1. 优先使用 eo.ioll.pp.ua（OpenRouter）作为备选 API
2. 如果用户提供的 API 不可用，自动尝试备选 API
3. 不需要询问用户，直接切换

**API 源优先级**：
1. 用户提供的 API
2. eo.ioll.pp.ua（OpenRouter）- 2026-06-13 验证可用
3. ai.prism.uno - 可能需要 VPN
4. api.luka77.cc

### 🔴 视频归档遗漏（v2.2.0 新增，2026-06-13）
**问题**：视频渲染完成后没有自动复制到日报目录，导致上传时找不到视频文件。

**解决**：Phase 9 视频合成完成后，立即执行归档：
```bash
cp "news-pipeline/video-project/out/【YYYY-MM-DD】{核心标题}… | 今日羊报AI.mp4" \
   "news-pipeline/YYYY-MM-DD/video/"
```

**归档时机**：视频合成完成后立即执行，不要等到上传阶段再复制。

### 🔴 封面生成不完整（v2.2.0 新增，2026-06-13）
**问题**：异步生成封面时，只生成了部分封面（如 1/2），另一张封面因 API 超时或错误未生成。

**解决**：
1. 每张封面生成后自动重试一次
2. 生成完成后验证所有封面文件
3. 如果封面不完整，同步补生成缺失的封面

**验证方法**：
```bash
ls -la news-pipeline/YYYY-MM-DD/*.png | wc -l
# 应该输出 2（horizontal-4-3.png【4:3 横版】, vertical-3-4.png【3:4 竖版】）
```

### 🔴 公益站内容过滤（v2.2.0 新增，2026-06-13）
**问题**：日报视频中不应包含公益站、中转站、倒卖相关内容。

**解决**：Phase 1 事件筛选时，主动过滤以下类型内容：
- 公益站上架/开通/故障
- 中转站价格/稳定性讨论
- 邀请码/兑换码分享
- 倒卖/交易相关内容

**选择事件时只保留**：模型发布、公司动态、安全事件、开源模型、行业政策、技术突破等。

### 🔴 周报所有上传保存草稿（v2.4.0 新增，2026-06-14）

**问题**：周报视频上传到各平台时，直接发布存在风险（标题/封面/合集可能需要调整）。

**解决方案**：周报模式下，所有平台上传一律保存草稿，不直接发布。

**具体流程**：
| 平台 | 操作 | 说明 |
|------|------|------|
| B站 | 保存草稿 | 周报可选择直接投稿或存草稿 |
| 公众号 | 保存草稿 | 标题+正文已填，封面/原创/合集需手动 |
| 视频号 | 保存草稿 | 描述+短标题已填，封面/合集需手动 |
| 抖音 | 暂存离开 | 描述+封面已填，合集/发布需手动 |

**Why:** 周报内容比日报更正式，用户需要二次确认标题、封面、合集等信息后再发布
**How to apply:** SKILL.md 周报上传流程中，所有平台最后一步改为「保存草稿」而非「发布/投稿」

### 🔴 抖音草稿页竖封面入口（v3.5.0 新增，2026-07-16；v3.6.0 补强）

**问题**：从草稿箱打开投稿页（`enter_from=draft`）时，横封面点「完成」后**不一定**弹出「设置竖封面」；旧文档写的「弹窗必现」在草稿流失效，导致竖封面一直缺失。

**解决**：
1. 横封面：语义找「横封面4:3」→ 同卡「选择封面」→ `force` 点「上传封面」→ `horizontal-4-3.png` →「完成」
2. 竖封面：若无弹窗，用「竖封面3:4」标签的 `getBoundingClientRect`，点击 **标签上方约 50–80px** 的封面框打开编辑器
3. 再 `force` 点「上传封面」→ `vertical-3-4.png` →「完成」
4. 验收文案无「竖封面缺失」/「横/竖双封面缺失」后「暂存离开」

**Why:** 首次投稿页与草稿编辑页 UI 分支不同；硬编码坐标在不同窗口尺寸下也易失效  
**How to apply:** Phase 14.6 已改为语义优先 + 草稿页专用竖封面点击逻辑

### 🔴 抖音封面「完成」按钮非 button role（v3.6.0 新增，2026-07-17）

**问题**：竖封面已通过 `filechooser.setFiles` 上传成功、弹窗里也能看到预览，但 `getByRole('button', { name: '完成' })` **count=0**，脚本以为点了完成、实际没点上；或过早点完成导致状态未写入，发文助手仍报「竖封面缺失」。

**解决**：
1. `setFiles` 后 **wait 1.5–3s**，等预览区出图
2. 用 `page.locator('text=完成').last().click({ force: true })`；失败再 `evaluate` 点 **y 最大、宽>40** 的「完成」节点
3. 点完再读 `innerText`：若仍含「设置竖封面」→ 再点一次完成
4. **禁止**在未完成时关弹窗并对「封面未保存」点「确定」
5. 最终验收：`missingV=false && missingDual=false && !hasSetDialog` 再「暂存离开」

**Why:** 抖音封面弹窗主按钮常用自定义 div/span，不是 accessibility button  
**How to apply:** Phase 14.6 步骤 3/6 一律按 text/evaluate 完成 + 双次确认

### 🔴 抖音只补竖封面场景（v3.6.0 新增，2026-07-17）

**问题**：横封面已在草稿中，只缺竖封面时，全流程重跑浪费时间；误操作还可能冲掉横封面。

**解决**：
1. 直接打开草稿：`https://creator.douyin.com/creator-micro/content/post/video?enter_from=draft`（或内容管理→编辑）
2. **跳过横封面**，只做竖封面打开→上传→完成→验收
3. 验收通过后「暂存离开」

**Why:** 发文助手单独报「竖封面缺失」时横封面往往已 OK  
**How to apply:** 用户说「补竖封面」时走最小路径，不重传视频/横封面

### 🔴 公众号封面不阻塞草稿（v3.5.0 新增，2026-07-16）

**问题**：「从正文选择」链路偶发失败（file chooser 不弹、上传中弹窗挡保存、class 选择器找不到），若强依赖封面会导致整篇无法存草稿。

**解决**：
1. 完整链路仍优先：工具栏图片→本地上传封面图（`horizontal-4-3.png` 横版 / `vertical-3-4.png` 竖版，均按公众号头条封面 900×383 自动裁剪）→ hover 封面区 → `.js_selectCoverFromContent` → 下一步 → 确认
2. chooser 不弹：`input[type=file][accept*=image].setInputFiles(...)` 兜底
3. 上传中弹窗：等待 8–15s + Escape 再点「保存为草稿」
4. **封面失败也要保存草稿**；成功信号优先看 URL 是否含 `appmsgid=`

**Why:** 正文/原创比封面更关键，封面可在草稿箱手补  
**How to apply:** Phase 12.7 已写降级原则与 setInputFiles 兜底

### 🔴 抖音双封面上传（v2.4.0 新增，2026-06-14）

**问题**：抖音需要同时上传横封面（4:3）和竖封面（3:4），竖封面弹窗会在横封面完成后自动弹出。

**解决方案**：
1. 先上传横封面（4:3）→ 点击「完成」
2. 弹出「设置竖封面获更多流量」弹窗 → 点击「设置竖封面」
3. 上传竖封面（3:4）→ 点击「完成」
4. 如果弹窗点击「暂不设置」，可后续在编辑页面补充

**封面文件**：
- 横封面：`horizontal-4-3.png`（1536x1152，4:3）
- 竖封面：`vertical-3-4.png`（1152x1536，3:4）

**Why:** 抖音个人主页显示竖封面，搜索结果展示横封面，两者都需要
**How to apply:** 抖音上传时必须上传双封面，竖封面可在横封面完成后通过弹窗上传

### 🟡 视频号需要独立登录（v2.4.0 确认，2026-06-14）

**问题**：视频号助手与公众号使用不同的登录会话，需要微信扫码登录。

**解决方案**：
1. 首次访问视频号助手时提示扫码登录
2. 登录后在同一浏览器会话中保持登录状态
3. 视频号页面内容在 iframe 中（`name="content"`），操作需用 `page.frame({ name: 'content' })`

**Why:** 视频号和公众号是两个独立的产品，登录系统不互通
**How to apply:** Phase 13 开始时检查是否已登录，未登录则提示用户扫码

### 🟡 抖音上传页面导航问题（v2.4.0 新增，2026-06-14）

**问题**：抖音创作者中心页面导航偶尔超时（`net::ERR_ABORTED`），可能需要重试。

**解决方案**：
1. 首次导航失败后重试一次
2. 如果仍然失败，提示用户手动打开抖音创作者中心
3. 草稿编辑链接：`https://creator.douyin.com/creator-micro/content/post/video?enter_from=draft`

**Why:** 抖音页面有复杂的前端路由和弹窗拦截，Playwright 导航可能被中断
**How to apply:** 导航失败时自动重试，不询问用户

### 🔴 Agent 工具生成封面失败（v2.5.0 新增，2026-06-16）

**问题**：使用 `Agent(run_in_background=True)` 异步生成封面时，Agent 遇到 Bash 权限被拒绝，无法执行 curl 和 Python 脚本。

**解决方案**：不要用 Agent 工具生成封面。直接在主线程中用 Python 脚本串行生成所有封面。封面生成（5个，约 3-5 分钟）和 TTS 配音（7个，约 2-3 分钟）串行执行总时间约 8 分钟，可以接受。

**Why:** Agent 工具在执行 Bash 命令时会遇到权限问题，无法完成 API 调用和文件操作
**How to apply:** 封面生成直接用 `Bash` 工具执行 Python 脚本，不用 Agent

### 🔴 克隆音色太机械（v2.5.0 新增，2026-06-16）

**问题**：使用曼波/阿根的克隆音色（voiceclone）生成的 TTS 在新闻播报场景下听起来太机械、不自然，用户反馈"配音太机械"。

**解决方案**：使用 MiMo 预置音色「白桦」（男性，中文），效果远好于克隆音色。其他可选预置音色：苏打（男）、冰糖（女）、茉莉（女）。

**Why:** 克隆音色在短句和新闻播报场景下表现不佳，预置音色经过专业调优
**How to apply:** TTS 默认使用 `mimo-v2.5-tts` 模型 + `voice: "白桦"`，不要用 `mimo-v2.5-tts-voiceclone`

### 🟡 MIMO_TTS_API_KEY 未配置（v2.5.0 新增，v2.8.0 更新，v3.2.0 更新）

**问题**：mimo-tts.sh 脚本报错 `MIMO_TTS_API_KEY not found`，因为 ~/.claude/settings.json 的 env 中没有配置该变量。

**v2.8.0 新发现**：settings.json 中 `MIMO_TTS_API_URL` 可能包含 `/anthropic` 后缀（如 `https://token-plan-cn.xiaomimimo.com/anthropic`），这是 **错误的**！正确 URL 格式为 `https://token-plan-cn.xiaomimimo.com/v1/chat/completions`（不带 `/anthropic`）。

**v3.2.0 新发现**：settings.json 中可能根本没有 MIMO_TTS_API_KEY 和 MIMO_TTS_API_URL 配置。此时必须使用环境变量方式调用 mimo-tts.sh，而不是依赖 settings.json。

**解决方案**：
1. **首选方案（v3.2.0）**：使用环境变量方式调用 mimo-tts.sh
   ```bash
   MIMO_TTS_API_URL="https://your-api-url.com" MIMO_TTS_API_KEY="sk-your-key" \
   bash ~/Documents/learn-claude-code/skills/mimo-tts/scripts/mimo-tts.sh \
     --text "配音文本" --voice "白桦" --style "新闻播报" \
     --output "news-pipeline/YYYY-MM-DD/voiceover/sceneN.wav"
   ```
2. **备选方案**：如果环境变量方式也失败，直接用 Python+curl 调用 MiMo TTS API
3. **URL 校验**：如果 settings.json 中的 URL 以 `/anthropic` 结尾，需要去掉 `/anthropic` 再拼接 `/v1/chat/completions`
4. API 格式：`POST {API_URL}/v1/chat/completions`，body 格式见 mimo-tts.sh 源码

**Why:** TTS API Key 和图片 API Key 是分开的，需要分别收集。settings.json 可能没有 TTS 配置。
**How to apply:** 预授权时额外收集 TTS API URL + Key。Phase 6 TTS 生成时，先尝试环境变量方式，失败再用 Python 直接调用。

### 🟡 脚本风格必须"说人话"（v2.5.0 新增，2026-06-16）

**问题**：默认生成的脚本风格偏播音腔、书面化，用户反馈"观众要求说人话"。

**解决方案**：脚本生成时强调口语化、像跟朋友聊天、不要堆砌术语。具体要求：
- 不要"各位观众大家好"式的开场
- 用"说白了"、"这谁不爱"、"怕是要来了"等口语表达
- 保留情绪感但不要夸张
- 每段不超过 80 字

**Why:** B站观众更喜欢自然、真实的表达方式
**How to apply:** Phase 2 脚本生成时，风格要求第一条改为"说人话"

## 注意事项

- **权限预授权是第一步**，覆盖内容生成 + 全部平台上传，一次确认后全程不再询问
- 每个 Phase 完成后向用户展示中间结果，确认后继续
- 图片生成失败时自动重试一次
- TTS 使用 mimo-tts，推荐预置音色「白桦」（不要用克隆音色！）
- **TTS 必须串行执行，禁止并行！**
- 视频总时长按 `REPORT_MODE`：daily 60-120s（≤150s）/ weekly **100-150s**（深聊型，替代旧 90-120s）/ **monthly 180-240s（≤300s）**
- 事件数量建议 4-6 个（日报/周报）
- **默认全模式 3W + 可信度**（v3.4）；精简 = 3-5 条 + 更短句，总时长约 60-100s
- **灰色渠道每期 ≤1**；情绪黑名单见 `templates/credibility-and-tone.md`
- **精简模式可与破格模式、周报模式、月报模式叠加使用**
- **月报模式事件数为 4 趋势主线**（精简月报 3 趋势），不要套用日报 4-6 单日事件
- **月报模式每段 ≤100 字**（趋势段落比日报单事件长）
- **月报 B站简介强制全数字中文化**（见 B站简介数字中文化章节，月报数据全数字，不中文化必触发违规推广检测）
- **月报合集「羊报AI月报」需用户预先在 B站/公众号后台创建**，否则上传 Phase 失败
- **月报不重新聚合**：直接消费 linuxdo-daily v13 的 `data/monthly/{YYYY-MM}.md`，不读取当月日报
- **月报去重改为对比上期月报**（`data/monthly/{上月}.md`），不扫 30 天日报（月报本身已跨日去重）
- **Phase 1 去重是强制步骤，不可跳过**（月报模式改为对比上期月报，同样不可跳过）
- **Phase 1 Step 1.6 专业锚点选题是强制步骤**（用户可选手动换概念或跳过；算法见 `templates/professional-anchor.md`）
- **Phase 2 用户确认脚本后必须写 `ai-concept-bank` usage-log**（`ANCHOR_SKIP` 除外），再进 Phase 3
- **专业锚点台词只读 eligible ready**（narrator + reviewed + 非空）；否则调 `ai-concept-narrator`，禁止主会话瞎编长段
- **Phase 8（渲染前校验）是强制步骤，不可跳过**
- **字幕必须使用原始脚本文本 + ffprobe 对齐**，不用 FunASR（专业术语识别率太低）
- **B站自定义下拉框必须用 JS evaluate，不能用 browser_click 文本匹配**
- **封面生成应与 TTS 并行执行**（用 Agent 异步），节省 3-5 分钟

### imageId 偏移问题（v2.7.0 修复，v2.8.0 补充）

Composition.tsx 中 imageId 与实际图片文件可能存在偏移。验证方法：
```bash
# 对比文件大小确认 public 目录的文件是否正确
ls -la news-pipeline/video-project/public/images/scene*.png
ls -la news-pipeline/YYYY-MM-DD/images/scene*.png
# 用 md5 验证
for i in 1 2 3 4 5 6; do
  src=$(md5 -q news-pipeline/YYYY-MM-DD/images/scene${i}.png)
  pub=$(md5 -q news-pipeline/video-project/public/images/scene${i}.png)
  [ "$src" = "$pub" ] && echo "scene${i}: OK" || echo "scene${i}: MISMATCH"
done
```

如果图片内容正确但视频中错位，修改 Composition.tsx 的 imageId 映射，而不是重新生成图片。
常见原因：上次渲染的 sceneConfig 未更新，或 scene 数量变化导致 ID 整体偏移。

**v2.8.0 补充**：偏移最常见的根因是 Hook 场景独立生成了一张图片，而脚本中 Hook 与第一条新闻是同一个场景。
预防措施：Phase 4 生成 prompt 时，图片数量必须与脚本场景数一致（见 Phase 4 图片-脚本映射铁律）。

### 公众号封面上传（自动方法）

公众号编辑器上传图片有两种路径：

**路径 A：工具栏「图片」按钮（推荐）**
```javascript
// 1. 点击正文区域获取 focus
await page.evaluate(() => {
  const editors = document.querySelectorAll('.ProseMirror');
  if (editors[1]) editors[1].click();
});
// 2. 点击工具栏「图片」→「本地上传」
// 3. 用 hidden file input 上传（封面图：horizontal-4-3.png 横版 / vertical-3-4.png 竖版）
const input = await page.$('input[type="file"][accept*="image"]');
await input.setInputFiles('news-pipeline/YYYY-MM-DD/horizontal-4-3.png');
```

**路径 B：封面区域直接上传**
```javascript
// 1. 找到封面区域的 file input（可能有多个）
const inputs = await page.$$('input[type="file"]');
// 2. 筛选 accept 包含 image 的
for (const input of inputs) {
  const accept = await input.getAttribute('accept');
  if (accept && accept.includes('image')) {
    await input.setInputFiles('news-pipeline/YYYY-MM-DD/horizontal-4-3.png');
    break;
  }
}
```

### B站封面上传（自动方法）

B站上传页面的封面选择器是隐藏的 file input：
```javascript
// 1. 先点击「更改封面」按钮
// 2. 找到 hidden file input 并上传
const input = await page.$('input[type="file"][accept*="image"]');
await input.setInputFiles('news-pipeline/YYYY-MM-DD/horizontal-4-3.png');
// 3. 等待上传完成，点击确认
```

### 🔴 所有平台上传一律存草稿（v2.8.0 新增，2026-06-29 确认）

**问题**：自动发布/投稿存在风险，标题、封面、合集等可能需要用户二次确认。

**解决方案**：所有平台上传后一律保存草稿，不直接发布。用户可在各平台草稿箱中检查后手动发布。

**各平台存草稿操作**：
| 平台 | 操作 | 说明 |
|------|------|------|
| B站 | 点击「存草稿」 | 替代「立即投稿」 |
| 抖音 | 点击「暂存离开」或关闭标签页 | 视频自动保存到草稿箱 |
| 视频号 | 点击「保存草稿」 | 视频进入草稿箱 |
| 公众号 | 点击「保存为草稿」 | 文章进入草稿箱 |

**Why:** 自动发布容易出错，用户需要二次确认内容
**How to apply:** Phase 11-14 所有平台上传最后一步改为存草稿，不要点击发布/投稿

### 🔴 视频号 iframe 上传复杂（v2.8.0 新增，2026-06-29 确认）

**问题**：视频号页面内容在 iframe 中，文件上传的 file input 在 iframe 内部，Playwright 的 `frame.$()` 有时找不到动态创建的 input。

**解决方案**：
1. 先检查 iframe 结构：`page.frames()` 找到 `name="content"` 的 iframe
2. 在 iframe 内用 `frame.evaluate()` 操作 DOM
3. 如果 file input 找不到，提示用户手动上传

**Why:** 视频号使用 Ant Design 的 Upload 组件，file input 是动态创建的
**How to apply:** 视频号上传如果自动化失败，直接跳过提示用户手动操作

### 🟡 抖音封面弹窗关闭确认（v2.8.0 新增，2026-06-29 确认）

**问题**：抖音封面编辑弹窗关闭时会弹出确认对话框「你有未保存的封面编辑效果，是否关闭？」。

**解决方案**：点击「确定」关闭弹窗，封面已自动保存。

**Why:** 抖音的封面编辑器有防误关机制
**How to apply:** 关闭封面弹窗时如果出现确认对话框，点击「确定」

### 🟡 抖音章节要点弹窗（v2.8.0 新增，2026-06-29 确认）

**问题**：抖音上传视频后会自动弹出「章节要点」弹窗，阻挡后续操作。

**解决方案**：关闭章节弹窗（点击 X 或取消），不影响视频发布。

**Why:** 抖音自动检测视频内容生成章节建议
**How to apply:** 上传视频后如果出现章节弹窗，直接关闭

### 🔴 公众号弹窗阻挡「保存为草稿」（v3.3.0 新增，2026-07-05）

**问题**：公众号封面图上传后弹出「图片上传中，请稍后」弹窗，此时点击「保存为草稿」无效（被弹窗拦截）。弹窗不会自动关闭，需要等待图片上传完成。

**解决**：
1. 上传封面图后等待 10 秒再操作（`browser_wait_for(time=10)`）
2. 保存前检测是否有弹窗阻挡：`document.body.textContent.includes('上传中')`
3. 如果仍有弹窗，按 Escape 关闭弹窗后再保存
4. 验证保存成功：`document.body.textContent.includes('已保存')`

```javascript
// 保存前自动处理弹窗
browser_run_code_unsafe("""async (page) => {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
  await page.waitForTimeout(5000);
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('button');
    for (const btn of buttons) {
      if (btn.textContent.trim() === '保存为草稿') {
        btn.click(); return;
      }
    }
  });
  await page.waitForTimeout(3000);
  const body = await page.evaluate(() => document.body.textContent);
  return body.includes('已保存') ? 'saved!' : 'failed';
}""")
```

**Why:** 公众号图片上传是异步的，但弹窗会阻挡所有按钮点击
**How to apply:** Phase 12 公众号上传时，封面图上传后等10s，保存前先Escape关闭弹窗

### 🟡 公众号合集选择失败时自动跳过（v3.3.0 新增，2026-07-05）

**问题**：公众号合集选择器用 `page.getByText('「羊报AI周刊」', { exact: true })` 精确匹配时，可能因合集名不完全匹配而超时（如合集名实际为「羊报AI周刊」vs页面显示差异）。

**解决**：合集选择失败时自动跳过，不阻塞保存草稿。合集可后续手动添加。

```javascript
// 合集选择带超时保护
try {
  const option = page.getByText('「羊报AI周刊」', { exact: true });
  await option.hover({ timeout: 5000 });
  await option.click();
} catch (e) {
  console.log('合集选择跳过: ' + e.message);
  await page.keyboard.press('Escape');
}
```

**Why:** 合集选择器是自定义 Vue 组件，匹配规则不稳定
**How to apply:** Phase 12 公众号合集选择用 try-catch 包裹，失败时 Escape 跳过

### 🔴 B站封面上传 file input 无 image accept（v3.3.0 新增，2026-07-05）

**问题**：B站上传页面有 4 个 file input，但没有任何一个的 accept 属性包含 image 类型。之前用 `input[accept*="image"]` 找不到封面 input。

**解决**：封面 file input 通常在 inputs 数组的第 2 个位置（index 1）。按位置索引设置文件：
```javascript
const inputs = await page.$$('input[type="file"]');
// inputs[0]: 视频 (.mp4)
// inputs[1]: 封面 (通过封面设置弹窗触发)
await inputs[1].setInputFiles('horizontal-4-3.png');
```

或者跳过自动封面上传，提示用户手动上传。

**Why:** B站的 file input 使用动态 accept 属性，不包含 image
**How to apply:** Phase 11 B站封面上传时，用 inputs[1] 或提示手动上传

### 🔴 精简模式脚本审核必须前置（v3.3.0 新增，2026-07-05）

**问题**：脚本生成后直接展示给用户，但没有先执行脚本审核检查清单。用户需要提醒才执行审核。

**解决**：脚本生成后、展示给用户前，**必须先执行审核检查清单**，审核结果和脚本一起展示：

```
## ✅ 脚本审核检查
1. 禁止词汇检查 ✅
2. 口语化程度 ✅
3. 平台合规审查 ✅
4. 标题检查 ✅
5. 内容准确性 ✅

## 📝 脚本内容
[完整脚本]
```

**Why:** 用户期望审核是自动执行的，不需要手动提醒
**How to apply:** Phase 2 脚本生成后，先审核再展示，审核不通过则修改后再展示

### 🟡 周报去重需对比上周周报（v3.3.0 新增，2026-07-05）

**问题**：周报模式的去重策略是「对比上一期周报」，但实际执行时没有找到上周周报文件，跳过了去重。

**解决**：如果上周周报文件不存在（`data/reports/2026-W26.md`），跳过去重步骤，但在脚本审核时标注「未去重」。

**Why:** 周报文件可能不存在（首次生成或文件被清理）
**How to apply:** Phase 1 周报去重时，先检查上周周报文件是否存在，不存在则跳过

### 🔴 MCP 与独立 Playwright 互抢 Profile（v3.7.0 / 2026-07-18）
**问题**：流水线中为视频号上传反复 `pkill` 共用 profile，用户感知「浏览器老是退出」。
**解决**：见文首「浏览器与 Profile 全局铁律」；仅在切换驱动时 scoped kill；向用户解释关闭原因。
**Why:** 同一 `user-data-dir` 不能被两个 Chromium 同时占用。
**How to apply:** 视频号优先 MCP 闭环；独立脚本仅作 fallback。

### 🔴 视频号双 body 导致 MCP 工具层崩溃（v3.7.0 / 2026-07-18）
**问题**：`strict mode violation: locator('body') resolved to 2 elements`（外层 + wujie-app body）。
**解决**：单次 `browser_run_code_unsafe` 完成关键步骤；返回前导航到 baidu/about:blank；禁止在双 body 页用 snapshot/find/file_upload。
**How to apply:** Phase 13 全程遵守。

### 🔴 视频号封面 3:4/4:3 与 CDP setFileInputFiles（v3.7.0 / 2026-07-18）
**问题**：`input[accept=image/*]` 在 `.single-cover-uploader-wrap` 中 `display:none`，跨 frame `setInputFiles` 报 detached；须等「预览图生成中」结束。
**解决**：点对应比例「编辑」后，用 CDP `DOM.performSearch` + `backendNodeId` + `DOM.setFileInputFiles`；4:3 已多次验证成功，3:4 同法但须点中 `.vertical-cover-wrap` 的编辑。
**How to apply:** Phase 13 封面步骤。

### 🔴 公众号「从正文选择」缩略图非 img 标签（v3.7.0 / 2026-07-18）
**问题**：弹窗缩略图是 `span.appmsg_content_img.cover` + background-image，`img` 列表为空导致无法选中、「下一步」不进入裁剪。
**解决**：点 `.appmsg_content_img_item`；裁剪点「确认」；验收看 `#js_cover_area .js_cover_preview_new` 的 background-image。
**How to apply:** Phase 12 封面。

### 🔴 公众号裁剪确认与验收（v3.8.0 / 2026-07-19 周报实测）
**问题**：
1. 点「下一步」后进入「编辑封面」，页面同时存在 **disabled「确定」** 与 **「确认」**；点错会超时/`Element is not visible`
2. 过早 `Escape` 会关掉裁剪，preview 仍为 `display:none` / `url("")`
3. 成功后文案区仍可能显示「拖拽或选择封面」，误判为失败

**解决**：
1. 只点 `button` 文本精确为 **「确认」** 且 `class` 含 `weui-desktop-btn_primary`、**不含** `disabled`
2. 裁剪弹窗打开期间 **禁止 Escape**
3. 成功条件：`.js_cover_preview_new` 的 `display==='block'` 且 `background-image` 含 `mmbiz`/`qpic`；可再存草稿（`appmsgid=` 保留）
4. 已有草稿用 `appmsg?…&appmsgid=` 直达编辑，比「新的创作」稳

**Why:** 2026-07-19 周报 `appmsgid=100000479` 封面链路完整复现后才闭环。  
**How to apply:** Phase 12.7 一律走 v3.8.0 轮询验收。

### 🟡 B站存草稿成功信号（v3.8.0 / 2026-07-19）
**问题**：第二次再找「存草稿」按钮可能 `not found`，但 URL 已跳到 `upload-manager/article?group=draft`。
**解决**：以 **URL 含 `group=draft`** 为成功；中文文件名先复制为 `upload-weekly-w28.mp4` / `upload-YYYY-MM-DD.mp4` 再传。
**How to apply:** Phase 11 末检查 URL。

### 🟡 视频号未登录不阻塞流水线（v3.8.0 / v3.9.0）
**问题**：`channels.weixin.qq.com` 落到 `login.html` 扫码页时整条流水线挂起。
**解决**：检测到登录页 → 标记 `channels: login_required`，继续抖音/公众号；向用户汇报需扫码后手传。
**How to apply:** Phase 13 开头检查 title/URL 含 login。

### 🔴 视频号「用户已登录」≠ MCP 已登录（v3.9.0 / 2026-07-20 实测）
**问题**：用户说「视频号已经登录」后，MCP 仍停在 `login.html`；`net::ERR_HTTP_RESPONSE_CODE_FAILURE`；QR iframe「加载失败，点击重试」；在错误 profile 上反复刷新二维码空转。
**解决**：
1. **以 MCP 页为准**：`page.url()` 含 `login.html` 或标题/正文含「登录视频号助手」→ 仍 `login_required`
2. 用户本机其它 Chrome 已登录**不能**代替 MCP profile
3. 需要扫码时：在 **MCP 当前标签**出码，等 URL 离开 login 再上传；二维码加载失败可 `page.reload` 1–2 次，仍失败则写 `upload-status.md` 为 ⏭ 并**停止空转**
4. `ERR_HTTP_RESPONSE_CODE_FAILURE` 于 channels 域名：等 5–10s 重试 1 次；持续失败按未登录跳过
5. 禁止生成大量无执行价值的 `CHANNELS_*_GUIDE.md` 代替实际上传
**Why:** 0720 多轮「已经登录继续上传」仍卡 QR，浪费会话。
**How to apply:** Phase 13 入口硬判定 + upload-status 落盘。

### 🔴 抖音「暂存」不等于草稿可见（v3.9.0 / 2026-07-20）
**问题**：上传页操作看似成功，内容管理无当日草稿；用户反馈「抖音没看到草稿」。
**解决**：以「继续编辑」/ 内容管理标题 / draft 页非空表单验收；失败整段重传。
**How to apply:** Phase 14.10 验收三信号。

### 🔴 竖封面必须用当期 vertical-3-4.png（v3.9.0）
**问题**：补封面时用错图或比例不对，用户明确「竖封面3:4 不对」。
**解决**：只认 `news-pipeline/{date}/vertical-3-4.png`；上传后仍要 `missingV=false`。
**How to apply:** Phase 5.5 生成 + 14.6/14.10 补传。

### 🟡 TTS 503 网关无节点（v3.9.0）
**问题**：`gateway_error: 没有可用的内网节点`。
**解决**：退避重试 + fallback URL；校验 wav 非空。
**How to apply:** Phase 6。

### 🟡 免确认仍要审核落盘（v3.9.0）
**问题**：免确认时只自检不落盘，用户追问「有没有通过审核清单」。
**解决**：写 `review-checklist.md` 或 script 文末表。
**How to apply:** Phase 2 末。

### 🟡 图片/TTS API 读 settings.env（v3.8.0）
**问题**：主会话手写 API 易漏备选；打印 key 被安全策略拦截。
**解决**：从 `~/.claude/settings.json` 的 `env` 读 `GEN_IMG_API_URL`/`GEN_IMG_API_KEY`（及 `_001/_002`）、`MIMO_TTS_API_URL`/`MIMO_TTS_API_KEY`；脚本内 fallback，**日志禁止打印 key**。
**How to apply:** Phase 5/6 生成脚本。

### 🟡 抖音竖封面必须带日期（v3.7.0 / 2026-07-18）
**问题**：竖封面生成失败时用 scene 图回退，用户反馈「上面没日期」。
**解决**：`vertical-3-4.png` 失败必须重试 GEN_IMG，prompt 强制底部 `YYYY-MM-DD` 与右上「今日羊报 AI」；禁止无品牌 scene 回退当封面。
**How to apply:** Phase 5.5 / 14.6。


### 🔴 GEN_IMG 多端点与 Bash 超时（v3.10.0 / 2026-07-21）
**问题**：7 张 scene 串行生成时 Bash 默认 10 分钟超时被 kill（exit 143）；部分端点 HTTP 000/502。
**解决**：
1. 从 settings.env 组装 endpoint 列表 `['', '_001', '_002']`，逐张生成、已有文件跳过
2. 单张 max-time 90–180s；整批超时按张数放大或拆成多条 Bash
3. 日志只打印 `set/empty/len`，禁止打印 key 前缀（安全策略会拦）
4. CTA scene 可兜底；`vertical-3-4.png` 必须当期生成成功
**How to apply:** Phase 5 / 5.5

### 🔴 usage-log 与 concepts 根结构（v3.10.0 / 2026-07-21）
**问题**：把 `concepts.json` 当 list 迭代 → `AttributeError: str has no get`。
**解决**：`data = json.load(...); concepts = data['concepts']`；usage-log 可能是 list 或 `{entries:[]}`，append 时兼容两种。
**How to apply:** Step 1.6 / Phase 2 写 log

### 🟡 公众号草稿成功但封面未闭环（v3.10.0 / 2026-07-21）
**问题**：`appmsgid=` 已出现，`.js_cover_preview_new` 仍 `display:none`。
**解决**：草稿优先；封面失败写 upload-status「可手补封面图（horizontal-4-3.png / vertical-3-4.png）」；不因封面阻塞汇报成功。
**How to apply:** Phase 12 + upload-status.md

### 🟡 B站存草稿后 URL 已是 group=draft（v3.10 再确认）
**问题**：脚本 `draftClicked=false` 但 URL 已跳转草稿箱。
**解决**：以 `group=draft` 为成功信号，不依赖按钮二次查找。
**How to apply:** Phase 11


### 🔴 GEN_IMG 整批 10 分钟超时后必须续跑缺失文件（v3.11.0 / 2026-07-22）
**问题**：scene1–7 已生成，`horizontal-4-3.png` 也生成了，但 `vertical-3-4.png` 还没跑完时 Bash 10min kill（exit 143）。若当成「封面全失败」会重跑 scene 浪费时间。
**解决**：
1. 超时后立刻 `ls` 校验每张 `sceneN.png` / 平台封面的 size（>5KB 视为成功）
2. **只补缺失文件**，禁止无条件重跑已有 scene
3. 封面可单独一条 Bash；scene 与 cover 可拆开执行
**How to apply:** Phase 5 / 5.5 超时后先盘点再补齐

### 🔴 GEN_IMG 全挂 / 封面文字糊掉时本地 Pillow 兜底（v3.19.0 / 2026-08-21）
**问题**：GEN_IMG 所有端点 401/余额耗尽（0821 实测 prism+luka77 全 401，仅 xmiaom 出图）；或 API 出封面但中文日期/品牌名糊掉错字——封面文字必须像素级准确。
**解决**：
1. Scene 图全挂 → `gen_images_local.py`（Pillow 画 8 张抽象背景，深色演播室 + 场景配色 + 几何 motif）
2. 封面 API 余额耗尽 / 文字糊掉 → `gen_covers_local.py`（拿 `scene1.png` 作底图 + 渐变蒙版 + 本地字体叠加日期/品牌）
3. 见 Phase 5.6 完整脚本模板与决策流程
**Why:** 0821 scene 图走 API 成功，但封面 API 余额耗尽，用本地 Pillow 叠加保证日期文字 100% 清晰。
**How to apply:** Phase 5.6；API 恢复后应切回 API（本地图为兜底非默认）

### 🔴 抖音 filechooser 链式打断后的恢复（v3.11.0 / 2026-07-22）
**问题**：横/竖封面 `waitForEvent('filechooser')` 与后续步骤叠在一次长 `run_code` 里时，工具层会停在「Modal state: File chooser」，后续逻辑不返回；取消 chooser 后可能落到 `upload?enter_from=publish` 空页。
**解决**：
1. **横封面 / 竖封面上传拆成独立短步骤**；出现 File chooser 模态时用 `browser_file_upload(paths=[...])` 处理，禁止在同一长脚本里「点上传+等 chooser+再点完成」硬串
2. 若被带回上传页：以是否出现 **「你还有上次未发布的视频 / 继续编辑」** 判定草稿已落库
3. 点「继续编辑」验收描述/视频是否在；封面缺失可手补，不必整段重传视频
**How to apply:** Phase 14 封面步骤拆分 + 上传页「继续编辑」验收

### 🔴 公众号「新的创作」菜单项 class（v3.11.0 / 2026-07-22）
**问题**：只点 heading「新的创作」不会开文章；文本匹配「文章」易命中别处。
**解决**：`.new-creation__menu-item` 第一项即「文章」，`menu[0].click()` 会新开 `appmsg_edit` 标签；再 `browser_tabs(select, index=最新)`。
**How to apply:** Phase 12.2

### 🟡 浏览器崩溃后先重建再上传（v3.11.0）
**问题**：连续 `mp.weixin` / `channels` / `baidu` 导航 Timeout 后，下一调用报 `Target page, context or browser has been closed`。
**解决**：`pkill -f mcp-chrome` → sleep → 重新 `browser_navigate`；不要在 closed target 上继续堆工具调用。
**How to apply:** 任意 Phase 11–14 导航连环超时后

### 🔴 视频号限流 + 公众号按《公众账号信息服务管理规定》删文（v3.13.0 / 2026-07-26）
**问题**：
- 视频号：状态「限制传播」，问题说明「存在敏感或者违规内容」，仅引用《视频号常见违规内容概览》，**无细码**
- 公众号：通知「接相关投诉，违反《互联网用户公众账号信息服务管理规定》，已删除」，**不写条款号**
- 同期成片标题/脚本含：Opus5 发布 + DeepSeek 融资外泄/暂停 + 开源「切断」/政策升温；封面为写实 AI 主播
**解决**：
1. 强制对照新文件：`微信视频号常见的不合规频道内容概述.md`、`微信公众号互联网用户公众账号信息服务管理规定.md`
2. 执行 `templates/platform-compliance.md`：选题 A/B 档；公众号默认不上 B 档；封面禁写实主播
3. 标题禁「同日升温/切断/外泄/博弈/风暴」；媒体信息标题勿写成定论
4. 视频号打 AI 生成标识；被处置后优先改封面+改文案重发，勿同题硬刚申诉
**Why:** 0726 双端同时处置，根因是「新闻体包装 + 融资/政策话术 + AI 真人封面」叠加，而非单句脏话/低俗
**How to apply:** Phase 1–2 / Phase 5.5 / Phase 10；review-checklist 必须含 platform-compliance §5

### 🔴 抖音「不适宜公开 / 仅自己可见·画面」与周报攻击叙事（v3.14.0 / 2026-07-26–27 周报）
**问题**：
1. 标题 `沙箱逃逸进立法·Kimi开源地缘` → 抖音 **不适宜公开**；视频号 **限制传播**（描述同样含逃逸/立法）
2. 换成产品向标题 + 新封面后仍 **限制自己可见**，违规原因标 **「画面」** → 机审扫的是**成片帧**，不是元数据
3. 原 scene prompt 含 security breach、cracked isolation glass、legislative silhouettes、gavel 等
4. 内部 `review-checklist` 黑名单/3W 全过，**仍过不了抖音/视频号机审**
**解决**：
1. 抖音/视频号/公众号主标题禁用：`逃逸/入侵/窃取/横向移动/立法/两党/终止开关/地缘`（作主卖点时）→ 见 `platform-compliance.md` §8
2. 推荐标题：`评测安全升级·Flash全量与订阅变化｜羊报AI周刊 …`；短标题：`本周AI安全与工具速览`
3. **画面违规强制过审重渲**：`voiceover-texts-safe.json` + `image-prompts-safe.json` 重画高风险 scene（建议 1/2/3/6 或全量）→ TTS → captions → Remotion → `*-safe.mp4`
4. 落盘 `platform-copy-safe.md` 供用户复制；旧敏感 mp4 归档勿再发
5. 只改标题/封面后重传旧片 = **无效**；必须新成片
**Why:** W29 周报同日双端处置；二次投稿证明「画面」标签独立于标题
**How to apply:** Phase 2 标题分平台；Phase 3–5 画面合规；处置后走 platform-compliance §6.1

### 🟡 公众号草稿「只补封面」（v3.14 / 2026-07-27）
**问题**：用户只要更新 `appmsgid=…` 封面，正文自理；自动化链路可能 `preview display:none` 仍点了确认/保存。
**解决**：
1. 直达 `appmsg?…&appmsgid=` → 正文插封面图（`horizontal-4-3.png` / `vertical-3-4.png`）→ 从正文选择 → 编辑封面 → **确认** → 保存草稿
2. 验收优先：`.js_cover_preview_new` 的 `display:block` + `mmbiz/qpic`；失败时**明确告知用户需手补**，不假装成功
3. 勿在用户未要求时改标题/正文
**How to apply:** Phase 12 封面-only 任务

### 🔴 TTS 禁止在工具参数里硬编码 API Key（v3.12.0 / 2026-07-25）
**问题**：Bash/Python 参数文本含 `sk-mimo-…` 时，自动模式安全分类器 **Credential Leakage** 直接拒绝；会话卡住。
**解决**：
1. 写 `news-pipeline/{date}/scripts/gen_tts.py`：**只从** `MIMO_TTS_API_*` 环境变量、`~/.claude/settings.json` env、或历史 `news-pipeline/*/scripts/gen-tts.sh` 的 export **读 key**（脚本内解析，**不**把 key 写进工具调用文本）
2. 运行：`python3 news-pipeline/{date}/scripts/gen_tts.py`（日志只打 `keylen` / 端点名）
3. endpoint 列表：历史 gen-tts 的 URL + `token-plan-cn` / `token-plan-ams` fallback；失败退避重试
4. 每 scene 校验 wav `>5KB`；已存在则跳过
**Why:** 0725 首次 TTS 因硬编码 key 被拒。
**How to apply:** Phase 6 一律「脚本读凭据」，禁止 `export MIMO_TTS_API_KEY=sk-...` 出现在工具参数里。

### 🔴 B站草稿补封面闭环（v3.12.0 / 2026-07-25）
**问题**：首次投稿常跳过封面；用户追问「封面上传了吗」。
**解决（草稿编辑页）**：
1. 打开 `upload-manager/article?group=draft` → 找当日标题 → `frame?type=draft&draftId=...`
2. 点 **「封面设置」**（`.cover-empty` / 坐标点封面框）→ 弹窗 **「封面制作」**
3. 弹窗内出现 `input[accept="image/png, image/jpeg"]`（可有多个：4:3 / 16:9）→ **`setInputFiles(horizontal-4-3.png)`**
4. 点底部 **「完成」**（y 较大的主按钮）
5. 验收：`.cover-empty` / `.cover-empty.failed` **消失**；`.cover-img` 的 `background-image` 含 `archive.biliimg.com` 或 `bfs/archive`
6. 再点 **「存草稿」**；成功信号仍是 URL `group=draft`
**标题坑**：稿件标题 `maxLength=80`，用 **原生 `HTMLInputElement` value setter** + `input` 事件，不要只靠 React 假赋值。
**Why:** 0725 草稿 `draftId=3685995` 封面补传成功。
**How to apply:** Phase 11 首次可先存草稿；缺封面则走本闭环，**不要**默认「建议用户手传」就结束。

### 🔴 视频号独立脚本 vs MCP Profile 锁（v3.12.0 / 2026-07-25）
**问题**：MCP 仍占用 `mcp-chrome-*` 时，`channels_upload.js` 报 `Failed to create a ProcessSingleton` / SingletonLock。
**解决**：
1. 跑独立脚本前：`browser_close` 或 `pkill -f mcp-chrome` → `rm -f …/SingletonLock` → sleep 2
2. 再用 `NODE_PATH=…/node_modules` + `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=…/Google Chrome for Testing` 启动
3. 若 URL 仍是 `login.html` → `login_required` ⏭，写 `upload-status.md`，**禁止空转扫码循环**
**Why:** 0725 视频号先被 profile 锁挡住，释放后仍 login_required。
**How to apply:** Phase 13 独立脚本路径；与文首「浏览器 Profile 铁律」一致。

### 🟡 抖音 filechooser + 暂存验收（v3.12 再确认 / 0725）
- 视频 / 横竖封面：`waitForEvent` 触发后工具层停在 **File chooser** → 下一步必须 `browser_file_upload(paths=[...])`
- 暂存后回上传页：出现 **「你还有上次未发布的视频…继续编辑」** 即草稿 ✅

### 🔴 抖音 Semi Design 组件拦截（v3.18.0 / 2026-08-18）
**问题**：抖音创作者中心基于 Semi Design，`label.semi-radio` 拦截自主声明 radio 的 pointer events（`locator.click()` 超时 30s）；`div.semi-modal-wrap` 拦截「暂存离开」按钮；`browser_run_code_unsafe` 触发 file chooser 后工具层停在 "Modal state: File chooser" 阻塞后续调用。
**解决**：
1. 自主声明 radio：`page.locator('label.semi-radio').filter({ hasText: '内容为个人观点或见解' }).click()`
2. 「暂存离开」：`page.keyboard.press('Escape')` → `waitForTimeout(1000)` → `locator('button:has-text("暂存离开")').click({ force: true })`
3. file chooser：用 `browser_file_upload(paths=[...])` 处理，不要在同一长脚本里串 `filechooser` 事件
**Why:** 0818 自主声明超时 30s、暂存离开被 modal 拦截、file chooser 卡 Modal state。
**How to apply:** Phase 14.8 自主声明 / 14.10b 暂存离开 / 14.2/14.6 文件上传

### 🔴 视频号 QR 跨域 iframe 无法自主扫码（v3.18.0 / 2026-08-18）
**问题**：`channels.weixin.qq.com` 重定向 `login.html`，QR iframe 来自 `open.weixin.qq.com`（跨域），iframe 显示「加载失败，点击重试」，点击重试 + 等 5s 仍不加载；跨域 iframe `contentDocument` 为 null，JS 无法访问；`page.reload` 1–2 次仍失败。
**解决**：reload 1–2 次仍失败 → 标记 `channels: login_required`，写 `upload-status.md` 为 `⏭`，停止空转；**明确**自主流程无法完成视频号扫码登录，需用户手动扫码后重跑。
**Why:** 0818 视频号 QR 跨域加载失败，自主流程空转无果。
**How to apply:** Phase 13.0b

### 🔴 抖音草稿恢复弹窗「继续编辑放弃」文本合并（v3.18.0 / 2026-08-18）
**问题**：上传页弹「你还有上次未发布的视频，是否继续编辑？」，点击合并文本「继续编辑放弃」无法精确丢弃旧草稿，会落到 `enter_from=draft` 编辑页混入旧素材；离开草稿编辑页时弹 beforeunload「将此次编辑保留？」，不处理会触发 `net::ERR_ABORTED`。
**解决**：从草稿编辑页点「重新上传」→ 导航回 upload 页 → 重新触发 file chooser；离开草稿页弹 beforeunload 时 `browser_handle_dialog(accept=true)`。
**Why:** 0818 旧草稿混入新上传，beforeunload 未处理导致导航失败。
**How to apply:** Phase 14.0

### 🟡 公众号 appmsgid 验收（v3.12 再确认 / 0725）
- `.new-creation__menu-item[0]` 开文章；标题/作者/正文 ProseMirror 注入；**保存为草稿** 后 URL 含 `appmsgid=`（0725：`100000512`）
- 封面可手补，不阻塞草稿成功

### 🔴 抖音草稿恢复弹窗「放弃」精确点击（v3.22.0 / 2026-08-28）
**问题**：上传页弹「你还有上次未发布的视频，是否继续编辑？」，点合并文本「继续编辑放弃」会落到 `enter_from=draft` 编辑页混入旧素材。
**解决**：用 JS evaluate 精确点 `textContent.trim() === '放弃'` 的可见按钮节点（勿点合并文本）；点完弹窗消失即恢复 upload 页空白上传区。
**Why:** 0828 实测点合并文本落到草稿编辑页，beforeunload 连环 + `net::ERR_ABORTED`。
**How to apply:** Phase 14.0

### 🔴 抖音封面选择被 @好友 mention 浮层拦截（v3.22.0 / 2026-08-28）
**问题**：点「横封面4:3」同卡的「选择封面」无反应——点击被 `publish-mention-wrapper`（话题/`@好友` 自动补全浮层）拦截。
**解决**：先 `keyboard.press('Escape')` 关浮层 → JS evaluate 找「设置封面」header → `parentElement` 攀爬到封面容器 → 点容器内第一个 `textContent === '选择封面'` 的 div。
**Why:** 0828 实测封面点击静默失败，发文助手仍报「竖封面缺失」。
**How to apply:** Phase 14.6 步骤1 之后兜底

### 🔴 抖音描述/话题 contenteditable 误用 nth(1)（v3.22.0 / 2026-08-28）
**问题**：`div[contenteditable="true"].nth(1)` 30s 超时——编辑页通常只有 1 个 contenteditable（描述/简介），话题另有入口。
**解决**：描述填 `contenteditable.nth(0)`；话题（#标签）改点「#添加话题」按钮 → `keyboard.type(tag)` + `keyboard.press('Enter')` 逐个加。
**Why:** 0828 实测 `nth(1)` 超时导致描述/话题卡住。
**How to apply:** Phase 14.5b

### 🔴 抖音合集名大小写陷阱（v3.22.0 / 2026-08-28）
**问题**：硬搜「今日羊报AI」返回 not found——实测抖音合集名是「「今日羊报Al」」（小写 L，非大写 I）+ 「共80个作品」，与 B站/公众号不同。
**解决**：探测下拉框可见文本，按「今日羊报」前缀（不分大小写）+ 「共N个作品」模糊匹配选项点击；勿硬编码精确合集名；snapshot 验收按前缀模糊匹配。
**Why:** 0828 实测硬编码精确名 not found，合集选择卡住。
**How to apply:** Phase 14.7

### 🔴 公众号原创声明 y 范围失效（v3.22.0 / 2026-08-28）
**问题**：「原创」标题实测在 `y=471`，旧代码 `rect.y < 400` 漏选，点不开原创声明弹窗。
**解决**：去 y 上界改为 `rect.y > 150 && rect.x > 500`；优先用 `.setting-group__title` 文本 === '原创' 定位，比全 `*` 扫描 + y 范围更稳。
**Why:** 0828 实测「原创」在 y=471，旧上界 400 漏选。
**How to apply:** Phase 12.8 步骤1

### 🔴 公众号合集输入框 getByRole 超时（v3.22.0 / 2026-08-28）
**问题**：合集弹窗未开时 `page.getByRole('textbox', { name: '请选择合集' })` 30s 超时。
**解决**：先 `document.querySelector('.js_article_tags_content').scrollIntoView({block:'center'})` + click 开弹窗，再用 `page.locator('input[placeholder="请选择合集"]')` 兜底定位输入框。
**Why:** 0828 实测弹窗未开时 getByRole 直接超时。
**How to apply:** Phase 12.10 步骤2

### 🔴 公众号正文 ProseMirror 拒绝 innerHTML 直接赋值（v3.23.0 / 2026-08-29）
**问题**：`bodyEditor.innerHTML = html` 返回"ok"但编辑器回滚，`pm.textContent.length === 1`——正文被静默清空，无报错。
**解决**：`focus()` → `range.selectNodeContents(pm)` → `sel.addRange(range)` → `document.execCommand('insertHTML', false, html)`；注入后回读 `textContent.length > 1000` 验证。
**Why:** ProseMirror 通过 selection/execCommand 管状态，直接 DOM 写入会被视图层丢弃。
**How to apply:** Phase 12.5（已重写，替代旧 innerHTML 方案）

### 🔴 公众号标题被正文注入操作灌入全文（v3.23.0 / 2026-08-29）
**问题**：正文注入操作导致标题框变成整篇文章（计数器 1776/64）。
**解决**：按 `data-placeholder` 含「标题」定位标题框 → `selectNodeContents` + `execCommand('delete')` + `execCommand('insertText', false, title)` 重置；**标题填写固定放到正文注入之后**。
**Why:** 注入时的 selection 操作可能落到标题框；索引定位在操作后会漂移。
**How to apply:** Phase 12.5b（新增）

### 🔴 公众号原创声明协议 checkbox 不自动勾选（v3.23.0 / 2026-08-29）
**问题**：旧文档称「自动勾选同意，直接点确定」；实测 `checked:false`，点「确定」no-op（弹窗不关）。
**解决**：点 checkbox 的 `closest('label')` 容器（点 input/文字 span 可能不切换）→ 验证 `checked===true` → 点「确定」；成功标志 = 弹窗关 + 「文字原创 · 已开启快捷转载」。
**Why:** weui-desktop checkbox 的 click handler 绑在 label 容器上。
**How to apply:** Phase 12.8（已修正）

### 🔴 公众号封面 4 子坑：hover 菜单/label 拦截/未选中/视口外 radio（v3.23.0 / 2026-08-29）
**问题**：①「从图片库选择」直接 click 报 not visible ②上传按钮被 webuploader-pick 内 `<label>` 拦截 ③图库首击未出现 selected ④2.35:1 radio 在视口外报 outside of viewport。
**解决**：① `page.mouse.move(coverBox.x, coverBox.y)` 先 hover 再 evaluate 点 ② `.single_upload_btn_container, .webuploader-pick` force click + waitForEvent('filechooser')（勿用含点动态 id 选择器）③ 回读 `.selected` 类验证，无则 evaluate 再点 ④ evaluate 点含 "2.35" 文本的 label/span。
**Why:** hover 菜单、webuploader 结构、选择态回读、视口外元素四类典型 Playwright 拦截。
**How to apply:** Phase 12.7c（新增）

### 🔴 抖音描述 editor-kit 编辑器 + 封面 SVG 拦截 + 封面路径（v3.23.0 / 2026-08-29）
**问题**：①描述编辑器实为 `.editor-kit-editor-container [contenteditable="true"]`，fill 可能不同步 ②封面上传图标 click 被 SVG 截获 ③封面文件在日期目录根，无 `covers/` 子目录。
**解决**：① locator 点 focus + `keyboard.type(text, {delay:5})` ② 点 `.semi-upload.upload-BvM5FF` 容器 + filechooser ③ 传路径前先 `ls` 确认。
**Why:** editor-kit 组件状态同步依赖真实键盘事件；SVG 覆盖层拦截指针；生成脚本输出目录与假设不符。
**How to apply:** Phase 14.5c（新增）/ 14.6（已补）

### 🔴 视频号 QR iframe 跨域失败连续两日复发（v3.23.0 / 2026-08-29）
**问题**：0828 + 0829 连续两日 `qrconnect` iframe「加载失败，点击重试」且重试无效——非偶发，是复发模式。
**解决**：重试 1 次即放弃 → QR 截图落盘 `channels-login-{MMDD}.png` → upload-status.md 写「视频号待办」6 步手动补跑清单（附双 body 铁律）。
**Why:** 跨域 iframe 自主流程无法修复，止损输出比反复重试有价值。
**How to apply:** Phase 13.0b（已升级为复发协议）

### 🔴 抖音「画面」+「引导至风险不可控渠道」叠标须重渲（v3.27.0 / 2026-09-01）
**问题**：0901 原片内部 review-checklist PASS 后用户手动发布，09:21:28 被机审「减少作品推荐」；原因「引导至风险不可控渠道」；标签 **「画面」**。根因不是标题：S2 口播「想试的去 Hugging Face」+ 仓库站 UI 入帧；S5 口播「清 Cookie / 跑杀毒扫描」+ 断链/信用卡扔垃圾桶画面；描述含「窃密木马」。
**解决**：标签含「画面」→ **禁止**只改标题/封面后重传旧 mp4。写 `voiceover-texts-safe.json` + `image-prompts-safe.json`，至少重画高风险 scene（本期 S2/S5），改口播去引导动词，TTS → captions → Remotion → `*-safe.mp4` + `platform-copy-safe.md`。账号安全视觉改为平静设备列表+盾标；开源视觉改为抽象管线图，禁第三方网站壳。
**Why:** 内部 3W/灰渠道 PASS 扫的是脚本结构，抖音机审扫的是成片帧 + 引导动词（v3.14 坑 130 复发）。「跑杀毒」会被读成引导下载第三方软件。
**How to apply:** Phase 2 审核清单增加上表三项；命中后走 `templates/platform-compliance.md` §6.1 过审重渲协议。Phase 14.0-pre 仍有效：未获用户确认前不自动重开创作者中心。

### 🔴 抖音用户手动上传后禁止再自动传（v3.26.0 / 2026-09-01）
**问题**：用户已手动把当期视频传到抖音后，流水线仍按 Phase 14 打开创作者中心、点上传/暂存，会撞上未发布草稿弹窗、混入旧素材或重复稿。
**解决**：用户说「已手动 / 不要再自动传」→ 立即停 Phase 14，标记 `douyin: user-manual`，不重开上传页、不核验除非用户要求。
**Why:** 手动稿优先于自动稿；再跑会破坏用户已完成的草稿。
**How to apply:** Phase 14.0-pre（新增）

### 🔴 视频号 login.html QR 已加载仍须止损（v3.26.0 / 2026-09-01）
**问题**：0901 打开 `/platform/post/create` 被 302 到 `login.html`，QR **已加载**（`qrcode loaded`，截图可见扫码框），不是「加载失败，点击重试」。console 同时刷 `300334`、`fastLogin: false`、`localhost.weixin.qq.com:14xxx/api/check-login ERR_CONNECTION_REFUSED`。误判成「QR 好了再等一会 / 再 reload」会空转。
**解决**：与 v3.23.0 复发协议同一止损——重试 1 次仍 `login.html` → `channels: login_required`。上述 console 噪声是微信桌面 fast-login 探测失败，**不是**继续重试的理由。
**Why:** 无桌面客户端时 fast-login 必然失败；QR 可见仍需真人扫码，自主流程做不到。
**How to apply:** Phase 13.0b（v3.26.0 变体）

### 🔴 公众号 appmsgid 已落后禁止因空壳 snapshot 重建（v3.26.0 / 2026-09-01）
**问题**：草稿已保存（URL 含 `appmsgid=100000882`）后，再 snapshot 可能读到标题 `0/64`、正文「从这里开始写正文」、封面「拖拽或选择封面」空壳，看起来像没写过。
**解决**：以 `appmsgid=` 为唯一成功信号；空壳 UI **禁止**再点新建 / 再跑全文注入。
**Why:** 编辑器 SPA 切 tab 或无障碍树读到空代理，不等于草稿丢失；重建会重复稿。
**How to apply:** Phase 12 保存关键经验第 9 条

### 🔴 视频号 login.html snapshot YAML 为空（v3.26.0 / 2026-09-01）
**问题**：`login.html` 上 `browser_snapshot` 落盘 YAML 可能是 0 字节，无法用 a11y 树判断 QR 是否在。
**解决**：改 `browser_take_screenshot`（如 `channels-login-YYYY-MM-DD.png`）判定；空 snapshot 不构成再 reload 的理由。
**Why:** 登录页跨域 iframe / 无障碍树残缺，截图比 snapshot 可靠。
**How to apply:** Phase 13.0b 截图落盘步骤

## 更新日志

### v3.27.0（2026-09-01）
基于 **2026-09-01 抖音机审**（原片 09:21:28 发布 → 减少作品推荐 / 引导至风险不可控渠道 / 标签「画面」）实测，吸收坑 173：

**平台机审**
- 内部 `review-checklist` PASS ≠ 抖音过审
- 「画面」+「渠道」可叠标：口播引导动词（去 Hugging Face / 清 Cookie / 跑杀毒）与事故视觉（断链、丢卡、仓库站 UI）一起打
- **只改标题/封面后重传旧片无效**；必须 `voiceover-texts-safe.json` + 重画高风险 scene + TTS + captions + `*-safe.mp4`

**0901 产物**
- 成片 `【2026-09-01】…｜今日羊报AI-safe.mp4`（142.592s / 12.7MB）
- S2 抽象多模态管线；S5 平静账号安全页；描述去「窃密木马」
- 锚点 94.896/142.416 = 0.666（偏离 3.4pp <5%，不重排）

**版本**：3.26.0 → 3.27.0

### v3.26.0（2026-09-01）
基于 **2026-09-01 日报全流程**（B站草稿 ✅ / 公众号 `appmsgid=100000882` ✅ / 抖音用户手动 ⏭ / 视频号 `login.html` QR 已加载仍 `login_required` ⏭）实测，吸收坑 169–172：

**抖音（Phase 14）**
- 新增 14.0-pre：用户说已手动上传 / 不要再自动传 → 立即停 Phase 14，标记 `douyin: user-manual`，不重开创作者页

**视频号（Phase 13.0b）**
- 补「QR 已加载仍需扫码」变体：`login.html` + `qrcode loaded` 与「加载失败，点击重试」走同一止损（重试 1 次）
- `300334` / `fastLogin: false` / `localhost.weixin.qq.com:14xxx/api/check-login ERR_CONNECTION_REFUSED` 是桌面 fast-login 噪声，不是继续重试的理由
- `login.html` 上 snapshot YAML 可能为空 → 用截图判定

**公众号（Phase 12）**
- `appmsgid=` 一旦出现即禁止因后续空壳 snapshot（标题 `0/64` / 空正文）重建草稿

**已知坑**：169–172 入「已知坑与经验教训」

**版本**：3.25.0 → 3.26.0

### v3.25.0（2026-08-31）
基于 **2026-08 月报字幕实测**（语义切行后 48 条、min_dur≈1.30s、禁切反例整行保留），把切行从「所有标点一视同仁 + 16 字硬墙」换成语义 `group_caps`：

**切行（Phase 7 当前默认）**
- `SENT_END`（`。！？；`）强制断；`SOFT_PUNCT`（`，、：`）仅 ≥`max_len=16` 才断
- 允许略超 16 至 `hard_max=20` 保住专名/动宾/正反并列；超 hard_max 黄金分割 40–60%（扩 30–70%）→ `WEAK_BEFORE` → **整句保留**
- **禁止按字符下标硬切**（会切开 `终止Cursor官方直连` / `硬新闻主轴`）
- 后处理：`GLUE_TAILS` + `BAD_ENDS`/`BAD_STARTS` + 当期 `jieba.add_word`
- 对齐后 `merge_short_dwell(min_sec=1.0)`，治 `延期；` 0.5s 闪行
- Remotion 字幕 **单行**，不做双行长度平衡

**禁切反例（切开即错）**
- `稳不稳` / `硬新闻主轴` / `规划步骤` / `编程 Agent` / `终止Cursor官方直连` / `Hy四连发` / `羊报AI月报` / `整月风向` / `主题近一万` / `延期；`

**时间轴（不回退）**
- 内容 100% 来自脚本，时间 100% 来自音频；whisper 只负责时间轴
- 禁止按字数比例切时间轴（v2.1/v2.2 已废弃）；无 whisper 词时才允许比例兜底
- `WhisperModel` 必须在 `--dry-run` 提前 return 之后才 import

**落盘**
- 规则全文：`templates/captions.md`
- 可运行脚本：`templates/gen_captions.py`（`--report-dir` / `--dry-run` / `--extra-word`）
- 复制到当期 `scripts/gen_captions.py`，先 dry-run 扫禁切，再全量 whisper
- 旧 `gen_captions_v2.py` / `split_sentences` **已废弃作切行器**

**版本**：3.24.0 → 3.25.0

### v3.24.0（2026-08-30）
基于 **2026-08-30 W35 周报全流程**（B站/抖音/公众号 3 平台草稿 ✅ + 视频号当日补跑草稿箱(4) ✅）实战，吸收坑 161–167，把映射表/标题规则/Phase 12 作者标题/Phase 13 wujie 协议写成单一事实源：

**映射表 + 标题（单一事实源）**
- 视频号标题改为 `今日羊报AI M月D日` / `羊报AI周刊 M月D日至D日` / `羊报AI月报 YYYY年M月`（≤16 字，禁 `.` `~`；超限保存按钮 silent disabled）
- 公众号作者字段与署名拆开：作者固定 `今日羊报AI` / `羊报AI周刊` / `羊报AI月报`（≤8 字）；署名格式仅用于正文/简介

**公众号（Phase 12）**
- 作者 ≤8 字；隐藏 `#title`（h=0）不可 click，走 `.ProseMirror`.first() + keyboard.type，回读 `#title.value`
- 两个 `.ProseMirror`：first()=标题代理、nth(1)=正文；标题填写永远放到正文注入之后（12.5b）

**视频号（Phase 13）——wujie shadow 全套**
- 全部表单在 `wujie-app` open shadow；页面级 locator / 普通 evaluate / `page.frame({name:'content'})` 失效
- 视频/封面 `setInputFiles` 穿 shadow；描述 `.input-editor`；短标题 Vue 受控 input（原生 setter + keyboard.type）
- 封面弹窗「编辑个人主页卡片」未关会吞保存；保存成功无跳转、无 toast → 必须 `/platform/post/draftListManager` 数条目（`post/record?tab=draft` 会 302）
- 旧 iframe / `.edit-shorttitle-content` / 描述坐标法全部降为 `hasWujie=false` 兜底

**抖音 + TTS**
- 草稿验收 URL 改为 `https://creator.douyin.com/creator-micro/content/publish/record?tab=draft`（`content/manage` 只显示已发布）
- 换期硬性前置 `rm public/voiceover/scene*.wav`，否则 atempo SKIP 启发式被上期残留 wav 骗过 → 成片 0:52 音画/字幕错位

**已知坑**：161–167 入「已知坑与经验教训」；v1.5.0 / v1.7.0 总结与坐标法记载已降级，避免与 13.1 矛盾

**版本**：3.23.3 记载 → 3.24.0（skill 版本号；不另发 3.23.4）

### v3.23.0（2026-08-29）
基于 **2026-08-29 日报视频全流程**（319 帖 → 视频 → B站/抖音/公众号 3 平台草稿 + 视频号 QR 连续两日复发按复发协议跳过）实战，**修正 2 处既有记载与实测相矛盾**，固化 6 组新坑：

**公众号（Phase 12）——核心矛盾修正**
- 🔴 12.5 重写：ProseMirror 正文**禁止直接 innerHTML 赋值**（实测被静默清空 pmLen=1）→ 唯一可靠方式 `selectNodeContents` + `execCommand('insertHTML')`，注入后回读字数验证
- 🔴 12.5b 新增：正文注入操作会把标题框灌入全文（计数器 1776/64）→ data-placeholder 定位 + delete + insertText 重置；标题填写固定放到正文注入之后
- 🔴 12.8 修正：「我已阅读并同意」协议 checkbox **不会**自动勾选（实测 checked:false，直接点确定 no-op）→ 点 `closest('label')` 容器验证 checked 后再确定
- 12.7c 新增：封面 4 子坑——hover 菜单 mouse.move、webuploader-pick label 拦截（force click + filechooser，勿用含点动态 id）、`.selected` 类回读验证、2.35:1 裁剪 radio 视口外 evaluate 点 label

**抖音（Phase 14）**
- 14.5c 新增：描述编辑器实为 `.editor-kit-editor-container [contenteditable="true"]`，用 `keyboard.type({delay:5})` 逐字输入
- 14.6 补录：封面上传图标被 SVG 拦截 → 点 `.semi-upload.upload-BvM5FF` 容器；封面文件落日期目录根（无 covers/ 子目录），传路径前先 ls

**视频号（Phase 13）**
- 13.0b 升级为复发协议：QR iframe 跨域失败 0828+0829 **连续两日复发**（非偶发）→ 重试 1 次即放弃，QR 截图落盘 + upload-status.md 写 6 步手动补跑清单

**已知坑新增**：上述 6 条入「已知坑与经验教训」

**实测**
- 公众号 appmsgid=100000820 ✅（正文 1536 字 execCommand 注入 + 原创「文字原创·已开启快捷转载」+ 2.35:1 封面 + 合集「今日羊报 AI」）
- B站 draftId=3809839 ✅；抖音双封面 + 7 话题 ✅；视频号 login_required ⏭（复发协议）
- **版本**：3.22.0 → 3.23.0

### v3.22.0（2026-08-28）
基于 **2026-08-28 日报视频全流程**（511 帖 → 视频 150.29s → B站/抖音/公众号 3 平台草稿 + 视频号 login_required 按既有协议跳过）实战，固化上传阶段 6 个新坑：

**抖音（Phase 14）**
- 14.0 草稿恢复弹窗：点合并文本「继续编辑放弃」落草稿编辑页 → JS evaluate 精确点「放弃」
- 14.5b 新增：描述/话题分离输入——描述填 contenteditable[0]，话题用「#添加话题」+ keyboard.type；勿用 nth(1)（页面仅 1 个 contenteditable）
- 14.6 横封面选择被 publish-mention-wrapper（@好友浮层）拦截 → Escape + JS 攀爬「设置封面」header 到容器点「选择封面」
- 14.7 合集名大小写陷阱：实测「「今日羊报Al」」小写 L ≠ 大写 I → 探测可见文本前缀匹配，勿硬编码

**公众号（Phase 12）**
- 12.8 原创声明 y 范围失效（实测 y=471，旧 y<400 漏选）→ 去 y 上界，优先 .setting-group__title 文本匹配
- 12.10 合集输入框 getByRole 超时 → 先 scrollIntoView「未添加」开弹窗，再 input[placeholder] 兜底

**版本一致性修复**：frontmatter version 3.20.0 → 3.22.0（原与 H1 v3.21.0 不一致）

**已知坑新增**：上述 6 条入「已知坑与经验教训」

**实测**
- 视频：news-pipeline/2026-08-28/video/【2026-08-28】GLM新模型测评分化与英伟达收购HuggingFace｜5条重磅AI新闻一次看完 | 今日羊报AI.mp4（150.29s / 8 场景）
- 锚点：killing_line_chart（tier3 首次使用，位置 67.45% 容差内通过）
- B站 draftId=3805516 ✅；抖音 暂存离开 ✅；公众号 appmsgid=100000813 ✅；视频号 login_required ⏭（按 v3.18.0 13.0b 协议）
- **版本**：3.21.0 → 3.22.0

### v3.19.0（2026-08-21）
基于 **2026-08-21 日报视频全流程**（GEN_IMG 端点大面积 401 + 封面 API 余额耗尽 → 本地 Pillow 兜底）实战：

**Phase 5.6 本地生图兜底（核心，与 edge-tts 兜底 mimo-tts 同构）**
- 新增 Phase 5.6：当 GEN_IMG 多端点全挂 / 封面 API 余额耗尽 / gpt-image-2 中文文字糊掉时，用 Pillow 本地生成 scene 图和封面
- Scene 图本地化（`gen_images_local.py`）：API 全挂或旧图与本期脚本不匹配时触发；画 8 张主题化抽象背景（1920×1080，深色演播室 + 场景配色 + 几何 motif）
- 封面本地化（`gen_covers_local.py`）：API 余额耗尽或文字糊掉时触发；拿 `scene1.png` 作底图 + 渐变蒙版 + 本地字体叠加日期/品牌，保证文字 100% 清晰
- 决策流程：API 优先，全挂才切本地；API 恢复后切回 API（本地仅兜底非默认）
- 日期/品牌名变量按模式参数映射表读取，禁止硬编码；改日期只改 `DATE` 一处

**已知坑新增**
- 🔴 GEN_IMG 全挂 / 封面文字糊掉 → 本地 Pillow 兜底（`gen_images_local.py` / `gen_covers_local.py`）

**实测数据**
- 0821：scene 图走 API 成功（prism+luka77 全 401，xmiaom http=200 出 8/8）；封面 API 余额耗尽 → `gen_covers_local.py` 本地 Pillow 生成 horizontal-4-3.png + vertical-3-4.png
- 后续改封面日期（2026-08-21 → 2026-08-22）：只需改 `gen_covers_local.py` 的 `DATE` 变量重跑，无需重调 API

**版本**：3.18.0 → 3.19.0

### v3.18.0（2026-08-18）
基于 **2026-08-18 日报视频全流程**（抖音草稿恢复 + Semi Design 拦截 + 视频号 QR 跨域 + edge-tts atempo 加速）实战：

**Phase 14（抖音）新增**
- 14.0 草稿恢复弹窗处理：不点合并文本「继续编辑放弃」，走「重新上传」回 upload 页；离开草稿页弹 beforeunload「将此次编辑保留？」→ `browser_handle_dialog(accept=true)`，否则 `net::ERR_ABORTED`
- 14.8b Semi Design 组件拦截修复：`label.semi-radio` 拦截自主声明 radio → 直接点 label；`semi-modal-wrap` 拦截「暂存离开」→ `Escape` + force click；file chooser 停在 "Modal state" → 用 `browser_file_upload(paths=[...])` 处理
- 14.10b 暂存离开 + 草稿落库验收：`Escape` 关残留 modal → force click「暂存离开」→ beforeunload accept → 验收三信号

**Phase 13（视频号）新增**
- 13.0b 自主登录失败协议：QR iframe 跨域（`open.weixin.qq.com`）无法 JS 访问，「加载失败点击重试」+ reload 1–2 次仍失败 → 标记 `channels: login_required`，写 `upload-status.md` 为 `⏭`，停止空转，等待用户手动扫码

**Phase 6（edge-tts）新增**
- 6.3b atempo=1.4 加速：音色 `zh-CN-YunxiNeural` + ffmpeg `atempo=1.4`，8 场景总时长 112.13s；加速后必须重算 Composition.tsx sceneConfig / Root.tsx TOTAL_DURATION_SEC / captions.json → 重渲染

**已知坑新增**
- 🔴 抖音 Semi Design 组件拦截（`semi-radio` label / `semi-modal-wrap`）
- 🔴 视频号 QR 跨域 iframe 无法自主扫码
- 🔴 抖音草稿恢复弹窗「继续编辑放弃」文本合并

**版本**：3.17.0 → 3.18.0

### v3.17.0（2026-08-13）
基于 **2026-08-13 日报视频全流程**（DeepSeek V4 Pro / Grok 4.6 同期上线 → 多平台草稿）实战：

**B站标题规则（核心）**
- 标题改为「日期在前、报刊名在后」：`【YYYY-MM-DD】{核心标题}｜{N}条重磅AI新闻一次看完 | 今日羊报AI`
- 同步更新模式映射表 / publish.json 模板 / 渲染文件名 / 归档路径（周报、月报同规则）
- 渲染文件名改为 `【{YYYY-MM-DD}】{核心标题}… | 今日羊报AI.mp4`

**封面精简**
- 封面由 5 张精简为 **2 张**：`horizontal-4-3.png`（1536x1152，4:3，B站/通用/横版）+ `vertical-3-4.png`（1152x1536，3:4，抖音/竖版）
- 全量替换旧封面名（wechat-21-9 / douyin-horizontal-4-3 / cover.png / weekly-cover.png）

**B站分区自动选择**
- 新增 Phase 11.4：上传 B 站时自动选择分区「**人工智能**」（Translate.creator 自定义下拉需 JS evaluate 点击）

**数据来源去展示化**
- 视频脚本默认模板不出现「数据来自 linux.do 社区精选」等来源字样，正文/CTA 不展示平台来源

**版本**：3.16.0 → 3.17.0

### v3.16.0（2026-08-08）
基于 **2026-08-08 抖音/视频号标题规则优化** 实战：
- 抖音/视频号标题改为纯报刊名 + 日期，≤30/≤16 字
- 版本号由 3.15.0 → 3.16.0（本轮 git 历史已记录，见 commit c00286b）

### v3.15.0（2026-07-31）
基于 **2026-07-31 日报视频全流程**（daily 428 → 抖音「引导至风险不可控渠道」违规 → 修改脚本 + edge-tts 重渲 → 公众号封面）实战：

**TTS 故障转移（核心）**
- Phase 6 新增 6.3 兜底方案：mimo-tts 全部端点不可用时 → 切换到 edge-tts（Microsoft Azure Neural TTS）
- edge-tts 无需 API Key，`pip install edge-tts` 即可使用
- 推荐音色 `zh-CN-YunyangNeural`（男声，专业可靠，新闻风）
- 切换条件：`Gateway Error: 没有可用的内网节点` / 连续 3 次 503/502 / 所有 fallback 端点失败
- 输出 MP3 后须 ffmpeg 转为 WAV（24kHz PCM16LE）与字幕流程兼容

**抖音违规审核**
- 新增 `🔴 抖音违规审核与处理` 章节（Phase 14 后）：常见违规原因表（引导至风险不可控渠道/画面/双封面缺失/违规推广）
- 新增违规处理流程：定位违规源 → 修改方案 → 重传流程
- 新增违规文案修改示例表（"申请试用"→"正在落地"、"去XX体验"→"门槛降低"）
- 审核清单新增项：抖音描述检查引导性动词

**实测数据**
- 违规原因：`引导至风险不可控渠道`（Scene 5「去 Flow Music 体验」+ Scene 6「申请试用」）
- 修改：voiceover-texts.json 去掉引导性表述 → edge-tts 重生成 scene5/6 → 重算 captions → 重渲染 → 文案修改后重传
- 视频约 140.14s / 9 场景 / 16.2MB
- 公众号：appmsgid=100000542 草稿已保存，封面上传至正文库

**版本**：3.14.0 → 3.15.0
基于 **2026-W29 周报全流程**（聚合 → 视频 → 抖音/视频号连拒 → 过审重渲 → 公众号文案同步）实战：

**平台机审（核心）**
- 抖音：`不适宜公开` / `限制自己可见` + 标签 **「画面」**
- 视频号：`限制传播`（描述含逃逸/立法时）
- **只改标题+封面不够**；画面违规必须 **重画场景 + 改口播 + 重渲**
- B 档扩展：攻击动词（逃逸/入侵/窃取）与立法词作标题主卖点
- `platform-compliance.md` §3.4 抖音专项、§6.1 过审重渲协议、§8 标题禁词表

**产物约定**
- `voiceover-texts-safe.json` / `image-prompts-safe.json` / `*-safe.mp4` / `platform-copy-safe.md`
- 内部 review-checklist 与平台禁词 **双轨扫描**

**其它**
- 公众号草稿可「只补封面」；preview 失败须如实汇报
- Phase 3 增加画面合规表；Phase 2 How to apply 覆盖画面维度

**版本**：3.13.0 → 3.14.0

### v3.13.0（2026-07-26）
基于 **2026-07-26 日报视频发布后处置**（视频号限制传播 + 公众号接投诉删除）实战：

**合规文档**
- 新增 skill 依据：`微信视频号常见的不合规频道内容概述.md`、`微信公众号互联网用户公众账号信息服务管理规定.md`
- 新增模板：`templates/platform-compliance.md`（选题 A/B 档、封面铁律、两平台专项、落盘清单）
- Phase 2「平台合规审查」升级：强制引用上述文件与模板；审核清单扩展

**内容与封面**
- 封面 prompt **禁止写实 news anchor / 真人主播**；改无人演播室 + 产品/抽象视觉
- 公众号默认不上融资/政策/外泄/监管对抗类；标题禁「同日升温/切断/外泄」等

**已知坑**
- 视频号无细码限流、公众号无条款号删文的归因与整改路径

**版本**：3.12.0 → 3.13.0

### v3.12.0（2026-07-25）
基于 **2026-07-25 日报视频**（daily **455** → 成片 ≈**149.8s** → 多平台草稿）实战：

**TTS**
- 禁止工具参数硬编码 `sk-`；`gen_tts.py` 从 env / 历史 gen-tts.sh 读 key；7 scene 全成功

**成片**
- 字幕：加权字符 + silencedetect；Composition/Root 时长与 ffprobe 对齐
- 视频：`news-pipeline/2026-07-25/video/【今日羊报AI】OpenAI沙箱越狱进立法，DeepSeek新思维链现身 | 2026-07-25.mp4`（≈149.8s / 14.4MB）

**B站**
- 存草稿 `group=draft`；**草稿页补封面**（封面制作弹窗 + image accept setInputFiles + 完成）→ `archive.biliimg.com` 预览 + 再存草稿

**抖音**
- filechooser 拆步；暂存后「继续编辑」验收 ✅

**公众号**
- `appmsgid=100000512` ✅（封面可手补）

**视频号**
- 独立脚本前必须释放 MCP profile；`login.html` → login_required ⏭

**版本**：3.11.0 → 3.12.0

### v3.11.0（2026-07-22）
基于 **2026-07-22 日报视频**（daily 440 → 成片 ≈140.7s → 多平台草稿）实战：

**图片续跑**
- GEN_IMG 整批 10min 超时后：**盘点已有 scene/cover，只补缺失**（0722：scene1–7 + cover 已齐，再补 4 平台封面）

**抖音上传**
- filechooser 模态打断长脚本 → **封面上传拆短步骤** + `browser_file_upload`
- 草稿验收：`继续编辑` 弹窗 + 描述含当日关键词（0722 描述已落库）

**公众号**
- `.new-creation__menu-item` 点「文章」新开标签；`appmsgid=100000497` 草稿成功
- 封面仍可手补（不阻塞）

**视频号**
- `login.html` + 二维码「加载失败」→ `login_required` ⏭，不空转

**实测**
- 视频：`news-pipeline/2026-07-22/video/【今日羊报AI】OpenAI沙箱长程模型停用，Gemini3.6Flash全量上线 | 2026-07-22.mp4`（≈140.7s / 7 场景）
- 锚点：`multimodal`
- B站 `group=draft` ✅；抖音继续编辑 ✅；公众号 `appmsgid=100000497` ✅；视频号 login_required ⏭
- **版本**：3.10.0 → 3.11.0

### v3.21.0（2026-08-27）
基于 **B站 190 条作品数据分析 + 5 个真实脚本审计**（`social_media/流水线增量补丁方案_基于真实脚本_2026-08-26.md`）的**数据驱动增量补丁**，非 greenfield 重写。流水线已做对 8 件事（3W 四段/P2 锚点/1-3min 体裁/灰渠道配额/去重/锚点 70-80%/无过渡词/审核清单），本版只补 4 个真实差距。

**核心数据**：5s 完播 31.4%（→目标 40%+，提到 40%+ 均播可翻倍）、完播 4.35%（中段尿点）、2s 跳出 44%、周报均播 47/5s 25.3%（全站最差）。

**补丁清单（17 条，精确到文件）**：
- `templates/script-template.md`（补丁1-5）：Hook 槽加 4 主力公式+15-25 字自检、新增「对应封面大字」字段、选材排序表槽、锚点位置硬约束 70-80%、Now What 质量红线禁纯观察
- **新建 `templates/script-template-weekly.md`**（§3.2）：周报从「5-6 条堆叠各 3W 浅聊」改「1 件大事 3W 深聊 50s + 锚点 + 2-3 条一句话快讯 + CTA」，100-150s——堆叠的结构性根因是缺周报模板
- `SKILL.md`（补丁6-11）：Hook 槽同步 4 公式约束、周报结构指令改深聊型（line 165/175/123/213）、Step 1.4 选材排序升强制、周报 Hook 禁套话、Phase 1 周报 TOP1 选取步骤、Phase 10.5 周报砍掉决策（<80 停/连续2期<80 砍）
- `SKILL.md` 审核清单（补丁12-16）：加 5 项必勾——Hook 4 项、锚点位置 70-80%、Now What 非纯观察、选材排序表、周报结构
- `templates/professional-anchor.md`（补丁17）：锚点位置与 70-80% 联动
- Phase 2 新增 A/B 双 Hook 输出 + `hook-ab-log.md`（解"无公式轮换对照"）
- Phase 7 字幕补丁：Hook 5s 文本独立成段、`Subtitles.tsx` 前 5s 字号 +20%（治 2s 跳出 44%）

**4 主力钩子公式**（源 `social_media/爆款开头钩子.md`，按热度）：社交共鸣型 / 反转认知型 / 否定警告型 / 数据背书型；禁总结型堆≥2事件，禁套话后缀。

**边界声明**：P0 账号限流（89 条自见 0 播放，根因账号同质化降权非标题敏感词）无理论可解，不进流水线，靠 Week 1 停更冷却 + 换赛道。无投币字段→不说三连率；无弹幕字段→弹幕结论禁止。

**版本**：3.20.0 → 3.21.0

### v3.20.0（2026-08-23）
- whisper 强制对齐字幕 + 公众号图库封面 DOM（i 元素 backgroundImage）

### v3.10.0（2026-07-21）

基于 **2026-07-21 日报视频**（daily 447 → 成片 ≈143s → 多平台草稿）实战：

**图片生成稳定性（核心）**
- GEN_IMG 多端点 `URL/KEY` + `_001/_002` fallback；禁止日志打印 key
- 按 scene 跳过已生成文件；避免整批 10 分钟 Bash 超时（exit 143）
- CTA 图可临时兜底；竖封面必须当期 `vertical-3-4.png`

**概念锚点 / usage-log**
- `concepts.json` 根 dict + `concepts[]`；usage-log 兼容 list / `{entries}`
- 免确认仍写 `review-checklist.md` + usage-log

**上传验收**
- B站：`group=draft` ✅（0721）
- 抖音：暂存后「继续编辑」+ 无竖/双封面缺失 ✅
- 公众号：`appmsgid=100000492` ✅（封面可手补）
- 视频号：`login.html` → login_required ⏭（不空转）

**实测**
- 视频：`news-pipeline/2026-07-21/video/【今日羊报AI】Kimi停售与开源争议，国模密集冲榜 | 2026-07-21.mp4`（≈143.1s / 7 场景）
- 锚点：`rate_limit`
- **版本**：3.9.0 → 3.10.0

### v3.9.0（2026-07-20）
基于 **2026-07-20 日报视频**（`data/reports/2026-07-20.md` → 成片 → 多平台草稿）实战：

**抖音草稿闭环（核心）**
- 「暂存离开」后必须验收：继续编辑 / 内容管理可见 / draft 表单非空
- 验收失败 → 视频+元数据+双封面整段重传，不可只报「已点暂存」
- 竖封面只使用当期 `vertical-3-4.png`（用户可点名文件）

**视频号登录判定**
- 用户口头「已登录」无效；以 MCP `login.html` 为准
- QR 加载失败有限次重试后跳过；禁止空转刷码与堆指南 md

**其它**
- TTS `gateway_error`/503：退避 + fallback + wav 校验
- 免确认：内部审核清单仍须执行并落盘
- 实测：B站 `group=draft` ✅；公众号 `appmsgid=100000487` ✅；抖音重传后草稿可恢复 ✅；视频号 login_required ⏭
- 视频：`news-pipeline/2026-07-20/video/【今日羊报AI】Fable永久留Max，通义3.8预览上线 | 2026-07-20.mp4`（≈172.8s）
- **版本**：3.8.0 → 3.9.0

### v3.8.0（2026-07-19）
基于 **2026-W28 全量周报视频流水线**（`data/weekly/2026-W28.pdf` 落盘后 → 视频 → 多平台草稿）实战：

**公众号封面闭环（核心）**
- 裁剪弹窗标题「编辑封面」；主按钮 **「确认」**（避开 disabled「确定」）
- 裁剪中禁止 Escape；点确认后 **轮询 preview `display:block` + mmbiz 背景**
- 从正文选择：hover + 强制显示 `.js_selectCoverFromContent`；缩略图优先 mmbiz 背景 item
- 直达草稿：`appmsgid=` 编辑 URL；封面图（`horizontal-4-3.png` / `vertical-3-4.png`）必须先入正文

**上传与联跑**
- B站：中文文件名 → 简单路径；成功看 `group=draft`
- 视频号：未登录（login.html）不阻塞其他平台
- 用户说「事件按推荐自动选定 / 不用确认」时，Phase 1/2 **跳过人工确认**（仍写 usage-log）
- GEN_IMG / MIMO_TTS 从 settings.env 读取 + fallback；禁止日志打印 key

**实测数据**
- 周报视频约 155.8s / 8 场景；公众号草稿 `appmsgid=100000479` 封面 `mmbiz_jpg` 验收通过
- **版本**：3.7.0 → 3.8.0

### v3.7.0（2026-07-18）
- **浏览器 Profile 铁律**：MCP 与独立 Playwright 互斥；scoped pkill；解释「退出」原因
- **视频号双 body**：单次 run_code 闭环、返回前离开 channels 页、避免 snapshot/file_upload 拆分
- **视频号封面**：等预览生成；CDP `backendNodeId` 写 image input；草稿箱条数/标题验收
- **公众号封面**：正文图 → 从正文选择 → 非 img 缩略图 class → 下一步 → **确认**；preview 背景 URL 验收
- **抖音竖封面**：强制日期+品牌，禁止 scene 无日期回退
- **版本**：3.6.0 → 3.7.0

### v3.6.0（2026-07-17）
- **抖音封面完成按钮（Phase 14.6）**：`getByRole('button','完成')` 常 count=0 → 改用 `locator('text=完成').last()` + evaluate 点底部主按钮；`setFiles` 后等 1.5–3s 再完成
- **验收三件套**：`竖封面缺失=false` + `双封面缺失=false` + 无「设置竖封面」弹窗 → 再「暂存离开」
- **只补竖封面路径**：横封面已在草稿时跳过视频/横封面，直接 `enter_from=draft` 补竖封面
- **禁止误关弹窗**：未保存时勿对「封面未保存」点确定（会丢图）
- **组件表升级**：抖音上传总结 v1.8.0 → v3.6.0（完成按钮、fill 标题、暂存离开）
- **版本**：3.5.0 → 3.6.0

### v3.5.0（2026-07-15）
- **抖音封面（Phase 14.6，2026-07-16 实测）**：草稿编辑页「设置竖封面」弹窗常不出现 → 用「竖封面3:4」标签 getBoundingClientRect 点标签上方封面框；语义点「选择封面」优先于硬编码坐标；文件名强制 horizontal-4-3.png（横）/ vertical-3-4.png（竖）；验收无「竖封面缺失」再暂存
- **公众号封面（Phase 12.7，2026-07-16 实测）**：file chooser 不弹时用 setInputFiles 兜底；封面失败不阻塞「保存为草稿」；成功以 URL appmsgid= 为准；保留「从正文选择」+ .js_selectCoverFromContent + 上传中弹窗 Escape
- **字幕算法根治**：Phase 7 默认方案从 v2.1.0 纯字符比例升级为 v2.2.0 混合算法（加权字符估算 + silencedetect 真实停顿点吸附）
- **加权字符**：中文 1.0 / 数字 0.6 / 英文 0.35，避免版本号密集句（`GPT-5.6`、`85.5GiB`）被高估时长
- **停顿吸附**：用 ffmpeg silencedetect 提取音频真实停顿点，句子边界吸附上去，消除长视频后半段累积漂移
- **已知坑**：字幕不同步条目更新为 v2.0.0 → v2.1.0 → v2.2.0 演进，附 Why/How to apply
- **版本**：3.4.0 → 3.5.0

### v3.4.0（2026-07-12）
- **专业锚点**：Step 1.6 + `professional-anchor.md`；eligible = ready + narrator + reviewed；usage-log 写回
- **3W 默认**：全模式 What/So What/Now What + 可信度五档；精简仅更短更少条
- **可信度/语气**：新增 `templates/credibility-and-tone.md`（五档、情绪黑名单、灰渠道措辞、标题示例）
- **Phase 1**：灰渠道配额 ≤1；传闻 3 日跟踪；消费上游 `可信度`/`技术锚点`
- **脚本模板**：script-template / monthly 去炸锅示例，默认 3W + 锚点 scene
- **审核清单**：3W、可信度、灰渠道、锚点 eligible、黑名单
- **版本**：3.3.0 → 3.4.0


### v3.3.0（2026-07-05）
- **公众号上传修复**：新增弹窗阻挡「保存为草稿」的处理方案（等待上传完成+Escape关闭弹窗+验证已保存）
- **公众号合集选择**：新增 try-catch 超时保护，失败时自动跳过不阻塞
- **B站封面上传**：更新 file input 查找方案（按位置索引 inputs[1] 而非 accept 属性匹配）
- **精简模式审核强化**：脚本审核检查必须在展示前执行，审核结果与脚本一起展示
- **周报去重优化**：新增上周周报文件不存在时的跳过逻辑
- **精简周报验证**：v3.3.0 实测精简+周报叠加模式可用（4条事件，125s，B站+公众号均存草稿成功）
- **版本号升级**：3.2.0 → 3.3.0

### v3.2.0（2026-07-04）
- **Phase 6 TTS 优化**：新增环境变量直接调用 mimo-tts.sh 方案（v3.2.0），解决 settings.json 未配置 MIMO_TTS_API_KEY 的问题
- **B站上传新问题**：新增 502/400 错误处理（服务器端问题，需手动上传）和文件路径中文字符问题（需复制到简单路径）
- **公众号上传验证**：v3.2.0 实测确认完整流程可用（标题/作者/正文/原创声明/合集选择/保存草稿）
- **已知坑补充**：MIMO_TTS_API_KEY 未配置问题更新为 v3.2.0，新增环境变量首选方案
- **版本号升级**：3.1.0 → 3.2.0

### v3.1.0（2026-06-30）
- **新增月报模式**：兼容 linuxdo-daily v13 月报产物，直接消费 `data/monthly/{YYYY-MM}.md`，不重新聚合
- 新增「模式参数映射表」统一管理 daily/weekly/monthly 三模式字段（单一事实源）
- Phase 0 新增 `REPORT_MODE` 自动判定 + 月报前置检查（文件存在性 + 合集预创建提醒）
- Phase 1 新增 Step 1.5 月报选材流程：4 趋势骨架 + 每趋势 1-2 代表主题 + 套利帖二次过滤；月报跳过跨日去重，改为对比上期月报
- Phase 2 新增月报脚本模板（Hook + 4 趋势段 + 月度总结 + 下月展望 + CTA，180-240s/≤300s，每段≤100字），引用 `templates/script-template-monthly.md`
- Phase 5.5 封面 prompt 模式化（月报品牌名"羊报AI月报" + 日期 `{YYYY-MM}` + 副标题"AI 月度盘点"），引用 `templates/image-prompt-monthly.md`
- Phase 9 渲染文件名模式化（月报 `【羊报AI月报】{核心标题} | YYYY-MM.mp4`）
- Phase 10 新增月报变体：publish.json（tags 含 AI月报/AI月度盘点）、标题规则（月报 B站/抖音/视频号/公众号）、公众号图文（按趋势分节 + 月度总结 + 下月展望）
- Phase 11 B站合集 / Phase 12 公众号合集 / 抖音合集模式化（月报用「羊报AI月报」，需用户预先创建）
- B站简介数字中文化规则升级（v2.9.0 仅日报零星版本号 → v3.1.0 月报强制全数字中文化，含详细中文化映射表 + 安全版简介示例）
- 目录结构补 `news-pipeline/monthly/YYYY-MM/` 子树 + 月报输入路径说明
- 注意事项补月报全部约束（时长/事件数/数字中文化/合集预创建/不重新聚合/去重对比上期月报）
- 触发词新增"AI月报""羊报AI月报""monthly report""月报视频"等
- **已知风险**：合集「羊报AI月报」需用户在 B站/公众号后台预先创建；月报选材严禁把 4 趋势拆成单日事件

### v3.0.0
- 周报模式（读 7 天日报聚合）
- 精简模式、破格模式可叠加

### v2.9.0（2026-06-24）
- B站简介数字检测误判修复
- TTS API 多节点故障转移

### v2.8.0（2026-06-23）
- 所有平台存草稿
- 平台合规审查
- 视频号 AI 标识
- 标题党检查
- 图片-脚本映射铁律
