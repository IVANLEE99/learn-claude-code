---
name: linuxdo-daily
description: linux.do AI日报自动生成。多 Agent 协作：Crawler 抓取双数据源 → Topic Merger 合并主题 → Trend Analyzer 生成趋势 → Writer 输出日报 → Press Writer 生成新闻稿 → PDF Builder 生成 PDF。触发词：日报、linuxdo日报、AI日报、技术日报、抓取linuxdo
version: 2.1.0
---

# linuxdo-daily — AI 技术日报生成 Skill（多 Agent 架构）

从 linux.do 自动抓取 AI 相关帖子，通过 6 个专用 Agent 协作生成每日技术日报。

## 数据源

| 源 | URL | 说明 |
|----|-----|------|
| Source A: #人工智能 标签 | `https://linux.do/tag/444-tag/444` | 直接命中，无需过滤 |
| Source B: 前沿快讯 分类 | `https://linux.do/c/news/34` | 全部新闻，需按 tags 过滤 |

## 触发条件

当用户说以下关键词时激活：
- "日报"、"AI日报"、"技术日报"
- "linuxdo日报"、"抓取linuxdo"
- "今日AI新闻"、"AI资讯"

## 目录结构

```
data/
├── daily/{date}.json          # 每日抓取原始数据（合并后）
├── posts/{id}.json            # 单帖详情（含 scrape_history）
├── reports/{date}.md          # 生成的 Markdown 日报
├── reports/{date}_press.md    # 生成的专业新闻稿
├── reports/{date}.pdf         # 生成的 PDF 日报
├── reports/{date}.typ         # Typst 源文件
└── cookies.json               # 浏览器 cookies（需登录时用）
```

## 多 Agent 协作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    linuxdo-daily 工作流                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐                           │
│  │  Source A     │    │  Source B     │                           │
│  │  /tag/444     │    │  /c/news/34   │                           │
│  └──────┬───────┘    └──────┬───────┘                           │
│         │                   │                                    │
│         └───────┬───────────┘                                    │
│                 ▼                                                │
│  ┌──────────────────────────────┐                               │
│  │  Agent 1: Crawler            │                               │
│  │  - 打开两个数据源列表页       │                               │
│  │  - 提取帖子链接               │                               │
│  │  - 检查历史是否已抓取         │                               │
│  │  - 逐条抓取正文（随机1-3s）   │                               │
│  │  - 返回时刷新页面获取新帖     │                               │
│  │  - 每源最多50帖               │                               │
│  │  → 输出: data/posts/*.json    │                               │
│  │  → 输出: data/daily/{date}.json│                              │
│  └──────────────┬───────────────┘                               │
│                 ▼                                                │
│  ┌──────────────────────────────┐                               │
│  │  Agent 2: Topic Merger       │                               │
│  │  - 读取两源帖子数据           │                               │
│  │  - 去重（同帖多源）           │                               │
│  │  - 按主题聚类分组             │                               │
│  │  → 输出: 合并后的帖子列表     │                               │
│  └──────────────┬───────────────┘                               │
│                 ▼                                                │
│  ┌──────────────────────────────┐                               │
│  │  Agent 3: Trend Analyzer     │                               │
│  │  - 分析帖子内容和热度         │                               │
│  │  - 识别技术趋势和热点话题     │                               │
│  │  - 生成趋势总结（3-5条）      │                               │
│  │  → 输出: 今日技术趋势         │                               │
│  └──────────────┬───────────────┘                               │
│                 ▼                                                │
│  ┌──────────────────────────────┐                               │
│  │  Agent 4: Writer             │                               │
│  │  - 读取合并数据 + 趋势分析    │                               │
│  │  - 生成日报 Markdown 正文     │                               │
│  │  → 输出: data/reports/{date}.md│                              │
│  └──────────────┬───────────────┘                               │
│                 ▼                                                │
│  ┌──────────────────────────────┐                               │
│  │  Agent 5: Press Writer       │                               │
│  │  - 读取日报 + 社区帖子        │                               │
│  │  - 生成专业 AI 科技新闻稿     │                               │
│  │  → 输出: data/reports/{date}_press.md│                       │
│  └──────────────┬───────────────┘                               │
│                 ▼                                                │
│  ┌──────────────────────────────┐                               │
│  │  Agent 6: PDF Builder        │                               │
│  │  - Markdown → Typst 源码      │                               │
│  │  - Typst 编译 → PDF           │                               │
│  │  → 输出: data/reports/{date}.pdf│                             │
│  └──────────────────────────────┘                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent 1: Crawler（抓取器）

**职责**：从两个数据源抓取帖子，检查历史记录，模拟人类浏览行为。

### 1.1 打开列表页

使用 Playwright MCP `browser_navigate` 依次打开：
- Source A: `https://linux.do/tag/444-tag/444`
- Source B: `https://linux.do/c/news/34`

如果触发 Cloudflare 挑战页，通知用户进行人工验证。

### 1.2 提取帖子链接

使用 `browser_evaluate` 提取列表中的帖子：

```javascript
() => {
  const rows = document.querySelectorAll('tr.topic-list-item');
  const posts = [];
  rows.forEach((row, i) => {
    const topicId = row.getAttribute('data-topic-id');
    const titleLink = row.querySelector('.main-link a.title') || row.querySelector('a.title');
    const title = titleLink ? titleLink.textContent.trim() : '';
    const href = titleLink ? titleLink.getAttribute('href') : '';
    const views = row.querySelector('.views .number')?.textContent?.trim() || '0';
    const replies = row.querySelector('.posts .number')?.textContent?.trim() || '0';
    if (topicId) posts.push({ index: i, id: topicId, title, href, views, replies });
  });
  return posts;
}
```

### 1.3 检查历史记录

对每个帖子 ID，检查 `data/posts/{id}.json` 是否已存在：
- **已存在**：跳过，不重复抓取
- **不存在**：加入待抓取队列

### 1.4 逐条抓取正文（模拟人类浏览）

对待抓取帖子执行循环，**每源最多 50 帖**：

```
for each post in 待抓取队列（最多50帖）:
  1. browser_navigate → 打开帖子 URL
  2. browser_wait_for → 等待 random(1, 3) 秒（模拟人类阅读）
  3. browser_evaluate → 提取正文：
     () => {
       const cooked = document.querySelector('.cooked');
       const content = cooked ? cooked.innerText.trim() : '';
       return { content: content.substring(0, 500), fullLength: content.length };
     }
  4. browser_navigate_back → 返回列表页
  5. browser_evaluate → 刷新页面并提取新帖子列表
     () => {
       location.reload();
       return 'reloading';
     }
  6. browser_wait_for → 等待 random(1, 3) 秒
  7. 重新提取列表（可能有新帖子出现）
  8. 保存帖子数据到 data/posts/{id}.json
```

### 1.5 保存数据

- `data/posts/{id}.json` — 单帖详情（含 content 和 scrape_history）
- `data/daily/{date}.json` — 每日汇总数据（合并两源）

### 1.6 Cloudflare 检测

如果在抓取过程中触发 Cloudflare 保护：
- 立即通知用户进行人工验证
- 用户完成验证后，从当前帖子继续抓取

---

## Agent 2: Topic Merger（主题合并器）

**职责**：合并两个数据源的帖子，去重并按主题聚类。

### 2.1 读取数据

- 读取 `data/daily/{date}.json` 中的所有帖子
- 或直接从 Agent 1 输出获取帖子列表

### 2.2 去重处理

- 同一帖子可能同时出现在 Source A 和 Source B
- 按帖子 ID 去重，保留首次抓取的数据
- 记录帖子来源（sources 字段可包含多个源）

### 2.3 主题聚类

按以下维度对帖子进行分组：
- **关键词匹配**：标题和内容中的技术关键词
- **标签分类**：帖子的 tags 字段
- **热度排序**：每组内按 views + replies 排序

建议的主题分组（可根据实际内容调整）：
- 客户端与工具生态
- Agent 与多智能体
- 开源平台与工具
- Claude 生态
- DeepSeek 与国产模型
- 实用教程与讨论
- 行业动态与新闻

### 2.4 输出

返回合并后的帖子列表，包含分组信息。

---

## Agent 3: Trend Analyzer（趋势分析器）

**职责**：分析帖子内容和热度，生成今日技术趋势。

### 3.1 分析维度

- **热度分析**：浏览量、回复数、点赞数最高的帖子
- **内容分析**：帖子正文中反复出现的技术关键词
- **时间线**：今日新出现的话题 vs 持续讨论的话题
- **争议性**：回复数/浏览比最高的帖子（讨论最激烈）

### 3.2 生成趋势总结

输出 3-5 条趋势，每条包含：
- 趋势标题（一句话概括）
- 支撑数据（相关帖子 ID、关键数据）
- 趋势描述（2-3 句话）

示例格式：
```
1. **Claude API 封号潮引发社区讨论**
   - 相关帖子：#2246176（98浏览）、#2245687（451浏览）
   - 多位用户反映账号被封，社区讨论退款策略和替代方案...
```

### 3.3 输出

返回趋势分析结果，供 Agent 4 使用。

---

## Agent 4: Writer（日报撰写器）

**职责**：读取合并数据和趋势分析，生成完整的 Markdown 日报。

### 4.1 日报结构

```markdown
# linux.do 人工智能 技术日报
**{date}** | 发布于 {time} UTC+8 | 新帖 {N} 篇 | 数据来源：linux.do #人工智能 + 前沿快讯

## 今日亮点
（3-5 条高亮，每条一句话概括，包含关键数据如点赞数、回复数）

## 新内容

### 客户端与工具生态
- **帖子标题** — 摘要（浏览 X / 回复 Y）

### Agent 与多智能体
- **帖子标题** — 摘要（浏览 X / 回复 Y）

（按主题分组，每组 2-3 个帖子）

## 数据概览
| 指标 | 数值 |
|------|------|
| 抓取窗口 | ... |
| Source A 原始帖数 | ... |
| Source B 原始帖数 | ... |
| 合并后总数 | ... |
| AI 相关帖数 | ... |

## 今日技术趋势
（来自 Agent 3 的趋势分析，3-5 条）
```

### 4.2 输出

保存到 `data/reports/{date}.md`。

---

## Agent 5: Press Writer（新闻稿撰写器）

**职责**：基于日报内容和社区帖子，生成专业 AI 科技新闻稿。风格对标 Bloomberg Tech / The Verge，信息密度高，无论坛口语。

### 5.1 新闻稿结构

```markdown
# {标题}

{导语 — 一句话概括核心事件，包含关键数据}

## 正文

{2-4 段深度报道，包含：
- 事件背景与时间线
- 关键数据与定价细节
- 行业影响分析
- 引用社区真实观点（去口语化）}

## 趋势分析

{1-2 段趋势研判，将单一事件放入行业大背景中分析}

## 社区反应

{精选 3-5 条有代表性的社区观点，保留真实态度但去除口语化表达}

## 风险与争议

{潜在风险、争议点、尚未验证的信息}
```

### 5.2 写作风格要求

- **对标媒体**：Bloomberg Tech、The Verge、TechCrunch
- **语言风格**：专业科技新闻体，简洁有力，信息密度高
- **禁止**：论坛口语（"佬"、"蹬"、"薅"）、emoji、感叹号堆砌
- **保留**：社区真实观点和争议，但用新闻语言重新表述
- **数据优先**：每个论点必须有数据支撑（浏览量、回复数、价格、额度等）
- **少 AI 味**：避免"值得注意的是"、"总而言之"等 AI 常用套话

### 5.3 内容来源

从以下数据生成新闻稿：
- Agent 4 生成的日报 Markdown（`data/reports/{date}.md`）
- Agent 3 的趋势分析
- 原始帖子数据（`data/posts/*.json`）中的社区讨论

### 5.4 输出

保存到 `data/reports/{date}_press.md`。

---

## Agent 6: PDF Builder（PDF 生成器）

**职责**：将 Markdown 日报转换为 PDF 文件，使用 Typst 排版。

### 6.1 Markdown → Typst

将 Markdown 内容转换为 Typst 格式：

```typst
#set document(title: "linux.do AI 技术日报 - {date}")
#set page(paper: "a4", margin: (top: 2cm, bottom: 2cm, left: 2cm, right: 2cm))
#set text(font: ("Noto Sans CJK SC", "Noto Sans"), size: 10pt)
#set heading(numbering: none)

#align(center)[
  #text(size: 18pt, weight: "bold")[linux.do 人工智能 技术日报]
  #text(size: 12pt)[{date} | 新帖 {N} 篇]
]

// 转换 Markdown 内容为 Typst 格式
// ...
```

### 6.2 Typst 编译

使用 Typst CLI 编译为 PDF：

```bash
typst compile data/reports/{date}.typ data/reports/{date}.pdf
```

### 6.3 Typst 安装检查

如果 Typst 未安装，提示用户安装：

```bash
# macOS
brew install typst

# Linux (使用 cargo)
cargo install typst-cli

# 或下载预编译二进制
# https://github.com/typst/typst/releases
```

### 6.4 输出

- `data/reports/{date}.typ` — Typst 源文件
- `data/reports/{date}.pdf` — 最终 PDF 文件

---

## 数据结构

### 单帖数据 (data/posts/{id}.json)

```json
{
  "id": 2241720,
  "title": "帖子标题",
  "created_at": "2026-05-26",
  "views": 373,
  "like_count": 24,
  "posts_count": 17,
  "tags": ["人工智能"],
  "sources": ["ai_tag", "news"],
  "content": "帖子正文摘要（通过 Playwright MCP 从 .cooked 元素提取，最长 500 字符）",
  "content_fetched_at": "2026-05-26T14:26:31Z",
  "scrape_history": [
    {
      "date": "2026-05-26",
      "source": "ai_tag",
      "fetched_at": "2026-05-26T14:26:31Z"
    }
  ]
}
```

### 每日数据 (data/daily/{date}.json)

```json
{
  "date": "2026-05-26",
  "stats": {
    "raw_source_a": 50,
    "raw_source_b": 45,
    "ai_filtered_source_b": 29,
    "merged_total": 72,
    "ai_posts": 65
  },
  "posts": [...]
}
```

---

## Playwright MCP 登录与 Cookies

### 首次登录

1. 使用 `browser_navigate` 打开 `https://linux.do/login`
2. 用户手动完成登录
3. 使用 `browser_run_code_unsafe` 导出 cookies：
   ```js
   async (page) => {
     const cookies = await page.context().cookies();
     return JSON.stringify(cookies);
   }
   ```
4. 将输出保存到 `data/cookies.json`

### 恢复登录态

使用 `browser_run_code_unsafe` 加载已保存的 cookies：
```js
async (page) => {
  const cookies = /* 从 data/cookies.json 读取 */;
  await page.context().addCookies(cookies);
  return `Loaded ${cookies.length} cookies`;
}
```

---

## 注意事项

- **必须使用 Playwright MCP 浏览器工具抓取**，不要使用 curl/JSON API，避免触发 Cloudflare 保护
- 模拟人类浏览行为：每帖随机等待 1-3 秒
- 如果触发 Cloudflare 挑战页，通知用户进行人工验证
- 返回列表页时刷新页面，获取最新帖子
- 每个数据源最多抓取 50 帖
- 抓取前检查历史记录，避免重复抓取
- Cookies 通过 Playwright MCP 的 `page.context().cookies()` 持久化到 `data/cookies.json`
- 列表页帖子的 like_count 显示为 0（Discourse 显示问题），实际点赞数需从详情页获取
- 正文从 `.cooked` 元素提取，最长 500 字符
- PDF 生成使用 Typst，需确保已安装 typst CLI
