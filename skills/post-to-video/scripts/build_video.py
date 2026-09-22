#!/usr/bin/env python3
"""post-to-video: ffmpeg 分段合成带字幕短视频

流程：durations.json（ffprobe 实测，唯一时长源）→ 每场景「图片循环 + wav」等长分段
→ concat 拼合 → captions.json 生成 SRT → 烧录字幕（对齐 ai-news-factory Subtitles.tsx：
白字 + 黑半透明圆角底 rgba(0,0,0,0.75) + padding 10/24 + radius 12，单行）→ 校验。

规则来源（references/experience.md）：
- 渲染前校验：图片数 == 音频数 == 场景数，禁止无声场景
- 时长禁止手填估算；逐场景 ceil(dur*fps) 进位（总时长只 ceil 一次会切掉片尾，坑 209）
- 渲染后：视频总时长 ≈ captions 末条 endMs（差 >0.5s 即不同源，回 TTS 环节重修）

用法:
  python3 build_video.py --dir <slug_dir> --orientation vertical    # 1080x1440 (3:4)
  python3 build_video.py --dir <slug_dir> --orientation horizontal  # 1440x1080 (4:3)
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

ORIENTATIONS = {
    'vertical':   {'size': (1080, 1440), 'suffix': '3x4', 'img_tag': '3x4'},
    'horizontal': {'size': (1440, 1080), 'suffix': '4x3', 'img_tag': '4x3'},
}


def ffprobe_duration(path: Path) -> float:
    r = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(path)],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def load_plan(slug_dir: Path, img_tag: str):
    """读 content.json scenes（list 顺序=播放顺序）+ durations.json，产出 (sid, image, audio, dur) 列表。
    渲染前校验：图片数 == 音频数 == 场景数，缺一即报错退出。"""
    data = json.loads((slug_dir / 'content.json').read_text(encoding='utf-8'))
    raw = data.get('scenes') or []
    ids = []
    if isinstance(raw, dict):
        ids = sorted(int(k) for k in raw if str(k).isdigit())
    else:
        for i, item in enumerate(raw, 1):
            if isinstance(item, dict):
                try:
                    ids.append(int(item.get('id', item.get('num', i))))
                except (TypeError, ValueError):
                    ids.append(i)
            else:
                ids.append(i)
    dur_path = slug_dir / 'voiceover' / 'durations.json'
    if not dur_path.exists():
        sys.exit(f'缺少 {dur_path}（gen_tts_edge.py 产物，ffprobe 实测时长是唯一时长源）')
    dur_map = json.loads(dur_path.read_text(encoding='utf-8'))

    plan, missing = [], []
    for sid in ids:
        img = slug_dir / 'images' / f'scene{sid}-{img_tag}.png'
        if not img.exists():  # 兜底：无比例后缀的通用命名
            img = slug_dir / 'images' / f'scene{sid}.png'
        aud = slug_dir / 'voiceover' / f'scene{sid}.wav'
        dur = float(dur_map.get(str(sid)) or 0)
        if not img.exists() or img.stat().st_size <= 5120:
            missing.append(f'图片 scene{sid}（{img.name}）')
        if not aud.exists():
            missing.append(f'音频 scene{sid}.wav')
        if dur <= 0:
            missing.append(f'时长 scene{sid}（durations.json 无有效值）')
        if img.exists() and aud.exists() and dur > 0:
            plan.append({'id': sid, 'image': img, 'audio': aud, 'dur': dur})
    if missing:
        sys.exit('渲染前校验失败（图片数/音频数/场景数必须一致）：\n  - ' + '\n  - '.join(missing))
    return plan


def ms_to_srt(ms: int) -> str:
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def write_srt(captions, srt_path: Path):
    lines = []
    for i, c in enumerate(captions, 1):
        lines.append(f"{i}\n{ms_to_srt(c['startMs'])} --> {ms_to_srt(c['endMs'])}\n{c['text']}\n")
    srt_path.write_text('\n'.join(lines), encoding='utf-8')


def find_cjk_font():
    """系统中文字体（禁止商用字体）。PingFang.ttc 在 macOS AssetsV2 下，路径随系统版本漂移，用 glob 找。"""
    import glob
    candidates = sorted(glob.glob(
        '/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/PingFang.ttc'))
    candidates += ['/System/Library/Fonts/Hiragino Sans GB.ttc',
                   '/System/Library/Fonts/STHeiti Medium.ttc']
    for f in candidates:
        if Path(f).exists():
            return f
    raise FileNotFoundError('找不到系统中文字体（PingFang / Hiragino / STHeiti）')


def render_caption_pngs(captions, png_dir: Path, w: int, h: int, font_size: int):
    """每条字幕渲染为全帧透明 PNG。视觉对齐 ai-news-factory Subtitles.tsx：
    白字加粗 + 黑半透明圆角底 rgba(0,0,0,0.75) + padding 10/24 + radius 12，底部居中单行。
    本机 ffmpeg 无 libass/drawtext 时的烧录方案。"""
    from PIL import Image, ImageDraw, ImageFont
    png_dir.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(find_cjk_font(), font_size)
    # Subtitles.tsx: paddingBottom 80 @ 1080p → 按高度比例落到当前画幅
    margin_v = int(round(h * (80 / 1080)))
    pad_x, pad_y, radius = 24, 10, 12
    bg_fill = (0, 0, 0, 191)  # 0.75 * 255
    paths = []
    for i, c in enumerate(captions, 1):
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        text = c['text'].replace('\n', ' ')
        bbox = d.textbbox((0, 0), text, font=font, stroke_width=2)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        # 画在 (x,y) 时字形实际占 (x+bbox[0], y+bbox[1]) … 先对齐字形再画底
        gx0 = (w - tw) // 2
        gy1 = h - margin_v
        gy0 = gy1 - th
        x, y = gx0 - bbox[0], gy0 - bbox[1]
        d.rounded_rectangle(
            [gx0 - pad_x, gy0 - pad_y, gx0 + tw + pad_x, gy0 + th + pad_y],
            radius=radius, fill=bg_fill)
        d.text((x, y), text, font=font, fill=(255, 255, 255, 255),
               stroke_width=2, stroke_fill=(0, 0, 0, 200))
        p = png_dir / f'cap{i:04d}.png'
        img.save(p)
        paths.append((p, c['startMs'] / 1000, c['endMs'] / 1000))
    return paths


def burn_subtitles_overlay(nosub: Path, final_path: Path, cap_pngs, fps_args, crf):
    """用 overlay + enable=between(t,...) 链式烧录字幕 PNG。"""
    inputs = ['-i', str(nosub)]
    for p, _, _ in cap_pngs:
        inputs += ['-loop', '1', '-i', str(p)]
    chain, prev = [], '0:v'
    for i, (_, st, en) in enumerate(cap_pngs, 1):
        label = f'v{i}'
        chain.append(f"[{prev}][{i}:v]overlay=0:0:enable='between(t,{st:.3f},{en:.3f})'[{label}]")
        prev = label
    r = subprocess.run([
        'ffmpeg', '-y', *inputs,
        '-filter_complex', ';'.join(chain), '-map', f'[{prev}]', '-map', '0:a',
        '-c:v', 'libx264', '-crf', crf, '-pix_fmt', 'yuv420p',
        '-c:a', 'copy', '-movflags', '+faststart', '-t', f'{ffprobe_duration(nosub):.3f}',
        str(final_path)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f'字幕烧录失败:\n{r.stderr[-600:]}')


def main():
    p = argparse.ArgumentParser(description='ffmpeg 分段合成带字幕视频')
    p.add_argument('--dir', required=True, help='slug 目录')
    p.add_argument('--orientation', choices=list(ORIENTATIONS), default='vertical')
    p.add_argument('--fps', type=int, default=30)
    p.add_argument('--crf', default='18')
    p.add_argument('--font-size', type=int, default=46, help='字幕像素字号（PlayRes=视频分辨率，46px 符合 40–48px 规范）')
    p.add_argument('--no-subs', action='store_true', help='不烧录字幕')
    p.add_argument('--out', default='', help='输出文件名（默认 video/post-video-{3x4|4x3}.mp4）')
    args = p.parse_args()

    slug_dir = Path(args.dir).expanduser().resolve()
    cfg = ORIENTATIONS[args.orientation]
    w, h = cfg['size']
    plan = load_plan(slug_dir, cfg['img_tag'])

    video_dir = slug_dir / 'video'
    video_dir.mkdir(parents=True, exist_ok=True)
    out_name = args.out or f'post-video-{cfg["suffix"]}.mp4'
    final_path = video_dir / out_name

    # ---- 1. 每场景分段（逐场景 ceil(dur*fps) 进位，坑 209）----
    seg_paths = []
    total_frames = 0
    for sc in plan:
        frames = math.ceil(sc['dur'] * args.fps)
        total_frames += frames
        seg_t = frames / args.fps  # ≥ dur，保证音频完整不被截
        seg = video_dir / f'.seg{sc["id"]}.mp4'
        vf = (f'scale={w}:{h}:force_original_aspect_ratio=decrease,'
              f'pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1')
        r = subprocess.run([
            'ffmpeg', '-y', '-loop', '1', '-framerate', str(args.fps), '-i', str(sc['image']),
            '-i', str(sc['audio']),
            '-c:v', 'libx264', '-tune', 'stillimage', '-preset', 'medium', '-crf', args.crf,
            '-c:a', 'aac', '-b:a', '160k',
            '-pix_fmt', 'yuv420p', '-r', str(args.fps), '-vf', vf,
            '-t', f'{seg_t:.3f}', '-movflags', '+faststart', str(seg)],
            capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f'scene{sc["id"]} 分段编码失败:\n{r.stderr[-500:]}')
        seg_paths.append(seg)
        print(f'[seg ] scene{sc["id"]}: {sc["dur"]:.2f}s → {frames} frames ({seg_t:.3f}s)')

    # ---- 2. concat（同参数分段可直接 -c copy）----
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for seg in seg_paths:
            f.write(f"file '{seg}'\n")
        concat_list = f.name
    nosub = video_dir / '.nosub.mp4'
    r = subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_list,
                        '-c', 'copy', '-movflags', '+faststart', str(nosub)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f'concat 失败:\n{r.stderr[-500:]}')

    # ---- 3. 字幕烧录 ----
    cap_path = slug_dir / 'captions' / 'captions.json'
    if args.no_subs or not cap_path.exists():
        if not cap_path.exists():
            print('[warn] 无 captions.json，输出无字幕版')
        nosub.replace(final_path)
    else:
        captions = json.loads(cap_path.read_text(encoding='utf-8'))
        write_srt(captions, slug_dir / 'captions' / 'captions.srt')  # SRT sidecar 留给平台上传
        cap_pngs = render_caption_pngs(captions, slug_dir / 'captions' / '.cap_pngs', w, h, args.font_size)
        burn_subtitles_overlay(nosub, final_path, cap_pngs, args.fps, args.crf)
        nosub.unlink(missing_ok=True)

    for seg in seg_paths:
        seg.unlink(missing_ok=True)
    Path(concat_list).unlink(missing_ok=True)

    # ---- 4. 渲染后校验：视频总时长 ≈ 音频总时长（差 >0.5s 即漂移）----
    # 基准用 durations.json 求和（音频总时长），不用 captions 末条 endMs——
    # 末条来自 whisper 实测发音结束时刻，天然早于场景尾部 pad 静音，不是视频应有的长度。
    vdur = ffprobe_duration(final_path)
    audio_total = sum(sc['dur'] for sc in plan)
    expect = total_frames / args.fps
    print(f'\n=== 校验 ===')
    print(f'视频时长 {vdur:.2f}s / 音频总时长 {audio_total:.2f}s（分段进位预期 {expect:.2f}s）')
    diff = abs(vdur - audio_total)
    status = 'PASS' if diff <= 0.5 else 'FAIL — 回 TTS 环节检查 durations 是否与本批音频同源'
    print(f'差值 {diff:.2f}s → {status}')
    if cap_path.exists():
        last_end = json.loads(cap_path.read_text(encoding='utf-8'))[-1]['endMs'] / 1000
        print(f'（参考）captions 末条 endMs: {last_end:.2f}s，片尾静音余量 {vdur - last_end:.2f}s')
    print(f'\n=== DONE === {final_path}')
    print(f'分辨率 {w}x{h} @ {args.fps}fps，{len(plan)} 场景')
    print('交付前必须抽帧视觉校验：')
    print(f'  ffmpeg -y -i "{final_path}" -vf "select=eq(n\\,0)" -frames:v 1 /tmp/post2video_first.png')


if __name__ == '__main__':
    main()
