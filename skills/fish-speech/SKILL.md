---
name: fish-speech
description: Generate TTS voiceover using Fish Audio S2. Trigger when user says "generate voiceover", "text to speech", "tts", "生成配音", "文本转语音", "语音合成", "fish speech", or wants to convert text into speech audio.
version: 1.0.0
---

# fish-speech — Fish Audio S2 语音合成 Skill

使用 Fish Audio S2 模型进行文本转语音（TTS）合成，支持 80+ 语言和声音克隆。

## 触发条件

当用户提到以下关键词时，自动触发此 Skill：
- 生成配音 / 文本转语音 / 语音合成 / TTS
- generate voiceover / text to speech / tts
- fish speech / fish audio
- 声音克隆 / voice cloning

## 前置要求

### 系统依赖

```bash
# macOS
brew install portaudio sox ffmpeg

# Ubuntu/Debian
apt install portaudio19-dev libsox-dev ffmpeg
```

### Python 环境

项目使用 `fish-speech/venv/` 虚拟环境，已预装：
- Python 3.12
- PyTorch 2.8.0 (CPU)
- fish-speech 2.0.0

### 模型文件

模型已下载至 `fish-speech/checkpoints/s2-pro/`：
- `codec.pth` (1.7GB) - 音频编码器
- `model-00001-of-00002.safetensors` (4.6GB) - 文本模型 Part 1
- `model-00002-of-00002.safetensors` (3.9GB) - 文本模型 Part 2

## 执行步骤

### 第 1 步：解析用户请求

从用户输入中提取：
- 要合成的文本内容
- 语言（默认中文）
- 是否需要参考音频（声音克隆）
- 输出文件名

### 第 2 步：运行推理

使用 `scripts/tts.sh` 脚本进行推理：

```bash
cd fish-speech
./scripts/tts.sh "要合成的文本内容" [输出文件名] [参考音频路径]
```

或者手动执行三步推理：

#### 步骤 A：生成 VQ tokens（如有参考音频）

```bash
source venv/bin/activate
python fish_speech/models/dac/inference.py \
    -i "参考音频.wav" \
    --checkpoint-path "checkpoints/s2-pro/codec.pth" \
    --device cpu \
    -o "fake.wav"
```

#### 步骤 B：文本转语义 tokens

```bash
python fish_speech/models/text2semantic/inference.py \
    --text "要合成的文本" \
    --prompt-text "参考文本" \
    --prompt-tokens "fake.npy" \
    --max-new-tokens 256 \
    --device cpu \
    --checkpoint-path "checkpoints/s2-pro" \
    --output-dir "output"
```

#### 步骤 C：语义 tokens 转音频

```bash
python fish_speech/models/dac/inference.py \
    -i "output/codes_0.npy" \
    --checkpoint-path "checkpoints/s2-pro/codec.pth" \
    --device cpu \
    -o "output_audio.wav"
```

### 第 4 步：输出结果

- 生成的音频文件路径
- 音频时长
- 文件大小

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--text` | - | 要合成的文本（必填） |
| `--max-new-tokens` | 2048 | 最大生成 token 数 |
| `--device` | cpu | 推理设备（cpu/cuda） |
| `--checkpoint-path` | checkpoints/s2-pro | 模型路径 |
| `--output-dir` | output | 输出目录 |
| `--temperature` | 1.0 | 采样温度 |
| `--top-p` | 0.9 | Top-p 采样 |
| `--top-k` | 30 | Top-k 采样 |

## 高级功能

### 声音克隆

提供 10-30 秒的参考音频，模型可以克隆该声音：

```bash
python fish_speech/models/dac/inference.py \
    -i "参考音频.wav" \
    --checkpoint-path "checkpoints/s2-pro/codec.pth" \
    --device cpu \
    -o "voice_ref.wav"
```

然后在文本转语音时使用生成的 tokens。

### 情感控制

Fish Audio S2 支持通过标签控制情感：

```
[excited] 大家好！[pause] 今天天气真不错。
[whisper] 这是一个秘密。
[angry] 我很生气！
```

### 多语言

支持 80+ 语言，无需额外配置：
- Tier 1: 中文(zh), 英文(en), 日文(ja)
- Tier 2: 韩文(ko), 西班牙文(es), 法文(fr) 等

## CPU 推理注意事项

- CPU 推理速度约 0.05 tokens/sec（非常慢）
- 建议使用 `--max-new-tokens 256` 限制生成长度
- 每个 token 约需 17-20 秒
- 建议使用 GPU（至少 24GB 显存）进行生产使用

## 输出文件

| 文件 | 说明 |
|------|------|
| `fake.npy` | VQ tokens（参考音频编码） |
| `fake.wav` | 参考音频重建 |
| `output/codes_0.npy` | 生成的语义 tokens |
| `output_audio.wav` | 最终合成音频 |

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `PytorchStreamReader failed` | 模型文件损坏 | 重新下载模型文件 |
| `No format specified` | 输出文件缺少扩展名 | 确保输出文件以 `.wav` 结尾 |
| `CUDA out of memory` | GPU 显存不足 | 使用 `--device cpu` 或减少 `--max-new-tokens` |

### 模型下载

如需重新下载模型：

```bash
cd fish-speech
curl -L -o checkpoints/s2-pro/codec.pth \
    "https://huggingface.co/fishaudio/s2-pro/resolve/main/codec.pth"

curl -L -o checkpoints/s2-pro/model-00002-of-00002.safetensors \
    "https://huggingface.co/fishaudio/s2-pro/resolve/main/model-00002-of-00002.safetensors"
```

## 相关资源

| 资源 | 链接 |
|------|------|
| 官方文档 | https://speech.fish.audio/zh/install/ |
| GitHub 仓库 | https://github.com/fishaudio/fish-speech |
| HuggingFace 模型 | https://huggingface.co/fishaudio/s2-pro |
| 技术报告 | https://arxiv.org/abs/2603.08823 |
