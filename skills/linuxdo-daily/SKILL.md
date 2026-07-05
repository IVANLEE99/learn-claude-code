---
name: linuxdo-daily
description: linux.do AI日报/周报/月报自动生成。多 Agent 协作：Crawler 抓取双数据源 → Topic Merger 合并主题 → Trend Analyzer 生成趋势 → Writer 输出日报/周报/月报 → Press Writer 生成新闻稿 → PDF Builder 生成 PDF。触发词：日报、周报、月报、linuxdo日报、AI日报、AI周报、AI月报、技术日报、weekly、monthly
version: 14.0.0
---

# linuxdo-daily — AI 技术日报生成 Skill（多 Agent 架构）

从 linux.do 自动抓取 AI 相关帖子，通过 6 个专用 Agent 协作生成每日技术日报，并支持周报与月报模式。

> **v14 核心改进**：Cloudflare 点击绕过、周报模式完整流程、并行 Agent 优化、旧 batch 文件清理。
> **v13 核心改进**：新增月报模式。月报基于当月已抓取数据与已生成的日报数据聚合，不重复抓取，输出月度趋势总结 + 主题归纳 + 下月展望。
> **v12 核心改进**：批量抓取数据强制保存、空帖检测跳过、官方警告检测、全量抓取支持、Typst 特殊字符处理。

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

### 1.6 时间戳解析与 32h 筛选

> **v11 变更**：时间戳已在步骤 1.3 中从列表页 `td.activity[title]` 提取，此步骤仅做解析和筛选。

**⚠️ 常识提醒**：帖子页面没有 `<time>` 元素！`document.querySelector('time')` 返回空。时间只能从列表页提取。

```python
import json
from dateutil import parser as dateparser
from datetime import datetime, timezone, timedelta

now = datetime.now(timezone(timedelta(hours=8)))
cutoff = now - timedelta(hours=32)

with open('data/daily/2026-06-24.json') as f:
    daily = json.load(f)

final_posts = []
for post in daily['posts']:
    created_str = post.get('created', '')
    if not created_str:
        continue
    try:
        created_dt = dateparser.parse(created_str)
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone(timedelta(hours=8)))
        if created_dt >= cutoff:
            post['created_at'] = created_dt.isoformat()
            final_posts.append(post)
    except:
        pass

daily['posts'] = final_posts
daily['total'] = len(final_posts)
print(f'32h 筛选: {len(daily["posts"])} 帖')
```

### 1.7 逐帖浏览器浏览（核心抓取方案）

**必须使用此方案**，浏览器 fetch API 会被 429 限流。

#### ⚡ 提前终止策略（v11 新增）

**不需要抓取全部帖子！** 实测表明，100-150 帖的正文数据已足够生成高质量日报。其余帖子仅使用标题+标签+浏览量即可完成主题分类。

**推荐做法**：
- 按浏览量降序排列待抓取列表（热门帖优先）
- 抓取前 4-5 批（120-150 帖）后直接进入日报生成
- 冷门帖子的标题和标签已包含足够信息用于主题分类

#### 抓取流程

1. **打开列表页**：`browser_navigate → https://linux.do/tag/444-tag/444`
2. **滚动加载全部帖子**：见步骤 1.2（35 次滚动）
3. **提取帖子列表含时间戳**：`browser_evaluate`（见步骤 1.3）
4. **合并去重筛选**：历史去重 + 公益站过滤 + 32h 筛选
5. **按浏览量排序**：热门帖优先抓取
6. **批量抓取正文**：每批 30 帖，抓取 4-5 批后可提前终止

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

#### ⚠️ 批量抓取数据保存（v12 核心修复）

**2026-06-29 实测问题**：浏览器 `browser_run_code_unsafe` 返回的 JSON 结果必须**立即用 Python 保存到文件**，否则数据会丢失。

**正确流程**：
1. `browser_run_code_unsafe` 执行批量抓取 → 返回 JSON 字符串
2. **立即**用 Bash/Python 保存到 `data/batch_browser_N.json`
3. 继续下一批

**错误做法**：等所有批次抓完再保存（数据会丢失）

```python
# 每批抓取后立即执行此代码保存数据
import json
# results_json 是 browser_run_code_unsafe 返回的字符串
data = json.loads(results_json)
with open(f'data/batch_browser_{N}.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'Batch {N} 已保存: {len(data.get("results", []))} 帖')
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

- **每批 30 帖**：处理完一批后保存到 `data/batch_browser_N.json`
- **每帖等待 2 秒**：帖子页加载后等待 2 秒再提取
- **帖间等待 1.5 秒**：避免触发限流（不回列表页，直接导航下一帖）
- **超时 20 秒**：单帖加载超时 20 秒则跳过

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

### 1.8 数据合并与过滤

> **v12 重要修复**：`browser_evaluate` 使用 `filename` 参数保存的 JSON 文件是 **double-encoded**（双重编码），需要用 `json.loads(json.load(f))` 读取。

```python
import json, os, glob, re
from datetime import datetime, timezone, timedelta

# 1. 合并所有 batch 文件
all_posts = {}
for f in sorted(glob.glob('data/batch_browser_*.json')):
    with open(f) as fh:
        batch = json.load(fh)
    # 处理可能的 double-encoded JSON
    if isinstance(batch, str):
        batch = json.loads(batch)
    results = batch.get('results', [])
    for p in results:
        pid = str(p.get('id', ''))
        if pid and p.get('title'):  # v12: 只保留有标题的帖子
            all_posts[pid] = p

print(f'合并后有效帖子: {len(all_posts)}')

# 2. 公益站过滤
GONGYI_KEYWORDS = ['公益站', '公益推广', 'LDC', 'ldc', 'cdk', '签到', '白嫖',
                   '薅羊毛', '薅秃', '兑换码', '免费额度', '号池', '号商', '充值额度',
                   '中转站', '高级推广', '抽奖', '富可敌国']

filtered = {}
for pid, p in all_posts.items():
    all_text = f"{p.get('title', '')} {' '.join(p.get('tags', []))}"
    if not any(kw in all_text for kw in GONGYI_KEYWORDS):
        filtered[pid] = p

print(f'公益站过滤后: {len(filtered)}')

# 3. 保存每日数据
date_str = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')
os.makedirs('data/daily', exist_ok=True)
daily_data = {
    'date': date_str,
    'total': len(filtered),
    'posts': [{'id': pid, **p} for pid, p in filtered.items()]
}
with open(f'data/daily/{date_str}.json', 'w') as f:
    json.dump(daily_data, f, ensure_ascii=False, indent=2)
```

```python
import json, os, glob, re
from datetime import datetime, timezone, timedelta

# 1. 合并所有 batch 文件
all_posts = {}
for f in sorted(glob.glob('data/batch_browser_*.json')):
    with open(f) as fh:
        posts = json.load(fh)
    for p in posts:
        pid = str(p.get('id', ''))
        if pid and pid not in all_posts and p.get('title'):
            all_posts[pid] = p

# 2. 公益站过滤
GONGYI_KEYWORDS = ['公益站', '公益推广', 'LDC', 'ldc', 'cdk', '签到', '白嫖',
                   '薅羊毛', '薅秃', '兑换码', '免费额度', '号池', '号商', '充值额度',
                   '中转站', '高级推广', '抽奖', '富可敌国']

filtered = {}
for pid, p in all_posts.items():
    all_text = f"{p.get('title', '')} {' '.join(p.get('tags', []))}"
    if not any(kw in all_text for kw in GONGYI_KEYWORDS):
        filtered[pid] = p

# 3. 保存每日数据
date_str = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')
os.makedirs('data/daily', exist_ok=True)
daily_data = {
    'date': date_str,
    'total': len(filtered),
    'posts': [{'id': pid, **p} for pid, p in filtered.items()]
}
with open(f'data/daily/{date_str}.json', 'w') as f:
    json.dump(daily_data, f, ensure_ascii=False, indent=2)
```

---

## Agent 2: Topic Merger（主题合并器）

**职责**：合并两个数据源的帖子，去重，过滤公益站，按主题聚类。

### 主题分类规则

按以下维度对帖子进行分组（按优先级匹配，命中第一个即归类）：
- **OpenAI/ChatGPT/Codex 生态**：codex, chatgpt, gpt, openai, sub2api, plus, pro20, pro 5x
- **Claude/Anthropic 生态**：fable, mythos, opus, anthropic, claude code, claudecode, cc-switch, max
- **豆包/火山引擎 生态**：豆包, doubao, seed, 火山, seedance, 字节
- **GLM/智谱 生态**：glm, 智谱, zai, glm5.2
- **Grok 生态**：grok
- **Kimi/月之暗面**：kimi, 月之暗面
- **Google/Gemini 生态**：gemini, google, antigravity
- **AI 编程工具**：cursor, windsurf, trae, hermes, opencode, kiro, minimax
- **开源项目**：开源推广, 开源
- **行业动态**：前沿快讯, 前沿, 转载, 安全, 边界
- **其他话题**：其余

---

## Agent 3: Trend Analyzer（趋势分析器）

**职责**：分析帖子内容和热度，生成今日技术趋势。

### 分析维度

- **热度分析**：浏览量、回复数、点赞数最高的帖子
- **内容分析**：帖子正文中反复出现的技术关键词
- **时间线**：今日新出现的话题 vs 持续讨论的话题
- **争议性**：回复数/浏览比最高的帖子（讨论最激烈）

---

## Agent 4: Writer（日报撰写器）

**职责**：读取合并数据和趋势分析，生成完整的 Markdown 日报。

### 日报结构

```markdown
# linux.do 人工智能 技术日报
**{date}** | 数据来源：linux.do #人工智能 + 前沿快讯

## 今日亮点
（3-5 条高亮，每条一句话概括，包含关键数据如浏览量）

## 新内容

### {主题分组名}
- **帖子标题** — 摘要（浏览 X）

（按主题分组，每组 3-10 个帖子）

## 数据概览
| 标签 | 帖数 |
|------|------|
```

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
- **禁止**：论坛口语、emoji、感叹号堆砌
- **数据优先**：每个论点必须有数据支撑

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
                if pid and p.get('title'):
                    week_posts[pid] = p
        except:
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
        except:
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
```

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
（5 条高亮，每条一句话概括，包含关键数据）

## 本周大事记
（按时间线列出每天 1-3 条重大事件）

## 本周热门主题 TOP 10
1. **帖子标题** — 摘要（浏览 X | 日期）

## 主题趋势分析
### 趋势一：{趋势名}
（2-3句话描述趋势变化）

## 主题分布
| 主题分组 | 帖数 | 占比 |

## 升温 vs 降温
| 升温话题 | 降温话题 |

## 下周展望
（2-3句话预测）

## 数据来源说明
- 数据时间范围：{week_start} ~ {week_end}
- 基于日报文件：{count} 份
- 公益站/中转站内容已过滤
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
1. **帖子标题** — 摘要（浏览 X | 回复 Y | 出现日期）
2. ...
（按月度浏览量降序排列，标注每周话题峰值）

## 月度技术趋势
### 趋势一：{趋势名称}
- **热度变化**：本月讨论量 / 起止时间 / 周环比
- **关键驱动**：核心事件或发布
- **代表主题**：相关帖子链接

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
- **必须使用浏览器逐帖浏览**：`browser_navigate` 打开帖子页面，不能用 fetch API
- **Cloudflare 挑战**：每帖检测标题，包含 "Just a moment" 则等待 15 秒；预授权阶段需要**点击验证区域**（v14 新增）
- **不回列表页**：直接从一个帖子导航到下一个帖子（v11 确认：省去返回列表页的 1.5s 等待）
- **每帖等待 1.5 秒**：避免触发限流
- **每批 30 帖**：处理完一批保存，继续下一批（v11：从 20 帖提升到 30 帖）
- **提前终止**：抓取 100-150 帖后可直接生成日报，不需要全部抓完
- **全量抓取**：用户要求"全部抓取"时，需完成所有批次（通常 8-10 批，240-300 帖）

### ⚠️ 反检测规则（必须遵守）
1. **逐帖浏览间隔 1.5 秒**：每帖之间固定等待 1.5 秒
2. **检测 Cloudflare 挑战**：如果页面标题包含 "Just a moment"，等待 15 秒
3. **检测官方警告**：如果页面内容包含 "异常的自动化访问行为" 或 "系统检测到"，立即停止爬取
4. **429 限流处理**：如果触发 429，等待 30 秒后重试

### ⚠️ 旧 Batch 文件清理（v14 新增）
跨 session 运行时，`data/batch_browser_*.json` 可能残留上次抓取的数据，导致：
- 合并计数虚高（显示已抓取229帖，实际本次仅抓取120帖）
- 包含过期数据

**解决方案**：每次抓取前**先删除旧 batch 文件**：
```python
import glob, os
for f in glob.glob('data/batch_browser_*.json'):
    os.remove(f)
print("已清理旧 batch 文件")
```
或者在合并时按 session 过滤——但删除更简单可靠。

### 数据保存（v12 重点）
- **每批抓取后必须立即保存**：`browser_run_code_unsafe` 返回的 JSON 必须用 Python 保存到文件
- **不要等所有批次完成再保存**：会导致数据丢失
- **空帖过滤**：已删除或私有帖子返回空标题，不需要保存

### 日期与过滤
- **不能用 ID 阈值判断日期**：Discourse ID 不按日期顺序
- **必须过滤公益站**：公益站、LDC、cdk、签到、白嫖、薅羊毛、兑换码、免费额度、号池、号商、中转站、高级推广、抽奖、富可敌国
- **必须历史去重**：扫描 `data/reports/*.md` 提取已报道帖子 ID
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
