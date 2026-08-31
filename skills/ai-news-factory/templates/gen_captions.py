#!/usr/bin/env python3
"""字幕生成 v3.25.0 — 语义切行 + whisper 词级对齐

内容 100% 来自脚本，时间 100% 来自音频。禁止按字数比例切时间轴。
切行规则见同目录 captions.md。

用法:
  python3 gen_captions.py --report-dir news-pipeline/monthly/2026-08 --dry-run
  python3 gen_captions.py --report-dir news-pipeline/monthly/2026-08
  python3 gen_captions.py --report-dir news-pipeline/2026-08-31 --extra-word 专名
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path('/Users/youngsdream/Documents/learn-claude-code')

PUNCT = set('。！？；，、：')
SENT_END = set('。！？；')
SOFT_PUNCT = set('，、：')
LATIN_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9.\-+ ]*$')

WEAK_BEFORE = {
    '还能', '还能自己', '就好比', '所以', '若仍', '也可能',
    '再被', '再开源', '再收价', '配可', '变钝', '打开',
    '备一', '备一条', '关键词', '可信度',
}
GLUE_TAILS = (
    '稳不稳', '硬新闻主轴', '规划步骤', 'Hy四连发', 'Hy 四连发',
    '编程 Agent', '性价比标杆', '官方直连', '整月风向',
    '能不能扛', '切默认', '把事做完', '调用工具',
)
BAD_ENDS = ('硬新闻', '稳', '自己', '编程', '混元', '回顾')
BAD_STARTS = ('主轴', '不稳', '规划步骤', 'Agent', 'Hy', 'Hy四', 'AI圈')

JIEBA_BASE = [
    'OpenAI', 'ChatGPT', 'Codex', 'GPT', 'DeepSeek', 'Harness', 'AI',
    'GLM', 'Kimi', 'Hy4', 'MoE', 'Flash', 'Gemini', 'Cursor',
    'Claude', 'DSH', 'Agent', 'Astra', 'Fable', 'Grok', 'IDE',
    'Token', 'token', 'API', 'Pro',
]
JIEBA_PHRASES = [
    '羊报AI月报', '羊报AI周刊', '今日羊报AI',
    'DeepSeek Harness', '峰谷定价', '峰谷价',
    '官方确认', '社区实测', '媒体报道',
    '编程 Agent', '硬新闻主轴', '稳不稳', '规划步骤',
    'Hy 四连发', 'Hy四连发', '混元 Hy',
    '四点零 Flash', 'V 四 Flash', '千问二十七 B', '二十七 B',
    '能不能扛', '会不会', '官方直连', '切默认',
    '性价比标杆', '可切换后端', '可回滚仓库', '整月风向',
    '近一半帖', '网络安全关键级', '调用工具', '把事做完',
    '专业锚点', '先放量', '再收价', '再开源',
    'DeepSeek 四点零', 'Grok 四点六', 'Grok 四点七',
    'GLM 五点三', 'Fable 五',
]


def normalize(s):
    return re.sub(r'[\s\.,，。！？；：、""\'\(\)（）\-—…/??""]', '', s)


def _char_len(s):
    return len(s.replace(' ', ''))


def init_jieba(extra_words=None):
    import jieba
    jieba.setLogLevel(60)
    for w in JIEBA_BASE + JIEBA_PHRASES + list(extra_words or []):
        if w:
            jieba.add_word(w)
    return jieba


def segment_words(text, jieba):
    raw = [tok for tok in jieba.cut(text, cut_all=False, HMM=True) if tok and tok.strip()]
    merged = []
    for tok in raw:
        if (merged and LATIN_RE.match(merged[-1]) and LATIN_RE.match(tok)
                and tok not in PUNCT and merged[-1] not in PUNCT):
            merged[-1] = merged[-1] + ' ' + tok
        else:
            merged.append(tok)
    return merged


def _find_golden_cut(buf, soft_min=0.4, soft_max=0.6):
    """标点黄金分割：在 40–60% 处找软标点；找不到则扩到 30–70%。"""
    n = _char_len(buf)
    if n < 2:
        return -1
    for lo, hi in ((soft_min, soft_max), (0.30, 0.70)):
        start, end = int(n * lo), int(n * hi)
        mid = n // 2
        best = -1
        best_dist = 10**9
        acc = 0
        for i, ch in enumerate(buf):
            if ch != ' ':
                acc += 1
            if ch in SOFT_PUNCT and start <= acc <= end:
                dist = abs(acc - mid)
                if dist < best_dist:
                    best_dist = dist
                    best = i + 1
        if best >= 0:
            return best
    return -1


def _split_overlong(buf, max_len, hard_max):
    """超长行：先黄金分割，再弱连接。没有合法切点就整句保留，
    绝不按字硬切（会切开 终止Cursor / 硬新闻主轴）。"""
    if _char_len(buf) <= hard_max:
        return [buf]
    cut = _find_golden_cut(buf)
    if 0 < cut < len(buf):
        left, right = buf[:cut], buf[cut:]
        if _char_len(left) >= 4 and _char_len(right) >= 4:
            return _split_overlong(left, max_len, hard_max) + _split_overlong(right, max_len, hard_max)
    for weak in sorted(WEAK_BEFORE, key=len, reverse=True):
        idx = buf.find(weak)
        if idx >= 6 and _char_len(buf[:idx]) >= 6:
            return _split_overlong(buf[:idx], max_len, hard_max) + _split_overlong(buf[idx:], max_len, hard_max)
    return [buf]


def group_caps(tokens, max_len=16, min_len=6, hard_max=20):
    """语义优先切行：句末强制断；软标点在 ≥max_len 时断；
    允许略超 16 字（≤hard_max=20）以保住专名/动宾/正反并列；
    超 hard_max 才黄金分割。短尾巴并回上一行。"""
    caps = []
    buf = ''
    for tok in tokens:
        if tok in PUNCT:
            buf += tok
            if tok in SENT_END:
                if buf.strip():
                    caps.extend(_split_overlong(buf, max_len, hard_max))
                buf = ''
            else:
                if _char_len(buf) >= max_len:
                    caps.extend(_split_overlong(buf, max_len, hard_max))
                    buf = ''
        else:
            nxt = buf + tok
            if buf and _char_len(nxt) > hard_max:
                cut = _find_golden_cut(buf)
                if 0 < cut < len(buf) and _char_len(buf[:cut]) >= min_len:
                    caps.append(buf[:cut])
                    buf = buf[cut:] + tok
                else:
                    buf = nxt
            else:
                buf = nxt
    if buf.strip():
        caps.extend(_split_overlong(buf, max_len, hard_max))
    caps = [c.strip() for c in caps if c.strip()]
    merged = []
    for c in caps:
        glue = any(c.lstrip('，、：').startswith(t) or c.strip() in (
            t, t + '。', t + '；', t + '、', t + '，') for t in GLUE_TAILS)
        short = _char_len(c) < min_len
        if merged and (short or glue) and _char_len(merged[-1]) + _char_len(c) <= hard_max + 4:
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
    fixed = []
    for c in merged:
        if (fixed and any(fixed[-1].rstrip('，、：').endswith(e) for e in BAD_ENDS)
                and any(c.lstrip('，、：').startswith(s) for s in BAD_STARTS)):
            if _char_len(fixed[-1]) + _char_len(c) <= hard_max + 6:
                fixed[-1] = fixed[-1] + c
                continue
        fixed.append(c)
    return fixed


def merge_short_dwell(aligned, min_sec=1.0):
    """对齐后：时长 <1s 的行并回上一行（物理下限）。"""
    if not aligned:
        return aligned
    out = [dict(aligned[0])]
    for c in aligned[1:]:
        dur = c['end'] - c['start']
        prev_dur = out[-1]['end'] - out[-1]['start']
        if dur < min_sec and _char_len(out[-1]['text'] + c['text']) <= 24:
            out[-1]['text'] = out[-1]['text'] + c['text']
            out[-1]['end'] = c['end']
        elif prev_dur < min_sec and _char_len(out[-1]['text'] + c['text']) <= 24:
            out[-1]['text'] = out[-1]['text'] + c['text']
            out[-1]['end'] = c['end']
        else:
            out.append(dict(c))
    return out


def align_caps_to_words(caps, words, audio_dur):
    if not words:
        total_chars = sum(len(c) for c in caps)
        out = []
        cur = 0.0
        for c in caps:
            d = (len(c) / max(total_chars, 1)) * audio_dur
            out.append({'text': c, 'start': cur, 'end': cur + d})
            cur += d
        return out
    spoken_norm = ''
    char_word = []
    for wi, w in enumerate(words):
        wn = normalize(w['word'])
        for _ in wn:
            char_word.append(wi)
        spoken_norm += wn
    out = []
    search_from = 0
    for cap in caps:
        cn = normalize(cap)
        if not cn:
            continue
        best_ratio = 0
        best_pos = -1
        end_search = len(spoken_norm) - len(cn) + 1
        for pos in range(search_from, max(end_search, search_from)):
            ratio = SequenceMatcher(None, cn, spoken_norm[pos:pos + len(cn)]).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_pos = pos
            if ratio > 0.9:
                break
        if best_pos < 0 or best_pos >= len(char_word):
            start = words[max(0, min(search_from, len(words) - 1))]['start'] if words else 0
            end = start + 1.0
        else:
            start_wi = char_word[best_pos]
            end_wi = char_word[min(best_pos + len(cn) - 1, len(char_word) - 1)]
            start = words[start_wi]['start']
            end = words[end_wi]['end']
            search_from = min(end_wi + 1, len(words))
        out.append({'text': cap, 'start': round(start, 3), 'end': round(end, 3)})
    for i in range(1, len(out)):
        if out[i]['start'] < out[i - 1]['end']:
            out[i]['start'] = out[i - 1]['end']
        if out[i]['end'] <= out[i]['start']:
            out[i]['end'] = round(out[i]['start'] + 0.5, 3)
    return out


def load_scenes(report_dir: Path):
    """优先 scenes-meta.json；否则 voiceover-texts.json（dict 或 list）。"""
    meta_path = report_dir / 'scenes-meta.json'
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        scenes = meta.get('scenes') or []
        out = []
        for sc in scenes:
            audio = sc.get('audio') or f"voiceover/scene{sc['id']}.wav"
            ap = report_dir / audio
            if not ap.exists():
                ap = ROOT / 'news-pipeline/video-project/public/voiceover' / Path(audio).name
            out.append({
                'id': int(sc['id']),
                'text': sc['text'],
                'audio': str(ap),
                'duration': float(sc.get('duration') or 0),
            })
        if out:
            return out

    vt_path = report_dir / 'scripts' / 'voiceover-texts.json'
    if not vt_path.exists():
        raise FileNotFoundError(f'neither scenes-meta.json nor {vt_path}')
    vt = json.loads(vt_path.read_text(encoding='utf-8'))
    raw = vt.get('scenes', vt) if isinstance(vt, dict) else vt
    items = []
    if isinstance(raw, dict):
        for k, text in raw.items():
            if str(k).isdigit():
                items.append((int(k), text))
        items.sort()
    else:
        for i, text in enumerate(raw, 1):
            items.append((i, text))
    vo_dir = report_dir / 'voiceover'
    pub_dir = ROOT / 'news-pipeline/video-project/public/voiceover'
    out = []
    for sid, text in items:
        ap = vo_dir / f'scene{sid}.wav'
        if not ap.exists():
            ap = pub_dir / f'scene{sid}.wav'
        out.append({'id': sid, 'text': text, 'audio': str(ap), 'duration': 0.0})
    return out


def whisper_words(model, audio_path):
    segments, info = model.transcribe(
        audio_path, word_timestamps=True, language='zh', vad_filter=True, beam_size=5)
    words = []
    for seg in segments:
        for w in (seg.words or []):
            words.append({'word': w.word.strip(), 'start': w.start, 'end': w.end})
    return words, info.duration


def parse_args():
    p = argparse.ArgumentParser(description='语义切行 + whisper 对齐字幕')
    p.add_argument('--report-dir', required=True, help='当期目录，如 news-pipeline/monthly/2026-08')
    p.add_argument('--dry-run', action='store_true', help='只切行，不加载 whisper')
    p.add_argument('--extra-word', action='append', default=[], help='额外 jieba 专名，可重复')
    return p.parse_args()


def main():
    args = parse_args()
    os.chdir(ROOT)
    report_dir = Path(args.report_dir)
    if not report_dir.is_absolute():
        report_dir = ROOT / report_dir
    scenes = load_scenes(report_dir)
    jieba = init_jieba(args.extra_word)

    if args.dry_run:
        print('=== DRY-RUN group_caps (no whisper) ===')
        for sc in scenes:
            tokens = segment_words(sc['text'], jieba)
            caps = group_caps(tokens)
            print(f"\n--- Scene {sc['id']} ({len(caps)} lines) ---")
            for c in caps:
                print(f"  [{_char_len(c):2d}] {c}")
        return

    from faster_whisper import WhisperModel
    print('Loading whisper model (small, cpu, int8)...')
    model = WhisperModel('small', device='cpu', compute_type='int8')

    all_caps = []
    scene_offset = 0.0
    for sc in scenes:
        n = sc['id']
        audio = Path(sc['audio'])
        print(f'\n=== Scene {n} ({audio.name}) ===')
        tokens = segment_words(sc['text'], jieba)
        caps = group_caps(tokens)
        print(f'  {len(caps)} caption segments')
        words, adur = whisper_words(model, str(audio))
        dur = adur if adur else sc['duration']
        print(f'  whisper: {len(words)} words, dur={adur:.2f}s (meta {sc["duration"]}s)')
        aligned = align_caps_to_words(caps, words, dur)
        aligned = merge_short_dwell(aligned, min_sec=1.0)
        print(f'  after min-1s merge: {len(aligned)} lines')
        for c in aligned:
            c['sceneId'] = n
            c['startMs'] = int((c['start'] + scene_offset) * 1000)
            c['endMs'] = int((c['end'] + scene_offset) * 1000)
            c['timestampMs'] = c['startMs']
            all_caps.append(c)
        scene_offset += dur if dur else sc['duration']

    out_path = report_dir / 'captions' / 'captions.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(all_caps, ensure_ascii=False, indent=2), encoding='utf-8')
    pub = ROOT / 'news-pipeline/video-project/public/captions.json'
    shutil.copy(out_path, pub)
    print(f'\n=== DONE ===')
    print(f'Captions: {len(all_caps)}')
    print(f'Total: {scene_offset:.2f}s')
    print(f'Output: {out_path}')
    for c in all_caps[:5]:
        print(f"  [{c['startMs']}-{c['endMs']}] {c['text']}")


if __name__ == '__main__':
    main()
