---
name: post-to-video
description: 将论坛帖子/长文自动转化为短视频——按 3:4 竖版与 4:3 横版生成配图，再由 content.json 经 edge-tts 生成配音与字幕，最终合成带字幕视频。触发词: "帖子转视频", "post to video", "长文转视频", "帖子做视频", "图文转视频", "复盘视频", "帖子成片", linux.do 帖子视频
version: 1.0.5
---

# post-to-video — 帖子/长文 → 配图 + TTS + 字幕 → 短视频

把 **linux.do 帖子、Markdown 长文、粘贴正文** 结构化为 `content.json`，生成 **3:4 竖版 + 4:3 横版** 配图（走 `gen-img`），再按 `content.json` 的口播文本用 **edge-tts** 生成配音、用语义切行 + whisper 对齐生成字幕，最后用 **ffmpeg** 合成带字幕的短视频。

> 经验基础：本 skill 的 TTS / 字幕 / 合成 / 校验规则全部沉淀自 `ai-news-factory`（至 v3.38.0）的实战坑位，全文见 `references/experience.md`。**改动规则前先读它。**
>
> **合规**：脚本、生图、封面、`publish.json` 必须遵守 [`合规检查.md`](合规检查.md)。结果落盘 `{slug}/review-checklist.md`，禁止只口头说「合规」。

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
[2b] 合规  对照 合规检查.md → 落盘 review-checklist.md（脚本/生图/封面都要过）
        ↓
[2c] 帖子内容图（阻塞门，先于一切视频步骤）
     post-to-img 信息图 → 4:3 + 3:4 提示词 → 两张海报
        ↓
[3] 确认（可选）  用户说「直接出片/开干」则跳过口头确认，**不能跳过 2b 落盘，也不能跳过 2c**
        ↓
[4] 场景生图  gen_images.sh → 场景图 + 封面无字底图（.scratch）→ overlay_cover_text.py 两张正片
        ↓
[5] TTS  gen_tts_edge.py → voiceover/sceneN.wav（24kHz PCM16 单声道）
        ↓
[6] 字幕  gen_captions.py --dry-run 人工扫 → 全量 whisper → captions/captions.json
        ↓
[7] 合成  build_video.py → video/post-video-{3x4|4x3}.mp4（烧录字幕）
        ↓
[8] 校验交付  时长对齐 + 首帧/中段抽帧 Read 视觉校验
        ↓
[9] 发布文案  publish.json（标题 + 内容脉络 + 四平台）
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
6. **来源 / 称呼（合规硬规则）**：`source_url` 可留空；口播、字幕、画面、封面、简介 **禁止出现帖子来源**（linux.do / L站 / 链接）。称呼全部 **「道友+名字」**，禁止「佬友」裸用（不要套用 ai-news-factory 的「佬友→大家」）。
7. **用户名去下划线（坑 223）**：口播里的用户名去掉 `_`，用空格（`道友chen dragon`）。edge-tts 会把 `_` 读成「下划线」。`publish.json` 和图内文字保留原名。改了口播必须重跑对应场景 TTS。

### Step 2b — 合规对照（不可跳过落盘）

对照 [`合规检查.md`](合规检查.md) 勾选 **禁止词汇 / 脚本审核检查清单 / 平台合规审查规则 / 合规检查清单**。

```bash
# 清单复制到 slug 后逐项勾选（禁止只口头说合规）
cp ~/.claude/skills/post-to-video/合规检查.md 的清单段落 \
  → {slug}/review-checklist.md
```

未勾完禁止进 Step 2c。带娃选题：口播可点到「不敢请外人」，禁止虐婴细节与写实儿童主视觉。

### Step 2c — 帖子内容图（阻塞门，先于视频流程）

**先出整帖信息图，再做场景配图 / TTS / 字幕 / 合成。** 两张海报未通过视觉校验，禁止进 Step 4。

信息图不是封面，也不是场景帧：

| 产物 | 是什么 | 不是什么 |
|------|--------|----------|
| `posters/post-to-img-horizontal-poster.png` | 4:3 手账信息图，文字在图里 | 不是 `covers/horizontal-4-3.png` |
| `posters/post-to-img-vertical-poster.png` | 3:4 手账信息图，文字在图里 | 不是 `covers/vertical-3-4.png` |
| `images/sceneN-*.png` | 视频每一镜 | 不要用信息图代替分镜 |

风格对齐 `post-to-img` 的 kawaii-journal（奶油纸、草莓粉大标题、圆角卡片、仓鼠/白兔）。参考成片：`generated-images/post-to-img/20260921_2931081/poster.png` 与同目录 `prompt.txt`。

1. 另写 `posters/infographic.json`（post-to-img 的区块 schema：title / subtitle / sections / table / plan / tip / closing）。**禁止**拿它覆盖视频用的 `content.json`。
2. 标题 ≤14 字；bullet ≤28 字；称呼「道友+名字」；无论坛来源、无写实婴幼儿脸、不把伤害画出来。
3. 用 `post-to-img` 的 `build_prompt.py` 出两份提示词（竖版必须上下堆叠，不要三栏并排）。脚本会按 `--size` **自动写入画布锁定句**（「像素 W×H，宽高比严格 a:b」；真 3:4 = `1152x1536`，`1024x1536` 是 2:3）。实测服务端不认精确像素，但锁句能保证比例——不要手删：

```bash
SLUG=~/Documents/learn-claude-code/generated-videos/post-to-video/{slug}
python3 ~/.claude/skills/post-to-img/scripts/build_prompt.py \
  --content "$SLUG/posters/infographic.json" \
  --preset kawaii-journal --orientation horizontal --aspect 4:3 --size 1536x1152 \
  --prompt-name post-to-img-horizontal.txt --out-dir "$SLUG/prompts"
python3 ~/.claude/skills/post-to-img/scripts/build_prompt.py \
  --content "$SLUG/posters/infographic.json" \
  --preset kawaii-journal --orientation vertical --aspect 3:4 --size 1152x1536 \
  --prompt-name post-to-img-vertical.txt --out-dir "$SLUG/prompts"
```

4. manifest 只含这两张，走 `gen_images.sh`（quality/size fallback 与场景图相同）。gpt-image-2 能把中文排进信息图；grok 容易乱码，乱了就缩短 prompt 重试，不要改用封面叠字脚本硬贴整张信息图。

```text
posters/post-to-img-horizontal-poster.png|1536x1152|prompts/post-to-img-horizontal.txt
posters/post-to-img-vertical-poster.png|1152x1536|prompts/post-to-img-vertical.txt
```

5. `Read` 两张图：标题可辨、三区（或竖版上中下）都在、无站点水印。不过就重出。
6. **比例门（PIL 实测，必须）**：竖版宽高比 ≈0.75（3:4）、横版 ≈1.3333（4:3）。实测端点可能不认精确像素（2924762：请求 1152×1536 返回 1086×1448，等比 0.943×），**比例对即可用，比例不对必须重出**——禁止只看文件大小或只凭目测。通过后才进入 Step 3/4。

### Step 3 — 确认（可跳过口头确认）

默认展示：场景列表（heading + 口播字数）、封面大字、帖子内容图两张路径、将生成的场景图清单与尺寸、音色/语速、合规清单路径。用户已说「直接出片 / 开干」→ 跳过口头确认，**仍须完成 Step 2b 与 Step 2c**。

### Step 4 — 生图（3:4 + 4:3，走 gen-img）

**尺寸表（ai-news-factory v3.35.0 起实测）：**

| 文件 | 比例 | 首选 size | 接口不认时 fallback | 用途 |
|------|------|-----------|---------------------|------|
| `images/sceneN-3x4.png` | 3:4 | `1152x1536`（**1024x1536 是 2:3**） | `1024x1536` | 竖版视频画面 |
| `images/sceneN-4x3.png` | 4:3 | `1536x1152`（**grok 直接 `1536x1024`**） | `1536x1024` | 横版视频画面 |
| `covers/.scratch/*-notext.png` | 同上 | 同上 | 同上 | 无字底图，禁止当正片 |
| `covers/vertical-3-4.png` | 3:4 | Pillow 叠字产出 `1152x1536` | — | 抖音/视频号/公众号封面 |
| `covers/horizontal-4-3.png` | 4:3 | Pillow 叠字产出 `1536x1152` | — | B站/通用封面 |

每个场景出 **两个比例各一张**（用户只要单一比例时减半）。prompt 由 Claude 按 post-to-img 风格预设拼装（默认 `kawaii-journal`；技术帖可 `clean-tech`），每场景 prompt 落盘 `prompts/sceneN.txt`。

用封装脚本批量生成（**自带续跑**：已存在且 >5KB 的文件跳过，只补缺失——坑：整批超时后禁止无条件重跑）。`gen_images.sh` 按当前 `GEN_IMG_MODEL` 选 quality（grok → `medium/low`，禁止硬编码 `high`），并做 size fallback；非正片封面路径自动改写进 `covers/.scratch/`。

```bash
# manifest.txt 每行: <相对路径>|<size>|<prompt文件>
# 封面只写无字底图到 .scratch，不要直接写正片路径（正片由叠字脚本产出）
bash ~/.claude/skills/post-to-video/scripts/gen_images.sh \
  ~/Documents/learn-claude-code/generated-videos/post-to-video/{slug} \
  manifest.txt

python3 ~/.claude/skills/post-to-video/scripts/overlay_cover_text.py \
  --dir ~/Documents/learn-claude-code/generated-videos/post-to-video/{slug} \
  --both
```

封面 prompt **禁止**让模型写中文大字（grok 会出日英乱码）；写 `no text, no letters, no watermark, no website, no forum logo`。叠完 `Read` 视觉校验，糊字/不居中即重出。

失败处理顺序：缩短 prompt 重试 → 换英文 prompt → `gpt-image-2` 预扣费失败则切 `settings.json` 备用 `GEN_IMG_*_001`（grok-imagine-image），用完恢复主配置 → 仍失败报告错误，**不编造图片**。日志**禁止打印 API Key**。

**正片只许两张**：`covers/vertical-3-4.png` + `covers/horizontal-4-3.png`。中间图全部进 `.scratch/`。

### Step 5 — TTS 配音 `gen_tts_edge.py`

**默认且唯一路径 = edge-tts**（坑 210：无需先试探别的端点）：

```bash
python3 ~/.claude/skills/post-to-video/scripts/gen_tts_edge.py \
  --dir ~/Documents/learn-claude-code/generated-videos/post-to-video/{slug} \
  --voice zh-CN-YunyangNeural --atempo 1.4
```

脚本行为（全部来自实战规则）：

1. **先清残留**：已有 `voiceover/scene*.wav` 一律 `shutil.move` 归档到 `voiceover/.stale_archive/`（不用 `rm`——自动权限会拦不可逆删除；残留旧音频是 desync 头号根因）。**无 `--only` 时这是全量归档**（坑 225）：口播未定稿就跑会清掉已有好配音。只改几个场景用 `--only 6,7`，其余 wav 与其 `durations.json` 条目保留。
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

切行规则（语义优先，勿改）：`。！？；` 强制断；`，、：` 仅当行 ≥16 字才断；允许略超至 20 字保住专名/动宾；超 20 黄金分割 40–60%；无合法切点整句保留，**禁止按字符下标硬切**；对齐后 <1s 的行并回上一行，**合并后仍 ≤20 字**（坑 224：放宽到 24 会拼出 26 字行，42px 烧录时被右边缘裁掉；超长就保留短行）。

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
2. **抽帧视觉校验**：至少 6 个时间点抽帧 `Read`，必须覆盖**最长几条字幕**所在时刻，不只抽首帧和片尾。字幕被画幅右边缘切掉即回 Step 6 重切（坑 224：Pillow 预检报 995px 仍被裁，数字不能代替看帧）。
   ```bash
   ffmpeg -y -i video/post-video-3x4.mp4 -vf "select=eq(n\,0)" -frames:v 1 /tmp/first.png
   ```
3. 汇报：视频路径、时长、分辨率、音色、atempo、场景数。
4. 同目录保留全链路产物：`source.md / content.json / review-checklist.md / publish.json / prompts/ / images/ / covers/ / voiceover/ / captions/ / video/`。

**重跑任何一步的联动铁律**：重跑 TTS（哪怕只改一个场景）→ 必须重新 ffprobe 全部时长 → 重算 captions → 重渲染。四者必须来自同一批音频。

### Step 9 — 发布文案 `publish.json`

对照 `ai-news-factory` 四平台结构，但 **不要套用日报「今日羊报AI + 日期」报头**（那是新闻流水线规则）。帖子成片用内容标题；抖音 ≤30 字、视频号 ≤16 字且无 `.` `~`。必须包含 **内容脉络** `outline`。

```json
{
  "title": "《靠老人带娃，就是认命吗？》",
  "date": "YYYY-MM-DD",
  "slug": "YYYYMMDD_topicid",
  "cover_text": "靠老人带娃\n就是认命吗？",
  "outline": [
    "深夜吐苦水",
    "纠结（不敢请保姆 / 老人带娃旧模式）",
    "评论区一边倒（有人带就不错了）",
    "最扎心质问（道友laoyou：你就是她带大的）",
    "务实方案（育儿嫂 + 沟通）",
    "谁带娃谁说了算",
    "两条路",
    "结尾「每一代前进一点点就很好了」+ 评论区 CTA"
  ],
  "description": "2–3 句概括，无论坛来源，称呼用道友+名字",
  "tags": ["育儿", "带娃"],
  "platform": {
    "bilibili": { "title": "…", "partition": "生活", "tags": [], "description": "…" },
    "douyin":   { "title": "…", "tags": [], "description": "…" },
    "channels": { "title": "…", "tags": [], "description": "…" },
    "wechat":   { "title": "…", "article": "", "images": "covers/" }
  }
}
```

B站分区按内容选（生活向用「生活」，勿盲填「人工智能」）；标签 ≤10。简介遵守 `合规检查.md`。

## 目录约定

```text
~/.claude/skills/post-to-video/
  SKILL.md
  合规检查.md                   # 禁止词汇 / 脚本审核 / 平台合规 / 清单（强制对照）
  references/experience.md      # ai-news-factory 经验总结（至 v3.38.0）+ 2924762 坑
  scripts/gen_images.sh         # manifest 批量生图 + quality/size fallback + .scratch
  scripts/overlay_cover_text.py # 无字底图叠 cover_text（Pillow / STHeiti）
  scripts/gen_tts_edge.py       # edge-tts 串行 TTS + atempo + 24k WAV
  scripts/gen_captions.py       # 语义切行 + whisper 词级对齐字幕
  scripts/build_video.py        # ffmpeg 分段合成 + 字幕烧录 + 校验

项目同步（必须双向一致）：
  skills/post-to-video/   ← 与系统 skill 同步

产出：
  ~/Documents/learn-claude-code/generated-videos/post-to-video/{slug}/
    source.md  content.json  posters/infographic.json  review-checklist.md  publish.json
    prompts/  posters/post-to-img-{horizontal,vertical}-poster.png
    images/  covers/{vertical-3-4,horizontal-4-3}.png  covers/.scratch/
    voiceover/  captions/  video/
```

## 质量检查清单（出片前）

- [ ] `cover_text` 是 Hook 短句两行，不是整条标题（坑 203）
- [ ] 口播说人话，每段 ≤ 80 字；scenes 顺序即播放顺序
- [ ] 口播用户名无 `_`（否则 TTS 读出「下划线」）
- [ ] 字幕合并后每行 ≤20 字；抽帧覆盖最长字幕，确认没被右边缘裁掉
- [ ] 无帖子来源；称呼全部「道友+名字」
- [ ] `review-checklist.md` 已按 合规检查.md 落盘勾选
- [ ] 帖子内容图两张已出、PIL 实测比例（竖 ≈0.75 / 横 ≈1.3333）且 Read 通过，才开始场景配图与配音
- [ ] `posters/` 里是信息图，没有拿去替换 `covers/` 或 `images/sceneN`
- [ ] 图片数 == 音频数 == 场景数；图片均 >5KB
- [ ] `covers/` 根目录只有两张正片（1152×1536 / 1536×1152），中间图在 `.scratch/`
- [ ] 封面中文大字 Pillow 叠字且 Read 视觉校验通过
- [ ] 旧 wav 已归档 `.stale_archive/`，durations.json 来自本期 ffprobe
- [ ] 字幕 dry-run 人工扫过禁切反例；无 <1s 闪行
- [ ] 抽帧可见黑半透明圆角字幕底（对齐 Subtitles.tsx），不是裸白字
- [ ] 视频时长 vs durations.json 音频总时长差 ≤0.5s
- [ ] 首帧 + 场景切点抽帧已 Read 视觉校验
- [ ] 生图走 gen-img，日志无 API Key
- [ ] `publish.json` 含标题、内容脉络、四平台；抖音 ≤30 / 视频号 ≤16

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

- **v1.0.5**（2026-09-23）：按 2931081 成片补三条——口播用户名去掉 `_`（坑 223，否则读出「下划线」）；`merge_short_dwell` 合并上限从 24 收到 20 字，抽帧必须覆盖最长字幕（坑 224，26 字行被画幅右缘裁）；`gen_tts_edge.py` 增加 `--only`，全量重跑会归档全部现有 wav（坑 225）。
- **v1.0.3**（2026-09-22）：视频流程前增加阻塞门——用 post-to-img 先出 4:3 / 3:4 帖子内容图（`posters/post-to-img-horizontal-poster.png`、`posters/post-to-img-vertical-poster.png`）。竖版提示词上下堆叠。信息图不是封面，也不是分镜。
- **v1.0.2**（2026-09-22）：按 2924762 成片过程补全流水线——`合规检查.md`（脚本/生图/封面强制对照）+ `publish.json`（标题与内容脉络）+ `review-checklist.md` 落盘；`gen_images.sh` quality/size 按模型 fallback（grok 禁 high、4:3=1536x1024）；封面无字底图进 `.scratch/`，`overlay_cover_text.py` 叠 `cover_text`；正片只留两张。
- **v1.0.1**（2026-09-22）：字幕烧录对齐 `ai-news-factory` `Subtitles.tsx`——Pillow PNG 叠黑半透明圆角底（`rgba(0,0,0,0.75)` / padding 10×24 / radius 12），不再只有白字黑边。
- **v1.0.0**（2026-09-21）：首版。取文 → content.json → gen-img 双比例配图（3:4/4:3）→ edge-tts 配音 → 语义切行 + whisper 对齐字幕 → ffmpeg 合成校验。经验规则沉淀自 ai-news-factory v3.38.0（见 references/experience.md）。
