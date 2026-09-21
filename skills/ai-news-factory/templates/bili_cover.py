#!/usr/bin/env python3
"""B站封面制作弹窗自动上传（v3.38.0 / 坑 218）。

用法:
    python3 templates/bili_cover.py 2026-09-21
    python3 templates/bili_cover.py 2026-09-21 --cover /abs/path/to.png

前置:
    1. 上传 daemon 已在跑（日常 Chrome + --remote-debugging-port=9222，见 browser_daemon.py）
    2. 封面已拷到日期目录根:
       cp news-pipeline/{date}/images/horizontal-4-3.png news-pipeline/{date}/images/vertical-3-4.png news-pipeline/{date}/
    3. 投稿表单页已打开且视频/标题就位（脚本不动表单其他字段、不点存草稿）

铁律（坑 218）:
    - 点「添加封面」不会触发原生 file chooser -> 禁止 expect_file_chooser（必超时）
    - 此刻页面有 5 个 input[type=file]（.mp4 x2 / .txt / .zip / 封面 image）
      -> 只能按 accept 含 "image" 过滤，禁止 inputs[1] / inputs[-1]（会喂给视频或 zip，静默无报错）
    - 顺序不可换: 先「上传封面」+ set_input_files，再点「完成」；先点完成只关空弹窗
"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

DATE = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else None
if not DATE:
    print(__doc__)
    sys.exit(1)

BASE = f'news-pipeline/{DATE}'
COVER = os.path.abspath(f'{BASE}/horizontal-4-3.png')
if '--cover' in sys.argv:
    COVER = os.path.abspath(sys.argv[sys.argv.index('--cover') + 1])
if not os.path.exists(COVER):
    print(f'COVER NOT FOUND: {COVER}')
    print('提示: gen_images.py 写的是 images/ 子目录，先 cp 到日期目录根')
    sys.exit(2)

BAR = '=' * 60


def shot(page, name):
    path = f'/tmp/bili_cover_{name}.png'
    page.screenshot(path=path)
    print(f'[shot] {path}')
    return path


def find_bili_page(ctx):
    for p in ctx.pages:
        if 'member.bilibili.com' in (p.url or ''):
            return p
    return None


def dump_inputs(page):
    return page.evaluate('''() => Array.from(document.querySelectorAll('input[type="file"]')).map(i => {
      const r = i.getBoundingClientRect();
      return { accept: i.accept || '(none)', visible: !!i.offsetParent, y: Math.round(r.y) };
    })''')


def dialog_open(page):
    return page.evaluate('''() => Array.from(document.querySelectorAll('*'))
      .some(e => (e.textContent || '').trim() === '封面制作' && e.offsetParent
                  && e.getBoundingClientRect().width > 50)''')


def main():
    print(BAR)
    print(f'B站封面上传  date={DATE}  cover={COVER} ({os.path.getsize(COVER)} bytes)')
    print(BAR)

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp('http://localhost:9222')
        ctx = browser.contexts[0]
        page = find_bili_page(ctx)
        if not page:
            print('B站页面未找到（member.bilibili.com）—— 请先打开投稿表单页')
            return
        page.bring_to_front()

        # 0. 已经设过封面就别重复传（幂等，可重入）
        pre = page.evaluate('''() => {
          const empty = document.querySelector('.cover-empty');
          const img = document.querySelector('.cover-img');
          const bg = img ? getComputedStyle(img).backgroundImage : '';
          return { emptyVisible: !!(empty && empty.offsetParent), bg: bg.slice(0, 120) };
        }''')
        print('pre-check:', pre)
        if not pre['emptyVisible'] and ('biliimg' in pre['bg'] or 'bfs/archive' in pre['bg']):
            print('封面已就位，跳过')
            shot(page, 'already')
            browser.close()
            return

        # 1. 滚到封面区并点「添加封面」-> 打开「封面制作」全屏弹窗
        page.evaluate('''() => {
          const empty = document.querySelector('.cover-empty');
          if (empty) empty.scrollIntoView({ block: 'center' });
        }''')
        page.wait_for_timeout(800)
        clicked = page.evaluate('''() => {
          const empty = document.querySelector('.cover-empty');
          if (empty) { empty.click(); return 'clicked .cover-empty'; }
          for (const e of document.querySelectorAll('div, span, button')) {
            if ((e.textContent || '').trim() === '添加封面' && e.offsetParent) { e.click(); return 'clicked 添加封面'; }
          }
          return 'not found';
        }''')
        print('step1 添加封面:', clicked)
        for _ in range(15):
            page.wait_for_timeout(800)
            if dialog_open(page):
                break
        if not dialog_open(page):
            shot(page, 'no_dialog')
            print('FAILED: 「封面制作」弹窗未打开（先看截图）')
            browser.close()
            return
        print('step1 弹窗已开: 封面制作')
        print('step1 file inputs:', dump_inputs(page))

        # 2. 弹窗内点「上传封面」——该操作会渲染出封面的 image input
        up = page.evaluate('''() => {
          for (const e of document.querySelectorAll('span.upload-text, div, span, button')) {
            if ((e.textContent || '').trim() === '上传封面' && e.offsetParent) { e.click(); return 'clicked 上传封面'; }
          }
          return 'not found';
        }''')
        print('step2 上传封面:', up)
        page.wait_for_timeout(2500)
        print('step2 file inputs:', dump_inputs(page))

        # 3. 按 accept 过滤取封面 input（唯一可靠判据）
        handle = page.evaluate_handle('''() => {
          for (const i of document.querySelectorAll('input[type="file"]')) {
            if ((i.accept || '').includes('image')) return i;
          }
          return null;
        }''')
        el = handle.as_element()
        if not el:
            shot(page, 'no_input')
            print('FAILED: 找不到 accept 含 image 的封面 input（禁止退回索引取 input）')
            browser.close()
            return
        el.set_input_files(COVER)
        print('step3 set_input_files OK（按 accept 过滤，未使用索引）')
        page.wait_for_timeout(6000)
        shot(page, 'uploaded')

        # 4. 点「完成」关弹窗（必须在 set_files 之后）
        done = page.evaluate('''() => {
          const loc = Array.from(document.querySelectorAll('.cover-editor-button .button.submit, .button.submit'));
          const hit = loc.filter(e => (e.textContent || '').trim() === '完成' && e.offsetParent).pop();
          if (hit) { hit.click(); return 'clicked 完成'; }
          return 'not found';
        }''')
        print('step4 完成:', done)
        page.wait_for_timeout(3000)
        page.wait_for_timeout(1000)

        # 5. 断言：弹窗已关 + 表单封面缩略图已变成 B站图床
        after = page.evaluate('''() => {
          const empty = document.querySelector('.cover-empty');
          const img = document.querySelector('.cover-img');
          const bg = img ? getComputedStyle(img).backgroundImage : '';
          return { dialogOpen: Array.from(document.querySelectorAll('*'))
                     .some(e => (e.textContent || '').trim() === '封面制作' && e.offsetParent),
                   emptyVisible: !!(empty && empty.offsetParent), bg: bg.slice(0, 160) };
        }''')
        shot(page, 'after')
        ok = (not after['dialogOpen']) and (not after['emptyVisible']) \
            and ('biliimg' in after['bg'] or 'bfs/archive' in after['bg'])
        print('post-check:', after)
        print('RESULT:', '✅ 封面已落到表单' if ok else '❌ 未确认（看截图 /tmp/bili_cover_after.png）')
        print('提醒: 封面过后请单独点 span.submit-draft 存草稿（本脚本不动草稿）')
        browser.close()


main()
