#!/usr/bin/env python3
"""post-to-video: edge-tts 逐场景串行配音 → atempo 加速 → 24kHz PCM16 单声道 WAV

规则来源（ai-news-factory 实战坑位，详见 references/experience.md）：
- 先清残留：旧 scene*.wav 一律 shutil.move 归档 .stale_archive/（rm 会被权限拦；旧音频是 desync 头号根因）
- 逐场景串行，禁止并发（并发会让 TTS 静默失败）
- 失败指数退避 5s→15s→30s，最多 3 次；禁止把空 wav / 半截音频当成功
- 输出 WAV 统一 24kHz PCM16LE 单声道（字幕/合成流程兼容格式）
- 时长以 ffprobe 实测为唯一事实源，写入 voiceover/durations.json

用法:
  python3 gen_tts_edge.py --dir <slug_dir> [--voice zh-CN-YunyangNeural] [--atempo 1.4] [--rate +0%]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEFAULT_VOICE = 'zh-CN-YunyangNeural'  # 云扬：男声新闻风，ai-news-factory 长期实测稳定


def load_scenes(slug_dir: Path):
    """从 content.json 读口播场景。兼容：
    - {"scenes": [{"id"/"num": 1, "voiceover"/"text": "..."}]}   （标准，list 保留声明顺序=播放顺序）
    - {"scenes": {"1": "text"}}                                   （dict 按 sid 排序）
    缺失 voiceover 的整条流水线不该继续——口播文本是字幕内容唯一来源。
    """
    cj = slug_dir / 'content.json'
    if not cj.exists():
        raise FileNotFoundError(f'缺少 {cj}，先执行 Step 2 结构化')
    data = json.loads(cj.read_text(encoding='utf-8'))
    raw = data.get('scenes')
    if not raw:
        raise ValueError('content.json 缺少 scenes 字段')
    items = []
    if isinstance(raw, dict):
        for k, v in raw.items():
            if str(k).isdigit():
                text = v if isinstance(v, str) else (v.get('voiceover') or v.get('text') or '')
                items.append((int(k), text))
        items.sort()
    else:
        for i, item in enumerate(raw, 1):
            if isinstance(item, dict):
                try:
                    sid = int(item.get('id', item.get('num', i)))
                except (TypeError, ValueError):
                    sid = i
                text = item.get('voiceover') or item.get('text') or ''
            else:
                sid, text = i, str(item)
            if text.strip():
                items.append((sid, text.strip()))
    if not items:
        raise ValueError('content.json scenes 中没有口播文本（voiceover/text 字段为空）')
    return items


def archive_stale(vo_dir: Path, only=None):
    """旧音频归档而非删除（rm 可能被自动权限判为不可逆删除而拒绝）。
    only 非空时只归档这些场景，其余 wav 留在原地。"""
    stale = sorted(vo_dir.glob('scene*.wav'))
    if only:
        stale = [f for f in stale if f.stem[5:].isdigit() and int(f.stem[5:]) in only]
    if not stale:
        return
    archive = vo_dir / '.stale_archive'
    archive.mkdir(exist_ok=True)
    for f in stale:
        shutil.move(str(f), str(archive / f.name))
    print(f'[stale] 归档 {len(stale)} 个旧 wav → {archive}')


async def synth_one(text: str, voice: str, rate: str, mp3_path: str):
    import edge_tts
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(mp3_path)


def ffprobe_duration(path: Path) -> float:
    r = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(path)],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def main():
    p = argparse.ArgumentParser(description='edge-tts 逐场景配音 → 24k WAV')
    p.add_argument('--dir', required=True, help='slug 目录（含 content.json）')
    p.add_argument('--voice', default=DEFAULT_VOICE)
    p.add_argument('--rate', default='+0%', help='edge-tts 语速，如 +10%%')
    p.add_argument('--atempo', default='1.4', help='ffmpeg 加速倍率，1.0 = 原速')
    p.add_argument('--only', default='', help='只重合成这些场景 id，逗号分隔（如 6,7）；其余 wav 原样保留，不归档')
    args = p.parse_args()

    slug_dir = Path(args.dir).expanduser().resolve()
    scenes = load_scenes(slug_dir)
    only = {int(x) for x in args.only.split(',') if x.strip()}
    if only:
        missing = only - {sid for sid, _ in scenes}
        if missing:
            sys.exit(f'--only 指定的场景不在 content.json：{sorted(missing)}')
        scenes = [(sid, text) for sid, text in scenes if sid in only]
    vo_dir = slug_dir / 'voiceover'
    vo_dir.mkdir(parents=True, exist_ok=True)
    # 坑 223：无 --only 时归档全部旧 wav。重跑前确认 content.json 的 voiceover 是终稿，
    # 否则好的配音被移进 .stale_archive/，只能从归档里捞回来。
    archive_stale(vo_dir, only or None)

    atempo = float(args.atempo)
    durations = {}
    for sid, text in scenes:
        wav = vo_dir / f'scene{sid}.wav'
        ok = False
        last_err = ''
        for attempt, wait in enumerate([0, 5, 15, 30], 0):
            if attempt >= 3:
                break
            if wait:
                print(f'[scene{sid}] 第 {attempt + 1} 次重试，等待 {wait}s…')
                time.sleep(wait)
            try:
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                    mp3_path = tmp.name
                asyncio.run(synth_one(text, args.voice, args.rate, mp3_path))
                af = ['-filter:a', f'atempo={atempo}'] if abs(atempo - 1.0) > 1e-6 else []
                subprocess.run(
                    ['ffmpeg', '-y', '-i', mp3_path, *af,
                     '-acodec', 'pcm_s16le', '-ar', '24000', '-ac', '1', str(wav)],
                    capture_output=True, check=True)
                Path(mp3_path).unlink(missing_ok=True)
                dur = ffprobe_duration(wav)
                if wav.stat().st_size > 1000 and dur > 0:
                    durations[str(sid)] = round(dur, 3)
                    print(f'[scene{sid}] OK {dur:.2f}s  ({len(text)} 字)')
                    ok = True
                    break
                last_err = f'产物异常 size={wav.stat().st_size} dur={dur}'
            except Exception as e:  # 网络抖动 / ffmpeg 失败
                last_err = str(e)[:200]
        if not ok:
            print(f'[scene{sid}] FAILED: {last_err}', file=sys.stderr)
            sys.exit(1)

    dur_path = vo_dir / 'durations.json'
    if only and dur_path.exists():
        kept = json.loads(dur_path.read_text(encoding='utf-8'))
        kept.update(durations)
        durations = kept
    dur_path.write_text(
        json.dumps(durations, ensure_ascii=False, indent=2), encoding='utf-8')
    total = sum(durations.values())
    print(f'\n=== DONE === 场景 {len(durations)} 个，总时长 {total:.2f}s')
    print(f'durations.json → {vo_dir / "durations.json"}（字幕偏移与视频分段的唯一时长源）')
    print('下一步：gen_captions.py --dir <slug_dir> --dry-run')


if __name__ == '__main__':
    main()
