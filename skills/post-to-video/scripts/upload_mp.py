#!/usr/bin/env python3
"""微信公众号草稿上传（post-to-video 通用版，2026-11-05 实战沉淀）

只存草稿，绝不点发表。读取 {slug}/publish.json 的 platform.wechat 段：

  "wechat": {
    "title": "公众号标题",
    "article": "wechat-article-YYYYMMDD.md",     # 正文 Markdown（H1=标题，## =小节）
    "images": "images/scene*-3x4.png",           # glob，按小节顺序插入
    "cover": "covers/vertical-3-4.png",          # 竖封面，正文末尾作为候选封面图
    "group": "「虢礫緙嘞」"                        # 合集名，可带「」
  }

2026-11-05 踩过的三个致命坑（本脚本已内置规避，改动前先读）：
  坑 A：`set_input_files` 之后**按 Escape** → ProseMirror 取消插入，图片全部不落，
        占位符原样留在正文（日志却打印 done，属于假绿）。
  坑 B：点「保存为草稿」后**在同一标签页 goto 列表页** → 掐断在途 AJAX，草稿退回旧版本。
  坑 C：合集弹窗填完搜索框不点 `li.select-opt-li` → 永远「未添加」。

用法：
  python3 upload_mp.py --dir <slug_dir> [--draft-only]

退出码 0 表示草稿保存成功且回读图片数 == 期望数。
"""
import argparse
import glob
import json
import os
import re
import sys
import time

from playwright.sync_api import sync_playwright

CDP = 'http://localhost:9222'


def log(*a):
    print('[mp]', *a, flush=True)


# ---------- markdown → 微信 HTML（每小节后插一个图片占位符） ----------

def md_to_blocks(md_text):
    out = []
    for raw in md_text.split('\n'):
        line = raw.rstrip()
        if line.startswith('## '):
            out.append(('h2', line[3:].strip()))
        elif line.startswith('# '):
            continue                      # H1 就是标题，不进正文
        elif re.match(r'^[-*] ', line.strip()):
            out.append(('li', line.strip()[2:].strip()))
        elif line.strip() in ('---', ''):
            continue
        else:
            out.append(('p', line.strip()))
    return out


def build_html(md_text, n_images):
    """把 Markdown 转成微信 HTML，并把 n_images 个占位符**均匀**分配到各小节末尾。

    坑：一节配一张图是错的——今天正文只有 4 个 `##`，却有 15 张场景图。
    按「一节一张」写，`zip(keys, imgs)` 会静默截断，11 张图被丢掉而脚本照样报成功。
    所以张数由调用方（图片文件数）决定，按小节均摊，余数分给前几节。

    返回 (html, [(占位符 key, 期望小节标题), ...])
    """
    blocks = md_to_blocks(md_text)
    sections = []                          # [{heading, blocks: []}]
    preface = []
    for kind, text in blocks:
        if kind == 'h2':
            sections.append({'heading': text, 'blocks': []})
        elif sections:
            sections[-1]['blocks'].append((kind, text))
        else:
            preface.append((kind, text))

    S = max(len(sections), 1)
    base, rem = divmod(n_images, S)
    plan = [base + (1 if i < rem else 0) for i in range(S)]

    parts = []
    for kind, text in preface:
        parts.append(f'<p>{text}</p>' if kind != 'li' else f'<p>• {text}</p>')

    idx = 0
    mapping = []
    for i, sec in enumerate(sections):
        parts.append(f"<h2>{sec['heading']}</h2>")
        for kind, text in sec['blocks']:
            parts.append(f'<p>{text}</p>' if kind != 'li' else f'<p>• {text}</p>')
        for _ in range(plan[i]):
            idx += 1
            parts.append(f'<p>PLACEHOLDER_IMG_{idx}</p>')
            mapping.append((f'PLACEHOLDER_IMG_{idx}', sec['heading']))

    if not sections and n_images:          # 无小节：全部堆到文末
        for _ in range(n_images):
            idx += 1
            parts.append(f'<p>PLACEHOLDER_IMG_{idx}</p>')
            mapping.append((f'PLACEHOLDER_IMG_{idx}', ''))

    parts.append('<p>PLACEHOLDER_IMG_COVER</p>')
    mapping.append(('PLACEHOLDER_IMG_COVER', '（文末）'))
    return ''.join(parts), mapping


# ---------- 编辑器 DOM 工具 ----------

PM_HELPERS = '''
window.__ptv = {
  pm() {
    // 正文 PM 通常是最后一个 .ProseMirror；用「文本最长」兜底，禁止硬编码 [1]
    const pms = [...document.querySelectorAll('.ProseMirror')];
    if (!pms.length) return null;
    return pms.reduce((a, b) =>
      (b.innerText || '').length > (a.innerText || '').length ? b : a);
  },
  text() { const pm = window.__ptv.pm(); return pm ? (pm.innerText || '') : ''; },
  has(key) { return window.__ptv.text().includes(key); },
  placeholders() { return (window.__ptv.text().match(/PLACEHOLDER_IMG_[A-Z0-9_]+/g) || []); },
  imgCount() { const pm = window.__ptv.pm(); return pm ? pm.querySelectorAll('img').length : -1; },
  selectPlaceholder(key) {
    const pm = window.__ptv.pm();
    if (!pm) return 'no-pm';
    const walk = (n) => {
      if (n.nodeType === 3 && n.textContent.includes(key)) return n;
      if (n.nodeType !== 1) return null;
      for (const c of n.childNodes) { const h = walk(c); if (h) return h; }
      return null;
    };
    const tn = walk(pm);
    if (!tn) return 'not-found';
    const rg = document.createRange();
    rg.selectNodeContents(tn);
    const s = window.getSelection();
    s.removeAllRanges();
    s.addRange(rg);
    return 'selected';
  },
};
'''


def install_helpers(pg):
    pg.evaluate(PM_HELPERS)


def dom_set_title(pg, title):
    """坑 372：PM 页面 #title 不接 .click()，用 value setter + input/change 事件。"""
    pg.evaluate('''() => {
      const t = document.querySelector('#title');
      if (t) { t.scrollIntoView({block:'center'}); t.focus(); }
    }''')
    pg.wait_for_timeout(300)
    pg.evaluate('''(t) => {
      const el = document.querySelector('#title');
      if (!el) return;
      el.focus();
      el.value = t;
      el.dispatchEvent(new Event('input', {bubbles: true}));
      el.dispatchEvent(new Event('change', {bubbles: true}));
      el.blur();
    }''', title)
    pg.wait_for_timeout(800)


def get_title(pg):
    return pg.evaluate('() => { const t = document.querySelector("#title"); return t ? t.value : null; }')


def click_toolbar_image(pg):
    """顶部工具栏「图片」（rect.y < 90）。"""
    r = pg.evaluate('''() => {
      for (const it of document.querySelectorAll('li, a, span')) {
        if ((it.textContent || '').trim() === '图片' && it.offsetParent) {
          const r = it.getBoundingClientRect();
          if (r.y < 90 && r.y >= 0) { it.click(); return 'ok'; }
        }
      }
      return 'not-found';
    }''')
    pg.wait_for_timeout(700)
    return r


def click_local_upload(pg):
    r = pg.evaluate('''() => {
      for (const el of document.querySelectorAll('li, div, span, a')) {
        if ((el.innerText || '').trim() === '本地上传' && el.offsetParent) {
          el.click(); return 'ok';
        }
      }
      return 'not-found';
    }''')
    pg.wait_for_timeout(700)
    return r


def click_save(pg, wait=3500):
    r = pg.evaluate('''() => {
      for (const b of document.querySelectorAll('button, a')) {
        if (/^(Save as draft|保存为草稿)$/i.test((b.textContent || '').trim()) && b.offsetParent) {
          b.click(); return 'clicked';
        }
      }
      return 'not-found';
    }''')
    pg.wait_for_timeout(wait)
    return r


def save_state(pg):
    return pg.evaluate('''() => {
      const hits = [];
      for (const e of document.querySelectorAll('*')) {
        if (e.children.length) continue;
        const t = (e.innerText || '').trim();
        if (/^(已保存|手动保存|保存中|自动保存)$/.test(t)) hits.push(t);
      }
      return hits;
    }''')


def replace_one_image(pg, key, img_path, logfn):
    """把 key 占位符替换成本地图片。返回 True/False。

    **绝不按 Escape**（坑 A）。每张都要等占位符真的消失才算成功。
    """
    sel = pg.evaluate('(key) => window.__ptv.selectPlaceholder(key)', key)
    if sel == 'not-found':
        return True                        # 已替换或本来就没有
    assert sel == 'selected', f'{key}: {sel}'
    pg.wait_for_timeout(300)

    assert click_toolbar_image(pg) == 'ok', f'{key}: 工具栏「图片」没找到'
    assert click_local_upload(pg) == 'ok', f'{key}: 「本地上传」没找到'

    inp = pg.locator('input[type="file"][accept*="image"]').first
    inp.set_input_files(img_path)

    for _ in range(25):
        pg.wait_for_timeout(1000)
        if not pg.evaluate('(key) => window.__ptv.has(key)', key):
            logfn(f'{key} -> {os.path.basename(img_path)} OK')
            return True
    logfn(f'{key} 替换超时（图片未落进正文）')
    return False


def set_group(pg, group, logfn):
    """坑 C：必须点 li.select-opt-li，只填输入框不算选中。"""
    cur = pg.evaluate('''() => {
      const e = document.querySelector('.js_article_tags_content');
      return e ? e.innerText.trim() : '';
    }''')
    if group and group in cur:
        logfn('collection already set:', cur)
        return cur

    pg.locator('.js_article_tags_label').first.click()
    pg.wait_for_timeout(1500)
    inp = pg.locator('input[placeholder="请选择合集"]').first
    inp.click()
    pg.wait_for_timeout(400)
    # 用前两字做前缀搜索，避免全名里的生僻字被输入法/组件截断
    inp.fill(group[:2] if len(group) >= 2 else group)
    pg.wait_for_timeout(1800)
    pg.locator('li.select-opt-li').first.click()
    pg.wait_for_timeout(900)
    pg.evaluate('''() => {
      const dlgs = [...document.querySelectorAll('.weui-desktop-dialog')].filter(d => d.offsetParent);
      const dlg = dlgs[0];
      if (!dlg) return;
      for (const b of dlg.querySelectorAll('button')) {
        if (/^(确定|确认)$/.test((b.innerText || '').trim()) && b.className.includes('primary')) {
          b.click(); return;
        }
      }
    }''')
    pg.wait_for_timeout(1200)
    now = pg.evaluate('''() => {
      const e = document.querySelector('.js_article_tags_content');
      return e ? e.innerText.trim() : '';
    }''')
    logfn('collection now:', now)
    return now


def set_cover_from_content(pg, logfn):
    """封面：从正文选最后一张（正文末尾放的就是竖版封面）。"""
    pg.evaluate('''() => {
      const a = document.querySelector('#js_cover_area .js_cover_btn_area');
      if (a) a.scrollIntoView({block:'center'});
    }''')
    pg.wait_for_timeout(500)
    try:
        pg.locator('#js_cover_area .js_cover_btn_area').first.hover(force=True)
    except Exception:
        pass
    pg.wait_for_timeout(600)
    pg.evaluate('''() => {
      const b = document.querySelector('.js_selectCoverFromContent');
      if (b) {
        b.style.cssText = 'display:block!important;visibility:visible!important;opacity:1!important;pointer-events:auto!important;';
        b.click();
      }
    }''')
    pg.wait_for_timeout(1800)
    pg.evaluate('''() => {
      const items = [...document.querySelectorAll('.appmsg_content_img_item')];
      if (items.length) items[items.length - 1].click();
    }''')
    pg.wait_for_timeout(700)
    pg.evaluate('''() => {
      for (const b of document.querySelectorAll('button')) {
        if ((b.textContent || '').trim() === '下一步' && b.className.includes('primary') && b.offsetParent) {
          b.click(); return;
        }
      }
    }''')
    pg.wait_for_timeout(1800)
    pg.evaluate('''() => {
      for (const b of document.querySelectorAll('button')) {
        if (/^(确认|Confirm)$/i.test((b.textContent || '').trim())
            && b.className.includes('weui-desktop-btn_primary')
            && !b.className.includes('disabled') && !b.disabled) { b.click(); return; }
      }
    }''')
    pg.wait_for_timeout(1500)
    logfn('cover set from content')


def open_draft_editor(ctx):
    """从公众号首页新建一条草稿，返回编辑页 Page。"""
    home = None
    for pg in ctx.pages:
        if 'mp.weixin.qq.com' in (pg.url or ''):
            home = pg
            break
    if home is None:
        home = ctx.new_page()
        home.goto('https://mp.weixin.qq.com/', wait_until='domcontentloaded', timeout=45000)
        home.wait_for_timeout(4000)

    home.bring_to_front()
    home.evaluate('''() => { const m = document.querySelector('.new-creation__menu-item'); if (m) m.click(); }''')
    for _ in range(20):
        home.wait_for_timeout(1500)
        for pg in ctx.pages:
            u = pg.url or ''
            if 'appmsg' in u and ('action=edit' in u or 'appmsg_edit' in u):
                return pg
    raise RuntimeError('没能打开公众号新建草稿页（登录态失效？）')


def verify_by_preview(ctx, title, expect_imgs, logfn):
    """坑 B：验证必须在**新标签页**做，禁止在编辑页 goto。

    首页必须带 token，否则会跳登录页 → 误判「草稿没保存」。
    token 从任一 mp 标签的 URL 里取。
    """
    token = None
    for pg in ctx.pages:
        m = re.search(r'token=(\d+)', pg.url or '')
        if m:
            token = m.group(1)
            break
    assert token, '拿不到公众号 token（登录态失效？）'

    page = ctx.new_page()
    try:
        page.goto(f'https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token={token}',
                  wait_until='domcontentloaded', timeout=45000)
        page.wait_for_timeout(4000)
        t = page.evaluate('() => document.body.innerText') or ''
        has_title = title in t
        logfn('draft in 近期草稿:', has_title)
        return has_title
    finally:
        page.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True, help='slug 目录（含 publish.json）')
    args = ap.parse_args()

    slug = os.path.abspath(args.dir)
    pub = json.load(open(f'{slug}/publish.json', encoding='utf-8'))
    W = pub.get('platform', {}).get('wechat', {})
    title = W.get('title') or pub.get('title')
    group = (W.get('group') or '').strip('「」')
    article = W.get('article')
    assert article, 'publish.json 缺 platform.wechat.article'

    md_text = open(f'{slug}/{article}', encoding='utf-8').read()

    imgs = sorted(glob.glob(f'{slug}/{W.get("images", "images/scene*-3x4.png")}'),
                  key=lambda p: int(re.search(r'(\d+)', os.path.basename(p)).group(1))
                  if re.search(r'(\d+)', os.path.basename(p)) else 0)
    cover = os.path.join(slug, W.get('cover', 'covers/vertical-3-4.png'))
    assert os.path.exists(cover), f'封面不存在: {cover}'
    assert imgs, f'没有匹配到配图: {slug}/{W.get("images")}'

    body_html, mapping = build_html(md_text, len(imgs))
    # mapping 恒为 len(imgs)+1 个（末尾是 COVER）；imgs 也补上 cover，两者必须等长
    assert len(mapping) == len(imgs) + 1, f'占位符 {len(mapping)} != 图片 {len(imgs)}+1'
    imgs = imgs + [cover]

    log(f'title={title!r} images={len(imgs)} group={group!r}')
    for k, h in mapping:
        log(f'  {k} → 小节「{h}」')

    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(CDP, timeout=45000)
        ctx = b.contexts[0]

        # 复用已有编辑页：标题相等 **且** 正文签名对得上，才认是本条草稿（坑 379 同族）
        # 只判标题不够——同名不同稿会把别人的正文当成本期的继续改。
        sig = re.sub(r'\s+', '', md_text)[:40]
        ed = None
        for pg in ctx.pages:
            if 'appmsg_edit' in (pg.url or '') and 'action=edit' in pg.url:
                install_helpers(pg)
                cur_title = get_title(pg)
                cur_text = re.sub(r'\s+', '', pg.evaluate('() => window.__ptv.text()') or '')
                fresh = (cur_title in (None, '')) and len(cur_text) < 50
                ours = (cur_title == title) and (len(cur_text) == 0 or cur_text[:40] == sig
                                                 or cur_text.startswith(sig[:20]))
                if fresh or ours:
                    ed = pg
                    log(f'复用编辑页（{"空白新建" if fresh else "标题+正文签名一致"}）')
                else:
                    log(f'关掉串期编辑页 title={cur_title!r} bodyHead={cur_text[:20]!r}')
                    pg.close()
        if ed is None:
            ed = open_draft_editor(ctx)
            install_helpers(ed)
        ed.bring_to_front()
        ed.wait_for_timeout(1500)
        install_helpers(ed)

        # 1) 标题
        if get_title(ed) != title:
            dom_set_title(ed, title)
        log('title now:', get_title(ed))
        assert get_title(ed) == title, f'标题写不进去: {get_title(ed)!r}'

        # 2) 正文
        if len(ed.evaluate('() => window.__ptv.text()')) < 200:
            ed.evaluate('''(html) => {
              const pm = window.__ptv.pm();
              if (!pm) return 'no-pm';
              pm.focus();
              const dt = new DataTransfer();
              dt.setData('text/html', html);
              dt.setData('text/plain', html.replace(/<[^>]+>/g, '\\n'));
              pm.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
              return 'ok';
            }''', body_html)
            ed.wait_for_timeout(4000)
        log('placeholders after body:', len(ed.evaluate('() => window.__ptv.placeholders()')))

        # 3) 逐张图片（禁止 Escape）
        keys = [k for k, _ in mapping]
        for key, img in zip(keys, imgs):
            if not replace_one_image(ed, key, img, log):
                raise RuntimeError(f'图片替换失败: {key}')
            ed.wait_for_timeout(400)
        left = ed.evaluate('() => window.__ptv.placeholders()')
        assert not left, f'占位符未清空: {left}'
        body_imgs = ed.evaluate('() => window.__ptv.imgCount()')
        log('all placeholders cleared, imgs in body =', body_imgs)
        # 回读断言：正文图片数不得少于上传数（PM 可能额外挂 0×0 占位 img，故用 >=）
        assert body_imgs >= len(imgs), f'正文图片数 {body_imgs} < 上传数 {len(imgs)}'

        # 4) 封面
        try:
            set_cover_from_content(ed, log)
        except Exception as e:
            log('cover skip:', str(e)[:90])

        # 5) 合集
        if group:
            try:
                set_group(ed, group, log)
            except Exception as e:
                log('collection skip:', str(e)[:90])

        # 6) 保存（禁止随后在本页 goto）
        click_save(ed, 4000)
        states = save_state(ed)
        log('save state:', states)
        assert any(s in ('已保存', '手动保存') for s in states), f'保存状态不明: {states}'

        # 7) 回读验证（新标签页）
        ok = verify_by_preview(ctx, title, len(imgs), log)
        print('MP_RESULT:', json.dumps({'title_ok': ok, 'images': len(imgs)}, ensure_ascii=False))
        return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
