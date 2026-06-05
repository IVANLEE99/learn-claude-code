---
name: ai-news-factory
description: AI News Factory - 从日报 Markdown 自动生成短视频+图文的完整 Pipeline。触发词: "AI日报", "新闻工厂", "news factory", "日报视频", "生成日报视频", "AI news video"
version: 1.4.0
---

# AI News Factory — 日报短视频自动生成 v1.4.0

将 AI 日报 Markdown 自动转化为 B站风格短视频 + 多平台发布内容，完整 Pipeline：日报 → 去重 → 事件切分 → 视频脚本 → 分镜 → 图片 → TTS → 字幕 → 视频合成 → 封面 → 多平台发布信息 → 公众号图文 → B站上传。

**核心原则：字数比例估算字幕时间轴（TTS 语速稳定，字数比例比 ASR 更可靠）。**

## ⚡ 权限预授权（必须在执行前完成）

**在开始 Pipeline 之前，必须先获得用户的一次性预授权。执行过程中不再逐个询问权限。**

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

🌐 API 调用
  ☐ 图片生成 API（用户提供 URL + Key）
  ☐ TTS API（mimo-tts）

🖥️ 浏览器操作（Phase 12 上传时）
  ☐ Playwright MCP 打开B站上传页面
  ☐ 自动填写标题、简介、标签
  ☐ 自动上传视频和封面
  ☐ 自动点击投稿

请回复「确认」或「全部授权」开始执行。
```

## 触发条件

- "AI日报", "新闻工厂", "news factory"
- "日报视频", "生成日报视频", "AI news video"
- "把日报做成视频", "日报转视频"

## 前置依赖

- **mimo-tts skill**: 语音合成 (`~/Documents/learn-claude-code/skills/mimo-tts/`)
- **ffmpeg**: 音频格式转换（获取音频时长）
- **Remotion**: 视频渲染（`news-pipeline/video-project/`）
- **Playwright MCP**: B站自动上传
- **图片生成 API**: 用户提供 URL + Key（支持 OpenAI 兼容格式）

## 执行流程

### Phase 0: 获取用户输入

向用户确认以下信息（可在预授权时一并收集）：

```
需要你提供：
1. 📄 日报文件路径（默认: data/reports/YYYY-MM-DD.md）
2. 🖼️ 图片生成 API URL（如 https://ai.prism.uno）
3. 🔑 图片生成 API Key
```

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

**参考模板**: `templates/script-template.md`

### Phase 3: 分镜生成

根据视频脚本生成分镜表，每个脚本段落对应 1 个分镜。

| 镜号 | 时长 | 镜头类型 | 画面内容 | 字幕重点 | 转场 |
|------|------|----------|----------|----------|------|
| 1 | 3s | 特写 | AI 芯片电路 | Hook 文字 | 淡入 |
| 2 | 5s | 全景 | 科技新闻编辑室 | 事件标题 | 切换 |

**参考模板**: `templates/storyboard-template.md`

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
| 2 | prism | https://ai.prism.uno | gpt-image-2 | 2026-06-05 验证可用 |
| 3 | luka77 | http://api.luka77.cc | gpt-image-2 | 2026-06-04 验证可用 |
| 4 | windhub | https://windhub.cc | gpt-image-1 | 需检查配额 |

**API 选择逻辑**：
1. 优先使用用户提供的 API
2. 如果报错（配额不足、渠道不存在），尝试下一个
3. 如果所有 API 都不可用，提示用户提供可用的 API

**注意事项**:
- 使用 `1536x1024` (16:9 横屏)
- **必须逐张生成**：API 有并发限制
- **必须从 JSON 文件读取 Prompt**，不能用简化版本
- 每张图片生成后重试一次（如果失败）

### Phase 6: TTS 配音

根据视频脚本逐场景生成配音：

```bash
bash ~/Documents/learn-claude-code/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "配音文本" \
  --profile "阿根" \
  --style "兴奋 新闻播报" \
  --output "news-pipeline/YYYY-MM-DD/voiceover/sceneN.wav"
```

**🔴 关键限制：mimo-tts.sh 使用 `mktemp` 生成临时文件，并行调用会导致文件名冲突和静默失败。必须逐场景串行执行！**

**配音要求**:
- 推荐音色: 阿根
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

### Phase 7: 字幕生成（字数比例估算）

**v1.4.0 方案：字数比例估算为主，FunASR 为备选。**

> **经验教训**：FunASR 逐句对齐在实际使用中匹配率偏低（部分场景仅 1/7），字数比例估算更稳定可靠。

#### 7.1 语义拆句（8-18 字小句）

```python
def smart_split(text, min_chars=8, max_chars=20):
    """Split text preserving English terms and ensuring min duration."""
    sentences = re.split(r"[。！？]", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    result = []
    for sent in sentences:
        if len(sent) <= max_chars:
            result.append(sent)
            continue
        parts = re.split(r"([，、——]+)", sent)
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
        result.extend(merged)
    final = []
    for s in result:
        if final and len(s) < min_chars and len(final[-1]) + len(s) <= max_chars:
            final[-1] = final[-1] + s
        else:
            final.append(s)
    return final
```

#### 7.2 字数比例时间轴估算

```python
def generate_captions(sentences, scene_duration_ms, offset_ms):
    """Generate captions with char-ratio timing, min 1.5s per caption."""
    total_chars = sum(len(s.replace(" ", "")) for s in sentences)
    raw_durations = []
    for sent in sentences:
        chars = len(sent.replace(" ", ""))
        dur = scene_duration_ms * chars / total_chars if total_chars > 0 else scene_duration_ms / len(sentences)
        raw_durations.append(max(dur, 1500))  # 最小 1.5s

    total_adj = sum(raw_durations)
    scale = scene_duration_ms / total_adj if total_adj > 0 else 1

    captions = []
    current_ms = offset_ms
    for i, sent in enumerate(sentences):
        dur = int(raw_durations[i] * scale)
        captions.append({"text": sent, "startMs": current_ms, "endMs": current_ms + dur})
        current_ms += dur
    if captions:
        captions[-1]["endMs"] = offset_ms + scene_duration_ms
    return captions
```

#### 7.3 完整流程

```
脚本文本 → 语义拆句(8-20字) → 字数比例估算时间轴
    → 最小 duration 约束(1.5s) → 缩放到场景时长 → 输出 captions.json
```

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

```bash
cd video-project && npx remotion render AINewsVideo "out/【今日羊报AI】{核心标题} | YYYY-MM-DD.mp4" --codec h264 --crf 18
```

### Phase 10: 封面、发布信息与公众号图文

#### 10.1 生成视频封面

使用图片生成 API 生成封面（1536x1024，16:9）：

**封面模板 Prompt**：
```
A professional Chinese AI news studio cover image. A male news anchor in a dark navy suit with white shirt and dark tie sits at a modern curved news desk, hands clasped, looking directly at camera with serious expression. Behind him are multiple large display screens arranged in a grid showing: {本期核心新闻相关的视觉元素}. The studio has dramatic blue and red neon lighting, with red accent lights along the desk edges and blue ambient lighting. In the top right corner, display the text "今日羊报 AI" on the first line and "AI 新闻" on the second line in large white Chinese characters. In the bottom center, display the date "{YYYY-MM-DD}" in large white bold text. Professional broadcast news photography style, photorealistic, highly detailed, cinematic lighting, 16:9 aspect ratio.
```

输出到 `news-pipeline/YYYY-MM-DD/cover.png`

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
- B站：`【今日羊报AI】{核心标题}｜{N}条重磅AI新闻一次看完 | YYYY-MM-DD`
- 抖音/视频号：`{核心标题}｜今日羊报AI YYYY-MM-DD`（较短）
- 公众号：`{核心标题}｜今日羊报AI YYYY-MM-DD`

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

**⚠️ 执行前需要用户确认（风险操作）。权限已在预授权阶段获得。**

#### 11.0 处理浏览器锁

如果 Playwright MCP 报错 "Browser is already in use"：

```bash
# 1. 关闭现有浏览器进程
pkill -f "mcp-chrome-*" 2>/dev/null
sleep 2

# 2. 删除锁文件
rm -f ~/Library/Caches/ms-playwright/mcp-chrome-*/SingletonLock
```

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

## 注意事项

- **权限预授权是第一步**，必须在执行前完成
- 每个 Phase 完成后向用户展示中间结果，确认后继续
- 图片生成失败时自动重试一次
- TTS 使用 mimo-tts，推荐音色「阿根」
- **TTS 必须串行执行，禁止并行！**
- 视频总时长建议 60-120 秒（可适当放宽）
- 事件数量建议 4-6 个
- **Phase 1 去重是强制步骤，不可跳过**
- **Phase 8（渲染前校验）是强制步骤，不可跳过**
- **Phase 11（B站上传）需要用户确认后执行**
- **B站自定义下拉框必须用 JS evaluate，不能用 browser_click 文本匹配**
