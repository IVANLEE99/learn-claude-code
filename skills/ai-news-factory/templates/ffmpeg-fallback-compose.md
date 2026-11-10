# ffmpeg 直合成兜底（Remotion 不可用时的唯一出片路径）

> **何时用**：`remotion render` 无输出、0% CPU 永久挂起，且
> `node_modules/@remotion/compositor-<platform>/remotion --version` 单独跑也挂死。
> 判定见 SKILL.md 坑 427：**`sample` 全部样本落在同一未知地址 + 物理内存 < 200K + 无 dyld 输出
> = 二进制与本机 OS 不兼容**（典型：SDK 26 构建的二进制跑在 macOS 14 上）。
> 这条路上**不要**再试清 quarantine / `env -i` / 换 node 版本 / 重装包——全部已验证无效。

产物规格：1920×1080 / h264 / AAC 128k，可直接上传五平台。1110 期实测 8 分钟出片（107.48 s / 10.2 MB）。

---

## 0. 前置检查（决定走哪条字幕路径）

```bash
ffmpeg -hide_banner -filters 2>/dev/null | grep -wE "ass|subtitles|drawtext"
```

- **有 `ass`/`subtitles`/`drawtext`** → 可用 `-vf ass=...` 直接烧字幕，跳到 §3。
- **一个都没有**（本机 Homebrew ffmpeg 9.0.2 实测为空）→ 必须走 **PIL 预渲染 overlay**（§4）。

---

## 1. 逐场景切片（图 + 口播 → 片段）

```python
import subprocess, json, os, wave

D = 'news-pipeline/2026-11-10'
vo = json.load(open(f'{D}/scripts/voiceover-texts.json'))
frames = []

for n in sorted(s['num'] for s in vo['scenes']):
    img = f'{D}/images/scene{n}.png'
    wav = f'{D}/voiceover/scene{n}.wav'
    with wave.open(wav, 'rb') as w:
        dur = w.getnframes() / w.getframerate()

    part = f'/tmp/part_{n}.mp4'
    r = subprocess.run([
        'ffmpeg', '-y', '-loop', '1', '-i', img, '-i', wav,
        # 🔴 坑428-①：必须强制 1920x1080 偶数尺寸。
        #    生图端点出 1672x941（高为奇数）→ libx264 直接拒绝，
        #    报 "height not divisible by 2" + "Nothing was written into output file"。
        '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,'
               'pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black',
        '-t', f'{dur:.3f}',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '128k', '-shortest', part,
    ], capture_output=True, text=True)
    assert r.returncode == 0 and os.path.getsize(part) > 10000, r.stderr[-300:]
    frames.append(part)
```

**要点**：
- `-loop 1` + `-t <wav 时长>` + `-shortest`：静帧按音频长度铺满
- 每段单独编码后再 concat（比整体 filter_complex 稳，失败可单段重跑）
- 音频时长用 `wave.getnframes()/getframerate()`，**不要**用 whisper 的 `info.duration`（VAD 会裁掉片尾 pad）

## 2. 拼接

```python
concat = '/tmp/concat_list.txt'
open(concat, 'w').write('\n'.join(f"file '{f}'" for f in frames))
r = subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                    '-i', concat, '-c', 'copy', '/tmp/full_raw.mp4'],
                   capture_output=True, text=True)
assert r.returncode == 0, r.stderr[-300:]
```

## 3. 【有 ass 滤镜时】直接烧字幕

```python
ass = os.path.abspath(f'{D}/captions/captions.ass')
# 🔴 filtergraph 里 `:` 是选项分隔符、`\` 是转义符，绝对路径必须转义
escaped = ass.replace('\\', '/').replace(':', '\\:').replace("'", "\\'")
subprocess.run(['ffmpeg', '-y', '-i', '/tmp/full_raw.mp4',
                '-vf', f'ass={escaped}',
                '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
                '-c:a', 'copy', OUT])
```

## 4. 【无 ass 滤镜时】PIL 预渲染字幕 + overlay

### 4a. 逐条字幕 → 带半透明圆角底的 PNG

```python
from PIL import Image, ImageDraw, ImageFont
import json, os

FONT = '/System/Library/Fonts/PingFang.ttc'
f64 = ImageFont.truetype(FONT, 64)   # 普通字幕
f80 = ImageFont.truetype(FONT, 80)   # Hook 前 5 s 放大（治 2s 跳出）

def render_caption(text, big=False):
    fnt = f80 if big else f64
    bbox = fnt.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 28, 16
    w, h = tw + pad_x * 2, th + pad_y * 2
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=14, fill=(10, 10, 10, 150))
    d.text((pad_x - bbox[0], pad_y - bbox[1]), text, font=fnt, fill=(255, 255, 255, 255))
    return img

caps = json.load(open(f'{D}/captions/captions.json'))   # [{text,startMs,endMs}, ...]
os.makedirs('/tmp/capovl', exist_ok=True)
man = []
for i, c in enumerate(caps):
    s, e = int(c['startMs']), int(c['endMs'])
    big = s < 5000
    img = render_caption(c['text'], big)
    p = f'/tmp/capovl/c{i:03d}.png'
    img.save(p)
    y = 830 if big else 880                    # 底部安全区
    man.append((p, (1920 - img.width) // 2, y, s / 1000.0, e / 1000.0))
json.dump(man, open('/tmp/capovl/man.json', 'w'))
```

### 4b. 标题栏（常驻）

```python
pub = json.load(open(f'{D}/publish.json'))
bar = Image.new('RGBA', (1920, 110), (0, 0, 0, 0))
bd = ImageDraw.Draw(bar)
bd.rounded_rectangle([0, 0, 1919, 109], radius=0, fill=(8, 8, 8, 170))
b40 = ImageFont.truetype(FONT, 40)
bd.rounded_rectangle([24, 20, 24 + 440, 92], radius=36, fill=(196, 62, 48, 255))
bd.text((56, 24), '今日羊报AI', font=b40, fill=(255, 255, 255, 255))
bd.text((504, 38), '2026-11-10', font=b40, fill=(255, 255, 255, 230))
bd.text((560, 24), pub['title'].replace('| 今日羊报AI', '').strip(),
        font=b40, fill=(255, 255, 255, 255))
bar.save('/tmp/capovl/titlebar.png')
```

### 4c. filter_complex 合成（四个语法陷阱全在这里）

```python
man = json.load(open('/tmp/capovl/man.json'))

cmd = ['ffmpeg', '-y', '-i', '/tmp/full_raw.mp4', '-i', '/tmp/capovl/titlebar.png']
for p, _, _, _, _ in man:
    cmd += ['-i', p]                       # 🔴 每个 -i 是独立 argv 元素

fc, prev = [], '0:v'
fc.append('[0:v][1:v]overlay=0:0[t0]'); prev = 't0'
for i, (p, x, y, s, e) in enumerate(man):
    outl = f'o{i}'
    # 🔴 坑428-③：between() 的逗号必须转义，否则报 "No such filter: '0.000'"
    expr = f'between(t\\,{s:.3f}\\,{e:.3f})'
    fc.append(f'[{prev}][{i+2}:v]overlay={x}:{y}:enable={expr}[{outl}]')
    prev = outl
fc.append(f'[{prev}]null[vout]')

cmd += ['-filter_complex', ';'.join(fc),   # 🔴 坑428-④：本机无 -filter_complex_script
        '-map', '[vout]', '-map', '0:a',
        '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p',
        '-c:a', 'copy', OUT]

r = subprocess.run(cmd, capture_output=True, text=True)   # 🔴 绝不走 shell 拼字符串
assert r.returncode == 0, r.stderr[-600:]
```

**四条铁律（错一条就出不了片）**：

| # | 陷阱 | 报错指纹 | 正解 |
|---|---|---|---|
| 1 | 奇数高度 | `height not divisible by 2` + `Nothing was written into output file` | `scale=1920:1080:force_original_aspect_ratio=decrease,pad=...` |
| 2 | `between()` 逗号未转义 | `No such filter: '0.000'` | `between(t\,0.000\,0.740)` |
| 3 | 无 `-filter_complex_script` | `Unrecognized option 'filter_complex_script'` | 用 `-filter_complex` 传整串 |
| 4 | 走 shell 拼串 | `Unrecognized option 'i/tmp/...png'` | `subprocess.run(list)`，参数各自独立 |

## 5. 验收门（缺一不许汇报"视频已生成"）

```bash
ffprobe -v error -show_entries format=duration,size \
        -show_entries stream=codec_type,width,height,codec_name -of json "$OUT"
```

必须同时满足：`duration ≈ 音频总长 ±0.5 s`、`size > 3 MB`、`video h264 1920 1080`、存在 `audio` 流。

**抽帧目检**（别只信数字）：

```bash
ffmpeg -y -ss 2 -i "$OUT" -frames:v 1 /tmp/f2.png     # 2s：Hook 大字 + 标题栏
ffmpeg -y -ss 8 -i "$OUT" -frames:v 1 /tmp/f8.png     # 8s：普通字号字幕
```

```python
import numpy as np; from PIL import Image
im = np.array(Image.open('/tmp/f2.png').convert('RGB'))
print('字幕区 std:', im[830:1000, 300:1620].std())   # >15 = 有字
print('标题栏 std:', im[0:110, :].std())             # >15 = 有标题栏
```

## 6. 归档

```bash
mkdir -p news-pipeline/<DATE>/video
cp "$OUT" news-pipeline/<DATE>/video/
```

文件名必须 = `publish.json` 的 `video` 字段（坑 401），否则三平台上传脚本一律 `FileNotFoundError`。
