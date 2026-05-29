---
name: mimo-asr
description: MiMo 语音识别（ASR）。当用户说"语音识别"、"语音转文字"、"ASR"、"听写"、"转录"、"识别音频"、"音频转文字"、"transcribe"、"听一下"时触发。
version: 1.0.0
---

# mimo-asr — MiMo V2.5 语音识别 Skill

将语音/音频转换为文字，支持中英文双语、方言、Code-Switch、歌曲歌词、强噪声、多人对话等复杂场景。

## Trigger Conditions

Activate when user requests:
- 语音识别 / 语音转文字 / ASR
- "听写" / "转录" / "识别音频" / "音频转文字"
- "transcribe" / "听一下" / "帮我识别"
- 任何需要将语音/音频转为文字的请求

## Environment Variables

在 `~/.claude/settings.json` 的 `env` 中配置：

**自动模式（推荐）：** 如果已配置 `ANTHROPIC_BASE_URL` 且包含 `xiaomimimo.com`，会自动复用 `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN`，无需额外配置。

**专用配置：**

| Variable | Description | Default |
|----------|-------------|---------|
| `MIMO_API_URL` | MiMo API Base URL | `https://api.xiaomimimo.com` |
| `MIMO_API_KEY` | MiMo API Key | (required) |

优先级：`ANTHROPIC_BASE_URL`（含 xiaomimimo.com）> `MIMO_API_URL`

## Models

| 模型 | Model ID | 用途 |
|------|----------|------|
| 语音识别（API） | `mimo-v2.5` | 通过音频理解 API 进行语音转文字 |
| 语音识别（本地） | `MiMo-V2.5-ASR` | 本地部署的专用 ASR 模型（需 GPU） |

## Core Features

- **中文方言**: 支持吴语、粤语、闽南语、四川话等
- **中英混说 (Code-Switch)**: 无需预设语言标签，自由切换中英文
- **歌曲识别**: 识别中英文歌曲歌词，伴奏与人声混合场景下保持高准确率
- **强噪声场景**: 高噪声、远场拾音等复杂声学环境下保持鲁棒识别
- **多人对话**: 支持多人交叉对话场景的准确转录（如会议场景）
- **强知识关联**: 精准识别古诗词、技术术语、人名、地名等知识密集型内容
- **原生标点**: 结合语音韵律和语义原生输出标点，转录结果可直接使用

## Execution Steps

### Step 1: Parse User Request

Extract from the user's message:
- **audio** (required): 音频文件路径或 URL
- **language** (optional): 语言偏好，`zh`（中文）/ `en`（英文）/ `auto`（自动检测，默认）
- **output** (optional): 输出文件路径（默认输出到终端 + 保存文本文件）
- **mode** (optional): `api`（云端 API，默认）/ `local`（本地模型）

### Step 2: Determine Input Type

根据音频来源选择输入方式：
- **本地文件**: 自动 Base64 编码
- **URL**: 直接传入 URL

### Step 3: Transcribe Audio

```bash
# 本地文件识别（默认 API 模式）
bash ~/.claude/skills/mimo-asr/scripts/mimo-asr.sh --audio /path/to/audio.wav

# 指定语言
bash ~/.claude/skills/mimo-asr/scripts/mimo-asr.sh --audio /path/to/audio.wav --language zh

# URL 音频识别
bash ~/.claude/skills/mimo-asr/scripts/mimo-asr.sh --audio "https://example.com/audio.wav"

# 保存转录结果到文件
bash ~/.claude/skills/mimo-asr/scripts/mimo-asr.sh --audio /path/to/audio.wav --output /path/to/output.txt

# 指定输出目录（自动生成文件名）
bash ~/.claude/skills/mimo-asr/scripts/mimo-asr.sh --audio /path/to/audio.wav --output-dir /path/to/dir

# 本地模型模式（需 GPU + Python 环境）
bash ~/.claude/skills/mimo-asr/scripts/mimo-asr.sh --audio /path/to/audio.wav --mode local

# 指定本地模型路径
bash ~/.claude/skills/mimo-asr/scripts/mimo-asr.sh --audio /path/to/audio.wav --mode local --model-dir /path/to/models
```

### Step 4: Output Results

脚本自动：
- 在终端显示转录文本
- 保存转录结果到文件（可选）

## Audio Restrictions

- **支持格式**: MP3, WAV, FLAC, M4A, OGG
- **文件大小**:
  - URL 模式：单个音频不超过 100 MB
  - Base64 模式：编码后不超过 50 MB
- **多音频**: 受模型上下文长度限制，所有音频和文本的总 token 数须小于模型上下文长度

## API Reference

**Endpoint:** `{API_URL}/v1/chat/completions`

### Request

```json
{
  "model": "mimo-v2.5",
  "messages": [
    {
      "role": "system",
      "content": "You are MiMo, an AI assistant developed by Xiaomi."
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

### Base64 Input

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

### Response

```json
{
  "choices": [{
    "message": {
      "content": "",
      "reasoning_content": "转录的文本内容"
    }
  }]
}
```

转录文本位于 `reasoning_content` 字段。

## Local Model (Open Source)

MiMo-V2.5-ASR 已开源，可本地部署：

```bash
# 安装
git clone https://github.com/XiaomiMiMo/MiMo-V2.5-ASR.git
cd MiMo-V2.5-ASR
pip install -r requirements.txt
pip install flash-attn==2.7.4.post1

# 下载模型
hf download XiaomiMiMo/MiMo-Audio-Tokenizer --local-dir ./models/MiMo-Audio-Tokenizer
hf download XiaomiMiMo/MiMo-V2.5-ASR --local-dir ./models/MiMo-V2.5-ASR

# Python API
python -c "
from src.mimo_audio.mimo_audio import MimoAudio
model = MimoAudio(model_path='./models/MiMo-V2.5-ASR', tokenizer_path='./models/MiMo-Audio-Tokenizer')
text = model.asr_sft('path/to/audio.wav')
print(text)
"
```

本地模型要求：
- Python 3.12
- CUDA >= 12.0
- GPU 显存建议 >= 8GB

## Error Handling

- **401**: 检查 API Key
- **429**: 等待后重试
- **400**: 检查音频格式和大小
- **网络错误**: 检查 API_URL 连通性
- **本地模型**: 检查 CUDA 环境和模型路径

## Notes

- 转录文本默认输出到终端并保存到文件
- 支持中英文自动语言检测，Code-Switch 场景推荐使用 `auto`
- 音频 token 消耗估算：`总 token ≈ 音频时长(秒) × 6.25`
- 云端 API 当前限时免费
- 本地模型完全免费，但需要 GPU 资源
- 更多信息：[GitHub](https://github.com/XiaomiMiMo/MiMo-V2.5-ASR) | [HuggingFace](https://huggingface.co/XiaomiMiMo/MiMo-V2.5-ASR) | [Demo](https://mimo.xiaomi.com/mimo-v2-5-asr)
