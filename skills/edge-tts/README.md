# edge-tts — Microsoft Edge / Azure Neural TTS Skill

> **版本**: 1.0.0 · **依赖**: `edge-tts` ≥ 7.2.8 · **默认音色**: `zh-CN-YunyangNeural` (男声, 专业可靠, 新闻风)

## 项目结构

```
skills/edge-tts/
├── SKILL.md                     # Claude Code skill 配置（触发词、执行步骤、音色表）
├── README.md                    # 本文档
├── scripts/
│   └── edge-tts-synth.py        # Python 包装脚本
└── edge-tts-audition/           # 试听音频样本
    ├── zh-CN-YunyangNeural.mp3   # ★ 默认男声，专业可靠
    ├── zh-CN-YunjianNeural.mp3   # 男声，激情
    ├── zh-CN-YunxiNeural.mp3     # 男声，活泼阳光
    ├── zh-CN-YunxiaNeural.mp3    # 男声，可爱
    ├── zh-CN-XiaoyiNeural.mp3    # 女声，活泼（卡通风）
    ├── zh-CN-liaoning-XiaobeiNeural.mp3  # 女声，东北方言
    ├── zh-CN-shaanxi-XiaoniNeural.mp3    # 女声，陕西方言
    ├── zh-HK-WanLungNeural.mp3   # 粤语男声
    ├── zh-HK-HiuGaaiNeural.mp3   # 粤语女声
    ├── zh-HK-HiuMaanNeural.mp3   # 粤语女声
    ├── zh-TW-YunJheNeural.mp3    # 台湾国语男声
    ├── zh-TW-HsiaoChenNeural.mp3 # 台湾国语女声
    └── zh-TW-HsiaoYuNeural.mp3   # 台湾国语女声
```

## 快速开始

### 安装

```bash
pip install edge-tts>=7.2.8
```

### 列出所有音色

```bash
python3 scripts/edge-tts-synth.py --list-voices
```

按语言筛选：

```bash
python3 scripts/edge-tts-synth.py --list-voices --locale zh-CN
python3 scripts/edge-tts-synth.py --list-voices --locale en-US
```

### 生成语音

```bash
python3 scripts/edge-tts-synth.py --text "你好世界" --output output.mp3
```

### 从文件读取文本

```bash
python3 scripts/edge-tts-synth.py --file article.txt --output output.mp3
```

### 指定音色

```bash
python3 scripts/edge-tts-synth.py --text "Hello" --voice en-US-AriaNeural --output output.mp3
```

### 调整语速 / 音调 / 音量

```bash
python3 scripts/edge-tts-synth.py --text "快速朗读" --rate +20% --output output.mp3
python3 scripts/edge-tts-synth.py --text "低沉朗读" --pitch -5Hz --output output.mp3
```

### 生成字幕

```bash
python3 scripts/edge-tts-synth.py --text "你好世界" --output output.mp3 --write-subtitles output.srt
```

### 直接用 edge-tts CLI

```bash
edge-tts --voice zh-CN-YunyangNeural --text "你好" --write-media output.mp3
```

> ⚠️ 负值必须用 `=` 语法：`--rate=-50%`，不能写 `--rate -50%`（会被解析为命令选项）。

## 可选音色

### 中文普通话 (zh-CN)

| 音色 | 性别 | 风格 | 备注 |
|------|------|------|------|
| `zh-CN-YunyangNeural` ★ | 男 | 专业可靠, 新闻 | **默认音色** |
| `zh-CN-YunxiNeural` | 男 | 活泼阳光, 小说 | |
| `zh-CN-YunjianNeural` | 男 | 激情, 体育/小说 | |
| `zh-CN-YunxiaNeural` | 男 | 可爱, 卡通 | |
| `zh-CN-XiaoyiNeural` | 女 | 活泼, 卡通/小说 | |
| `zh-CN-liaoning-XiaobeiNeural` | 女 | 幽默, 东北方言 | 方言特色 |
| `zh-CN-shaanxi-XiaoniNeural` | 女 | 明亮, 陕西方言 | 方言特色 |

### 中文粤语 (zh-HK)

| 音色 | 性别 | 风格 |
|------|------|------|
| `zh-HK-WanLungNeural` | 男 | 通用 |
| `zh-HK-HiuGaaiNeural` | 女 | 通用 |
| `zh-HK-HiuMaanNeural` | 女 | 通用 |

### 中文台湾国语 (zh-TW)

| 音色 | 性别 | 风格 |
|------|------|------|
| `zh-TW-YunJheNeural` | 男 | 通用 |
| `zh-TW-HsiaoChenNeural` | 女 | 通用 |
| `zh-TW-HsiaoYuNeural` | 女 | 通用 |

### 英语 (en-US / en-GB)

| 音色 | 性别 | 风格 |
|------|------|------|
| `en-US-AriaNeural` | 女 | 新闻/小说 |
| `en-US-GuyNeural` | 男 | 新闻/小说 |
| `en-US-JennyNeural` | 女 | 友好, 通用 |
| `en-GB-SoniaNeural` | 女 | 英式通用 |
| `en-GB-RyanNeural` | 男 | 英式通用 |

> 完整 200+ 音色列表（100+ 语言）请运行：`edge-tts --list-voices`

## 试听音频

`edge-tts-audition/` 目录下包含 13 个音色的试听样本，使用同一段测试文本生成：

> "大家好，我是 [音色名]，来给大家打个招呼。今天天气真不错，适合出去走走。"

可以直接播放 `.mp3` 文件试听，文件名即音色名。

## 参数说明

| 参数 | 格式 | 默认值 | 示例 |
|------|------|--------|------|
| `--voice` | Azure Neural 音色名 | `zh-CN-YunyangNeural` | `zh-CN-XiaoxiaoNeural` |
| `--rate` | 百分比 | `+0%` | `+10%`（快）, `-20%`（慢） |
| `--pitch` | Hz 偏移 | `+0Hz` | `+5Hz`（高）, `-10Hz`（低） |
| `--volume` | 百分比 | `+0%` | `-50%`（小声）, `+10%`（大声） |

## Python API 用法

```python
import asyncio
import edge_tts

async def main():
    # 基础用法
    comm = edge_tts.Communicate(
        text="你好世界",
        voice="zh-CN-YunyangNeural",
        rate="+0%",
        pitch="+0Hz",
        volume="+0%",
    )
    await comm.save("output.mp3")

    # 流式获取音频和字幕
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            # chunk["data"] — MP3 字节流
            pass
        elif chunk["type"] == "SentenceBoundary":
            # chunk["text"] / chunk["offset"] / chunk["duration"]
            pass

asyncio.run(main())
```

## 常见问题

### Q: 生成时 403 Forbidden

**A:** 旧版本 `edge-tts`（7.0.x）的 WebSocket 认证 token 已过期。升级到 7.2.8+：

```bash
pip install --upgrade edge-tts
```

### Q: 支持 SSML 吗

**A:** 不完全支持。Microsoft 只允许 Edge 本身能生成的 SSML，即 `<voice>` 内嵌 `<prosody>` 的简单结构。更复杂的 SSML 被拒绝。

### Q: 输出格式是什么

**A:** MP3（48kHz / 320kbps 单声道）。

### Q: 长文本怎么办

**A:** edge-tts 支持任意长度文本，但建议拆分成段落以控制质量。可用 `--file` 读取长文件。

### Q: 在中国大陆如何使用

**A:** 需要能访问 `speech.platform.bing.com`（ping 延迟 ~160ms，正常）。如遇连接问题可配置 HTTP 代理。

## License

本 skill 封装代码为 MIT。底层 `edge-tts` 库为 GPL-3.0。
