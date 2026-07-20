---
name: linuxdo-daily
description: linux.do AI日报/周报/月报自动生成。多 Agent 协作：Crawler 抓取双数据源 → Topic Merger 合并主题 → Trend Analyzer 生成趋势 → Writer 输出日报/周报/月报 → Press Writer 生成新闻稿 → PDF Builder 生成 PDF。触发词：日报、周报、月报、linuxdo日报、AI日报、AI周报、AI月报、技术日报、weekly、monthly、过滤后全部抓取完
version: 15.5.0
---

# linuxdo-daily — AI 技术日报生成 Skill（多 Agent 架构）

从 linux.do 自动抓取 AI 相关帖子，通过 6 个专用 Agent 协作生成每日技术日报，并支持周报与月报模式。

> **v15.5 核心改进（2026-07-20 日报实测）**：批抓 MCP 长静默超时；`ERR_ABORTED` 重置浏览器重试；batch 污染校验；`retryN` 批号；中断后续跑；实测 364 帖 / 26+ 批。
> **v15.4 核心改进（2026-07-19 周报实测）**：周聚合浏览量解析 `6.2k/万`；同 id 保留更高 views；`week_posts[id]['_day']` 记录来源日；周 PDF/Typst 同步落盘；与 ai-news-factory 衔接时 **PDF 落盘后再开视频**。
> **v15.3 核心改进（2026-07-18 实测）**：全量 19 批 / 531 帖闭环；Playwright 批抓与「浏览器退出」解耦说明；batch 保存脚本固化；二次过滤后再 Writer；与 ai-news-factory 衔接时避免边抓边开多浏览器。
> **v15.2 核心改进（2026-07-17 实测）**：固定项目 cwd；「过滤后全部抓取完」冷启动协议；`crawl_queue`/`batch_ids` 预切分；transcript 回填 batch；正文二次公益站过滤；列表页 views 合并；全量规模 500+ 帖。
> **v15.1 核心改进**：概念候选受控入库——日报附录经去重/过滤后只追加最小 `candidate`，不写口播、不晋升 ready。
> **v15 核心改进**：接入 `ai-concept-bank` 技术锚点；可信度五档；账号权益黑话过滤。
> **v14 核心改进**：Cloudflare 点击绕过、周报模式完整流程、并行 Agent 优化、旧 batch 文件清理。
> **v13 核心改进**：新增月报模式。月报基于当月已抓取数据与已生成的日报数据聚合，不重复抓取，输出月度趋势总结 + 主题归纳 + 下月展望。
> **v12 核心改进**：批量抓取数据强制保存、空帖检测跳过、官方警告检测、全量抓取支持、Typst 特殊字符处理。

## ⚡ 工作目录与冷启动（v15.2 必读）

### 固定项目根目录

**所有 `data/` 读写必须在项目目录执行**，不要依赖 shell 默认 cwd：

```bash
cd /Users/youngsdream/Documents/learn-claude-code
# 或在 Python 内：
# os.chdir('/Users/youngsdream/Documents/learn-claude-code')
```

> **2026-07-17 实测坑**：Bash 可能落在 `~/.claude/projects/...`，导致 `data/` 不存在、清理 batch 误报 0、写出文件写到错误位置。

`browser_evaluate` 的 `filename` 参数也要用**绝对路径**：

```text
/Users/youngsdream/Documents/learn-claude-code/data/source_a.json
/Users/youngsdream/Documents/learn-claude-code/data/source_b.json
```

### 触发词：「过滤后全部抓取完」/「0717 linuxdo日报 过滤后全部抓取完」

含义：**按全量模式跑完日报流水线**（不是“已经有 daily 了只写报告”）。

| 磁盘状态 | 动作 |
|---------|------|
| 无 `data/daily/{date}.json`，batch 也为昨/空 | **从 Crawler 冷启动**：清旧 batch → 预授权 → 双源列表 → 合并过滤 → **全量正文** → Writer/Press/PDF |
| 有 `batch_browser_*.json` 且 mtime 是今天、无 daily | 合并 batch → 写 daily → 后续 Agent |
| 已有 `data/daily/{date}.json` 与报告 | 跳过抓取，只补缺失产物 |

**禁止**在未验证 `data/daily/{date}.json` 存在时，假设“用户说抓取完=数据已在磁盘”。

### 推荐 Todo 清单（全量日）

```
1. 清理旧 batch + 浏览器预授权（固定 cwd）
2. Source A/B 列表 + 合并去重/公益站/32h → crawl_queue + batch_ids
3. 全量逐帖抓取正文（每批立即保存）
4. 合并 daily JSON + 正文二次过滤 + Topic/Trend
5. Writer 日报 + 概念候选入库
6. Press Writer + PDF Builder
```

## ⚡ 权限预授权（必须最先执行，一次性完成）

**开始抓取前，必须一次性授权所有 Playwright MCP 工具**，避免中途反复弹出授权窗口。

### 预授权步骤（按顺序执行，用户只需点击"允许"一次）

```
步骤 1: pkill -f "mcp-chrome" 2>/dev/null; sleep 2
步骤 2: browser_navigate → https://linux.do
步骤 3: browser_wait_for → time: 15（等待 Cloudflare 加载）
步骤 4: browser_snapshot → 查看页面结构
步骤 5: 如果标题仍为 "Just a moment..."，用 browser_click 点击验证区域（通常是 ref=e6 或 e5）
步骤 6: browser_evaluate → () => document.title（确认标题变为 "LINUX DO"）
```

**⚠️ Cloudflare 点击绕过（v14 新增）**：
2026-07-05 实测发现，Cloudflare Turnstile 挑战页需要**点击验证区域**才能通过，仅等待 15 秒不够。
- `browser_snapshot` 后找到 `main` 内的 `generic` 元素（通常是 `e6`）
- 用 `browser_click(target="e6")` 点击，页面标题会立即变为 "LINUX DO - 新的理想型社区"
- 如果一次点击未通过，再等 15 秒后重试点击

### 需要预授权的工具清单

| 工具 | 用途 | 必须 |
|------|------|------|
| `browser_navigate` | 页面导航（列表页、帖子页） | ✅ |
| `browser_run_code_unsafe` | 执行 JS（滚动加载列表页） | ✅ |
| `browser_evaluate` | 执行 JS 表达式（提取帖子数据） | ✅ |
| `browser_wait_for` | 等待加载（Cloudflare 挑战页） | ✅ |
| `browser_snapshot` | 页面快照 | 可选 |
| `browser_take_screenshot` | 截图 | 可选 |

> **不需要登录态**：匿名访问即可获取公开帖子数据。

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
- **"过滤后全部抓取完"** / `MMDD linuxdo日报 过滤后全部抓取完` → **全量模式冷启动**（见上方协议）

### 周报模式
当用户说以下关键词时激活：
- "周报"、"AI周报"、"技术周报"
- "weekly"、"出周报"
- "本周AI新闻"、"一周总结"

### 月报模式
当用户说以下关键词时激活：
- "月报"、"AI月报"、"技术月报"
- "linuxdo月报"、"monthly"、"出月报"
- "本月AI新闻"、"月度总结"

**指定月份**（可选）：
- "月报 2026-05" / "2026年5月月报" — 生成指定月份的月报
- "上月月报" — 生成上一个自然月的月报
- 不指定时默认生成**上一个自然月**的月报（若当月已结束则也可生成当月）

## 模式对比

| 维度 | 日报 | 周报 | 月报 |
|------|------|------|------|
| 时间范围 | 当前往前 32h | 上周一~上周日 | 指定月份（默认上月）1日~月末 |
| 数据来源 | 实时抓取双源 | 聚合当周日报 | **聚合当月已抓取数据 + 已生成日报** |
| 是否抓取 | ✅ 必须抓取 | 可复用日报数据 | ❌ 不重复抓取 |
| 历史去重 | 必须执行 | 按周累计 | 不去重（全量呈现） |
| 输出风格 | 今日亮点 + 新内容 | 本周总结 | **月度趋势总结 + 主题归纳 + 下月展望** |

## 目录结构

**数据输出目录**：`/Users/youngsdream/Documents/learn-claude-code/data/`（项目目录，非 skill 目录）

```
/Users/youngsdream/Documents/learn-claude-code/data/
├── daily/{date}.json          # 每日抓取原始数据（合并后）
├── posts/{id}.json            # 单帖详情（含 scrape_history）
├── reports/{date}.md          # 生成的 Markdown 日报
├── reports/{date}_press.md    # 生成的专业新闻稿
├── reports/{date}.pdf         # 生成的 PDF 日报
├── reports/{date}.typ         # Typst 源文件
├── weekly/{week}.md           # 周报 Markdown
├── weekly/{week}_press.md     # 周报新闻稿
├── weekly/{week}.pdf          # 周报 PDF
├── monthly/{YYYY-MM}.md       # 月报 Markdown
├── monthly/{YYYY-MM}_press.md # 月报新闻稿
├── monthly/{YYYY-MM}.pdf      # 月报 PDF
├── monthly/{YYYY-MM}.typ      # 月报 Typst 源文件
├── source_a.json              # Source A 帖子列表
├── source_b.json              # Source B 帖子列表（AI过滤后）
├── merged_ids.json            # 合并后的帖子ID列表
└── batch_browser_N.json       # 浏览器抓取的帖子数据批次
```

## 过滤规则

### 公益站过滤（日报模式必须执行）

以下帖子在生成日报时**必须过滤掉**，不纳入统计和报告：

**关键词过滤**（标题、标签、内容中出现以下任一即过滤）：
- 公益站、公益推广、LDC、ldc、cdk
- 签到、白嫖、薅羊毛、薅秃
- 充值额度、兑换码、免费额度
- 号池、号商、共享号
- 中转站、高级推广、抽奖、富可敌国

**意图过滤**（帖子主要内容为以下类型即过滤）：
- 分享免费 API 额度/Key 的帖子
- 公益站注册/使用教程
- 公益站运维公告（关站、维护、升级等）
- 薅羊毛攻略
- **纯交易帖（v15）**：求号/出号/共享车/代充/接码且无行业分析价值 → 过滤
- 标题命中「接码」「号商」「代充」且无风控/行业讨论价值 → 过滤

**说明（v15）**：账号风控/封号潮**不默认删除**（仍有信息价值），但 Writer **降权**，不得霸榜亮点。

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

### 32小时范围筛选（日报模式必须执行）

帖子必须在 32 小时范围内才纳入日报。

**时间窗口**：当前时间往前 32 小时（例如：当前 09:41，则窗口为 06-19 01:41 ~ 06-20 09:41）

**注意**：Discourse ID 不按日期顺序（跨分类），**不能用 ID 阈值判断日期**。必须通过帖子页面获取 `created_at`。

---

## Agent 1: Crawler（抓取器）

**职责**：从两个数据源抓取帖子，获取时间戳筛选32h范围，检查历史记录，批量抓取正文。

### ⚠️ 核心经验：浏览器 fetch API 会触发 429

**2026-06-21 实测结论**：
- `browser_evaluate` + `fetch('/t/{id}.json')` 会被 linux.do 429 限流
- 即使间隔 1.5 秒，批量 50 帖也会触发 429
- **必须使用浏览器逐帖浏览方式**：`browser_navigate` 打开帖子页面 → 提取 DOM 数据

### 1.1 打开列表页

使用 Playwright MCP `browser_navigate` 依次打开：
- Source A: `https://linux.do/tag/444-tag/444`
- Source B: `https://linux.do/c/news/34`

**Cloudflare 处理**：如果页面标题包含 "Just a moment"，使用 `browser_wait_for → time: 15` 等待自动通过。

### 1.2 滚动加载全部帖子

打开列表页后，使用 `browser_run_code_unsafe` 滚动加载。**采用递增滚动策略**，每轮后检查数量：

| 轮次 | 滻动次数 | 间隔 | 预期加载量 |
|------|---------|------|-----------|
| 第 1 轮 | 15 次 | 2.5s | ~450 帖 |
| 第 2 轮 | 10 次 | 2.5s | ~750 帖 |
| 第 3 轮 | 5 次 | 2.5s | ~900 帖 |
| 第 4 轮（可选） | 5 次 | 2.5s | ~1050 帖 |

```js
async (page) => {
  for (let i = 0; i < 15; i++) {
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(2500);
    const title = await page.title();
    if (title.includes('Just a moment') || title.includes('Checking')) {
      await page.waitForTimeout(15000);
    }
  }
  const count = await page.evaluate(() => document.querySelectorAll('tr.topic-list-item').length);
  return `scrolled 15 times, found ${count} posts`;
}
```

**终止条件**：每轮滚动后检查数量，如果 < 400 则追加一轮。通常 35 次滚动（3 轮）可加载 1000+ 帖，足够日报使用。

### 1.3 提取帖子列表（含时间戳）并保存

> **v11 优化**：时间戳提取合并到此步骤，无需单独提取。从 `td.activity[title]` 一次提取完成。

使用 `browser_evaluate` 的 `filename` 参数直接保存帖子列表到文件：

```js
// Source A: 保存全部帖子（含时间戳）
browser_evaluate(filename="data/source_a.json", function=() => {
  const rows = document.querySelectorAll('tr.topic-list-item');
  const posts = [];
  rows.forEach(row => {
    const topicId = row.getAttribute('data-topic-id');
    const titleLink = row.querySelector('.main-link a.title') || row.querySelector('a.title');
    const title = titleLink ? titleLink.textContent.trim() : '';
    const views = row.querySelector('.views .number')?.textContent?.trim() || '0';
    const replies = row.querySelector('.posts .number')?.textContent?.trim() || '0';
    const tags = Array.from(row.querySelectorAll('.discourse-tag')).map(t => t.textContent.trim());
    const activityCell = row.querySelector('td.activity');
    const titleAttr = activityCell?.getAttribute('title') || '';
    const createdMatch = titleAttr.match(/Created:\s*(.+?)(?:\n|$)/);
    const created = createdMatch ? createdMatch[1].trim() : '';
    posts.push({ id: topicId, title, views, replies, tags, created });
  });
  return JSON.stringify({ source: 'A', count: posts.length, ids: posts.map(p => p.id), posts });
})

// Source B: 保存 AI 标签过滤后的帖子（含时间戳）
browser_evaluate(filename="data/source_b.json", function=() => {
  const rows = document.querySelectorAll('tr.topic-list-item');
  const aiPosts = [];
  rows.forEach(row => {
    const topicId = row.getAttribute('data-topic-id');
    const titleLink = row.querySelector('.main-link a.title') || row.querySelector('a.title');
    const title = titleLink ? titleLink.textContent.trim() : '';
    const views = row.querySelector('.views .number')?.textContent?.trim() || '0';
    const replies = row.querySelector('.posts .number')?.textContent?.trim() || '0';
    const tags = Array.from(row.querySelectorAll('.discourse-tag')).map(t => t.textContent.trim());
    const activityCell = row.querySelector('td.activity');
    const titleAttr = activityCell?.getAttribute('title') || '';
    const createdMatch = titleAttr.match(/Created:\s*(.+?)(?:\n|$)/);
    const created = createdMatch ? createdMatch[1].trim() : '';
    if (tags.some(t => /人工智能|ai/i.test(t))) {
      aiPosts.push({ id: topicId, title, views, replies, tags, created });
    }
  });
  return JSON.stringify({ source: 'B', total: rows.length, aiFiltered: aiPosts.length, ids: aiPosts.map(p => p.id), posts: aiPosts });
})
```

时间戳格式为 `"Jun 22, 2026 9:53 pm"`，后续用 `dateutil.parser.parse()` 解析。

### 1.4 合并两源 ID 列表

```python
import json
with open('data/source_a.json') as f:
    src_a = json.loads(json.load(f))
with open('data/source_b.json') as f:
    src_b = json.loads(json.load(f))

ids_a = set(src_a['ids'])
ids_b = set(src_b['ids'])
merged = list(ids_a | ids_b)

with open('data/merged_ids.json', 'w') as f:
    json.dump(merged, f)
print(f'Source A: {len(ids_a)}, Source B: {len(ids_b)}, Merged: {len(merged)}')
```

### 1.5 历史去重

```python
import re, os
prev_ids = set()
for f in os.listdir('data/reports'):
    if f.endswith('.md'):
        with open(f'data/reports/{f}') as fh:
            ids = re.findall(r'\[(\d{7,})\]', fh.read())
            prev_ids.update(ids)

with open('data/merged_ids.json') as f:
    all_ids = json.load(f)
new_ids = [pid for pid in all_ids if pid not in prev_ids]
with open('data/merged_ids.json', 'w') as f:
    json.dump(new_ids, f)
print(f'历史去重: {len(all_ids)} → {len(new_ids)}')
```

### 1.6 时间戳解析与 32h 筛选 + 写 crawl_queue（v15.2）

> **v11 变更**：时间戳已在步骤 1.3 中从列表页 `td.activity[title]` 提取，此步骤仅做解析和筛选。  
> **v15.2**：筛选结果写入 `data/crawl_queue.json`，并切分为 `data/batch_ids_{N}.json`（每批 30 id），**禁止**只 merge id 不写 queue。

**⚠️ 常识提醒**：帖子页面没有 `<time>` 元素！`document.querySelector('time')` 返回空。时间只能从列表页提取。

```python
import json, re, os
from dateutil import parser as dateparser
from datetime import datetime, timezone, timedelta

# 假定 posts 已是：两源合并 + 历史去重 + 标题/标签公益站过滤后的 dict 或 list
now = datetime.now(timezone(timedelta(hours=8)))
cutoff = now - timedelta(hours=32)
date_str = now.strftime('%Y-%m-%d')

def views_num(p):
    return int(re.sub(r'\D', '', str(p.get('views', '0'))) or 0)

final = []
for p in posts:  # list of post dicts with id/title/views/tags/created
    created_str = p.get('created', '')
    if not created_str:
        continue
    try:
        created_dt = dateparser.parse(created_str)
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone(timedelta(hours=8)))
        if created_dt >= cutoff:
            p = dict(p)
            p['id'] = str(p['id'])
            p['created_at'] = created_dt.isoformat()
            final.append(p)
    except Exception:
        pass

final.sort(key=views_num, reverse=True)
os.makedirs('data', exist_ok=True)
with open('data/merged_ids.json', 'w') as f:
    json.dump([p['id'] for p in final], f)
with open('data/crawl_queue.json', 'w') as f:
    json.dump({'date': date_str, 'total': len(final), 'cutoff': cutoff.isoformat(), 'posts': final},
              f, ensure_ascii=False, indent=2)
for i in range(0, len(final), 30):
    n = i // 30
    with open(f'data/batch_ids_{n}.json', 'w') as f:
        json.dump([p['id'] for p in final[i:i+30]], f)
print(f'32h 筛选: {len(final)} 帖 → batches 0-{(len(final)-1)//30}')
```

### 1.7 逐帖浏览器浏览（核心抓取方案）

**必须使用此方案**，浏览器 fetch API 会被 429 限流。

#### ⚡ 提前终止 vs 全量（v15.2 澄清）

| 模式 | 条件 | 行为 |
|------|------|------|
| **标准** | 用户只说「日报」 | 按浏览量优先抓 4–5 批（120–150 帖）后可生成 |
| **全量** | 用户说「全部抓取」「过滤后全部抓取完」 | **必须**跑完 `crawl_queue` 全部批次（0717 实测约 18 批 / 517 帖） |

全量时不要在 150 帖提前停；Todo 标进度 `valid/total`。

#### 抓取流程

1. **打开列表页**：`browser_navigate → https://linux.do/tag/444-tag/444`
2. **滚动加载全部帖子**：见步骤 1.2（35 次滚动）
3. **提取帖子列表含时间戳**：`browser_evaluate`（见步骤 1.3，**绝对路径 filename**）
4. **合并去重筛选**：历史去重 + 公益站过滤 + 32h 筛选 → **crawl_queue + batch_ids**
5. **按浏览量排序**：已在 queue 内完成
6. **批量抓取正文**：每批 30 帖，从 `batch_ids_N.json` 读 id

#### 每帖提取数据

```js
// browser_evaluate 提取帖子数据
() => {
  const title = document.querySelector('.fancy-title')?.textContent?.trim() || '';
  const cooked = document.querySelector('.topic-post .cooked');
  const content = cooked ? cooked.textContent.trim().substring(0, 500) : '';
  const views = document.querySelector('.views .number')?.textContent?.trim() || '0';
  const tags = Array.from(document.querySelectorAll('.discourse-tag')).map(t => t.textContent.trim());
  return { title, content, views, tags };
}
```

**注意**：不要用 `document.querySelector('time')` 获取时间，帖子页面没有 `<time>` 元素！时间从列表页的 `td.activity[title]` 提取。

#### 批量抓取代码（每批 30 帖，不回列表页）

```js
async (page) => {
  const ids = ["ID1", "ID2", /* ... 30个ID */];
  const results = [];
  for (let i = 0; i < ids.length; i++) {
    const tid = ids[i];
    try {
      await page.goto('https://linux.do/t/topic/' + tid, { waitUntil: 'domcontentloaded', timeout: 20000 });
      await page.waitForTimeout(2000);
      let pgTitle = await page.title();
      // Cloudflare 检测
      if (pgTitle.includes('Just a moment') || pgTitle.includes('Checking')) await page.waitForTimeout(15000);
      // 官方警告检测（v12 新增）
      const pageContent = await page.evaluate(() => document.body.innerText);
      if (pageContent.includes('异常的自动化访问行为') || pageContent.includes('系统检测到')) {
        return JSON.stringify({ batch: N, count: results.length, results, stopped: 'official_warning' });
      }
      const data = await page.evaluate(() => {
        const title = document.querySelector('.fancy-title')?.textContent?.trim() || '';
        const cooked = document.querySelector('.topic-post .cooked');
        const content = cooked ? cooked.textContent.trim().substring(0, 500) : '';
        const views = document.querySelector('.views .number')?.textContent?.trim() || '0';
        const tags = Array.from(document.querySelectorAll('.discourse-tag')).map(t => t.textContent.trim());
        return { title, content, views, tags };
      });
      results.push({ id: tid, ...data });
      await page.waitForTimeout(1500);
    } catch (e) {
      results.push({ id: tid, error: String(e).substring(0, 100) });
    }
  }
  return JSON.stringify({ batch: N, count: results.length, results });
}
```

#### ⚠️ 批量抓取数据保存（v12 核心 + v15.2 transcript 回填）

**2026-06-29 实测问题**：浏览器 `browser_run_code_unsafe` 返回的 JSON 结果必须**立即保存到文件**，否则数据会丢失。

**正确流程**：
1. `browser_run_code_unsafe` 执行批量抓取 → 返回 JSON 字符串
2. **立即**保存到 `data/batch_browser_N.json`
3. 继续下一批

**错误做法**：等所有批次抓完再保存（数据会丢失）

```python
# 理想情况：工具返回字符串可直接 loads
import json
data = json.loads(results_json)  # 若外层仍是转义字符串，再 loads 一次
with open(f'data/batch_browser_{N}.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'Batch {N} 已保存: {len(data.get("results", []))} 帖, valid={sum(1 for r in data["results"] if r.get("title"))}')
```

#### ⚠️ 大结果无法直接管道时：从 session transcript 回填（v15.2）

当返回体极大、无法在下一步 Bash 里手工粘贴时，**不要重爬该批**。从当前 session 的 jsonl 解析最近一次 `### Result\n"{...}"`：

```python
# 思路：读 ~/.claude/projects/.../<session>.jsonl
# 找含 ### Result 且 "batch":N 的 tool 结果文本
# start = text.find('### Result\n"') + len('### Result\n"')
# end = text.find('"\n###', start)
# unescaped = json.loads('"' + text[start:end] + '"')
# data = json.loads(unescaped)
# 写入 data/batch_browser_{N}.json
```

建议在项目里保留可复用脚本 `data/save_latest_batch.py`（参数为 batch 号），每批结束后：

```bash
python3 data/save_latest_batch.py N
```

#### 空帖检测（v12 新增）

抓取过程中会遇到大量**已删除或私有帖子**（返回空标题/空内容）。这些帖子不需要保存。

```python
# 过滤空帖
valid_posts = [p for p in results if p.get('title')]
deleted_count = len(results) - len(valid_posts)
if deleted_count > 0:
    print(f'跳过 {deleted_count} 个已删除/私有帖子')
```

#### 速度优化

- **每批 10–15 帖优先（v15.5）**：全量日长批（30）易触发 MCP 静默超时；稳定优先用 15，失败多时降到 10
- **每帖等待 2 秒**：帖子页加载后等待 2 秒再提取
- **帖间等待 1.5 秒**：避免触发限流（不回列表页，直接导航下一帖）
- **超时 20 秒**：单帖加载超时 20 秒则记 `error`，不中断整批

#### ⚠️ 批抓稳定性（v15.5 / 2026-07-20 实测）

**1) MCP 长静默超时**

`browser_run_code_unsafe` 一批跑很久无 progress 时，可能被 abort（实测约 **2491s**）：
> `MCP server "playwright" tool "browser_run_code_unsafe" sent no response or progress for 2491s; aborting`

**处理**：
- 优先 **缩小批次**（15 → 10），不要硬等超时
- 若可改 MCP 配置：为 playwright 设更大 per-server `timeout`（ms）
- 超时后：**不要当成功**；检查是否已有 partial 结果可回填；否则重跑该批

**2) `net::ERR_ABORTED` 批量失败**

`page.goto` 连续 `ERR_ABORTED` 时浏览器会话多半已坏。

**处理**：
1. 立即把本批结果落盘（含 `error` 项）
2. `pkill -f "mcp-chrome"` → `sleep 2` → `browser_navigate https://linux.do` 重建会话
3. 失败 id 写入 `data/rem_batch_*.json` 或单独 `batch_browser_retryN.json`
4. 重试成功后再并入 daily；**禁止**把全 error 批当 valid

**3) batch 文件污染**

旧 session / 错 cwd / 回填脚本把 **别日或非本批** 内容写入 `batch_browser_0.json` 等。

**合并前必须校验**每个 batch：
```python
import json, glob
for f in sorted(glob.glob('data/batch_browser_*.json')):
    d = json.load(open(f))
    results = d.get('results', d if isinstance(d, list) else [])
    if not results:
        print('EMPTY', f); continue
    # 本批应含 title 或 error；全空 / 结构不对则删除重抓
    ok = sum(1 for r in results if r.get('title') or r.get('error'))
    print(f, 'n=', len(results), 'okish=', ok)
```
污染文件：**删除** → 重算剩余 queue → 只抓缺失 id。

**4) 重试批命名**

`batch_browser_retry1.json` 等 **非纯数字** 批号合法。`save_latest_batch.py` 解析 batch 号时勿 `int()` 强制数字文件名；合并用 `glob('data/batch_browser_*.json')`。

**5) 中断 / 工具丢失后续跑**

用户 interrupt 或会话只剩部分工具时：
1. 先 `ls data/batch_browser_*.json` + 是否已有 `data/daily/{date}.json`
2. 有 batch 无 daily → **只合并 + Writer**，不冷启动清 queue
3. 有 daily+pdf → 直接交 ai-news-factory
4. **禁止**在工具不全时重写「手动 bash 教程」假装完成；恢复 MCP/Bash 后再跑

### 1.7 数据保存

每批抓取完成后，**必须立即**使用 Python 保存到文件（v12 强调：延迟保存会导致数据丢失）：

```python
import json
# results_json 是 browser_run_code_unsafe 返回的字符串
data = json.loads(results_json)
with open(f'data/batch_browser_{N}.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'Batch {N} 已保存: {data.get("count", 0)} 帖')
```

### 1.8 数据合并与过滤（v15.2：正文二次过滤 + 列表 views 合并）

> **v12 重要修复**：`browser_evaluate` 使用 `filename` 参数保存的 JSON 文件是 **double-encoded**，需要用 `json.loads(json.load(f))` 读取。  
> **v15.2**：列表阶段公益站过滤不够（正文才暴露「公益推广/CDK/日抛」）→ **合并 batch 后再滤一次**；帖子页 `views` 常为 `0` → **与 crawl_queue 列表 views 取更合理值**。

```python
import json, os, glob, re
from datetime import datetime, timezone, timedelta

queue = json.load(open('data/crawl_queue.json'))
meta = {str(p['id']): p for p in queue['posts']}

all_posts = {}
for f in sorted(glob.glob('data/batch_browser_*.json')):
    with open(f) as fh:
        batch = json.load(fh)
    if isinstance(batch, str):
        batch = json.loads(batch)
    for p in batch.get('results', []):
        pid = str(p.get('id', ''))
        if not (pid and p.get('title')):
            continue
        m = meta.get(pid, {})
        if m.get('created'):
            p['created'] = m['created']
        if m.get('created_at'):
            p['created_at'] = m['created_at']
        # 列表页 views 优先于帖子页 0/异常
        def vn(x):
            return int(re.sub(r'\D', '', str(x or '0')) or 0)
        if vn(p.get('views')) == 0 and vn(m.get('views')) > 0:
            p['views'] = m.get('views')
        elif vn(m.get('views')) > vn(p.get('views')):
            p['views'] = m.get('views')
        p['tags'] = list(dict.fromkeys((p.get('tags') or []) + (m.get('tags') or [])))
        p['id'] = pid
        all_posts[pid] = p

print(f'合并后有效帖子: {len(all_posts)}')

GONGYI_KEYWORDS = [
    '公益站', '公益推广', 'LDC', 'ldc', 'cdk', '签到', '白嫖',
    '薅羊毛', '薅秃', '兑换码', '免费额度', '号池', '号商', '充值额度',
    '中转站', '高级推广', '抽奖', '富可敌国', '接码', '代充',
    # v15.2 正文二次过滤补充
    'LightBridge公益', 'YSX666', '日抛', '午夜福利', 'CDK',
]
TRADE = ['求号', '出号', '共享车']

filtered = {}
removed = 0
for pid, p in all_posts.items():
    title = p.get('title', '') or ''
    tags = ' '.join(p.get('tags') or [])
    content = (p.get('content') or '')[:200]
    all_text = f'{title} {tags} {content}'
    if any(kw in all_text for kw in GONGYI_KEYWORDS):
        removed += 1
        continue
    if any(kw in title for kw in TRADE) and not any(x in title for x in ['风控', '封号', '行业', '分析', '讨论']):
        removed += 1
        continue
    filtered[pid] = p

print(f'公益站/交易二次过滤后: {len(filtered)} (removed {removed})')

date_str = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')
os.makedirs('data/daily', exist_ok=True)
posts_list = sorted(filtered.values(),
                    key=lambda p: int(re.sub(r'\D', '', str(p.get('views', '0'))) or 0),
                    reverse=True)
daily_data = {
    'date': date_str,
    'total': len(posts_list),
    'with_content': sum(1 for p in posts_list if p.get('content')),
    'cutoff': queue.get('cutoff'),
    'posts': posts_list,
}
with open(f'data/daily/{date_str}.json', 'w') as f:
    json.dump(daily_data, f, ensure_ascii=False, indent=2)
print(f'saved data/daily/{date_str}.json total={daily_data["total"]}')
```

---

## Agent 2: Topic Merger（主题合并器）

**职责**：合并两个数据源的帖子，去重，过滤公益站，按主题聚类。

### 主题分类规则

按以下维度对帖子进行分组（按优先级匹配，命中第一个即归类）：
- **OpenAI/ChatGPT/Codex 生态**：codex, chatgpt, gpt, openai, sub2api, plus, pro20, pro 5x, sol, terra, luna, tibo, gpt-red
- **Claude/Anthropic 生态**：fable, mythos, opus, anthropic, claude code, claudecode, cc-switch, max, ultracode
- **Kimi/月之暗面**：kimi, 月之暗面, moonshot, k3, kivine, kivio
- **Grok/xAI 生态**：grok, xai, spacexai, supergrok, 马圣, 老马
- **豆包/火山引擎 生态**：豆包, doubao, seed, 火山, seedance, 字节, qoder
- **GLM/智谱 生态**：glm, 智谱, zai, glm5.2, codegeex
- **Google/Gemini 生态**：gemini, google, antigravity, spark, ai studio, pixel
- **DeepSeek 生态**：deepseek, ds, v4（注意与通用英文词区分，优先标题/标签）
- **AI 编程工具**：cursor, windsurf, trae, hermes, opencode, kiro, minimax, copilot
- **开源项目**：开源推广, 开源
- **行业动态**：前沿快讯, 前沿, 转载, 安全, 边界, waic, nvidia, h200, 监管, linus
- **其他话题**：其余

---

## Agent 3: Trend Analyzer（趋势分析器）

**职责**：分析帖子内容和热度，生成今日技术趋势。

### 分析维度

- **热度分析**：浏览量、回复数、点赞数最高的帖子
- **内容分析**：帖子正文中反复出现的技术关键词
- **时间线**：今日新出现的话题 vs 持续讨论的话题
- **争议性**：回复数/浏览比最高的帖子（讨论最激烈）
- **可信度提示（v15）**：对关键话题尽量给 `source_hint`（能判则判，不能判标未确认）：
  - 含官网 / 官方 blog / 官方公告 / 官方 X → `官方确认`
  - 含主流媒体报道 → `媒体报道`
  - 含可复现实测 / 截图实测 → `社区实测`
  - 仅模型列表 / changelog / 源码字符串 → `源码迹象`
  - 含网传 / 疑似 / 爆料 / 猜测 → `未确认传闻`

---

## Agent 4: Writer（日报撰写器）

**职责**：读取合并数据和趋势分析，生成完整的 Markdown 日报。

### 🔴 技术锚点（v15.0.0 · ai-concept-bank）

Writer **应**在日报中点出技术概念，供下游 ai-news-factory Step 1.6 匹配；**不**在报告里写完整 15s 口播。

1. **读库**（可选但推荐）：`ai-concept-bank/concepts.json`  
   - 仅使用 `status=ready` 且 `script_meta.authored_by=ai-concept-narrator` 且 `reviewed=true` 的条目做「技术锚点」字段  
   - 用帖子标题+摘要匹配 `news_keywords` / `aliases` / `name`  
2. **条目可增字段**（有命中时写；无命中可省略）：
   - `技术锚点：{concept name} — {one_liner}`  
   - 不得把 `script_15s` 全文贴进日报（口播留给视频 Phase 2）  
3. **禁止**：主会话手写与库冲突的长定义；库无命中时可用半句中性说明，或省略  
4. **候选发现**（不阻断成稿）：正文出现库中没有的黑话 → 在日报末可选附录 `## 概念候选（供 concept-bank）` 列 1–5 个词，供周维护晋升  

> 完整 15s 台词、usage-log 由 **ai-news-factory** 与 **ai-concept-narrator** 负责，Writer 不写 usage-log。

### 日报结构

```markdown
# linux.do 人工智能 技术日报
**{date}** | 数据来源：linux.do #人工智能 + 前沿快讯

## 今日亮点
1. [{可信度五档之一}] {一句话事实} — 影响：{一句}（浏览 X）
2. ...
（3–5 条；优先模型发布/开源/安全/开发者工具/政策/可引用数据；
 权益/封号/低价渠道 **不得占亮点 50% 以上**）

## 新内容

### {主题分组名}
- **{中性重写标题}** — {事实摘要 1–2 句}
  - 可信度：{官方确认 | 媒体报道 | 社区实测 | 源码迹象 | 未确认传闻}
  - 影响：{对用户/开发者/行业，一句}
  - 技术锚点：{可选} {ready name} — {one_liner}
  - 信号：浏览 X · 争议度{高/中/低}

（按主题分组，每组 3-10 个帖子；低价值权益帖可短摘要或合并）

## 数据概览
| 标签 | 帖数 |
|------|------|

## 概念候选（供 concept-bank，可选）
- {新黑话1} — 出现在：{帖标题}
```

### Writer 风格硬规则（v15）

1. **禁止原样转发**含：震惊、牛逼、已急哭、铁证、炸了、大瓜、彻底炸锅 等 → 必须中性重写  
2. **摘要**须回答「发生了什么 + 为何值得记」，禁止只截帖子首句情绪句  
3. **可信度必填**（五档枚举，禁止自创）；`未确认传闻` 不得写成已官宣事实  
4. **技术锚点**：架构/评测/安全/Agent/定价机制尽量给 1 句（来自 concept-bank ready 的 one_liner）；纯融资可省略  
5. **亮点选择**：硬新闻优先；封号潮重复、低价区、未确认灰度第 N 次、纯情绪帖降权  
6. 数据来源说明可加：「条目含可信度分层，未确认信息不作为定论」

### 🟡 概念候选受控入库（v15.1.0 · 可选但推荐）

**执行时机**：日报 Markdown 写入完成后、Press Writer / PDF Builder 启动前。
**目标**：减少人工搬运，但只把合格新词追加为最小 `candidate`；不生产口播、不晋升 `draft/ready`、不写 `usage-log`。

#### 1. 读取候选来源

仅从本期日报 Markdown 的附录读取：

```markdown
## 概念候选（供 concept-bank）
- **候选名** — 出现在：...
```

若日报没有该附录，或附录为空，跳过本步骤，不阻断 Press / PDF。

#### 2. 读取概念库与频次表

必须读取：

```text
ai-concept-bank/concepts.json
```

可选读取（用于长期价值参考，不要求每天重跑）：

```text
ai-concept-bank/extracts/term-frequency.json
```

月度维护时由 `ai-concept-bank/scripts/extract-term-frequency.py` 刷新长期频次；日报候选只负责发现新词。

#### 3. 去重规则（任一命中即跳过新增）

候选必须与 `concepts.json` 中已有条目的以下字段去重：

- `id`
- `name`
- `aliases`
- `news_keywords`

去重时应同时检查中英文、大小写、空格、连字符和常见缩写。若候选更像已有概念的新说法，优先记录为后续 `aliases` / `angles.available` 的维护建议，不新建概念。

#### 4. 过滤规则（任一命中即跳过）

- 营销词、标题党词、社区情绪词。
- 公司名、产品名、模型型号或单次事件名。
- 账号权益、低价渠道、封号套利、号池、兑换码等权益黑话。
- `可信度=未确认传闻` 且缺少可复核技术含义。
- 只能描述当天个案、无法形成稳定定义的说法。
- 不能在约 15 秒内讲清一个核心点的复杂混合表达。
- 与已有 ready/candidate 概念高度重叠，但更适合作为新角度。

#### 5. 追加最小 candidate

通过去重与过滤后，只能追加最小 `candidate`，字段模板：

```json
{
  "id": "snake_case_id",
  "name": "候选名",
  "aliases": [],
  "category": "待定",
  "tier": 3,
  "difficulty": "待定",
  "status": "candidate",
  "one_liner": "",
  "analogy": "",
  "script_15s": "",
  "script_60s": null,
  "script_meta": {
    "authored_by": "ai-concept-narrator",
    "authored_at": null,
    "reviewed": false,
    "angle": null
  },
  "news_keywords": ["候选名"],
  "corpus": null,
  "angles": {
    "available": ["基础定义"],
    "used": []
  },
  "related_events": [],
  "sources": ["data/reports/{YYYY-MM-DD}.md#概念候选"],
  "last_used": null,
  "use_count": 0
}
```

若候选可匹配 `term-frequency.json` 的 `normalized_id`，可复制精简 `corpus`：

```json
{
  "count_total": 0,
  "count_scripts": 0,
  "count_reports": 0,
  "top_paths": []
}
```

否则保持 `corpus: null`，等待月度 term-frequency 验证长期价值。

#### 6. 写入后校验

写入 `concepts.json` 后必须执行：

```bash
jq empty ai-concept-bank/concepts.json
```

并人工确认：

- 新增条目 `status == "candidate"`。
- `script_15s == ""`。
- `script_meta.reviewed == false`。
- 未修改 `usage-log.json`。
- 未改动已有 ready 概念的口播和状态。

#### 7. 禁止事项

- 禁止自动调用 `ai-concept-narrator`。
- 禁止自动设 `reviewed=true`。
- 禁止自动晋升 `draft` 或 `ready`。
- 禁止写入 `usage-log.json`。
- 禁止覆盖已有概念、删除历史字段或改 `last_used/use_count`。
- 禁止静默 git commit 子模块。

> 职责边界：日报候选负责发现新词；`term-frequency` 负责验证长期价值；概念库维护 Agent 决定后续 `candidate → draft → ready`。

---

## Agent 5: Press Writer（新闻稿撰写器）

**职责**：基于日报内容，生成专业 AI 科技新闻稿。

### 新闻稿结构

```markdown
# {标题}

{导语 — 一句话概括核心事件}

## 正文

{2-4 段深度报道}

## 社区反应

{精选 3-5 条有代表性的社区观点}

## 风险与争议

{潜在风险、争议点}
```

### 写作风格

- **对标媒体**：Bloomberg Tech、The Verge、TechCrunch
- **禁止**：论坛口语、emoji、感叹号堆砌、情绪夸张词（炸了/大瓜等）
- **数据优先**：每个论点必须有数据支撑
- **可信度（v15）**：每则核心事件标注五档之一；导语禁止情绪词；「风险与争议」区分已证实风险 vs 社区猜测
- **技术概念（v15）**：可引用 `ai-concept-bank` ready 的 `one_liner`；禁止自创与库冲突的长定义；完整口播归 narrator

---

## Agent 6: PDF Builder（PDF 生成器）

**职责**：将 Markdown 日报转换为 PDF 文件，使用 Typst 排版。

### Typst 模板

```typst
#set document(title: "linux.do AI 技术日报 - {date}")
#set page(paper: "a4", margin: (top: 2cm, bottom: 2cm, left: 2cm, right: 2cm))
#set text(font: ("PingFang SC", "Helvetica Neue", "Arial"), size: 10pt)
#set heading(numbering: none)
```

### ⚠️ Typst 特殊字符处理（v12 重点修复）

**2026-06-29 实测问题**：以下字符在 Typst 中有特殊含义，必须转义：

| 字符 | 用途 | 转义方式 | 示例 |
|------|------|---------|------|
| `$` | 数学模式 | `\$` | `\$50` 而非 `$50` |
| `#` | 标记符号 | `\#` | `\#人工智能` 而非 `#人工智能` |
| `*` | 斜体 | 用 `*text*` | 标题用斜体代替粗体 |
| `_` | 下标 | `\_` | `\_views` 而非 `_views` |

**Typst 不支持 `**bold**` 语法**，用 `*斜体*` 代替。

### 编译命令

```bash
typst compile data/reports/{date}.typ data/reports/{date}.pdf
```

---

## 周报模式（v14 新增完整流程）

周报**聚合当周已抓取的日报数据**，不重复抓取。基于 `data/daily/{YYYY-MM-DD}.json` 和 `data/reports/{YYYY-MM-DD}.json` 生成。

### 周报数据聚合

```python
import json, os, glob, re
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone(timedelta(hours=8)))
# 计算本周范围（周一~周日）
weekday = now.weekday()  # 0=Monday
week_start = (now - timedelta(days=weekday)).strftime('%Y-%m-%d')
week_end = now.strftime('%Y-%m-%d')
week_id = now.strftime('%Y-W%W')  # 如 "2026-W27"

# 聚合本周 daily JSON（注意只匹配 YYYY-MM-DD.json，排除 _sorted/_topics 等后缀文件）
week_posts = {}
covered_days = []
for f in sorted(glob.glob('data/daily/2026-*.json')):
    fname = os.path.basename(f).replace('.json', '')
    # 排除带后缀的文件（如 2026-06-30_sorted.json）
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', fname):
        continue
    if week_start <= fname <= week_end:
        try:
            with open(f) as fh:
                d = json.load(fh)
            posts = d.get('posts', [])
            covered_days.append(fname)
            for p in posts:
                pid = str(p.get('id', ''))
                if not (pid and p.get('title')):
                    continue
                # v15.4：同 id 保留更高浏览量；记下来源日
                def vn(x):
                    s = str(x or '0').strip().lower().replace(',', '')
                    m = re.match(r'([\d.]+)\s*([km万])?', s)
                    if not m:
                        return int(re.sub(r'\D', '', s) or 0)
                    n = float(m.group(1)); u = m.group(2)
                    if u == 'k': n *= 1000
                    elif u == 'm': n *= 1e6
                    elif u == '万': n *= 10000
                    return int(n)
                prev = week_posts.get(pid)
                if not prev or vn(p.get('views')) >= vn(prev.get('views')):
                    p = dict(p)
                    p['id'] = pid
                    p['_day'] = fname
                    week_posts[pid] = p
        except Exception:
            pass

# 扫描本周日报提取亮点
weekly_highlights = {}
for f in sorted(glob.glob('data/reports/2026-*.md')):
    fname = os.path.basename(f).replace('.md', '')
    if '_press' in fname:
        continue
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', fname):
        continue
    if week_start <= fname <= week_end:
        try:
            with open(f) as fh:
                content = fh.read()
            m = re.search(r'## (?:今日|本周)亮点\n+(.*?)(?=\n##|\Z)', content, re.S)
            if m:
                bullets = [b.strip() for b in m.group(1).strip().split('\n') if b.strip()]
                if bullets:
                    weekly_highlights[fname] = bullets
        except Exception:
            pass

os.makedirs('data/weekly', exist_ok=True)
week_data = {
    'week': week_id,
    'week_start': week_start,
    'week_end': week_end,
    'covered_days': covered_days,
    'total_topics': len(week_posts),
    'posts': list(week_posts.values()),
    'daily_highlights': weekly_highlights,
}
with open(f'data/weekly/{week_id}.json', 'w') as f:
    json.dump(week_data, f, ensure_ascii=False, indent=2)
print(f'week={week_id} days={covered_days} total={len(week_posts)}')
```

### 周报 TOP 排序注意（v15.4）

列表页 `views` 常为 **`6.2k` / `1.1万` 字符串**，TOP 排序必须用上面的 `vn()`（k/m/万）解析，**禁止** `int(re.sub(r'\D','', views))`（会把 `6.2k` 变成 `62` 或丢掉数量级）。

输出文件（建议齐全）：
- `data/weekly/{week_id}.json` / `.md` / `_press.md` / `.typ` / `.pdf`
- 可选：`{week_id}_topics.json`（主题分组计数 + hard-news TOP）

### 周报多 Agent 流程

周报**不抓取新数据**，6 个 Agent 职责调整：

| Agent | 日报职责 | 周报职责 |
|-------|---------|---------|
| Crawler | 抓取双源 | **聚合本周 daily JSON + 日报 MD** |
| Topic Merger | 合并去重 | 合并本周所有帖子按主题分类（每周 TOP 5） |
| Trend Analyzer | 今日趋势 | **跨日趋势归纳**（升温/降温/事件线） |
| Writer | 日报 MD | 周报 MD（含大事记 + 趋势 + 升温降温表） |
| Press Writer | 新闻稿 | 周度新闻稿 |
| PDF Builder | 日报 PDF | 周报 PDF |

**⚡ 并行优化（v14 新增）**：Topic Merger 和 Trend Analyzer 可以**并行启动**，两者数据独立无需等待。Writer 等两者完成后再启动。

### 周报 Markdown 模板（Writer Agent 专用）

```markdown
# linux.do 人工智能 技术周报
**{week_id}（{week_start} ~ {week_end}）** | 数据来源：linux.do #人工智能 + 前沿快讯

## 本周亮点
1. [{可信度}] {事实} — 影响：{一句}（浏览 X）
（5 条；硬新闻优先；中性标题）

## 本周大事记
- **{日期}** [{可信度}] {中性标题} — {一句}；影响：{一句}

## 本周热门主题 TOP 10
1. **{中性标题}** — 摘要（浏览 X | 日期）
   - 可信度：{五档}

## 主题趋势分析
### 趋势一：{趋势名}
（事实变化 → 谁受益/谁承压 → 下周观察；避免情绪复述）
- 可信度区间：{若案例多为传闻需写明}

## 主题分布
| 主题分组 | 帖数 | 占比 |

## 升温 vs 降温
| 升温话题 | 降温话题 |

## 下周展望
（2-3 句可验证观察点）

## 数据来源说明
- 数据时间范围：{week_start} ~ {week_end}
- 基于日报文件：{count} 份
- 公益站/中转站内容已过滤
- 条目含可信度分层，未确认信息不作为定论
```

---

## 月报模式（v13 新增）

月报**不重复抓取**，而是基于当月已抓取的日报数据（`data/daily/{YYYY-MM-DD}.json`）与已生成的日报 Markdown（`data/reports/{YYYY-MM-DD}.md`）聚合生成。若某日数据缺失，月报会标注缺失天数并继续生成。

### 月份解析

```python
import re
from datetime import datetime, timezone, timedelta

def parse_month(user_msg, now=None):
    """从用户消息解析目标月份，默认返回上一个自然月 (YYYY-MM)。"""
    now = now or datetime.now(timezone(timedelta(hours=8)))
    # 支持形如 "2026-05" / "2026年5月" / "2026-5"
    m = re.search(r'(20\d{2})\D{0,2}(\d{1,2})', user_msg)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    # "上月月报" → 上一个自然月
    first_of_this_month = now.replace(day=1)
    last_month = first_of_this_month - timedelta(days=1)
    return last_month.strftime('%Y-%m')
```

### 数据聚合逻辑

读取目标月份所有日报数据，合并帖子去重，并扫描日报 Markdown 提取亮点：

```python
import json, os, glob, re
from datetime import datetime, timedelta, timezone

month = parse_month(user_msg)  # 如 "2026-05"

# 1. 定位月内所有日期
year, mon = map(int, month.split('-'))
start = datetime(year, mon, 1, tzinfo=timezone(timedelta(hours=8)))
if mon == 12:
    end = datetime(year + 1, 1, 1, tzinfo=timezone(timedelta(hours=8)))
else:
    end = datetime(year, mon + 1, 1, tzinfo=timezone(timedelta(hours=8)))
total_days = (end - start).days

# 2. 聚合 daily JSON
month_posts = {}          # 帖子去重
covered_days = []         # 有日报数据的日期
missing_days = []
day_topic_counts = {}     # 每日主题数（用于活跃度趋势）

cur = start
while cur < end:
    date_str = cur.strftime('%Y-%m-%d')
    daily_path = f'data/daily/{date_str}.json'
    if os.path.exists(daily_path):
        try:
            with open(daily_path) as f:
                daily = json.load(f)
            posts = daily.get('posts', [])
            day_topic_counts[date_str] = len(posts)
            if posts:
                covered_days.append(date_str)
            for p in posts:
                pid = str(p.get('id', ''))
                if pid and p.get('title'):
                    month_posts[pid] = p
        except Exception:
            missing_days.append(date_str)
    else:
        missing_days.append(date_str)
    cur += timedelta(days=1)

# 3. 扫描日报 Markdown 提取每日亮点（用于月度趋势归纳）
daily_highlights = {}     # {date: [亮点句子]}
for md_path in sorted(glob.glob('data/reports/*.md')):
    fname = os.path.basename(md_path).replace('.md', '')
    if not fname.startswith(month):
        continue
    try:
        with open(md_path) as f:
            content = f.read()
    except Exception:
        continue
    # 提取 "今日亮点" / "本周亮点" 段落要点
    m = re.search(r'## (?:今日|本周)亮点\n+(.*?)(?=\n##|\Z)', content, re.S)
    if m:
        bullets = [b.strip('- ').strip() for b in m.group(1).strip().split('\n') if b.strip().startswith('-')]
        if bullets:
            daily_highlights[fname] = bullets

# 4. 公益站过滤（与日报一致，v12 规则复用）
GONGYI_KEYWORDS = ['公益站', '公益推广', 'LDC', 'ldc', 'cdk', '签到', '白嫖',
                   '薅羊毛', '薅秃', '兑换码', '免费额度', '号池', '号商', '充值额度',
                   '中转站', '高级推广', '抽奖', '富可敌国']
filtered_posts = {}
for pid, p in month_posts.items():
    all_text = f"{p.get('title', '')} {' '.join(p.get('tags', []))}"
    if not any(kw in all_text for kw in GONGYI_KEYWORDS):
        filtered_posts[pid] = p

# 5. 按浏览量排序取月度 TOP 10
top_posts = sorted(filtered_posts.values(),
                   key=lambda p: int(re.sub(r'\D', '', p.get('views', '0')) or 0),
                   reverse=True)[:10]

month_data = {
    'month': month,
    'total_days': total_days,
    'covered_days': covered_days,
    'missing_days': missing_days,
    'coverage': f'{len(covered_days)}/{total_days}',
    'total_topics': len(filtered_posts),
    'day_topic_counts': day_topic_counts,
    'daily_highlights': daily_highlights,
    'top_posts': top_posts,
}
os.makedirs('data/monthly', exist_ok=True)
with open(f'data/monthly/{month}.json', 'w') as f:
    json.dump(month_data, f, ensure_ascii=False, indent=2)
print(f'月报数据聚合: {month} 覆盖 {len(covered_days)}/{total_days} 天, '
      f'有效主题 {len(filtered_posts)} 个')
```

### 月报 Markdown 模板（Writer Agent 专用）

```markdown
# linux.do 人工智能 技术月报
**{YYYY-MM}** | 数据来源：当月日报聚合（{covered_days}/{total_days} 天）

## 本月概览
- 数据覆盖天数：{covered_days}/{total_days}
- 缺失天数：{missing_days}（如有）
- 月度主题总数：{total_topics}
- 最活跃讨论日：{most_active_day}（{peak_count} 个新主题）
- 日均新主题数：{avg_per_day}

## 本月热门主题 TOP 10
1. **{中性标题}** — 摘要（浏览 X | 回复 Y | 出现日期）
   - 可信度：{五档}
2. ...
（按月度浏览量降序；套利/渠道促销帖不得入选 TOP）

## 月度技术趋势
### 趋势一：{趋势名称}
- **热度变化**：本月讨论量 / 起止时间 / 周环比
- **关键驱动**：核心事件或发布
- **代表主题**：相关帖子链接
- **可信度区间**：{若案例多为传闻需写明}
- **影响**：谁受益 / 谁承压

### 趋势二 / 趋势三 …
（基于 daily_highlights 跨日归纳，不按天拼接）

## 主题分布
| 主题分组 | 帖数 | 占比 |
|---------|------|------|
| OpenAI/ChatGPT 生态 | ... | ... |
| Claude/Anthropic 生态 | ... | ... |
（复用 Agent 2 主题分类规则）

## 下月展望
基于本月趋势，预测下月可能关注的方向：
- 预测方向 1（依据：本月某趋势持续升温）
- 预测方向 2
- 预测方向 3

## 数据来源说明
- 数据时间范围：{YYYY-MM-01} ~ {YYYY-MM-末}
- 基于日报文件：{daily_count} 份
- 缺失日期：{missing_days}（如有，标注影响）
- 公益站/中转站内容已过滤
- 条目含可信度分层，未确认信息不作为定论
```

### 月报多 Agent 流程

月报模式下，**Crawler 不抓取新数据**，6 个 Agent 的职责调整：

| Agent | 日报职责 | 月报职责 |
|-------|---------|---------|
| Crawler | 抓取双源 | **读取当月 daily JSON + 日报 MD** |
| Topic Merger | 合并去重 | 合并当月所有帖子去重（不去重历史） |
| Trend Analyzer | 今日趋势 | **跨日趋势归纳**（基于 daily_highlights） |
| Writer | 日报 MD | 月报 MD（用月报模板） |
| Press Writer | 新闻稿 | 月度新闻稿 |
| PDF Builder | 日报 PDF | 月报 PDF（复用 Typst 模板，转义规则同 v12） |

### 月报 Typst 输出

```bash
typst compile data/monthly/{YYYY-MM}.typ data/monthly/{YYYY-MM}.pdf
```
Typst 特殊字符转义规则与日报一致（`$` → `\$`、`#` → `\#`、不支持 `**bold**`）。

---

## 注意事项

### 浏览器与抓取
- **固定 cwd**：先 `cd /Users/youngsdream/Documents/learn-claude-code`（v15.2）
- **必须使用浏览器逐帖浏览**：`browser_navigate` / `browser_run_code_unsafe` 打开帖子页面，不能用 fetch API
- **Cloudflare 挑战**：标题含 "Just a moment" 则等待 15 秒；预授权可点击验证区域（v14）。**0717 实测有时可直接进入站点**——以 `document.title` 为准
- **不回列表页**：直接从一个帖子导航到下一个帖子
- **每帖等待 1.5 秒** + 页载后 2 秒：避免触发限流
- **每批 10–15 帖（v15.5 默认）**：全量稳定优先；标准模式仍可 30
- **提前终止**：仅标准日报可在 120–150 帖后进入生成
- **全量抓取**：「全部抓取 / 过滤后全部抓取完」必须跑完 queue；规模约 **20–30 批 / 350–550 帖**（0717：517→490 有效；**0720：26+ 批 → 364 有效**）
- **单 Playwright**：批抓阶段禁止并行独立 Chrome 抢 profile（v15.3）
- **ERR_ABORTED / MCP 静默超时**：重置浏览器、缩小批次、retry 批号（v15.5）

### ⚠️ 反检测规则（必须遵守）
1. **逐帖浏览间隔 1.5 秒**
2. **检测 Cloudflare 挑战**：标题含 "Just a moment" 则等待 15 秒
3. **检测官方警告**：内容含 "异常的自动化访问行为" 或 "系统检测到" 则立即停止
4. **429 限流处理**：等待 30 秒后重试
5. **单帖 timeout 20s**：超时记 `error`，不中断整批
6. **连续 ERR_ABORTED ≥3**：停止本批，重置 MCP 浏览器后再抓（v15.5）

### ⚠️ 旧 Batch 文件清理（v14 + v15.2 + v15.5）
跨 session 时 `batch_browser_*` / `batch_ids_*` / `rem_batch_*` 会污染合并计数。

**冷启动抓取前删除**（必须在项目 cwd；**续跑有今日 batch 时不要清**）：
```python
import glob, os
os.chdir('/Users/youngsdream/Documents/learn-claude-code')
patterns = [
    'data/batch_browser_*.json', 'data/batch_ids_*.json',
    'data/rem_batch_*.json', 'data/crawl_queue*.json', 'data/remaining_todo.json',
]
n = 0
for pat in patterns:
    for f in glob.glob(pat):
        os.remove(f); n += 1
print(f'cleaned {n} files')
```

**合并前污染检查（v15.5）**：空 results / 结构异常 / mtime 明显非本 run → 删除该文件并只补抓缺失 id。

### 数据保存（v12 + v15.2 + v15.5）
- **每批立即保存**到 `data/batch_browser_N.json`（或 `batch_browser_retryN.json`）
- **不要等所有批次完成再保存**
- **空帖过滤**：无 `title` 不入库
- **大结果回填**：无法管道时用 session transcript / `save_latest_batch.py`（v15.2）
- **合并时二次公益站过滤**（标题+标签+content 前 200 字）
- **列表 views 合并**：帖子页 views=0 时用 crawl_queue 列表 views
- **error 帖单独重试**：不要把 error 计入 with_content

### 日期与过滤

- **概念库（v15）**：Writer 技术锚点只引用 `ai-concept-bank` 中 eligible ready；路径 `ai-concept-bank/concepts.json`
- **概念候选入库（v15.1）**：仅从日报 `## 概念候选（供 concept-bank）` 附录追加最小 `candidate`；必须去重、过滤、`jq` 校验；不生成口播、不改 ready、不写 usage-log
- **不能用 ID 阈值判断日期**：Discourse ID 不按日期顺序
- **必须过滤公益站**（列表 + 正文两遍）：公益站、LDC、cdk、签到、白嫖、薅羊毛、兑换码、免费额度、号池、号商、中转站、高级推广、抽奖、富可敌国、LightBridge公益、YSX666、日抛、午夜福利
- **必须历史去重**：扫描 `data/reports/*.md` 提取已报道帖子 ID（可排除 `_press.md`）
- **daily 文件名匹配**：用正则 `^\d{4}-\d{2}-\d{2}$` 严格匹配，排除 `_sorted`、`_topics`、`_classified` 等后缀文件（v14 新增）

### 并行 Agent 优化（v14 新增）
- **Topic Merger 和 Trend Analyzer 可并行启动**：两者数据独立，无需互相等待
- **Writer 必须等两者完成**：需要读取 topic_groups 和 trend_analysis
- **Press Writer 等 Writer 完成**：需要读取日报 Markdown
- **PDF Builder 等 Writer 完成**：需要读取日报 Markdown 转 Typst

### 流程完整性
- **必须按顺序完成所有 Agent**：Crawler → Topic Merger → Trend Analyzer → Writer → Press Writer → PDF Builder
- **Press Writer 和 PDF Builder 不可跳过**：即使用户没有明确要求，也必须生成
- **月报模式不抓取新数据**：聚合当月 daily JSON + 日报 MD，Crawler 仅做读取与聚合
- **月报数据缺失处理**：若某日数据缺失，标注缺失天数并继续生成，不中断流程

---

## 更新日志

### v15.5.0 (2026-07-20)
基于 **2026-07-20 全量日报**（过滤后全部抓取完）实战：

**批抓稳定性**
- MCP `browser_run_code_unsafe` 长静默可被 abort（~2491s）→ 默认批大小 **10–15**，必要时加 MCP timeout
- 连续 `page.goto` **`net::ERR_ABORTED`** → 立即落盘 → 重置 mcp-chrome → `rem_batch` / `batch_browser_retryN` 重试
- 合并前 **batch 污染校验**（旧 session 可写坏 `batch_browser_0.json`）
- 批号支持 `retry1` 等非纯数字；合并用 glob，勿假设 `int(N)` 文件名

**续跑协议**
- 中断后以磁盘为准：有 batch 无 daily → 合并；有 daily+pdf → 交视频；工具不全时不假装完成

**实测数据（2026-07-20）**
- 全量约 26 批 + retry → `data/daily/2026-07-20.json` **total=364 / with_content=364**
- 报告：`data/reports/2026-07-20.md` + press + typ + pdf
- PDF 落盘后接 ai-news-factory 免视频

**版本**：15.4.0 → 15.5.0

### v15.4.0 (2026-07-19)
基于 **2026-W28 周报**（07-13~07-19）实战：

**周聚合浏览量与去重**
- `views` 支持 `6.2k` / `万` 解析；同 id 合并时保留更高 views
- 帖子写入 `_day` 来源日期，便于大事记与 TOP 标注
- 覆盖检查：本周 7 日 `daily/*.json` + `reports/*.md` 齐全后再写周报

**产物与衔接**
- 周报 md/press/typ/**pdf** 必须落盘；`typst compile data/weekly/{week_id}.typ …pdf`
- 实测：去重主题 **2823**；日帖 374/491/454/390/490/531/668
- 与 ai-news-factory：**周 PDF 落盘后再开视频流水线**；批抓阶段只保留一个 Playwright

**版本**：15.3.0 → 15.4.0

### v15.2.0 (2026-07-17)
基于 2026-07-17 全量日报实战优化：

**固定项目 cwd（核心）**
- Bash 可能落在 `~/.claude/projects/...`，导致 `data/` 找不到、清理 batch 失败
- 强制 `cd /Users/youngsdream/Documents/learn-claude-code`；`browser_evaluate` filename 用绝对路径

**「过滤后全部抓取完」冷启动协议**
- 该触发词 = 全量流水线，不以用户口述代替磁盘检查
- 无 `data/daily/{date}.json` 时从 Crawler 重跑；有今日 batch 无 daily 则只合并

**crawl_queue + batch_ids 预切分**
- 32h 筛选后写 `data/crawl_queue.json` 与 `data/batch_ids_N.json`
- 全量模式按 batch_ids 顺序抓完，不在 150 帖提前停

**batch 保存 / transcript 回填**
- 每批立即 `batch_browser_N.json`
- 大 JSON 无法管道时，从 session jsonl 解析 `### Result` 转义串回填（`save_latest_batch.py`）

**正文二次公益站过滤 + views 合并**
- 列表过滤后仍会混入正文含「公益推广/CDK/日抛」的帖 → 合并时 title+tags+content[:200] 再滤
- 帖子页 views 常为 0 → 用列表页 views 补全

**主题分类扩展**
- 独立 DeepSeek；Kimi/Grok/OpenAI 关键词补全（k3/kivine/sol/terra/gpt-red 等）

**实测数据（2026-07-17）**
- Source A 930 + Source B AI 378 → 合并 1232 → 历史去重/公益站后 1084 → 32h **517** 帖
- 全量 18 批（0–17）→ 正文合并 514 → 二次过滤 **490** 有效
- 产出：`data/daily/2026-07-17.json` + reports md/press/pdf/typ + 4 个 concept candidate
- 整体耗时：约 90 分钟（含全量抓取 + 成稿）

### v15.1.0 (2026-07-13)
- **概念候选受控入库**：日报生成后可读取 `## 概念候选（供 concept-bank）`，经去重、过滤后只追加最小 `candidate`
- **安全边界**：不自动调用 narrator、不设 `reviewed=true`、不晋升 `draft/ready`、不写 `usage-log`
- **长期验证**：日报候选负责发现新词；`term-frequency` 负责验证长期价值；维护 Agent 决定后续 `candidate → draft → ready`
- **校验要求**：写入 `concepts.json` 后必须 `jq empty`，并确认新增条目为空口播、未审核、未影响 ready 概念

### v15.0.0 (2026-07-12)
- **接入 ai-concept-bank**：Writer 可读 `concepts.json`，条目「技术锚点：name — one_liner」（仅 ready + narrator + reviewed）
- **可信度五档**：官方确认 / 媒体报道 / 社区实测 / 源码迹象 / 未确认传闻；条目与亮点必标
- **条目模板**：中性标题 + 事实摘要 + 可信度 + 影响 + 技术锚点 + 信号
- **亮点**：硬新闻优先；权益/封号不得占亮点 50% 以上
- **Trend Analyzer**：可选 `source_hint` 映射五档
- **Press**：核心事件标可信度；风险区分已证实 vs 猜测
- **过滤**：求号/出号/接码/号商/代充纯交易帖过滤；账号风控帖降权不删
- **周报/月报模板**：同步可信度与中性标题；数据来源声明含「未确认不作为定论」
- **不写 15s 全文 / usage-log**：归 ai-news-factory + narrator
- **可选附录**：`## 概念候选（供 concept-bank）`
- **版本**：14.0.0 → 15.0.0


### v14.0.0 (2026-07-05)
基于 2026-07-05 日报+周报实战经验优化：

**Cloudflare 点击绕过（核心修复）**
- 旧方案：等待 15 秒自动通过 → **实测不够，页面停留在 "Just a moment..."**
- 新方案：`browser_snapshot` 查看结构 → `browser_click` 点击验证区域（通常是 `e6`）→ 页面立即通过
- 原因：Cloudflare Turnstile 挑战需要用户交互才能通过

**周报模式完整流程（核心新增）**
- 新增周报数据聚合脚本：基于 `data/daily/YYYY-MM-DD.json` 和 `data/reports/YYYY-MM-DD.md` 聚合
- 新增周报 Markdown 模板：含本周亮点、大事记、TOP 10、趋势分析、升温/降温对照表
- 新增周报多 Agent 流程表：6 个 Agent 的周报职责对照
- 新增并行优化说明：Topic Merger + Trend Analyzer 可并行启动

**旧 Batch 文件清理**
- 新增清理脚本：每次抓取前删除 `data/batch_browser_*.json`，避免跨 session 数据污染
- 新增说明：旧 batch 文件导致合并计数虚高

**daily 文件名匹配修复**
- 问题：`2026-06-30_sorted.json`、`2026-07-01_topics.json` 等后缀文件被日期范围匹配选中
- 修复：用正则 `^\d{4}-\d{2}-\d{2}$` 严格匹配纯日期格式文件名

**并行 Agent 优化**
- 新增并行模式说明：Topic Merger 和 Trend Analyzer 数据独立，可并行启动
- Writer/Press Writer/PDF Builder 仍需串行（有数据依赖关系）

**实测数据**
- 日报：Source A 930 帖 + Source B 292 帖 → 合并 1189 帖 → 32h 筛选 239 帖 → 全量抓取 8 批
- 周报：聚合 6 天日报数据、1994 帖、11 个主题分组
- 周报生成耗时：约 8 分钟（含 Topic Merger + Trend Analyzer 并行）

### v13.0.0 (2026-06-30)
新增**月报模式**，基于已有数据聚合，不重复抓取：

**月报触发词**
- 新增：月报、AI月报、技术月报、linuxdo月报、monthly、出月报、本月AI新闻、月度总结
- 支持指定月份：`月报 2026-05` / `2026年5月月报` / `上月月报`
- 不指定时默认生成上一个自然月

**月报数据策略（核心）**
- 不重复抓取，聚合当月 `data/daily/{YYYY-MM-DD}.json` 与 `data/reports/{YYYY-MM-DD}.md`
- 扫描日报 Markdown 提取每日亮点，用于跨日趋势归纳
- 帖子去重但不做历史去重（月内全量呈现）
- 复用 v12 公益站过滤规则
- 缺失日期标注并继续生成，不中断

**月报输出风格**
- 月度趋势总结 + 主题归纳（非按天拼接）
- 月度热门主题 TOP 10（按月度浏览量）
- 主题分布表（复用 Agent 2 分类规则）
- **下月展望**（基于本月趋势预测）

**月报多 Agent 职责调整**
- Crawler：改为读取当月已有数据并聚合
- Trend Analyzer：改为跨日趋势归纳（基于 daily_highlights）
- Writer / Press Writer / PDF Builder：使用月报模板，Typst 转义规则同 v12

**目录结构**
- 新增 `data/monthly/{YYYY-MM}.md` / `.json` / `_press.md` / `.pdf` / `.typ`

### v12.0.0 (2026-06-29)
基于 2026-06-29 实战经验优化：

**批量抓取数据保存修复（核心问题）**
- 旧方案：文档未强调保存时机，导致 batch 3-10 数据丢失
- 新方案：明确要求每批抓取后**立即**用 Python 保存到文件
- 新增空帖检测：已删除/私有帖子（空标题）不保存

**官方警告检测（v12 新增）**
- 新增检测页面内容中的 "异常的自动化访问行为" 或 "系统检测到"
- 触发时立即停止爬取，返回 `stopped: 'official_warning'`

**JSON 双重编码处理（v12 新增）**
- `browser_evaluate` 使用 `filename` 参数保存的 JSON 文件是 double-encoded
- 读取时需用 `json.loads(json.load(f))` 处理

**Typst 特殊字符处理（v12 重点修复）**
- `$` 必须转义为 `\$`（数学模式符号）
- `#` 必须转义为 `\#`（标记符号）
- `*` 用于斜体，不支持 `**bold**` 语法
- macOS 字体只需 PingFang SC

**全量抓取支持**
- 新增"全量抓取"模式说明：用户要求"全部抓取"时需完成所有批次
- 通常 8-10 批，240-300 帖

**实测数据**
- Source A: 868 帖，Source B: 135 帖 → 合并 970 帖
- 历史去重后 871 帖，32h 筛选后 262 帖
- 全量抓取 10 批 × 30 帖 = 300 帖（含空帖）
- 有效帖子约 180-200 帖，整体耗时约 35 分钟

### v11.0.0 (2026-06-24)
基于 2026-06-24 实战经验优化：

**滚动策略优化**
- 旧方案：固定 15 次滚动，不足再追加
- 新方案：递增滚动 3 轮（15+10+5），35 次可加载 1000+ 帖
- 每轮后检查数量决定是否继续

**批量抓取提前终止（核心优化）**
- 旧方案：必须抓取全部帖子正文
- 新方案：100-150 帖正文 + 其余仅用标题/标签/浏览量即可生成高质量日报
- 按浏览量降序优先抓取热门帖，4-5 批后可直接进入日报生成
- 大幅缩短总耗时（从 50 分钟降至 ~25 分钟）

**时间戳提取合并**
- 旧方案：步骤 1.3 提取列表 + 步骤 1.6 单独提取时间戳
- 新方案：步骤 1.3 一次性提取列表+时间戳（从 `td.activity[title]`）
- 省去单独的时间戳提取步骤和 `data/topic_timestamps.json` 中间文件

**批量抓取不回列表页**
- 旧方案：每帖抓取后返回列表页（多 1.5s 等待 + 一次页面加载）
- 新方案：直接从一个帖子导航到下一个帖子
- 每帖节省约 3 秒，30 帖一批节省约 90 秒

**批量大小调整**
- 每批从 20 帖提升到 30 帖（减少批次切换开销）

**Typst 模板修复**
- 字体：`("PingFang SC", "Helvetica Neue", "Arial")`（移除未安装的 Noto Sans CJK SC）
- 新增 `#` 转义提醒：文本中的 `#` 必须写成 `\#`

**主题分类规则更新**
- 新增：豆包/火山引擎 生态（豆包, doubao, seed, 火山, seedance, 字节）
- 新增：Grok 生态（grok）
- 扩展 AI 编程工具：加入 hermes, opencode, kiro, minimax
- 扩展 OpenAI 关键词：sub2api, plus, pro20, pro 5x
- 扩展 Claude 关键词：cc-switch, max

**实测数据**
- Source A: 1049 帖，Source B: 372 帖 → 合并 1379 帖
- 历史去重后 1313 帖，32h 筛选后 432 帖，公益站过滤后 412 帖
- 正文抓取 120 帖（4 批），整体耗时约 25 分钟

### v10.0.0 (2026-06-23)
基于 2026-06-23 实战经验重构：

**核心变更：时间戳提取方式**
- 旧方案：`document.querySelector('time')` 从帖子页面提取 → **返回空！帖子页面没有 `<time>` 元素**
- 新方案：从列表页 `td.activity[title]` 属性提取 `"Created: Jun 22, 2026 9:53 pm"` 格式
- 原因：Discourse 帖子页使用相对时间显示（"14h"），不暴露 `<time>` 元素

**抓取流程优化**
- 用户要求模拟人类浏览：逐帖打开 → 返回列表页 → 打开下一帖
- 每批 20 帖（原 30 帖），返回列表页间隔 1.5 秒
- 全部抓取完后再做 32 小时筛选（不在抓取过程中筛选）
- 超时 20 秒（原 15 秒）

**时间戳合并流程**
- 滚动加载列表页 → 提取 `td.activity[title]` → 保存到 `data/topic_timestamps.json`
- 使用 `dateutil.parser.parse()` 解析 `"Jun 22, 2026 9:53 pm"` 格式
- 合并时间戳到帖子数据后再做 32 小时筛选

**公益站过滤优化**
- 增加关键词：LDC、ldc、高级推广、富可敌国、中转站、抽奖
- 同时检查标题、标签、内容前 200 字

**实测数据**
- 496 帖全部抓取，公益站过滤后 420 帖
- 32 小时筛选后 253 帖纳入日报
- 整体耗时约 50 分钟（含浏览器预授权）

### v9.0.0 (2026-06-21)
基于 2026-06-21 实战经验重构：

**核心变更：浏览器 fetch API → 浏览器逐帖浏览**
- 旧方案：`browser_evaluate` + `fetch('/t/{id}.json')` → 触发 429 限流
- 新方案：`browser_navigate` 打开帖子页面 → 提取 DOM 数据 → 直接导航下一帖
- 原因：linux.do 对批量 API 请求做了严格限流，浏览器逐帖浏览更安全

**抓取流程**
- 主力方案：`browser_navigate` 打开帖子页面 + `browser_evaluate` 提取 DOM 数据
- 速度优化：不回列表页，直接从一个帖子导航到下一个帖子
- Cloudflare 处理：每帖检测标题，包含 "Just a moment" 则等待 15 秒

**预授权优化**
- 简化为 4 步：关闭旧实例 → 导航触发 → 等待 Cloudflare → 确认页面加载
- 明确列出需要预授权的工具清单
- 强调不需要登录态

**已知限制**
- 逐帖浏览方式较慢（每帖约 3-5 秒：导航 2s + 提取 1s + 等待 0.5s）
- 849 帖全部抓取需要约 45-70 分钟
- 部分帖子可能返回空标题（已删除或私有）

### v15.3.0 (2026-07-18)
基于 2026-07-18 全量日报 + 视频工厂联跑经验：

**全量抓取闭环（实测）**
- 双源列表合并后队列约 557 帖 → 正文批次 0–18（末批不足 30）→ 有效标题约 556 → 二次公益站过滤后 **531** 入 `data/daily/YYYY-MM-DD.json`
- **每批必须立即** `data/save_latest_batch.py N` 或等价写入 `data/batch_browser_N.json`；禁止「全部抓完再存」
- 工具返回 JSON 若只在 transcript 里：从 session jsonl 回填（见 v15.2 协议）

**浏览器稳定**
- 全量批抓阶段**只保留一个** Playwright MCP 会话；不要并行启动视频号独立 Chrome 共用 profile
- 批抓循环内：Cloudflare 标题检测 + 官方「异常自动化访问」文案则停批保存已抓
- 与 `ai-news-factory` 衔接：日报 PDF/报告落盘后再开视频流水线，减少浏览器互杀

**合并与过滤**
- 合并 `crawl_queue` 元数据时：列表页 views 若高于详情 DOM 则回填（详情有时为 0/占位）
- 二次过滤：标题/标签/内容前 200 字扫公益站与纯交易词（与 v15.2 关键词表一致）
- Writer 可信度分层：官方确认 / 社区实测 / 媒体报道 / 未确认传闻

**联跑检查清单**
1. `data/daily/{date}.json` total 与 with_content
2. `data/reports/{date}.md` + `_press.md` + `.pdf`
3. 再触发 ai-news-factory（推荐事件可不确认）
