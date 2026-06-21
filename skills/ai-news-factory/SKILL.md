---
name: ai-news-factory
description: AI News Factory - 从日报 Markdown 自动生成短视频+图文的完整 Pipeline。触发词: "AI日报", "新闻工厂", "news factory", "日报视频", "生成日报视频", "AI news video"
version: 2.6.0
---

# AI News Factory — 日报短视频自动生成 v2.5.0

将 AI 日报 Markdown 自动转化为 B站风格短视频 + 多平台发布内容，完整 Pipeline：日报 → 去重 → 事件切分 → 视频脚本 → 分镜 → 图片 → TTS → 字幕 → 视频合成 → 封面 → 多平台发布信息 → 公众号图文 → 多平台上传。

**核心原则：原始脚本文本 + ffprobe 时长比例对齐，确保字幕 100% 准确且与音频精确同步。**

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

🖥️ 浏览器操作（全部平台上传）
  ☐ B站：自动上传视频、封面、填写标题/简介/标签、选择合集、投稿
  ☐ 抖音：自动上传视频、封面、填写描述、选择合集、发布
  ☐ 视频号：自动上传视频、封面、填写描述/短标题、选择合集
  ☐ 公众号：自动创建文章、填写标题/正文、上传封面、声明原创、选择合集

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
- "破格模式", "破格元素", "破格风格", "元素破格"

## 周报模式

**当触发词包含"周报"或"weekly"时，进入周报模式：**

### 周报与日报的区别

| 项目 | 日报 | 周报 |
|------|------|------|
| 数据源 | 单日日报 | 7天日报汇总 |
| 输出目录 | `news-pipeline/YYYY-MM-DD/` | `news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD/` |
| 封面提示词 | 单日事件 | 本周多事件拼贴 |
| 视频脚本 | 3-5个当日事件 | 5-6个本周核心事件 |
| 过滤规则 | 无 | **过滤公益站/中转站/倒卖相关内容** |
| 标题格式 | `【今日羊报AI】...` | `【羊报AI周刊】...` |

### 周报生成流程

1. **读取本周日报**：读取 `data/reports/` 目录下最近7天的日报文件
2. **提取关键事件**：每天选出1-2个最重要事件，过滤公益站相关内容
3. **生成周报 Markdown**：输出到 `news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD.md`
4. **生成周报封面**：使用周报专用封面提示词（多事件拼贴风格）
5. **生成视频脚本**：5-6个本周核心事件，总时长90-120秒
6. **后续流程**：与日报相同（分镜→图片→TTS→字幕→视频→上传）

### 周报封面提示词模板

```
A professional Chinese AI news studio weekly cover image. A male news anchor in a dark navy suit sits at a modern curved news desk. Behind him are multiple large display screens showing: {本周核心事件相关视觉元素}. The studio has dramatic blue and red neon lighting. In the top right corner, display the text "羊报AI周刊" on the first line and "AI 新闻" on the second line in large white Chinese characters. In the bottom center, display the date range "{YYYY-MM-DD} ~ {YYYY-MM-DD}" in large white bold text. Professional broadcast news photography style, photorealistic, highly detailed, cinematic lighting, 16:9 aspect ratio.
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

- `REPORT_PATH`: 日报文件路径
- `API_URL`: 图片生成 API URL
- `API_KEY`: 图片生成 API Key
- `UPLOAD_PLATFORMS`: 上传平台列表
- `STYLE_MODE`: 风格模式（standard / poge），默认 standard

如信息不完整，在此处补充询问。

### Phase 1: 输入、去重与事件切分

**Step 1.1**: 读取今日日报内容。

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

### Phase 2: 视频脚本生成

对每个选中事件，按模板生成脚本。

**风格要求**:
- **🔴 说人话！** 像跟朋友聊天一样，不要播音腔、不要堆砌术语、口语化、有温度
- 像 B站 AI 科技 UP 主
- 快节奏、有情绪、不书面
- 总时长 60-120 秒（可适当放宽到 150s）
- 每段不超过 80 字
- 保留争议性与情绪感

**输出结构**:
```
标题：{标题}
Hook：{开场钩子，5秒内抓住注意力}

正文：
{段落1 - 引入}
{段落2 - 核心信息}
{段落3 - 争议/反转}
{段落4 - 深入}

结尾：{CTA 引导互动}
```

**🔴 重要：保存每个场景的 TTS 文本**，Phase 7 字幕生成需要直接使用这些文本（不用 ASR 识别）。

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

**🔴 禁止使用的词汇**：文案和字幕中不得出现以下词汇，需替换为通用称呼：
- 「佬友」→「大家」「朋友们」
- 「Linuxdo」→「社区」「论坛」
- 「L站」→「社区」「论坛」

**🔴 用户审核步骤**：脚本生成后，必须将完整脚本展示给用户审核，获得确认后才能进入 Phase 3。用户可能要求修改某些场景的文案。

**参考模板**: `templates/script-template.md`

### Phase 3: 分镜生成

根据视频脚本生成分镜表，每个脚本段落对应 1 个分镜。

| 镜号 | 时长 | 镜头类型 | 画面内容 | 字幕重点 | 转场 |
|------|------|----------|----------|----------|------|
| 1 | 3s | 特写 | AI 芯片电路 | Hook 文字 | 淡入 |
| 2 | 5s | 全景 | 科技新闻编辑室 | 事件标题 | 切换 |

**参考模板**: `templates/storyboard-template.md`

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
- **必须逐张生成**：API 有并发限制
- **必须从 JSON 文件读取 Prompt**，不能用简化版本
- 每张图片生成后重试一次（如果失败）
- **HTTP API 优先**：HTTP（如 luka77）比 HTTPS 更稳定，避免 SSL/DNS 问题
- **超时设置**：图片生成可能需要 30-120 秒，`--max-time` 设为 300
- **DNS 劫持**：如遇连接超时，用 `nslookup` + `curl --resolve` 绕过

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

COVER_PROMPT = """A professional Chinese AI news studio cover image. A male news anchor in a dark navy suit with white shirt and dark tie sits at a modern curved news desk, hands clasped, looking directly at camera with serious expression. Behind him are multiple large display screens arranged in a grid showing: {本期核心新闻相关的视觉元素}. The studio has dramatic blue and red neon lighting, with red accent lights along the desk edges and blue ambient lighting. In the top right corner, display the text "今日羊报 AI" on the first line and "AI 新闻" on the second line in large white Chinese characters. In the bottom center, display the date "{YYYY-MM-DD}" in large white bold text. Professional broadcast news photography style, photorealistic, highly detailed, cinematic lighting, {ratio} aspect ratio."""

# 封面配置
COVERS = [
    {"name": "cover.png", "size": "1536x1024", "ratio": "16:9"},           # 通用封面
    {"name": "bilibili-4-3.png", "size": "1536x1152", "ratio": "4:3"},     # B站
    {"name": "wechat-21-9.png", "size": "1536x659", "ratio": "21:9"},     # 公众号
    {"name": "douyin-horizontal-4-3.png", "size": "1536x1152", "ratio": "4:3"},  # 抖音横版
    {"name": "douyin-vertical-3-4.png", "size": "1152x1536", "ratio": "3:4"},    # 抖音竖版
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
# 应该输出 5（cover.png, bilibili-4-3.png, wechat-21-9.png, douyin-horizontal-4-3.png, douyin-vertical-3-4.png）
```

**优势**：
- 封面生成（5个，约 3-5 分钟）与 TTS 配音（9个，约 2-3 分钟）并行
- 总时间从串行的 6-8 分钟缩短到并行的 3-5 分钟
- 每张封面自动重试一次，提高成功率

### Phase 6: TTS 配音

根据视频脚本逐场景生成配音：

```bash
bash ~/Documents/learn-claude-code/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "配音文本" \
  --voice "白桦" \
  --style "新闻播报" \
  --output "news-pipeline/YYYY-MM-DD/voiceover/sceneN.wav"
```

**🔴 关键限制：mimo-tts.sh 使用 `mktemp` 生成临时文件，并行调用会导致文件名冲突和静默失败。必须逐场景串行执行！**

**配音要求**:
- 推荐音色: **白桦**（预置音色，效果最佳）
- **🔴 重要：使用 `--voice "白桦"` 而非 `--profile "白桦"`！`--profile` 只能使用本地 profiles.json 中已保存的克隆音色（曼波/阿根），预置音色必须用 `--voice` 参数。**
- **🔴 重要：优先使用预置音色（白桦/苏打/冰糖/茉莉），不要使用克隆音色（曼波/阿根）！克隆音色在新闻播报场景下听起来太机械、不自然。**
- **🔴 TTS API 直接调用**：如果 mimo-tts.sh 报错缺少 MIMO_TTS_API_KEY，直接用 Python+curl 调用 MiMo TTS API（见下方代码）
- **必须逐场景串行生成**（不要并行！）
- 按场景生成音频文件（scene1.wav, scene2.wav, ...）
- 每个场景的文本来自视频脚本对应段落
- 结束语（"今天AI圈真是又热闹又魔幻..."）作为最后一个场景

**获取音频时长**:

```bash
for i in 1 2 3 4 5 6 7; do
  duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "news-pipeline/YYYY-MM-DD/voiceover/scene${i}.wav" 2>/dev/null)
  echo "scene${i}: ${duration}s"
done
```

**TTS API 直接调用（备选方案）**:

如果 mimo-tts.sh 报错 `MIMO_TTS_API_KEY not found`，直接用 Python 调用 MiMo TTS API：

```python
import json, subprocess, base64, tempfile, os, time

API_URL = "https://token-plan-cn.xiaomimimo.com"  # 用户提供
API_KEY = "用户提供的 TTS API Key"
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

### Phase 7: 字幕生成（原始脚本文本 + ffprobe 比例对齐）

**v2.1.0 方案：使用原始脚本文本 + ffprobe 时长比例对齐（默认方案）。**

> **🔴 经验教训（2026-06-12）**：FunASR 对专业术语识别极差（GPT→GDP、DeepSeek→Deep triep、Claude Code→Claude coat、Fable-5→核酸efbo杠五、Codex→搞dex、Hermes→HMMI、MiMo→mini/明末），修正字典永远追不上新术语。**直接使用原始 TTS 脚本文本 + ffprobe 时长比例分配，字幕 100% 准确。**

#### 7.1 默认方案：原始脚本文本 + ffprobe 对齐

```python
import json, subprocess, re, os

def get_audio_duration(wav_path):
    """获取音频实际时长（毫秒）"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", wav_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip()) * 1000

# 原始脚本文本（从 Phase 2 视频脚本中提取每个场景的 TTS 文本）
SCENE_TEXTS = {
    1: "场景1的TTS文本...",
    2: "场景2的TTS文本...",
    # ... 每个场景的完整 TTS 文本
}

def split_by_punctuation(text):
    """按中文标点分割文本，标点保留在前一句"""
    parts = re.split(r'(?<=[。！？，；：])', text)
    return [p.strip() for p in parts if p.strip()]

def generate_captions_from_script(base_dir, scene_count=8):
    """使用原始脚本文本 + ffprobe 时长比例生成字幕"""
    all_captions = []
    global_offset_ms = 0

    for scene_num in range(1, scene_count + 1):
        wav_path = os.path.join(base_dir, "voiceover", f"scene{scene_num}.wav")
        if not os.path.exists(wav_path):
            continue

        # 获取实际音频时长
        audio_duration_ms = get_audio_duration(wav_path)

        # 使用原始脚本文本（100% 准确）
        text = SCENE_TEXTS.get(scene_num, "")
        if not text:
            global_offset_ms += audio_duration_ms
            continue

        # 按标点分割
        sentences = split_by_punctuation(text)
        if not sentences:
            global_offset_ms += audio_duration_ms
            continue

        # 按字符比例分配时间（排除标点计算比例）
        char_counts = [len(re.sub(r'[。！？，；：、]', '', s).replace(" ", "")) for s in sentences]
        total_chars = sum(char_counts) if sum(char_counts) > 0 else len(sentences)

        relative_ms = 0
        for sent, chars in zip(sentences, char_counts):
            proportion = chars / total_chars
            duration = audio_duration_ms * proportion

            all_captions.append({
                "text": sent,
                "startMs": round(global_offset_ms + relative_ms),
                "endMs": round(global_offset_ms + relative_ms + duration)
            })
            relative_ms += duration

        global_offset_ms += audio_duration_ms

    return all_captions
```

#### 7.2 完整流程

```
视频脚本(Phase 2) → 提取每个场景TTS文本 → ffprobe获取每个音频实际时长
    → 按标点分割文本 → 按字符比例分配时间 → 输出 captions.json
```

**关键点**：
- **直接使用原始脚本文本**，不需要 ASR 识别，字幕 100% 准确
- **必须用 ffprobe 获取音频实际时长**，按比例分配确保总时长对齐
- **标点分割后按字符比例分配**，每个场景内部时间轴精确

**字体使用规范**：
- 使用系统字体：`"PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif`
- 字幕：40-48px，加粗，白色，黑色半透明背景
- **禁止使用商用字体**（方正、汉仪、造字工房等）

### Phase 8: 渲染前校验（必须执行）

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

#### Step 8.3: 更新 Root.tsx

```tsx
const TOTAL_DURATION_SEC = 场景1时长 + 场景2时长 + ... + 场景N时长;
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
  "out/【今日羊报AI】{核心标题} | YYYY-MM-DD.mp4" \
  --codec h264 --crf 18 \
  --public-dir /Users/youngsdream/Documents/learn-claude-code/news-pipeline/video-project/public
```

**关键参数说明**：
- `node_modules/.bin/remotion`：使用 video-project 下的本地 remotion
- `src/index.ts`：必须指定入口点文件路径
- `--public-dir`：必须指定 public 目录的绝对路径

**🔴 渲染输出位置（必须记住）**：
- 视频渲染到：`/Users/youngsdream/Documents/learn-claude-code/out/`
- **不是** `news-pipeline/video-project/out/`

**🔴 视频合成后自动归档（必须执行）**：

视频渲染完成后，必须立即将视频从根目录 `out/` 复制到日报目录：

```bash
# 复制视频到日报目录（从根目录 out/ 复制）
cp "/Users/youngsdream/Documents/learn-claude-code/out/【今日羊报AI】{核心标题} | YYYY-MM-DD.mp4" \
   "/Users/youngsdream/Documents/learn-claude-code/news-pipeline/YYYY-MM-DD/video/"

# 验证复制成功
ls -la "/Users/youngsdream/Documents/learn-claude-code/news-pipeline/YYYY-MM-DD/video/"
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
| 通用/视频封面 | 16:9 | 1536x1024 | `cover.png` | 视频封面、B站默认 |
| B站 | 4:3 | 1536x1152 | `bilibili-4-3.png` | B站投稿封面 |
| 公众号 | 21:9 | 1536x659 | `wechat-21-9.png` | 公众号文章封面 |
| 抖音横版 | 4:3 | 1536x1152 | `douyin-horizontal-4-3.png` | 抖音视频封面 |
| 抖音竖版 | 3:4 | 1152x1536 | `douyin-vertical-3-4.png` | 抖音个人主页卡片 |

**封面模板 Prompt**：
```
A professional Chinese AI news studio cover image. A male news anchor in a dark navy suit with white shirt and dark tie sits at a modern curved news desk, hands clasped, looking directly at camera with serious expression. Behind him are multiple large display screens arranged in a grid showing: {本期核心新闻相关的视觉元素}. The studio has dramatic blue and red neon lighting, with red accent lights along the desk edges and blue ambient lighting. In the top right corner, display the text "今日羊报 AI" on the first line and "AI 新闻" on the second line in large white Chinese characters. In the bottom center, display the date "{YYYY-MM-DD}" in large white bold text. Professional broadcast news photography style, photorealistic, highly detailed, cinematic lighting, {ratio} aspect ratio.
```

输出到 `news-pipeline/YYYY-MM-DD/` 目录

#### 10.2 生成多平台发布信息

生成 `news-pipeline/YYYY-MM-DD/publish.json`，包含 B站、抖音、视频号、公众号四个平台：

```json
{
  "title": "【今日羊报AI】{核心标题} | YYYY-MM-DD",
  "description": "视频简介，2-3句话概括本期内容",
  "tags": ["今日羊报AI", "AI日报", "..."],
  "platform": {
    "bilibili": {
      "title": "【今日羊报AI】{核心标题}｜{N}条重磅AI新闻一次看完 | YYYY-MM-DD",
      "tags": ["今日羊报AI", "AI日报", "..."],
      "description": "B站简介，含 hashtag"
    },
    "douyin": {
      "title": "{核心标题}｜今日羊报AI YYYY-MM-DD",
      "tags": ["AI日报", "..."],
      "description": "抖音简介，含 hashtag"
    },
    "channels": {
      "title": "{核心标题}｜今日羊报AI YYYY-MM-DD",
      "tags": ["AI日报", "..."],
      "description": "视频号简介，含 hashtag"
    },
    "wechat": {
      "title": "{核心标题}｜今日羊报AI YYYY-MM-DD",
      "article": "wechat-article-YYYY-MM-DD.md",
      "images": "wechat-images/"
    }
  }
}
```

**标题规则**:
- 日报 B站：`【今日羊报AI】{核心标题}｜{N}条重磅AI新闻一次看完 | YYYY-MM-DD`
- 日报 抖音/视频号：`{核心标题}｜今日羊报AI YYYY-MM-DD`（较短）
- 日报 公众号：`{核心标题}｜今日羊报AI YYYY-MM-DD`
- **周报 B站**：`【羊报AI周刊】{核心标题}｜本周{N}大AI新闻一次看完 | MM-DD~MM-DD`
- **周报 抖音/视频号**：`{核心标题}｜羊报AI周刊 MM-DD~MM-DD`
- **周报 公众号**：`{核心标题}｜羊报AI周刊 MM-DD~MM-DD`

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

**生成规则**：
- 标题使用视频标题
- 每个新闻事件一个 `##` 标题
- 正文从脚本段落中提取，去掉口语化表达（"今天"、"我们"、"大家"等）
- 每个事件配一张场景图片（scene2.png ~ sceneN.png，跳过 Hook 场景）
- 结尾替换为引导关注的 CTA

输出到：
- 文章：`news-pipeline/YYYY-MM-DD/wechat-article-YYYY-MM-DD.md`
- 配图：`news-pipeline/YYYY-MM-DD/wechat-images/sceneN.png`

#### 10.4 归档资源

```bash
mkdir -p news-pipeline/YYYY-MM-DD/{scripts,storyboards,prompts,images,voiceover,captions,video,wechat-images}
cp news-pipeline/video-project/out/【今日羊报AI】*.mp4 news-pipeline/YYYY-MM-DD/video/
```

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
browser_file_upload("news-pipeline/YYYY-MM-DD/video/【今日羊报AI】*.mp4")
```

**🔴 重要**：`browser_click` 使用 `target` 参数（ref 编号）比 `element` 文本描述更可靠。

#### 11.3 上传封面（两步流程）

```
browser_click(target=e328)  # 点击「封面设置」→ 打开封面编辑弹窗
browser_click(target=e656)  # 点击「上传封面」→ 触发 file chooser
browser_file_upload("news-pipeline/YYYY-MM-DD/cover.png")
browser_click(target=e715)  # 点击「完成」→ 确认封面
```

#### 11.4 设置创作声明（自定义下拉框）

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

#### 11.5 填写简介（Quill 编辑器）

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

#### 11.6 填写标签

```
# 标签输入框: textbox "按回车键Enter创建标签"
# 最多 10 个标签，每个标签输入后按 Enter 确认
tags = ["DeepSeek", "Anthropic", "Ideogram", "英伟达", ...]
for tag in tags:
    browser_type(target=e399, text=tag)
    browser_press_key("Enter")
```

#### 11.7 加入合集（自定义下拉框）

**🔴 合集选择器也是自定义下拉框，必须用 JS evaluate：**

```javascript
// 1. 点击打开下拉框
browser_click(target=e525)  // "请选择合集"

// 2. 用 JS 找到并点击选项
browser_evaluate("""() => {
  const options = document.querySelectorAll('li, div, span, p');
  for (const opt of options) {
    if (opt.textContent.trim() === '「今日羊报 AI」') {
      opt.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")
```

#### 11.8 确认投稿

```
browser_click(target=e552)  # 点击「立即投稿」
# 等待页面跳转到「稿件投递成功」
browser_wait_for("text=稿件投递成功")
```

#### B站上传组件操作总结（v1.4.0 实测）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 视频上传 | file chooser | `browser_click(ref)` → `file_upload` | ✅ 高 |
| 封面设置 | 弹窗 | 点击封面设置 → 上传封面 → file_upload → 完成 | ✅ 高 |
| 创作声明 | **自定义下拉框** | 点击 textbox → **JS evaluate 点击选项** | ⚠️ 必须用 JS |
| 分区 | 自定义下拉框 | 已有默认值，一般不需要改 | ✅ 高 |
| 标签 | 输入框 | `type` + `Enter`，最多 10 个 | ✅ 高 |
| 简介 | **Quill 编辑器** | **JS 注入 `.ql-editor`** | ⚠️ 必须用 JS |
| 合集 | **自定义下拉框** | 点击展开 → **JS evaluate 点击选项** | ⚠️ 必须用 JS |
| 投稿按钮 | 按钮 | `browser_click(ref)` | ✅ 高 |

**关键经验**：
1. **`browser_click(target=ref编号)` 比 `browser_click(element=文本描述)` 更可靠**
2. **所有自定义下拉框（创作声明、合集）必须用 `browser_evaluate` + JS 点击**
3. **Quill 编辑器必须用 JS 注入 `innerHTML` + dispatch `input` 事件**
4. **`browser_file_upload` 必须在 file chooser 对话框打开后才能调用**
5. **封面上传是两步流程：先点「封面设置」打开弹窗，再点「上传封面」触发 file chooser**

### Phase 12: 微信公众号自动上传（Playwright MCP）

**权限已在预授权阶段获得，直接执行。**

**🔴 重要经验：公众号编辑器使用 ProseMirror + 自定义 Vue 组件，自动化难度较高。封面选择、合集选择等需要特殊处理。**

#### 12.0 完整上传流程（推荐顺序）

```
1. 打开公众号后台 → 点击「新的创作」→「文章」（新标签页打开）
2. 切换到新标签页
3. 填写标题（ProseMirror）+ 作者（标准 input）
4. 点击正文区域获取 focus → 插入视频号内容
5. 填写正文内容（ProseMirror innerHTML）
6. 通过「图片」→「本地上传」插入封面图到正文
7. 上传封面（从正文选择 / 从图片库选择）
8. 设置原创声明
9. 设置赞赏
10. 选择合集
11. 保存草稿
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

#### 12.3 填写标题和作者

**🔴 公众号标题使用 ProseMirror 编辑器，不是标准 input：**

```javascript
browser_run_code_unsafe("""async (page) => {
  const result = await page.evaluate(() => {
    const editors = document.querySelectorAll('.ProseMirror');
    // 第一个 ProseMirror 是标题
    if (editors[0]) {
      editors[0].textContent = '标题内容';
      editors[0].dispatchEvent(new Event('input', { bubbles: true }));
    }
    // 作者是标准 input
    const authorInput = document.querySelector('input[placeholder="请输入作者"]');
    if (authorInput) {
      authorInput.value = 'Youngs羊示';
      authorInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
    return 'title and author set';
  });
  return result;
}""")
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

**🔴 正文使用 ProseMirror 编辑器，用 innerHTML 注入：**

```javascript
browser_run_code_unsafe("""async (page) => {
  const result = await page.evaluate(() => {
    const editors = document.querySelectorAll('.ProseMirror');
    const bodyEditor = editors[1];  // 第二个 ProseMirror 是正文
    if (!bodyEditor) return 'body editor not found';
    bodyEditor.innerHTML = `
      <h2>1. 新闻标题</h2>
      <p>正文内容...</p>
      <h2>2. 新闻标题</h2>
      <p>正文内容...</p>
    `;
    bodyEditor.dispatchEvent(new Event('input', { bubbles: true }));
    return 'body content set';
  });
  return result;
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

#### 12.7 上传封面（已验证流程 v1.9.1）

**🔴 推荐流程：先上传图片到正文，再通过「从正文选择」设置封面。**

```
# 步骤1：上传封面图到正文（通过工具栏「图片」→「本地上传」）
# 点击正文区域获取 focus
browser_click(target={正文段落ref})

# 点击工具栏「图片」按钮（动态查找坐标）
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const items = document.querySelectorAll('li, a, span');
    for (const item of items) {
      if (item.textContent.trim() === '图片' && item.offsetParent !== null) {
        const rect = item.getBoundingClientRect();
        if (rect.y < 50 && rect.y > 0) { item.click(); return; }
      }
    }
  });
  await page.waitForTimeout(1500);
  // 点击「本地上传」
  await page.evaluate(() => {
    const items = document.querySelectorAll('*');
    for (const item of items) {
      if (item.textContent.trim() === '本地上传' && item.offsetParent !== null) {
        item.click(); return;
      }
    }
  });
  return 'clicked';
}""")

# 等待 file chooser 出现后上传
browser_file_upload("news-pipeline/YYYY-MM-DD/wechat-21-9.png")

# 步骤2：Hover 封面区域，显示选项菜单
browser_hover(target={拖拽或选择封面ref})

# 步骤3：点击「从正文选择」（必须用 class 选择器）
browser_evaluate("""() => {
  const btn = document.querySelector('.js_selectCoverFromContent');
  if (btn) { btn.click(); return 'clicked'; }
  return 'not found';
}""")

# 步骤4：在弹窗中点击图片选择（出现勾选标记）
browser_run_code_unsafe("""async (page) => {
  await page.mouse.click(313, 340);  // 图片位置
  await page.waitForTimeout(1000);
  return 'selected';
}""")

# 步骤5：点击「下一步」
browser_evaluate("""() => {
  const buttons = document.querySelectorAll('button, a');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '下一步' && btn.offsetParent !== null) {
      btn.click(); return 'clicked';
    }
  }
  return 'not found';
}""")

# 步骤6：确认裁剪
browser_evaluate("""() => {
  const buttons = document.querySelectorAll('button, a');
  for (const btn of buttons) {
    const text = btn.textContent.trim();
    if ((text === '确定' || text === '确认') && btn.offsetParent !== null) {
      btn.click(); return 'clicked: ' + text;
    }
  }
  return 'not found';
}""")

# 步骤7：保存草稿
browser_click(target={保存为草稿按钮ref})
```

**🔴 关键经验（v1.9.1 新增）：**
1. **必须先通过工具栏「图片」→「本地上传」将封面图插入正文**，否则「从正文选择」不可用
2. **Hover 封面区域才能显示选项菜单**，直接 click 不会触发
3. **「从正文选择」必须用 `.js_selectCoverFromContent` class 选择器**，普通文本匹配找不到
4. **弹窗中点击图片后会出现勾选标记**，然后才能点「下一步」
5. **裁剪弹窗点击「确认」**即可，不需要调整裁剪区域

#### 12.8 设置原创声明（已验证 v1.9.1）

**🔴 弹窗打开后「文字原创」和「我已阅读并同意」已默认选中，直接点确定即可。**

```
# 步骤1：点击「原创」区域打开弹窗
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent.trim() === '原创' && el.offsetParent !== null) {
        const rect = el.getBoundingClientRect();
        if (rect.y > 150 && rect.y < 400 && rect.x > 500) {
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

# 步骤3：直接点击「确定」（弹窗已默认选中文字原创+同意协议）
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
- 弹窗打开后「文字原创」已默认选中
- 「我已阅读并同意」checkbox 已默认勾选
- 直接点击「确定」即可，无需手动操作其他选项
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

# 步骤2：点击输入框 focus
browser_run_code_unsafe("""async (page) => {
  const input = page.getByRole('textbox', { name: '请选择合集' });
  await input.click();
  await page.waitForTimeout(500);
  await input.fill('今日羊报');
  await page.waitForTimeout(1000);
  return 'typed';
}""")

# 步骤3：hover 并点击选项（必须用 exact: true 精确匹配！）
browser_run_code_unsafe("""async (page) => {
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

```
browser_run_code_unsafe("""async (page) => {
  const saveBtn = page.locator('button:has-text("保存为草稿")');
  await saveBtn.first().click();
  await page.waitForTimeout(3000);
  return 'saved as draft';
}""")
```

#### 微信公众号上传组件操作总结（v1.7.0 实测）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 标题 | **ProseMirror** | JS 注入 `textContent` | ✅ 高 |
| 作者 | 标准 input | `value` + dispatch `input` | ✅ 高 |
| 正文 | **ProseMirror** | JS 注入 `innerHTML` | ✅ 高 |
| 视频号 | 弹窗选择 | 工具栏「视频号」→ 选账号 → 选视频 → 插入 | ✅ 高 |
| 图片上传 | 工具栏菜单 | 「图片」→「本地上传」→ file_upload | ✅ 高 |
| 封面 | 拖拽区域 | 「从图片库选择」/ 「从正文选择」 | ⚠️ 需坐标点击 |
| 原创声明 | 弹窗 | 点击「原创」→ 确定 | ✅ 高 |
| 赞赏 | 弹窗 | 点击「赞赏」→ 不开启 → 勾选同意 → 确定 | ✅ 高 |
| 合集 | **自定义 Vue 组件** | 坐标点击下拉框 → 选择 → 确认 | ⚠️ 坐标方式 |
| 保存草稿 | 按钮 | `button:has-text("保存为草稿")` | ✅ 高 |

**关键经验**：
1. **公众号编辑器使用 ProseMirror**，不是 Quill，注入方式不同
2. **标题和正文都是 ProseMirror**，通过 `document.querySelectorAll('.ProseMirror')` 获取，第一个是标题，第二个是正文
3. **视频号插入是最可靠的视频方式**，通过工具栏「视频号」按钮 → 选择账号 → 选择视频 → 插入
4. **图片通过工具栏「图片」→「本地上传」插入**，会插入到正文光标位置
5. **「从正文选择」封面**：必须先通过工具栏上传图片到正文，然后用 `.js_selectCoverFromContent` class 选择器点击
6. **合集选择器是自定义 Vue 组件**，需要用坐标点击（约 x=730, y=355 点击「未添加」，x=690, y=375 打开下拉框）
7. **赞赏弹窗中「我已阅读并同意」需要手动勾选**，checkbox 在 `label > input[type="checkbox"]` 结构中
8. **原创声明弹窗会自动选中「文字原创」+ 勾选同意**，直接点确定即可
9. **保存草稿前不需要完成所有设置**，封面和合集可以后续手动添加
10. **新标签页打开**：点击「文章」会打开新标签页，需要切换到最新标签页

#### 12.3 填写作者

```javascript
// 作者是标准 input，可以直接 type
browser_click(target={作者输入框ref})
browser_type(target={作者输入框ref}, text="Youngs羊示")
```

#### 12.4 填写正文

**🔴 公众号正文也是 ProseMirror 编辑器，必须用 JS 注入 innerHTML：**

```javascript
browser_evaluate("""() => {
  const editors = document.querySelectorAll('.ProseMirror');
  const bodyEditor = editors.length > 1 ? editors[1] : editors[0];  // 第二个是正文
  if (bodyEditor) {
    bodyEditor.innerHTML = `
      <h2>1. 新闻标题</h2>
      <p>正文内容...</p>
      <h2>2. 新闻标题</h2>
      <p>正文内容...</p>
    `;
    bodyEditor.dispatchEvent(new Event('input', { bubbles: true }));
    return 'body content set';
  }
  return 'editor not found';
}""")
```

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
| 标题 | **ProseMirror** | JS 注入 `textContent` | ✅ 高 |
| 作者 | 标准 input | `browser_type` | ✅ 高 |
| 正文 | **ProseMirror** | JS 注入 `innerHTML` | ✅ 高 |
| 图片上传 | **隐藏 file input** | `setInputFiles`（但不插入文章） | ⚠️ 需手动插入 |
| 封面 | 拖拽区域 | 需手动上传 | ❌ 建议手动 |
| 合集 | **自定义 Vue 组件** | JS click（不稳定） | ❌ 建议手动 |
| 保存草稿 | 按钮 | JS click | ✅ 高 |

**关键经验**：
1. **公众号编辑器使用 ProseMirror**，不是 Quill，注入方式不同
2. **标题和正文都是 ProseMirror**，通过 `document.querySelectorAll('.ProseMirror')` 获取，第一个是标题，第二个是正文
3. **图片上传到素材库成功，但不会自动插入文章**，需要手动定位光标后插入
4. **合集选择器是自定义 Vue 组件**，JS click 不稳定，建议手动
5. **保存草稿前不需要完成所有设置**，可以先保存再编辑

### Phase 13: 微信视频号自动上传（Playwright MCP）

**权限已在预授权阶段获得，直接执行。**

**🔴 重要经验：视频号编辑器使用 iframe + 自定义 React 组件，自动化难度较高。必须先检测 iframe 结构。**

#### 13.0 检测 iframe 结构（关键步骤）

**🔴 视频号页面内容在 iframe 中渲染！必须先检测 iframe 才能操作表单元素。**

```javascript
// 检测 iframe 结构
browser_run_code_unsafe("""async (page) => {
  const frames = page.frames();
  const frameInfo = frames.map(f => ({ url: f.url().substring(0, 80), name: f.name() }));
  return JSON.stringify(frameInfo);
}""")
```

**常见 iframe 结构**：
- 主页面：`https://channels.weixin.qq.com/platform/post/...`
- 内容 iframe：`name="content"`, URL 包含 `/micro/content/post/...`

**操作 iframe 内容时必须用 `page.frame({ name: 'content' })`**：
```javascript
browser_run_code_unsafe("""async (page) => {
  const frame = page.frame({ name: 'content' });
  if (!frame) return 'frame not found';
  const result = await frame.evaluate(() => {
    // 在 iframe 内操作 DOM
    return document.querySelector('.some-class')?.textContent;
  });
  return result;
}""")
```

#### 13.1 打开视频号发布页

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

```
# 点击上传区域（+号按钮）触发 file chooser
browser_run_code_unsafe("""async (page) => {
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser', { timeout: 5000 }),
    page.locator('.finder-upload__add-btn, [class*="upload-btn"]').first().click({ force: true })
  ]);
  await fileChooser.setFiles('news-pipeline/YYYY-MM-DD/video/【今日羊报AI】*.mp4');
  return 'uploaded';
}""")

# 等待上传完成（15MB 视频约需 10-15 秒）
browser_wait_for(time=15)
```

#### 13.3 填写视频描述（坐标方式）

**🔴 视频号描述使用自定义 contenteditable div，标准选择器找不到。必须用坐标点击 + 键盘输入：**

```javascript
browser_run_code_unsafe("""async (page) => {
  // 1. 点击描述区域（根据截图估算坐标）
  await page.mouse.click(990, 420);  // x=990, y=420 附近
  await page.waitForTimeout(500);
  // 2. 键盘输入描述
  await page.keyboard.type('描述内容');
  await page.waitForTimeout(500);
  return 'description filled';
}""")
```

**坐标估算方法**：截图后根据「视频描述」标签位置，描述输入框在其右侧约 200px 处。

#### 13.4 填写短标题

**🔴 短标题是 contenteditable div（不是标准 input），在 iframe 中！必须用 JS 在 iframe 内操作：**

```javascript
// 方法1：坐标点击 + 键盘输入（推荐）
browser_run_code_unsafe("""async (page) => {
  await page.mouse.click(990, 550);  // 短标题区域坐标
  await page.waitForTimeout(300);
  await page.keyboard.type('标题内容');
  return 'typed';
}""")

// 方法2：在 iframe 内用 JS 直接修改（更可靠）
browser_run_code_unsafe("""async (page) => {
  const frame = page.frame({ name: 'content' });
  if (!frame) return 'frame not found';
  const result = await frame.evaluate(() => {
    const div = document.querySelector('.edit-shorttitle-content');
    if (div) {
      div.textContent = '新标题内容';
      div.dispatchEvent(new Event('input', { bubbles: true }));
      return 'updated: ' + div.textContent;
    }
    return 'div not found';
  });
  return result;
}""")
```

**短标题限制**：最多 16 个中文字符，超过会报错「标题超过16字限制」。

#### 13.5 选择合集

```javascript
browser_run_code_unsafe("""async (page) => {
  // 1. 点击合集下拉框
  const dropdown = page.locator('text=选择合集').first();
  await dropdown.click();
  await page.waitForTimeout(1000);
  // 2. 用坐标点击选项（根据截图调整）
  await page.mouse.click(880, 420);
  await page.waitForTimeout(500);
  return 'selected';
}""")
```

#### 13.6 上传封面和短标题（在 iframe 中操作）

**🔴 视频号页面内容在 iframe 中，必须用 `page.frame({ name: 'content' })` 操作！**

##### 13.6.1 检测 iframe 结构

```javascript
browser_run_code_unsafe("""async (page) => {
  const frames = page.frames();
  const frameInfo = frames.map(f => ({ url: f.url().substring(0, 80), name: f.name() }));
  return JSON.stringify(frameInfo);
}""")
```

**常见 iframe 结构**：
- 主页面：`https://channels.weixin.qq.com/platform/post/create`
- 内容 iframe：`name="content"`, URL 包含 `/micro/content/post/...`

##### 13.6.2 上传封面（在 iframe 中操作）

**🔴 封面编辑在 iframe 中，通过「编辑」按钮触发 file chooser：**

```javascript
// 上传 3:4 个人主页卡片封面
browser_run_code_unsafe("""async (page) => {
  const frame = page.frame({ name: 'content' });
  if (!frame) return 'frame not found';
  
  // 1. 找到「编辑」按钮并点击（触发 file chooser）
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser', { timeout: 5000 }),
    frame.locator('.edit-btn, [class*="edit"]').first().click({ force: true })
  ]);
  
  // 2. 上传 3:4 封面文件
  await fileChooser.setFiles('news-pipeline/YYYY-MM-DD/douyin-vertical-3-4.png');
  await page.waitForTimeout(2000);
  return 'cover uploaded';
}""")

# 确认封面
browser_run_code_unsafe("""async (page) => {
  const frame = page.frame({ name: 'content' });
  if (frame) {
    await frame.evaluate(() => {
      const buttons = document.querySelectorAll('button');
      for (const btn of buttons) {
        if (btn.textContent.trim() === '确认' && btn.offsetParent !== null) {
          btn.click();
          return;
        }
      }
    });
  }
  await page.waitForTimeout(2000);
  return 'cover confirmed';
}""")
```

**封面尺寸**：
- 个人主页卡片：3:4（1024×1536）→ `douyin-vertical-3-4.png`
- 分享卡片：4:3（1536×1024）→ `douyin-horizontal-4-3.png`

##### 13.6.3 填写短标题（在 iframe 中操作）

**🔴 短标题是 contenteditable div（`.edit-shorttitle-content`），不是标准 input：**

```javascript
// 方法1：在 iframe 内用 JS 直接修改（推荐）
browser_run_code_unsafe("""async (page) => {
  const frame = page.frame({ name: 'content' });
  if (!frame) return 'frame not found';
  
  const result = await frame.evaluate(() => {
    const div = document.querySelector('.edit-shorttitle-content');
    if (div) {
      div.textContent = '短标题内容（最多16字）';
      div.dispatchEvent(new Event('input', { bubbles: true }));
      return 'updated: ' + div.textContent;
    }
    return 'div not found';
  });
  return result;
}""")

// 方法2：坐标点击 + 键盘输入
browser_run_code_unsafe("""async (page) => {
  await page.mouse.click(990, 550);  // 短标题区域坐标
  await page.waitForTimeout(300);
  await page.keyboard.type('短标题内容');
  return 'typed';
}""")
```

**短标题限制**：最多 16 个中文字符，超过会报错。

#### 13.7 保存草稿（不发布）

**🔴 保存草稿后视频进入草稿箱，用户可手动确认发布。**

```javascript
browser_run_code_unsafe("""async (page) => {
  const frame = page.frame({ name: 'content' });
  if (!frame) return 'frame not found';
  
  // 确保定时发表为「不定时」
  const radio = frame.locator('text=不定时').first();
  if (await radio.isVisible()) await radio.click();
  
  // 点击「保存草稿」按钮
  const draftBtn = frame.locator('button:has-text("保存草稿"), button:has-text("存草稿")');
  await draftBtn.first().click();
  await page.waitForTimeout(3000);
  return 'saved as draft';
}""")
```

**保存草稿后**：
- 视频进入草稿箱，URL 变为 `/platform/post/draft`
- 用户可手动在草稿箱中确认发布
- **不自动跳转到发布成功页面**

#### 视频号上传组件操作总结（v1.7.0 实测）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 视频上传 | file chooser | 点击 + 号 → `file_upload` | ✅ 高 |
| 视频描述 | **iframe 内 contenteditable** | 坐标点击 + `keyboard.type` | ⚠️ 坐标方式 |
| 短标题 | **iframe 内 contenteditable div** | iframe JS 修改 `.edit-shorttitle-content` | ✅ 高（用JS） |
| 位置 | 下拉框 | 已有默认值，一般不需改 | ✅ 高 |
| 合集 | **自定义下拉框** | 坐标点击（不稳定） | ⚠️ 可能需手动 |
| 定时发表 | radio 按钮 | `browser_click` | ✅ 高 |
| 发表 | 按钮 | `button:has-text("发表")` | ✅ 高 |
| 封面上传 | **iframe 内 file chooser** | 点击编辑 → +号 → `file_upload` → 确认 | ✅ 高 |
| 短标题修改 | **iframe 内 div** | JS 修改 `.edit-shorttitle-content` → 完成 → 确认修改 | ✅ 高 |

**关键经验**：
1. **🔴 视频号页面内容在 iframe 中**，必须用 `page.frame({ name: 'content' })` 操作表单元素
2. **🔴 短标题是 contenteditable div**（`.edit-shorttitle-content`），不是标准 input
3. **🔴 封面修改和短标题修改有「仅支持修改一次」限制**，修改前确认内容正确
4. **坐标点击是描述填写的最可靠方式**，根据截图估算坐标
5. **发布后跳转到 `/platform/post/list`**，可通过 URL 变化判断发布成功
6. **修改后显示「修改审核中」**，约 30 分钟审核完成
7. **视频号支持两种封面比例**：3:4（个人主页卡片）和 4:3（分享卡片）

## 目录结构

```
news-pipeline/
├── YYYY-MM-DD/                 # 按日期隔离的产出目录
│   ├── scripts/                # 视频脚本
│   ├── storyboards/            # 分镜表
│   ├── prompts/                # 图片 Prompt JSON
│   ├── images/                 # 生成的图片 (scene1.png ~ sceneN.png)
│   ├── voiceover/              # TTS 音频 (scene1.wav ~ sceneN.wav)
│   ├── captions/               # 字幕 JSON
│   ├── video/                  # 最终视频
│   │   └── 【今日羊报AI】*.mp4
│   ├── cover.png               # 视频封面
│   ├── publish.json            # 多平台发布信息
│   ├── wechat-article-*.md     # 公众号图文
│   └── wechat-images/          # 公众号配图
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

## 已知坑与经验教训

### 🔴 字幕与音频不同步（v2.0.0 → v2.1.0 修复）

**问题**：使用字数比例估算字幕时间轴时，由于 TTS 语速不均匀，越到后面字幕偏差越大。

**v2.0.0 方案（已废弃）**：FunASR 语音识别 + ffprobe 比例调整
- FunASR 对专业术语识别极差：GPT→GDP、DeepSeek→Deep triep、Claude Code→Claude coat、Fable-5→核酸efbo杠五、Codex→搞dex、Hermes→HMMI、MiMo→mini/明末
- 修正字典永远追不上新术语，每次都要手动添加大量修正规则
- 识别错误导致字幕内容完全不可用

**v2.1.0 方案（当前默认）**：原始脚本文本 + ffprobe 时长比例对齐
```python
# 1. 直接使用 Phase 2 视频脚本中的原始 TTS 文本（100% 准确）
text = SCENE_TEXTS[scene_num]

# 2. 用 ffprobe 获取音频实际时长
audio_duration_ms = get_audio_duration(wav_path)

# 3. 按标点分割文本
sentences = split_by_punctuation(text)

# 4. 按字符比例分配时间（排除标点计算比例）
char_counts = [len(re.sub(r'[。！？，；：、]', '', s).replace(" ", "")) for s in sentences]
total_chars = sum(char_counts)

# 5. 按比例分配音频时长
for sent, chars in zip(sentences, char_counts):
    duration = audio_duration_ms * chars / total_chars
    # 添加到字幕列表...
```

**关键点**：
- **直接使用原始脚本文本**，不需要 ASR 识别，字幕 100% 准确
- **必须用 ffprobe 获取音频实际时长**，按比例分配确保总时长对齐
- **标点分割后按字符比例分配**，每个场景内部时间轴精确

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

### 🟡 API 地址不固定
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
- 正文：`editors[1].innerHTML = '<h2>...</h2><p>...</p>'` + dispatch `input` 事件

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

### 🔴 公众号封面上传正确流程（v1.9.1 更新）
**问题**：之前的方法（坐标点击、innerHTML 注入）都不可靠。

**已验证的正确流程**：
1. 通过工具栏「图片」→「本地上传」将封面图插入正文（触发 file chooser）
2. Hover 封面区域「拖拽或选择封面」→ 显示选项菜单
3. 用 `.js_selectCoverFromContent` class 选择器点击「从正文选择」
4. 在弹窗中点击图片（出现勾选标记）→ 点击「下一步」
5. 确认裁剪 → 点击「确认」
6. 保存草稿

**关键点**：
- 必须先通过工具栏上传图片到正文，不能用 innerHTML 注入
- Hover 才能显示选项菜单，直接 click 不触发
- 「从正文选择」必须用 class 选择器，文本匹配找不到

### 🔴 公众号赞赏弹窗 checkbox 结构（v1.7.0 新增）
**问题**：「我已阅读并同意」checkbox 在 `label > div` 结构中，不是标准 `input[type="checkbox"]`。

**解决**：用 JS 遍历找到包含「我已阅读并同意」的元素，然后找其父元素中的 checkbox：
```javascript
const parent = el.closest('label, div');
const checkbox = parent.querySelector('input[type="checkbox"], [role="checkbox"]');
if (checkbox) checkbox.click();
```

### 🔴 公众号合集选择器正确流程（v1.9.1 更新）
**问题**：合集选择器是自定义 Vue 组件，JS evaluate 和坐标点击都不可靠。

**已验证的正确流程**：
1. 点击「合集」→「未添加」打开弹窗
2. 点击「请选择合集」输入框 focus
3. 输入「今日羊报」搜索
4. 用 `page.getByText('「今日羊报 AI」', { exact: true })` 精确匹配选项
5. **先 hover 再 click**（必须！）
6. 用 `page.getByRole('button', { name: '确认' })` 点击确认

**关键点**：
- 必须用 `exact: true` 精确匹配，否则会匹配到正文中的同名文本
- 必须先 hover 再 click，直接 click 不生效
- 不要用 JS evaluate，用 Playwright locator 更可靠

### 🟡 公众号原创声明弹窗自动填充（v1.7.0 新增）
**问题**：原创声明弹窗打开后，「文字原创」已默认选中，「我已阅读并同意」已默认勾选。

**解决**：直接点击「确定」即可，无需手动操作其他选项。

### 🟡 公众号工具栏按钮坐标（v1.7.0 新增）
**问题**：工具栏按钮（图片、视频号等）的位置会随页面滚动变化。

**解决**：
- 「图片」按钮：约 x=530, y=17（顶部工具栏）
- 「视频号」按钮：约 x=1074, y=17（顶部工具栏右侧）
- 使用 `browser_evaluate` 动态查找按钮位置更可靠

### 🔴 微信视频号描述字段
**问题**：视频号描述使用自定义 contenteditable div，标准 `textarea`、`placeholder`、`contenteditable="true"` 选择器都找不到。

**解决**：使用坐标点击方式：
1. 根据截图估算描述区域坐标（约 x=760, y=310）
2. `page.mouse.click(x, y)` 点击
3. `page.keyboard.type(text)` 输入内容

### 🔴 微信视频号合集选择器
**问题**：视频号合集选择器是自定义 React 组件，下拉框坐标方式偶尔有效。

**解决**：
1. 点击「选择合集」下拉框
2. 用坐标点击选项（约 x=860, y=180）
3. 如果失败，建议手动选择

### 🔴 微信视频号保存草稿限制
**问题**：如果「定时发表」设为「定时」，保存草稿按钮会显示警告「使用定时发表将无法保存草稿」。

**解决**：保存草稿前必须确保「定时发表」选中「不定时」。

### 🟡 视频号描述自动填充失败
**问题**：尝试用 Playwright 的 `getByPlaceholder`、`getByText`、`locator('textarea')` 等方法都找不到描述输入框。

**解决**：这是微信视频号的自定义组件，只能通过坐标点击 + 键盘输入的方式填写。

### 🔴 视频号 iframe 结构（v1.7.0 新增）
**问题**：视频号页面内容在 iframe 中渲染，直接操作 `document.querySelector` 找不到表单元素。短标题（`.edit-shorttitle-content`）、封面编辑弹窗等都在 iframe 内。

**解决**：
1. 先用 `page.frames()` 检测 iframe 结构
2. 找到 `name="content"` 的 iframe
3. 用 `page.frame({ name: 'content' })` 获取 frame 对象
4. 在 frame 内用 `frame.evaluate()` 操作 DOM

### 🔴 视频号短标题是 contenteditable div（v1.7.0 新增）
**问题**：短标题不是标准 `<input>`，而是 `<div class="edit-shorttitle-content">`，Playwright 的 `fill()`、`type()` 无法直接操作。

**解决**：在 iframe 内用 JS 直接修改：
```javascript
const frame = page.frame({ name: 'content' });
await frame.evaluate(() => {
  document.querySelector('.edit-shorttitle-content').textContent = '新标题';
});
```

### 🔴 视频号封面修改限制（v1.7.0 新增）
**问题**：视频号修改封面和短标题有「仅支持修改一次，修改后不可撤回」限制。修改记录会展示在视频上。

**解决**：
1. 修改前确认所有内容（封面、短标题）都正确
2. 一次性完成所有修改再提交
3. 修改后显示「修改审核中，预计30分钟内审核完成」

### 🔴 视频号封面在 iframe 内上传（v1.7.0 新增）
**问题**：封面编辑弹窗在 iframe 中，`browser_file_upload` 无法直接触发 file chooser。

**解决**：
1. 点击 `.edit-btn` 打开封面编辑弹窗
2. 用坐标点击 `+` 号按钮（约 x=680, y=585）触发 file chooser
3. 用 `browser_file_upload` 上传文件
4. 点击「确认」保存

### 🟡 B站封面隐藏 file input（v1.7.0 新增）
**问题**：B站封面上传的 file input 是隐藏的（`accept: "image/png, image/jpeg"`），且有多个 file input（视频、封面、字幕等）。

**解决**：
```javascript
const inputs = await page.$$('input[type="file"]');
// inputs[0]: 视频 (.mp4)
// inputs[1]: 封面 (image/png, image/jpeg)
// inputs[2]: 字幕 (.txt)
// inputs[3]: 素材 (.zip)
await inputs[1].setInputFiles('cover.png');  // 设置封面
```

### 周报多平台上传流程（v1.9.2 新增）

**周报上传流程与日报相同，但需要使用周报专用文件和合集：**

#### 周报 B站上传
1. 导航到 `https://member.bilibili.com/platform/upload/video/frame`
2. 上传周报视频：`news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD/video/【羊报AI周刊】*.mp4`
3. 标题自动填充：`【羊报AI周刊】... | YYYY-MM-DD~YYYY-MM-DD`
4. 上传封面：`news-pipeline/weekly/YYYY-MM-DD~YYYY-MM-DD/bilibili-4-3.png`
5. 设置创作声明：个人观点，仅供参考
6. 添加标签：羊报AI周刊, AI周报, OpenAI, Anthropic, DeepSeek
7. 填写简介：本期热点...
8. 选择合集：「羊报AI周刊」
9. 点击「立即投稿」

#### 周报公众号上传
1. 打开公众号后台 → 点击「新的创作」→「文章」
2. 切换到新标签页
3. 填写标题：`OpenAI二验风暴、Anthropic IPO、DeepSeek 500亿融资｜羊报AI周刊 YYYY-MM-DD~YYYY-MM-DD`
4. 填写作者：Youngs羊示
5. 填写正文（ProseMirror innerHTML）
6. 上传封面图到正文：
   - 点击正文区域获取 focus
   - 按回车创建新行
   - 点击工具栏「图片」→「本地上传」
   - 用 `input.setInputFiles()` 上传 `wechat-21-9.png`
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
| 通用/视频封面 | `weekly-cover.png` | 1536x1024 (16:9) |
| B站 | `bilibili-4-3.png` | 1536x1152 (4:3) |
| 公众号 | `wechat-21-9.png` | 1536x659 (21:9) |
| 抖音横版 | `douyin-horizontal-4-3.png` | 1536x1152 (4:3) |
| 抖音竖版 | `douyin-vertical-3-4.png` | 1152x1536 (3:4) |

### Phase 14: 抖音自动上传（Playwright MCP）

**权限已在预授权阶段获得，直接执行。**

**🔴 重要经验：抖音创作者中心使用自定义组件，封面上传需要用 force click，发布需要短信验证码。**

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
browser_file_upload("news-pipeline/YYYY-MM-DD/video/【今日羊报AI】*.mp4")

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

**🔴 抖音作品描述是标准 input，但 placeholder 为「填写作品标题，为作品获得更多流量」：**

```
browser_run_code_unsafe("""async (page) => {
  const result = await page.evaluate(() => {
    const elements = document.querySelectorAll('textarea, input[type="text"], [contenteditable]');
    for (const el of elements) {
      const placeholder = el.placeholder || '';
      if (placeholder.includes('填写作品标题')) {
        el.focus();
        el.value = '标题内容';
        el.dispatchEvent(new Event('input', { bubbles: true }));
        return 'filled';
      }
    }
    return 'not found';
  });
  return result;
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

#### 14.6 上传封面（横封面4:3 + 竖封面3:4）

**🔴 抖音封面上传需要两步：先上传横封面，再上传竖封面。封面编辑器使用 canvas 组件：**

```
# 步骤1：点击横封面区域打开封面编辑器
browser_run_code_unsafe("""async (page) => {
  // 滚动到封面区域
  await page.evaluate(() => window.scrollBy(0, 300));
  // 点击横封面4:3区域
  await page.mouse.click(421, 562);  // 横封面位置
  await page.waitForTimeout(1000);
  return 'clicked 横封面';
}""")

# 步骤2：点击「上传封面」（需要 force: true，因为 SVG 元素拦截点击）
browser_run_code_unsafe("""async (page) => {
  const uploadBtn = page.locator('text=上传封面');
  await uploadBtn.first().click({ force: true });
  await page.waitForTimeout(2000);
  return 'clicked';
}""")

# 步骤3：上传横封面文件
browser_file_upload("news-pipeline/YYYY-MM-DD/cover-horizontal.png")

# 步骤4：点击「完成」确认横封面
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent.trim() === '完成' && el.offsetParent !== null) {
        const rect = el.getBoundingClientRect();
        if (rect.y > 630 && rect.y < 680) {
          el.click();
          return;
        }
      }
    }
  });
  return 'confirmed';
}""")

# 步骤5：点击「设置竖封面」按钮
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent.trim() === '设置竖封面' && el.offsetParent !== null) {
        const rect = el.getBoundingClientRect();
        if (rect.y > 560 && rect.y < 600) {
          el.click();
          return;
        }
      }
    }
  });
  return 'clicked 设置竖封面';
}""")

# 步骤6：上传竖封面文件
browser_run_code_unsafe("""async (page) => {
  const uploadBtn = page.locator('text=上传封面');
  await uploadBtn.first().click({ force: true });
  await page.waitForTimeout(2000);
  return 'clicked';
}""")

browser_file_upload("news-pipeline/YYYY-MM-DD/cover-vertical.png")

# 步骤7：点击「完成」确认竖封面
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent.trim() === '完成' && el.offsetParent !== null) {
        const rect = el.getBoundingClientRect();
        if (rect.y > 630 && rect.y < 680) {
          el.click();
          return;
        }
      }
    }
  });
  return 'confirmed';
}""")
```

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
# 找到 option "「今日羊报AI」 共1个作品" 的 ref（如 e1232）
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

#### 14.10 发布视频

**🔴 发布需要短信验证码，必须用户手动输入：**

```
# 点击「发布」按钮
browser_run_code_unsafe("""async (page) => {
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  const buttons = document.querySelectorAll('button');
  for (const btn of buttons) {
    if (btn.textContent.trim() === '发布' && btn.offsetParent !== null) {
      btn.click();
      return 'clicked';
    }
  }
  return 'not found';
}""")

# 等待短信验证码弹窗出现
browser_wait_for(time=3)

# 提示用户输入验证码
# 用户输入验证码后点击「验证」
```

#### 抖音上传组件操作总结（v1.8.0 实测）

| 组件 | 类型 | 操作方式 | 可靠性 |
|------|------|----------|--------|
| 视频上传 | file chooser | `text=上传视频` → `file_upload` | ✅ 高 |
| 提示弹窗 | 按钮 | `getByRole('button', { name: '我知道了' })` | ✅ 高 |
| 作品描述 | 标准 input | JS 设置 `value` + dispatch `input` | ✅ 高 |
| 作品简介 | 文本区域 | 坐标点击 + `keyboard.type` | ✅ 高 |
| 横封面4:3 | **canvas 组件** | 坐标点击 → force click 上传封面 → file_upload → 完成 | ⚠️ 需 force |
| 竖封面3:4 | **canvas 组件** | 设置竖封面 → force click 上传封面 → file_upload → 完成 | ⚠️ 需 force |
| 合集 | listbox | 点击下拉框 → snapshot 找 ref → 精确点击 | ✅ 高 |
| 自主声明 | 弹窗 | 点击打开 → 选择选项 → 确定 | ✅ 高 |
| 标签 | 输入框 | 点击 `#添加话题` → `keyboard.type` + Enter | ✅ 高 |
| 发布 | 按钮 | 点击「发布」→ 短信验证码（需用户手动） | ⚠️ 需用户 |

**关键经验**：
1. **上传视频后必须关闭「视频预览功能」弹窗**，否则后续操作被阻挡
2. **封面上传需要 `force: true`**，因为 SVG 元素会拦截点击事件
3. **合集选择器使用 listbox 组件**，可以用 `snapshot` 找到 ref 精确点击
4. **发布需要短信验证码**，这是安全验证，必须用户手动输入
5. **作品描述是标准 input**，但 placeholder 是「填写作品标题，为作品获得更多流量」
6. **作品简介是文本区域**，需要用坐标点击 + `keyboard.type` 输入
7. **自主声明弹窗**中选择「内容为个人观点或见解」，然后点确定

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
await input.setInputFiles('news-pipeline/weekly/.../wechat-21-9.png');
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
cp "news-pipeline/video-project/out/【今日羊报AI】{核心标题} | YYYY-MM-DD.mp4" \
   "news-pipeline/YYYY-MM-DD/video/"
```

**归档时机**：视频合成完成后立即执行，不要等到上传阶段再复制。

### 🔴 封面生成不完整（v2.2.0 新增，2026-06-13）
**问题**：异步生成封面时，只生成了部分封面（2/5），其余封面因 API 超时或错误未生成。

**解决**：
1. 每张封面生成后自动重试一次
2. 生成完成后验证所有封面文件
3. 如果封面不完整，同步补生成缺失的封面

**验证方法**：
```bash
ls -la news-pipeline/YYYY-MM-DD/*.png | wc -l
# 应该输出 5（cover.png, bilibili-4-3.png, wechat-21-9.png, douyin-horizontal-4-3.png, douyin-vertical-3-4.png）
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

### 🔴 抖音双封面上传（v2.4.0 新增，2026-06-14）

**问题**：抖音需要同时上传横封面（4:3）和竖封面（3:4），竖封面弹窗会在横封面完成后自动弹出。

**解决方案**：
1. 先上传横封面（4:3）→ 点击「完成」
2. 弹出「设置竖封面获更多流量」弹窗 → 点击「设置竖封面」
3. 上传竖封面（3:4）→ 点击「完成」
4. 如果弹窗点击「暂不设置」，可后续在编辑页面补充

**封面文件**：
- 横封面：`douyin-horizontal-4-3.png`（1536x1152，4:3）
- 竖封面：`douyin-vertical-3-4.png`（1152x1536，3:4）

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

### 🟡 MIMO_TTS_API_KEY 未配置（v2.5.0 新增，2026-06-16）

**问题**：mimo-tts.sh 脚本报错 `MIMO_TTS_API_KEY not found`，因为 ~/.claude/settings.json 的 env 中没有配置该变量。

**解决方案**：
1. 在预授权阶段向用户收集 TTS API URL 和 Key
2. 如果 mimo-tts.sh 失败，直接用 Python+curl 调用 MiMo TTS API
3. API 格式：`POST {API_URL}/v1/chat/completions`，body 格式见 mimo-tts.sh 源码

**Why:** TTS API Key 和图片 API Key 是分开的，需要分别收集
**How to apply:** 预授权时额外收集 TTS API URL + Key，或在 Phase 6 遇到错误时询问用户

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
- 视频总时长建议 60-120 秒（可适当放宽到 150s）
- 事件数量建议 4-6 个
- **Phase 1 去重是强制步骤，不可跳过**
- **Phase 8（渲染前校验）是强制步骤，不可跳过**
- **字幕必须使用原始脚本文本 + ffprobe 对齐**，不用 FunASR（专业术语识别率太低）
- **B站自定义下拉框必须用 JS evaluate，不能用 browser_click 文本匹配**
- **封面生成应与 TTS 并行执行**（用 Agent 异步），节省 3-5 分钟
