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

# 🔒 上传浏览器铁律（2026-11-12 用户明确指示）：
#   五平台登录态长期驻留在**专用 profile** `ms-playwright-mcp/mcp-chrome-10b76e5`。
#   以后每次上传都用它；**禁止**改用日常 Chrome 的 profile ——
#   Chrome 157+ 对默认 data dir 直接拒绝开调试端口（坑 461），符号链接也绕不过。
DEDICATED = os.path.expanduser("~/Library/Caches/ms-playwright-mcp/mcp-chrome-10b76e5")
PROFILE = os.environ.get("UPLOAD_PROFILE") or DEDICATED
if not os.path.isdir(PROFILE):
    cand = sorted(glob.glob(os.path.expanduser("~/Library/Caches/ms-playwright*/mcp-chrome-*")))
    if not cand:
        raise SystemExit("no mcp-chrome profile found")
    PROFILE = cand[0]

DAILY_PROFILES = (
    os.path.expanduser("~/Library/Application Support/Google/Chrome"),
    os.path.expanduser("~/Library/Application Support/Chromium"),
)
for _bad in DAILY_PROFILES:
    if os.path.realpath(PROFILE) == os.path.realpath(_bad):
        raise SystemExit(
            f"REFUSE: 禁止用日常浏览器 profile 跑自动化（Chrome 157+ 会拒绝调试端口，"
            f"且会污染用户日常登录态）: {PROFILE}")

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
