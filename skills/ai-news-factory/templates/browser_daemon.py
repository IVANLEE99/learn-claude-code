#!/usr/bin/env python3
"""上传自动化浏览器守护进程（v3.34.0 坑 193/198/199）

用法（后台任务运行，全程不退）：
  python3 browser_daemon.py

要点：
- 浏览器本体 = 日常 Google Chrome（/Applications/Google Chrome.app），
  **禁止** Playwright 自带 Google Chrome for Testing（坑 198 / 0917）。
- 裸启 Chrome 进程 + --remote-debugging-port=9222 + mcp-chrome profile。
  **禁止** `with sync_playwright() + launch_persistent_context + while True`
  当 daemon——弹窗协议错误会把 driver 和浏览器一起打死（坑 199 / 0917）。
- 后续脚本 `connect_over_cdp("http://localhost:9222")` 附着，结束只断连。
- 选页按 URL 匹配（member.bilibili.com / cgi-bin/appmsg），禁止 pages[-1]。
"""
import glob
import os
import subprocess
import sys
import time

PROFILE = os.path.expanduser("~/Library/Caches/ms-playwright/mcp-chrome-10b76e5")
if not os.path.isdir(PROFILE):
    cand = sorted(glob.glob(os.path.expanduser("~/Library/Caches/ms-playwright*/mcp-chrome-*")))
    if not cand:
        raise SystemExit("no mcp-chrome profile found")
    PROFILE = cand[0]

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if not os.path.isfile(CHROME):
    raise SystemExit(f"daily Chrome not found: {CHROME}")

lock = os.path.join(PROFILE, "SingletonLock")
if os.path.lexists(lock):
    os.unlink(lock)

cmd = [
    CHROME,
    f"--user-data-dir={PROFILE}",
    "--remote-debugging-port=9222",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-blink-features=AutomationControlled",
    "about:blank",
]
print(f"DAEMON_START chrome={CHROME} profile={PROFILE} port=9222", flush=True)
proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
# 等 CDP 起来
for i in range(20):
    time.sleep(0.5)
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:9222/json/version", timeout=1).read()
        print("DAEMON_READY port=9222", flush=True)
        break
    except Exception:
        if i == 19:
            proc.kill()
            raise SystemExit("CDP 9222 did not come up")
try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()
    sys.exit(0)
