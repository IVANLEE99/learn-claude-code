#!/usr/bin/env python3
"""Bilibili upload for 20261105_si — draft ONLY (span.submit-draft).
Collection: 虢礫緙嘞
"""
import json
import os
import shutil
import sys
from playwright.sync_api import sync_playwright

import argparse as _argparse
_ap = _argparse.ArgumentParser(description='post-to-video 草稿上传')
_ap.add_argument('--dir', required=True, help='slug 目录（含 publish.json）')
ROOT = os.path.abspath(_ap.parse_args().dir)
pub = json.load(open(f'{ROOT}/publish.json'))
BILI = pub['platform']['bilibili']
BILI_TITLE = BILI['title']
DESC = BILI['description']
TAGS = BILI['tags'][:10]
PARTITION = BILI.get('partition', '生活')
COLLECTION = BILI.get('season', '虢礫緙嘞')
COVER = os.path.abspath(f'{ROOT}/covers/horizontal-4-3.png')
VIDEO = os.path.abspath(f'{ROOT}/{pub["video"]}')

assert os.path.exists(VIDEO), f'video missing: {VIDEO}'
assert os.path.exists(COVER), f'cover missing: {COVER}'

SIMPLE = f'/tmp/upload-bili-si.mp4'
shutil.copy2(VIDEO, SIMPLE)
print(f'[bili] video ready -> {SIMPLE} ({os.path.getsize(SIMPLE)} bytes)', flush=True)

def log(*a): print('[bili]', *a, flush=True)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://localhost:9222', timeout=45000)
    ctx = browser.contexts[0]
    page = ctx.new_page()
    page.goto('https://member.bilibili.com/platform/upload/video/frame', wait_until='domcontentloaded', timeout=45000)
    page.wait_for_timeout(4000)

    body0 = page.evaluate('() => document.body.innerText') or ''
    if '扫码登录' in body0:
        print('BILI_RESULT:', json.dumps({'login': False, 'hint': body0[:100]}, ensure_ascii=False))
        sys.exit(2)

    # ---- 1. 视频上传 ----
    inputs = page.locator('input[type=file]')
    target = None
    for i in range(inputs.count()):
        acc = (inputs.nth(i).get_attribute('accept') or '')
        if 'video' in acc or 'mp4' in acc:
            target = inputs.nth(i)
            break
    assert target, 'no video file input found'
    target.set_input_files(SIMPLE)
    log('video set, waiting form ready...')
    page.wait_for_selector('input[placeholder*="标题"], textarea[placeholder*="标题"]', timeout=180000)
    log('form ready')

    # ---- 2. 标题 ----
    ti = page.locator('input[placeholder*="标题"], textarea[placeholder*="标题"]').first
    ti.click()
    page.keyboard.press('Meta+A')
    page.keyboard.type(BILI_TITLE, delay=10)
    page.wait_for_timeout(600)
    log('title typed len=', len(BILI_TITLE))

    # ---- 3. 封面 ----
    try:
        page.locator('text=添加封面').first.click(timeout=5000)
        page.wait_for_timeout(2500)
        up = page.locator('span.upload-text')
        if up.count() == 0:
            up = page.get_by_text('上传封面')
        up.first.click()
        page.wait_for_timeout(1500)
        cover_input = None
        for i in range(page.locator('input[type=file]').count()):
            acc = (page.locator('input[type=file]').nth(i).get_attribute('accept') or '')
            if 'image' in acc:
                cover_input = page.locator('input[type=file]').nth(i)
                break
        assert cover_input, 'no image accept input in cover dialog'
        cover_input.set_input_files(COVER)
        page.wait_for_timeout(3000)
        page.locator('.cover-editor-button .button.submit, button:has-text("完成")').first.click()
        page.wait_for_timeout(2000)
        log('cover done')
    except Exception as e:
        log('cover error:', str(e))

    # ---- 4. 分区 ----
    hs = page.evaluate('''() => {
      const hs = Array.from(document.querySelectorAll('h1,h2,h3,h4,div,span'));
      const h = hs.find(e => e.children.length === 0 && e.textContent.trim() === '分区');
      if (!h) return null;
      let p = h.parentElement && h.parentElement.querySelector('p, span');
      if (!p || p.textContent.trim() === '分区') {
        const sib = h.parentElement && h.parentElement.parentElement;
        p = sib && sib.querySelector('p, span:not(:has(*))');
      }
      return p ? p.textContent.trim() : '';
    }''')
    log('partition current:', hs)
    if hs != PARTITION:
        page.evaluate("""() => {
          const p=[...document.querySelectorAll('p.select-item-cont')].find(e=>e.offsetParent);
          if (p) p.click();
        }""")
        page.wait_for_timeout(2000)
        loc = page.locator('.drop-list-v2-item', has_text=PARTITION).first
        if loc.count() > 0:
            loc.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            loc.click(force=True)
            page.wait_for_timeout(1500)
        log('partition set')

    # ---- 5. 创作声明 ----
    try:
        page.locator('.creation-statement-container .bcc-select').first.click(force=True, timeout=5000)
        page.wait_for_timeout(800)
        page.locator('text=个人观点，仅供参考').first.click(timeout=5000)
        page.wait_for_timeout(500)
        log('declaration set')
    except Exception as e:
        log('declaration skip:', str(e)[:80])

    # ---- 6. 标签 ----
    def chips():
        return page.evaluate('''() => Array.from(document.querySelectorAll('.label-item-v2-container'))
          .map(c => (c.innerText || '').replace(/×/g,'').trim()).filter(Boolean)''')

    for _ in range(12):
        cur = chips()
        if not cur: break
        drop = [c for c in cur if c not in TAGS]
        if not drop: break
        page.evaluate('''(name) => {
          const cs = Array.from(document.querySelectorAll('.label-item-v2-container'));
          const c = cs.find(x => (x.innerText||'').replace(/×/g,'').trim() === name);
          if (!c) return;
          const b = c.getBoundingClientRect();
          const ev = (t,x,y) => c.dispatchEvent(new MouseEvent(t, {bubbles:true, clientX:x, clientY:y}));
          ev('mousedown', b.right-6, b.y+b.height/2); ev('mouseup', b.right-6, b.y+b.height/2); ev('click', b.right-6, b.y+b.height/2);
        }''', drop[0])
        page.wait_for_timeout(500)

    tag_input = page.locator('input[placeholder*="回车键Enter创建标签"], input[placeholder*="创建标签"]').first
    for t in TAGS:
        if t in chips(): continue
        for v in [t, t.lower(), t.upper()]:
            tag_input.click()
            tag_input.fill(v)
            page.keyboard.press('Enter')
            page.wait_for_timeout(600)
            if any(c.lower() == t.lower() for c in chips()):
                break
    log('chips now:', chips())

    # ---- 7. 简介 ----
    page.evaluate('''(desc) => {
      const ed = document.querySelector('.ql-editor');
      if (!ed) return 'no editor';
      ed.innerHTML = desc.split('\\n').filter(Boolean).map(l => '<p>'+l+'</p>').join('');
      ed.dispatchEvent(new Event('input', {bubbles: true}));
      return 'ok';
    }''', DESC)
    page.wait_for_timeout(400)
    log('desc injected')

    # ---- 8. 合集（虢礫緙嘞）----
    try:
        col_btn = page.locator('text=请选择合集')
        if col_btn.count() > 0:
            col_btn.first.click(timeout=5000)
            page.wait_for_timeout(2600)
            clicked = page.evaluate('''(name) => {
              for (const opt of document.querySelectorAll('li, div, span, p')) {
                const t = opt.textContent.trim();
                if ((t === name || t.includes(name)) && opt.offsetParent && opt.children.length === 0) {
                  opt.click(); return t;
                }
              }
              return false;
            }''', COLLECTION)
            page.wait_for_timeout(800)
            log('collection clicked:', clicked)
    except Exception as e:
        log('collection skip:', str(e)[:80])

    # ---- 9. 存草稿 ----
    page.locator('span.submit-draft').first.click(force=True)
    page.wait_for_timeout(5000)
    url_now = page.url
    log('after save url:', url_now[:100])

    # 验证草稿箱
    vpage = ctx.new_page()
    vpage.goto('https://member.bilibili.com/platform/upload-manager/article?group=draft', wait_until='domcontentloaded', timeout=45000)
    vpage.wait_for_timeout(6000)
    vtext = vpage.evaluate('() => document.body.innerText') or ''
    title_ok = 'SI搞砸了一切' in vtext or 'OnLeave' in vtext or BILI_TITLE[:10] in vtext
    vpage.close()
    page.close()

    log('draft box title found:', title_ok)
    print('BILI_RESULT:', json.dumps({'saved_url': 'draft' in url_now, 'title_in_draftbox': title_ok}, ensure_ascii=False))
