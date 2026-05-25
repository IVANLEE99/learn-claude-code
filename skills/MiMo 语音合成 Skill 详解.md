# MiMo 语音合成 Skill 详解

> 基于小米 MiMo V2.5 TTS 模型的 Claude Code 语音合成技能，支持预置音色、风格控制、声音克隆、音色设计和音色档案管理。

---

## 目录

- [1. 概述](#1-概述)
- [2. 文件结构](#2-文件结构)
- [3. 环境配置](#3-环境配置)
- [4. 功能特性](#4-功能特性)
- [5. 脚本参数详解](#5-脚本参数详解)
- [6. 使用示例](#6-使用示例)
- [7. 预置音色列表](#7-预置音色列表)
- [8. 风格控制](#8-风格控制)
- [9. 音色档案管理](#9-音色档案管理)
- [10. API 参考](#10-api-参考)
- [11. 错误处理](#11-错误处理)
- [12. 常见问题](#12-常见问题)

---

## 1. 概述

`mimo-tts` 是一个 Claude Code Skill，将文本转换为自然流畅的语音。基于小米 MiMo V2.5 TTS 系列模型，提供三种合成模式：

| 模式 | 模型 ID | 说明 |
|------|---------|------|
| **预置音色** | `mimo-v2.5-tts` | 使用 9 个精品音色直接合成 |
| **声音克隆** | `mimo-v2.5-tts-voiceclone` | 基于音频样本复刻任意音色 |
| **音色设计** | `mimo-v2.5-tts-voicedesign` | 通过自然语言描述生成定制音色 |

**输出格式：** 24kHz PCM16LE 单声道 WAV

---

## 2. 文件结构

```
~/.claude/skills/mimo-tts/
├── SKILL.md                    # Skill 元数据和触发条件
├── scripts/
│   └── mimo-tts.sh             # 主执行脚本（358 行）
├── voices/
│   ├── profiles.json           # 音色档案索引
│   └── 曼波.mp3                # 已保存的音色样本
└── examples/
    └── 逍遥游.wav              # 示例音频输出
```

---

## 3. 环境配置

### 自动模式（推荐）

如果已在 `~/.claude/settings.json` 中配置了 `ANTHROPIC_BASE_URL` 且包含 `xiaomimimo.com`，会自动复用 `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN`，无需额外配置。

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://xxx.xiaomimimo.com/v1",
    "ANTHROPIC_AUTH_TOKEN": "your-token"
  }
}
```

### 专用配置

如果 `ANTHROPIC_BASE_URL` 未配置或不包含 `xiaomimimo.com`，则使用以下专用变量：

```json
{
  "env": {
    "MIMO_TTS_API_URL": "https://token-plan-cn.xiaomimimo.com",
    "MIMO_TTS_API_KEY": "your-api-key-here"
  }
}
```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MIMO_TTS_API_URL` | MiMo API 基础 URL | `https://token-plan-cn.xiaomimimo.com` |
| `MIMO_TTS_API_KEY` | API 密钥（必填） | — |

**优先级：** `ANTHROPIC_BASE_URL`（含 xiaomimimo.com）> `MIMO_TTS_API_URL`

> 当前限时免费，可在 [MiMo 控制台](https://platform.xiaomimimo.com/) 查看用量。

---

## 4. 功能特性

### 4.1 预置音色合成

使用 9 个精品音色，支持中英文：

```bash
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好世界" --voice "冰糖"
```

### 4.2 风格控制

两种风格标签：

- **Style Tags**：`(开心 温柔)你好` — 放在文本开头
- **Fine-grained Tags**：`你好[笑]世界` — 放在文本任意位置

```bash
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好世界" --style "开心 温柔"
```

### 4.3 声音克隆

基于 mp3/wav 音频样本复刻音色：

```bash
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好世界" --clone /path/to/voice.mp3
```

**音频要求：**
- 支持 mp3 和 wav 格式
- Base64 编码后不超过 10 MB
- 建议 10-30 秒清晰语音

### 4.4 音色设计

通过自然语言描述生成定制音色：

```bash
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好世界" --voice-desc "年轻女性，温柔甜美，语速稍慢"
```

**描述维度：**
- 性别与年龄
- 音色/质感（磁性、清亮、沙哑等）
- 情绪/语气（温柔、活泼、严肃等）
- 语速/节奏
- 角色/人设、说话风格、场景描写

### 4.5 音色档案管理

保存常用音色，下次直接调用：

```bash
# 保存音色档案
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --clone voice.mp3 --save-profile 我的声音

# 使用已保存的音色
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --profile 我的声音

# 列出所有档案
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --list-profiles
```

### 4.6 唱歌模式

```bash
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "两只老虎两只老虎跑得快" --singing
```

> 唱歌模式标签必须在最开头，歌词建议用中文。

---

## 5. 脚本参数详解

```
用法: mimo-tts.sh --text "文本" [选项]
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--text TEXT` | string | 是 | — | 待合成的文本内容 |
| `--voice VOICE` | string | 否 | `mimo_default` | 预置音色 ID |
| `--style STYLE` | string | 否 | — | 风格标签，空格分隔多个 |
| `--singing` | flag | 否 | false | 启用唱歌模式 |
| `--clone FILE` | string | 否 | — | 克隆音色的音频文件路径 |
| `--voice-desc DESC` | string | 否 | — | 音色设计描述文本 |
| `--profile NAME` | string | 否 | — | 使用已保存的音色档案 |
| `--save-profile NAME` | string | 否 | — | 将当前 --clone 音频保存为档案 |
| `--list-profiles` | flag | 否 | false | 列出所有已保存的音色档案 |
| `--output PATH` | string | 否 | 自动生成 | 输出文件路径 |
| `--model MODEL` | string | 否 | 自动选择 | 强制指定模型 |
| `-h, --help` | flag | 否 | false | 显示帮助信息 |

**模型自动选择逻辑：**

```
有 --clone     → mimo-v2.5-tts-voiceclone
有 --voice-desc → mimo-v2.5-tts-voicedesign
其他           → mimo-v2.5-tts
```

---

## 6. 使用示例

### 基础用法

```bash
# 默认音色
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好，世界！"

# 指定音色
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --voice "茉莉"
```

### 风格控制

```bash
# 单个风格
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --style "开心"

# 多个风格叠加
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --style "温柔 甜美 慵懒"

# 方言
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好啊" --style "粤语"
```

### 声音克隆

```bash
# 直接克隆
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --clone ~/voice.mp3

# 克隆并保存为档案
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --clone ~/voice.mp3 --save-profile 小明

# 使用已保存的档案
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --profile 小明
```

### 音色设计

```bash
# 年轻女性
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --voice-desc "年轻女性，温柔甜美，语速稍慢"

# 老年男性
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --voice-desc "老年男性，声音沙哑苍老，语速缓慢"

# 动漫角色
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --voice-desc "萝莉音，活泼可爱，元气满满"
```

### 组合使用

```bash
# 克隆音色 + 风格控制
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --profile 曼波 --style "开心"

# 音色设计 + 方言
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "你好" --voice-desc "年轻女性" --style "四川话"
```

### 实战案例：庄子《逍遥游》

使用曼波音色 + 深沉醇厚风格朗读古典文学：

```bash
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh \
  --text "北冥有鱼，其名为鲲。鲲之大，不知其几千里也。化而为鸟，其名为鹏。鹏之背，不知其几千里也；怒而飞，其翼若垂天之云。是鸟也，海运则将徙于南冥。南冥者，天池也。齐谐者，志怪者也。谐之言曰：鹏之徙于南冥也，水击三千里，抟扶摇而上者九万里，去以六月息者也。野马也，尘埃也，生物之以息相吹也。天之苍苍，其正色邪？其远而无所至极邪？其视下也亦若是，则已矣。且夫水之积也不厚，则负大舟也无力。覆杯水于坳堂之上，则芥为之舟，置杯焉则胶，水浅而舟大也。风之积也不厚，则其负大翼也无力。故九万里则风斯在下矣，而后乃今培风；背负青天而莫之夭阏者，而后乃今将图南。蜩与学鸠笑之曰：我决起而飞，枪榆枋，时则不至而控于地而已矣，奚以之九万里而南为？适莽苍者三湌而反，腹犹果然；适百里者宿舂粮；适千里者三月聚粮。之二虫又何知！小知不及大知，小年不及大年。奚以知其然也？朝菌不知晦朔，蟪蛄不知春秋，此小年也。楚之南有冥灵者，以五百岁为春，五百岁为秋；上古有大椿者，以八千岁为春，八千岁为秋。而彭祖乃今以久特闻，众人匹之，不亦悲乎！" \
  --profile 曼波 \
  --style "深沉 醇厚"
```

**合成结果：**
- 音色：曼波（克隆音色）
- 风格：深沉 + 醇厚
- 文本长度：约 450 字
- 输出大小：3.7 MB
- 时长：约 2 分钟

**示例音频：** [逍遥游.wav](mimo-tts/examples/逍遥游.wav)

> 此案例展示了克隆音色档案 + 风格叠加的实际效果。曼波的音色配合深沉醇厚的风格，非常适合朗读古典文学作品。

---

## 7. 预置音色列表

| 音色 | Voice ID | 语言 | 性别 | 说明 |
|------|----------|------|------|------|
| MiMo-默认 | `mimo_default` | — | — | 系统默认音色 |
| 冰糖 | `冰糖` | 中文 | 女性 | 甜美女声 |
| 茉莉 | `茉莉` | 中文 | 女性 | 清新女声 |
| 苏打 | `苏打` | 中文 | 男性 | 清爽男声 |
| 白桦 | `白桦` | 中文 | 男性 | 沉稳男声 |
| Mia | `Mia` | 英文 | 女性 | English female |
| Chloe | `Chloe` | 英文 | 女性 | English female |
| Milo | `Milo` | 英文 | 男性 | English male |
| Dean | `Dean` | 英文 | 男性 | English male |

> 中国集群默认为 `冰糖`，其他集群默认为 `Mia`。

---

## 8. 风格控制

### 8.1 Style Tags（放在文本开头）

格式：`(风格1 风格2)待合成文本`

支持 `()`、`（）`、`[]` 三种括号。

| 类别 | 可用标签 |
|------|----------|
| **基础情绪** | 开心、悲伤、愤怒、恐惧、惊讶、兴奋、委屈、平静、冷漠 |
| **复合情绪** | 怅然、欣慰、无奈、愧疚、释然、嫉妒、厌倦、忐忑、动情 |
| **整体语调** | 温柔、高冷、活泼、严肃、慵懒、俏皮、深沉、干练、凌厉 |
| **音色定位** | 磁性、醇厚、清亮、空灵、稚嫩、苍老、甜美、沙哑、醇雅 |
| **人设腔调** | 夹子音、御姐音、正太音、大叔音、台湾腔 |
| **方言** | 东北话、四川话、河南话、粤语 |
| **角色扮演** | 孙悟空、林黛玉 |
| **唱歌** | 唱歌（必须在最开头，歌词建议用中文） |

### 8.2 Fine-grained Tags（放在文本任意位置）

格式：`[标签]`，例如 `你好[笑]世界[叹气]`

| 类别 | 可用标签 |
|------|----------|
| **语速与节奏** | 吸气、深呼吸、叹气、长叹一口气、喘息、屏息 |
| **情绪状态** | 紧张、害怕、激动、疲惫、委屈、撒娇、心虚、震惊、不耐烦 |
| **语音特征** | 颤抖、变调、破音、鼻音、气声、沙哑 |
| **哭笑表达** | 笑、轻笑、大笑、冷笑、抽泣、呜咽、哽咽、嚎啕大哭 |

### 8.3 自然语言控制

通过 `role: user` 的 `content` 传入自然语言描述，支持导演模式（角色 + 场景 + 指导三维度）。

---

## 9. 音色档案管理

### 9.1 存储位置

```
~/.claude/skills/mimo-tts/voices/
├── profiles.json       # 音色档案索引
├── 曼波.mp3            # 音色样本文件
└── ...                 # 更多样本
```

### 9.2 profiles.json 格式

```json
{
  "曼波": {
    "file": "曼波.mp3",
    "description": "曼波音色克隆",
    "added": "2026-05-24"
  }
}
```

### 9.3 操作命令

```bash
# 列出所有档案
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --list-profiles

# 保存新档案（需要配合 --clone）
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --clone voice.mp3 --save-profile 名称

# 使用档案
bash ~/.claude/skills/mimo-tts/scripts/mimo-tts.sh --text "文本" --profile 名称
```

---

## 10. API 参考

### 10.1 Endpoint

```
POST {API_URL}/v1/chat/completions
```

**Headers：**
```
Content-Type: application/json
api-key: {API_KEY}
```

### 10.2 预置音色请求

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

### 10.3 声音克隆请求

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

**音频样本要求：**
- 支持 mp3 和 wav 格式
- Base64 编码后不超过 10 MB
- 必须携带前缀：`data:{MIME_TYPE};base64,$BASE64_AUDIO`
- MIME 类型：`audio/mpeg`（mp3）、`audio/wav`（wav）

### 10.4 音色设计请求

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

### 10.5 响应格式

```json
{
  "model": "mimo-v2.5-tts",
  "choices": [
    {
      "message": {
        "audio": {
          "format": "wav",
          "data": "<base64-encoded-wav>"
        }
      }
    }
  ]
}
```

---

## 11. 错误处理

| 状态码 | 原因 | 解决方案 |
|--------|------|----------|
| **401** | API Key 无效或缺失 | 检查 `MIMO_TTS_API_KEY` 配置 |
| **400** | 请求参数错误 | 检查文本内容、音色 ID、模型选择 |
| **429** | 请求频率超限 | 等待后重试 |
| **404** | API 端点不存在 | 检查 `MIMO_TTS_API_URL` 配置 |
| **超时** | 网络问题或文本过长 | 检查网络连接，缩短文本 |
| **无响应** | 网络不可达 | 检查 API_URL 连通性 |

---

## 12. 常见问题

### Q: 音色档案保存在哪里？

A: 保存在 `~/.claude/skills/mimo-tts/voices/` 目录，包含音频文件和 `profiles.json` 索引。

### Q: 声音克隆的音频有什么要求？

A: 支持 mp3 和 wav 格式，Base64 编码后不超过 10 MB。建议使用 10-30 秒清晰、无背景噪音的语音样本。

### Q: 可以同时使用风格控制和声音克隆吗？

A: 可以。风格标签会应用到克隆的音色上。

### Q: 唱歌模式有什么限制？

A: 唱歌标签 `(唱歌)` 必须放在文本最开头，歌词建议用中文。唱歌模式与风格控制互斥。

### Q: 音色设计的描述有什么建议？

A: 1-4 句即可，从性别、年龄、音色质感、情绪语气、语速节奏等维度描述。避免矛盾特征和音质效果词（混响、回声等）。

### Q: 输出音频的格式是什么？

A: 24kHz PCM16LE 单声道 WAV 文件。

---

## 附录：触发条件

当用户输入以下关键词时自动触发：

- 语音合成 / 文字转语音 / TTS / tts
- 朗读 / 读出来 / 合成语音
- 克隆音色 / 声音克隆 / 用XX的声音读
- 任何需要将文本转为语音的请求
