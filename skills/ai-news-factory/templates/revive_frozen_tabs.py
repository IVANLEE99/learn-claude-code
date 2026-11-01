#!/usr/bin/env python3
"""revive_frozen_tabs.py —— playwright connect_over_cdp 挂起时的诊断与修复（坑 373 / v3.77.0）

背景
----
`connect_over_cdp` 卡在 "ws connected" 之后超时，**不是** daemon 抖动。
真根因：浏览器里有 renderer 已冻结的 page target，playwright attach-all 时卡死在上面。
1101 实测：16 个 page 里 8 个 ping 超时；导走后 playwright 秒级恢复。
旧文档「等 40 分钟自愈」在 1101 期等了 6 小时 40 分也没发生。

用法
----
    python3 revive_frozen_tabs.py            # 扫描 + 修复 + 校验
    python3 revive_frozen_tabs.py --scan     # 只扫描，不修复
    python3 revive_frozen_tabs.py --port 9222

退出码
------
    0  修复后 playwright 可连（或本来就没有冻结 target 且可连）
    2  daemon HTTP 端点不通 —— 报告用户，不要自己重开带登录态的窗口
    3  修复后 playwright 仍挂 —— 此时才考虑 raw CDP 兜底

依赖
----
    pip3 install websockets playwright
    注意：本脚本会临时清掉 http_proxy/https_proxy/all_proxy 环境变量，
    否则 websockets / playwright 都会去走系统 SOCKS 代理（报 python-socks is required
    或直接连不上 127.0.0.1 的 CDP 端点）。
"""
import argparse
import asyncio
import json
import os
import sys
import urllib.request

for _k in ('http_proxy', 'https_proxy', 'all_proxy',
           'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY'):
    os.environ.pop(_k, None)

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _http(path):
    port = PORT
    return json.load(_OPENER.open(f'http://127.0.0.1:{port}{path}', timeout=8))


async def _ping(target, timeout=3.0):
    """True = renderer 活着；False = 冻结（ping 超时或连接失败）。"""
    import websockets
    ws_url = (target.get('webSocketDebuggerUrl') or '').replace('localhost', '127.0.0.1')
    if not ws_url:
        return False
    try:
        async with websockets.connect(ws_url, max_size=1024 * 1024,
                                      proxy=None, open_timeout=4) as w:
            await w.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate',
                                     'params': {'expression': '1', 'returnByValue': True}}))
            await asyncio.wait_for(w.recv(), timeout=timeout)
        return True
    except Exception:
        return False


async def _revive(target):
    """browser 进程级导航到 about:blank —— 唤醒 renderer，不关闭标签、不丢数据。

    这是唯一能自动执行的安全修法：Target.closeTarget / page.close() 属破坏性操作，
    会被权限闸门拦下，且可能丢掉用户未保存的内容。
    """
    import websockets
    ws_url = (target.get('webSocketDebuggerUrl') or '').replace('localhost', '127.0.0.1')
    try:
        async with websockets.connect(ws_url, max_size=1024 * 1024,
                                      proxy=None, open_timeout=5) as w:
            await w.send(json.dumps({'id': 1, 'method': 'Page.navigate',
                                     'params': {'url': 'about:blank'}}))
            await asyncio.wait_for(w.recv(), timeout=6)
        return True
    except Exception:
        return False


def playwright_alive(timeout_ms=60000):
    """True=可连(返回 contexts 数) / False=真挂 / None=未装 playwright。

    超时时长必须随 page target 数量放大：playwright 默认 attach-all，
    24 个标签页实测要 15s+，固定 15s 会误报「仍挂」（2026-11-01 实测假阴性）。
    这里用 60s，并把超时单独标出来，方便判断是「慢」还是「死」。
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None                      # 未安装，无法判定
    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f'http://127.0.0.1:{PORT}',
                                            timeout=timeout_ms)
            n = len(b.contexts)
            b.close()
        return n
    except Exception as e:
        if 'Timeout' in type(e).__name__ or 'Timeout' in str(e):
            print(f'  (playwright 超时 {timeout_ms}ms —— 可能只是 attach 太慢，'
                  f'page target 越多越慢；可加大 timeout 复测)')
        else:
            print(f'  (playwright 异常: {type(e).__name__}: {str(e)[:120]})')
        return False


async def main():
    # 1) daemon HTTP 端点
    try:
        t0 = _http('/json/version')
        print(f"daemon OK: {t0.get('Browser')}")
    except Exception as e:
        print(f'FATAL: CDP HTTP 端点不通（{e}）—— 报告用户，不要自己重开带登录态的窗口')
        return 2

    # 2) 冻结扫描
    tabs = [t for t in _http('/json/list') if t.get('type') == 'page']
    alive, dead = [], []
    for t in tabs:
        (alive if await _ping(t) else dead).append(t)
    print(f'pages={len(tabs)} alive={len(alive)} dead={len(dead)}')
    for t in dead:
        print('  DEAD:', (t.get('url') or '')[:80])

    # 3) 修复
    if dead and not args.scan:
        ok = 0
        for t in dead:
            if await _revive(t):
                ok += 1
            print(f"  revived: {'ok ' if ok else 'FAIL'} {(t.get('url') or '')[:70]}")
        print(f'revived {ok}/{len(dead)}')

    # 4) playwright 校验
    #    必须在 asyncio 事件循环之外跑：sync_playwright 在协程里调用会直接抛
    #    "using Playwright Sync API inside the asyncio loop"，被 except 吃掉后
    #    误报「仍挂」（2026-11-01 实测就是这个假阴性，不是超时）。
    if args.scan:
        print('(--scan: 跳过修复与 playwright 校验)')
        return 0
    return await asyncio.get_running_loop().run_in_executor(None, _verify_playwright)


def _verify_playwright():
    n = playwright_alive()
    if n is None:
        print('playwright 未安装，跳过校验')
        return 0
    if n is False:
        print('playwright 仍挂 —— 此时才考虑 raw CDP 兜底（见 SKILL 坑 306）')
        return 3
    print(f'PLAYWRIGHT_OK contexts={n}')
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=int(os.environ.get('CDP_PORT', 9222)))
    ap.add_argument('--scan', action='store_true', help='只扫描，不修复')
    args = ap.parse_args()
    global PORT
    PORT = args.port
    sys.exit(asyncio.run(main()))
