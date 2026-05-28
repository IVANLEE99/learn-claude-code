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

使用填空即用模板为每个分镜生成图片 Prompt，输出到 `news-pipeline/prompts/image-prompts-YYYY-MM-DD.json`。

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

`image-prompts-YYYY-MM-DD.json` 结构：

```json
[
  {
    "scene": 1,
    "news": "新闻标题",
    "prompt": "填充后的完整 Prompt"
  }
]
```

#### 填充示例（Claude Opus 4.8 发布新闻）

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
「今日羊报 AI」
「AI 新闻」
分两行显示在右上角,充当背景
```

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

### Phase 7.5: 音画同步优化（借鉴 pyVideoTrans）

**在生成字幕后、渲染前，进行音画同步优化，确保字幕与配音精确对齐。**

#### 7.5.1 精确音频时长获取

使用 `ffprobe` 获取每个配音文件的精确时长：

```bash
# 获取单个音频时长
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 voiceover/scene1.wav

# 批量获取所有音频时长
for i in 1 2 3 4 5; do
  duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 voiceover/scene$i.wav)
  echo "scene$i: ${duration}s"
done
```

**关键点**:
- 时长精确到毫秒（如 8.800000）
- 不能使用估算值，必须用 ffprobe 实际测量
- 将时长记录到对应关系表中

#### 7.5.2 时间差补偿机制

当字幕时长与音频时长不匹配时，进行补偿：

| 情况 | 处理方式 |
|------|----------|
| 音频时长 > 字幕时长 | 延长场景时长，匹配音频 |
| 音频时长 < 字幕时长 | 在场景末尾添加静音填充 |
| 字幕间隙 > 0.3s | 压缩间隙，使节奏更紧凑 |

**补偿脚本**:
```python
import subprocess

def get_audio_duration(audio_path):
    """获取音频精确时长（秒）"""
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ], capture_output=True, text=True)
    return float(result.stdout.strip())

def calculate_scene_durations(audio_files):
    """计算每个场景的实际时长"""
    durations = []
    for audio in audio_files:
        if audio:
            durations.append(get_audio_duration(audio))
        else:
            durations.append(1.0)  # 无音频场景默认 1s
    return durations
```

#### 7.5.3 字幕间隙静音去除

去除字幕之间的静音区间，使视频节奏更紧凑：

```bash
# 使用 ffmpeg 去除静音
ffmpeg -i input.wav -af "silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB" output.wav
```

**优化策略**:
- 字幕间隙 > 0.5s 时，压缩到 0.2-0.3s
- 保持段落间的自然停顿（0.3s）
- 去除句首句尾的多余静音

### Phase 8: 渲染前校验（必须执行）

**在渲染视频前，必须完成以下校验步骤，确保图片-音频-字幕三者完全对齐。**

#### Step 8.1: 梳理对应关系表

列出所有场景的对应关系，输出表格确认：

```
| 场景 | 图片 | 音频 | 内容 | 时长 |
|------|------|------|------|------|
| 1 | scene1.png | scene1.wav | Hook | Xs |
| 2 | scene2.png | scene3.wav | 第一条 | Xs |
| ... | ... | ... | ... | ... |
```

**关键规则**:
- 每个场景的图片ID、音频ID、字幕内容必须一一对应
- 无音频的过渡场景（如主播画面），音频ID填「无」，时长用固定值（如 1s）
- 字幕内容必须与音频内容一致，不能错位
- 音频时长决定场景时长，不能用估算值

#### Step 8.2: 更新 Composition.tsx

根据对应关系表，重写 `video-project/src/Composition.tsx` 中的场景配置：

```tsx
// 正确的场景配置：图片ID、音频ID、时长
const sceneConfig = [
  { imageId: 1, audioId: 1, duration: 6.40 },   // Hook
  { imageId: 2, audioId: 0, duration: 1.00 },   // 主播过渡 (无音频)
  { imageId: 3, audioId: 2, duration: 14.40 },  // 第一条
  // ... 每个场景都必须明确指定 imageId、audioId、duration
];
```

**禁止使用**:
- 简单的 `scene.id` 自动映射（容易错位）
- 硬编码的时长数组（应从音频实际时长获取）

#### Step 8.3: 更新 Root.tsx

更新总时长为所有场景时长之和：

```tsx
const TOTAL_DURATION_SEC = 场景1时长 + 场景2时长 + ... + 场景N时长;
```

#### Step 8.4: 重新生成字幕

根据 Step 8.1 的对应关系表，重新生成 `captions.json`：

- 字幕的时间轴必须从 0 开始，按场景顺序累加
- 无音频的场景不生成字幕，但时间轴要跳过该场景的时长
- 每句字幕的时长按字数比例分配

#### Step 8.5: 复制资源到 public 目录

```bash
cp images/scene*.png video-project/public/images/
cp voiceover/scene*.wav video-project/public/voiceover/
cp captions/captions.json video-project/public/captions.json
```

#### Step 8.6: 确认渲染

**只有在以上所有步骤完成后，才能执行 Phase 9 渲染。**

### Phase 9: 视频合成

调用 video-maker skill 合成最终视频：

```bash
cd video-project && npx remotion render AINewsVideo "out/【今日羊报AI】{核心标题} | YYYY-MM-DD.mp4" --codec h264 --crf 18
```

**输出**:
- 视频文件路径
- 时长、分辨率
- 文件大小

### Phase 10: 封面与发布信息生成

视频渲染完成后，生成发布所需的全部素材，输出到 `news-pipeline/YYYY-MM-DD/` 目录。

#### Step 10.1: 生成视频封面

使用 gen-img 生成封面图（1536x1024，16:9）：

- 封面需包含当期日期
- 体现本期核心新闻主题
- 保持「今日羊报 AI」品牌风格
- 输出到 `YYYY-MM-DD/cover.png`

#### Step 10.2: 生成发布信息

生成 `publish.json`，包含以下字段：

```json
{
  "title": "【今日羊报AI】{核心标题} | YYYY-MM-DD",
  "subtitle": "副标题（可选）",
  "description": "视频简介，2-3句话概括本期内容",
  "tags": ["标签1", "标签2", "..."],
  "publish_time": "建议发布时间",
  "platform": {
    "bilibili": {
      "title": "【今日羊报AI】{核心标题}｜{N}条重磅AI新闻一次看完 | YYYY-MM-DD",
      "tags": ["B站标签"],
      "description": "B站简介"
    },
    "douyin": {
      "title": "{核心标题}（15字以内，带情绪）",
      "tags": ["抖音标签"]
    }
  }
}
```

**标题生成规则**:
- 格式: `【今日羊报AI】{核心标题} | YYYY-MM-DD`
- 核心标题包含关键词（模型名、公司名）+ 情绪感（震惊、突破、炸了）
- B站标题追加 `｜{N}条重磅AI新闻一次看完`
- 示例: `【今日羊报AI】MiMo V2.5 降价99%！Token Plan暴涨55倍｜7条重磅AI新闻一次看完 | 2026-05-27`
- 抖音标题保持简短（15字以内），不带前缀

**简介生成规则**:
- 2-3 句话概括本期 3-5 条核心新闻
- 包含关键词便于搜索
- 引导互动（点赞、关注、评论）

**标签生成规则**:
- 包含：AI日报、具体模型名、公司名、技术领域
- 5-10 个标签
- 覆盖热搜关键词

#### Step 10.3: 归档资源

将所有产出复制到日期目录：

```bash
# 创建日期目录
mkdir -p news-pipeline/YYYY-MM-DD/{scripts,storyboards,prompts,images,voiceover,captions,video}

# 复制资源
cp news-pipeline/sources/YYYY-MM-DD.md news-pipeline/YYYY-MM-DD/
cp news-pipeline/prompts/*.json news-pipeline/YYYY-MM-DD/prompts/
cp news-pipeline/images/scene*.png news-pipeline/YYYY-MM-DD/images/
cp news-pipeline/voiceover/scene*.wav news-pipeline/YYYY-MM-DD/voiceover/
cp news-pipeline/captions/captions.json news-pipeline/YYYY-MM-DD/captions/
cp news-pipeline/video-project/out/【今日羊报AI】*.mp4 news-pipeline/YYYY-MM-DD/video/
cp news-pipeline/YYYY-MM-DD/cover.png news-pipeline/YYYY-MM-DD/
cp news-pipeline/YYYY-MM-DD/publish.json news-pipeline/YYYY-MM-DD/
```

#### Step 10.4: 输出摘要

向用户展示最终产出：

```
✅ 本期视频制作完成！

📅 日期: YYYY-MM-DD
🎬 视频: news-pipeline/YYYY-MM-DD/video/【今日羊报AI】{核心标题} | YYYY-MM-DD.mp4
🖼️ 封面: news-pipeline/YYYY-MM-DD/cover.png
📋 发布信息: news-pipeline/YYYY-MM-DD/publish.json

📝 标题: 【今日羊报AI】{核心标题} | YYYY-MM-DD
🏷️ 标签: {tags}
📄 简介: {description}
```

## 注意事项

- 每个 Phase 完成后向用户展示中间结果，确认后继续
- 图片生成失败时自动重试一次
- TTS 使用 mimo-tts，推荐音色「阿根」
- 视频总时长建议 60-120 秒
- 事件数量建议 3 个（保证信息密度）
- **Phase 8 渲染前校验是强制步骤，不可跳过**

## 目录结构

**每一期的内容按日期隔离存储，防止覆盖历史数据。**

```
news-pipeline/
├── sources/                    # 原始日报 Markdown
│   └── 2026-05-27.md
├── YYYY-MM-DD/                 # 按日期隔离的产出目录
│   ├── scripts/                # 视频脚本
│   ├── storyboards/            # 分镜表
│   ├── prompts/                # 图片 Prompt
│   ├── images/                 # 生成的图片 (scene1.png ~ sceneN.png)
│   ├── voiceover/              # TTS 音频 (scene1.wav ~ sceneN.wav)
│   ├── captions/               # 字幕 JSON
│   ├── video/                  # 最终视频
│   │   └── 今日羊报AI_YYYY-MM-DD.mp4
│   ├── cover.png               # 视频封面
│   └── publish.json            # 发布信息 (标题、简介、标签、建议)
├── video-project/              # Remotion 项目 (固定复用)
│   ├── public/
│   │   ├── images/             # 当期图片符号链接或复制
│   │   ├── voiceover/          # 当期音频符号链接或复制
│   │   └── captions.json       # 当期字幕
│   └── src/
├── topics/                     # 事件切分结果 JSON
└── images/                     # 临时目录 (可清理)
```

**关键规则**:
- 每期开始时，创建 `news-pipeline/YYYY-MM-DD/` 目录
- 所有产出文件（脚本、分镜、图片、音频、字幕、视频、封面、发布信息）存入该日期目录
- `video-project/public/` 中的资源从当期日期目录复制过来
- 历史日期的目录不可修改或删除

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
9. 渲染前校验：梳理对应关系 → 修正 Composition → 重新生成字幕 → 复制资源
10. 调用 Remotion 渲染视频
11. 生成封面 + 发布信息 (publish.json)
12. 归档所有资源到 YYYY-MM-DD/ 目录
13. 输出最终摘要
```

## 注意事项

- 每个 Phase 完成后向用户展示中间结果，确认后继续
- 图片生成失败时自动重试一次
- TTS 使用 mimo-tts，推荐音色「阿根」
- 视频总时长建议 60-120 秒
- 事件数量建议 3 个（保证信息密度）
