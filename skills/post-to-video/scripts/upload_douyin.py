#!/usr/bin/env python3
"""Douyin end-to-end draft upload for 20261105_si.
Collection: 虢礫緙嘞
Draft ONLY (暂存离开).
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
DY = pub['platform']['douyin']
TITLE30 = DY['title']
DESC = DY['description'].split('\n#')[0]
TAGS = DY['tags']
COLLECTION = DY.get('collection', '虢礫緙嘞')
VIDEO_SRC = os.path.abspath(f"{ROOT}/{pub['video']}")
V_SIMPLE = '/tmp/upload-douyin-si.mp4'
COVER_H = os.path.abspath(f'{ROOT}/covers/horizontal-4-3.png')
COVER_V = os.path.abspath(f'{ROOT}/covers/vertical-3-4.png')

assert len(TITLE30) <= 30, f'title too long: {TITLE30} ({len(TITLE30)})'

def log(*a): print('[dy-e2e]', *a, flush=True)

def state(page):
    return page.evaluate('''() => {
      const t = document.body.innerText || '';
      const ti = document.querySelector('input[placeholder*="作品标题"]');
      const ed = document.querySelector('.editor-kit-editor-container [contenteditable="true"], div[contenteditable="true"]');
      const ci = t.indexOf('设置封面');
      return { url: location.href.slice(-40),
               title: ti ? ti.value : null,
               descLen: ed ? (ed.innerText||'').trim().length : -1,
               tags: ed ? ((ed.innerText||'').match(/#[^\\s#\\u200b]+/g) || []) : [],
               vids: document.querySelectorAll('video').length,
               uploadArea: t.includes('点击上传'),
               hasZancun: !!Array.from(document.querySelectorAll('button')).find(b => (b.textContent||'').trim() === '暂存离开' && b.offsetParent),
               hasResume: t.includes('继续编辑'),
               coverSeg: ci >= 0 ? t.slice(ci, ci + 110).replace(/\\n/g, ' | ') : null,
               missingV: t.includes('竖封面缺失'), missingDual: t.includes('双封面缺失'),
               decl: (t.match(/作者声明[^\\n]*/) || [])[0] || null };
    }''')

def click_text(page, text, exact_leaf=True):
    box = page.evaluate('''([t, leaf]) => { for (const el of document.querySelectorAll('*')) {
      if ((el.textContent||'').trim() === t && el.offsetParent && (!leaf || el.children.length === 0)) {
        const r = el.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) return {x: r.x + r.width/2, y: r.y + r.height/2}; } }
      return null; }''', [text, exact_leaf])
    if box:
        page.mouse.click(box['x'], box['y'])
    return bool(box)

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp('http://localhost:9222', timeout=45000)
    ctx = b.contexts[0]
    page = None
    for q in ctx.pages:
        if 'creator.douyin.com' in (q.url or '') and 'login' not in (q.url or ''):
            page = q
            break
    if page is None:
        page = ctx.new_page()
    page.bring_to_front()
    page.goto('https://creator.douyin.com/creator-micro/content/upload', wait_until='domcontentloaded', timeout=45000)
    page.wait_for_timeout(6000)

    # 清残留草稿（若有横幅则放弃）
    if '继续编辑' in (page.evaluate("() => document.body.innerText") or ''):
        log('discarding stale draft')
        click_text(page, '放弃')
        page.wait_for_timeout(2500)

    # ---- 1. 上传 ----
    shutil.copy2(VIDEO_SRC, V_SIMPLE)
    log('video size', os.path.getsize(V_SIMPLE))
    try:
        with page.expect_file_chooser(timeout=8000) as fc:
            page.locator('text=上传视频').first.click(force=True, timeout=5000)
        fc.value.set_files(V_SIMPLE)
    except Exception as e:
        log('chooser fallback:', str(e)[:60])
        page.locator('input[type=file]').first.set_input_files(V_SIMPLE)
    for _ in range(25):
        page.wait_for_timeout(3000)
        if page.evaluate("() => !!document.querySelector('.editor-kit-editor-container [contenteditable=\"true\"], div[contenteditable=\"true\"]')"):
            break
    page.evaluate('''() => { for (const btn of document.querySelectorAll('button')) {
      if (/我知道了|知道了/.test((btn.textContent||'').trim()) && btn.offsetParent) { btn.click(); return; } } }''')
    page.wait_for_timeout(2000)
    log('uploaded form ready')

    # ---- 2. 标题 / 描述 / 话题 / 声明 ----
    page.get_by_placeholder('填写作品标题，为作品获得更多流量').fill(TITLE30)
    done = False
    for sel in ['.editor-kit-editor-container [contenteditable="true"]', 'div[contenteditable="true"]']:
        try:
            page.locator(sel).first.click(timeout=4000)
            page.keyboard.type(DESC, delay=5)
            done = True
            break
        except Exception:
            continue
    assert done, 'desc typing failed'
    for t in TAGS[:6]:
        try:
            page.locator('text=#添加话题').first.click(force=True, timeout=3000)
            page.wait_for_timeout(300)
            page.keyboard.type(t)
            page.wait_for_timeout(600)
            page.keyboard.press('Enter')
            page.wait_for_timeout(400)
        except Exception:
            pass
    try:
        page.locator('text=请选择自主声明').first.click(force=True, timeout=4000)
        page.wait_for_timeout(800)
        page.locator('label.semi-radio').filter(has_text='内容为个人观点或见解').first.click(timeout=5000)
        page.wait_for_timeout(500)
        page.evaluate('''() => { for (const btn of document.querySelectorAll('button')) {
          if ((btn.textContent||'').trim() === '确定' && btn.offsetParent) { btn.click(); return; } } }''')
        page.wait_for_timeout(600)
    except Exception as e:
        log('declaration skip:', str(e)[:70])
    s = state(page)
    log('meta:', json.dumps({k: s[k] for k in ('title', 'descLen', 'tags', 'decl')}, ensure_ascii=False))

    # ---- 3. 双封面 ----
    def click_done():
        try:
            page.locator('text=完成').last.click(force=True, timeout=3000)
            return 'text'
        except Exception:
            return 'eval' if page.evaluate('''() => { const cs = [];
              for (const el of document.querySelectorAll('button, div, span, a')) {
                if ((el.textContent||'').trim() !== '完成' || !el.offsetParent) continue;
                const r = el.getBoundingClientRect();
                if (r.width > 40 && r.y > 300) cs.push({y: r.y, el}); }
              if (!cs.length) return false;
              cs.sort((a,b) => b.y - a.y); cs[0].el.click(); return true; }''') else 'none'

    page.keyboard.press('Escape'); page.wait_for_timeout(400)
    page.evaluate('''() => { for (const el of document.querySelectorAll('*')) {
      if ((el.textContent||'').trim() === '横封面4:3' && el.offsetParent) {
        let pp = el.parentElement;
        for (let i = 0; i < 6 && pp; i++, pp = pp.parentElement) {
          const sel = Array.from(pp.querySelectorAll('*')).find(n => (n.textContent||'').trim() === '选择封面');
          if (sel) { sel.click(); return; } }
        el.click(); return; } } }''')
    page.wait_for_timeout(1500)
    try:
        with page.expect_file_chooser(timeout=6000) as fc:
            page.locator('text=上传封面').first.click(force=True, timeout=4000)
        fc.value.set_files(COVER_H)
    except Exception:
        page.locator('input[type=file]').last.set_input_files(COVER_H)
    page.wait_for_timeout(3000)
    log('h cover:', click_done())
    page.wait_for_timeout(1500)

    # 竖封面
    vp = page.get_by_role('button', name='设置竖封面')
    vp_ok = False
    if vp.count():
        try:
            vp_ok = vp.first.is_visible() and vp.first.is_enabled()
        except Exception:
            vp_ok = False
    if vp_ok:
        vp.first.click()
    else:
        c = page.locator('.coverControl-CjlzqC').nth(1)
        c.scroll_into_view_if_needed()
        page.wait_for_timeout(700)
        box = c.bounding_box()
        if box and box['width'] > 0:
            cx, cy = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
            page.mouse.move(cx, cy)
            page.wait_for_timeout(1800)
            leaf = page.evaluate("""(slot) => {
              const pad = 6;
              for (const el of document.querySelectorAll('*')) {
                const t = (el.textContent || '').replace(/\\s+/g, '');
                if (t !== '编辑封面') continue;
                const r = el.getBoundingClientRect();
                if (r.width < 15 || r.height < 8) continue;
                const inSlot = r.x >= slot.x - pad && r.y >= slot.y - pad
                            && r.x + r.width <= slot.x + slot.width + pad
                            && r.y + r.height <= slot.y + slot.height + pad;
                if (!inSlot) continue;
                return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
              }
              return null;
            }""", box)
            if leaf:
                page.mouse.click(leaf['x'], leaf['y'])
    page.wait_for_timeout(3000)

    vinp = page.locator('.selectArea-BCIYQD input[type=file]').first
    try:
        vinp.wait_for(state='attached', timeout=12000)
        vinp.set_input_files(COVER_V)
        log('v cover via selectArea input')
    except Exception as e:
        log('selectArea input fallback:', str(e)[:70])
        try:
            with page.expect_file_chooser(timeout=6000) as fc:
                page.locator('text=上传封面').first.click(force=True, timeout=4000)
            fc.value.set_files(COVER_V)
        except Exception:
            page.locator('input[type=file]').first.set_input_files(COVER_V)
    page.wait_for_timeout(4000)

    # 缩放滑块归零
    try:
        sl = page.evaluate("""() => {
          const rail = document.querySelector('.semi-slider-rail');
          const h = document.querySelector('.semi-slider-handle');
          if (!rail || !h) return null;
          const rr = rail.getBoundingClientRect(), hr = h.getBoundingClientRect();
          return {rx: rr.x, ry: rr.y, rw: rr.width, hx: hr.x + hr.width/2, hy: hr.y + hr.height/2};
        }""")
        if sl:
            target_x = sl['rx'] + 2
            page.mouse.move(sl['hx'], sl['hy'])
            page.wait_for_timeout(200)
            page.mouse.down()
            for i in range(1, 13):
                page.mouse.move(sl['hx'] + (target_x - sl['hx']) * i / 12, sl['hy'])
                page.wait_for_timeout(40)
            page.mouse.up()
            page.wait_for_timeout(800)
    except Exception as e:
        log('slider drag skip:', str(e)[:70])

    page.evaluate("""() => {
      const t = [...document.querySelectorAll('button')].filter(e => e.offsetParent)
        .find(b => (b.innerText || '').trim() === '完成');
      if (t) t.click();
    }""")
    page.wait_for_timeout(3500)
    log('v done:', click_done())
    page.wait_for_timeout(2000)

    # ---- 4. 合集（虢礫緙嘞）----
    try:
        page.evaluate('() => window.scrollTo(0, 400)')
        page.evaluate('''() => { for (const el of document.querySelectorAll('*')) {
          if ((el.textContent||'').trim() === '请选择合集' && el.offsetParent) { el.click(); return; } } }''')
        page.wait_for_timeout(1800)
        picked = page.evaluate('''(name) => {
          const cands = [];
          for (const o of document.querySelectorAll('li, div, span, p, [class*=option], [class*=item]')) {
            const t = (o.textContent||'').trim();
            if (!o.offsetParent || !t.includes(name) || t.length > 40) continue;
            const r = o.getBoundingClientRect();
            if (r.height < 10 || r.height > 90) continue;
            cands.push({t, area: r.width * r.height, el: o});
          }
          if (!cands.length) return null;
          cands.sort((a, b) => a.area - b.area);
          cands[0].el.click();
          return cands[0].t.slice(0, 40);
        }''', COLLECTION)
        log('collection:', picked)
        page.wait_for_timeout(1200)
    except Exception as e:
        log('collection skip:', str(e)[:70])

    # ---- 5. 暂存 #1 ----
    page.keyboard.press('Escape'); page.wait_for_timeout(1200)
    has_zancun = page.evaluate('''() => {
      const b = Array.from(document.querySelectorAll('button')).find(x => (x.textContent||'').trim() === '暂存离开' && x.offsetParent);
      if (!b) return false;
      b.click();
      return true;
    }''')
    assert has_zancun, '暂存离开 button missing'
    for _ in range(15):
        page.wait_for_timeout(2000)
        s = state(page)
        if s['hasResume'] and not s['hasZancun']:
            break
    log('after save#1: resume=', s['hasResume'], 'zancun=', s['hasZancun'])

    # ---- 6. 同标签恢复回读 ----
    assert click_text(page, '继续编辑'), 'resume banner not clickable'
    readback = {}
    for _ in range(12):
        page.wait_for_timeout(4000)
        readback = state(page)
        if readback['vids'] > 0 and readback['title']:
            break
    log('readback:', json.dumps({k: readback[k] for k in ('title', 'descLen', 'tags', 'vids', 'decl')}, ensure_ascii=False))

    # ---- 7. 再暂存 ----
    page.wait_for_timeout(1500)
    ok2 = page.evaluate('''() => {
      const b = Array.from(document.querySelectorAll('button')).find(x => (x.textContent||'').trim() === '暂存离开' && x.offsetParent);
      if (!b) return false;
      b.click();
      return true;
    }''')
    log('save#2 clicked:', ok2)
    for _ in range(15):
        page.wait_for_timeout(2000)
        s = state(page)
        if s['hasResume'] and not s['hasZancun']:
            break
    log('after save#2: resume=', s['hasResume'], 'zancun=', s['hasZancun'])
    page.close()
    print('DY_RESULT:', json.dumps({'draft_saved': s['hasResume']}, ensure_ascii=False))
