---
name: post-to-img
description: 将论坛帖子/长文复盘自动转化为日系手账风信息图，并调用 gen-img 生图。触发词: "帖子生图", "post to image", "长文转图", "复盘信息图", "被优化了生图", "手账风海报", "帖子做成图", linux.do 帖子配图
version: 1.0.0
---

# post-to-img — 帖子/长文 → 手账风信息图

把 **linux.do 帖子、Markdown 长文、粘贴正文** 结构化为「日系手账 × Q 版吉祥物」信息图提示词，再 **强制通过 `gen-img` skill** 出图。

> **设计锚点**：参考图「被优化了，第一天」——奶油纸、草莓粉标题、圆角卡片、仓鼠/白兔吉祥物、三栏网格、治愈不丧。

## 触发条件

用户出现以下意图时激活：

- 帖子生图 / 长文转图 / 复盘信息图 / 手账风海报
- 「把这个帖子做成图」「仿那张仓鼠信息图」
- 给出 `linux.do/t/topic/...` 并要求配图 / 生图
- post to image / forum post infographic

**不触发**：纯画风景/角色、与帖子无关的自由生图 → 走 `gen-img`。

## 依赖

| 依赖 | 用途 |
|------|------|
| `gen-img` skill | **唯一**生图出口：`bash ~/.claude/skills/gen-img/scripts/gen-img.sh` |
| Playwright MCP | 抓取 `linux.do` 等需登录/反爬页面 |
| `settings.json` env | `GEN_IMG_API_URL` / `GEN_IMG_API_KEY` / `GEN_IMG_MODEL`（由 gen-img 读取） |

本 skill **禁止**自己 curl Images API；一律调用 gen-img 脚本。

## 端到端流程（必须按序）

```
用户输入（URL / 文件 / 粘贴）
        ↓
[1] 取文  fetch_post
        ↓
[2] 结构化  structure_content  → content.json
        ↓
[3] 选风格  pick_style（默认 kawaii-journal）
        ↓
[4] 拼 Prompt  build_prompt → prompt.txt + prompt.meta.json
        ↓
[5] 确认（可选）  用户说「直接出图」则跳过
        ↓
[6] 生图  invoke gen-img
        ↓
[7] 落盘展示  image + prompt 同目录，Read 展示图片
```

### Step 1 — 取文 `fetch_post`

按输入类型处理：

| 输入 | 动作 |
|------|------|
| `https://linux.do/t/topic/...` | Playwright：`browser_navigate` → `browser_evaluate` 抽 `#post_1 .cooked` 或首个 `.cooked` 正文 + `h1` 标题 + 作者 |
| 其他公开 URL | `WebFetch`；失败再用 Playwright |
| 本地 `.md` / `.txt` | `Read` 文件 |
| 对话内粘贴 | 直接使用用户文本 |

**linux.do 抽取脚本（evaluate）：**

```js
() => {
  const title = document.querySelector('h1')?.innerText?.trim() || document.title;
  const author = document.querySelector('.topic-meta-data .username, .names .username')?.innerText?.trim() || '';
  const cooked = document.querySelector('#post_1 .cooked, article#post_1 .cooked, .topic-post:first-of-type .cooked')
    || document.querySelector('.cooked');
  return {
    title,
    author,
    url: location.href,
    body: cooked ? cooked.innerText.trim() : '',
  };
}
```

保存原始文到：

```text
~/Documents/learn-claude-code/generated-images/post-to-img/{slug}/source.md
```

`slug` = 日期 + 标题拼音/topic-id 简化，例如 `20260721_2609603`。

### Step 2 — 结构化 `structure_content`

把长文压成 **信息图友好的 6–8 个区块**（不要原文照搬墙字）。输出 JSON：

```json
{
  "title": "被优化了，第一天",
  "subtitle": "接受现实，复盘自己，拥抱AI，创造更多可能！",
  "hook": "生活不会突然变好，但你可以选择让自己变得更强",
  "mood_checklist": ["接受现实", "复盘反思", "规划未来", "行动起来"],
  "sections": [
    {
      "id": 1,
      "heading": "今天发生了什么",
      "bullets": ["...", "..."],
      "mascot_mood": "crying"
    }
  ],
  "table": {
    "title": "AI带来的变化",
    "headers": ["阶段", "时间", "AI能力", "我做的事", "效果"],
    "rows": []
  },
  "toolbox": ["MCP", "Rules & Skills", "..."],
  "trials": ["小尝试1", "..."],
  "plan": ["下一步1", "..."],
  "money_ideas": ["...", "..."],
  "letter_to_future": "给未来的自己一句话",
  "tip": "今日小贴士一句话",
  "closing": "底部寄语",
  "cta": "交流欢迎 / 一起加油"
}
```

**结构化规则：**

1. **标题**：优先帖子 `h1`；可轻微润色（去掉句号、控制 8–14 字）。
2. **副标题**：从全文提炼 1 句行动纲领（接受 / 复盘 / AI / 行动）。
3. **左栏情绪**：发生了什么 → 内心感受 → 担忧/竞争力（3 卡）。
4. **中栏能力**：AI 跃迁表（若文中有时间线）+ 工具箱 + 小尝试勾选。
5. **右栏行动**：计划 / 赚钱或下一步 / 给未来的自己。
6. **底部**：小贴士 + 寄语 + CTA。
7. 每条 bullet **≤ 28 字**；整图中文可见字建议 **≤ 450 字**（生图模型吃字能力有限）。
8. 保留原帖金句，不编造未出现的事实；可归纳压缩。
9. `mascot_mood` 映射：`crying | sad | dizzy | focus-laptop | coins | reading | pray | heart | teacher-rabbit`。

可先把 JSON 写到 `{slug}/content.json`。

### Step 3 — 选风格 `pick_style`

读取本 skill 的风格预设：

| preset | 说明 | 何时用 |
|--------|------|--------|
| `kawaii-journal`（默认） | 奶油纸 + 仓鼠/白兔 + 草莓粉手账信息图 | 复盘、被优化、情绪向、职场自媒体 |
| `clean-tech` | 浅灰蓝极简信息卡，无吉祥物 | 纯技术总结、用户明确不要萌系 |
| `warm-note` | 便签拼贴、少表格 | 短感想、书摘 |

用户说「像那张仓鼠图 / 手账风 / 可爱风」→ 强制 `kawaii-journal`。  
完整视觉 DNA 见 `references/style-presets.md`。

### Step 4 — 拼 Prompt `build_prompt`

**优先**用脚本生成，再由 Claude 做一次人工润色（补漏、压字数）：

```bash
python3 ~/.claude/skills/post-to-img/scripts/build_prompt.py \
  --content ~/Documents/learn-claude-code/generated-images/post-to-img/{slug}/content.json \
  --preset kawaii-journal \
  --out-dir ~/Documents/learn-claude-code/generated-images/post-to-img/{slug}
```

脚本产出：

- `prompt.txt` — 送给 gen-img 的完整中文 prompt（主）
- `prompt_en.txt` — 英文备用（部分模型更稳）
- `prompt.meta.json` — size / quality / preset / source_url

**Prompt 铁律（kawaii-journal）：**

1. 先写 **画幅与整体风格**，再写 **顶栏 → 三栏 → 底栏** 布局。
2. 点名 **奶油米白底、草莓粉大标题、圆角卡片、细手绘描边、Q 版仓鼠/白兔**。
3. 关键中文标题、副标题、各 section 标题必须出现在 prompt 里（便于模型尝试渲染文字）。
4. bullet 只放压缩后的短句，禁止把整段原文塞进 prompt。
5. 结尾加 negative 约束（可并入 prompt 末尾或 gen-img 不支持 negative 时写进正文）：

```text
避免：写实摄影、3D、赛博霓虹、暗黑丧系、纯黑大字墙、无分区的密密麻麻正文、真人脸、低清模糊。
```

6. 默认尺寸：**`1536x1024`**（横版信息图）；用户要小红书竖图则用 `1024x1536`。

### Step 5 — 确认（可跳过）

默认展示：

- 结构化摘要（各 section 标题 + bullet 数）
- `prompt.txt` 前 40 行
- 将使用的 size / model（model 来自 gen-img 配置）

若用户已说 **「直接出图 / 不用确认 / 开干」** → 跳过确认。

### Step 6 — 生图（调用 gen-img）

**必须**执行：

```bash
bash ~/.claude/skills/gen-img/scripts/gen-img.sh \
  "$(cat ~/Documents/learn-claude-code/generated-images/post-to-img/{slug}/prompt.txt)" \
  "~/Documents/learn-claude-code/generated-images/post-to-img/{slug}/poster.png" \
  "1536x1024" \
  "high" \
  "1" \
  "png"
```

注意：

- prompt 含引号/换行时，**不要**直接裸拼进 bash 双引号；用脚本读文件传参，或：

```bash
PROMPT=$(python3 -c "print(open('.../prompt.txt').read())")
bash ~/.claude/skills/gen-img/scripts/gen-img.sh "$PROMPT" "$OUT" "1536x1024" "high" "1" "png"
```

更稳妥：用本 skill 封装脚本：

```bash
bash ~/.claude/skills/post-to-img/scripts/run_gen.sh \
  ~/Documents/learn-claude-code/generated-images/post-to-img/{slug}
```

`run_gen.sh` 内部读取 `prompt.txt` + `prompt.meta.json` 再调 gen-img。

失败时：

1. 缩短 prompt（先砍 toolbox/table 细节）重试 1 次  
2. 换 `prompt_en.txt` 再试 1 次  
3. 仍失败 → 报告 gen-img 错误，不编造图片

### Step 7 — 展示与交付

1. `Read` 生成的 `poster.png` 给用户看  
2. 汇报路径、size、model、preset、source  
3. 同目录保留：`source.md` / `content.json` / `prompt.txt` / `poster.png`  
4. 若文字糊/乱（生图通病）：提供「无字底板 prompt」二次生成方案（见下）

## 无字底板模式（可选）

当用户要求 **可编辑文字** 或模型中文排版崩坏时：

1. 用 `build_prompt.py --textless` 生成只有布局+吉祥物+色块标题占位的 prompt  
2. 出图后提示用户在 Figma/PS 叠 `content.json` 文案  
3. 文件名：`poster_textless.png`

## 快速命令示例

```text
# 从 linux.do 帖子
把 https://linux.do/t/topic/2609603 做成手账风信息图

# 粘贴正文
帖子生图：下面是正文……直接出图

# 指定比例
按小红书 3:4 竖版，把这篇复盘做成仓鼠信息图

# 只要 prompt 不生图
只生成 prompt，先别调用 gen-img
```

## 目录约定

```text
~/.claude/skills/post-to-img/
  SKILL.md
  references/style-presets.md
  scripts/build_prompt.py
  scripts/run_gen.sh

项目同步（必须双向一致）：
  skills/post-to-img/   ← 与系统 skill 同步

产出：
  ~/Documents/learn-claude-code/generated-images/post-to-img/{slug}/
    source.md
    content.json
    prompt.txt
    prompt_en.txt
    prompt.meta.json
    poster.png
```

## 质量检查清单（出图前）

- [ ] 标题 ≤ 14 字，有情绪钩子  
- [ ] 三栏结构完整（情绪 / 能力 / 行动）  
- [ ] 每 bullet ≤ 28 字，总可见中文不过载  
- [ ] preset 视觉词已写入 prompt（奶油纸、草莓粉、仓鼠…）  
- [ ] size 已定为 `1536x1024` 或用户指定  
- [ ] 生图走 gen-img，未私自 curl API  

## 与参考帖对齐示例

输入：`https://linux.do/t/topic/2609603`《被优化了，第一天。》

期望结构：

1. 今天发生了什么（交接 → 通知优化 → 当天搞定）  
2. 内心感受（35+、一线、失眠看球…）  
3. 竞争力担忧（业务/技术/客户三面）  
4. AI 生产力跃迁表 + 工具箱（MCP/Skills/E2E…）  
5. 小尝试勾选（OAuth2 / Rust MD / 百度 Map…）  
6. 接下来计划  
7. 赚钱思路（openclaw / codex 皮肤隐喻）  
8. 给未来的自己 + 底部寄语  

风格：`kawaii-journal`，size `1536x1024`。

## 版本

- **v1.0.0**（2026-07-21）：首版。取文 → 结构化 → kawaii-journal prompt → gen-img；双向 skill 同步。
