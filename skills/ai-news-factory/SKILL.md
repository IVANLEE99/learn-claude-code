---
name: ai-news-factory
description: AI News Factory - 从日报 Markdown 自动生成短视频的完整 Pipeline。触发词: "AI日报", "新闻工厂", "news factory", "日报视频", "生成日报视频", "AI news video"
version: 1.2.0
---

# AI News Factory — 日报短视频自动生成 v1.2.0

将 AI 日报 Markdown 自动转化为 B站风格短视频，完整 Pipeline：日报 → 事件切分 → 视频脚本 → 分镜 → 图片 → TTS → 字幕 → 视频合成 → B站上传。

**核心原则：字数比例估算字幕时间轴（TTS 语速稳定，字数比例比 ASR 更可靠）。**

## ⚡ 权限预授权（必须在执行前完成）

**在开始 Pipeline 之前，必须先获得用户的一次性预授权。执行过程中不再逐个询问权限。**

### 预授权检查清单

向用户展示以下清单，请求一次性确认：

```
🎬 AI News Factory 权限预授权

执行以下操作需要你的授权，确认后全程不再询问：

📁 文件操作
  ☐ 读取日报 Markdown 文件
  ☐ 写入脚本、分镜、Prompt、字幕等文件
  ☐ 复制资源到 video-project/public/

🔧 Shell 执行
  ☐ 调用 mimo-tts.sh 生成配音
  ☐ 调用 ffprobe 获取音频时长
  ☐ 调用 npx remotion render 渲染视频

🌐 API 调用
  ☐ 图片生成 API（gpt-image-2）
  ☐ TTS API（mimo-tts）

🖥️ 浏览器操作（Phase 12 上传时）
  ☐ Playwright MCP 打开B站上传页面
  ☐ 自动填写标题、简介、标签
  ☐ 自动上传视频和封面
  ☐ 自动点击投稿

请回复「确认」或「全部授权」开始执行。
```

### 预授权实现

用户确认后，记录授权状态，后续所有工具调用不再询问：

```python
# 授权状态追踪
PERMISSIONS = {
    "file_read": True,      # 用户已授权
    "file_write": True,
    "shell_exec": True,
    "api_call": True,
    "browser": True,
}
```

**注意**：如果用户在某个 Phase 拒绝了权限，记录该拒绝并在后续跳过相关操作。

## 触发条件

- "AI日报", "新闻工厂", "news factory"
- "日报视频", "生成日报视频", "AI news video"
- "把日报做成视频", "日报转视频"

## 前置依赖

- **mimo-tts skill**: 语音合成 (`~/Documents/learn-claude-code/skills/mimo-tts/`)
- **ffmpeg**: 音频格式转换（获取音频时长）
- **mimo-asr skill**: 语音识别（可选，用于 ASR 验证）
- **FunASR**: 字符级时间戳提取（`pip install funasr`）
- **Remotion**: 视频渲染（`news-pipeline/video-project/`）
- **Playwright MCP**: B站自动上传

## 执行流程

### Phase 1: 输入与事件切分

**输入**: 日报 Markdown 文件路径或直接粘贴内容。

**Step 1.1**: 读取日报内容，提取所有独立新闻事件。

**Step 1.2**: 对每个事件打分排序，展示给用户：

```
已识别以下热点事件，请确认要制作视频的事件：
1. [事件1] (重要性: 9/10) — 浏览/回复数
2. [事件2] (重要性: 8/10)
3. [事件3] (重要性: 7/10)
...
```

**Step 1.3**: 用户确认选择（可选全部或部分事件）。

### Phase 2: 视频脚本生成

对每个选中事件，按模板生成脚本。

**风格要求**:
- 像 B站 AI 科技 UP 主
- 快节奏、有情绪、不书面
- 总时长 60-120 秒
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

**主方案**: 使用 Python+curl 直接调用图片生成 API（绕过 gen-img.sh 的 shell 变量限制）。

```python
import json, subprocess, base64, tempfile, os, time

API_URL = "http://api.luka77.cc"  # 主 API
API_KEY = "用户提供的 key"
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
            "-o", tmp_path
        ], check=True, timeout=120)
        with open(tmp_path) as f:
            resp = json.load(f)
        if "error" in resp:
            return False, resp["error"].get("message", str(resp["error"]))
        img_b64 = resp["data"][0].get("b64_json", "")
        if img_b64:
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(img_b64))
            return True, "OK"
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
| 1 | luka77 | http://api.luka77.cc | gpt-image-2 | 2026-06-04 验证可用 |
| 2 | windhub | https://windhub.cc | gpt-image-1 | 需检查配额 |
| 3 | littlesheep | https://ai.littlesheep.cc | - | 需用户提供 key |
| 4 | ioll | https://eo.ioll.pp.ua | - | 需用户提供 key |

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

**配音要求**:
- 推荐音色: 阿根
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

**v1.2.0 方案：字数比例估算为主，FunASR 为备选。**

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

### Phase 10: 封面与发布信息

#### 10.1 生成视频封面

使用图片生成 API 生成封面（1536x1024，16:9）：

**封面模板 Prompt**：
```
A professional Chinese AI news studio cover image. A male news anchor in a dark navy suit with white shirt and dark tie sits at a modern curved news desk, hands clasped, looking directly at camera with serious expression. Behind him are multiple large display screens arranged in a grid showing: {本期核心新闻相关的视觉元素}. The studio has dramatic blue and red neon lighting, with red accent lights along the desk edges and blue ambient lighting. In the top right corner, display the text "今日羊报 AI" on the first line and "AI 新闻" on the second line in large white Chinese characters. In the bottom center, display the date "{YYYY-MM-DD}" in large white bold text. Professional broadcast news photography style, photorealistic, highly detailed, cinematic lighting, 16:9 aspect ratio.
```

输出到 `news-pipeline/YYYY-MM-DD/cover.png`

#### 10.2 生成发布信息

生成 `news-pipeline/YYYY-MM-DD/publish.json`：

```json
{
  "title": "【今日羊报AI】{核心标题} | YYYY-MM-DD",
  "description": "视频简介，2-3句话概括本期内容",
  "tags": ["今日羊报AI", "AI日报", "..."],
  "platform": {
    "bilibili": {
      "title": "【今日羊报AI】{核心标题}｜{N}条重磅AI新闻一次看完 | YYYY-MM-DD",
      "tags": ["今日羊报AI", "AI日报", "..."],
      "description": "B站简介"
    }
  }
}
```

**标题规则**: `【今日羊报AI】{核心标题} | YYYY-MM-DD`，B站追加 `｜{N}条重磅AI新闻一次看完`

#### 10.3 归档资源

```bash
mkdir -p news-pipeline/YYYY-MM-DD/{scripts,storyboards,prompts,images,voiceover,captions,video}
cp news-pipeline/YYYY-MM-DD/images/scene*.png news-pipeline/YYYY-MM-DD/images/
cp news-pipeline/YYYY-MM-DD/voiceover/scene*.wav news-pipeline/YYYY-MM-DD/voiceover/
cp news-pipeline/YYYY-MM-DD/captions/captions.json news-pipeline/YYYY-MM-DD/captions/
cp "news-pipeline/video-project/out/【今日羊报AI】*.mp4" news-pipeline/YYYY-MM-DD/video/
```

### Phase 11: B站自动上传（Playwright MCP）

**⚠️ 执行前需要用户确认（风险操作）。权限已在预授权阶段获得。**

#### 11.0 处理浏览器锁

如果 Playwright MCP 报错 "Browser is already in use"：

```bash
# 1. 关闭现有浏览器进程
ps aux | grep -i "chromium\|chrome" | grep -i "playwright"
kill <PID>

# 2. 删除锁文件
rm -f ~/Library/Caches/ms-playwright/mcp-chrome-*/SingletonLock
```

#### 11.1 打开上传页面

```
browser_navigate("https://member.bilibili.com/platform/upload/video/frame")
```

#### 11.2 上传视频

```
browser_click("element=点击上传或将视频拖拽到此区域")  # 触发 file chooser
browser_file_upload("news-pipeline/YYYY-MM-DD/video/【今日羊报AI】*.mp4")
browser_wait_for("text=上传完成", time=120)
```

#### 11.3 上传封面

```
browser_click("element=封面设置")  # 打开封面编辑弹窗
browser_click("element=上传封面")  # 触发 file chooser
browser_file_upload("news-pipeline/YYYY-MM-DD/cover.png")
browser_click("element=完成")  # 确认封面
```

#### 11.4 设置创作声明

```
browser_click("textbox=请选择符合您视频内容的创作声明")  # 打开下拉框
browser_click("listitem=个人观点，仅供参考")  # 选择（不是「含AI生成内容」）
```

#### 11.5 填写简介（Quill 编辑器）

```javascript
browser_evaluate("""() => {
  const editor = document.querySelector('.ql-editor');
  if (editor) {
    editor.innerHTML = '<p>第一行简介</p><p><br></p><p>第二行简介</p>';
    editor.dispatchEvent(new Event('input', { bubbles: true }));
  }
}""")
```

#### 11.6 填写标签

```
# 标签输入框: textbox "按回车键Enter创建标签"
# 最多 10 个标签
tags = ["今日羊报AI", "AI日报", "OpenAI", "ChatGPT", ...]
for tag in tags:
    browser_type("textbox=按回车键Enter创建标签", tag)
    browser_press_key("Enter")
```

#### 11.7 加入合集

```
browser_click("element=请选择合集")  # 展开下拉框
browser_click("generic=「今日羊报 AI」")  # 选择合集
```

#### 11.8 确认投稿

```
browser_click("element=立即投稿")
browser_wait_for("text=稿件投递成功")
```

#### B站上传 UI 要点（2026-06-04 实测）

| 组件 | 类型 | 操作方式 |
|------|------|----------|
| 视频上传 | file chooser | 点击上传区域 → file_upload |
| 封面设置 | 弹窗 | 点击封面设置 → 上传封面 → 完成 |
| 创作声明 | bcc-select | 点击 textbox → 点击 listitem |
| 简介 | Quill 编辑器 | JS 注入 `.ql-editor` |
| 标签 | 输入框 | type + Enter，最多 10 个 |
| 合集 | 自定义下拉框 | 点击展开 → 选择合集名 |
| 投稿按钮 | 按钮 | 点击「立即投稿」 |

**常见坑**：
- `browser_file_upload` 必须在 file chooser 对话框打开后才能调用
- 创作声明**必须选「个人观点，仅供参考」**
- 简介用 Quill 编辑器，直接 `browser_type` 可能不生效，推荐 JS 注入
- 封面上传需要两步：先点「封面设置」打开弹窗，再点「上传封面」触发 file chooser

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
│   ├── asr/                    # ASR 转录文本（可选）
│   ├── video/                  # 最终视频
│   │   └── 【今日羊报AI】*.mp4
│   ├── cover.png               # 视频封面
│   └── publish.json            # 发布信息
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

## 注意事项

- **权限预授权是第一步**，必须在执行前完成
- 每个 Phase 完成后向用户展示中间结果，确认后继续
- 图片生成失败时自动重试一次
- TTS 使用 mimo-tts，推荐音色「阿根」
- 视频总时长建议 60-120 秒
- 事件数量建议 3-6 个
- **Phase 8（渲染前校验）是强制步骤，不可跳过**
- **Phase 11（B站上传）需要用户确认后执行**
