#!/usr/bin/env python3
"""Raw CDP helper — bypass playwright.connect_over_cdp when it hangs (v3.65.0 坑 306).

用法：`sys.path.insert(0, '<本目录>'); from cdp_helper import open_tab, Tab, targets, close_tab`

三个必踩细节（都是静默失败）：
  1. `websockets.connect(..., proxy=None)` —— 不带会走环境 SOCKS，报 python-socks 缺失
  2. `Runtime.evaluate` 的表达式必须包进 async IIFE 再 JSON.stringify，否则返回 undefined
     或报 ReferenceError: await is not defined
  3. wujie 长页面会偶发 ConnectionClosedError —— send() 内重连一次

文件上传：**首选 `Runtime.evaluate` 求值出 `input[type=file]` 元素（`returnByValue:false`）取 `objectId`
→ `DOM.setFileInputFiles({files, objectId})`**（v3.67.0 坑 319：本机 Chrome 155 上 `DOM.getDocument`
报 -32601 `wasn't found`，pierce 遍历路径已失效）。shadowRoot 内的 input 也能直接 querySelector 取到。

坐标点击：**必须过 `click_safe()`**（v3.67.0 坑 317）——1028 期视频号因「scrollIntoView 与测 rect
在同一次 evaluate 内 + sleep 后点击」用了滚动落定前的旧坐标，落点偏到 16px 外的「发表」按钮，
`视频 187→188`、草稿箱 7→6，内容直接公开且平台无二次确认。点击前一律 `elementFromPoint` 自证。
"""
import json
import time
import urllib.request
import asyncio

import websockets


def http(path, method='GET', timeout=15):
    req = urllib.request.Request(f'http://127.0.0.1:9222{path}', method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
    return json.loads(body) if body else {}


def targets():
    return [t for t in http('/json') if t.get('type') == 'page']


def new_tab(url='about:blank'):
    """Create a new page target via HTTP (no WS needed). Returns target dict."""
    return http(f'/json/new?{url}', method='PUT')


def close_tab(tid):
    try:
        http(f'/json/close/{tid}')
    except Exception as e:
        print('close_tab warn', str(e)[:80])


class Tab:
    """Minimal raw CDP session for one page target."""

    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self._id = 0

    async def __aenter__(self):
        # 坑(1025): CHROME WS 必须绕开环境 SOCKS 代理，否则需 python-socks
        self.ws = await websockets.connect(self.ws_url, max_size=64 * 1024 * 1024,
                                           ping_interval=None, proxy=None)
        return self

    async def __aexit__(self, *a):
        if self.ws:
            await self.ws.close()

    async def send(self, method, params=None, timeout=60):
        self._id += 1
        mid = self._id
        try:
            await self.ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
        except Exception as e:
            # 断线重连一次（wujie 页面偶发断开）
            print(f'[cdp] reconnect after {type(e).__name__}', flush=True)
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = await websockets.connect(self.ws_url, max_size=64 * 1024 * 1024,
                                               ping_interval=None, proxy=None)
            await self.ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            raw = await asyncio.wait_for(self.ws.recv(), timeout=max(1, deadline - time.time()))
            msg = json.loads(raw)
            if msg.get('id') == mid:
                if 'error' in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get('result', {})
        raise TimeoutError(method)

    def _is_arrow_at_top(self, src):
        """判断整个表达式是不是一个**箭头函数本身**（而非「调用了箭头函数的 IIFE」）。

        坑 v3.67.0：旧实现用 `src.partition('=>')` 一刀切，`(() => {...})()` 会在**内层**
        的 `=>` 处切开，head='(()' 恰好「以 ( 开头、以 ) 结尾」→ 被误判成箭头函数 →
        拼出 `async (() => {...})()` → `ReferenceError: async is not defined`。
        正确做法：扫描时跟踪括号/花括号深度与字符串，只在**深度 0** 出现 `=>` 才算箭头函数。
        """
        depth = 0
        i = 0
        n = len(src)
        quote = None
        while i < n:
            c = src[i]
            if quote:
                if c == '\\':
                    i += 2
                    continue
                if c == quote:
                    quote = None
                i += 1
                continue
            if c in '"\'`':
                quote = c
                i += 1
                continue
            if c in '([{':
                depth += 1
            elif c in ')]}':
                depth -= 1
            elif c == '=' and i + 1 < n and src[i + 1] == '>' and depth == 0:
                return True
            i += 1
        return False

    async def eval(self, expr, timeout=60, await_promise=True):
        """expr 支持两种形式：
          1) 普通表达式 / IIFE，如 "document.title" 或 "(() => {...})()"
          2) 形如 "async () => { ... }" 的箭头函数**本身** —— 会自动调用它
        （区分靠「深度 0 处是否有 =>」，见 `_is_arrow_at_top`）
        结果统一 JSON 序列化后回传。
        """
        src = expr.strip()
        if self._is_arrow_at_top(src):
            # 顶层直接写 await 会 ReferenceError，必须包在 async IIFE 里
            call = f'(async () => JSON.stringify(await ({src})()))()'
        else:
            call = f'(async () => JSON.stringify(await (async () => {{ return ({expr}); }})()))()'
        r = await self.send('Runtime.evaluate', {
            'expression': call, 'returnByValue': True, 'awaitPromise': await_promise,
            'userGesture': True,
        }, timeout=timeout)
        if 'exceptionDetails' in r:
            raise RuntimeError(json.dumps(r['exceptionDetails'], ensure_ascii=False)[:400])
        v = r.get('result', {}).get('value')
        if v is None:
            return None
        try:
            return json.loads(v)
        except Exception:
            return v

    async def goto(self, url, wait=3.0, timeout=45):
        await self.send('Page.enable')
        await self.send('Page.navigate', {'url': url}, timeout=timeout)
        # poll readyState
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                st = await self.eval('document.readyState', timeout=10)
                if st in ('interactive', 'complete'):
                    break
            except Exception:
                pass
            await asyncio.sleep(0.4)
        await asyncio.sleep(wait)

    async def js(self, fn_body, timeout=60):
        """Evaluate an async function body string."""
        return await self.eval(f'(async () => {{ {fn_body} }})()', timeout=timeout)

    # ---------- v3.67.0 坑 317/319 新增 ----------

    async def set_files(self, js_expr, files, timeout=30):
        """喂文件给 input[type=file]（含 wujie shadowRoot 内的）。

        js_expr 必须求值为**一个** input 元素，例如：
          "document.querySelector('wujie-app').shadowRoot.querySelector('input[type=file]')"
        坑 319：DOM.getDocument 在本机 Chrome 155 上 -32601，只能走 objectId。
        """
        r = await self.send('Runtime.evaluate', {
            'expression': js_expr, 'returnByValue': False, 'awaitPromise': False,
        })
        if 'exceptionDetails' in r:
            raise RuntimeError(json.dumps(r['exceptionDetails'], ensure_ascii=False)[:300])
        oid = r.get('result', {}).get('objectId')
        if not oid:
            raise RuntimeError(f'set_files: expression returned no object — {js_expr[:100]}')
        await self.send('DOM.enable', timeout=timeout)
        return await self.send('DOM.setFileInputFiles',
                               {'files': list(files), 'objectId': oid}, timeout=timeout)

    async def click_safe(self, js_expr, settle=0.8, timeout=30, allow_danger=False):
        """✅ 唯一允许的坐标点击入口（坑 317）。

        流程：① 滚动 → ② 等落定 → ③ **重新**测量 rect → ④ 穿透 shadowRoot 自证落点 → ⑤ 点击。
        js_expr 必须求值为**目标元素本身**。自证不通过直接抛异常，不重试。

        **危险按钮自动拦截**：目标文案命中 `发表 / 发布 / 立即投稿 / 提交审核 / 发表视频` 时
        无条件抛异常——这是常设约束「各平台一律存草稿，绝不点发布」的代码级闸门。
        `allow_danger=True` 仅供人工排障，流水线脚本里不应出现。
        """
        DANGER_WORDS = ('发表视频', '立即投稿', '提交审核', '发表', '发布')
        # ⓪ 文案闸门（在滚动之前就拦，连测量都不做）
        label = await self.eval(f'(() => {{ const el = {js_expr};'
                                f' return el ? (el.innerText || el.value || "").trim().slice(0, 20) : null; }})()')
        if label and any(w in label for w in DANGER_WORDS) and not allow_danger:
            raise RuntimeError(f'click_safe: 🔴 拒绝点击危险按钮 {label!r} —— '
                               f'常设约束「一律存草稿，绝不点发布」')
        # ① 滚动（单独一次，不与测量同批）
        await self.eval(f'(() => {{ const el = {js_expr}; if (!el) return false;'
                        f' el.scrollIntoView({{block:"center"}}); return true; }})()')
        await asyncio.sleep(settle)
        # ②③ 重新测量 + ④ 自证（同一个原子 evaluate 内完成，杜绝二次漂移）
        #    🔴 坑 321（1028 实测）：`document.elementFromPoint` **不穿 shadowRoot**，
        #    wujie/micro-frontend 里它只会返回宿主 `WUJIE-APP`，`hit === el` 恒假 →
        #    自证对最需要的那些控件全部失效。必须**递归下钻**到最深的 shadow 层。
        probe = await self.eval(f'''(() => {{
            const deepHit = (x, y) => {{
                let el = document.elementFromPoint(x, y);
                let guard = 0;
                while (el && el.shadowRoot && guard++ < 12) {{
                    const inner = el.shadowRoot.elementFromPoint(x, y);
                    if (!inner || inner === el) break;
                    el = inner;
                }}
                return el;
            }};
            const el = {js_expr};
            if (!el) return {{err: "element-gone"}};
            const r = el.getBoundingClientRect();
            if (r.width === 0 || r.height === 0) return {{err: "zero-rect"}};
            const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
            if (x < 0 || y < 0 || x > innerWidth || y > innerHeight)
                return {{err: "out-of-viewport", x, y, w: innerWidth, h: innerHeight}};
            const hit = deepHit(x, y);
            const ok = !!(hit && (hit === el || el.contains(hit) || hit.contains(el)));
            return {{x, y, ok, hit: hit ? (hit.tagName + "." + (hit.className || "").toString().slice(0, 40)
                     + " / " + (hit.innerText || "").trim().slice(0, 20)) : null,
                     want: (el.innerText || "").trim().slice(0, 20)}};
        }})()''', timeout=timeout)
        if not probe or probe.get('err'):
            raise RuntimeError(f'click_safe: 定位失败 {probe}')
        if not probe.get('ok'):
            raise RuntimeError(f'click_safe: 落点自证失败，拒绝点击 '
                               f'want={probe.get("want")!r} hit={probe.get("hit")!r} '
                               f'@({probe.get("x")},{probe.get("y")})')
        # ⑤ 点击
        for typ in ('mouseMoved', 'mousePressed', 'mouseReleased'):
            await self.send('Input.dispatchMouseEvent', {
                'type': typ, 'x': probe['x'], 'y': probe['y'],
                'button': 'none' if typ == 'mouseMoved' else 'left',
                'clickCount': 0 if typ == 'mouseMoved' else 1,
            }, timeout=timeout)
            await asyncio.sleep(0.07)
        return probe


async def open_tab(url='about:blank', wait=3.0):
    """Create target + attach; returns (Tab, target_id)."""
    t = new_tab('about:blank')
    tid = t['id']
    ws_url = t['webSocketDebuggerUrl']
    tab = Tab(ws_url)
    await tab.__aenter__()
    if url != 'about:blank':
        await tab.goto(url, wait=wait)
    return tab, tid


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


if __name__ == '__main__':
    async def _demo():
        ts = targets()
        print('pages:', len(ts))
        for t in ts[:10]:
            print(' ', t.get('title', '')[:40], '|', t.get('url', '')[:70])
    asyncio.run(_demo())
