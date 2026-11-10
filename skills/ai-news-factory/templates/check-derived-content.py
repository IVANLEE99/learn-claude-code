#!/usr/bin/env python3
"""派生后内容层交叉核对（ai-news-factory v3.87.0 坑 429 / linuxdo-daily v16.4.0 坑 A 的共同防线）

在「派生完成」与「生图 / TTS」之间跑一次。目的是在花掉生图额度和 TTS 时长之前，
把两类最贵的错误挡住：

  ① 串期：派生出来的脚本/口播/图片 prompt/公众号 sections 还是上一期的事件（只换了日期）。
  ② 日期形态漏改：派生器只替换了 `2026-11-10` 与 `1110`，漏掉 `11月10日` / `2026, 11, 10,` / `__wx1110`。

用法：
    python3 check-derived-content.py --date 2026-11-10
    python3 check-derived-content.py --date 2026-11-10 --prev 2026-11-09
    python3 check-derived-content.py --date 2026-11-10 --dir news-pipeline/2026-11-10

退出码：0 = 通过；1 = 有串期/漏改，禁止进生图与 TTS。

设计原则（对应坑 326 / 433）：
  · 「上期词出现在本期内容里」**不一定是错**——跨期承接引用是合法的
    （例：1110 场景 5「继上期 SAIR 模组接管国行 Apple 智能之后」）。
    所以本脚本只报「疑似」，并把上下文打出来供人工判；`--strict` 才把它当失败。
  · 「本期事件词不在报告里」**一定是错**——那说明内容层没按当日报告重写。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get('PIPELINE_ROOT', Path.cwd()))

# 日期形态：派生器最容易漏的几种
def date_forms(date_str: str) -> list[str]:
    y, m, d = (int(x) for x in date_str.split('-'))
    mmdd = f'{m:02d}{d:02d}'
    return [
        date_str,                       # 2026-11-10
        f'{y}/{m:02d}/{d:02d}',
        f'{y}, {m}, {d},',              # datetime(2026, 11, 10, ...)
        f'{m}月{d}日',                  # 11月10日
        f'{m}月{d:02d}日',
        f'__wx{mmdd}',                  # __wx1110
        f'_{mmdd}',                     # _1110
        mmdd,                           # 1110
    ]


CN_NUM = '〇一二三四五六七八九十百千万亿两'
EN_TOKEN = re.compile(r'[A-Za-z][A-Za-z0-9.+_-]{2,}')


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        return {'__error__': str(e)}


def flatten_text(obj) -> str:
    """把任意 JSON 结构拉平成一段文本（用于关键词检索）。"""
    out: list[str] = []

    def walk(x):
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, (int, float)):
            out.append(str(x))
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(obj)
    return ' '.join(out)


# 英文句式词黑名单：prompt 模板里的动词/冠词/形容词，不是事件专名
EN_STOPWORDS = {
    'The', 'This', 'That', 'These', 'Those', 'Create', 'Avoid', 'Show', 'Include',
    'Clear', 'Real', 'Modern', 'Professional', 'Cinematic', 'Photorealistic',
    'Highly', 'Detailed', 'Shot', 'Wide', 'Full', 'Frame', 'Landscape', 'Composition',
    'Absolutely', 'No', 'Not', 'With', 'Without', 'And', 'For', 'From', 'Into',
    'Image', 'Images', 'Prompt', 'Scene', 'Model', 'Models', 'Text', 'Watermark',
    'Logo', 'Logos', 'People', 'Facial', 'Features', 'Characters', 'Chinese',
    'American', 'European', 'China', 'Morning', 'Professional',
    # 结构/元信息词（脚本与 sections 里的，不是事件）
    'CTA', 'Hook', 'HookA', 'HookB', 'Now', 'What', 'So', 'TXT', 'IMG', 'VIDEO',
    'BODY', 'TITLE', 'MUST', 'STALE', 'AUTHOR', 'SIGNATURE', 'MP', 'OK', 'FAIL',
}


def english_tokens(text: str) -> set[str]:
    """抽英文专名当「事件词」样本（GitHub / Rubicon / Seedream / H200 …）。"""
    return {t for t in EN_TOKEN.findall(text)
            if not t.islower() and t not in EN_STOPWORDS}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True, help='本期日期 YYYY-MM-DD')
    ap.add_argument('--prev', help='上期日期 YYYY-MM-DD（默认自动减一天不算跨月）')
    ap.add_argument('--dir', help='当期产出目录（默认 news-pipeline/<date>）')
    ap.add_argument('--report', help='当日报告 markdown（默认 data/reports/<date>.md）')
    ap.add_argument('--strict', action='store_true', help='把「上期词疑似残留」也当失败')
    ap.add_argument('--allow-orphans', nargs='*', metavar='LAYER', default=[],
                    help='额外豁免某些层的孤儿专名检查（prompts 层默认已豁免）')
    ap.add_argument('--strict-prompts', nargs='*', metavar='LAYER', default=[],
                    help='对 prompts 层也做严格串期检查（默认豁免，因为英文 prompt 与中文报告词表天然不同）')
    args = ap.parse_args()

    D = Path(args.dir) if args.dir else ROOT / 'news-pipeline' / args.date
    report = Path(args.report) if args.report else ROOT / 'data' / 'reports' / f'{args.date}.md'

    problems: list[str] = []
    warnings: list[str] = []

    print(f'=== 派生内容交叉核对  date={args.date}  dir={D} ===')

    # ---------- 1. 报告必须存在（内容层的唯一事实源） ----------
    if not report.exists():
        problems.append(f'当日报告不存在：{report} —— 内容层没有事实源，禁止生成')
        report_text = ''
    else:
        report_text = report.read_text(encoding='utf-8')
        print(f'✅ 报告存在：{report} ({len(report_text)} 字)')

    # ---------- 2. 收集本期各内容层文本 ----------
    layers: dict[str, str] = {}
    scripts_dir = D / 'scripts'

    script_md = next(iter(sorted(scripts_dir.glob('script-*.md'))), None) if scripts_dir.is_dir() else None
    if script_md:
        layers['script'] = script_md.read_text(encoding='utf-8')
        print(f'   script: {script_md.name}')
    else:
        problems.append('缺少 scripts/script-<date>.md')

    # 元数据字段：这些键下面列出上期词是「声明」而非「内容残留」，串期扫描必须排除
    META_KEYS = {'must_have', 'must_not_have', 'STALE', 'stale', 'forbidden',
                 'FORBIDDEN', 'prior_tokens', 'issue_words', 'COLLOQ', '_rewrite_required'}

    def content_only(obj) -> str:
        """只取内容字段，跳过元数据/禁词表。"""
        out: list[str] = []

        def walk(x):
            if isinstance(x, str):
                out.append(x)
            elif isinstance(x, (int, float)):
                out.append(str(x))
            elif isinstance(x, dict):
                for k, v in x.items():
                    if k in META_KEYS:
                        continue
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)

        walk(obj)
        return ' '.join(out)

    vo_path = scripts_dir / 'voiceover-texts.json'
    if vo_path.exists():
        vo = load_json(vo_path)
        layers['voiceover'] = content_only(vo)
        print(f'   voiceover: {len(vo.get("scenes") or [])} 段')
        # 日期一致性
        if vo.get('date') != args.date:
            problems.append(f'voiceover-texts.json date={vo.get("date")!r}，应为 {args.date}')
    else:
        problems.append('缺少 scripts/voiceover-texts.json')

    for name, key in (
        (f'image-prompts-{args.date}.json', 'prompts'),
        (f'wechat-sections-{args.date.replace("-", "")[4:]}.json', 'sections'),   # wechat-sections-1110.json
    ):
        p = D / 'prompts' / name if key == 'prompts' else scripts_dir / name
        if p.exists():
            layers[key] = content_only(load_json(p))
            print(f'   {key}: {p.name}')
        else:
            warnings.append(f'未找到 {p}（若未派生该层可忽略）')

    if not layers:
        problems.append('没有任何内容层文件可核对')

    # ---------- 3. 日期形态漏改（硬失败） ----------
    # 只有「必须有日期」的层才校验缺失：script / voiceover。
    # prompts / sections 不含日期是正常的（本期就因为没有日期被误报过）。
    DATE_REQUIRED_LAYERS = {'script', 'voiceover'}
    y, mo, dy = (int(x) for x in args.date.split('-'))
    required_forms = (args.date, f'{mo}月{dy}日')
    prev_issue = int(args.date.replace('-', '')[2:]) - 1     # 20261110 → 1110 → 1109

    for layer, text in layers.items():
        # 3a. 上一期期号残留（任何层都查）
        if re.search(rf'(?<!\d){prev_issue}(?!\d)', text):
            problems.append(f'[{layer}] 残留上一期期号 {prev_issue}')
        # 3b. 上一期日期残留（任何层都查）—— 连字符形态 + 中文形态都要查
        #     （负样本测试暴露：只查 "2026-11-09" 会漏掉口播里的 "十一月九日" / "11月9日"）
        if args.prev:
            py, pm, pd = (int(x) for x in args.prev.split('-'))
        else:
            from datetime import date, timedelta
            _d = date(*(int(x) for x in args.date.split('-'))) - timedelta(days=1)
            py, pm, pd = _d.year, _d.month, _d.day
        CN_DIGITS = '〇一二三四五六七八九'
        def cn_day(n: int) -> str:
            if n <= 10:
                return '十' if n == 10 else CN_DIGITS[n]
            if n < 20:
                return '十' + CN_DIGITS[n % 10]
            return CN_DIGITS[n // 10] + '十' + (CN_DIGITS[n % 10] if n % 10 else '')
        prev_forms = [
            f'{py}-{pm:02d}-{pd:02d}',          # 2026-11-09
            f'{pm}月{pd}日',                     # 11月9日
            f'{pm}月{pd:02d}日',                 # 11月09日
            f'十一月{cn_day(pd)}日',             # 十一月九日
        ]
        for pf in prev_forms:
            if pf in text:
                problems.append(f'[{layer}] 残留上一期日期形态 {pf!r}（派生只换了一半日期）')
                break
        # 3c. 本期日期缺失（仅 script / voiceover）
        if layer in DATE_REQUIRED_LAYERS:
            if not any(f in text for f in required_forms):
                problems.append(f'[{layer}] 缺少本期日期（{required_forms} 一个都没出现）')

    # ---------- 4. 串期：英文专名与报告交叉（核心） ----------
    if report_text:
        # 本期报告里出现的英文专名 = 合法词汇表
        report_tokens = english_tokens(report_text)
        # script 里有「3 天去重」说明段，会合法引用上期事件词 → 不做串期判定
        ORPHAN_CHECK_LAYERS = {'voiceover', 'prompts', 'sections'}
        for layer, text in layers.items():
            if layer not in ORPHAN_CHECK_LAYERS:
                continue
            tokens = english_tokens(text)
            # 出现在内容层但完全不在报告里的英文专名 = 疑似上期残留
            orphans = sorted(tokens - report_tokens)
            # 过滤掉技术通配（URL、格式名、模型通用词）
            orphans = [o for o in orphans if not re.match(
                r'^(http|https|www|JSON|UTF|PNG|JPG|MP4|WAV|API|OK|FAIL|TODO)', o)]
            if orphans:
                # 🔴 判据分级（负样本测试出来的）：
                #    · 出现 1 个孤儿专名   → warning（可能是英文 prompt、样式词）
                #    · 出现 >=2 个孤儿专名 → 硬失败（本期负样本：口播里同时残留
                #      GitHub / Rubicon / Menlo / Ventures，5 个孤儿，绝不能判 OK）
                #    · 允许人工用 --allow-orphans 显式豁免（如 prompts 层刻意用英文）
                # prompts 层默认豁免：图片 prompt 用英文描述画面（NVIDIA / GPU / ByteDance），
                # 而报告是中文（英伟达 / 显卡 / 字节），词表天然不重合 —— 那不是串期。
                # 判据只对「中文内容层」（voiceover / sections）严格；prompts 需显式 --strict-prompts 才查。
                DEFAULT_EXEMPT = {'prompts'}
                exempt = DEFAULT_EXEMPT - (set(args.strict_prompts or ()) and set())
                if args.strict_prompts and 'prompts' in args.strict_prompts:
                    exempt = set()
                if args.allow_orphans:
                    exempt |= set(args.allow_orphans)
                if len(orphans) >= 2 and layer not in exempt:
                    problems.append(
                        f'[{layer}] 内容层疑似仍是上期事件：{orphans[:8]} 都不在当日报告里'
                        f'（这是派生后没重写内容层的典型指纹）')
                else:
                    warnings.append(f'[{layer}] 孤立的英文专名（请人工确认是否合法）：{orphans[:12]}')

    # ---------- 5. 锚点必须有资格（ready + narrator + reviewed + 台词逐字） ----------
    bank_path = ROOT / 'ai-concept-bank' / 'concepts.json'
    if bank_path.exists() and 'voiceover' in layers:
        bank = load_json(bank_path)
        concepts = bank.get('concepts') or []
        # 从 script 里找锚点场景标题
        m = re.search(r'###\s*场景\d+（专业锚点[·・]([^）]+)）', layers.get('script', ''))
        if m:
            target = m.group(1).strip()
            hit = next(
                (c for c in concepts
                 if c.get('name') == target or (c.get('name') or '').startswith(target)),
                None,
            )
            if not hit:
                problems.append(f'锚点概念 {target!r} 在 concept-bank 里找不到')
            else:
                s15 = hit.get('script_15s') or ''
                meta = hit.get('script_meta') or {}
                ok = (
                    hit.get('status') == 'ready'
                    and len(s15) > 50
                    and meta.get('authored_by') == 'ai-concept-narrator'
                    and meta.get('reviewed') is True
                )
                if not ok:
                    problems.append(
                        f'锚点 {hit.get("id")} 不合格：status={hit.get("status")} '
                        f'15s={len(s15)}字 authored_by={meta.get("authored_by")} reviewed={meta.get("reviewed")}')
                elif s15 not in layers['voiceover']:
                    problems.append(f'锚点 {hit.get("id")} 的 script_15s 未逐字出现在口播中（禁止改写库内定义句）')
                else:
                    print(f'✅ 锚点 {hit.get("id")} eligible 且台词逐字嵌入')
        else:
            warnings.append('脚本里找不到「### 场景N（专业锚点·XXX）」标题')

    # ---------- 6. 汇总 ----------
    print()
    if warnings:
        print(f'⚠️  疑似问题 {len(warnings)} 条：')
        for w in warnings:
            print(f'   - {w}')
    if problems:
        print(f'❌ 硬失败 {len(problems)} 条：')
        for p_ in problems:
            print(f'   - {p_}')

    if problems or (args.strict and warnings):
        print('\nRESULT: BLOCKED —— 先修内容层，禁止进入生图 / TTS')
        return 1

    print('\nRESULT: OK —— 内容层与当日报告一致，可以进入生图 / TTS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
