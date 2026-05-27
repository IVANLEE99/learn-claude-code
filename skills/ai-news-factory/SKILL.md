---
name: ai-news-factory
description: AI News Factory - 从日报 Markdown 自动生成短视频的完整 Pipeline。触发词: "AI日报", "新闻工厂", "news factory", "日报视频", "生成日报视频", "AI news video"
version: 1.0.0
---

# AI News Factory — 日报短视频自动生成

将 AI 日报 Markdown 自动转化为 B站风格短视频，完整 Pipeline：日报 → 事件切分 → 视频脚本 → 分镜 → 图片 → TTS → 字幕 → 视频合成。

## 触发条件

- "AI日报", "新闻工厂", "news factory"
- "日报视频", "生成日报视频", "AI news video"
- "把日报做成视频", "日报转视频"

## 前置依赖

- **gen-img skill**: AI 图片生成 (`~/.claude/skills/gen-img/`)
- **video-maker skill**: 视频合成 (`~/.claude/skills/video-maker/`)
- **mimo-tts skill**: 语音合成 (`~/Documents/learn-claude-code/skills/mimo-tts/`)
- **ffmpeg**: 音频格式转换

## 执行流程

### Phase 1: 输入与事件切分

**输入**: 日报 Markdown 文件路径或直接粘贴内容。

**Step 1.1**: 读取日报内容，提取所有独立新闻事件。

**Step 1.2**: 对每个事件打分排序，输出 JSON：

```json
[
  {
    "id": 1,
    "topic": "Claude 4.8 疑似曝光",
    "summary": "有人在 Claude Code 里抓到新模型 claude-jupiter-v1-p",
    "importance": 9,
    "emotion": "争议",
    "keywords": ["Claude", "新模型", "Sonnet 4.8"]
  }
]
```

**Step 1.3**: 选择 Top 3 事件进入视频脚本生成。向用户确认选择：

```
已识别以下热点事件，请确认要制作视频的事件：
1. [事件1] (重要性: 9/10)
2. [事件2] (重要性: 8/10)
3. [事件3] (重要性: 7/10)
```

### Phase 2: 视频脚本生成

对每个选中事件，按模板生成脚本。

**风格要求**:
- 像 B站 AI 科技 UP 主
- 快节奏、有情绪、不书面
- 60~120 秒短视频
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

**参考模板**: `templates/script-template.md`

### Phase 3: 分镜生成

根据视频脚本生成分镜表：

| 镜号 | 时长 | 镜头类型 | 画面内容 | 字幕重点 | 转场 |
|------|------|----------|----------|----------|------|
| 1 | 3s | 特写 | AI 芯片电路 | Hook 文字 | 淡入 |
| 2 | 5s | 全景 | 科技新闻编辑室 | 事件标题 | 切换 |

**镜头类型参考**:
- 特写: 数据、代码、模型名称
- 中景: 人物对话、产品展示
- 全景: 场景概述、趋势图表
- 动态: 数据流动、网络连接

**参考模板**: `templates/storyboard-template.md`

### Phase 4: 图片 Prompt 生成

为每个分镜生成 gen-img 兼容的图片 Prompt。

**视频品牌**: 「今日羊报 AI」
**副标题**: 「AI 新闻」

#### 核心方法：把新闻翻译成视觉画面

新闻通常是抽象逻辑，图像模型需要具体视觉元素。必须充当"美术指导"，把文字逻辑翻译成视觉画面。

#### 第一步：拆解新闻为可画元素

拿到新闻后，用四个问题拆解：
- **谁/什么**（主体：人物、物体、场景）
- **在哪里**（环境/地点）
- **在做什么**（动作/事件核心）
- **整体氛围/情绪**（严肃、喜庆、紧张、温暖）

#### 第二步：选择视觉表现策略

| 新闻类型 | 策略 | 说明 |
|----------|------|------|
| 科技/产品 | 社论插画风 | 用具象物体代表抽象概念 |
| 财经/数据 | 隐喻风 + 数据具象化 | 图表、金币等视觉元素 |
| 社会/突发 | 纪实写实风 | 直接描绘新闻现场 |

#### 第三步：Prompt 万能公式

```
[主体与环境] + [关键动作或事件] + [细节烘托] + [构图/镜头] + [风格/画质] — [不要什么]
```

#### 不同新闻类型的关键词

| 新闻类型 | 额外关键词 |
|----------|-----------|
| 科技/产品 | minimalist studio lighting, product photography, sharp focus, futuristic |
| 财经/数据 | conceptual editorial illustration, rising graphs, stock exchange background |
| 灾难/突发 | breaking news, emergency responders, blurred background urgency, raw and emotional |
| 时政/会议 | official press conference, formal attire, podium with flags, serious atmosphere |
| 暖闻/人情味 | warm color palette, genuine smile, soft natural light, close-up connection |

#### 避坑指南

1. **先说明任务**: Prompt 第一句告诉它要做什么（如 An editorial illustration... 或 A realistic news photo...）
2. **用英文写**: 图像模型底层标签大多是英文，专业词汇如 Editorial illustration、Photojournalism 质感更好
3. **避免抽象比喻**: 不要写"经济腾飞像雄鹰"，要画"城市高楼间阳光穿透、数据图表上升"
4. **不要让 AI 做算术或排版**: 不要试图画"500亿"字样，画"两只穿西装的手在金色背景下握手"
5. **用否定提示**: 加 —no text, no letters, no signature, no watermark 保证画面干净
6. **关键词前置**: 越靠前权重越高，重要元素放开头

#### 品牌规则

- 图片中如需显示新闻台标、频道名称、编辑室标识等，统一使用「今日羊报 AI」
- 图片中如需显示副标题，使用「AI 新闻」


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
今日羊报 AI
AI News 
分两行显示在右上角,充当背景
```

#### 填充示例（Claude Opus 4.8 发布新闻）

| 占位符 | 填充内容 |
|--------|----------|
| 新闻内容 | Claude Opus 4.8 预计明天发布，社区在代码中发现新模型痕迹，开发者社区热议 |
| 新闻核心地点 | Developer workspace |
| 主要人物/物体 | terminal screen |
| 他们在做的关键动作 | displaying model version 4.8 and benchmark metrics |
| 标志性环境细节 | code editor in background |
| 时间/天气/光线 | Warm desk lamp lighting with monitor glow, late night coding atmosphere |
| 情绪与氛围描述 | focused developer atmosphere |
| 新闻摄影/编辑插图风格 | Editorial news photography style |
| 镜头焦段 | 35mm lens |

**填充后完整 Prompt**:
```
Create a realistic editorial news image about:

Claude Opus 4.8 预计明天发布，社区在代码中发现新模型痕迹，开发者社区热议。

The image should show:
- clear main subject: terminal screen
- real-world environment: developer workspace
- strong relation to the news event: displaying model version 4.8 and benchmark metrics
- cinematic but realistic lighting: Warm desk lamp lighting with monitor glow, late night coding atmosphere
- professional news photography style: Editorial news photography style
- modern AI technology atmosphere: focused developer atmosphere

Avoid:
- abstract AI concepts
- floating holograms
- random sci-fi elements
- text in image
- logos
- low-detail compositions

Developer workspace with terminal screen displaying model version 4.8 and benchmark metrics, code editor in background. Warm desk lamp lighting with monitor glow, late night coding atmosphere. Editorial news photography style, photorealistic, highly detailed, shot on 35mm lens — no text, no watermark.

16:9 aspect ratio
今日羊报 AI
AI News 
分两行显示在右上角,充当背景
```

**参考模板**: `templates/image-prompt-template.md`

### Phase 5: 图片生成

使用 gen-img skill 为每个分镜生成图片：

```bash
bash ~/.claude/skills/gen-img/scripts/gen-img.sh "<PROMPT>" "news-pipeline/images/sceneN.png" "1536x1024" "auto" 1 "png"
```

**注意事项**:
- 使用 `1536x1024` (16:9 横屏)
- 所有图片保持统一风格
- 生成后立即预览，不满意可重新生成
- **必须逐张生成**：API 有并发限制，一张生成完成后再生成下一张，不可并行

### Phase 6: TTS 配音

使用 mimo-tts skill 生成配音：

```bash
# 基础用法 - 使用预置音色
bash ~/Documents/learn-claude-code/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "配音文本" \
  --voice "冰糖" \
  --output "news-pipeline/voiceover/scene1.wav"

# 使用音色档案
bash ~/Documents/learn-claude-code/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "配音文本" \
  --profile "曼波" \
  --output "news-pipeline/voiceover/scene1.wav"

# 带风格控制
bash ~/Documents/learn-claude-code/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "配音文本" \
  --voice "冰糖" \
  --style "兴奋 新闻播报" \
  --output "news-pipeline/voiceover/scene1.wav"
```

**可用预置音色**: mimo_default, 冰糖, 茉莉, 苏打, 白桦, Mia, Chloe, Milo, Dean

**配音要求**:
- 推荐音色: 冰糖（清亮女声，适合科技新闻）
- 可用 `--style` 添加情绪标签（如 "兴奋"、"震惊"、"思考"）
- 生成后用 `ffprobe` 获取时长用于字幕同步
- 段落间自然停顿

### Phase 7: 字幕生成

根据配音时长生成 `captions.json`：

```json
[
  {
    "text": "字幕文字",
    "startMs": 0,
    "endMs": 2500,
    "timestampMs": 0,
    "confidence": 1.0
  }
]
```

**字幕规则**:
- 按标点符号分句
- 每句时长按字数比例分配
- 段落间加 0.3s 间隔

### Phase 8: 视频合成

调用 video-maker skill 合成最终视频：

```bash
cd video-project && npx remotion render AIVideo out/video.mp4 --codec h264 --crf 18
```

**输出**:
- 视频文件路径
- 时长、分辨率
- 文件大小

## 目录结构

```
news-pipeline/
├── sources/          # 原始日报 Markdown
├── topics/           # 事件切分结果 JSON
├── scripts/          # 视频脚本
├── storyboards/      # 分镜表
├── prompts/          # 图片 Prompt
├── images/           # 生成的图片
├── voiceover/        # TTS 音频
├── captions/         # 字幕 JSON
└── videos/           # 最终视频
```

## 完整执行示例

```
用户: 帮我把今天的 AI 日报做成视频

Claude:
1. 读取日报文件
2. 切分事件 → 展示 Top 3 → 用户确认
3. 生成视频脚本 → 用户预览
4. 生成分镜表 → 用户确认
5. 选择图片风格 → 生成图片 Prompt
6. 调用 gen-img 生成图片 → 用户预览
7. TTS 生成配音
8. 生成字幕
9. 调用 video-maker 合成视频
10. 输出最终视频
```

## 注意事项

- 每个 Phase 完成后向用户展示中间结果，确认后继续
- 图片生成失败时自动重试一次
- TTS 使用 mimo-tts，推荐音色「阿根」
- 视频总时长建议 60-120 秒
- 事件数量建议 3 个（保证信息密度）
