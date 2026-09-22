---
name: post-to-video
description: 将论坛帖子/长文自动转化为短视频——按 3:4 竖版与 4:3 横版生成配图，再由 content.json 经 edge-tts 生成配音与字幕，最终合成带字幕视频。触发词: "帖子转视频", "post to video", "长文转视频", "帖子做视频", "图文转视频", "复盘视频", "帖子成片", linux.do 帖子视频
version: 1.0.1
---

# post-to-video — 帖子/长文 → 配图 + TTS + 字幕 → 短视频

把 **linux.do 帖子、Markdown 长文、粘贴正文** 结构化为 `content.json`，生成 **3:4 竖版 + 4:3 横版** 配图（走 `gen-img`），再按 `content.json` 的口播文本用 **edge-tts** 生成配音、用语义切行 + whisper 对齐生成字幕，最后用 **ffmpeg** 合成带字幕的短视频。

> 经验基础：本 skill 的 TTS / 字幕 / 合成 / 校验规则全部沉淀自 `ai-news-factory`（至 v3.38.0）的实战坑位，全文见 `references/experience.md`。**改动规则前先读它。**

## 触发条件

- 帖子转视频 / 长文转视频 / 帖子做视频 / 图文转视频 / 复盘视频
- 「把这个帖子做成视频」「帖子成片」
- 给出 `linux.do/t/topic/...` 并要求出视频
- post to video / forum post video

**不触发**：日报/周报/月报新闻流水线 → `ai-news-factory`；只生图不出视频 → `post-to-img`；纯 TTS → `edge-tts`。

## 依赖

| 依赖 | 用途 |
|------|------|
| `gen-img` skill | **唯一**生图出口：`bash ~/.claude/skills/gen-img/scripts/gen-img.sh` |
| `edge-tts`（pip 包） | TTS 配音，无需 API Key |
| `ffmpeg` / `ffprobe` | 转码、加速、合成、时长校验 |
| `faster-whisper` + `jieba` | 字幕词级时间锚 + 语义切行 |
| Playwright MCP | 抓取 `linux.do` 等需登录/反爬页面 |
| `post-to-img` skill（可选） | 复用其风格预设与 `build_prompt.py` 生成配图 prompt |

本 skill **禁止**自己 curl Images API；生图一律调用 gen-img 脚本。日志**禁止打印任何 API Key**。

## 端到端流程（必须按序）

```
用户输入（URL / 文件 / 粘贴）
        ↓
[1] 取文  fetch_post → source.md
        ↓
[2] 结构化  structure_content → content.json（含每场景口播 + 封面大字）
        ↓
[3] 确认（可选）  用户说「直接出片/开干」则跳过
        ↓
[4] 生图  gen_images.sh → images/sceneN-3x4.png + sceneN-4x3.png + 双封面
        ↓
[5] TTS  gen_tts_edge.py → voiceover/sceneN.wav（24kHz PCM16 单声道）
        ↓
[6] 字幕  gen_captions.py --dry-run 人工扫 → 全量 whisper → captions/captions.json
        ↓
[7] 合成  build_video.py → video/post-video-{3x4|4x3}.mp4（烧录字幕）
        ↓
[8] 校验交付  时长对齐 + 首帧/中段抽帧 Read 视觉校验
```

产出根目录：

```text
~/Documents/learn-claude-code/generated-videos/post-to-video/{slug}/
```

`slug` = 日期 + 标题拼音/topic-id 简化，例如 `20260921_2609603`。

### Step 1 — 取文 `fetch_post`

与 `post-to-img` Step 1 完全相同：

| 输入 | 动作 |
|------|------|
| `https://linux.do/t/topic/...` | Playwright：`browser_navigate` → `browser_evaluate` 抽 `#post_1 .cooked` 正文 + `h1` 标题 + 作者 |
| 其他公开 URL | `WebFetch`；失败再用 Playwright |
| 本地 `.md` / `.txt` | `Read` 文件 |
| 对话内粘贴 | 直接使用用户文本 |

linux.do 抽取脚本（evaluate）：

```js
() => {
  const title = document.querySelector('h1')?.innerText?.trim() || document.title;
  const author = document.querySelector('.topic-meta-data .username, .names .username')?.innerText?.trim() || '';
  const cooked = document.querySelector('#post_1 .cooked, article#post_1 .cooked, .topic-post:first-of-type .cooked')
    || document.querySelector('.cooked');
  return { title, author, url: location.href, body: cooked ? cooked.innerText.trim() : '' };
}
```

原文存 `{slug}/source.md`。

### Step 2 — 结构化 `structure_content` → content.json

在 post-to-img 的信息图结构之上，**增加视频必需的口播与封面字段**：

```json
{
  "title": "被优化了，第一天",
  "slug": "20260921_2609603",
  "source_url": "https://linux.do/t/topic/2609603",
  "hook": "前 5 秒钩子口播（保留原帖金句，1 句冲突 + 1 个数字最佳）",
  "cover_text": "封面大字第一行\n封面大字第二行",
  "scenes": [
    {
      "id": 1,
      "heading": "今天发生了什么",
      "voiceover": "该场景口播文本，≤80 字，说人话……",
      "image_brief": "该场景配图的画面要点（喂给 prompt 拼装）",
      "mascot_mood": "crying"
    }
  ],
  "closing": "结尾口播 + CTA"
}
```

**结构化规则：**

1. **scenes 数组顺序 = 播放顺序**（坑 209：重排顺序即可调整节奏，无需改文本）。
2. 口播必须 **「说人话」**：不要「各位观众大家好」式开场；用「说白了」「这事儿离谱在哪」等口语；每段 ≤ 80 字；保留情绪但不夸张（v2.5.0 经验）。
3. **封面大字铁律（坑 203）**：`cover_text` = Hook 原词短句两行（1 句冲突 + 1 个数字），**禁止**把整条 `title` 印上封面。`cover_text` 定稿必须早于生图；改 Hook 必须重出封面。
4. 保留原帖金句与事实，不编造；可归纳压缩。
5. 场景数建议 4–8 个；第 1 场景 = Hook（口播即 `hook` 字段）。

### Step 3 — 确认（可跳过）

默认展示：场景列表（heading + 口播字数）、封面大字、将生成的图片清单与尺寸、音色/语速。用户已说「直接出片 / 开干」→ 跳过。

### Step 4 — 生图（3:4 + 4:3，走 gen-img）

**尺寸表（ai-news-factory v3.35.0 起实测）：**

| 文件 | 比例 | 首选 size | 接口不认时 fallback | 用途 |
|------|------|-----------|---------------------|------|
| `images/sceneN-3x4.png` | 3:4 | `1024x1536` | `1152x1536` | 竖版视频画面 |
| `images/sceneN-4x3.png` | 4:3 | `1536x1152` | `1536x1024` | 横版视频画面 |
| `covers/vertical-3-4.png` | 3:4 | `1024x1536` | `1152x1536` | 抖音/视频号/公众号封面 |
| `covers/horizontal-4-3.png` | 4:3 | `1536x1152` | `1536x1024` | B站/通用封面 |

每个场景出 **两个比例各一张**（用户只要单一比例时减半）。prompt 由 Claude 按 post-to-img 风格预设拼装（默认 `kawaii-journal`；技术帖可 `clean-tech`），每场景 prompt 落盘 `prompts/sceneN.txt`。

用封装脚本批量生成（**自带续跑**：已存在且 >5KB 的文件跳过，只补缺失——坑：整批超时后禁止无条件重跑）：

```bash
# manifest.txt 每行: <相对路径>|<size>|<prompt文件>
bash ~/.claude/skills/post-to-video/scripts/gen_images.sh \
  ~/Documents/learn-claude-code/generated-videos/post-to-video/{slug} \
  manifest.txt
```

失败处理顺序：缩短 prompt 重试 1 次 → 换英文 prompt 重试 1 次 → 报告错误，**不编造图片**。封面文字（日期/封面大字）必须像素级准确：生成后 `Read` 视觉校验，糊字即重生；API 持续不可靠时用 Pillow 本地叠字兜底（见 `references/experience.md` §本地兜底）。

### Step 5 — TTS 配音 `gen_tts_edge.py`

**默认且唯一路径 = edge-tts**（坑 210：无需先试探别的端点）：

```bash
python3 ~/.claude/skills/post-to-video/scripts/gen_tts_edge.py \
  --dir ~/Documents/learn-claude-code/generated-videos/post-to-video/{slug} \
  --voice zh-CN-YunyangNeural --atempo 1.4
```

脚本行为（全部来自实战规则）：

1. **先清残留**：已有 `voiceover/scene*.wav` 一律 `shutil.move` 归档到 `voiceover/.stale_archive/`（不用 `rm`——自动权限会拦不可逆删除；残留旧音频是 desync 头号根因）。
2. **逐场景串行**合成（禁止并发），失败指数退避 5s→15s→30s 最多 3 次。
3. edge-tts 出 MP3 → `ffmpeg -filter:a atempo=1.4 -acodec pcm_s16le -ar 24000 -ac 1` 转 WAV。
4. 每场景校验文件大小 + ffprobe 时长 > 0，**禁止把空 wav 当成功**。
5. 全部完成后 ffprobe 实测时长写入 `voiceover/durations.json`——这是字幕偏移与视频分段的**唯一时长源**，禁止手填估算。

推荐音色：`zh-CN-YunyangNeural`（云扬，男声新闻风，默认）/ `YunxiNeural`（活泼）/ `XiaoxiaoNeural`（女声温暖）。`atempo=1.4` 显著压缩总时长；要原速就 `--atempo 1.0`。

### Step 6 — 字幕 `gen_captions.py`

**内容 100% 来自 content.json 口播文本，时间 100% 来自音频**（whisper 词级时间戳是唯一锚；字幕文字绝不依赖 ASR——ASR 对术语识别极差且修正字典永远追不上）。

```bash
# 1. 先 dry-run：只切行不加载 whisper，人工扫禁切反例（专名/动宾被切开、3 字闪行）
python3 ~/.claude/skills/post-to-video/scripts/gen_captions.py \
  --dir ~/.../{slug} --dry-run

# 2. 有专名（帖子里的产品名/人名/黑话）用 --extra-word 补 jieba 词典，可重复
python3 ~/.claude/skills/post-to-video/scripts/gen_captions.py \
  --dir ~/.../{slug} --extra-word OpenClaw --extra-word 被优化
```

切行规则（语义优先，勿改）：`。！？；` 强制断；`，、：` 仅当行 ≥16 字才断；允许略超至 20 字保住专名/动宾；超 20 黄金分割 40–60%；无合法切点整句保留，**禁止按字符下标硬切**；对齐后 <1s 的行并回上一行。

偏移按 **wav 文件实际时长**累加（含片尾静音），不用 whisper 的 `info.duration`（VAD 裁尾会让后面场景字幕整体提前——坑 208）。脚本会打印 `offset += file_dur=X (whisper Y)` 供对账。

产出 `captions/captions.json`（`text/startMs/endMs/sceneId`）。

### Step 7 — 视频合成 `build_video.py`

ffmpeg 轻量合成（无 Node/Remotion 依赖）：

```bash
# 竖版（抖音/视频号）：1080x1440
python3 ~/.claude/skills/post-to-video/scripts/build_video.py \
  --dir ~/.../{slug} --orientation vertical

# 横版（B站/通用）：1440x1080
python3 ~/.claude/skills/post-to-video/scripts/build_video.py \
  --dir ~/.../{slug} --orientation horizontal
```

脚本流程：读 `durations.json` → 每场景「图片循环 + wav」编码为等长分段 → concat 拼合 → 从 `captions.json` 生成 SRT → 烧录字幕（对齐 `ai-news-factory` `Subtitles.tsx`：PingFang SC，白字加粗，黑半透明圆角底 `rgba(0,0,0,0.75)` + padding 10/24 + radius 12，单行）→ 输出 `video/post-video-{3x4|4x3}.mp4`。

**渲染前校验（必须）**：图片数 == 音频数 == 场景数；三者不等先回 Step 4/5 补齐，禁止无声场景。

### Step 8 — 校验与交付（必须执行）

1. **时长对齐**：`ffprobe` 视频时长 ≈ `durations.json` 求和（音频总时长），差 >0.5s 说明分段时长与音频不同源，回 Step 5 重修（缺一步全链漂移）。不要用 captions 末条 `endMs` 当基准——它来自 whisper 实测发音结束时刻，天然早于场景尾部 pad 静音。
2. **抽帧视觉校验**：首帧 + 1–2 个场景切点抽帧 `Read` 检查画面与字幕：
   ```bash
   ffmpeg -y -i video/post-video-3x4.mp4 -vf "select=eq(n\,0)" -frames:v 1 /tmp/first.png
   ```
3. 汇报：视频路径、时长、分辨率、音色、atempo、场景数。
4. 同目录保留全链路产物：`source.md / content.json / prompts/ / images/ / covers/ / voiceover/ / captions/ / video/`。

**重跑任何一步的联动铁律**：重跑 TTS（哪怕只改一个场景）→ 必须重新 ffprobe 全部时长 → 重算 captions → 重渲染。四者必须来自同一批音频。

## 目录约定

```text
~/.claude/skills/post-to-video/
  SKILL.md
  references/experience.md      # ai-news-factory 经验总结（至 v3.38.0）
  scripts/gen_images.sh         # manifest 批量生图 + 断点续跑
  scripts/gen_tts_edge.py       # edge-tts 串行 TTS + atempo + 24k WAV
  scripts/gen_captions.py       # 语义切行 + whisper 词级对齐字幕
  scripts/build_video.py        # ffmpeg 分段合成 + 字幕烧录 + 校验

项目同步（必须双向一致）：
  skills/post-to-video/   ← 与系统 skill 同步

产出：
  ~/Documents/learn-claude-code/generated-videos/post-to-video/{slug}/
    source.md  content.json  prompts/  images/  covers/
    voiceover/  captions/  video/
```

## 质量检查清单（出片前）

- [ ] `cover_text` 是 Hook 短句两行，不是整条标题（坑 203）
- [ ] 口播说人话，每段 ≤ 80 字；scenes 顺序即播放顺序
- [ ] 图片数 == 音频数 == 场景数；图片均 >5KB
- [ ] 旧 wav 已归档 `.stale_archive/`，durations.json 来自本期 ffprobe
- [ ] 字幕 dry-run 人工扫过禁切反例；无 <1s 闪行
- [ ] 抽帧可见黑半透明圆角字幕底（对齐 Subtitles.tsx），不是裸白字
- [ ] 视频时长 vs durations.json 音频总时长差 ≤0.5s
- [ ] 首帧 + 场景切点抽帧已 Read 视觉校验
- [ ] 生图走 gen-img，日志无 API Key

## 快速命令示例

```text
# 从 linux.do 帖子出竖版视频
把 https://linux.do/t/topic/2609603 做成视频

# 粘贴正文 + 指定横版
帖子转视频：下面是正文……直接出片，要 4:3 横版

# 换音色 / 原速
用晓晓的声音、不要加速，把这个复盘做成竖版视频
```

## 版本

- **v1.0.1**（2026-09-22）：字幕烧录对齐 `ai-news-factory` `Subtitles.tsx`——Pillow PNG 叠黑半透明圆角底（`rgba(0,0,0,0.75)` / padding 10×24 / radius 12），不再只有白字黑边。
- **v1.0.0**（2026-09-21）：首版。取文 → content.json → gen-img 双比例配图（3:4/4:3）→ edge-tts 配音 → 语义切行 + whisper 对齐字幕 → ffmpeg 合成校验。经验规则沉淀自 ai-news-factory v3.38.0（见 references/experience.md）。
