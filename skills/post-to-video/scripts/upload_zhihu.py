#!/usr/bin/env python3
"""Zhihu draft upload for 20261105_si.
Draft ONLY (never touches publish button).
Column: 虢礫緙嘞
Topics: 职场, 人工智能, 职业发展
"""
import json
import os
import re
import sys
import time
from playwright.sync_api import sync_playwright

import argparse as _argparse
_ap = _argparse.ArgumentParser(description='post-to-video 草稿上传')
_ap.add_argument('--dir', required=True, help='slug 目录（含 publish.json）')
ROOT = os.path.abspath(_ap.parse_args().dir)
ARTICLE = os.path.join(ROOT, 'zhihu-article-20261105.md')
COVER = os.path.join(ROOT, 'covers', 'horizontal-4-3.png')
VIDEO = os.path.join(ROOT, 'video', 'post-video-3x4.mp4')
COLUMN_WANT = '虢礫緙嘞'
TOPICS = ['职场', '人工智能', '职业发展']
TOPIC_CHIP_SEL = '.css-1d3pntc'
DECL_WANT = '包含AI辅助创作作者对内容负责'

def md_to_blocks(md):
    out = []
    for raw in md.split('\n'):
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith('## '):
            out.append(('h2', line[3:].strip()))
        elif line.strip() == '---':
            out.append(('hr', ''))
        elif m := re.match(r'^!\[[^\]]*\]\(([^)]+)\)\s*$', line.strip()):
            out.append(('img', m.group(1)))
        elif line.startswith('**') and line.endswith('**'):
            out.append(('b', line.strip('*')))
        else:
            out.append(('p', line.strip()))
    return out

def inline_md(text):
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

def build_html(md_path):
    lines = open(md_path, encoding='utf-8').read().split('\n')
    title = lines[0].strip().lstrip('#').strip()
    body = '\n'.join(lines[1:])
    parts = []
    img_marks = []
    for kind, text in md_to_blocks(body):
        if kind == 'h2':
            parts.append(f'<h2>{inline_md(text)}</h2>')
        elif kind == 'hr':
            continue
        elif kind == 'img':
            img_marks.append(text)
            parts.append('<p>__IMG__</p>')
        elif kind == 'b':
            parts.append(f'<p><strong>{text}</strong></p>')
        else:
            parts.append(f'<p>{inline_md(text)}</p>')
    return title, '\n'.join(parts), img_marks

def paste_html(page, html):
    page.evaluate(
        """(html) => {
          const el = document.querySelector('div.public-DraftEditor-content');
          el.focus();
          const dt = new DataTransfer();
          dt.setData('text/html', html);
          dt.setData('text/plain', html.replace(/<[^>]+>/g, '\\n'));
          el.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
        }""",
        html,
    )

def read_state(page):
    return page.evaluate(
        """() => {
          const body = document.querySelector('div.public-DraftEditor-content');
          const norm = s => (s || '').replace(/[\\s\\u200b]/g, '');
          let decl = null;
          for (const box of document.querySelectorAll('div.css-be2u3')) {
            const lab = box.querySelector('label');
            if (!lab || norm(lab.textContent) !== '创作声明') continue;
            const c = box.querySelector('button[role=combobox]');
            if (c) decl = norm(c.innerText);
          }
          const cards = Array.from(document.querySelectorAll('div.public-DraftEditor-content [data-block="true"]')).map(c => {
            const v = !!c.querySelector('.Editable-video');
            const img = c.querySelector('img');
            const kind = v ? 'VIDEO' : (img ? 'IMG' : 'TXT');
            return kind + '|' + (c.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 40);
          });
          const vids = document.querySelectorAll('div.public-DraftEditor-content .Editable-video').length;
          const vp = document.querySelector('div.public-DraftEditor-content .Editable-video video');
          return {
            bodyLen: body ? (body.innerText || '').length : -1,
            blocks: cards,
            videos: vids,
            videoPlayable: vp ? (vp.src ? 'true' : 'no-src') : 'none',
            decl,
            footer: (document.body.innerText.match(/[^\\n]*(草稿|字数)[^\\n]*/g) || []).slice(0, 5),
          };
        }"""
    )

def main():
    title, html, img_marks = build_html(ARTICLE)
    print(f'[zhihu] title: {title!r}, imgs={len(img_marks)}')

    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp('http://localhost:9222', timeout=45000)
        ctx = b.contexts[0]

        # 打开专栏写文章页
        page = None
        for pg in ctx.pages:
            if 'zhuanlan.zhihu.com/write' in (pg.url or ''):
                page = pg
                break
        if page is None:
            page = ctx.new_page()
            page.goto('https://zhuanlan.zhihu.com/write', wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(6000)
        page.bring_to_front()
        page.keyboard.press('Escape')
        page.wait_for_timeout(600)
        print('[zhihu] editor url:', page.url)

        # 1. 清空旧内容
        page.evaluate("""() => {
          const el = document.querySelector('div.public-DraftEditor-content');
          if (el) {
            el.focus();
            const r = document.createRange();
            r.selectNodeContents(el);
            const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
          }
        }""")
        page.wait_for_timeout(300)
        page.keyboard.press('Backspace')
        page.wait_for_timeout(2000)

        # 2. 标题
        ti = page.locator('textarea[placeholder*="请输入标题"]').first
        ti.fill(title)
        page.wait_for_timeout(1000)
        print('[zhihu] title set')

        # 3. 正文 HTML
        paste_html(page, html)
        page.wait_for_timeout(4000)
        print('[zhihu] body pasted')

        # 4. 视频插入
        assert os.path.exists(VIDEO), f'missing video: {VIDEO}'
        page.evaluate("""() => {
          const el = document.querySelector('div.public-DraftEditor-content');
          el.focus();
          const first = el.querySelector('[data-block="true"]') || el;
          const r = document.createRange(); r.setStart(first, 0); r.collapse(true);
          const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
        }""")
        page.wait_for_timeout(400)
        page.evaluate("""() => {
          for (const e of document.querySelectorAll('button[aria-label="视频"]')) {
            if (e.offsetParent) { e.click(); return true; }
          }
        }""")
        page.wait_for_timeout(1800)
        inp = page.locator('input.VideoUploadButton-fileInput').first
        inp.set_input_files(VIDEO)
        print('[zhihu] video file set, waiting for card...')
        for i in range(40):
            page.wait_for_timeout(5000)
            st = read_state(page)
            if st['videos'] > 0:
                print(f'[zhihu] video card ready after ~{(i+1)*5}s')
                break

        # 5. 图片逐张替换
        done = 0
        for rel in img_marks:
            im_path = os.path.join(ROOT, rel)
            assert os.path.exists(im_path), f'missing image: {im_path}'
            sel = page.evaluate("""() => {
              const body = document.querySelector('div.public-DraftEditor-content');
              const walk = (n) => {
                if (n.nodeType === 3 && n.textContent.includes('__IMG__')) return n;
                if (n.nodeType !== 1) return null;
                for (const c of n.childNodes) { const h = walk(c); if (h) return h; }
                return null;
              };
              const tn = walk(body);
              if (!tn) return 'not-found';
              body.focus();
              const rg = document.createRange();
              rg.selectNodeContents(tn);
              const s = window.getSelection(); s.removeAllRanges(); s.addRange(rg);
              return 'selected';
            }""")
            assert sel == 'selected', f'placeholder not found for {rel}'
            page.keyboard.press('Backspace')
            page.wait_for_timeout(800)
            page.locator('input[type=file][accept*="image/webp"]').first.set_input_files(im_path)
            for _ in range(25):
                page.wait_for_timeout(1500)
                st = page.evaluate("""() => {
                  const body = document.querySelector('div.public-DraftEditor-content');
                  return Array.from(body.querySelectorAll('img')).map(i => i.naturalWidth || 0);
                }""")
                if len(st) > done and all(w > 50 for w in st[:done + 1]):
                    break
            done += 1
            print(f'[zhihu] image {done}/{len(img_marks)}: {os.path.basename(rel)} loaded')

        # 6. 封面
        try:
            for e_text in ['添加封面', '更换封面']:
                hit = page.evaluate("""(t) => {
                  for (const e of document.querySelectorAll('*')) {
                    if (e.children.length) continue;
                    if ((e.innerText || '').trim() === t && e.offsetParent) { e.click(); return true; }
                  }
                  return false;
                }""", e_text)
                if hit: break
            page.wait_for_timeout(2000)
            inp = page.locator('input[type=file][accept=".jpeg, .jpg, .png"]').first
            if inp.count() > 0:
                inp.set_input_files(COVER)
                page.wait_for_timeout(4000)
                print('[zhihu] cover uploaded')
        except Exception as e:
            print('[zhihu] cover error:', str(e))

        # 7. 创作声明
        try:
            page.evaluate("""() => {
              const norm = s => (s || '').replace(/[\\s\\u200b]/g, '');
              for (const box of document.querySelectorAll('div.css-be2u3')) {
                const lab = box.querySelector('label');
                if (!lab || norm(lab.textContent) !== '创作声明') continue;
                const c = box.querySelector('button[role=combobox]');
                if (c) { c.click(); return; }
              }
            }""")
            page.wait_for_timeout(1600)
            page.evaluate("""(want) => {
              const norm = s => (s || '').replace(/[\\s\\u200b]/g, '');
              for (const e of document.querySelectorAll('.Select-option')) {
                if (norm(e.innerText) === norm(want) && e.offsetParent) { e.click(); return true; }
              }
              return false;
            }""", '包含 AI 辅助创作 作者对内容负责')
            page.wait_for_timeout(2000)
            print('[zhihu] declaration set')
        except Exception as e:
            print('[zhihu] declaration error:', str(e))

        # 8. 发布到专栏（虢礫緙嘞）
        try:
            page.evaluate("""() => {
              for (const e of document.querySelectorAll('label,span,div,button')) {
                if (e.children.length) continue;
                if ((e.innerText || '').trim() === '发布设置' && e.offsetParent) { e.click(); return; }
              }
            }""")
            page.wait_for_timeout(2000)
            idx = page.evaluate("""() => {
              const norm = s => (s||'').replace(/[\\s\\u200b]/g,'');
              const all = Array.from(document.querySelectorAll('.RadioButtonSet-label'));
              return all.findIndex(e => norm(e.textContent) === '发布到专栏');
            }""")
            if isinstance(idx, int) and idx >= 0:
                loc = page.locator('.RadioButtonSet-label').nth(idx)
                loc.scroll_into_view_if_needed()
                loc.click(force=True)
                page.wait_for_timeout(2000)
                page.locator('.ColumnSetting-ColumnSelector button[role=combobox]').first.click(force=True)
                page.wait_for_timeout(2000)
                picked = page.evaluate("""(want) => {
                  const norm = s => (s||'').replace(/[\\s\\u200b「」]/g,'');
                  for (const e of document.querySelectorAll('.Select-option')) {
                    if (e.offsetParent && norm(e.innerText).includes(norm(want))) { e.click(); return e.innerText.trim(); }
                  }
                  return null;
                }""", COLUMN_WANT)
                page.wait_for_timeout(2000)
                print('[zhihu] column picked:', picked)
        except Exception as e:
            print('[zhihu] column error:', str(e))

        # 9. 话题
        try:
            got_chips = lambda: page.evaluate("() => [...document.querySelectorAll('%s')].map(e => (e.textContent||'').trim())" % TOPIC_CHIP_SEL)
            for want in TOPICS:
                if want in got_chips(): continue
                btn = page.evaluate("""() => {
                  const bs = [...document.querySelectorAll('button')]
                    .filter(b => (b.innerText || '').trim() === '添加话题' && b.offsetParent);
                  if (!bs.length) return null;
                  bs[0].scrollIntoView({block: 'center'});
                  const r = bs[0].getBoundingClientRect();
                  return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
                }""")
                if not btn: break
                page.mouse.click(btn['x'], btn['y'])
                page.wait_for_timeout(1800)
                inp = page.locator('input[placeholder="搜索话题..."]').first
                if inp.count() > 0:
                    inp.fill(want)
                    page.wait_for_timeout(2500)
                    cand = page.evaluate("""(want) => {
                      const vh = window.innerHeight;
                      for (const el of document.querySelectorAll('button,div,span,a,li')) {
                        if (el.children.length > 1) continue;
                        if ((el.textContent || '').trim() !== want) continue;
                        const r = el.getBoundingClientRect();
                        if (r.top < 0 || r.bottom > vh || r.width < 10) continue;
                        return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
                      }
                      return null;
                    }""", want)
                    if cand:
                        page.mouse.click(cand['x'], cand['y'])
                        page.wait_for_timeout(2000)
            print('[zhihu] topics now:', got_chips())
        except Exception as e:
            print('[zhihu] topics error:', str(e))

        # 10. 等待草稿自动保存
        for _ in range(15):
            page.wait_for_timeout(2000)
            txt = page.evaluate("""() => (document.body.innerText.match(/[^\\n]*草稿[^\\n]*/g)||[]).join(' ')""")
            if '草稿' in txt and '草稿保存中' not in txt:
                print('[zhihu] draft saved status:', txt)
                break

        st = read_state(page)
        print('ZHIHU_RESULT:', json.dumps({
            'bodyLen': st['bodyLen'],
            'videos': st['videos'],
            'imgs': sum(1 for b in st['blocks'] if b.startswith('IMG|')),
            'decl': st['decl'],
            'footer': st['footer']
        }, ensure_ascii=False))
        page.close()

if __name__ == '__main__':
    main()
