---
name: video-maker
description: 基于脚本生成视频，支持 AI 图片、MiMo TTS 配音和 Remotion 渲染。当用户说"制作视频"、"生成视频"、"剪辑视频"、"文字转视频"、"create video"、"generate video" 时触发。
version: 2.0.0
---

# video-maker — AI 视频生成 Skill

基于文本脚本自动生成视频，使用 AI 生成图片、MiMo TTS 配音和 Remotion 渲染。

## 触发条件

当用户提到以下关键词时，自动触发：
- 制作视频 / 生成视频 / 剪辑视频 / 文字转视频
- create video / generate video / make video
- 任何需要从文本/脚本生成视频的请求

## 前置条件

- **Remotion 项目**：必须在工作目录中初始化
- **gen-img skill**：用于 AI 图片生成（`~/.claude/skills/gen-img/`）
- **mimo-tts skill**：用于语音合成（`~/.claude/skills/mimo-tts/`）
- **Node.js 18+**：Remotion 运行环境
- **ffmpeg**：音频格式转换（可选）

## 环境变量

使用以下 skill 的配置，无需额外配置：
- gen-img: `GEN_IMG_API_URL`, `GEN_IMG_API_KEY`
- mimo-tts: 自动复用 `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`（含 xiaomimimo.com 时），或使用 `MIMO_TTS_API_URL` + `MIMO_TTS_API_KEY`

## 执行步骤

### 第 1 步：解析用户请求

从用户消息中提取：
- **script**（必填）：视频脚本文本或文件路径
- **output**（可选）：输出视频路径，默认 `out/video.mp4`
- **resolution**（可选）：视频分辨率，默认 `1920x1080`
- **fps**（可选）：帧率，默认 `30`
- **voice**（可选）：TTS 音色，默认 `冰糖`（中文女声）
- **style**（可选）：TTS 风格，默认无

### 第 2 步：创建 Remotion 项目

如果不存在 Remotion 项目，初始化一个：

```bash
# 创建项目目录
mkdir -p video-project/src video-project/public/images video-project/public/voiceover

# 初始化 package.json
cat > video-project/package.json << 'EOF'
{
  "name": "ai-video",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "remotion studio",
    "build": "remotion bundle",
    "render": "remotion render"
  },
  "dependencies": {
    "@remotion/cli": "4.0.463",
    "@remotion/google-fonts": "^4.0.463",
    "@remotion/media": "4.0.463",
    "@remotion/transitions": "^4.0.463",
    "react": "19.2.3",
    "react-dom": "19.2.3",
    "remotion": "4.0.463"
  },
  "devDependencies": {
    "@types/react": "19.2.7",
    "typescript": "5.9.3"
  }
}
EOF

# 安装依赖
cd video-project && npm install
```

### 第 3 步：生成场景图片

使用 gen-img skill 为每个场景生成图片：

```bash
# 使用 gen-img skill 生成图片
bash ~/.claude/skills/gen-img/scripts/gen-img.sh "<场景描述>" "video-project/public/images/sceneN.png" "1536x1024" "auto" 1 "png"
```

**图片提示词建议：**
- 视觉化描述场景（而非文本内容）
- 包含风格关键词："cinematic", "professional", "modern"
- 指定宽高比：16:9 用于横屏视频
- 所有场景保持一致的风格

### 第 4 步：生成配音

使用 mimo-tts skill 为每个场景生成配音：

```bash
# 使用 mimo-tts skill 生成配音
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "<场景旁白文本>" \
  --voice "冰糖" \
  --style "温柔 活泼" \
  --output "video-project/public/voiceover/sceneN.wav"
```

**批量生成配音脚本：**

```python
#!/usr/bin/env python3
"""使用 mimo-tts 生成视频配音"""
import subprocess
import json
import os

def generate_voiceover(text, output_path, voice="冰糖", style=""):
    """使用 mimo-tts 生成配音"""
    cmd = [
        "bash", os.path.expanduser("~/.claude/skills/mimo-tts/scripts/mimo-tts.sh"),
        "--text", text,
        "--voice", voice,
        "--output", output_path
    ]
    if style:
        cmd.extend(["--style", style])
    
    subprocess.run(cmd, check=True)
    
    # 获取音频时长
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", output_path
    ], capture_output=True, text=True)
    
    return float(result.stdout.strip())

# 场景列表
scenes = [
    {"id": "scene1", "text": "场景 1 旁白文本..."},
    {"id": "scene2", "text": "场景 2 旁白文本..."},
]

# 生成配音
durations = {}
for scene in scenes:
    output_path = f"video-project/public/voiceover/{scene['id']}.wav"
    duration = generate_voiceover(scene["text"], output_path)
    durations[scene["id"]] = duration
    print(f"{scene['id']}: {duration:.2f}s")

# 保存时长信息
with open("video-project/public/voiceover/durations.json", "w") as f:
    json.dump(durations, f, indent=2)
```

**音色选择建议：**
- 冰糖：甜美女声，适合温馨、活泼的内容
- 茉莉：清新女声，适合清新、自然的内容
- 苏打：清爽男声，适合科技、商务内容
- 白桦：沉稳男声，适合严肃、专业内容
- 曼波（克隆音色）：个性化音色

**风格选择建议：**
- 温柔：适合情感类、故事类内容
- 活泼：适合娱乐类、教育类内容
- 深沉 醇厚：适合纪录片、文学类内容
- 开心：适合轻松愉快的内容

### 第 5 步：生成字幕

创建与音频同步的 captions.json：

```python
#!/usr/bin/env python3
"""生成带精确时间轴的字幕 JSON"""
import json
import os
import re

def count_chars(text):
    """统计有效字符数"""
    return len(re.sub(r'[^一-鿿\w]', '', text))

def split_into_phrases(text):
    """按标点拆分文本为短句"""
    parts = re.split(r'([。！？，；：、])', text)
    phrases = []
    i = 0
    while i < len(parts):
        phrase = parts[i]
        if i + 1 < len(parts) and parts[i + 1] in '。！？，；：、':
            phrase += parts[i + 1]
            i += 2
        else:
            i += 1
        if phrase.strip():
            phrases.append(phrase)
    return phrases

def generate_captions(scenes, durations, output_path):
    """按字符比例分配时间生成字幕"""
    all_captions = []
    offset = 0.0
    transition_sec = 0.5  # 30fps 下 15 帧
    
    for scene in scenes:
        scene_id = scene["id"]
        total_duration = durations[scene_id]
        phrases = split_into_phrases(scene["text"])
        char_counts = [count_chars(p) for p in phrases]
        total_chars = sum(char_counts)
        
        current_time = 0.0
        for phrase, char_count in zip(phrases, char_counts):
            phrase_duration = total_duration * (char_count / total_chars)
            start_ms = (offset + current_time) * 1000
            end_ms = (offset + current_time + phrase_duration) * 1000
            
            all_captions.append({
                "text": phrase,
                "startMs": round(start_ms),
                "endMs": round(end_ms),
                "timestampMs": round(start_ms),
                "confidence": 1.0,
            })
            current_time += phrase_duration
        
        offset += total_duration - transition_sec
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_captions, f, ensure_ascii=False, indent=2)
    
    return len(all_captions)
```

### 第 6 步：创建 Remotion 组件

生成必要的 Remotion 文件：

#### Root.tsx
```tsx
import { Composition } from 'remotion';
import { MainComposition } from './Composition';

const FPS = 30;
// 从音频时长计算总时长
const DURATION_IN_FRAMES = 10974; // 所有场景时长之和

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="AIVideo"
      component={MainComposition}
      durationInFrames={DURATION_IN_FRAMES}
      fps={FPS}
      width={1920}
      height={1080}
    />
  );
};
```

#### Composition.tsx
```tsx
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { TransitionSeries, linearTiming } from '@remotion/transitions';
import { fade } from '@remotion/transitions/fade';
import { SceneWithAudio } from './components/SceneWithAudio';
import { Subtitles } from './components/Subtitles';

const TRANSITION_DURATION = 15; // 30fps 下 0.5 秒

export const MainComposition: React.FC = () => {
  return (
    <AbsoluteFill>
      <TransitionSeries>
        {/* 添加场景和转场 */}
        <TransitionSeries.Sequence durationInFrames={SCENE_DURATIONS.scene1}>
          <SceneWithAudio audioFile="scene1.wav">
            {/* 场景组件 */}
          </SceneWithAudio>
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_DURATION })}
        />
        {/* 更多场景... */}
      </TransitionSeries>
      <Subtitles />
    </AbsoluteFill>
  );
};
```

#### SceneWithAudio.tsx
```tsx
import React from 'react';
import { Audio } from '@remotion/media';
import { staticFile } from 'remotion';

interface SceneWithAudioProps {
  audioFile: string;
  children: React.ReactNode;
}

export const SceneWithAudio: React.FC<SceneWithAudioProps> = ({ audioFile, children }) => (
  <>
    <Audio src={staticFile(`voiceover/${audioFile}`)} />
    {children}
  </>
);
```

#### Subtitles.tsx
```tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  AbsoluteFill,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  useDelayRender,
  Sequence,
  interpolate,
  Easing,
} from 'remotion';
import { loadFont } from '@remotion/google-fonts/NotoSansSC';

const { fontFamily } = loadFont();

interface CaptionItem {
  text: string;
  startMs: number;
  endMs: number;
}

export const Subtitles: React.FC = () => {
  const [captions, setCaptions] = useState<CaptionItem[] | null>(null);
  const { delayRender, continueRender, cancelRender } = useDelayRender();
  const [handle] = useState(() => delayRender());
  const { fps } = useVideoConfig();

  const fetchCaptions = useCallback(async () => {
    try {
      const response = await fetch(staticFile('captions.json'));
      const data = await response.json();
      setCaptions(data);
      continueRender(handle);
    } catch (e) {
      cancelRender(e);
    }
  }, [continueRender, cancelRender, handle]);

  useEffect(() => {
    fetchCaptions();
  }, [fetchCaptions]);

  if (!captions) return null;

  return (
    <AbsoluteFill>
      {captions.map((caption, index) => {
        const startFrame = Math.round((caption.startMs / 1000) * fps);
        const endFrame = Math.round((caption.endMs / 1000) * fps);
        const durationInFrames = Math.max(1, endFrame - startFrame);

        return (
          <Sequence
            key={index}
            from={startFrame}
            durationInFrames={durationInFrames}
          >
            <SubtitleLine text={caption.text} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const SubtitleLine: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const fadeOut = interpolate(frame, [durationInFrames - 4, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.in(Easing.cubic),
  });
  const opacity = Math.min(fadeIn, fadeOut);

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-end',
        alignItems: 'center',
        paddingBottom: 80,
      }}
    >
      <div
        style={{
          background: 'rgba(0, 0, 0, 0.75)',
          borderRadius: 12,
          padding: '10px 24px',
          maxWidth: '85%',
          opacity,
        }}
      >
        <div
          style={{
            fontSize: 40,
            fontWeight: 'bold',
            fontFamily,
            color: '#FFFFFF',
            textAlign: 'center',
            lineHeight: 1.4,
            textShadow: '0 2px 8px rgba(0,0,0,0.8)',
          }}
        >
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};
```

### 第 7 步：渲染视频

执行最终渲染：

```bash
cd video-project && npx remotion render AIVideo out/video.mp4 --codec h264 --crf 18
```

**渲染选项：**
- `--codec h264`：H.264 视频编码（兼容性最好）
- `--crf 18`：恒定质量因子（越低质量越好，推荐 18-28）
- `--codec prores`：ProRes 输出（专业编辑用）

### 第 8 步：输出结果

报告：
- 输出视频路径
- 视频时长和分辨率
- 文件大小
- 场景数量和字幕数量

## 脚本结构

典型的视频脚本格式：

```
# 视频标题

## 场景 1：开场
场景 1 的旁白文本...

## 场景 2：主体内容
场景 2 的旁白文本...

## 场景 3：结尾
场景 3 的旁白文本...
```

**最佳实践：**
- 每个场景保持 20-60 秒
- 使用清晰的标点符号实现自然停顿
- 用清晰的标题分隔场景
- 建议总视频时长 1-5 分钟

## 文件结构

```
video-project/
├── package.json
├── src/
│   ├── Root.tsx
│   ├── Composition.tsx
│   ├── components/
│   │   ├── SceneWithAudio.tsx
│   │   └── Subtitles.tsx
│   └── scenes/
│       └── Scene*.tsx
├── public/
│   ├── images/
│   │   ├── scene1.png
│   │   └── scene2.png
│   ├── voiceover/
│   │   ├── scene1.wav
│   │   ├── scene2.wav
│   │   └── durations.json
│   └── captions.json
└── out/
    └── video.mp4
```

## 错误处理

- **TTS 失败**：检查 mimo-tts skill 是否安装，API Key 是否配置
- **图片生成失败**：检查 gen-img skill 是否安装，API Key 是否配置
- **渲染失败**：检查 Remotion 版本兼容性和 Node.js 版本
- **音频同步问题**：验证 durations.json 与实际音频文件匹配

## 自定义

### 场景转场
- 淡入淡出：`<TransitionSeries.Transition presentation={fade()} />`
- 滑动：`<TransitionSeries.Transition presentation={slide({ direction: 'from-right' })} />`
- 自定义：创建自定义 presentation 函数

### 字幕样式
- 字体：修改 `loadFont()` 参数
- 位置：修改 Subtitles.tsx 中的 `paddingBottom`
- 颜色：更新 `background` 和 `color` 样式
- 动画：调整 `interpolate` 时间

### 音色选项
- 冰糖：中文女声，甜美
- 茉莉：中文女声，清新
- 苏打：中文男声，清爽
- 白桦：中文男声，沉稳
- 曼波：克隆音色，个性化

### 风格选项
- 基础情绪：开心、悲伤、愤怒、平静
- 整体语调：温柔、活泼、严肃、深沉
- 音色定位：磁性、醇厚、清亮、甜美
- 方言：粤语、四川话、东北话

## 使用示例

### 示例 1：简单视频

```bash
# 1. 准备脚本
cat > script.md << 'EOF'
# 产品介绍视频

## 场景 1：开场
欢迎来到我们的产品介绍。

## 场景 2：功能展示
这是我们的核心功能。

## 场景 3：结尾
感谢观看，欢迎体验。
EOF

# 2. 生成视频
# Claude 会自动执行：
# - 解析脚本
# - 生成图片
# - 生成配音（使用 mimo-tts）
# - 生成字幕
# - 渲染视频
```

### 示例 2：使用克隆音色

```
用户: 用曼波的声音制作一个产品介绍视频
Claude: [激活 video-maker skill]
        [解析脚本]
        [生成图片]
        [使用 --profile 曼波 生成配音]
        [生成字幕]
        [渲染视频]
        输出: 视频已生成，使用曼波音色
```

### 示例 3：自定义风格

```
用户: 制作一个温柔风格的视频，使用冰糖音色
Claude: [激活 video-maker skill]
        [解析脚本]
        [生成图片]
        [使用 --voice 冰糖 --style 温柔 生成配音]
        [生成字幕]
        [渲染视频]
        输出: 视频已生成，使用冰糖音色，温柔风格
```

## 注意事项

- Remotion 需要 Node.js 18+
- 中文字体从 Google Fonts 加载（需要网络）
- 图片在渲染时会被 Remotion 缓存
- 渲染时间取决于时长和复杂度（通常为实时的 2-5 倍）
- mimo-tts 生成的音频为 WAV 格式，Remotion 支持直接使用

## 相关资源

- Remotion 官方文档: https://www.remotion.dev/
- gen-img skill: `~/.claude/skills/gen-img/`
- mimo-tts skill: `~/.claude/skills/mimo-tts/`
- Claude Code 官方文档: https://docs.anthropic.com/en/docs/claude-code
