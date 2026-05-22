# Fish Audio S2 语音合成 Skill

基于 [Fish Audio S2](https://fish.audio/) 的文本转语音（TTS）合成工具，支持 80+ 语言和声音克隆。

## 功能特性

- **多语言支持**：80+ 语言，无需额外配置
- **声音克隆**：10-30 秒参考音频即可克隆声音
- **情感控制**：通过标签控制语调和情感
- **CPU 推理**：无需 GPU 即可运行（速度较慢）
- **本地部署**：完全离线运行，无需 API 调用

## 快速开始

### 1. 环境准备

```bash
cd fish-speech
source venv/bin/activate
```

### 2. 生成配音

```bash
# 使用脚本
./scripts/tts.sh "大家好，欢迎使用 Fish Speech" output.wav

# 或手动执行
python fish_speech/models/text2semantic/inference.py \
    --text "大家好" \
    --max-new-tokens 256 \
    --device cpu \
    --checkpoint-path "checkpoints/s2-pro" \
    --output-dir "output"

python fish_speech/models/dac/inference.py \
    -i "output/codes_0.npy" \
    --checkpoint-path "checkpoints/s2-pro/codec.pth" \
    --device cpu \
    -o "output.wav"
```

## 目录结构

```
skills/fish-speech/
├── SKILL.md           # Skill 核心定义（Claude Code 使用）
├── README.md          # 本文档
└── scripts/
    └── tts.sh         # 一键推理脚本
```

## 模型信息

| 模型 | 参数量 | 说明 |
|------|--------|------|
| S2-Pro | 4B | 旗舰模型，最高质量 |

### 模型文件

```
fish-speech/checkpoints/s2-pro/
├── codec.pth                           # 音频编码器 (1.7GB)
├── model-00001-of-00002.safetensors    # 文本模型 Part 1 (4.6GB)
├── model-00002-of-00002.safetensors    # 文本模型 Part 2 (3.9GB)
├── tokenizer.json                      # 分词器
└── config.json                         # 模型配置
```

## 使用示例

### 基础文本转语音

```bash
./scripts/tts.sh "今天天气真不错" weather.wav
```

### 使用参考音频（声音克隆）

```bash
./scripts/tts.sh "用这个声音说话" cloned.wav reference.wav "这是参考音频的文本"
```

### 情感控制

```bash
./scripts/tts.sh "[excited] 大家好！[pause] 今天是个好日子。" excited.wav
```

### 多语言

```bash
# 英文
./scripts/tts.sh "Hello, welcome to Fish Speech" hello_en.wav

# 日文
./scripts/tts.sh "こんにちは、Fish Speechへようこそ" hello_ja.wav
```

## 性能说明

### CPU 推理速度

| 指标 | 数值 |
|------|------|
| 推理速度 | ~0.05 tokens/sec |
| 每 token 耗时 | ~17-20 秒 |
| 生成 256 tokens | ~70 分钟 |
| 建议文本长度 | < 50 字 |

### GPU 推理速度（推荐）

| 指标 | 数值（H200） |
|------|-------------|
| RTF | 0.195 |
| TTFA | ~100ms |
| 吞吐量 | 3000+ tokens/s |

## 高级配置

### 参数调整

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--max-new-tokens` | 2048 | 最大生成 token 数 |
| `--temperature` | 1.0 | 采样温度（越高越随机） |
| `--top-p` | 0.9 | Top-p 采样 |
| `--top-k` | 30 | Top-k 采样 |
| `--device` | cpu | 推理设备 |

### 情感标签

Fish Audio S2 支持丰富的情感标签：

| 标签 | 效果 |
|------|------|
| `[excited]` | 兴奋 |
| `[whisper]` | 低语 |
| `[angry]` | 生气 |
| `[sad]` | 悲伤 |
| `[pause]` | 停顿 |
| `[laughing]` | 笑声 |
| `[emphasis]` | 强调 |

## 依赖服务

此 Skill 依赖 `fish-speech/` 目录下的本地模型，无需外部 API。

## 相关链接

- [官方文档](https://speech.fish.audio/zh/install/)
- [GitHub 仓库](https://github.com/fishaudio/fish-speech)
- [HuggingFace 模型](https://huggingface.co/fishaudio/s2-pro)
- [技术报告](https://arxiv.org/abs/2603.08823)
