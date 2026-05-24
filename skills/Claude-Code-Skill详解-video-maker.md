# Claude Code Skill 详解：video-maker

> **版本**: 2.0.0 | **更新日期**: 2026-05-24 | **主要变更**: 集成 mimo-tts 替换 macOS say

## 一、Skill 是什么

Skill（技能）是 Claude Code 的扩展机制，允许用户定义可复用的专业能力。它比 Command（命令）更强大：

| 特性 | Command | Skill |
|------|---------|-------|
| 调用方式 | 用户手动 `/command` | Claude 自动触发 + 用户手动 |
| 文件结构 | 单个 `.md` 文件 | 目录，含 `SKILL.md` + 脚本/参考资料 |
| 典型用途 | 动作型："帮我做 X" | 知识型 + 执行型："知道 X 并执行 X" |
| 可捆绑资源 | 不能 | 可以（脚本、模板、API 配置等） |

**一句话理解**：Command 是快捷操作按钮，Skill 是会自动识别场景并执行标准流程的领域专家。

---

## 二、video-maker Skill 说明（v2.0.0）

> **v2.0.0 更新**：将 macOS `say` TTS 替换为 `mimo-tts` skill，支持多种音色和风格控制。

### 功能

基于 Remotion 的视频生成工具，支持：
- 从文本脚本自动生成视频
- 调用 `gen-img` skill 生成 AI 场景图片
- 调用 `mimo-tts` skill 生成中文配音（支持多种音色和风格）
- 自动生成与音频同步的字幕（TikTok 风格）
- 使用 TransitionSeries 实现场景转场
- 输出 1920x1080 H.264 视频

### 触发条件

当用户提到以下关键词时，自动触发：
- 制作视频 / 生成视频 / 剪辑视频
- create video / generate video / make video
- 文字转视频 / 脚本转视频
- 任何请求从文本/脚本生成视频的语句

### 技术架构

```
用户: "根据这个脚本制作视频"
        ↓
Claude 检测到关键词 "制作视频" → 激活 video-maker skill
        ↓
读取 SKILL.md → 解析用户意图（脚本内容、输出路径等）
        ↓
┌─────────────────────────────────────────────────────┐
│  Phase 1: 资源准备                                    │
│  ├── 解析脚本 → 拆分为多个场景                         │
│  ├── 调用 gen-img skill → 生成每场景的 AI 图片         │
│  └── 调用 mimo-tts skill → 生成每场景的配音 WAV        │
├─────────────────────────────────────────────────────┤
│  Phase 2: 字幕生成                                    │
│  ├── 读取音频时长 → durations.json                    │
│  ├── 按标点拆分文本 → 短句                            │
│  └── 按字符比例分配时间 → captions.json                │
├─────────────────────────────────────────────────────┤
│  Phase 3: Remotion 渲染                               │
│  ├── 组装 Composition → TransitionSeries              │
│  ├── 添加音频 + 字幕覆盖层                            │
│  └── 渲染输出 → video.mp4                             │
└─────────────────────────────────────────────────────┘
```

---

## 三、创建详细过程

### 第 1 步：分析需求

项目来源：基于 `ai-tools-video` 实践项目总结

核心需求：
- 用户提供文本脚本（Markdown 格式）
- 自动生成 AI 配图 + 配音 + 字幕
- 输出可发布的视频文件

**技术选型：**

| 组件 | 选择 | 原因 |
|------|------|------|
| 视频框架 | Remotion | React 生态，组件化，易于扩展 |
| 图片生成 | gen-img (GPT-Image-2) | 已有 skill，质量高 |
| 配音 | mimo-tts (MiMo V2.5) | 多音色、多风格、支持克隆 |
| 字幕 | 自定义 JSON | 精确控制时间轴 |
| 转场 | @remotion/transitions | 声明式，支持 fade/slide |

### 第 2 步：创建 Skill 目录结构

```bash
mkdir -p ~/.claude/skills/video-maker/scripts
```

最终结构：
```
~/.claude/skills/video-maker/
├── SKILL.md                        # 入口文件（触发条件 + 执行步骤）
└── scripts/
    ├── init-project.sh             # 初始化 Remotion 项目
    ├── generate-voiceover.py       # TTS 配音生成
    ├── generate-captions.py        # 字幕 JSON 生成
    └── render-video.sh             # 视频渲染
```

### 第 3 步：编写 SKILL.md

这是 Skill 的核心文件，包含：

1. **Frontmatter** — name、description、version
2. **触发条件** — 关键词列表，匹配用户输入
3. **前置条件** — Remotion、gen-img、macOS、ffmpeg
4. **执行步骤** — 8 步标准流程
5. **文件结构** — 项目目录规范
6. **错误处理** — 常见问题排查

**关键设计决策：**

| 决策 | 选择 | 原因 |
|------|------|------|
| 配音方案 | mimo-tts | 多音色、多风格、支持音色克隆 |
| 字幕格式 | JSON + Sequence | 精确到毫秒的逐句同步 |
| 转场时长 | 15 帧 (0.5s) | 平滑但不拖沓 |
| 视频编码 | H.264 CRF 18 | 兼容性好，质量高 |
| 字体 | NotoSansSC | Google Fonts 中文字体 |

### 第 4 步：编写配音生成脚本

`generate-voiceover.py` 负责 TTS 生成：

```python
# 核心逻辑：
# 1. 读取脚本文本，按场景拆分
# 2. 调用 mimo-tts skill 生成 WAV
# 3. 用 ffprobe 获取时长
# 4. 输出 durations.json
```

**mimo-tts 调用方式：**
```bash
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "<场景旁白>" \
  --voice "冰糖" \
  --style "温柔" \
  --output "scene1.wav"
```

**音色选择（mimo-tts）：**

| 音色 | 性别 | 特点 | 适用场景 |
|------|------|------|----------|
| 冰糖 | 女 | 甜美女声 | 温馨、活泼内容 |
| 茉莉 | 女 | 清新女声 | 清新、自然内容 |
| 苏打 | 男 | 清爽男声 | 科技、商务内容 |
| 白桦 | 男 | 沉稳男声 | 严肃、专业内容 |
| 曼波 | 克隆 | 个性化音色 | 特殊需求 |

**风格选择：**

| 风格 | 适用场景 |
|------|----------|
| 温柔 | 情感类、故事类内容 |
| 活泼 | 娱乐类、教育类内容 |
| 深沉 醇厚 | 纪录片、文学类内容 |
| 开心 | 轻松愉快的内容 |

### 第 5 步：编写字幕生成脚本

`generate-captions.py` 负责字幕时间轴：

```python
# 核心逻辑：
# 1. 读取 durations.json 获取每场景时长
# 2. 按标点符号拆分文本为短句
# 3. 按字符数比例分配时间
# 4. 计算场景偏移量（考虑转场重叠）
# 5. 输出 captions.json
```

**字幕格式（@remotion/captions 兼容）：**

```json
{
  "text": "大家好，",
  "startMs": 0,
  "endMs": 741,
  "timestampMs": 0,
  "confidence": 1.0
}
```

### 第 6 步：编写项目初始化脚本

`init-project.sh` 一键创建 Remotion 项目：

```bash
# 核心逻辑：
# 1. 创建目录结构（src、public、out）
# 2. 生成 package.json（含所有依赖）
# 3. 生成 tsconfig.json
# 4. 生成基础组件（Root、Composition、Subtitles 等）
# 5. 安装 npm 依赖
```

### 第 7 步：编写渲染脚本

`render-video.sh` 封装渲染命令：

```bash
# 核心逻辑：
# 1. 检查项目结构
# 2. 安装依赖（如需要）
# 3. 执行 npx remotion render
# 4. 输出文件信息
```

### 第 8 步：测试验证

实际项目 `ai-tools-video` 验证：

| 测试项 | 结果 |
|--------|------|
| 7 场景视频生成 | 成功 |
| AI 图片生成（gen-img） | 7 张 1536x1024 PNG |
| TTS 配音（mimo-tts） | 7 段 WAV，总时长 368.7s |
| 字幕同步 | 201 条，逐句匹配 |
| 最终渲染 | 1920x1080，6.1 分钟，179.9MB |

---

## 四、对话中的相关讨论

### Q: 为什么用 mimo-tts 而不是 macOS say 或其他 TTS？

**A**:
- **mimo-tts**：支持多种音色和风格，支持音色克隆，语音质量高
- **macOS `say`**：系统内置但音色有限，不支持风格控制
- **edge-tts**：曾尝试但遇到 403 错误（被微软封禁）
- **OpenAI TTS**：需要额外 API 费用，中文音色较少
- mimo-tts 提供最佳的中文语音合成体验

### Q: 字幕如何与音频精确同步？

**A**: 
1. 先用 `ffprobe` 获取每段音频的精确时长
2. 按标点符号将文本拆分为短句（每句 5-15 字）
3. 按字符数比例分配时间（中文语速约 4 字/秒）
4. 计算场景偏移量（考虑 0.5s 转场重叠）
5. 生成 `captions.json`，每条包含 `startMs` 和 `endMs`

### Q: 如何自定义视频风格？

**A**: 修改以下组件：

| 组件 | 文件 | 可定制项 |
|------|------|----------|
| 场景样式 | `src/scenes/ToolScenes.tsx` | 背景图、渐变、文字布局 |
| 字幕样式 | `src/components/Subtitles.tsx` | 字体大小、颜色、位置、动画 |
| 转场效果 | `src/Composition.tsx` | fade、slide、自定义 |
| 全局色彩 | `src/styles.ts` | 背景色、强调色、文字色 |

### Q: 支持哪些视频格式？

**A**: 
- **输出格式**：MP4 (H.264)
- **分辨率**：1920x1080 (默认)，可配置
- **帧率**：30fps (默认)，可配置
- **质量**：CRF 18 (高质量)，可调整 (18-28)

### Q: 视频时长有限制吗？

**A**: 
- 理论上无限制，但渲染时间与视频时长成正比
- 实测 6 分钟视频渲染约 3-5 分钟
- 建议单个视频控制在 1-10 分钟
- 超长视频可拆分为多个子项目

### Q: 如何添加背景音乐？

**A**: 在 `SceneWithAudio.tsx` 中添加额外的 `<Audio>` 组件：

```tsx
import { Audio } from '@remotion/media';
import { staticFile, interpolate, useCurrentFrame } from 'remotion';

export const SceneWithAudio: React.FC<Props> = ({ audioFile, children }) => {
  const frame = useCurrentFrame();
  
  // 背景音乐音量渐入
  const volume = interpolate(frame, [0, 30], [0, 0.3], {
    extrapolateRight: 'clamp',
  });

  return (
    <>
      <Audio src={staticFile(`voiceover/${audioFile}`)} />
      <Audio src={staticFile('bgm.mp3')} volume={volume} />
      {children}
    </>
  );
};
```

---

## 五、文件内容

Skill 已备份至本项目 `skills/video-maker/` 目录，完整文件请查看：

| 文件 | 说明 | 链接 |
|------|------|------|
| SKILL.md | 入口文件（触发条件 + 执行步骤） | [查看](video-maker/SKILL.md) |
| init-project.sh | Remotion 项目初始化脚本 | [查看](video-maker/scripts/init-project.sh) |
| generate-voiceover.py | TTS 配音生成脚本 | [查看](video-maker/scripts/generate-voiceover.py) |
| generate-captions.py | 字幕 JSON 生成脚本 | [查看](video-maker/scripts/generate-captions.py) |
| render-video.sh | 视频渲染脚本 | [查看](video-maker/scripts/render-video.sh) |
| mimo-tts Skill | 语音合成 Skill（依赖） | [查看](mimo-tts/SKILL.md) |
| gen-img Skill | AI 图片生成 Skill（依赖） | 外部 Skill |

---

## 六、使用方式

### 自动触发（推荐）

直接用自然语言描述你想生成的视频：

```
用户: "根据这个脚本制作一个视频"
Claude: [自动激活 video-maker skill → 解析脚本 → 生成资源 → 渲染视频]

用户: "帮我把这个文案转成视频，要有配音和字幕"
Claude: [自动激活 → 生成 AI 图片 + TTS + 字幕 → 输出视频]

用户: "create a video from this script with subtitles"
Claude: [自动激活 → 英文流程]
```

### 手动调用脚本

```bash
# 1. 初始化项目
bash ~/.claude/skills/video-maker/scripts/init-project.sh my-video

# 2. 生成配音（使用 mimo-tts）
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "场景旁白文本" \
  --voice "冰糖" \
  --style "温柔" \
  --output my-video/public/voiceover/scene1.wav

# 3. 生成字幕
python3 ~/.claude/skills/video-maker/scripts/generate-captions.py \
  scenes.json durations.json my-video/public/captions.json

# 4. 渲染视频
bash ~/.claude/skills/video-maker/scripts/render-video.sh my-video out/video.mp4
```

### 脚本格式

输入脚本应使用 Markdown 格式，按场景分节：

```markdown
# 视频标题

## Scene 1: 开场
大家好，今天分享五个实用工具...

## Scene 2: 工具介绍
第一个工具是 Claude Code...

## Scene 3: 总结
最后总结一下...
```

---

## 七、实战案例：5 个 AI 效率工具视频

### 项目概览

| 项目 | 值 |
|------|-----|
| 脚本来源 | B站视频脚本 |
| 场景数量 | 7 个 |
| 总时长 | 6.1 分钟 |
| 分辨率 | 1920x1080 |
| 文件大小 | 179.9MB |

### 生成流程

```
Step 1: 解析脚本 → 7 个场景
        ↓
Step 2: gen-img 生成 7 张场景图片 (并行)
        ↓
Step 3: mimo-tts 生成 7 段配音
        ↓
Step 4: 生成 201 条字幕 (captions.json)
        ↓
Step 5: Remotion 渲染 → out/ai-tools-video.mp4
```

### 资源文件

```
ai-tools-video/public/
├── images/
│   ├── scene1_opening.png      # 开场背景
│   ├── scene2_claude_code.png  # Claude Code 场景
│   ├── scene3_cursor.png       # Cursor 场景
│   ├── scene4_copilot.png      # Copilot 场景
│   ├── scene5_v0.png           # v0.dev 场景
│   ├── scene6_bolt.png         # bolt.new 场景
│   └── scene7_summary.png      # 总结场景
├── voiceover/
│   ├── scene1_opening.wav      # 开场配音
│   ├── scene2_claude_code.wav  # ...配音
│   ├── ...
│   ├── scene7_summary.wav      # 总结配音
│   └── durations.json          # 音频时长
└── captions.json               # 201 条字幕
```

### 渲染命令

```bash
cd ai-tools-video
npx remotion render AIToolsVideo out/ai-tools-video.mp4 --codec h264 --crf 18
```

---

## 八、扩展方向

### 短期优化

1. **Whisper 语音识别** — 用真实音频生成字幕，替代估算
2. **背景音乐** — 添加 BGM 支持
3. **更多转场** — 支持 zoom、wipe 等转场效果

### 长期规划

1. **一键流水线** — 从脚本到视频全自动化
2. **多语言 TTS** — 支持英文、日文等语音
3. **模板系统** — 预设多种视频风格模板
4. **MCP 集成** — 封装为 MCP 工具，支持远程调用

---

## 九、mimo-tts 集成说明

### 为什么选择 mimo-tts

| 特性 | mimo-tts | macOS say | edge-tts |
|------|----------|-----------|----------|
| 音色数量 | 5+ 预设 + 克隆 | 有限 | 有限 |
| 风格控制 | 支持 | 不支持 | 不支持 |
| 音色克隆 | 支持 | 不支持 | 不支持 |
| 中文质量 | 高 | 中 | 高 |
| API 依赖 | 需要 | 无 | 需要 |

### mimo-tts 使用示例

```bash
# 使用预设音色
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "欢迎观看本视频" \
  --voice "冰糖" \
  --style "温柔" \
  --output scene1.wav

# 使用克隆音色
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "欢迎观看本视频" \
  --clone ~/.claude/skills/mimo-tts/voices/曼波.mp3 \
  --output scene1.wav

# 使用保存的音色配置
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "欢迎观看本视频" \
  --profile "曼波" \
  --output scene1.wav
```

---

## 十、相关资源

- Claude Code 官方文档: https://docs.anthropic.com/en/docs/claude-code
- Remotion 官方文档: https://www.remotion.dev/docs
- @remotion/transitions: https://www.remotion.dev/docs/transitions
- @remotion/captions: https://www.remotion.dev/docs/captions
- Google Fonts (NotoSansSC): https://fonts.google.com/noto/specimen/Noto+Sans+SC
- mimo-tts Skill: `~/.claude/skills/mimo-tts/`
- gen-img Skill: `~/.claude/skills/gen-img/`
