#!/usr/bin/env python3
"""issue_guard.py —— 「我是谁」断言（坑 366/371）

2026-10-31→11-01 实测事故：两条流水线抢同一个知乎标签，
整篇月报写进了日更稿，而所有 13 项验收检查在**错误的文章上**全部给出了合理读数。
根因是没有任何一步问过「我现在在编辑谁的稿子」。

本模块提供三个函数，**任何写平台的脚本第一步都要调用**：

    from issue_guard import guard_editor_tab, claim_tab_file, assert_title

    tab_file = claim_tab_file('zhihu', '2026-10')        # /tmp/zhihu-2026-10-tab.txt
    tab = await guard_editor_tab(tab_file, ARTICLE_ID, TITLE, BODY_SIGNATURE)

判据三条全过才放行：
  ① URL 含本期文章 id（知乎 /p/<id>/edit；B站 draftId；抖音/视频号无 id 则跳过该条）
  ② 编辑器标题 == publish.json 里的本期标题
  ③ 正文首句 == 本期签名（有正文的平台必做）

任何一条不符 → 抛 WrongIssueError，脚本立刻停，不许「试试看」。

平台差异：
  · 知乎      page.url 含 /p/<id>/edit；标题 textarea[placeholder*="请输入标题"]；正文 div.public-DraftEditor-content
  · 公众号    page.url 含 appmsgid=<id> 或 token（草稿态无 appmsgid → 改为「标题 ProseMirror 文本」判据）
  · B站       page.url 含 draftId=<id>；标题 input[placeholder*="标题"]
  · 抖音/视频号  无稳定 id → 只能用「标题 + 描述首句」判

设计原则：
  1. 只在 **Playwright page** 上工作（raw CDP 请自行传 evaluate 函数）。
  2. 不做任何写操作 —— 纯只读，可在任何步骤前后反复调用。
  3. 判据失败时把「实际读到什么」一起打进异常消息，方便判断是被抢了还是选择器变了。
"""

import json
import os
import re


class WrongIssueError(AssertionError):
    """当前编辑器不属于本期 —— 立刻停手，不要重试。"""


def _norm(s):
    return re.sub(r'\s+', '', s or '')


def claim_tab_file(platform, date, base='/tmp'):
    """标签复用文件的规范路径：必须带期次（坑 366）。

    错误：/tmp/zhihu-tab.txt          ← 下一期会捡走上一期留下的标签
    正确：/tmp/zhihu-2026-10-tab.txt
    """
    assert re.fullmatch(r'[\w-]+', platform), platform
    assert re.fullmatch(r'[\d-]+', date), date
    path = os.path.join(base, f'{platform}-{date}-tab.txt')
    os.makedirs(base, exist_ok=True)
    return path


def find_own_page(ctx, issue_token, title=None, title_getter=None):
    """在 ctx.pages 里找**属于本期**的那个标签。

    禁止写法（坑 366 的直接成因）：
        page = next(pg for pg in ctx.pages if 'zhuanlan.zhihu.com' in pg.url)

    本函数要求 url 命中 issue_token **且**（若给了 title）标题匹配。
    """
    cands = [pg for pg in ctx.pages if issue_token and issue_token in (pg.url or '')]
    if title is None:
        return cands[0] if len(cands) == 1 else (cands[0] if cands else None)
    for pg in cands:
        try:
            actual = title_getter(pg) if title_getter else None
        except Exception:
            actual = None
        if _norm(actual) == _norm(title):
            return pg
    return None


def assert_title(actual, expected, what='标题'):
    if _norm(actual) != _norm(expected):
        raise WrongIssueError(
            f'{what}不符 —— 当前编辑器不是本期稿。\n'
            f'  期望: {expected!r}\n  实际: {actual!r}\n'
            f'  处理: 停手。不要重试、不要「覆盖成对的」——先确认你在哪篇稿子上。')


def assert_body_signature(actual_first_chars, signature):
    if not _norm(actual_first_chars).startswith(_norm(signature)):
        raise WrongIssueError(
            f'正文首句不符 —— 当前编辑器不是本期稿。\n'
            f'  期望以: {signature!r} 开头\n  实际: {actual_first_chars!r}')


# ---------------------------------------------------------------------------
# 平台相关的取数函数（Playwright page）
# ---------------------------------------------------------------------------

READERS = {
    'zhihu': dict(
        title_js="() => (document.querySelector('textarea[placeholder*=\"请输入标题\"]')||{}).value || ''",
        body_js="() => { const r = document.querySelector('div.public-DraftEditor-content');"
                " return r ? (r.innerText||'').trim() : ''; }",
        id_in_url=lambda aid: f'/p/{aid}/edit',
    ),
    'wechat': dict(
        title_js="() => { const p = document.querySelectorAll('.ProseMirror')[0];"
                 " return p ? (p.textContent||'').trim() : ''; }",
        body_js="() => { const p = document.querySelectorAll('.ProseMirror')[1];"
                " return p ? (p.textContent||'').trim() : ''; }",
        id_in_url=lambda aid: f'appmsgid={aid}',
    ),
    'bilibili': dict(
        title_js="() => (document.querySelector('input[placeholder*=\"标题\"]')||{}).value || ''",
        body_js="() => (document.querySelector('#post-description textarea, .ql-editor')||{}).innerText || ''",
        id_in_url=lambda aid: f'draftId={aid}',
    ),
}


def guard_editor_tab(page, platform, article_id=None, title=None, body_signature=None):
    """在 Playwright page 上执行三条自证。纯只读。

    返回 dict（便于写进状态文件留证）：
        {'platform', 'url', 'title', 'body_head', 'checks': {...}}
    """
    spec = READERS.get(platform)
    if not spec:
        raise ValueError(f'未支持的平台: {platform}（可在 READERS 里扩展）')

    url = page.url or ''
    actual_title = (page.evaluate(spec['title_js']) or '').strip()
    body = (page.evaluate(spec['body_js']) or '').strip()

    checks = {}
    if article_id:
        tok = spec['id_in_url'](article_id)
        checks['article_id'] = tok in url
    if title is not None:
        checks['title'] = _norm(actual_title) == _norm(title)
    if body_signature:
        checks['body_signature'] = _norm(body).startswith(_norm(body_signature))

    report = {'platform': platform, 'url': url, 'title': actual_title,
              'body_head': body[:40], 'checks': checks}

    failed = [k for k, v in checks.items() if not v]
    if failed:
        raise WrongIssueError(
            f'[{platform}] 身份断言失败: {failed}\n'
            f'  url      = {url}\n'
            f'  title    = {actual_title!r}（期望 {title!r}）\n'
            f'  body头   = {body[:40]!r}'
            + (f'（期望以 {body_signature!r} 开头）' if body_signature else '')
            + '\n  处理: 停手。你以为在写的稿子不是这一篇。')

    return report


def guard_from_publish_json(page, platform, publish_json_path, article_id=None,
                            body_signature=None):
    """从 publish.json 取标题/专栏等，做同一条断言。"""
    pub = json.load(open(publish_json_path, encoding='utf-8'))
    title = (pub.get('platform', {}).get(platform, {}) or {}).get('title')
    return guard_editor_tab(page, platform, article_id=article_id,
                            title=title, body_signature=body_signature)


if __name__ == '__main__':
    print(__doc__)
