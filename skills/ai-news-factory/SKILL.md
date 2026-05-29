---
name: ai-news-factory
description: AI News Factory - 从日报 Markdown 自动生成短视频的完整 Pipeline。触发词: "AI日报", "新闻工厂", "news factory", "日报视频", "生成日报视频", "AI news video"
version: 1.0.0
---

# AI News Factory — 日报短视频自动生成

将 AI 日报 Markdown 自动转化为 B站风格短视频，完整 Pipeline：日报 → 事件切分 → 视频脚本 → 分镜 → 图片 → TTS → ASR → 字幕 → 视频合成。

**核心原则：先 TTS 生成音频，再用 ASR 获取真实时间轴，最后生成精确对齐的字幕。**

## 触发条件

- "AI日报", "新闻工厂", "news factory"
- "日报视频", "生成日报视频", "AI news video"
- "把日报做成视频", "日报转视频"

## 前置依赖

- **gen-img skill**: AI 图片生成 (`~/.claude/skills/gen-img/`)
- **video-maker skill**: 视频合成 (`~/.claude/skills/video-maker/`)
- **mimo-tts skill**: 语音合成 (`~/Documents/learn-claude-code/skills/mimo-tts/`)
- **ffmpeg**: 音频格式转换
- **faster-whisper**: ASR 识别（字幕时间轴对齐）`pip install faster-whisper`

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

**先生成 TTS 音频，再用 ASR 获取真实时间轴，最后生成精确对齐的字幕。**

根据视频脚本逐场景生成配音：

```bash
# 基础用法 - 使用预置音色
bash ~/Documents/learn-claude-code/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "配音文本" \
  --profile "阿根" \
  --output "news-pipeline/voiceover/scene1.wav"

# 带风格控制
bash ~/Documents/learn-claude-code/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "配音文本" \
  --profile "阿根" \
  --style "兴奋 新闻播报" \
  --output "news-pipeline/voiceover/scene1.wav"
```

**配音要求**:
- 推荐音色: 阿根（音色档案）
- 按场景生成音频文件（scene1.wav, scene2.wav, ...）
- 每个场景的文本来自视频脚本对应段落

**Step 6.1**: 获取每个音频的精确时长

```bash
for i in 1 2 3 4 5 6 7 8; do
  duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 news-pipeline/voiceover/scene$i.wav 2>/dev/null)
  echo "scene$i: ${duration}s"
done
```

### Phase 7: ASR 识别（借鉴 VideoCaptioner）

**用 ASR 识别 TTS 生成的配音，获取每个词的精确时间戳。**

#### 7.1 ASR 词级时间戳提取

```python
from faster_whisper import WhisperModel

def asr_extract_words(audio_path: str) -> list:
    """
    用 Faster Whisper 提取词级时间戳
    
    原理（借鉴 VideoCaptioner）：
    1. Faster Whisper 支持 word_timestamps=True
    2. 直接输出每个词的开始/结束时间
    3. 无需二次识别，精度高
    """
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    
    segments, info = model.transcribe(
        audio_path,
        word_timestamps=True,  # 启用词级时间戳
        language="zh",
        vad_filter=True,       # 启用 VAD 过滤静音
    )
    
    words = []
    for segment in segments:
        for word_info in segment.words:
            words.append({
                'word': word_info.word.strip(),
                'start': word_info.start,  # 秒
                'end': word_info.end,      # 秒
                'probability': word_info.probability,
            })
    
    return words
```

#### 7.2 LLM 语义断句（借鉴 VideoCaptioner）

**用 LLM 将 ASR 输出的连续文本按语义分句**

```python
def llm_split_segments(full_text: str) -> list:
    """
    用 LLM 按语义自然分句
    
    优势：
    1. 不拆分专有名词（如 "GPT-4"、"OpenAI"）
    2. 数字和单位保持在一起（如 "100%"、"3.5秒"）
    3. 按语义停顿分句，更符合阅读习惯
    """
    prompt = f"""
请将以下文本按语义自然分句，每句不超过 15 个字符。

规则：
1. 按标点符号和语义停顿分句
2. 每句保持完整语义
3. 不拆分专有名词
4. 数字和单位保持在一起
5. 输出格式：每句一行

原文：
{full_text}
"""
    response = call_llm(prompt)
    sentences = response.strip().split('\n')
    return [s.strip() for s in sentences if s.strip()]
```

**备选：标点符号分句**（简单快速）

```python
import re

def punctuation_split(text: str) -> list:
    """按标点符号分句，每句不超过 15 字"""
    raw_segments = re.split(r'[。！？；]', text)
    
    merged = []
    buffer = ""
    for seg in raw_segments:
        seg = seg.strip()
        if not seg:
            continue
        if len(buffer) + len(seg) < 15:
            buffer += seg
        else:
            if buffer:
                merged.append(buffer)
            buffer = seg
    if buffer:
        merged.append(buffer)
    
    return merged
```

### Phase 8: 字幕生成（滑动窗口对齐）

**将 LLM 分句与 ASR 词级时间戳对齐，生成精确的字幕时间轴。**

#### 8.1 滑动窗口对齐算法

```python
def sliding_window_align(sentences: list, words: list) -> list:
    """
    滑动窗口对齐算法
    
    核心思想：
    1. 在 ASR 输出的 words 中找到与字幕文本匹配的子序列
    2. 用匹配到的词级时间戳作为字幕的 start/end 时间
    """
    captions = []
    word_index = 0
    
    for sentence in sentences:
        text = sentence.replace(' ', '')  # 去除空格
        
        # 在 words 中寻找匹配
        best_start = word_index
        best_length = 0
        
        for i in range(word_index, len(words)):
            match_text = ""
            j = i
            
            # 累积匹配文本
            while j < len(words) and len(match_text) < len(text) + 5:
                match_text += words[j]['word']
                j += 1
            
            # 检查是否匹配
            clean_match = match_text.replace(' ', '')
            if text in clean_match or clean_match in text:
                if j - i > best_length:
                    best_length = j - i
                    best_start = i
        
        # 用匹配到的时间戳创建字幕
        if best_length > 0:
            captions.append({
                "text": sentence,
                "startMs": int(words[best_start]['start'] * 1000),
                "endMs": int(words[best_start + best_length - 1]['end'] * 1000),
                "timestampMs": int(words[best_start]['start'] * 1000),
                "confidence": 1.0
            })
            word_index = best_start + best_length
        else:
            # 回退：保持原估算时间（见 8.2）
            pass
    
    return captions
```

#### 8.2 回退方案：字数比例估算

当 ASR 对齐失败时，使用字数比例估算时间轴：

```python
def estimate_caption_timing(captions: list, scene_duration_ms: int) -> list:
    """
    按字数比例估算每句字幕的时长
    
    核心假设：
    - 中文约 200ms/字（语速 300字/分钟）
    - 每句最短 0.5 秒，最长 3 秒
    - 句间间隔 0.3 秒
    """
    total_chars = sum(len(c['text']) for c in captions)
    
    if total_chars == 0:
        return captions
    
    ms_per_char = (scene_duration_ms - 300 * len(captions)) / total_chars
    
    current_ms = 0
    for cap in captions:
        char_count = len(cap['text'])
        duration_ms = int(char_count * ms_per_char)
        duration_ms = max(500, min(3000, duration_ms))
        
        cap['startMs'] = current_ms
        cap['endMs'] = current_ms + duration_ms
        cap['timestampMs'] = current_ms
        
        current_ms += duration_ms + 300  # 句间 0.3s 间隔
    
    return captions
```

#### 8.3 完整字幕生成流程

```python
def generate_subtitles_for_scene(audio_path: str, scene_text: str, scene_duration_ms: int) -> list:
    """
    为单个场景生成字幕
    
    流程：TTS音频 → ASR词级时间戳 → LLM分句 → 滑动窗口对齐
    """
    # Step 1: ASR 提取词级时间戳
    words = asr_extract_words(audio_path)
    
    # Step 2: LLM 语义断句
    sentences = llm_split_segments(scene_text)
    
    # Step 3: 滑动窗口对齐
    captions = sliding_window_align(sentences, words)
    
    # Step 4: 验证对齐结果
    if not validate_alignment(captions, scene_duration_ms):
        # 回退：用字数比例估算
        captions = [{"text": s, "startMs": 0, "endMs": 0, "timestampMs": 0, "confidence": 1.0}
                    for s in sentences]
        captions = estimate_caption_timing(captions, scene_duration_ms)
    
    return captions


def validate_alignment(captions: list, scene_duration_ms: int) -> bool:
    """验证对齐结果是否合理"""
    if not captions:
        return False
    
    # 检查时间是否递增
    for i in range(1, len(captions)):
        if captions[i]['startMs'] < captions[i-1]['startMs']:
            return False
    
    # 检查总时长是否合理（不超过场景时长的 120%）
    total_ms = captions[-1]['endMs'] - captions[0]['startMs']
    if total_ms > scene_duration_ms * 1.2:
        return False
    
    return True
```

### Phase 9: 渲染前校验（必须执行）

**在渲染视频前，必须完成以下校验步骤，确保图片-音频-字幕三者完全对齐。**

#### Step 9.1: 梳理对应关系表

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

#### Step 9.2: 更新 Composition.tsx

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

#### Step 9.3: 更新 Root.tsx

更新总时长为所有场景时长之和：

```tsx
const TOTAL_DURATION_SEC = 场景1时长 + 场景2时长 + ... + 场景N时长;
```

#### Step 9.4: 验证字幕对齐

确保字幕时间轴与音频时长匹配：

- 字幕的总时长应与所有音频时长之和一致
- 无音频的场景不生成字幕，但时间轴要跳过该场景的时长
- 每句字幕的 startMs/endMs 应在对应场景的时间范围内

#### Step 9.5: 复制资源到 public 目录

```bash
cp images/scene*.png video-project/public/images/
cp voiceover/scene*.wav video-project/public/voiceover/
cp captions/captions.json video-project/public/captions.json
```

#### Step 9.6: 确认渲染

**只有在以上所有步骤完成后，才能执行 Phase 10 渲染。**

### Phase 10: 视频合成

调用 video-maker skill 合成最终视频：

```bash
cd video-project && npx remotion render AINewsVideo "out/【今日羊报AI】{核心标题} | YYYY-MM-DD.mp4" --codec h264 --crf 18
```

**输出**:
- 视频文件路径
- 时长、分辨率
- 文件大小

### Phase 11: 封面与发布信息生成

视频渲染完成后，生成发布所需的全部素材，输出到 `news-pipeline/YYYY-MM-DD/` 目录。

#### Step 10.1: 生成视频封面

使用 gen-img 生成封面图（1536x1024，16:9），**必须使用以下统一模板**：

**封面模板 Prompt**：

```
A professional Chinese AI news studio cover image. A male news anchor in a dark navy suit with white shirt and dark tie sits at a modern curved news desk, hands clasped, looking directly at camera with serious expression. Behind him are multiple large display screens arranged in a grid showing: {本期核心新闻相关的视觉元素，如终端界面、产品截图、数据图表等}. The studio has dramatic blue and red neon lighting, with red accent lights along the desk edges and blue ambient lighting. In the top right corner, display the text "今日羊报 AI" on the first line and "AI 新闻" on the second line in large white Chinese characters. In the bottom left corner, display the date "{YYYY-MM-DD}" in large white bold text. The overall mood is professional and authoritative. Professional broadcast news photography style, photorealistic, highly detailed, cinematic lighting, 16:9 aspect ratio.
```

**模板要素**（必须包含）：
| 要素 | 位置 | 说明 |
|------|------|------|
| 新闻主播 | 画面中央 | 男性，深色西装，白色衬衫，深色领带，双手交叉放桌面 |
| 新闻台 | 底部 | 现代弧形设计，红色霓虹灯条 |
| 多屏背景 | 主播身后 | 2x3 或 3x3 网格，展示本期新闻相关画面 |
| 品牌文字 | 右上角 | 「今日羊报 AI」+「AI 新闻」，白色大字 |
| 日期 | 左下角 | YYYY-MM-DD 格式，白色粗体 |
| 灯光 | 全局 | 蓝色环境光 + 红色重点光，营造新闻演播室氛围 |

**背景屏幕内容**（根据当期新闻定制）：
- 左侧屏幕：终端/代码界面，展示技术细节
- 中间屏幕：核心产品/公司 logo + 问号或警示符号
- 右侧屏幕：相关产品/模型 logo 矩阵
- 底部条：关键数据或警告信息

**示例**（2026-05-29）：
- 左屏：终端显示身份混淆调试日志（Qwen/DeepSeek 标识）
- 中屏：Claude logo + 问号
- 右屏：Qwen、DeepSeek、ChatGPT、Gemini、Llama、Kimi logo 矩阵
- 底部：「身份混淆」放大镜图标

输出到 `YYYY-MM-DD/cover.png`

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
7. TTS 生成配音（根据脚本逐场景生成音频）
8. ASR 识别配音（faster-whisper 获取词级时间戳）
9. 字幕生成：
   a. LLM 语义断句（或标点符号分句）
   b. 滑动窗口对齐到 ASR 时间戳
   c. 验证对齐结果，失败时回退到字数比例估算
10. 渲染前校验：梳理对应关系 → 修正 Composition → 复制资源
11. 调用 Remotion 渲染视频
12. 生成封面 + 发布信息 (publish.json)
13. 归档所有资源到 YYYY-MM-DD/ 目录
14. 输出最终摘要
```

## 注意事项

- 每个 Phase 完成后向用户展示中间结果，确认后继续
- 图片生成失败时自动重试一次
- TTS 使用 mimo-tts，推荐音色「阿根」
- 视频总时长建议 60-120 秒
- 事件数量建议 3 个（保证信息密度）
