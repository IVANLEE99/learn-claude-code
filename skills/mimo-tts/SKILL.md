---
name: mimo-tts
description: MiMo 语音合成（TTS）。当用户说"语音合成"、"文字转语音"、"TTS"、"朗读"、"读出来"、"合成语音"、"tts"、"克隆音色"、"声音克隆"时触发。
version: 2.5.0
---

# mimo-tts — MiMo V2.5 语音合成 Skill

将文本转换为自然流畅的语音，支持预置音色、风格控制、声音克隆和音色设计。

## Trigger Conditions

Activate when user requests:
- 语音合成 / 文字转语音 / TTS
- "朗读" / "读出来" / "合成语音" / "tts"
- "克隆音色" / "声音克隆" / "用XX的声音读"
- 任何需要将文本转为语音的请求

## Environment Variables

在 `~/.claude/settings.json` 的 `env` 中配置：

| Variable | Description | Default |
|----------|-------------|---------|
| `MIMO_TTS_API_URL` | MiMo API Base URL | `https://token-plan-cn.xiaomimimo.com` |
| `MIMO_TTS_API_KEY` | MiMo API Key | (required) |

## Models

| 模型 | Model ID | 用途 |
|------|----------|------|
| 预置音色 | `mimo-v2.5-tts` | 使用精品音色合成（默认） |
| 音色设计 | `mimo-v2.5-tts-voicedesign` | 通过文本描述定制音色 |
| 声音克隆 | `mimo-v2.5-tts-voiceclone` | 基于音频样本复刻音色 |

## Preset Voices

| 音色 | Voice ID | 语言 | 性别 |
|------|----------|------|------|
| MiMo-默认 | `mimo_default` | — | — |
| 冰糖 | `冰糖` | 中文 | 女性 |
| 茉莉 | `茉莉` | 中文 | 女性 |
| 苏打 | `苏打` | 中文 | 男性 |
| 白桦 | `白桦` | 中文 | 男性 |
| Mia | `Mia` | 英文 | 女性 |
| Chloe | `Chloe` | 英文 | 女性 |
| Milo | `Milo` | 英文 | 男性 |
| Dean | `Dean` | 英文 | 男性 |

## Execution Steps

### Step 1: Parse User Request

Extract from the user's message:
- **text** (required): 待合成的文本内容
- **voice** (optional): 音色，见预置音色列表，默认 `mimo_default`
- **style** (optional): 风格标签，见下方风格列表
- **singing** (optional): 唱歌模式，默认 `false`
- **clone_audio** (optional): 克隆音色的音频文件路径（mp3/wav）
- **voice_desc** (optional): 音色设计描述文本
- **profile** (optional): 使用已保存的音色档案名称
- **output** (optional): 输出文件路径

### Step 2: Determine Model

- 如果提供了 `clone_audio` → 使用 `mimo-v2.5-tts-voiceclone`
- 如果提供了 `voice_desc` → 使用 `mimo-v2.5-tts-voicedesign`
- 否则 → 使用 `mimo-v2.5-tts`

### Step 3: Generate Speech

```bash
# 预置音色
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --voice "冰糖"

# 带风格
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --voice "冰糖" --style "开心 温柔"

# 唱歌模式
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "两只老虎跑得快" --singing

# 声音克隆
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --clone /path/to/voice.mp3

# 音色设计
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --voice-desc "年轻女性，温柔甜美，语速稍慢"

# 使用已保存的音色档案
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --profile 曼波

# 保存新的音色档案
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --clone /path/to/voice.mp3 --save-profile 我的声音

# 列出所有音色档案
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --list-profiles
```

### Step 4: Save and Play Audio

脚本自动保存 WAV 文件到 `~/Documents/learn-claude-code/generated-audio/`。

## Style Control

### Style Tags（放在 assistant 文本开头）

格式：`(风格1 风格2)待合成文本` — 支持 `()`、`（）`、`[]`

| 类别 | 示例 |
|------|------|
| 基础情绪 | 开心/悲伤/愤怒/恐惧/惊讶/兴奋/委屈/平静/冷漠 |
| 复合情绪 | 怅然/欣慰/无奈/愧疚/释然/嫉妒/厌倦/忐忑/动情 |
| 整体语调 | 温柔/高冷/活泼/严肃/慵懒/俏皮/深沉/干练/凌厉 |
| 音色定位 | 磁性/醇厚/清亮/空灵/稚嫩/苍老/甜美/沙哑/醇雅 |
| 人设腔调 | 夹子音/御姐音/正太音/大叔音/台湾腔 |
| 方言 | 东北话/四川话/河南话/粤语 |
| 角色扮演 | 孙悟空/林黛玉 |
| 唱歌 | 唱歌（必须在最开头，歌词建议用中文） |

### Fine-grained Tags（放在文本任意位置）

格式：`[标签]`，例如 `你好[笑]世界`

| 类别 | 示例 |
|------|------|
| 语速与节奏 | 吸气/深呼吸/叹气/长叹一口气/喘息/屏息 |
| 情绪状态 | 紧张/害怕/激动/疲惫/委屈/撒娇/心虚/震惊/不耐烦 |
| 语音特征 | 颤抖/变调/破音/鼻音/气声/沙哑 |
| 哭笑表达 | 笑/轻笑/大笑/冷笑/抽泣/呜咽/哽咽/嚎啕大哭 |

## API Reference

**Endpoint:** `{API_URL}/v1/chat/completions`

### Preset Voice Request

```json
{
  "model": "mimo-v2.5-tts",
  "messages": [
    {"role": "user", "content": "用温柔的语气"},
    {"role": "assistant", "content": "(温柔)你好，世界！"}
  ],
  "audio": {
    "format": "wav",
    "voice": "冰糖"
  }
}
```

### VoiceClone Request

```json
{
  "model": "mimo-v2.5-tts-voiceclone",
  "messages": [
    {"role": "user", "content": ""},
    {"role": "assistant", "content": "你好，世界！"}
  ],
  "audio": {
    "format": "wav",
    "voice": "data:audio/mpeg;base64,<BASE64_AUDIO>"
  }
}
```

音频样本要求：
- 支持 mp3 和 wav 格式
- Base64 编码后不超过 10 MB
- 必须携带前缀：`data:{MIME_TYPE};base64,$BASE64_AUDIO`

### VoiceDesign Request

```json
{
  "model": "mimo-v2.5-tts-voicedesign",
  "messages": [
    {"role": "user", "content": "年轻女性，温柔甜美，语速稍慢"},
    {"role": "assistant", "content": "你好，世界！"}
  ],
  "audio": {
    "format": "wav"
  }
}
```

## Error Handling

- **401**: 检查 API Key
- **429**: 等待后重试
- **400**: 检查请求参数
- **网络错误**: 检查 API_URL 连通性

## Notes

- 输出音频为 24kHz PCM16LE 单声道 WAV
- 音频默认保存到 `~/Documents/learn-claude-code/generated-audio/`
- 唱歌模式标签必须在最开头
- 声音克隆和风格控制可以同时使用
- 音色档案保存在 `~/.claude/skills/mimo-tts/voices/` 目录
- 使用 `--profile` 可以快速调用已保存的音色，无需每次提供音频文件
- 当前限时免费
