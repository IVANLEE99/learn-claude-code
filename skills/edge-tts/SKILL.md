---
name: edge-tts
description: Text-to-Speech via Microsoft Edge / Azure Neural TTS. Convert text to speech, list available voices, generate MP3 audio. Trigger when user says "TTS", "text to speech", "语音合成", "朗读", "读给我听", "说给我听", "朗读文章", "语音", "speak", "read aloud", "edge tts", "edge-tts", or needs to convert text to speech.
version: 1.0.0
---

# edge-tts — Microsoft Edge / Azure Neural TTS Skill

Edge TTS wrapper using Microsoft Edge's online text-to-speech service (Azure Neural voices). No API key needed.

## Installation

```bash
pip install edge-tts
# or
pipx install edge-tts
```

Verify: `edge-tts --version`

## Trigger Conditions

Activate when user asks to:
- Convert text to speech / read text aloud
- "TTS", "语音合成", "朗读", "speak", "read aloud"
- "edge tts", "edge-tts", "Azure TTS", "微软语音"
- List available voices or pick a voice
- Generate voiceover / narration for video

## Execution Steps

### Step 1: Parse User Request

Extract from user message:
- **text** (required): The text to convert to speech
- **voice** (optional): Voice name, default `zh-CN-XiaoxiaoNeural`
- **rate** (optional): Speech rate adjustment, default `+0%`
- **pitch** (optional): Pitch shift, default `+0Hz`
- **volume** (optional): Volume adjustment, default `+0%`
- **output** (optional): Output file path
- **subtitles** (optional): Whether to also generate SRT subtitles

If the user only provides text, use all defaults.

### Step 2: Check edge-tts Installation

```bash
python3 -c "import edge_tts; print(edge_tts.__version__)"
```

If this fails, install it:
```bash
pip install edge-tts
```

### Step 3: List Voices (if user asks)

To show all available voices grouped by locale:

```bash
python3 ~/.claude/skills/edge-tts/scripts/edge-tts-synth.py --list-voices
```

To show voices for a specific locale:

```bash
python3 ~/.claude/skills/edge-tts/scripts/edge-tts-synth.py --list-voices --locale zh-CN
```

Or use the edge-tts built-in command:

```bash
edge-tts --list-voices
```

### Step 4: Synthesize Speech

**From text string:**
```bash
python3 ~/.claude/skills/edge-tts/scripts/edge-tts-synth.py \
  --text "你好，这是 Edge TTS 语音合成测试。" \
  --output /Users/youngsdream/Documents/learn-claude-code/output.mp3
```

**From text file:**
```bash
python3 ~/.claude/skills/edge-tts/scripts/edge-tts-synth.py \
  --file /Users/youngsdream/Documents/learn-claude-code/input.txt \
  --output /Users/youngsdream/Documents/learn-claude-code/output.mp3
```

**With custom voice and speech parameters:**
```bash
python3 ~/.claude/skills/edge-tts/scripts/edge-tts-synth.py \
  --text "Hello world" \
  --voice en-US-AriaNeural \
  --rate +10% \
  --pitch -5Hz \
  --volume +0% \
  --output output.mp3
```

**With SRT subtitles:**
```bash
python3 ~/.claude/skills/edge-tts/scripts/edge-tts-synth.py \
  --text "这是第一句。这是第二句。" \
  --output output.mp3 \
  --write-subtitles output.srt
```

**Direct edge-tts CLI (alternative):**
```bash
edge-tts --voice zh-CN-XiaoxiaoNeural --text "你好" --write-media output.mp3
```

> ⚠️ **Negative values must use `=` syntax** to avoid CLI parsing errors:
> ```bash
> edge-tts --rate=-50% --text "Hello" --write-media output.mp3
> # NOT: --rate -50%  (this breaks)
> ```

### Step 5: Report Results

After synthesis, report:
- Output file path
- Voice used (name + gender + style)
- Rate / pitch / volume settings
- File size
- Subtitle file path (if generated)

## Available Azure Neural Voices

All voices are **Azure Neural TTS** (same voices available in Azure Speech Service). The `★` marks recommended voices.

### 🇨🇳 Chinese — Simplified (zh-CN)

| Voice | Gender | Style |
|-------|--------|-------|
| `zh-CN-XiaoxiaoNeural` ★ | Female | Warm, News/Novel |
| `zh-CN-YunyangNeural` ★ | Male | Professional, News |
| `zh-CN-YunxiNeural` | Male | Lively, Sunshine |
| `zh-CN-XiaoyiNeural` | Female | Lively, Cartoon/Novel |
| `zh-CN-YunjianNeural` | Male | Passion, Sports/Novel |
| `zh-CN-YunxiaNeural` | Male | Cute, Cartoon/Novel |
| `zh-CN-XiaochenNeural` | Female | General |
| `zh-CN-XiaohanNeural` | Female | General |
| `zh-CN-XiaomengNeural` | Female | General |
| `zh-CN-XiaomoNeural` | Female | General |
| `zh-CN-XiaoqiuNeural` | Female | General |
| `zh-CN-XiaoruiNeural` | Female | General |
| `zh-CN-XiaoshuangNeural` | Female | General |
| `zh-CN-XiaoxuanNeural` | Female | General |
| `zh-CN-XiaoyanNeural` | Female | General |
| `zh-CN-liaoning-XiaobeiNeural` | Female | Humorous (Liaoning dialect) |
| `zh-CN-shaanxi-XiaoniNeural` | Female | Bright (Shaanxi dialect) |

### 🇭🇰 Chinese — Cantonese (zh-HK)

| Voice | Gender | Style |
|-------|--------|-------|
| `zh-HK-HiuGaaiNeural` | Female | Cantonese (HK) |
| `zh-HK-HiuMaanNeural` | Female | Cantonese (HK) |
| `zh-HK-WanLungNeural` | Male | Cantonese (HK) |

### 🇹🇼 Chinese — Taiwan (zh-TW)

| Voice | Gender | Style |
|-------|--------|-------|
| `zh-TW-HsiaoChenNeural` | Female | Taiwan Mandarin |
| `zh-TW-HsiaoYuNeural` | Female | Taiwan Mandarin |
| `zh-TW-YunJheNeural` | Male | Taiwan Mandarin |

### 🇺🇸 English — US (en-US)

| Voice | Gender | Style |
|-------|--------|-------|
| `en-US-AriaNeural` ★ | Female | News/Novel |
| `en-US-JennyNeural` ★ | Female | Friendly, General |
| `en-US-GuyNeural` ★ | Male | News/Novel, Passion |
| `en-US-AndrewNeural` | Male | Warm, Conversation |
| `en-US-ChristopherNeural` | Male | News, Reliable/Authority |
| `en-US-EmmaNeural` | Female | Cheerful, Conversation |
| `en-US-MichelleNeural` | Female | News, Friendly |
| `en-US-BrianNeural` | Male | Conversation, Approachable |
| `en-US-SteffanNeural` | Male | News, Rational |
| `en-US-RogerNeural` | Male | News, Lively |
| `en-US-EricNeural` | Male | News, Rational |
| `en-US-AnaNeural` | Female | Cartoon, Cute |

### 🇬🇧 English — UK (en-GB)

| Voice | Gender | Style |
|-------|--------|-------|
| `en-GB-SoniaNeural` | Female | General |
| `en-GB-RyanNeural` | Male | General |
| `en-GB-LibbyNeural` | Female | General |
| `en-GB-MaisieNeural` | Female | General |
| `en-GB-ThomasNeural` | Male | General |

### 🇯🇵 Japanese (ja-JP)

| Voice | Gender | Style |
|-------|--------|-------|
| `ja-JP-NanamiNeural` | Female | General |
| `ja-JP-KeitaNeural` | Male | General |

### 🇰🇷 Korean (ko-KR)

| Voice | Gender | Style |
|-------|--------|-------|
| `ko-KR-SunHiNeural` | Female | General |
| `ko-KR-InJoonNeural` | Male | General |
| `ko-KR-HyunsuMultilingualNeural` | Male | Multilingual |

### 🇫🇷 French (fr-FR)

| Voice | Gender | Style |
|-------|--------|-------|
| `fr-FR-DeniseNeural` | Female | General |
| `fr-FR-EloiseNeural` | Female | General |
| `fr-FR-HenriNeural` | Male | General |

### 🇩🇪 German (de-DE)

| Voice | Gender | Style |
|-------|--------|-------|
| `de-DE-KatjaNeural` | Female | General |
| `de-DE-ConradNeural` | Male | General |

### 🇪🇸 Spanish (es-ES)

| Voice | Gender | Style |
|-------|--------|-------|
| `es-ES-ElviraNeural` | Female | General |
| `es-ES-AlvaroNeural` | Male | General |

### 🇮🇹 Italian (it-IT)

| Voice | Gender | Style |
|-------|--------|-------|
| `it-IT-IsabellaNeural` | Female | General |
| `it-IT-DiegoNeural` | Male | General |

### 🇧🇷 Portuguese — Brazil (pt-BR)

| Voice | Gender | Style |
|-------|--------|-------|
| `pt-BR-FranciscaNeural` | Female | General |
| `pt-BR-AntonioNeural` | Male | General |

> For the full voice list (200+ voices across 100+ locales), run: `edge-tts --list-voices`

## Speech Parameters

| Parameter | Format | Default | Examples |
|-----------|--------|---------|----------|
| `rate` | Percentage of base speed | `+0%` | `+10%` faster, `-20%` slower, `+0%` normal |
| `pitch` | Hz shift from base | `+0Hz` | `+5Hz` higher, `-10Hz` lower |
| `volume` | Percentage of base volume | `+0%` | `+0%` normal, `-50%` quieter |

## Python API (for advanced use)

```python
import asyncio
import edge_tts

async def main():
    communicate = edge_tts.Communicate(
        text="你好世界",
        voice="zh-CN-XiaoxiaoNeural",
        rate="+0%",
        pitch="+0Hz",
        volume="+0%",
    )
    await communicate.save("output.mp3")

    # Or stream chunks
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            # chunk["data"] contains MP3 bytes
            pass
        elif chunk["type"] == "WordBoundary":
            # subtitle timing info
            # chunk = {"type": "WordBoundary", "offset": ..., "duration": ..., "text": "..."}
            pass

asyncio.run(main())
```

## Output Location

- Default output: current working directory
- Recommended: `/Users/youngsdream/Documents/learn-claude-code/` or a project-specific subdirectory

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: edge_ts` | edge-tts not installed | `pip install edge-tts` |
| `edge-tts: error: one of -t/-f/-l required` | Missing arguments | Pass `--text`, `--file`, or `--list-voices` |
| `--rate -50%` parsed as option | CLI misparses leading `-` | Use `--rate=-50%` with `=` syntax |
| `timeout` / network error | Network issue | Retry or check connectivity |
| Voice not found | Typo in voice name | Use `--list-voices` to verify |

## Notes

- All voices are **Azure Neural TTS** voices (same backend as Azure Speech Service)
- No API key required — uses Microsoft Edge's free online service
- Default voice is `zh-CN-XiaoxiaoNeural` (Chinese female, news style)
- For videos/voiceovers, consider `zh-CN-YunyangNeural` (male, professional news) or `en-US-AriaNeural` (English news)
- SSML support is limited — Microsoft only allows SSML that Edge itself can generate
- Output format is MP3 (320 kbps)
