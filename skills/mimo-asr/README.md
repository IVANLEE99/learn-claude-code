# MiMo ASR — MiMo V2.5 语音识别 Skill

基于小米 MiMo-V2.5 语音识别模型的 Claude Code Skill，将语音/音频转换为文字。

> 参考：[MiMo-V2.5-TTS + ASR 发布公告](https://platform.xiaomimimo.com/docs/zh-CN/news/v2.5-tts-release)
> 开源地址：[GitHub](https://github.com/XiaomiMiMo/MiMo-V2.5-ASR) | [HuggingFace](https://huggingface.co/XiaomiMiMo/MiMo-V2.5-ASR) | [Demo](https://mimo.xiaomi.com/mimo-v2-5-asr)

## 触发条件

当用户提到以下关键词时自动激活：

- 语音识别 / 语音转文字 / ASR
- 听写 / 转录 / 识别音频 / 音频转文字
- transcribe / 听一下 / 帮我识别

## 文件结构

```
skills/mimo-asr/
├── SKILL.md              # Skill 文档（触发条件、用法、API 参考）
├── README.md             # 详细说明文档
└── scripts/
    └── mimo-asr.sh       # 核心执行脚本
```

## 环境配置

在 `~/.claude/settings.json` 的 `env` 中配置。

**自动模式（推荐）：** 如果已配置 `ANTHROPIC_BASE_URL` 且包含 `xiaomimimo.com`，会自动复用 `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN`，无需额外配置。

**专用配置：**

| Variable | Description | Default |
|----------|-------------|---------|
| `MIMO_API_URL` | MiMo API Base URL | `https://api.xiaomimimo.com` |
| `MIMO_API_KEY` | MiMo API Key | (required) |

优先级：`ANTHROPIC_BASE_URL`（含 xiaomimimo.com）> `MIMO_API_URL`

## 两种工作模式

### 1. API 模式（默认，推荐）

通过小米云端 API 调用 `mimo-v2.5` 模型的音频理解接口。

#### 请求流程

```
音频文件
  ↓
Base64 编码（本地文件）或 URL（远程文件）
  ↓
构建 chat completions 请求（input_audio 格式）
  ↓
POST /v1/chat/completions
  ↓
解析 reasoning_content 字段获取转录文本
```

#### 请求示例

```json
{
  "model": "mimo-v2.5",
  "messages": [
    {
      "role": "system",
      "content": "You are MiMo, an AI assistant developed by Xiaomi. You are an expert at transcribing audio content accurately."
    },
    {
      "role": "user",
      "content": [
        {
          "type": "input_audio",
          "input_audio": {
            "data": "https://example.com/audio.wav"
          }
        },
        {
          "type": "text",
          "text": "请将音频内容转录为文字"
        }
      ]
    }
  ],
  "max_completion_tokens": 4096
}
```

#### Base64 输入

```json
{
  "type": "input_audio",
  "input_audio": {
    "data": "data:{MIME_TYPE};base64,$BASE64_AUDIO"
  }
}
```

音频样本要求：
- 支持 mp3、wav、flac、m4a、ogg 格式
- Base64 编码后不超过 50 MB
- 必须携带前缀：`data:{MIME_TYPE};base64,$BASE64_AUDIO`

#### 响应格式

```json
{
  "choices": [{
    "message": {
      "content": "",
      "reasoning_content": "转录的文本内容在这里"
    }
  }]
}
```

> **注意：** 转录文本位于 `reasoning_content` 而非 `content`，因为 MiMo 的推理模型将 ASR 视为一种"推理"过程。

### 2. Local 模式（本地 GPU）

使用开源的 [MiMo-V2.5-ASR](https://github.com/XiaomiMiMo/MiMo-V2.5-ASR) 模型在本地运行，无需联网。

#### 前置要求

| 依赖 | 版本要求 |
|------|----------|
| Python | 3.12 |
| CUDA | >= 12.0 |
| GPU 显存 | 建议 >= 8GB |

#### 模型下载

```bash
# 安装依赖
pip install huggingface-hub

# 下载 ASR 模型
hf download XiaomiMiMo/MiMo-V2.5-ASR --local-dir ./models/MiMo-V2.5-ASR

# 下载 Audio Tokenizer
hf download XiaomiMiMo/MiMo-Audio-Tokenizer --local-dir ./models/MiMo-Audio-Tokenizer
```

#### Python API 调用

```python
from src.mimo_audio.mimo_audio import MimoAudio

model = MimoAudio(
    model_path="./models/MiMo-V2.5-ASR",
    tokenizer_path="./models/MiMo-Audio-Tokenizer",
)

# 自动语言检测（推荐）
text = model.asr_sft("path/to/audio.wav")
print(text)

# 指定语言
text_zh = model.asr_sft("path/to/audio.wav", audio_tag="<chinese>")
text_en = model.asr_sft("path/to/audio.wav", audio_tag="<english>")
```

## 脚本使用

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--audio` | 音频文件路径或 URL（必填） | — |
| `--language` | 语言: `zh` / `en` / `auto` | `auto` |
| `--output` | 输出文件路径 | — |
| `--output-dir` | 输出目录（自动生成文件名） | — |
| `--mode` | `api` 或 `local` | `api` |
| `--model-dir` | 本地模型目录 | 自动搜索 |
| `--max-tokens` | 最大输出 token 数 | `4096` |

### 使用示例

```bash
# 基本用法
bash skills/mimo-asr/scripts/mimo-asr.sh --audio recording.wav

# 指定中文 + 保存结果
bash skills/mimo-asr/scripts/mimo-asr.sh --audio recording.wav --language zh --output result.txt

# 指定输出目录
bash skills/mimo-asr/scripts/mimo-asr.sh --audio recording.wav --output-dir ./transcripts

# URL 音频
bash skills/mimo-asr/scripts/mimo-asr.sh --audio "https://example.com/audio.wav"

# 本地模型模式
bash skills/mimo-asr/scripts/mimo-asr.sh --audio recording.wav --mode local

# 指定本地模型路径
bash skills/mimo-asr/scripts/mimo-asr.sh --audio recording.wav --mode local --model-dir /path/to/models
```

### 输出格式

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
转录的文本内容会显示在这里
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Token 使用: 156

已保存到: /path/to/output.txt

识别完成！
```

## MiMo-V2.5-ASR 核心能力

| 能力 | 说明 |
|------|------|
| 中文方言 | 吴语、粤语、闽南语、四川话等 |
| 中英混说 | Code-Switch，无需预设语言标签 |
| 歌曲识别 | 伴奏与人声混合下的歌词转录 |
| 强噪声 | 高噪声、远场拾音等复杂环境 |
| 多人对话 | 会议等多人交叉对话场景 |
| 强知识关联 | 古诗词、技术术语、人名地名 |
| 原生标点 | 结合韵律和语义，输出可直接使用的文本 |

## 音频格式限制

| 限制项 | 说明 |
|--------|------|
| 支持格式 | MP3, WAV, FLAC, M4A, OGG |
| URL 模式大小 | 单个音频不超过 100 MB |
| Base64 模式大小 | 编码后不超过 50 MB |
| Token 消耗 | `≈ 音频时长(秒) × 6.25` |

## 与 mimo-tts 的对应关系

| 对比项 | mimo-tts | mimo-asr |
|--------|----------|----------|
| 方向 | 文字 → 语音 | 语音 → 文字 |
| API Endpoint | `/v1/chat/completions` | `/v1/chat/completions` |
| 模型 | `mimo-v2.5-tts` 系列 | `mimo-v2.5` |
| 输入 | 文本 | 音频（URL / Base64） |
| 输出 | WAV 音频文件 | 纯文本 |
| 音频格式 | 输出 24kHz PCM16LE WAV | 输入支持 MP3/WAV/FLAC/M4A/OGG |
| API 配置 | 复用 `ANTHROPIC_BASE_URL` | 同左 |
| 本地部署 | 不支持 | 支持（开源模型 + GPU） |
| 费用 | 限时免费 | API 限时免费 / 本地免费 |

## 错误处理

| 错误码 | 原因 | 解决方案 |
|--------|------|----------|
| 401 | API Key 无效 | 检查 `MIMO_API_KEY` 配置 |
| 429 | 请求频率超限 | 等待后重试 |
| 400 | 请求参数错误 | 检查音频格式和大小 |
| 网络错误 | API 不可达 | 检查 `MIMO_API_URL` 连通性 |
| 本地模型错误 | 模型未找到 | 检查 CUDA 环境和模型路径 |

## 参考链接

- [MiMo-V2.5-ASR GitHub](https://github.com/XiaomiMiMo/MiMo-V2.5-ASR)
- [MiMo-V2.5-ASR HuggingFace](https://huggingface.co/XiaomiMiMo/MiMo-V2.5-ASR)
- [MiMo-V2.5-ASR Demo](https://mimo.xiaomi.com/mimo-v2-5-asr)
- [MiMo API 开放平台](https://platform.xiaomimimo.com)
- [MiMo-Skills 仓库](https://github.com/XiaomiMiMo/MiMo-Skills)
