#!/usr/bin/env python3
"""Raw CDP helper — bypass playwright.connect_over_cdp when it hangs (v3.65.0 坑 306).

用法：`sys.path.insert(0, '<本目录>'); from cdp_helper import open_tab, Tab, targets, close_tab`

三个必踩细节（都是静默失败）：
  1. `websockets.connect(..., proxy=None)` —— 不带会走环境 SOCKS，报 python-socks 缺失
  2. `Runtime.evaluate` 的表达式必须包进 async IIFE 再 JSON.stringify，否则返回 undefined
     或报 ReferenceError: await is not defined
  3. wujie 长页面会偶发 ConnectionClosedError —— send() 内重连一次

文件上传：input[type=file] 先拿 objectId 再 DOM.setFileInputFiles；
shadowRoot 内的 input 必须 `Array.from(shadowRoot.querySelectorAll(...))` 后按 Runtime.getProperties 取下标。
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

    async def eval(self, expr, timeout=60, await_promise=True):
        """expr 支持两种形式：
          1) 普通表达式，如 "document.title"
          2) 形如 "async () => { ... }" 的异步箭头函数 —— 会自动调用它
        结果统一 JSON 序列化后回传。
        """
        src = expr.strip()
        is_arrow = False
        head, sep, _rest = src.partition('=>')
        if not src.startswith('async') and sep and head.strip().startswith('(') and head.strip().endswith(')'):
            src = 'async ' + src
            is_arrow = True
        elif src.startswith('async') and sep:
            is_arrow = True
        if is_arrow:
            # 坑: 顶层直接写 await 会 ReferenceError，必须包在 async IIFE 里
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
