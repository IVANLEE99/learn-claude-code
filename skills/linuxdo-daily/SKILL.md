---
name: linuxdo-daily
description: linux.do AI日报自动生成。多 Agent 协作：Crawler 抓取双数据源 → Topic Merger 合并主题 → Trend Analyzer 生成趋势 → Writer 输出日报 → Press Writer 生成新闻稿 → PDF Builder 生成 PDF。触发词：日报、linuxdo日报、AI日报、技术日报、抓取linuxdo
version: 2.2.0
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
│  │  - 滚动加载全部帖子           │                               │
│  │  - 提取帖子链接               │                               │
│  │  - 批量抓取正文（每批20帖）   │                               │
│  │  - 每源最多500帖              │                               │
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
│  └──────────────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent 1: Crawler（抓取器）

**职责**：从两个数据源抓取帖子，检查历史记录，批量抓取正文。

### 1.1 打开列表页

使用 Playwright MCP `browser_navigate` 依次打开：
- Source A: `https://linux.do/tag/444-tag/444`
- Source B: `https://linux.do/c/news/34`

如果触发 Cloudflare 挑战页，通知用户进行人工验证。

### 1.2 滚动加载全部帖子

打开列表页后，使用 `browser_run_code_unsafe` 滚动加载。**至少滚动 15 次**（每次间隔 2 秒），确保加载全部帖子：

```js
async (page) => {
  for (let i = 0; i < 15; i++) {
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(2000);
  }
  return 'scrolled 15 times';
}
```

滚动完成后用 `browser_evaluate` 检查帖子数量。如果帖子数 < 400，再追加 10 次滚动。最终目标是加载 400+ 帖子。

### 1.3 提取帖子链接（含动态ID范围判断）

使用 `browser_evaluate` 提取列表中的帖子。**关键：需动态判断"今日"帖子的ID范围**。

首先提取全部帖子的 ID，观察最大 ID 范围来判断今日起始 ID：
```js
() => {
  const rows = document.querySelectorAll('tr.topic-list-item');
  const ids = [];
  rows.forEach(row => {
    const topicId = row.getAttribute('data-topic-id');
    if (topicId) ids.push(parseInt(topicId));
  });
  ids.sort((a, b) => a - b);
  // 返回最大/最小ID和分布，用于判断今日范围
  return { min: ids[0], max: ids[ids.length-1], count: ids.length };
}
```

**ID范围判断规则**：
- 查看 `ls data/posts/*.json | sed 's/.*\///;s/\.json//' | sort -n | tail -5` 获取已有最大 ID
- 今日帖子 ID 必须 > 已有最大 ID
- 提取时只保留 ID > 阈值的帖子

提取帖子的完整代码：
```js
() => {
  const rows = document.querySelectorAll('tr.topic-list-item');
  const posts = [];
  rows.forEach(row => {
    const topicId = row.getAttribute('data-topic-id');
    const id = parseInt(topicId);
    if (id < TODAY_ID_THRESHOLD) return; // 动态阈值
    const titleLink = row.querySelector('.main-link a.title') || row.querySelector('a.title');
    const title = titleLink ? titleLink.textContent.trim() : '';
    const href = titleLink ? titleLink.getAttribute('href') : '';
    const views = row.querySelector('.views .number')?.textContent?.trim() || '0';
    const replies = row.querySelector('.posts .number')?.textContent?.trim() || '0';
    const tags = Array.from(row.querySelectorAll('.discourse-tag')).map(t => t.textContent.trim());
    posts.push({ id: topicId, title, href, views, replies, tags });
  });
  return posts;
}
```

### 1.4 批量抓取正文（核心优化）

**禁止逐条抓取**（太慢，500帖需要17分钟）。必须使用 `browser_run_code_unsafe` 批量抓取，每批 20 帖：

```js
async (page) => {
  const ids = ["2294504","2292281","2295037", /* ... 20个ID ... */];
  const results = [];
  for (const id of ids) {
    try {
      await page.goto('https://linux.do/t/topic/' + id, {
        waitUntil: 'domcontentloaded', timeout: 12000
      });
      await page.waitForTimeout(2000); // 模拟人类阅读
      const data = await page.evaluate(() => {
        const cooked = document.querySelector('.cooked');
        return cooked ? cooked.innerText.trim().substring(0, 500) : '';
      });
      results.push({ id, content: data.substring(0, 300) });
    } catch (e) {
      results.push({ id, error: e.message.substring(0, 100) });
    }
  }
  return results;
}
```

**批量抓取策略**：
- 每批 20 帖，每帖等待 2 秒
- 每批耗时约 40-60 秒
- 全部 500 帖约需 25 批 × 50 秒 ≈ 20 分钟
- 如果触发连接限制（`ERR_CONNECTION_CLOSED`），立即停止，进入恢复流程

### 1.5 连接恢复流程

当批量抓取触发连接限制时：

1. **停止当前批次**
2. 导航到主页恢复连接：`browser_navigate → https://linux.do`
3. 等待 5 秒
4. 用小批次（10帖）恢复抓取
5. 确认连接正常后恢复 20 帖/批

### 1.6 保存数据

- `data/posts/{id}.json` — 单帖详情（含 content 和 scrape_history）
- `data/daily/{date}.json` — 每日汇总数据（合并两源）

### 1.7 Source B 特殊处理

Source B（`/c/news/34`）需要按标签过滤 AI 相关帖子：
```js
() => {
  const tags = Array.from(row.querySelectorAll('.discourse-tag')).map(t => t.textContent.trim());
  const isAi = tags.some(t => /人工智能|ai/i.test(t));
  // 只保留 isAi = true 的帖子
}
```

Source B 中不在 Source A 的独立帖子也需抓取正文。

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
- OpenAI/ChatGPT 生态
- Codex 生态
- Claude 生态
- MiniMax/MiMo 与国产模型
- Agent 与工具
- 行业动态与新闻
- 公益站与中转站
- 支付与接码

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

### OpenAI/ChatGPT 生态
- **帖子标题** — 摘要（浏览 X / 回复 Y）

### Codex 生态
- **帖子标题** — 摘要（浏览 X / 回复 Y）

（按主题分组，每组 3-8 个帖子，覆盖所有有实质内容的帖子）

## 数据概览
| 指标 | 数值 |
|------|------|
| Source A 原始帖数 | ... |
| Source B 原始帖数 | ... |
| Source B AI 过滤后 | ... |
| 合并去重后总数 | ... |
| 抓取正文帖数 | ... |

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
#set text(font: ("PingFang SC", "Noto Sans CJK SC", "Noto Sans"), size: 10pt)
#set heading(numbering: none)

#align(center)[
  #text(size: 18pt, weight: "bold")[linux.do 人工智能 技术日报]
  #v(4pt)
  #text(size: 12pt)[{date} | 新帖 {N} 篇]
  #v(2pt)
  #text(size: 10pt, fill: gray)[数据来源：linux.do \#人工智能 + 前沿快讯]
]

// 转换 Markdown 内容为 Typst 格式
// ...
```

**重要**：Typst 中 `$` 是数学模式符号，文本中的 `$` 必须转义为 `\$`。例如：
- `1000x2000$兑换码` → `1000x2000\$兑换码`
- `$35-65` → `\$35-65`

### 6.2 Typst 编译

使用 Typst CLI 编译为 PDF：

```bash
typst compile data/reports/{date}.typ data/reports/{date}.pdf
```

### 6.3 字体说明

macOS 使用 `PingFang SC` 作为主字体。`Noto Sans CJK SC` 和 `Noto Sans` 作为后备字体，如果未安装会显示警告但不影响编译。

### 6.4 Typst 安装检查

如果 Typst 未安装，提示用户安装：

```bash
# macOS
brew install typst

# Linux (使用 cargo)
cargo install typst-cli

# 或下载预编译二进制
# https://github.com/typst/typst/releases
```

### 6.5 输出

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
- **必须批量抓取正文**：每批 20 帖，每帖等待 2 秒，禁止逐条抓取
- 滚动加载至少 15 次，确保帖子数 > 400
- 动态判断今日帖子 ID 范围（`ls data/posts/*.json | sort -n | tail -5` 获取最大 ID）
- 如果触发连接限制（`ERR_CONNECTION_CLOSED`），导航到主页恢复后用小批次继续
- 如果触发 Cloudflare 挑战页，通知用户进行人工验证
- 每个数据源最多抓取 500 帖
- 抓取前检查历史记录，避免重复抓取
- Source B 需按 AI 标签过滤
- Cookies 通过 Playwright MCP 的 `page.context().cookies()` 持久化到 `data/cookies.json`
- 列表页帖子的 like_count 显示为 0（Discourse 显示问题），实际点赞数需从详情页获取
- 正文从 `.cooked` 元素提取，最长 500 字符
- Typst 中 `$` 符号需转义为 `\$`
- PDF 生成使用 Typst，需确保已安装 typst CLI
