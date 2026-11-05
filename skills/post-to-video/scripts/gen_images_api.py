#!/usr/bin/env python3
"""post-to-video 生图直连 API 版（2026-11-05 实测沉淀，替代 gen_images.sh 的 API 路径）

与 gen-img.sh 的差异，也是 11-05 实测的坑：
  1. **不传 output_format** —— rainflow 直接拒
  2. rainflow 端点路径 = base(`/studio/v1`) + `/images/generations`
     ← **不能剥 `/v1`**，否则 403「用户 API Key 仅可调用专用图片 API」
  3. rainflow 白天直连被 reset → **必须 `-x http://127.0.0.1:7897`**
  4. rainflow 只认 1024x1024 / 1024x1536 / auto，**不认 1152x1536**
     → 请求 1152x1536 实测返回 1024x1536（2:3），须本地补白到 3:4
  5. 竖版比例门：接受 ar∈{0.667(2:3), 0.75(3:4)}，2:3 自动左右补白到 1152x1536
  6. 横版：接受 ar∈{1.333(4:3), 1.5(3:2)}，3:2 居中裁到 1536x1152
  7. 端点优先级按用户指定：rainflow(25 张额度) → prism → 其它
  8. 断点续跑：已存在且 >20KB 且**比例合格**才跳过；比例不合格会删掉重出

用法：
  python3 gen_images_api.py <slug_dir> <manifest> [--only 1,2,3]

manifest 每行: <相对路径>|<期望比例 0.75 或 1.3333>|<prompt 相对路径>
  images/scene1-3x4.png|0.75|prompts/scene1-3x4.txt
  images/scene1-4x3.png|1.3333|prompts/scene1-4x3.txt
  covers/.scratch/vertical-notext.png|0.75|prompts/cover-v.txt
"""
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid

try:
    from PIL import Image
except ImportError as e:
    sys.exit(f'FATAL: Pillow 不可用（{e}）')

PROXY = 'http://127.0.0.1:7897'
PAPER = (247, 241, 227)   # 奶油纸底色，补白用（与 post-to-img kawaii-journal 同色）
TARGET_V = (1152, 1536)   # 真 3:4
TARGET_H = (1536, 1152)   # 真 4:3
MIN_BYTES = 20000


def load_endpoints():
    env = json.load(open(os.path.expanduser('~/.claude/settings.json'))).get('env', {})
    eps = []
    for suf in ['', '_000', '_001', '_002', '_003']:
        u, k = env.get(f'GEN_IMG_API_URL{suf}'), env.get(f'GEN_IMG_API_KEY{suf}')
        if not (u and k):
            continue
        base = u.rstrip('/')
        is_rainflow = 'rainflow' in base
        # rainflow 的 base 已含 /studio/v1，直接拼 /images/generations；
        # 其余网关统一 /v1/images/generations。**不要**把 /v1 剥掉再拼。
        if is_rainflow:
            path = '/images/generations'
        else:
            if base.endswith('/v1'):
                base = base[:-3]
            path = '/v1/images/generations'
        model = env.get(f'GEN_IMG_MODEL{suf}') or env.get('GEN_IMG_MODEL') or 'gpt-image-2'
        prio = 0 if is_rainflow else (1 if 'prism' in base else 2)
        eps.append({'url': base + path, 'key': k, 'tag': f'ep{suf}', 'model': model,
                    'rainflow': is_rainflow, 'prio': prio,
                    'proxy': PROXY if is_rainflow else None})
    seen, out = set(), []
    for e in sorted(eps, key=lambda x: x['prio']):   # 同 URL 去重，避免重复烧额度
        key = (e['url'], e['model'])
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def probe(im_path):
    try:
        im = Image.open(im_path)
        im.load()
        return True, im.size
    except Exception as e:
        return False, str(e)


def fit_ratio(path, want_ar):
    """把图规整到目标比例：只补白或裁边，**禁止非等比拉伸**。
    返回 (ok, (w,h), action)"""
    ok, info = probe(path)
    if not ok:
        return False, info, 'decode-fail'
    w, h = info
    ar = w / h

    if want_ar < 1:      # 竖版目标 3:4 = 0.75
        if abs(ar - 0.75) <= 0.06:
            return True, (w, h), 'as-is-3x4'
        if abs(ar - 2 / 3) <= 0.06:      # 2:3 → 左右补白
            im = Image.open(path).convert('RGB')
            tw, th = TARGET_V
            if (w, h) != TARGET_V:
                im = im.resize(TARGET_V, Image.LANCZOS)   # 同为 2:3，等比缩放
                w, h = im.size
            bg = Image.new('RGB', (tw, th), PAPER)
            bg.paste(im, ((tw - w) // 2, 0))
            bg.save(path, 'PNG')
            return True, bg.size, 'pad-2to3'
        return False, (w, h), f'ar {ar:.3f} unsupported'
    else:                # 横版目标 4:3 = 1.3333
        if abs(ar - 4 / 3) <= 0.06:
            return True, (w, h), 'as-is-4x3'
        if abs(ar - 1.5) <= 0.06:        # 3:2 → 居中裁两侧
            im = Image.open(path).convert('RGB')
            if (w, h) != (1536, 1024):
                im = im.resize((1536, 1024), Image.LANCZOS)
            tw, th = TARGET_H
            left = (im.width - tw) // 2
            im.crop((left, 0, left + tw, th)).save(path, 'PNG')
            return True, (tw, th), 'crop-3to2'
        return False, (w, h), f'ar {ar:.3f} unsupported'


def try_one(ep, prompt, out_path, want_ar, sizes):
    for size in sizes:
        body = {'model': ep['model'], 'prompt': prompt, 'size': size,
                'quality': 'high', 'n': 1, 'response_format': 'b64_json'}
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        tmp.close()
        try:
            cmd = ['curl', '-sS', '-X', 'POST', ep['url'],
                   '-H', f"Authorization: Bearer {ep['key']}",
                   '-H', 'Content-Type: application/json',
                   '-H', f"Idempotency-Key: ptv-{uuid.uuid4()}",
                   '-d', json.dumps(body, ensure_ascii=False),
                   '-o', tmp.name, '--max-time', '300']
            if ep.get('proxy'):
                cmd += ['-x', ep['proxy']]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=340)
            if r.returncode != 0:
                print(f'    {ep["tag"]} {size} curl rc={r.returncode} {r.stderr[:80]}')
                continue
            try:
                resp = json.load(open(tmp.name))
            except Exception:
                print(f'    {ep["tag"]} {size} 非 JSON 响应')
                continue
            if 'error' in resp:
                msg = str(resp['error'].get('message', ''))[:100]
                print(f'    {ep["tag"]} {size} error: {msg}')
                if 'ratio' in msg or 'size' in msg or '不支持' in msg:
                    continue          # 尺寸类错误 → 换 size 再试
                return False          # 额度/鉴权类 → 换端点
            if 'detail' in resp:
                print(f'    {ep["tag"]} {size} detail: {str(resp["detail"])[:90]}')
                return False
            d = (resp.get('data') or [{}])[0]
            b64, url = d.get('b64_json'), d.get('url')
            if b64:
                open(out_path, 'wb').write(base64.b64decode(b64))
            elif url:
                subprocess.run(['curl', '-sS', '-o', out_path, url, '--max-time', '180'],
                               timeout=190)
            else:
                print(f'    {ep["tag"]} {size} 无图片数据')
                continue
            if not os.path.exists(out_path):
                print(f'    {ep["tag"]} {size} 下载未落盘')
                continue
            ok, info, action = fit_ratio(out_path, want_ar)
            if not ok:
                print(f'    {ep["tag"]} {size} 比例不合格: {info} ({action})')
                os.remove(out_path)
                continue
            sz = os.path.getsize(out_path)
            if sz < MIN_BYTES:
                print(f'    {ep["tag"]} {size} 文件过小 {sz}B')
                os.remove(out_path)
                continue
            print(f'    [OK] {ep["tag"]} {size} {info[0]}x{info[1]} {action} {sz//1024}KB')
            return True
        except subprocess.TimeoutExpired:
            print(f'    {ep["tag"]} {size} 超时')
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
    return False


def main():
    slug = os.path.abspath(sys.argv[1])
    manifest = os.path.join(slug, sys.argv[2])
    only = set()
    if '--only' in sys.argv:
        only = {x.strip() for x in sys.argv[sys.argv.index('--only') + 1].split(',')}

    eps = load_endpoints()
    print(f'endpoints: {[e["tag"] + ("(rainflow)" if e["rainflow"] else "") for e in eps]}')

    jobs = []
    for line in open(manifest, encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        rel, ar, pfile = line.split('|')
        jobs.append((rel, float(ar), pfile))

    if only:
        jobs = [j for j in jobs if re.search(r'scene(\d+)', j[0]) and
                re.search(r'scene(\d+)', j[0]).group(1) in only]

    failed = []

    def work(job):
        rel, want_ar, pfile = job
        out = os.path.join(slug, rel)
        prompt = open(os.path.join(slug, pfile), encoding='utf-8').read().strip()
        if os.path.exists(out) and os.path.getsize(out) > MIN_BYTES:
            ok, info, action = fit_ratio(out, want_ar)
            if ok:
                print(f'[skip] {rel} ({info[0]}x{info[1]} {action})')
                return True
            print(f'[redo] {rel} 比例/解码不合格 ({action})')
            os.remove(out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        print(f'[gen ] {rel}')
        t0 = time.time()
        for ep in eps:
            sizes = ['1152x1536', '1024x1536'] if want_ar < 1 else ['1536x1152', '1536x1024']
            if try_one(ep, prompt, out, want_ar, sizes):
                print(f'[done] {rel} {time.time() - t0:.0f}s')
                return True
        print(f'[FAIL] {rel}')
        return False

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as pool:   # ≤3，避免 API 429（坑 253）
        for job, ok in zip(jobs, pool.map(work, jobs)):
            if not ok:
                failed.append(job[0])

    print(f'\n=== {len(jobs) - len(failed)}/{len(jobs)} 成功 ===')
    if failed:
        print('失败:', failed)
        print('处置：缩短对应 prompt 后重跑（已合格的会跳过）；仍失败换英文 prompt；不编造图片。')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
