---
name: ai-news-factory
description: AI News Factory - 从日报 Markdown 自动生成短视频的完整 Pipeline。触发词: "AI日报", "新闻工厂", "news factory", "日报视频", "生成日报视频", "AI news video"
version: 1.0.0
---

# AI News Factory — 日报短视频自动生成

将 AI 日报 Markdown 自动转化为 B站风格短视频，完整 Pipeline：日报 → 事件切分 → 视频脚本 → 分镜 → 图片 → TTS → 字幕 → 视频合成。

**核心原则：先 TTS 生成音频，再用字数比例估算字幕时间轴（TTS 语速稳定，字数比例比 ASR 更可靠）。**

## 触发条件

- "AI日报", "新闻工厂", "news factory"
- "日报视频", "生成日报视频", "AI news video"
- "把日报做成视频", "日报转视频"

## 前置依赖

- **gen-img skill**: AI 图片生成 (`~/.claude/skills/gen-img/`)
- **video-maker skill**: 视频合成 (`~/.claude/skills/video-maker/`)
- **mimo-tts skill**: 语音合成 (`~/Documents/learn-claude-code/skills/mimo-tts/`)
- **ffmpeg**: 音频格式转换（获取音频时长）
- **mimo-asr skill**: 语音识别 (`~/Documents/learn-claude-code/skills/mimo-asr/`)
- **faster-whisper**（可选）: 词级时间戳 ASR，用于精确字幕对齐 `pip install faster-whisper`

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

**⚠️ gen-img.sh 大响应失败的备选方案**：

gen-img.sh 使用 shell 变量接收 API 响应，当 base64 图片数据过大时可能报错"无法解析 API 响应"。**此时必须使用 Python+curl 方案绕过 shell 变量限制**：

```python
# 从 JSON 文件读取 prompt，用 curl 调用 API，Python 解码 base64
import json, subprocess, base64, tempfile

with open("news-pipeline/prompts/image-prompts-YYYY-MM-DD.json") as f:
    prompts = json.load(f)

for item in prompts:
    prompt = item["prompt"]
    output_path = f"news-pipeline/images/scene{item['scene']}.png"

    # 用 curl 发请求，响应写入临时文件（绕过 shell 变量大小限制）
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp_path = tmp.name

    subprocess.run([
        "curl", "-s", "-X", "POST", f"{api_url}/v1/images/generations",
        "-H", f"Authorization: Bearer {api_key}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"model": "gpt-image-1", "prompt": prompt, "size": "1536x1024", "n": 1}),
        "-o", tmp_path
    ], check=True)

    with open(tmp_path) as f:
        resp = json.load(f)

    img_b64 = resp["data"][0]["b64_json"]
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(img_b64))
```

**注意事项**:
- 使用 `1536x1024` (16:9 横屏)
- 所有图片保持统一风格
- 生成后立即预览，不满意可重新生成
- **必须逐张生成**：API 有并发限制，一张生成完成后再生成下一张，不可并行
- **Prompt 必须从 JSON 文件读取**，不能用简化版本替代（JSON 中的详细 prompt 才是最终调用的）

### Phase 6: TTS 配音

**先生成 TTS 音频，再用字数比例估算字幕时间轴。**

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

### Phase 7: ASR 验证（mimo-asr）

**用 ASR 识别 TTS 音频，验证转录结果与脚本文本是否一致。**

#### 7.1 调用 mimo-asr 识别

```bash
# 逐场景识别 TTS 音频
for i in 1 2 3 4 5 6 7; do
  bash ~/Documents/learn-claude-code/skills/mimo-asr/scripts/mimo-asr.sh \
    --audio "news-pipeline/voiceover/scene${i}.wav" \
    --language zh \
    --output "news-pipeline/2026-05-29/asr/scene${i}.txt"
done
```

#### 7.2 ASR 转录 vs 脚本文本对比

对比 ASR 输出与原始脚本文本，检查：
- 是否有漏词、多词
- 专有名词是否正确（模型名、公司名）
- 数字是否准确

```python
def verify_asr(asr_text: str, script_text: str) -> dict:
    """
    对比 ASR 转录与脚本文本
    
    返回: {"match": bool, "diff": str}
    """
    # 去除标点和空格后比较
    clean_asr = re.sub(r'[^\w]', '', asr_text)
    clean_script = re.sub(r'[^\w]', '', script_text)
    
    match = clean_asr == clean_script
    return {"match": match, "asr": asr_text, "script": script_text}
```

**如果 ASR 发现脚本与实际发音不一致**：以 ASR 转录文本为准更新字幕。

### Phase 8: 字幕生成（FunASR 逐句对齐）

**FunASR 字符级 ASR + 逐句对齐 + 无间隙填充。**

> **核心原则**：先 TTS 生成音频，再用 FunASR 提取字符级时间戳，逐小句在 ASR 输出中滑动窗口匹配。一处匹配失败不影响其他句子。

#### 8.0.1 字体使用规范（必须遵守）

**⚠️ 重要：禁止使用商用字体，避免版权风险！**

**推荐字体（免费可商用）**：
| 字体名称 | 类型 | 适用场景 | 许可证 |
|----------|------|----------|--------|
| PingFang SC | 系统字体 | macOS 字幕 | Apple EULA |
| Microsoft YaHei | 系统字体 | Windows 字幕 | Microsoft EULA |
| Noto Sans SC | 开源字体 | 跨平台字幕 | Apache 2.0 |
| Source Han Sans | 开源字体 | 高质量字幕 | Apache 2.0 |
| WenQuanYi Micro Hei | 开源字体 | Linux 字幕 | GPL |

**禁止使用的字体**：
- ❌ 思源黑体（部分版本有商用限制）
- ❌ 方正字体（需要商业授权）
- ❌ 汉仪字体（需要商业授权）
- ❌ 造字工房字体（需要商业授权）
- ❌ 任何需要付费授权的字体

**字体配置示例**（Subtitles.tsx）：
```tsx
// 使用系统字体，避免 Google Fonts 网络加载超时
const fontFamily = '"PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif';
```

**字体大小规范**：
- 标题：48-56px，加粗
- 字幕：40-48px，加粗
- 辅助文字：32-36px，常规

**颜色规范**：
- 主文字：#FFFFFF（白色）
- 描边/阴影：黑色半透明（rgba(0,0,0,0.8)）
- 背景：黑色半透明（rgba(0,0,0,0.75)）

**注意事项**：
- 始终使用系统字体或开源字体
- 定期检查字体许可证是否变更
- 如需使用新字体，先确认商用许可
- 保留字体许可证文件以备查验

#### 8.0 结束语字幕生成

**每个视频必须包含结束语，增强用户互动和品牌认知。**

**结束语模板**：
```
今天AI圈真是又热闹又魔幻，
觉得有用点个赞，关注不迷路，
我们下期见！
```

**结束语生成流程**：
1. 生成结束语 TTS 音频（scene7.wav）
2. 获取结束语音频时长（约 6-8 秒）
3. 生成结束语字幕（3-4 条）
4. 添加到字幕文件末尾
5. 更新视频总时长

**结束语字幕示例**：
```json
[
  {
    "text": "今天AI圈真是又热闹又魔幻，",
    "startMs": 101520,
    "endMs": 104520
  },
  {
    "text": "觉得有用点个赞，",
    "startMs": 104520,
    "endMs": 105520
  },
  {
    "text": "关注不迷路，",
    "startMs": 105520,
    "endMs": 106520
  },
  {
    "text": "我们下期见！",
    "startMs": 106520,
    "endMs": 107920
  }
]
```

**注意事项**：
- 结束语开始时间 = 前一个场景结束时间
- 结束语字幕时长 = 结束语音频时长
- 每条字幕约 2-3 秒
- 结束语文案可根据当期内容微调

#### 8.1 语义拆句（8-18 字小句）

```python
def semantic_split(text: str, min_chars: int = 6, max_chars: int = 18) -> list:
    """
    按语义拆成 8-18 字小句。

    规则：
    1. 优先在逗号、顿号、破折号处断开
    2. 保持英文专有名词完整（Opus 4.8、Fast Mode、Claude Code）
    3. 保持数字+单位完整（30美元、16个号）
    4. 合并 <min_chars 的短句到前一句
    """
    # 先按句号/叹号/问号拆成大句
    major_sentences = re.split(r"[。！？]+", text)
    major_sentences = [s.strip() for s in major_sentences if s.strip()]

    result = []
    for major in major_sentences:
        if len(major) <= max_chars:
            result.append(major)
            continue

        # 按逗号/顿号/破折号拆分
        parts = re.split(r"([，、——]+)", major)
        segments = []
        i = 0
        while i < len(parts):
            seg = parts[i]
            if i + 1 < len(parts) and re.match(r"^[，、——]+$", parts[i + 1]):
                seg = seg + parts[i + 1]
                i += 2
            else:
                i += 1
            if seg.strip():
                segments.append(seg.strip())

        # 合并过短的段
        merged = []
        buf = ""
        for seg in segments:
            if buf and len(buf) + len(seg) > max_chars:
                merged.append(buf)
                buf = seg
            else:
                buf = (buf + seg) if buf else seg
        if buf:
            merged.append(buf)

        # 对仍然过长的段做二次拆分
        for seg in merged:
            if len(seg) <= max_chars:
                result.append(seg)
            else:
                text_buf = seg
                while len(text_buf) > max_chars:
                    cut = _find_best_split(text_buf, max_chars)
                    if cut <= 0:
                        cut = max_chars
                    result.append(text_buf[:cut].strip())
                    text_buf = text_buf[cut:].strip()
                if text_buf:
                    result.append(text_buf)

    # 合并相邻过短的句
    final = []
    for s in result:
        if final and len(s) < min_chars and len(final[-1]) + len(s) <= max_chars:
            final[-1] = final[-1] + s
        else:
            final.append(s)

    return final


def _find_best_split(text: str, max_chars: int) -> int:
    """
    找到最佳断句位置，保护英文单词不被拆分。

    优先级：
    1. 在 max_chars 附近找标点符号（逗号、顿号、破折号）
    2. 在 max_chars 附近找英文单词边界（空格）
    3. 如果都没有，回退到 max_chars 位置
    """
    # 在 max_chars 附近搜索最佳断点
    search_range = min(8, max_chars // 3)

    # 优先找标点
    for offset in range(search_range, 0, -1):
        pos = max_chars - offset
        if 0 <= pos < len(text) and text[pos] in '，、——':
            return pos + 1

    # 找英文单词边界（空格处断开）
    for offset in range(search_range, 0, -1):
        pos = max_chars - offset
        if 0 <= pos < len(text) and text[pos] == ' ':
            return pos

    # 回退：从 max_chars 向前找非英文字符位置，避免拆分英文单词
    pos = max_chars
    while pos > 0 and text[pos - 1].isalnum() and text[pos - 1].isascii():
        pos -= 1

    return pos if pos > 0 else max_chars
```

#### 8.2 FunASR 字符级时间戳提取

```python
from funasr import AutoModel

def asr_extract_chars(audio_path: str) -> list:
    """用 FunASR paraformer-zh 提取字符级时间戳"""
    model = AutoModel(model="paraformer-zh")
    result = model.generate(input=audio_path, batch_size_s=300)

    chars = []
    if result and len(result) > 0:
        text = result[0].get("text", "")
        timestamps = result[0].get("timestamp", [])
        tokens = text.split(" ")
        if len(tokens) == len(timestamps):
            for token, ts in zip(tokens, timestamps):
                if token.strip():
                    chars.append({"char": token.strip(), "start": ts[0], "end": ts[1]})
    return chars
```

#### 8.3 逐句滑动窗口对齐

```python
def align_single_sentence(sentence: str, expanded: list, search_start: int) -> dict:
    """在 expanded 字符序列中搜索 sentence 的最佳匹配位置"""
    script_text = sentence.replace(" ", "")
    best_start = -1
    best_score = -1
    best_end = -1

    search_end = min(len(expanded), search_start + len(script_text) * 4)

    for i in range(search_start, search_end):
        matched_chars = 0
        si = 0
        skip_count = 0
        last_j = i

        for j in range(i, len(expanded)):
            if si >= len(script_text):
                break
            while si < len(script_text) and not script_text[si].isalnum():
                si += 1
            if si >= len(script_text):
                break

            if expanded[j]["char"].lower() == script_text[si].lower():
                matched_chars += 1
                si += 1
                skip_count = 0
                last_j = j + 1
            elif not expanded[j]["char"].isalnum():
                continue
            elif skip_count < 5:
                skip_count += 1
            else:
                break

        if matched_chars > 0:
            score = matched_chars / len(script_text)
            if score > best_score and matched_chars >= len(script_text) * 0.25:
                best_score = score
                best_start = i
                best_end = last_j

        if best_score >= 0.7:
            break

    if best_score > 0.25 and best_start >= 0:
        end_idx = min(best_end - 1, len(expanded) - 1)
        return {"startMs": expanded[best_start]["start"], "endMs": expanded[end_idx]["end"]}
    return None
```

#### 8.4 填充未匹配字幕 + 无间隙后处理

```python
def fill_unmatched(captions: list, scene_duration_ms: int) -> list:
    """用前后锚点 + 字数比例填充未匹配字幕"""
    # 前锚点：前一个已匹配字幕的 endMs
    # 后锚点：后一个已匹配字幕的 startMs
    # 在可用窗口内按字数比例分配
    # 场景首尾用全场景字数比例覆盖
    ...

def ensure_no_gaps(captions: list, scene_duration_ms: int, max_gap_ms: int = 500) -> list:
    """后处理：如果相邻字幕间隙 > 500ms，将前一句 endMs 延伸"""
    for i in range(1, len(captions)):
        gap = captions[i]["startMs"] - captions[i - 1]["endMs"]
        if gap > max_gap_ms:
            captions[i - 1]["endMs"] = captions[i]["startMs"] - 50
    return captions
```

#### 8.5 完整流程

```
脚本文本 → 语义拆句(8-15字) → FunASR提取字符级时间戳
    → 逐句滑动窗口匹配 → 填充未匹配(前后锚点+字数比例)
    → 无间隙后处理 → 累加偏移 → 输出 captions.json
```

**与旧方案对比**：

| 对比项 | 旧方案（字数比例估算） | 新方案（FunASR 逐句对齐） |
|--------|----------------------|--------------------------|
| 时间轴来源 | 字数比例公式 | FunASR 词级时间戳 |
| 对齐粒度 | 整段 | 8-15字小句 |
| 失败影响 | 整段空白 | 仅该句，自动填充 |
| 间隙处理 | 无 | ensure_no_gaps 后处理 |
| 专有名词 | 可能拆分 | 语义拆句保护 |

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
- 字幕内容必须与音频内容一致，不能错位
- 音频时长决定场景时长，不能用估算值

**🔴 铁律：每个音频必须对应 1 张图，禁止 audioId=0 的无声场景！**

> **教训**：曾出现 IPO 新闻拆成 2 张图但只有 1 段音频，导致第二张图场景 audioId=0（有字幕但无声音）。用户反馈："0:12 有字幕没声音"。

**正确做法**：
- 有 N 段音频 → 场景数 = N → 每个场景都有音频
- 每段音频只配 1 张图，即使音频较长也只用一张图（不要拆图）
- **如果某段音频特别长（>20s），可以考虑拆成多段音频，但必须保证每段音频都有对应图片**
- **绝对禁止** `audioId: 0` 的场景配置——有字幕没声音会让用户以为视频有问题

**场景数量确定公式**：
```
场景数 = 音频文件数（每段音频 = 1 个场景 = 1 张图）
```

**错误示例（禁止）**：
```tsx
// ❌ 错误：scene2 没有音频，导致 0:12-0:24 有字幕没声音
{ imageId: 1, audioId: 1, duration: 12.0 },  // IPO part 1
{ imageId: 2, audioId: 0, duration: 11.68 }, // IPO part 2 — 没有音频！
```

**正确示例**：
```tsx
// ✅ 正确：每个场景都有音频
{ imageId: 1, audioId: 1, duration: 23.68 },  // IPO 完整音频，一张图
```

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
A professional Chinese AI news studio cover image. A male news anchor in a dark navy suit with white shirt and dark tie sits at a modern curved news desk, hands clasped, looking directly at camera with serious expression. Behind him are multiple large display screens arranged in a grid showing: {本期核心新闻相关的视觉元素，如终端界面、产品截图、数据图表等}. The studio has dramatic blue and red neon lighting, with red accent lights along the desk edges and blue ambient lighting. In the top right corner, display the text "今日羊报 AI" on the first line and "AI 新闻" on the second line in large white Chinese characters. In the bottom center, display the date "{YYYY-MM-DD}" in large white bold text. The overall mood is professional and authoritative. Professional broadcast news photography style, photorealistic, highly detailed, cinematic lighting, 16:9 aspect ratio.
```

**模板要素**（必须包含）：
| 要素 | 位置 | 说明 |
|------|------|------|
| 新闻主播 | 画面中央 | 男性，深色西装，白色衬衫，深色领带，双手交叉放桌面 |
| 新闻台 | 底部 | 现代弧形设计，红色霓虹灯条 |
| 多屏背景 | 主播身后 | 2x3 或 3x3 网格，展示本期新闻相关画面 |
| 品牌文字 | 右上角 | 「今日羊报 AI」+「AI 新闻」，白色大字 |
| 日期 | 底部居中 | YYYY-MM-DD 格式，白色粗体 |
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
- **Phase 9（渲染前校验）是强制步骤，不可跳过**
- **Phase 12（B站自动上传）需要用户确认后执行**

### Phase 12: B站自动上传（Playwright MCP）

**使用 Playwright MCP 自动化浏览器操作，将视频上传到B站。**

#### Step 12.1: 打开B站上传页面

```python
# 使用 Playwright MCP 打开浏览器
browser_navigate("https://member.bilibili.com/platform/upload/video/frame")
```

#### Step 12.2: 上传视频文件

```python
# 等待页面加载完成
browser_wait_for("text=上传视频")

# 上传视频文件
browser_file_upload("news-pipeline/YYYY-MM-DD/video/【今日羊报AI】{核心标题} | YYYY-MM-DD.mp4")
```

#### Step 12.3: 等待上传完成

```python
# 等待上传进度完成（通常需要几分钟）
browser_wait_for("text=上传完成")
```

#### Step 12.4: 上传封面

```python
# 点击封面上传区域
browser_click("element=封面上传区域")

# 上传封面图片
browser_file_upload("news-pipeline/YYYY-MM-DD/cover.png")
```

#### Step 12.5: 设置创作声明

```python
# 选择创作声明：个人观点
browser_click("element=创作声明下拉框")
browser_click("text=个人观点")
```

#### Step 12.6: 填写简介

```python
# 读取 publish.json 获取简介
# 填写简介内容
browser_type("element=简介输入框", "publish.json 中的 description")
```

#### Step 12.7: 填写标签

```python
# 读取 publish.json 获取标签
# 逐个添加标签
for tag in publish_json["platform"]["bilibili"]["tags"]:
    browser_type("element=标签输入框", tag)
    browser_press_key("Enter")
```

#### Step 12.8: 加入合集

```python
# 点击加入合集按钮
browser_click("element=加入合集")

# 选择「今日羊报AI」合集
browser_click("text=今日羊报AI")
```

#### Step 12.9: 选择推荐活动

```python
# 选择第一个推荐的活动
browser_click("element=推荐活动列表第一项")
```

#### Step 12.10: 设置定时发布

```python
# 计算最近的发布时间（12:00/14:00/20:00）
import datetime

now = datetime.datetime.now()
publish_times = [
    now.replace(hour=12, minute=0, second=0, microsecond=0),
    now.replace(hour=14, minute=0, second=0, microsecond=0),
    now.replace(hour=20, minute=0, second=0, microsecond=0),
]

# 找到最近的未来时间
future_times = [t for t in publish_times if t > now]
if future_times:
    nearest_time = min(future_times)
else:
    # 如果都过了，用明天12:00
    nearest_time = publish_times[0] + datetime.timedelta(days=1)

# 点击定时发布
browser_click("element=定时发布")

# 设置日期和时间
browser_type("element=日期输入框", nearest_time.strftime("%Y-%m-%d"))
browser_type("element=时间输入框", nearest_time.strftime("%H:%M"))
```

#### Step 12.11: 确认发布

```python
# 点击发布按钮
browser_click("element=发布按钮")

# 等待发布成功
browser_wait_for("text=发布成功")
```

#### 完整自动化流程

```python
def auto_upload_bilibili(video_path: str, cover_path: str, publish_info: dict):
    """
    自动上传视频到B站
    
    参数:
        video_path: 视频文件路径
        cover_path: 封面图片路径
        publish_info: publish.json 内容
    """
    # 1. 打开上传页面
    browser_navigate("https://member.bilibili.com/platform/upload/video/frame")
    
    # 2. 上传视频
    browser_file_upload(video_path)
    browser_wait_for("text=上传完成")
    
    # 3. 上传封面
    browser_click("element=封面上传区域")
    browser_file_upload(cover_path)
    
    # 4. 设置创作声明
    browser_click("element=创作声明下拉框")
    browser_click("text=个人观点")
    
    # 5. 填写简介
    browser_type("element=简介输入框", publish_info["description"])
    
    # 6. 填写标签
    for tag in publish_info["platform"]["bilibili"]["tags"]:
        browser_type("element=标签输入框", tag)
        browser_press_key("Enter")
    
    # 7. 加入合集
    browser_click("element=加入合集")
    browser_click("text=今日羊报AI")
    
    # 8. 选择推荐活动
    browser_click("element=推荐活动列表第一项")
    
    # 9. 设置定时发布
    nearest_time = calculate_nearest_publish_time()
    browser_click("element=定时发布")
    browser_type("element=日期输入框", nearest_time.strftime("%Y-%m-%d"))
    browser_type("element=时间输入框", nearest_time.strftime("%H:%M"))
    
    # 10. 确认发布
    browser_click("element=发布按钮")
    browser_wait_for("text=发布成功")
    
    return {"success": True, "publish_time": nearest_time.isoformat()}
```

#### 注意事项

- 执行前需要用户确认（风险操作）
- 上传过程可能需要 2-5 分钟（取决于视频大小和网速）
- 封面图片必须是 16:9 比例，建议 1920x1080
- 标签最多 10 个，每个标签不超过 20 字符
- 合集「今日羊报AI」需要提前在B站创建
- 定时发布时间必须是未来时间

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
8. ASR 验证：mimo-asr 识别 TTS 音频，对比脚本文本
9. 字幕生成：标点断句 → 字数比例估算时间轴
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
