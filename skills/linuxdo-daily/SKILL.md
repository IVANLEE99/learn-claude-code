---
name: linuxdo-daily
description: linux.do AI日报/周报自动生成。多 Agent 协作：Crawler 抓取双数据源 → Topic Merger 合并主题 → Trend Analyzer 生成趋势 → Writer 输出日报/周报 → Press Writer 生成新闻稿 → PDF Builder 生成 PDF。触发词：日报、周报、linuxdo日报、AI日报、AI周报、技术日报、weekly
version: 4.1.0
---

# linuxdo-daily — AI 技术日报生成 Skill（多 Agent 架构）

从 linux.do 自动抓取 AI 相关帖子，通过 6 个专用 Agent 协作生成每日技术日报。

## ⚡ 权限预授权（必须最先执行）

**开始抓取前，必须一次性授权所有 Playwright MCP 工具**，避免中途反复弹出授权窗口。

### 预授权步骤

1. **关闭旧浏览器实例**（如存在）：
   ```bash
   pkill -f "mcp-chrome" 2>/dev/null; sleep 2
   ```

2. **导航到目标页面触发浏览器启动**：
   ```
   browser_navigate → https://linux.do/tag/444-tag/444
   ```

3. **等待 Cloudflare 验证通过**（如有）：
   ```
   browser_wait_for → time: 10
   ```

4. **加载 cookies 保持登录态**（如有 cookies.json）：
   ```
   browser_run_code_unsafe → 读取 data/cookies.json 并加载
   ```

5. **此时所有 Playwright MCP 工具应已获得授权**，后续抓取不再需要逐次授权。

### 权限检查清单

以下工具在抓取过程中会用到，确保全部已授权：
- `browser_navigate` — 页面导航
- `browser_wait_for` — 等待加载
- `browser_run_code_unsafe` — 执行 JS 代码（滚动、批量抓取）
- `browser_evaluate` — 执行 JS 表达式（提取数据）
- `browser_snapshot` — 页面快照（调试用）
- `browser_take_screenshot` — 截图（调试用）

### ⚠️ 反检测措施（重要）

**必须遵守以下规则，避免触发官方警告或封号**：

1. **随机延迟**：每次请求后随机等待 2-5 秒（使用 `Math.random()`）
2. **User-Agent 轮换**：模拟真实浏览器行为
3. **批次间隔**：每批（20帖）完成后等待 10-15 秒
4. **检测警告**：如果收到官方警告，立即停止爬取并等待 24 小时
5. **限制并发**：单次最多同时处理 5 个页面

---

## 数据源

| 源 | URL | 说明 |
|----|-----|------|
| Source A: #人工智能 标签 | `https://linux.do/tag/444-tag/444` | 直接命中，无需过滤 |
| Source B: 前沿快讯 分类 | `https://linux.do/c/news/34` | 全部新闻，需按 tags 过滤 |

## 触发条件

### 日报模式
当用户说以下关键词时激活：
- "日报"、"AI日报"、"技术日报"
- "linuxdo日报"、"抓取linuxdo"
- "今日AI新闻"、"AI资讯"

### 周报模式
当用户说以下关键词时激活：
- "周报"、"AI周报"、"技术周报"
- "weekly"、"出周报"
- "本周AI新闻"、"一周总结"

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

## 过滤规则

### 公益站过滤（日报模式必须执行）

以下帖子在生成日报时**必须过滤掉**，不纳入统计和报告：

**关键词过滤**（标题、标签、内容中出现以下任一即过滤）：
- 公益站、公益推广、公益、公益站、公益站
- LDC、ldc、cdk
- 签到、白嫖、薅羊毛、薅秃
- 充值额度、兑换码、免费额度
- 号池、号商、共享号

**意图过滤**（帖子主要内容为以下类型即过滤）：
- 分享免费 API 额度/Key 的帖子
- 公益站注册/使用教程
- 公益站运维公告（关站、维护、升级等）
- 薅羊毛攻略

### 历史去重（日报模式必须执行）

生成日报前，扫描所有历史日报 Markdown 文件，提取已报道的帖子 ID：

```python
import re, os
prev_ids = set()
for f in os.listdir('data/reports'):
    if f.endswith('.md') and f != f'{today}.md':
        with open(f'data/reports/{f}') as fh:
            ids = re.findall(r'\[(\d{7,})\]', fh.read())
            prev_ids.update(ids)
```

已存在于 `prev_ids` 中的帖子不再纳入今日日报。

### 24小时范围筛选（日报模式必须执行）

帖子必须在 24 小时范围内才纳入日报。使用 Discourse JSON API 获取 `created_at`：

```
GET /t/{id}.json → post_stream.posts[0].created_at
```

**时间窗口**：今日 UTC+8 00:00 至 24:00（即 UTC 前一天 16:00 至今日 16:00）

**批量获取日期策略**：
1. 先提取全部帖子 ID（两源合并后）
2. 用 `browser_run_code_unsafe` 批量获取 `created_at`（每批 20 帖，使用 JSON API）
3. 按时间窗口筛选，只保留窗口内的帖子
4. **注意**：Discourse ID 不按日期顺序（跨分类），**不能用 ID 阈值判断日期**

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

## 周报模式（Weekly Report）

### 周报工作流

周报**不需要重新抓取**，直接读取 `data/daily/` 下最近7天的数据进行聚合。

```
┌─────────────────────────────────────────────────────────────────┐
│                    linuxdo-weekly 工作流                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────┐                               │
│  │  Agent 1: Data Loader        │                               │
│  │  - 读取最近7天 daily/*.json   │                               │
│  │  - 跨天去重（同帖多天出现）   │                               │
│  │  - 合并为周数据集             │                               │
│  │  → 输出: 合并后的周帖子列表   │                               │
│  └──────────────┬───────────────┘                               │
│                 ▼                                                │
│  ┌──────────────────────────────┐                               │
│  │  Agent 2: Topic Merger       │                               │
│  │  - 按主题聚类分组             │                               │
│  │  - 识别一周内的主题演变       │                               │
│  │  → 输出: 周主题分组           │                               │
│  └──────────────┬───────────────┘                               │
│                 ▼                                                │
│  ┌──────────────────────────────┐                               │
│  │  Agent 3: Trend Analyzer     │                               │
│  │  - 分析一周趋势变化           │                               │
│  │  - 识别新兴话题和衰减话题     │                               │
│  │  - 生成周趋势总结（5-8条）    │                               │
│  │  → 输出: 本周技术趋势         │                               │
│  └──────────────┬───────────────┘                               │
│                 ▼                                                │
│  ┌──────────────────────────────┐                               │
│  │  Agent 4: Weekly Writer      │                               │
│  │  - 生成周报 Markdown          │                               │
│  │  → 输出: data/weekly/{week}.md│                               │
│  └──────────────┬───────────────┘                               │
│                 ▼                                                │
│  ┌──────────────────────────────┐                               │
│  │  Agent 5: Press Writer       │                               │
│  │  - 生成周报新闻稿             │                               │
│  │  → 输出: data/weekly/{week}_press.md│                        │
│  └──────────────┬───────────────┘                               │
│                 ▼                                                │
│  ┌──────────────────────────────┐                               │
│  │  Agent 6: PDF Builder        │                               │
│  │  - Typst 编译 → PDF           │                               │
│  │  → 输出: data/weekly/{week}.pdf│                              │
│  └──────────────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 周报 Agent 1: Data Loader（数据加载器）

**职责**：读取最近7天的日报数据，跨天去重，合并为周数据集。

#### 1.1 确定日期范围

```python
# 计算最近7天的日期
from datetime import datetime, timedelta
end_date = datetime.now()
start_date = end_date - timedelta(days=7)
dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
```

#### 1.2 读取并合并数据

```python
import json, os

all_posts = {}
for date in dates:
    path = f'data/daily/{date}.json'
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        for p in data['posts']:
            pid = p['id']
            if pid not in all_posts:
                all_posts[pid] = {**p, 'first_seen': date}
            else:
                # 更新浏览量/回复数（取最大值）
                all_posts[pid]['views'] = max(all_posts[pid].get('views', '0'), p.get('views', '0'))
                all_posts[pid]['replies'] = max(all_posts[pid].get('replies', '0'), p.get('replies', '0'))

posts = sorted(all_posts.values(), key=lambda x: int(x['id']), reverse=True)
```

#### 1.3 去除话题延续

对合并后的帖子进行话题延续过滤（同日报逻辑）：
- 识别连续多天出现的同一话题
- 保留话题的最新进展帖，标记早期帖子为"延续"

#### 1.4 输出

保存到 `data/weekly/{week}.json`，格式同 daily。

### 周报 Agent 4: Weekly Writer（周报撰写器）

**职责**：生成一周技术趋势周报。

#### 4.1 周报结构

```markdown
# linux.do 人工智能 技术周报
**{start_date} ~ {end_date}** | 本周新帖 {N} 篇 | 数据来源：linux.do #人工智能 + 前沿快讯

## 本周五大事件
（5 条核心事件，每条一句话概括 + 关键数据）

## 每日速览

### {date_1}（周{weekday}）
- **事件1** — 摘要（浏览 X / 回复 Y）
- **事件2** — 摘要

### {date_2}（周{weekday}）
...

## 本周趋势分析
（5-8 条趋势，分析一周内的变化）

### 趋势1: {标题}
- 涉及天数: {days}
- 相关帖子: {top_post_ids}
- 分析: {description}

## 本周数据汇总
| 指标 | 数值 |
|------|------|
| 本周总帖数 | ... |
| 日均帖数 | ... |
| 最热帖子 | ... |
| 最多回复 | ... |
| 新兴话题数 | ... |
| 延续话题数 | ... |

## 下周展望
（基于本周趋势，预测下周可能的热点）
```

#### 4.2 输出

保存到 `data/weekly/{week}.md`，其中 `{week}` 格式为 `{start_date}~{end_date}`。

### 周报命名规则

- 周报文件: `data/weekly/2026-06-01~2026-06-07.md`
- 新闻稿: `data/weekly/2026-06-01~2026-06-07_press.md`
- PDF: `data/weekly/2026-06-01~2026-06-07.pdf`
- Typst: `data/weekly/2026-06-01~2026-06-07.typ`

---

## Agent 1: Crawler（抓取器）

**职责**：从两个数据源抓取帖子，获取时间戳筛选24h范围，检查历史记录，批量抓取正文。

### ⚠️ 反检测规则（必须遵守）

1. **每次请求后随机等待 2-5 秒**：使用 `Math.floor(Math.random() * 3000) + 2000`
2. **每批完成后等待 10-15 秒**：防止触发频率限制
3. **检测 Cloudflare 挑战**：如果页面标题包含 "Just a moment" 或 "Checking your browser"，立即停止并等待 15 秒
4. **检测官方警告**：如果页面内容包含 "异常的自动化访问行为"，立即停止爬取并通知用户
5. **单次最多处理 5 个页面**：避免并发过高

### 1.1 打开列表页

使用 Playwright MCP `browser_navigate` 依次打开：
- Source A: `https://linux.do/tag/444-tag/444`
- Source B: `https://linux.do/c/news/34`

如果触发 Cloudflare 挑战页，使用 `browser_wait_for → time: 15` 等待自动通过。如仍无法通过，通知用户进行人工验证。

### 1.2 滚动加载全部帖子

打开列表页后，使用 `browser_run_code_unsafe` 滚动加载。**至少滚动 15 次**（每次间隔 3 秒），确保加载全部帖子：

```js
async (page) => {
  for (let i = 0; i < 15; i++) {
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(3000);  // 增加到3秒
    // 检测是否触发了验证
    const title = await page.title();
    if (title.includes('Just a moment') || title.includes('Checking')) {
      await page.waitForTimeout(15000);  // 等待验证通过
    }
  }
  return 'scrolled 15 times';
}
```

滚动完成后用 `browser_evaluate` 检查帖子数量。如果帖子数 < 400，再追加 10 次滚动。最终目标是加载 400+ 帖子。

### 1.3 提取帖子列表

使用 `browser_evaluate` 提取列表中的帖子。**注意：不在此步骤过滤日期，先全部提取**。

```js
() => {
  const rows = document.querySelectorAll('tr.topic-list-item');
  const posts = [];
  rows.forEach(row => {
    const topicId = row.getAttribute('data-topic-id');
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

### 1.4 批量获取时间戳（关键步骤）

**Discourse ID 不按日期顺序（跨分类），不能用 ID 阈值判断日期。** 必须使用 JSON API 获取 `created_at`。

使用 `browser_run_code_unsafe` 批量获取，每批 15 帖（减少批量以降低风险）：

```js
async (page) => {
  const ids = ["2326008","2325913", /* ... 15个ID ... */];
  const results = [];
  for (const id of ids) {
    try {
      await page.goto('https://linux.do/t/' + id + '.json', {
        waitUntil: 'domcontentloaded', timeout: 10000
      });
      // 随机延迟 2-5 秒
      await page.waitForTimeout(Math.floor(Math.random() * 3000) + 2000);
      
      const data = await page.evaluate(() => {
        try {
          const text = document.body.innerText;
          const json = JSON.parse(text);
          return {
            created_at: json.post_stream?.posts?.[0]?.created_at || json.created_at || '',
            title: json.title || '',
            views: json.views || 0,
            posts_count: json.posts_count || 0,
            like_count: json.post_stream?.posts?.[0]?.like_count || 0
          };
        } catch(e) { return { error: 'parse' }; }
      });
      results.push({ id, ...data });
    } catch (e) {
      results.push({ id, error: 'nav' });
    }
  }
  return results;
}
```

**24小时时间窗口**：今日 UTC+8 00:00 至 24:00（即 UTC 前一天 16:00 至今日 16:00）

筛选代码：
```python
from datetime import datetime, timezone, timedelta
cst = timezone(timedelta(hours=8))
today_start = datetime.now(cst).replace(hour=0, minute=0, second=0, microsecond=0)
today_end = today_start + timedelta(days=1)
# 转为 UTC 用于比较
utc_start = today_start.astimezone(timezone.utc)
utc_end = today_end.astimezone(timezone.utc)
# 筛选: utc_start <= created_at < utc_end
```

### 1.5 批量抓取正文（核心优化）

**禁止逐条抓取**（太慢，500帖需要17分钟）。必须使用 `browser_run_code_unsafe` 批量抓取，每批 15 帖：

```js
async (page) => {
  const ids = ["2326008","2325913", /* ... 15个ID ... */];
  const results = [];
  for (const id of ids) {
    try {
      await page.goto('https://linux.do/t/topic/' + id, {
        waitUntil: 'domcontentloaded', timeout: 12000
      });
      // 随机延迟 2-5 秒
      await page.waitForTimeout(Math.floor(Math.random() * 3000) + 2000);
      
      // 检测 Cloudflare 挑战
      const title = await page.title();
      if (title.includes('Just a moment') || title.includes('Checking')) {
        await page.waitForTimeout(15000);  // 等待验证
        continue;  // 跳过此帖子
      }
      
      const data = await page.evaluate(() => {
        const title = document.querySelector('.fancy-title')?.textContent?.trim() || '';
        const cooked = document.querySelector('.cooked');
        const content = cooked ? cooked.innerText.trim().substring(0, 500) : '';
        const views = document.querySelector('.views .number')?.textContent?.trim() || '0';
        const tags = [...document.querySelectorAll('.discourse-tag')].map(x => x.textContent.trim());
        return { title, content, views, tags };
      });
      
      // 跳过空内容帖子
      if (!data.title || !data.content) {
        continue;
      }
      
      results.push({ id, ...data });
    } catch (e) {
      results.push({ id, error: e.message.substring(0, 100) });
    }
  }
  return results;
}
```

**批量抓取策略**：
- 每批 15 帖，每帖随机等待 2-5 秒
- 每批完成后等待 10-15 秒
- 如果触发连接限制（`ERR_CONNECTION_CLOSED`），立即停止，进入恢复流程
- 如果检测到 Cloudflare 挑战，等待 15 秒后继续

### 1.6 跳过已存在帖子

抓取前检查 `data/posts/{id}.json` 是否已存在，已存在的跳过：

```python
import os
def should_fetch(pid):
    return not os.path.exists(f'data/posts/{pid}.json')
```

### 1.7 连接恢复流程

当批量抓取触发连接限制时：

1. **停止当前批次**
2. 导航到主页恢复连接：`browser_navigate → https://linux.do`
3. 等待 10 秒（增加等待时间）
4. 用小批次（10帖）恢复抓取
5. 确认连接正常后恢复 15 帖/批

### 1.8 保存数据

- `data/posts/{id}.json` — 单帖详情（含 content 和 scrape_history）
- `data/daily/{date}.json` — 每日汇总数据（合并两源）

### 1.9 Source B 特殊处理

Source B（`/c/news/34`）需要按标签过滤 AI 相关帖子：
```js
() => {
  const tags = Array.from(row.querySelectorAll('.discourse-tag')).map(t => t.textContent.trim());
  const isAi = tags.some(t => /人工智能|ai/i.test(t));
  // 只保留 isAi = true 的帖子
}
```

Source B 中不在 Source A 的独立帖子也需抓取正文。

### 1.10 官方警告处理

**如果收到官方警告（"异常的自动化访问行为"）**：

1. **立即停止所有爬取操作**
2. **在 linux.do 上回复确认**（告知用户手动操作）
3. **等待 24 小时后再恢复**
4. **降低后续爬取频率**：每批 10 帖，每帖等待 5 秒

---

## Agent 2: Topic Merger（主题合并器）

**职责**：合并两个数据源的帖子，去重，过滤公益站，按主题聚类。

### 2.1 读取数据

- 读取 Agent 1 输出的帖子列表（已含时间戳和正文）
- 读取 `data/posts/*.json` 获取已抓取的帖子详情

### 2.2 去重处理

- 同一帖子可能同时出现在 Source A 和 Source B
- 按帖子 ID 去重，保留首次抓取的数据
- 记录帖子来源（sources 字段可包含多个源）

### 2.3 公益站过滤（必须执行）

过滤掉以下类型的帖子：

```python
GONGYI_KEYWORDS = ['公益站', '公益推广', 'LDC', 'ldc', 'cdk', '签到', '白嫖', '薅羊毛', '薅秃', '兑换码', '免费额度', '号池', '号商']

def is_gongyi(post):
    title = post.get('title', '')
    tags = post.get('tags', [])
    content = post.get('content', '')
    all_text = title + ' ' + content + ' ' + ' '.join(tags)
    return any(kw in all_text for kw in GONGYI_KEYWORDS)
```

**过滤范围**：标题、标签、内容中出现任一关键词即过滤。

### 2.4 历史去重（必须执行）

扫描所有历史日报 Markdown 文件，提取已报道的帖子 ID：

```python
import re, os
prev_ids = set()
for f in os.listdir('data/reports'):
    if f.endswith('.md') and f != f'{today}.md':
        with open(f'data/reports/{f}') as fh:
            ids = re.findall(r'\[(\d{7,})\]', fh.read())
            prev_ids.update(ids)
```

已存在于 `prev_ids` 中的帖子不再纳入今日日报。

### 2.5 主题聚类

按以下维度对帖子进行分组：
- **关键词匹配**：标题和内容中的技术关键词
- **标签分类**：帖子的 tags 字段
- **热度排序**：每组内按 views + replies 排序

建议的主题分组（可根据实际内容调整）：
- OpenAI/ChatGPT/Codex 生态
- Claude/Anthropic 生态
- MiniMax/MiMo 与国产模型
- Google/Gemini 生态
- 开源模型与发布
- AI 编程工具与 Agent
- AI 视频与图像生成
- 行业动态与新闻
- 支付、订阅与账号
- 技术讨论与问答

**注意**：不再包含"公益站与中转站"分组（已在 2.3 步骤过滤）。

### 2.6 输出

返回过滤、去重、分组后的帖子列表。

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
**{date}** | 发布于 {time} UTC+8 | 新帖 {N} 篇（过滤公益站后）
数据来源：linux.do #人工智能 + 前沿快讯

## 今日亮点
（3-5 条高亮，每条一句话概括，包含关键数据如浏览量）

## 新内容

### OpenAI/ChatGPT/Codex 生态
- **帖子标题** — 摘要（浏览 X）

### Claude/Anthropic 生态
- **帖子标题** — 摘要（浏览 X）

（按主题分组，每组 3-10 个帖子，覆盖所有有实质内容的帖子）

## 数据概览
| 指标 | 数值 |
|------|------|
| Source A (#人工智能) 抓取帖数 | ... |
| Source B (前沿快讯) 抓取帖数 | ... |
| Source B AI 过滤后 | ... |
| 合并去重后总数 | ... |
| 去除已报道帖子后 | ... |
| 过滤公益站后 | {最终数量} |
| 24小时范围内 | {最终数量} |

## 今日技术趋势
（来自 Agent 3 的趋势分析，3-5 条）
```

### 4.2 过滤流程（Writer 必须执行）

生成日报前，按以下顺序执行过滤：

1. **去除已报道帖子**：扫描 `data/reports/*.md` 提取历史帖子 ID，排除已报道的
2. **过滤公益站**：按 2.3 节规则过滤公益站相关帖子
3. **24小时筛选**：只保留 `created_at` 在今日 UTC+8 00:00-24:00 范围内的帖子
4. **统计并输出**：在数据概览中报告各步骤的过滤数量

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

### 浏览器与抓取
- **必须使用 Playwright MCP 浏览器工具抓取**，不要使用 curl/JSON API，避免触发 Cloudflare 保护
- **开始前必须预授权**：先关闭旧浏览器实例（`pkill -f "mcp-chrome"`），再导航触发新实例
- **必须批量抓取正文**：每批 15 帖，每帖随机等待 2-5 秒，禁止逐条抓取
- 滚动加载至少 15 次，确保帖子数 > 400
- 如果触发连接限制（`ERR_CONNECTION_CLOSED`），导航到主页恢复后用小批次继续
- 如果触发 Cloudflare 挑战页，先 `browser_wait_for → time: 15` 等待自动通过
- 每个数据源最多抓取 500 帖
- Cookies 通过 Playwright MCP 的 `page.context().cookies()` 持久化到 `data/cookies.json`

### ⚠️ 反检测规则（必须遵守）
1. **每次请求后随机等待 2-5 秒**：使用 `Math.floor(Math.random() * 3000) + 2000`
2. **每批完成后等待 10-15 秒**：防止触发频率限制
3. **检测 Cloudflare 挑战**：如果页面标题包含 "Just a moment" 或 "Checking your browser"，立即停止并等待 15 秒
4. **检测官方警告**：如果页面内容包含 "异常的自动化访问行为"，立即停止爬取并通知用户
5. **单次最多处理 5 个页面**：避免并发过高
6. **跳过空内容帖子**：如果帖子标题或内容为空，跳过该帖子

### 日期与过滤
- **不能用 ID 阈值判断日期**：Discourse ID 不按日期顺序（跨分类），必须用 JSON API 获取 `created_at`
- **24小时时间窗口**：今日 UTC+8 00:00 至 24:00（即 UTC 前一天 16:00 至今日 16:00）
- **必须过滤公益站**：公益站、LDC、cdk、签到、白嫖、薅羊毛、兑换码、免费额度、号池、号商
- **必须历史去重**：扫描 `data/reports/*.md` 提取已报道帖子 ID，避免重复
- Source B 需按 AI 标签过滤

### 数据格式
- 列表页帖子的 like_count 显示为 0（Discourse 显示问题），实际点赞数需从 JSON API 获取
- 正文从 `.cooked` 元素提取，最长 500 字符
- Typst 中 `$` 符号需转义为 `\$`
- PDF 生成使用 Typst，需确保已安装 typst CLI

### 流程完整性
- **必须按顺序完成所有 Agent**：Crawler → Topic Merger → Trend Analyzer → Writer → Press Writer → PDF Builder
- **Press Writer 和 PDF Builder 不可跳过**：即使用户没有明确要求，也必须生成
- 每个 Agent 完成后保存中间结果，确保流程可中断恢复

### 官方警告处理
**如果收到官方警告（"异常的自动化访问行为"）**：
1. **立即停止所有爬取操作**
2. **在 linux.do 上回复确认**（告知用户手动操作）
3. **等待 24 小时后再恢复**
4. **降低后续爬取频率**：每批 10 帖，每帖等待 5 秒

---

## 更新日志

### v4.1.0 (2026-06-10)
基于实际爬取经验优化：

**反检测措施**：
- 添加随机延迟（2-5秒/请求）
- 每批完成后等待 10-15 秒
- 检测 Cloudflare 挑战并自动等待
- 检测官方警告并自动停止
- 限制单次最多处理 5 个页面

**错误处理优化**：
- 跳过空内容帖子
- 添加重试逻辑
- 更好的 Cloudflare 处理

**性能优化**：
- 批量大小从 20 减少到 15
- 增加批次间延迟
- 更保守的爬取策略

**数据验证**：
- 添加帖子数据验证
- 跳过无效帖子
