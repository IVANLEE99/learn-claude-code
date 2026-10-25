#!/usr/bin/env python3
"""公众号草稿箱 + 发表记录只读核查（v3.37.0 坑 212/213/214）。

用途：Phase 12 验收，或用户手动发表后回查。
铁律：不新建文章、不点发表、不改稿 —— 只导航 + 截图 + 打印文本。

用法:
    python3 wechat_check_draft.py [YYYY-MM-DD]
    # 省略日期则只打印列表，不做当日判定

前置:
    python3 browser_daemon.py          # 起 CDP 9222
    curl -s http://localhost:9222/json/list          # 空 [] 则：
    curl -s -X PUT "http://localhost:9222/json/new?about:blank"   # 坑 214

产物:
    /tmp/wx_draftbox.png, /tmp/wx_publishlist.png（+ 登录失败时 /tmp/wx_draftbox_login.png）
"""
import json
import re
import sys
from playwright.sync_api import sync_playwright

DATE = sys.argv[1] if len(sys.argv) > 1 else None
KEYWORD = f'【{DATE}】' if DATE else None


def mp_page(browser):
    for p in browser.pages:
        if 'mp.weixin.qq.com' in p.url:
            return p
    return None


def settle(page, tries=20):
    """坑 213：mp 会 302 到带 token 的 home 并销毁 execution context，
    必须轮询重试直到拿到非空 body。"""
    for _ in range(tries):
        try:
            t = page.evaluate('() => document.body.innerText')
            if t and t.strip():
                return t
        except Exception as e:
            print('  eval retry:', str(e)[:50])
        page.wait_for_timeout(2000)
    return ''


def norm(t):
    """坑 305：innerText 按渲染折行输出，卡片标题常被拆成「Kimi\nK3.1」。
    判据和证据必须用同一份归一化文本，否则会出现
    「打印的证据明明命中、结论却是 false」的自相矛盾。"""
    return re.sub(r'\s+', ' ', t or '')


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp('http://localhost:9222')
        ctx = browser.contexts[0]
        page = mp_page(ctx) or ctx.new_page()
        page.bring_to_front()

        page.goto('https://mp.weixin.qq.com/', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(8000)
        home = settle(page)
        print('home URL:', page.url[:160])
        # 坑 195：登录判据 = 「新的创作」/ 英文 UI「New creation」
        if ('新的创作' not in home) and ('New creation' not in home):
            page.screenshot(path='/tmp/wx_draftbox_login.png')
            print('LOGIN REQUIRED — /tmp/wx_draftbox_login.png')
            return

        m = re.search(r'token=(\d+)', page.url)
        if not m:
            print('no token in URL — abort')
            return
        token = m.group(1)
        print('token:', token)

        # --- 草稿箱：只认首页「近期草稿」（坑 221 两次假阴性 / 坑 267 需 reload）---
        # 🔴 禁止再用 appmsg?type=10&action=list_card：它只展示历史图文素材（2018–2020），
        #    不含 type=77 新草稿，空结果永远是假阴性，照它排查会触发重建、产出重复稿。
        htext = home
        if KEYWORD and KEYWORD not in norm(htext):
            page.evaluate('() => location.reload()')     # 坑 267：刚存的草稿需 reload 才见
            page.wait_for_timeout(9000)
            htext = settle(page)
        page.screenshot(path='/tmp/wx_draftbox.png', full_page=True)
        print('[shot] /tmp/wx_draftbox.png  URL:', page.url[:140])
        dtext = norm(htext)
        di = dtext.find('近期草稿')
        print('近期草稿:', dtext[di:di + 200] if di >= 0 else '(未找到「近期草稿」区块)')
        in_draft = bool(KEYWORD and KEYWORD in dtext)

        # --- 发表记录（坑 212：已发表时草稿箱查不到，必须同查这里）---
        page.goto('https://mp.weixin.qq.com/cgi-bin/appmsgpublish'
                  f'?sub=list&begin=0&count=10&token={token}&lang=zh_CN',
                  wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(6000)
        ptext = norm(settle(page))
        page.screenshot(path='/tmp/wx_publishlist.png', full_page=True)
        print('[shot] /tmp/wx_publishlist.png  URL:', page.url[:140])
        in_pub = bool(KEYWORD and KEYWORD in ptext)

        if DATE:
            print('--- 判定 ---')
            print(json.dumps({
                'date': DATE,
                'in_recent_drafts': in_draft,
                'in_publish_record': in_pub,
                'verdict': ('已发表（近期草稿无条目属正常，禁止重建）' if in_pub and not in_draft
                            else '仅草稿' if in_draft and not in_pub
                            else '草稿+已发表' if in_draft and in_pub
                            else '两处均无 — 查 appmsgid 编辑页直达后再定性'),
            }, ensure_ascii=False))
            if not in_draft and not in_pub:
                print('⚠️ 铁律：此结论不等于「草稿丢失」——先按 appmsgid 编辑页直达验证，'
                      '不可重建（撞「appmsgid 出现即禁止重建」）')
        else:
            print('--- 近期草稿 (first 1200) ---')
            print(htext[:1200])

        browser.close()


main()
