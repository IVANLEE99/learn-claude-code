# 专业锚点（ai-concept-bank 接入）

> 供 Phase 1 选题 + Phase 2 口播 + 用户确认后写 log。  
> 主库路径（相对项目根）：`ai-concept-bank/concepts.json`  
> 使用记录：`ai-concept-bank/usage-log.json`  
> 台词生产：仅 `ai-concept-narrator`（**禁止**主会话手写成品定义）

---

## 铁律（ready + narrator only）

上片锚点必须同时满足：

1. `status == "ready"`  
2. `script_15s`（或周/月用的 `script_60s`）**非空**  
3. `script_meta.authored_by == "ai-concept-narrator"`  
4. `script_meta.reviewed == true`  

任一不满足 → **不得**直接进视频。处理：

- 调 `ai-concept-narrator` 按 `ai-concept-bank/prompts/script-15s-request.md` 生产  
- 写入概念库且 `reviewed=true` 后改 `ready`  
- 再用于本期脚本  

**禁止**：从白说库 / Gemini 草稿 / 主会话即兴段落 copy 进成片。

---

## 模式参数

| REPORT_MODE | 锚点时长 | 优先字段 |
|-------------|---------|----------|
| daily | **15s** | `script_15s` |
| weekly | **30–60s** | `script_60s`，若 null 则用 `script_15s` 并标注「15s 兜底」 |
| monthly | **30–60s** | 同上 |

每期 **恰好 1 个** 专业锚点（可与用户确认后跳过：仅当库不可用或用户明确「本期不要锚点」）。

---

## Phase 1：自动选题算法（Step 1.6）

在用户确认本期限定事件 / 趋势 **之后**、进入 Phase 2 **之前**执行。

### 1. 加载库

```bash
test -f ai-concept-bank/concepts.json
```

读取：

- `reuse_gap_days`（默认 14）
- 仅 **eligible** 概念：`ready` + 台词非空 + `authored_by=ai-concept-narrator` + `reviewed=true`  
- 可选读 `usage-log.json`

### 2. 从本期正文抽触发词

把用户确认的事件标题 + 摘要拼成 `episode_text`。  
对每个 eligible 概念，若 `news_keywords` / `aliases` / `name` 任一项命中 → 记入 `hits[]`，并记录命中的事件标题。

### 3. 冷却过滤

- `last_used` 为空 → 通过  
- 同角度：`days >= reuse_gap_days`（默认 14）  
- 换角度：`days >= 7`（Phase 2 必须再调 narrator，不得复读旧 `script_15s`）  
- 不满足 →「冷却中」，可展示但不默认推荐  

### 4. 打分排序

| 分 | 条件 |
|----|------|
| +100 | 命中本期事件 keywords（P1） |
| +40 | tier == 1 |
| +20 | `last_used` 为空 |
| +10 | `last_used` 越旧（天数/30 封顶 +10） |
| +5 | `use_count` 0–2 |
| -30 | 与 usage-log 最近 1 条同 category（弱） |

取 top 3，**默认推荐 #1**。

### 5. 向用户展示（必须确认）

```text
🎯 本期专业锚点候选（ai-concept-bank · narrator ready only）

推荐：`moe` MoE — 命中「…」· last_used=从未 · 15s ready · authored_by=ai-concept-narrator
  2. …
  3. …（P3 兜底：无强命中，tier1 最久未用）

冷却跳过：`distillation`（3 天前）
不合格跳过：`xxx`（非 narrator / 未 reviewed）— 不计分

请回复：用推荐 / 选编号 / 换概念id / 本期不要锚点
```

会话变量：

```text
ANCHOR_CONCEPT_ID=moe
ANCHOR_ANGLE=基础定义
ANCHOR_DURATION_SEC=15
ANCHOR_SKIP=false
```

---

## Phase 2：写入脚本

### 位置

- 日/周：命中新闻之后；无命中 → CTA 前
- 月：最相关趋势后；无命中 → 月度总结前
- 🔴 **70-80% 硬约束（v3.21.0）**：无论命中与否，锚点 scene 起始秒 / 总秒须 ∈ [0.7, 0.8]，直击中段尿点（诊断4 完播率 4.35%）。若命中概念在 **55% 前**出现的新闻后，补 ≤15 字桥句"这个词待会儿专门讲清"，再在 70-80% 处集中解释；偏离 >5% 须重排 scene 顺序。08-24 锚点落在 57%（中段尿点之前）即违反此约束。

### 场景文本

```text
场景N 专业锚点：
{eligible.script_15s 或 script_60s}
```

允许前缀过渡 ≤15 字（「刚才提到 MoE——」），**不得改动**库内定义句。

### 独立 scene

锚点 = 独立 wav + 图，计入 Phase 7/8 场景数。

---

## 用户确认脚本后：写 log（强制）

**时机**：Phase 2 用户确认通过 → Phase 3 之前。`ANCHOR_SKIP=true` 则跳过。

### 1. Append `usage-log.json`

```json
{
  "date": "YYYY-MM-DD",
  "concept_id": "moe",
  "angle": "基础定义",
  "mode": "daily",
  "duration_sec": 15,
  "news_trigger": "命中的事件标题或趋势名",
  "report_path": "{REPORT_PATH}",
  "script_path": "news-pipeline/.../scripts/...",
  "notes": ""
}
```

`date` 推荐成片日 `today`（便于 gap）；报告标签可写在 `notes`。

### 2. 更新 `concepts.json` 对应条目

- `last_used` = 同上 date  
- `use_count` += 1  
- `angles.used` 含本次 angle  
- **不要**改 `script_15s` / `status` / `script_meta.authored_by`

### 3. 子模块

写 log 后 submodule 会脏；**不静默 commit**，可提示稍后 bump。

---

## 失败降级

| 情况 | 处理 |
|------|------|
| 库不存在 | 提示 `git submodule update --init ai-concept-bank`；可跳过锚点 |
| 无 eligible ready | 跳过或现场调 narrator 补 1 条再审 |
| 全部冷却 | 展示列表；用户可 force（notes 标明）或跳过 |
| 命中 0 | P3：tier1 + last_used 最旧的 eligible |

---

## 审核清单追加

```text
☐ 仅 1 个锚点场景（或 ANCHOR_SKIP）
☐ 台词来自 ready 且 authored_by=ai-concept-narrator、reviewed=true
☐ 用户确认后已写 usage-log 并更新 last_used
☐ 🔴 锚点位置=总时长 70-80% 处（v3.21.0）：锚点 scene 起始秒/总秒∈[0.7,0.8]，偏离>5% 须重排
```
