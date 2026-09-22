#!/usr/bin/env python3
"""把 content.json 的 cover_text 叠到无字封面底图上（坑 203 + 2924762 grok 乱码教训）。

API 中文常糊/错字/日英乱码，封面文字必须像素级准确：先出无字插画，再用本脚本本地叠字。
正片只写 covers/vertical-3-4.png 与 covers/horizontal-4-3.png；底图放 covers/.scratch/。

用法:
  python3 overlay_cover_text.py --dir <slug_dir> \\
    --in covers/.scratch/vertical-notext.png --out covers/vertical-3-4.png
  python3 overlay_cover_text.py --dir <slug_dir> --both
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path


def find_cover_font() -> str:
    candidates = [
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
    ]
    candidates += sorted(glob.glob(
        '/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/PingFang.ttc'))
    for f in candidates:
        if Path(f).exists():
            return f
    raise FileNotFoundError('找不到系统中文字体（STHeiti / Hiragino / PingFang）')


def parse_lines(cover_text: str) -> list[str]:
    lines = [ln.strip() for ln in (cover_text or '').splitlines() if ln.strip()]
    if not lines:
        sys.exit('cover_text 为空：禁止把整条 title 印上封面（坑 203）')
    if len(lines) == 1 and len(lines[0]) > 10:
        # 单行过长时按常见冲突点对切，仍优先尊重调用方已拆好的两行
        s = lines[0]
        for sep in ('，', '。', '？', '?', '！', ' '):
            if sep in s:
                a, b = s.split(sep, 1)
                a, b = a.strip(), (sep + b).strip() if sep in '？?！' else b.strip()
                if a and b:
                    return [a, b]
    return lines[:4]


def overlay(src: Path, dst: Path, lines: list[str], fill, stroke):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(src).convert('RGBA')
    w, h = img.size
    # 字号随短边走：竖版约 72–96，横版略小
    font_size = max(48, min(96, int(min(w, h) * 0.072)))
    font = ImageFont.truetype(find_cover_font(), font_size)
    draw = ImageDraw.Draw(img)

    gap = int(font_size * 0.28)
    sizes = []
    for text in lines:
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=3)
        sizes.append((bbox[2] - bbox[0], bbox[3] - bbox[1], bbox[0], bbox[1]))
    total_h = sum(s[1] for s in sizes) + gap * (len(lines) - 1)
    # 偏上：竖版视觉重心约 18% 处起；水平居中（日期/大字都必须 dx=(tw-dw)//2）
    y = int(h * 0.16)
    if y + total_h > int(h * 0.48):
        y = max(int(h * 0.08), int((h * 0.42 - total_h) / 2))

    for text, (tw, th, bx, by) in zip(lines, sizes):
        x = (w - tw) // 2
        draw.text((x - bx, y - by), text, font=font, fill=fill,
                  stroke_width=3, stroke_fill=stroke)
        y += th + gap

    dst.parent.mkdir(parents=True, exist_ok=True)
    img.convert('RGB').save(dst, 'PNG')
    print(f'[ok] {dst} ← {src.name}  {font_size}px  lines={lines!r}')


def main():
    p = argparse.ArgumentParser(description='Pillow 叠封面大字')
    p.add_argument('--dir', required=True, help='slug 目录')
    p.add_argument('--in', dest='src', default='', help='无字底图（相对 slug 或绝对路径）')
    p.add_argument('--out', dest='dst', default='', help='正片输出路径')
    p.add_argument('--both', action='store_true',
                   help='自动叠 .scratch 里的 vertical/horizontal-notext → 两张正片')
    p.add_argument('--fill', default='#2C2416', help='字体颜色（奶油纸默认深棕）')
    p.add_argument('--stroke', default='#F7F1E3', help='描边（衬在插画上）')
    args = p.parse_args()

    slug = Path(args.dir).expanduser().resolve()
    data = json.loads((slug / 'content.json').read_text(encoding='utf-8'))
    lines = parse_lines(data.get('cover_text') or '')
    title = (data.get('title') or '').replace('\n', '')
    joined = ''.join(lines)
    if title and joined.replace(' ', '') == title.replace(' ', '') and '\n' not in (data.get('cover_text') or ''):
        print('[warn] cover_text 几乎等于整条 title，违反坑 203；仍然叠字，请改 content.json 后重跑',
              file=sys.stderr)

    def rgba(hex_color: str):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)

    fill, stroke = rgba(args.fill), rgba(args.stroke)

    jobs = []
    if args.both:
        scratch = slug / 'covers' / '.scratch'
        mapping = [
            ('vertical-notext.png', 'vertical-notext2.png', 'vertical-3-4.png'),
            ('horizontal-notext.png', 'horizontal-notext2.png', 'horizontal-4-3.png'),
        ]
        for a, b, official in mapping:
            src = scratch / b if (scratch / b).exists() else scratch / a
            if not src.exists():
                # 兼容曾经直接堆在 covers/ 根目录的重试稿
                alt = slug / 'covers' / b if (slug / 'covers' / b).exists() else slug / 'covers' / a
                src = alt
            if not src.exists():
                sys.exit(f'找不到无字底图（先放到 covers/.scratch/）: {a}')
            jobs.append((src, slug / 'covers' / official))
    else:
        if not args.src or not args.dst:
            sys.exit('指定 --in/--out，或用 --both')
        src = Path(args.src)
        dst = Path(args.dst)
        if not src.is_absolute():
            src = slug / src
        if not dst.is_absolute():
            dst = slug / dst
        jobs.append((src, dst))

    for src, dst in jobs:
        if not src.exists():
            sys.exit(f'底图不存在: {src}')
        overlay(src, dst, lines, fill, stroke)


if __name__ == '__main__':
    main()
