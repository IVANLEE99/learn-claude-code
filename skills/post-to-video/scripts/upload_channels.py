#!/usr/bin/env python3
"""WeChat Channels (视频号) upload for 20261105_si — draft ONLY.
Album: 虢礫緙嘞
AI declaration: Contains AI-generated content
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
CH = pub['platform']['channels']
SHORT_TITLE = CH['title']
DESC = CH['description']
ALBUM = CH.get('album', '虢礫緙嘞')
VIDEO_SRC = os.path.abspath(f"{ROOT}/{pub['video']}")
V_SIMPLE = '/tmp/upload-channels-si.mp4'
COVER_V = os.path.abspath(f'{ROOT}/covers/vertical-3-4.png')

assert len(SHORT_TITLE) <= 16, f'title too long: {SHORT_TITLE}'

def log(*a): print('[ch]', *a, flush=True)

def get_page(ctx):
    def state(pg):
        try:
            return pg.evaluate("""() => {
              const w = document.querySelector('wujie-app');
              let inShadow = 0;
              try { const sr = w && w.shadowRoot; if (sr) inShadow = sr.querySelectorAll('input,button,[contenteditable]').length; } catch(e){}
              return {hasWujie: !!w, inShadow, url: location.href};
            }""")
        except Exception:
            return {'hasWujie': False, 'inShadow': 0, 'url': pg.url}

    cand = None
    for pg in ctx.pages:
        if 'channels.weixin.qq.com' in (pg.url or '') and 'post/create' in pg.url:
            cand = pg; break
    if cand is None:
        for pg in ctx.pages:
            if 'channels.weixin.qq.com' in (pg.url or '') and 'login' not in pg.url:
                cand = pg; break
    if cand is not None:
        st = state(cand)
        log('existing tab:', st['url'][:70], 'inShadow=', st['inShadow'])
        if st['hasWujie'] and st['inShadow'] > 0 and 'post/create' in st['url']:
            return cand
        cand.close()
    page = ctx.new_page()
    page.goto('https://channels.weixin.qq.com/platform/post/create', wait_until='domcontentloaded', timeout=45000)
    page.wait_for_timeout(7000)
    st = state(page)
    log('new tab:', st['url'][:70], 'inShadow=', st['inShadow'])
    assert st['hasWujie'] and st['inShadow'] > 0, f'wujie not mounted {st}'
    return page

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp('http://localhost:9222', timeout=45000)
    ctx = b.contexts[0]
    page = get_page(ctx)
    page.bring_to_front()
    page.wait_for_timeout(1000)

    # ---- 1. 上传视频 ----
    shutil.copy2(VIDEO_SRC, V_SIMPLE)
    log('video ready ->', os.path.getsize(V_SIMPLE), 'bytes')
    inp = page.locator('wujie-app input[type=file]').first
    inp.wait_for(state='attached', timeout=20000)
    inp.set_input_files(V_SIMPLE)
    log('file set, waiting form...')
    ready = False
    for i in range(50):
        page.wait_for_timeout(3000)
        st = page.evaluate("""() => {
          const sr = document.querySelector('wujie-app').shadowRoot;
          const t = sr.body ? sr.body.innerText : '';
          const m = t.match(/(\\d{1,3})%/);
          const vs = sr.querySelectorAll('video');
          let dur = 0;
          for (const v of vs) if (isFinite(v.duration)) dur = Math.max(dur, v.duration);
          return {videos: vs.length, dur: Math.round(dur), pct: m ? m[1] : null,
                  uploading: /上传中|处理中/.test(t)};
        }""")
        if i % 4 == 0:
            log('poll', i, st)
        if st['videos'] >= 1 and st['dur'] > 60 and not st['uploading']:
            ready = True
            break
    assert ready, 'form not ready after upload'
    log('form ready')

    # ---- 2. 描述 & 短标题 ----
    page.evaluate("""() => {
      const sr = document.querySelector('wujie-app').shadowRoot;
      const ed = sr.querySelector('.input-editor');
      ed.dispatchEvent(new MouseEvent('mousedown', {bubbles:true}));
      ed.dispatchEvent(new MouseEvent('click', {bubbles:true}));
      ed.focus();
    }""")
    page.wait_for_timeout(400)
    page.keyboard.type(DESC, delay=4)
    page.wait_for_timeout(800)

    page.evaluate("""() => {
      const sr = document.querySelector('wujie-app').shadowRoot;
      const inp = sr.querySelector('input[placeholder*="短标题"]');
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(inp, '');
      inp.dispatchEvent(new Event('input', {bubbles:true}));
      inp.focus();
    }""")
    page.keyboard.type(SHORT_TITLE, delay=8)
    page.wait_for_timeout(800)
    log('meta set')

    # ---- 3. AI 标注 ----
    try:
        box = page.evaluate("""() => {
          const sr = document.querySelector('wujie-app').shadowRoot;
          const s = sr.querySelector('.mark-tag-select');
          if (!s) return null;
          s.scrollIntoView({block: 'center'});
          const d = s.querySelector('.select-display');
          const r = d.getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
        }""")
        if box:
            page.mouse.click(box['x'], box['y'])
            page.wait_for_timeout(1400)
            opts = page.evaluate("""() => {
              const sr = document.querySelector('wujie-app').shadowRoot;
              return Array.from(sr.querySelectorAll('.mark-tag-option .option-main'))
                .filter(e => e.offsetParent)
                .map(e => {
                  const r = e.getBoundingClientRect();
                  return {t: (e.innerText||'').trim(),
                          x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
                });
            }""")
            target = next((o for o in opts if 'AI-generated' in o['t']), None)
            if target:
                page.mouse.click(target['x'], target['y'])
                page.wait_for_timeout(1200)
                log('AI label set')
    except Exception as e:
        log('AI label skip:', str(e)[:70])

    # ---- 4. 竖封面 ----
    try:
        page.evaluate("""() => {
          const sr = document.querySelector('wujie-app').shadowRoot;
          const wrap = sr.querySelector('.vertical-img-wrap');
          if (!wrap) return;
          const btn = wrap.querySelector('.edit-btn') || wrap.querySelector('[class*="edit"]') || wrap;
          const r = btn.getBoundingClientRect();
          btn.dispatchEvent(new MouseEvent('click',{bubbles:true, clientX:r.x+r.width/2, clientY:r.y+r.height/2}));
        }""")
        page.wait_for_timeout(2000)
        finp = page.locator('wujie-app input[type=file][accept*="image"]').first
        if finp.count() > 0:
            finp.set_input_files(COVER_V)
            page.wait_for_timeout(3000)
            btnbox = page.evaluate("""() => {
              const sr = document.querySelector('wujie-app').shadowRoot;
              const cands = Array.from(sr.querySelectorAll('button'))
                .filter(b => b.offsetParent && /^(确认|完成|保存)$/.test((b.innerText||'').trim()));
              if (!cands.length) return null;
              const r = cands[0].getBoundingClientRect();
              return {x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)};
            }""")
            if btnbox:
                page.mouse.click(btnbox['x'], btnbox['y'])
                page.wait_for_timeout(2500)
            log('cover set')
    except Exception as e:
        log('cover skip:', str(e)[:70])

    # ---- 5. 合集（虢礫緙嘞）----
    try:
        page.evaluate("""() => {
          const sr = document.querySelector('wujie-app').shadowRoot;
          const d = sr.querySelector('.post-album-display');
          if (d) d.scrollIntoView({block:'center'});
        }""")
        page.wait_for_timeout(600)
        box = page.evaluate("""() => {
          const sr = document.querySelector('wujie-app').shadowRoot;
          const d = sr.querySelector('.post-album-display');
          if (!d) return null;
          const r = d.getBoundingClientRect();
          return {x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)};
        }""")
        if box:
            page.mouse.click(box['x'], box['y'])
            page.wait_for_timeout(2000)
            opts = page.evaluate("""() => {
              const sr = document.querySelector('wujie-app').shadowRoot;
              return Array.from(sr.querySelectorAll('.post-album-wrap .option-item'))
                .filter(e => e.offsetParent)
                .map(e => { const r = e.getBoundingClientRect();
                            return {t:(e.innerText||'').replace(/\\s+/g,' ').trim(),
                                    x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)}; });
            }""")
            log('album options:', [o['t'] for o in opts])
            target = next((o for o in opts if ALBUM in o['t']), None)
            if target:
                page.mouse.click(target['x'], target['y'])
                page.wait_for_timeout(1500)
                log('album picked:', target['t'])
    except Exception as e:
        log('album skip:', str(e)[:70])

    # ---- 6. 存草稿 ----
    res = page.evaluate("""() => {
      const sr = document.querySelector('wujie-app').shadowRoot;
      const dlg = Array.from(sr.querySelectorAll('*')).find(e => /编辑个人主页卡片/.test(e.textContent||'') && e.offsetParent && (e.className||'').toString().includes('dialog'));
      if (dlg) { const ok = Array.from(sr.querySelectorAll('button')).find(b => /确认/.test(b.textContent||'') && b.offsetParent); if (ok) ok.click(); }
      const btn = Array.from(sr.querySelectorAll('button')).find(b => (b.innerText||'').includes('保存草稿') && b.offsetParent);
      if (!btn) return 'no-btn';
      if (btn.disabled) return 'disabled';
      btn.click();
      return 'clicked';
    }""")
    log('save button click:', res)
    assert res == 'clicked', f'save failed: {res}'
    page.wait_for_timeout(5000)

    # 验证草稿
    page.goto('https://channels.weixin.qq.com/platform/post/draftListManager', wait_until='domcontentloaded', timeout=45000)
    page.wait_for_timeout(7000)
    v = page.evaluate("""() => {
      const w = document.querySelector('wujie-app');
      const t = w && w.shadowRoot && w.shadowRoot.body ? w.shadowRoot.body.innerText : (document.body.innerText||'');
      return {hasTitle: t.includes('三天五个') || t.includes('OnLeave') || t.includes('SI搞砸'), len: t.length};
    }""")
    log('draft list result:', v)
    page.close()
    print('CHANNELS_RESULT:', json.dumps(v, ensure_ascii=False))
