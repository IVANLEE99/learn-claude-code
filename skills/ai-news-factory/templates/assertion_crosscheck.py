#!/usr/bin/env python3
"""断言层 × 本期成品文案 双向交叉检查（v3.85.0，坑 326 的机械防线）。

用途：派生完、渲染/上传之前跑一次，把「判据指向上一期」这类**内容层正确却被自己判死**的
问题挡在最前面。1107 期一晚连踩三次，全部出自这里，且一次都没在内容层。

Run:
    python3 templates/assertion_crosscheck.py --date 2026-11-07 \
        --prev-words 英伟达 ERNIE Kimi 混元 \
        --issue-words Gemini 反重力 Hy-Memory Qwen

参数语义：
  --date        当期 DATE（定位 news-pipeline/<DATE>/）
  --prev-words  上期事件词
  --issue-words 本期主线词（断言要求在场，但成品文案里根本没有）

退出码：0 全绿；1 有 FAIL。

────────────────────────────────────────────────────────────────────────
⚠️ 本工具自身也必须遵守坑 326：**判据要先证明不误伤**。
v3.85.0 首版在 1107 已完成的正确产物上报了 13 处假 FAIL，**三种**形态：

 1) B 段把 `script-<date>.md` 整篇算作「成品文案」，可其中「3 天去重」那段合法列着
    近三天事件（`FlashProve` / `ERNIE` / `白宫住宅代理`）。它是工作笔记，不发平台。
    → 现版本只取 `## 正文` 之后的章节，并额外剥离「去重 / 历史 / 上期」类说明行。

 2) C 段只认 `NAME = [ ... ]` 形态，于是把下面两种**正当判据**当成残留：
      · `for w in [...]: assert w not in DESC`   ← 禁词断言，要求缺席，正当
      · `'stale_<prev>': ('X' in full) or ...`    ← 残留检测，正当
    → 现版本改成**按语义判**：只有「正向断言」（`assert w in ...`，即要求某词必须在场）
      才可能是坑 326；含 `not in` 的块、`stale_*` / `prior_*` 键一律跳过。

 3) B 段把 JSON 整份 `json.load` 后塞进 blob，于是 `wechat-sections-<issue>.json` 的
    `must_not_have`（**禁词表**）里那 8 个上期词全被判「漏进成品文案」。
    → 现版本按**键名语义**取载荷：内容键收（PAYLOAD_KEYS），判据键一律丢（JUDGE_KEYS）。

核心结论：**判据的语义是「要求在场」还是「要求缺席」，比词来自哪一期更重要**；
同一个 JSON 里「发出去的内容」和「用来判它的表」必须分开读。

验证纪律：改动检查器后必须做**双向控制** ——
  ① 正确产物 → 必须 PASS 且 exit 0；② 已知错误输入 → 必须 FAIL 且 exit 1。
  读退出码时**不要接管道**（`| tail` 会让 `$?` 变成 tail 的），先 `> log 2>&1` 再单独读。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

ROOT = '/Users/yihuan/Documents/youngs/learn-claude-code'

ASSERTION_GLOBS = [
    'scripts/audit_*.py',
    'scripts/gen_publish_*.py',
    'scripts/gen_covers_local_*.py',
    'scripts/mp_*_run.py',
    'scripts/bili_upload_*.py',
    'scripts/douyin_e2e_*.py',
    'scripts/channels_upload_*.py',
    'scripts/zhihu_upload_*.py',
    'scripts/_setup_remotion_*.py',
]

# 一段代码里出现这些，说明它是「要求缺席」的判据（禁词表 / 残留检测），合法。
NEGATIVE_MARKERS = re.compile(
    r'\bnot\s+in\b|\bnot\s+any\b|\bstale_|\bprior_|\bSTALE\b|\bforbidden\b'
    r'|\bFORBIDDEN\b|\bBANNED\b|\bmust_not',
    re.I,
)

# 脚本 Markdown 里这些行是工作笔记，不进入成品文案
NOTE_LINE = re.compile(r'去重|历史|上期|上一期|前一期|近三日|3 天去重|三天去重')


def slice_script_md(text: str) -> str:
    """脚本 md 只保留「## 正文」之后的部分（选材排序/去重说明属工作笔记）。"""
    m = re.search(r'^##\s*正文\s*$', text, re.M)
    body = text[m.end():] if m else text
    keep = [ln for ln in body.split('\n') if not NOTE_LINE.search(ln)]
    return '\n'.join(keep)


def blocks_with_flags(text: str):
    """拆出所有 `[ ... ]` 列表块，并标注所在语句是「正向」还是「负向」断言。

    覆盖两种形态：
      · `NAME = [ ... ]` / `'key': ( ... )`      → 从行首到括号配平
      · `for w in [ ... ]:`                       → 判断其后首个 assert 是 in 还是 not in

    yield (start_line, end_line, is_negative, block_text)
    """
    lines = text.split('\n')
    n = len(lines)
    i = 0
    while i < n:
        ln = lines[i]
        if '[' not in ln:
            i += 1
            continue
        # 从这一行开始做括号配平
        j = i
        depth = 0
        buf = []
        while j < n:
            buf.append(lines[j])
            depth += lines[j].count('[') - lines[j].count(']')
            if depth <= 0 and j >= i:
                if depth == 0:
                    break
            j += 1
        if depth != 0:
            i += 1
            continue
        block = '\n'.join(buf)
        # 判断「这段列表是被正向还是负向断言消费的」：
        # 看块本身 + 紧随其后的 3 行（for 循环的 assert 在块之后）
        tail = '\n'.join(lines[j + 1: j + 4])
        head = '\n'.join(lines[max(0, i - 1): i + 1])
        scope = block + '\n' + tail + '\n' + head
        is_neg = bool(NEGATIVE_MARKERS.search(scope))
        yield (i + 1, j + 1, is_neg, block)
        i = j + 1


def die(msg: str) -> None:
    print(f'FAIL: {msg}')
    sys.exit(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True)
    ap.add_argument('--prev-words', nargs='*', default=[])
    ap.add_argument('--issue-words', nargs='*', default=[])
    ap.add_argument('--dir', default=None, help='默认 news-pipeline/<DATE>')
    a = ap.parse_args()

    os.chdir(ROOT)
    D = a.dir or f'news-pipeline/{a.date}'
    if not os.path.isdir(D):
        die(f'{D} 不存在')

    # ---------- 上期词表：给了就用；没给就不猜（见 C2）----------
    # 1111 实测：本期 B站/抖音/视频号三个脚本的 issue-word 表仍写着 GitHub / 7200 / Menlo，
    # 但调用方只手工传了「报告里的显性词」（H200/Seedream…），漏掉这三个 → C 段全绿放行，
    # 上传第一步才被 assert 拦住。
    # 试过「从上一期产物自动推导」，但任何自动推导都会把 'title'/'scenes'/'.mp4' 这类
    # 通用字面量当事件词（实测 144 个里一半是噪声）。因此**不猜上期词**，
    # 改用 C2 的「正向断言 × 本期成品文案」直接对账 —— 那才是坑 441 的真判据。
    if not a.prev_words:
        print('[prev-words] 未传入 —— 跳过 B/C 两段，改由 C2 逐条对账')

    # ---------- 载入本期「会发到平台」的成品文案 ----------
    parts = []

    def add(p):
        try:
            parts.append(open(p, encoding='utf-8').read())
        except Exception:
            pass

    # ⚠️ 形态 3（v3.85.0 第三次实证）：JSON 里既有「会发出去的内容」也有「判据表」。
    #   `wechat-sections-<issue>.json` 的 `must_not_have` 就是**禁词表**，里面必然
    #   列着上期事件词——把它当成品文案读，B 段必然假 FAIL（1107 实测 8 个词全出自这里）。
    #   规则：JSON 按**键名语义**取载荷，判据键一律排除。
    PAYLOAD_KEYS = {'sections', 'tail', 'scenes', 'text', 'title', 'description',
                    'paragraphs', 'body', 'content', 'summary', 'hook', 'heads'}
    JUDGE_KEYS = {'must_have', 'must_not_have', 'must_not', 'forbidden', 'stale',
                  'stale_tokens', 'prior_tokens', 'prior_hits', 'banned', 'checks',
                  'issue_words', 'colloq', 'tags_forbidden', 'forbidden_words',
                  '_rewrite_required', 'ALLOWED_SAME'}

    def json_payload(obj, key=''):
        """只取内容载荷：判据键整块丢弃，其余按类型递归。"""
        if key in JUDGE_KEYS:
            return ''
        if isinstance(obj, str):
            return obj + '\n'
        if isinstance(obj, list):
            return ''.join(json_payload(v, key) for v in obj)
        if isinstance(obj, dict):
            out = []
            for k, v in obj.items():
                if k in JUDGE_KEYS:
                    continue
                out.append(json_payload(v, k))
            return ''.join(out)
        return ''

    def add_json(p):
        try:
            obj = json.load(open(p, encoding='utf-8'))
        except Exception:
            return
        parts.append(json_payload(obj))

    add_json(f'{D}/publish.json')
    add_json(f'{D}/scripts/voiceover-texts.json')
    for p in glob.glob(f'{D}/scripts/wechat-sections-*.json'):
        add_json(p)
    for p in glob.glob(f'{D}/zhihu-article-*.md'):
        add(p)
    # 脚本 md 只取正文（去重/选材排序是工作笔记，合法引用历史事件）
    sm = f'{D}/scripts/script-{a.date}.md'
    if os.path.exists(sm):
        parts.append(slice_script_md(open(sm, encoding='utf-8').read()))

    blob = '\n'.join(parts)
    if not blob.strip():
        die(f'{D} 下没找到任何成品文案（publish.json / voiceover / wechat-sections / zhihu-article）')

    fails, warns = [], []

    # ---------- A) 本期 issue word 是否真的出现在成品文案里 ----------
    missing = [w for w in a.issue_words if w not in blob]
    if missing:
        fails.append(
            f'[A] 本期 issue word 不在成品文案里: {missing}\n'
            f'    建议：**补描述/补文案**（gen_publish 的 description），'
            f'不是从断言表里删掉（坑 380）'
        )
    else:
        print(f'PASS [A] issue words 全部在场（{len(a.issue_words)} 个）')

    # ---------- B) 上期事件词是否出现在成品文案里 ----------
    leaked = [w for w in a.prev_words if w in blob]
    if leaked:
        fails.append(
            f'[B] 上期事件词出现在本期**成品文案**里: {leaked}\n'
            f'    建议：逐个判断——本期合法引用（如专题回溯）就保留并在此说明；'
            f'真残留就改文案。**不要为了让它过而放宽断言**（坑 326）'
        )
    else:
        print(f'PASS [B] 成品文案无上期事件词（{len(a.prev_words)} 个）')

    # ---------- C) 上期事件词是否留在本期「正向断言」里 ----------
    stale_asserts = []
    for pat in ASSERTION_GLOBS:
        for f in sorted(glob.glob(f'{D}/{pat}')):
            try:
                raw = open(f, encoding='utf-8').read()
            except Exception:
                continue
            for s, e, is_neg, block in blocks_with_flags(raw):
                if is_neg:
                    continue           # 禁词表 / 残留检测 = 正当
                hit = [w for w in a.prev_words if w in block]
                if hit:
                    snippet = ' '.join(block.split())[:120]
                    stale_asserts.append(
                        f'{os.path.relpath(f, D)}:{s}-{e}: 正向断言含上期词 {hit} → {snippet}')
    if stale_asserts:
        fails.append(
            '[C] 上期事件词仍留在本期**正向断言**里（要求它们必须在场）:\n  '
            + '\n  '.join(stale_asserts[:20])
            + f'\n    共 {len(stale_asserts)} 处。改成 ① 换本期事件词；'
              f'② 若该词本期确实要出现，把它从上期词表移入本期 issue words'
        )
    else:
        print('PASS [C] 无「正向断言含上期词」（禁词表/残留检测已按语义排除）')

    # ---------- C2) 正向断言要求的词，本期成品文案里到底有没有（坑 441 的真判据）----------
    # 坑 441 的本质不是「词来自上期」，而是「断言要求某词必须在场，但本期内容里没有」。
    # 这不需要知道上期是哪些词 —— 直接对账即可，且能抓住任何来源的过时断言。
    #
    # 只看「事件词表型」的正向断言：一个 list 里 ≥3 个纯词项，且紧随其后有
    # `assert ... in <blob>`。BANNED/EMO/GREY/SENSITIVE 这类多词表天然被排除
    # （它们的 assert 是 `not any(...)` / `not hits`，即负向）。
    orphan = []
    for pat in ASSERTION_GLOBS:
        for f in sorted(glob.glob(f'{D}/{pat}')):
            try:
                raw = open(f, encoding='utf-8').read()
            except Exception:
                continue
            for s, e, is_neg, block in blocks_with_flags(raw):
                if is_neg:
                    continue
                # 只认「明确正向」：紧随其后的 assert 必须形如 `assert x in <blob>`，
                # 且**不含** not / any / hits 这类否定与计数痕迹。
                tail = '\n'.join(raw.split('\n')[e:e + 4])
                if not re.search(r'assert\s+\w+\s+in\s', tail):
                    continue
                if re.search(r'\bnot\b|\bany\b|\bhits\b', tail):
                    continue
                lits = re.findall(r"['\"]([^'\"]{2,24})['\"]", block)
                lits = [x for x in lits if not x.startswith(('.', '/', '#'))
                        and not x.endswith(('.py', '.md', '.json', '.mp4', '.png'))
                        and not re.search(r'[{}\\%]', x)]
                # 字段名不是事件词：name / platform.* / *.title / *.description 等
                lits = [x for x in lits
                        if not re.fullmatch(r'[a-z_]+(\.[a-z_]+)*', x)
                        and '.' not in x]
                if len(lits) < 3:
                    continue
                absent = [x for x in lits if x not in blob]
                # 整表几乎全缺席 → 这张表整个是上期的（坑 441 的典型形态）
                if len(absent) >= max(2, len(lits) * 0.6):
                    orphan.append(
                        f'{os.path.relpath(f, D)}:{s}-{e}: 断言表要求在场但本期没有 '
                        f'{absent[:5]}{"…" if len(absent) > 5 else ""}'
                        f'（全表 {len(lits)} 项，缺 {len(absent)} 项）')
    if orphan:
        fails.append(
            '[C2] 脚本里的「必须在场」词表与本期内容不符（坑 441：派生器只换日期不换内容）:\n  '
            + '\n  '.join(orphan[:15])
            + f'\n    共 {len(orphan)} 处。整表换成本期事件词，**不要删断言**（坑 380）'
        )
    else:
        print('PASS [C2] 所有「必须在场」词表都能在本期内容里找到')

    # ---------- D) publish.json 完整性 ----------
    try:
        pub = json.load(open(f'{D}/publish.json', encoding='utf-8'))
    except Exception as e:
        fails.append(f'[D] publish.json 读取失败: {e}')
        pub = {}
    if pub:
        zh = ((pub.get('platform') or {}).get('zhihu') or {})
        if zh.get('article_id') is not None and not zh.get('article_id'):
            warns.append('platform.zhihu.article_id 为空 —— 重跑 gen_publish 后必须回填旧 id，'
                         '否则知乎身份断言找不到本期文章')
        v = pub.get('video')
        names = [os.path.basename(x) for x in glob.glob(f'{D}/video/*.mp4')]
        if v and names:
            if v not in names:
                fails.append(f'[D] 视频文件名与 publish.video 不一致（坑 401）\n'
                             f'    publish.video = {v!r}\n    video/ 实际 = {names}')
            else:
                print('PASS [D] 视频文件名 == publish.video')

    # ---------- E) 内容层哨兵 ----------
    # 1111 修正（坑 442）：原实现 rglob 整个 news-pipeline/<DATE>/，会把派生器的
    # `scripts.bak-<ts>/` 备份目录、`__pycache__` 也扫进来 —— 备份里本来就带着派生时的
    # 哨兵，于是每期都必然报一堆假 FAIL（本期实测 20 条全是备份目录）。
    # 只扫「会真正被上传/渲染消费」的位置：D 顶层、scripts/、prompts/、captions/。
    sent_re = re.compile(r'__REWRITE_FOR_(\d{4})__')
    SKIP_PARTS = ('scripts.bak-', '__pycache__')
    left = []
    scan = (glob.glob(f'{D}/*') + glob.glob(f'{D}/scripts/*')
            + glob.glob(f'{D}/prompts/*') + glob.glob(f'{D}/captions/*'))
    for f in scan:
        if not os.path.isfile(f) or f.endswith(('.png', '.jpg', '.mp4', '.pdf', '.wav', '.pyc')):
            continue
        if any(s in f for s in SKIP_PARTS):
            continue
        try:
            t = open(f, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        for m in sent_re.finditer(t):
            left.append(f'{os.path.relpath(f, D)} ({m.group(0)})')
    if left:
        fails.append('[E] 仍有未删除的内容层哨兵:\n  ' + '\n  '.join(sorted(set(left))[:20]))
    else:
        print('PASS [E] 无残留哨兵')

    # ---------- F) review-checklist 指向本期 ----------
    rc = f'{D}/review-checklist.md'
    if not os.path.exists(rc):
        warns.append('review-checklist.md 不存在（渲染门禁要求它先于 audit 写好）')
    else:
        t = open(rc, encoding='utf-8').read()
        head = '\n'.join(t.split('\n')[:5])
        if a.date not in t:
            fails.append(f'[F] review-checklist.md 不含本期日期 {a.date} —— 坑 420：'
                         f'派生器只加哨兵不换正文，必须在 audit **之前**整份重写')
        elif a.date not in head:
            warns.append(f'review-checklist 标题区没有 {a.date}，确认它指向本期')
        else:
            print('PASS [F] review-checklist 指向本期')

    # ---------- 汇总 ----------
    print()
    for w in warns:
        print(f'WARN {w}')
    if fails:
        print(f'\n=== {len(fails)} 项 FAIL ===')
        for x in fails:
            print('\n' + x)
        print('\nASSERTION CROSSCHECK FAILED')
        return 1
    print('\nASSERTION CROSSCHECK OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())