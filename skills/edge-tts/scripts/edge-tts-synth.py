#!/usr/bin/env python3
"""
edge-tts wrapper — text-to-speech via Microsoft Edge TTS (Azure voices).

Usage:
  # List all voices grouped by locale
  python3 edge-tts-synth.py --list-voices

  # List voices for a specific locale
  python3 edge-tts-synth.py --list-voices --locale zh-CN

  # Synthesize speech (text string) — MP3 (default)
  python3 edge-tts-synth.py --text "你好世界" --output output.mp3

  # Synthesize to WAV (requires ffmpeg)
  python3 edge-tts-synth.py --text "你好世界" --output output.wav --format wav

  # Synthesize from file
  python3 edge-tts-synth.py --file input.txt --output output.mp3

  # With custom voice / rate / pitch / volume
  python3 edge-tts-synth.py --text "你好" --voice zh-CN-XiaoxiaoNeural --rate +10% --pitch -5Hz --volume +0% --output output.mp3

  # Also write SRT subtitles
  python3 edge-tts-synth.py --text "你好世界" --output output.mp3 --write-subtitles output.srt

Default voice: zh-CN-YunyangNeural (Azure Neural TTS, 男声, 新闻风格, 专业可靠)
"""

import argparse
import asyncio
import os
import subprocess
import sys

try:
    import edge_tts
except ImportError:
    print("ERROR: edge-tts is not installed. Install with: pip install edge-tts", file=sys.stderr)
    sys.exit(1)


# ── Azure Neural Voice Catalogue (subset — most useful voices) ──────────────
# Full list: edge-tts --list-voices  (200+ voices across 100+ locales)

VOICE_CATALOG = {
    "zh-CN": [
        {"name": "zh-CN-XiaoxiaoNeural",  "gender": "Female", "style": "Warm, News/Novel",       "recommended": True},
        {"name": "zh-CN-YunyangNeural",   "gender": "Male",   "style": "Professional, News",   "recommended": True},
        {"name": "zh-CN-YunxiNeural",    "gender": "Male",   "style": "Lively, Sunshine",     "recommended": False},
        {"name": "zh-CN-XiaoyiNeural",    "gender": "Female", "style": "Lively, Cartoon/Novel", "recommended": False},
        {"name": "zh-CN-YunjianNeural",   "gender": "Male",   "style": "Passion, Sports/Novel", "recommended": False},
        {"name": "zh-CN-YunxiaNeural",    "gender": "Male",   "style": "Cute, Cartoon/Novel",   "recommended": False},
        {"name": "zh-CN-XiaochenNeural",  "gender": "Female", "style": "General",               "recommended": False},
        {"name": "zh-CN-XiaohanNeural",   "gender": "Female", "style": "General",               "recommended": False},
        {"name": "zh-CN-XiaomengNeural",  "gender": "Female", "style": "General",               "recommended": False},
        {"name": "zh-CN-XiaomoNeural",    "gender": "Female", "style": "General",               "recommended": False},
        {"name": "zh-CN-XiaoqiuNeural",   "gender": "Female", "style": "General",               "recommended": False},
        {"name": "zh-CN-XiaoruiNeural",   "gender": "Female", "style": "General",               "recommended": False},
        {"name": "zh-CN-XiaoshuangNeural","gender": "Female", "style": "General",               "recommended": False},
        {"name": "zh-CN-XiaoxuanNeural",  "gender": "Female", "style": "General",               "recommended": False},
        {"name": "zh-CN-XiaoyanNeural",   "gender": "Female", "style": "General",               "recommended": False},
        {"name": "zh-CN-liaoning-XiaobeiNeural", "gender": "Female", "style": "Humorous (Liaoning dialect)", "recommended": False},
        {"name": "zh-CN-shaanxi-XiaoniNeural",   "gender": "Female", "style": "Bright (Shaanxi dialect)",    "recommended": False},
    ],
    "zh-HK": [
        {"name": "zh-HK-HiuGaaiNeural", "gender": "Female", "style": "Cantonese (HK)"},
        {"name": "zh-HK-HiuMaanNeural", "gender": "Female", "style": "Cantonese (HK)"},
        {"name": "zh-HK-WanLungNeural", "gender": "Male",   "style": "Cantonese (HK)"},
    ],
    "zh-TW": [
        {"name": "zh-TW-HsiaoChenNeural", "gender": "Female", "style": "Taiwan Mandarin"},
        {"name": "zh-TW-HsiaoYuNeural",   "gender": "Female", "style": "Taiwan Mandarin"},
        {"name": "zh-TW-YunJheNeural",    "gender": "Male",   "style": "Taiwan Mandarin"},
    ],
    "en-US": [
        {"name": "en-US-AriaNeural",        "gender": "Female", "style": "News/Novel", "recommended": True},
        {"name": "en-US-JennyNeural",       "gender": "Female", "style": "General, Friendly", "recommended": True},
        {"name": "en-US-GuyNeural",         "gender": "Male",   "style": "News/Novel, Passion", "recommended": True},
        {"name": "en-US-AndrewNeural",      "gender": "Male",   "style": "Conversation, Warm", "recommended": False},
        {"name": "en-US-ChristopherNeural", "gender": "Male",   "style": "News, Reliable/Authority", "recommended": False},
        {"name": "en-US-EmmaNeural",        "gender": "Female", "style": "Conversation, Cheerful", "recommended": False},
        {"name": "en-US-MichelleNeural",    "gender": "Female", "style": "News, Friendly", "recommended": False},
        {"name": "en-US-BrianNeural",       "gender": "Male",   "style": "Conversation, Approachable", "recommended": False},
        {"name": "en-US-SteffanNeural",     "gender": "Male",   "style": "News, Rational", "recommended": False},
        {"name": "en-US-RogerNeural",       "gender": "Male",   "style": "News, Lively", "recommended": False},
        {"name": "en-US-EricNeural",        "gender": "Male",   "style": "News, Rational", "recommended": False},
        {"name": "en-US-AnaNeural",         "gender": "Female", "style": "Cartoon, Cute", "recommended": False},
    ],
    "en-GB": [
        {"name": "en-GB-SoniaNeural",  "gender": "Female", "style": "General"},
        {"name": "en-GB-RyanNeural",   "gender": "Male",   "style": "General"},
        {"name": "en-GB-LibbyNeural",  "gender": "Female", "style": "General"},
        {"name": "en-GB-MaisieNeural", "gender": "Female", "style": "General"},
        {"name": "en-GB-ThomasNeural", "gender": "Male",   "style": "General"},
    ],
    "ja-JP": [
        {"name": "ja-JP-NanamiNeural", "gender": "Female", "style": "General"},
        {"name": "ja-JP-KeitaNeural",  "gender": "Male",   "style": "General"},
    ],
    "ko-KR": [
        {"name": "ko-KR-SunHiNeural",      "gender": "Female", "style": "General"},
        {"name": "ko-KR-InJoonNeural",      "gender": "Male",   "style": "General"},
        {"name": "ko-KR-HyunsuMultilingualNeural", "gender": "Male", "style": "Multilingual"},
    ],
    "fr-FR": [
        {"name": "fr-FR-DeniseNeural", "gender": "Female", "style": "General"},
        {"name": "fr-FR-HenriNeural",  "gender": "Male",   "style": "General"},
        {"name": "fr-FR-EloiseNeural", "gender": "Female", "style": "General"},
    ],
    "de-DE": [
        {"name": "de-DE-KatjaNeural",  "gender": "Female", "style": "General"},
        {"name": "de-DE-ConradNeural", "gender": "Male",   "style": "General"},
    ],
    "es-ES": [
        {"name": "es-ES-ElviraNeural", "gender": "Female", "style": "General"},
        {"name": "es-ES-AlvaroNeural", "gender": "Male",   "style": "General"},
    ],
    "it-IT": [
        {"name": "it-IT-IsabellaNeural", "gender": "Female", "style": "General"},
        {"name": "it-IT-DiegoNeural",    "gender": "Male",   "style": "General"},
    ],
    "pt-BR": [
        {"name": "pt-BR-FranciscaNeural", "gender": "Female", "style": "General"},
        {"name": "pt-BR-AntonioNeural",   "gender": "Male",   "style": "General"},
    ],
}


async def list_voices(locale: str | None = None):
    """Print voice list. Optionally filter by locale prefix."""
    if locale:
        locales = [locale]
    else:
        locales = sorted(VOICE_CATALOG.keys())

    for loc in locales:
        voices = VOICE_CATALOG.get(loc, [])
        if not voices:
            print(f"\n[{loc}]  — no voices in local catalogue, use `edge-tts --list-voices` for full list")
            continue

        print(f"\n[{loc}]")
        for v in voices:
            marker = " ★" if v.get("recommended") else ""
            print(f"  {v['name']:<36} {v['gender']:<6} {v['style']}{marker}")


async def synthesize(
    text: str | None,
    file_path: str | None,
    voice: str,
    rate: str | None,
    pitch: str | None,
    volume: str | None,
    output: str,
    write_subtitles: str | None,
    format: str = "mp3",
):
    if not text and not file_path:
        print("ERROR: provide --text or --file", file=sys.stderr)
        sys.exit(1)

    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    if not text.strip():
        print("ERROR: text is empty", file=sys.stderr)
        sys.exit(1)

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate or "+0%",
        pitch=pitch or "+0Hz",
        volume=volume or "+0%",
    )

    # Determine actual output path and whether we need post-conversion
    is_wav = format.lower() == "wav"
    # edge-tts always outputs MP3; for WAV we convert afterwards
    mp3_output = output if not is_wav else output.rsplit(".", 1)[0] + ".mp3"

    if write_subtitles:
        audio_data = bytearray()
        subs = []
        async for chunk in communicate.stream():
            ctype = chunk.get("type")
            if ctype == "audio":
                audio_data.extend(chunk["data"])
            elif ctype in ("WordBoundary", "SentenceBoundary"):
                subs.append(chunk)
        with open(mp3_output, "wb") as f:
            f.write(audio_data)
        with open(write_subtitles, "w", encoding="utf-8") as f:
            for i, sub in enumerate(subs, 1):
                start = sub["offset"] / 10_000_000
                duration = sub["duration"] / 10_000_000
                end = start + duration
                text_seg = sub["text"]
                f.write(f"{i}\n{start:.3f} --> {end:.3f}\n{text_seg}\n\n")
        print(f"Subtitles: {write_subtitles}")
    else:
        await communicate.save(mp3_output)

    # Convert to WAV if requested
    if is_wav:
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", mp3_output, "-acodec", "pcm_s16le", "-ar", "44100", output],
                check=True,
                capture_output=True,
            )
            os.remove(mp3_output)  # clean up intermediate MP3
            print(f"Converted: {mp3_output} -> {output} (WAV 44.1kHz 16-bit)")
        except FileNotFoundError:
            print("WARNING: ffmpeg not found. Keeping MP3 output. Install ffmpeg for WAV support.", file=sys.stderr)
            output = mp3_output
        except subprocess.CalledProcessError as e:
            print(f"WARNING: ffmpeg conversion failed: {e.stderr.decode()}. Keeping MP3 output.", file=sys.stderr)
            output = mp3_output

    print(f"Output:    {output}")
    print(f"Voice:     {voice}")
    print(f"Rate:      {rate or '+0%'}")
    print(f"Pitch:     {pitch or '+0Hz'}")
    print(f"Volume:    {volume or '+0%'}")


def main():
    parser = argparse.ArgumentParser(
        description="edge-tts wrapper — Text-to-Speech via Microsoft Edge / Azure Neural TTS"
    )
    parser.add_argument("--list-voices", action="store_true", help="List available Azure Neural voices")
    parser.add_argument("--locale", type=str, default=None, help="Filter voices by locale (e.g. zh-CN, en-US)")
    parser.add_argument("--text", type=str, help="Text to synthesize")
    parser.add_argument("--file", type=str, help="Read text from file (UTF-8)")
    parser.add_argument(
        "--voice", type=str, default="zh-CN-YunyangNeural",
        help="Voice name (default: zh-CN-YunyangNeural). Use --list-voices to see all."
    )
    parser.add_argument("--rate", type=str, help="Speech rate, e.g. +0%, -10%, +20%")
    parser.add_argument("--pitch", type=str, help="Pitch shift, e.g. +0Hz, -5Hz, +10Hz")
    parser.add_argument("--volume", type=str, help="Volume, e.g. +0%, -10%")
    parser.add_argument("--output", "-o", type=str, help="Output MP3 file path", required="--list-voices" not in sys.argv)
    parser.add_argument("--write-subtitles", type=str, help="Also write SRT subtitles to this path")
    parser.add_argument("--format", type=str, default="mp3", choices=["mp3", "wav"], help="Output format: mp3 (default) or wav (requires ffmpeg)")

    args = parser.parse_args()

    if args.list_voices:
        asyncio.run(list_voices(args.locale))
    else:
        asyncio.run(synthesize(
            text=args.text,
            file_path=args.file,
            voice=args.voice,
            rate=args.rate,
            pitch=args.pitch,
            volume=args.volume,
            output=args.output,
            write_subtitles=args.write_subtitles,
            format=args.format,
        ))


if __name__ == "__main__":
    main()
