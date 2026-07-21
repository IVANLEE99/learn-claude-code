# Claude Code Skill 详解：post-to-img

## 一、Skill 是什么

Skill（技能）是 Claude Code 的扩展机制，允许用户定义可复用的专业能力。它比 Command（命令）更强大：

| 特性 | Command | Skill |
|------|---------|-------|
| 调用方式 | 用户手动 `/command` | Claude 自动触发 + 用户手动 |
| 文件结构 | 单个 `.md` 文件 | 目录，含 `SKILL.md` + 脚本/参考资料 |
| 典型用途 | 动作型："帮我做 X" | 知识型 + 执行型："知道 X 并执行 X" |
| 可捆绑资源 | 不能 | 可以（脚本、模板、API 配置等） |

**一句话理解**：Command 是快捷操作按钮，Skill 是会自动识别场景并执行标准流程的领域专家。

本 skill 的定位：**上游内容编排**；真正的 API 出图仍交给 [gen-img](Claude-Code-Skill详解-gen-img.md)。

---

## 二、post-to-img Skill 说明

### 功能

把论坛帖子 / Markdown 长文 / 粘贴正文，自动变成「日系手账 × Q 版吉祥物」信息图：

1. **取文**：linux.do URL（Playwright）、公开 URL、本地文件、对话粘贴  
2. **结构化**：压成 6–8 个信息图友好区块（`content.json`）  
3. **选风格**：默认 `kawaii-journal`（奶油纸仓鼠手账风）  
4. **拼 Prompt**：`build_prompt.py` 生成中/英 prompt  
5. **生图**：**只调用 gen-img**，不私自 curl Images API  
6. **落盘展示**：`source.md` / `content.json` / `prompt.txt` / `poster.png` 同目录  

### 触发条件

当用户提到以下意图时自动触发：

- 帖子生图 / 长文转图 / 复盘信息图 / 手账风海报  
- 「把这个帖子做成图」「仿那张仓鼠信息图」  
- 给出 `linux.do/t/topic/...` 并要求配图 / 生图  
- post to image / forum post infographic  

**不触发**：与帖子无关的自由生图（「画一只猫」）→ 直接走 `gen-img`。

### 技术架构

```
用户: "把 https://linux.do/t/topic/2609603 做成手账风信息图"
        ↓
Claude 匹配触发词 → 激活 post-to-img
        ↓
[1] 取文（Playwright / Read / 粘贴）
        ↓
[2] 结构化 → content.json（左情绪 / 中能力 / 右行动）
        ↓
[3] 选 preset（默认 kawaii-journal）
        ↓
[4] build_prompt.py → prompt.txt + prompt_en.txt + prompt.meta.json
        ↓
[5] 可选确认（用户说「直接出图」则跳过）
        ↓
[6] run_gen.sh → bash ~/.claude/skills/gen-img/scripts/gen-img.sh
        ↓
[7] Read 展示 poster.png
```

与 gen-img 的关系：

| 层级 | Skill | 职责 |
|------|-------|------|
| 编排层 | **post-to-img** | 取文、摘要、版式、风格、prompt |
| 执行层 | **gen-img** | API Key、model、size、解码落盘 |

**铁律**：post-to-img **禁止**自己调用 `/v1/images/generations`；一律走 gen-img 脚本，复用 `GEN_IMG_*` 配置。

### 设计锚点

参考「被优化了，第一天」类手账信息图：

- 奶油米白纸底 + 草莓粉大标题  
- 圆角卡片三栏网格  
- Q 版仓鼠 / 白兔老师吉祥物  
- 温柔治愈、自嘲但不丧  

完整视觉 DNA 见 skill 内 [style-presets.md](post-to-img/references/style-presets.md)。

---

## 三、创建详细过程

### 第 1 步：明确边界

| 要做 | 不做 |
|------|------|
| 长文 → 信息图结构 | 替代 gen-img 调 API |
| 固定版式 + 风格预设 | 任意艺术风格自由画（那是 gen-img） |
| 字数压缩、bullet 化 | 原文整段塞进 prompt |

### 第 2 步：创建 Skill 目录结构

```bash
mkdir -p ~/.claude/skills/post-to-img/{scripts,references,examples}
mkdir -p skills/post-to-img/{scripts,references,examples}   # 项目同步
```

最终结构：

```
~/.claude/skills/post-to-img/          # 系统 skill（运行时）
skills/post-to-img/                    # 项目备份（须双向同步）
├── SKILL.md                           # 入口：触发 + 7 步流程
├── references/
│   └── style-presets.md               # kawaii-journal / clean-tech / warm-note
├── scripts/
│   ├── build_prompt.py                # content.json → prompt
│   └── run_gen.sh                     # 读 prompt → 调 gen-img
└── examples/
    └── 2609603.content.json           # linux.do 示例结构
```

### 第 3 步：编写 SKILL.md

核心包含：

1. **Frontmatter** — `name` / `description` / `version`  
2. **触发条件** — 与 gen-img 区分边界  
3. **依赖** — gen-img + Playwright + `GEN_IMG_*`  
4. **7 步流程** — 取文 → 结构化 → 风格 → prompt → 确认 → 生图 → 展示  
5. **linux.do 抽取 JS** — `#post_1 .cooked`  
6. **质量清单** — 标题字数、bullet 长度、唯一生图出口  

### 第 4 步：编写脚本

**`build_prompt.py`**

- 输入：`content.json` + `--preset` + 可选 `--textless`  
- 输出：`prompt.txt`（中文主）、`prompt_en.txt`、`prompt.meta.json`（size/quality）  
- 默认 size：`1536x1024`（横版信息图）  
- 规则：标题 ≤14 字、bullet ≤28 字、布局顶栏/三栏/底栏写死进 prompt  

**`run_gen.sh`**

```bash
# 读 slug 目录下 prompt.txt + prompt.meta.json
# 再调用：
bash ~/.claude/skills/gen-img/scripts/gen-img.sh \
  "$PROMPT" "$OUT/poster.png" "$SIZE" "$QUALITY" 1 png
```

### 第 5 步：风格预设

| preset | 说明 | 默认何时用 |
|--------|------|------------|
| `kawaii-journal` | 仓鼠手账奶油纸（默认） | 复盘、被优化、情绪向 |
| `clean-tech` | 浅灰蓝极简、无吉祥物 | 纯技术总结 |
| `warm-note` | 便签拼贴、少表格 | 短感想、金句 |

### 第 6 步：双向同步

与仓库其他 skill 一致：

```bash
# 项目 → 系统
rsync -a skills/post-to-img/ ~/.claude/skills/post-to-img/

# 系统 → 项目
rsync -a ~/.claude/skills/post-to-img/ skills/post-to-img/
```

改任一处后必须同步另一处，避免「对话触发的是旧版」。

### 第 7 步：环境依赖（复用 gen-img）

本 skill **不新增** API 变量。需已配置：

```json
{
  "env": {
    "GEN_IMG_API_URL": "https://your-api-endpoint.com",
    "GEN_IMG_API_KEY": "sk-your-api-key-here",
    "GEN_IMG_MODEL": "gpt-image-2"
  }
}
```

详见 [gen-img 详解](Claude-Code-Skill详解-gen-img.md) 第三节「配置环境变量」。

---

## 四、对话中的相关讨论

### Q: 为什么不直接让 gen-img 吃整篇帖子？

**A**: 长文直接当 prompt 会导致：

- 字墙、无分区，模型糊成一团  
- 缺少固定版式（三栏/吉祥物/色板）  
- 中文信息密度失控  

post-to-img 先做 **编辑式压缩 + 版式骨架**，再交给 gen-img，成功率更高。

### Q: 为什么必须调用 gen-img，不能自己 curl？

**A**:

- API URL / Key / Model 已在 gen-img 统一管理  
- 超时、b64 解码、落盘路径、错误信息一套逻辑  
- 换模型只改 `GEN_IMG_MODEL`，编排层零改动  

### Q: 生图中文标题总是乱怎么办？

**A**:

1. 先用默认带字 prompt 试一版  
2. 仍崩 → `build_prompt.py --textless` 出无字底板，再在 Figma/PS 叠 `content.json` 文案  
3. 标题尽量 ≤14 字，bullet ≤28 字  

### Q: linux.do 为什么要用 Playwright？

**A**: 站点常有登录墙 / Cloudflare / 403，`WebFetch` 易失败。Playwright 走已登录 MCP 浏览器，抽 `#post_1 .cooked` 最稳。

### Q: 和 ai-news-factory 有什么区别？

| | post-to-img | ai-news-factory |
|--|-------------|-----------------|
| 输入 | 单帖/长文复盘 | 日报/周报/月报 Markdown |
| 输出 | 一张信息图海报 | 短视频 + 多平台图文 |
| 生图 | 调 gen-img | 流水线内自有图片步骤 |
| 风格 | 手账仓鼠信息图 | B 站/短视频分镜风 |

---

## 五、文件内容

Skill 已备份至本项目 `skills/post-to-img/`，完整文件：

| 文件 | 说明 | 链接 |
|------|------|------|
| SKILL.md | 入口（触发 + 7 步） | [查看](post-to-img/SKILL.md) |
| style-presets.md | 视觉 DNA 与 preset | [查看](post-to-img/references/style-presets.md) |
| build_prompt.py | 结构化 → prompt | [查看](post-to-img/scripts/build_prompt.py) |
| run_gen.sh | 调 gen-img 出图 | [查看](post-to-img/scripts/run_gen.sh) |
| 2609603.content.json | 示例 content | [查看](post-to-img/examples/2609603.content.json) |

产出目录约定：

```text
~/Documents/learn-claude-code/generated-images/post-to-img/{slug}/
  source.md
  content.json
  prompt.txt
  prompt_en.txt
  prompt.meta.json
  poster.png
```

`slug` 示例：`20260721_2609603`（日期 + topic id）。

---

## 六、使用方式

### 自动触发（推荐）

```
用户: 把 https://linux.do/t/topic/2609603 做成手账风信息图
Claude: [取文 → 结构化 → prompt → 可选确认 → gen-img → 展示]

用户: 帖子生图，直接出图：
      <粘贴正文>
Claude: [跳过确认，跑完全流程]

用户: 只生成 prompt，先别调用 gen-img
Claude: [停在 Step 4，给出 prompt 路径]

用户: 按小红书竖版做成仓鼠信息图
Claude: [size 用 1024x1536]
```

### 手动调用脚本

```bash
SLUG=~/Documents/learn-claude-code/generated-images/post-to-img/20260721_2609603

# 1) 已有 content.json → 拼 prompt
python3 ~/.claude/skills/post-to-img/scripts/build_prompt.py \
  --content "$SLUG/content.json" \
  --preset kawaii-journal \
  --out-dir "$SLUG"

# 无字底板
python3 ~/.claude/skills/post-to-img/scripts/build_prompt.py \
  --content "$SLUG/content.json" \
  --preset kawaii-journal \
  --textless \
  --out-dir "$SLUG"

# 2) 调 gen-img 出图
bash ~/.claude/skills/post-to-img/scripts/run_gen.sh "$SLUG"
```

### 参数说明（build_prompt.py）

| 参数 | 默认 | 说明 |
|------|------|------|
| `--content` | 必填 | `content.json` 路径 |
| `--preset` | `kawaii-journal` | 风格预设 |
| `--out-dir` | 必填 | 输出目录 |
| `--textless` | off | 布局占位、少渲染正文汉字 |
| `--size` | preset 默认 `1536x1024` | 写入 `prompt.meta.json` |

### content.json 最小字段

```json
{
  "title": "被优化了，第一天",
  "subtitle": "接受现实，复盘自己，拥抱AI，创造更多可能！",
  "hook": "生活不会突然变好，但你可以选择让自己变得更强",
  "sections": [
    { "id": 1, "heading": "今天发生了什么", "bullets": ["..."], "mascot_mood": "crying" }
  ],
  "table": { "title": "...", "headers": [], "rows": [] },
  "toolbox": [],
  "trials": [],
  "plan": [],
  "money_ideas": [],
  "letter_to_future": "...",
  "tip": "...",
  "closing": "...",
  "cta": "..."
}
```

`mascot_mood` 可选：`crying | sad | dizzy | focus-laptop | coins | reading | pray | heart | teacher-rabbit | sweat`。

---

## 七、测试结果

### 测试 1：linux.do 帖子取文 + 结构化 + prompt（2026-07-21）

| 项 | 结果 |
|----|------|
| 源帖 | https://linux.do/t/topic/2609603 《被优化了，第一天。》 |
| 取文 | Playwright 成功，作者 wkcause |
| 结构化 | 左 3 情绪卡 + AI 跃迁表 + 工具箱 + 小尝试 + 计划/赚钱/寄语 |
| prompt.txt | ~3.7KB 中文主 prompt |
| prompt_en.txt | ~1.2KB 英文备用 |
| 产出路径 | `generated-images/post-to-img/20260721_2609603/` |
| 双向同步 | `skills/` ↔ `~/.claude/skills/` 一致 |

**本轮未强制调用 gen-img 出图**（用户中断 API 调用）；prompt 链路已打通。需要出图时执行：

```bash
bash ~/.claude/skills/post-to-img/scripts/run_gen.sh \
  ~/Documents/learn-claude-code/generated-images/post-to-img/20260721_2609603
```

### 测试总结

| 测试项 | 结果 |
|--------|------|
| linux.do 抓正文 | 成功 |
| content.json 示例 | 成功 |
| build_prompt 中英文 | 成功 |
| run_gen → gen-img | 脚本就绪（待用户授权 API 调用） |
| skill 双向同步 | 成功 |

---

## 八、扩展方向

### 短期

1. **一键竖版模板** — 小红书 3:4 / `1024x1536` 专用布局词  
2. **无字底板 + 自动叠字** — 本地 Pillow/HTML 渲染中文（避开模型糊字）  
3. **批量帖子** — 多个 topic id 串行出图  

### 中期

1. **风格参考图 img2img** — 若 gen-img 扩展 edits 端点，用仓鼠海报作 style ref  
2. **与 publish-issue 串联** — 出图后一键发 GitHub Issue  
3. **content 质量自检** — bullet 过长自动截断告警  

### 长期

1. 更多 preset（极简黑白、赛博、政务风）  
2. 多页长图（故事分镜条）  
3. 作为 MCP tool 暴露「post → image」  

---

## 九、相关资源

- 本 skill 入口: [post-to-img/SKILL.md](post-to-img/SKILL.md)  
- 生图底层: [Claude-Code-Skill详解-gen-img.md](Claude-Code-Skill详解-gen-img.md)  
- 风格预设: [post-to-img/references/style-presets.md](post-to-img/references/style-presets.md)  
- Claude Code 官方文档: https://docs.anthropic.com/en/docs/claude-code  
- 示例帖: https://linux.do/t/topic/2609603  

---

## 十、版本

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-07-21 | 首版：取文 → 结构化 → kawaii-journal prompt → gen-img；双向同步 |
