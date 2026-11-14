#!/usr/bin/env python3
"""gongyi-checkin — daily check-in runner for public-benefit API stations.

Reads the Chrome bookmark folder `daily-check-in` (id 5923, falls back to name),
opens each station in the logged-in daily Chrome, performs the daily check-in,
and writes a report.

Usage:
  python3 run_checkin.py                 # full run, default bookmark folder
  python3 run_checkin.py --dry-run       # probe only, no clicks
  python3 run_checkin.py --limit 5       # first N stations
  python3 run_checkin.py --url https://x/profile --name X   # single site
  python3 run_checkin.py --report-only   # re-render the last report

Outputs:
  <skill>/data/last-run.json   machine-readable results
  <skill>/data/last-run.md     human-readable report
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chrome_driver import (  # noqa: E402
    ChromeError, activate_tab, classify, click_checkin, close_extra_tabs,
    count_tabs, current_url, get_captcha_image_base64, is_cf_challenge, js,
    js_retry, navigate, new_tab, osa, probe, save_captcha_image,
    solve_react_captcha, tab_count, wait_cf_pass, wait_for,
)

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_DIR, "data")
BOOKMARKS = os.path.expanduser(
    "~/Library/Application Support/Google/Chrome/Default/Bookmarks"
)
DEFAULT_FOLDER_ID = "5923"
# Chrome regenerates the numeric folder id when the folder is moved/recreated.
# The NAME is the stable identifier, so keep it and fall back to it.
FOLDER_NAME = "daily-check-in"

# Stations that are known NOT to be check-in targets even though they live in
# the same bookmark folder (status pages, dashboards without a check-in).
SKIP_URL_FRAGMENTS = [
    "uptime-kuma",  # status monitoring page
]

# Load / settle times (seconds) per station, by page archetype.
LOAD_SECONDS = 8
SETTLE_SECONDS = 3
LOGIN_SETTLE_SECONDS = 6

# Stations whose check-in state is fetched asynchronously AFTER the page body is
# already substantial. settle() returns as soon as the body is big enough, so
# these are still showing "正在读取签到状态" when we probe → false `pending`.
# 2026-11-06 链趣: 6s → pending (wrong, then clicks the wrong nav link);
# 15s → done. Give these extra wall-clock after open_station.
EXTRA_SETTLE_HOSTS = {
    "qulink.cyou": 9,   # 链趣 — 「正在读取签到状态」
}


def extra_settle_for(url):
    host = (urlparse(url).hostname or "").lower()
    for key, secs in EXTRA_SETTLE_HOSTS.items():
        if key in host:
            return secs
    return 0


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Bookmarks
# ---------------------------------------------------------------------------

def read_bookmarks(folder_id=DEFAULT_FOLDER_ID, path=BOOKMARKS,
                   folder_name=FOLDER_NAME):
    """Return [{'name','url'}] for the given bookmark folder.

    Chrome regenerates a folder's numeric id when the folder is moved/recreated
    (2026-11-11: `daily-check-in` was 6233, after a move it became 5923).
    So fall back to matching by NAME when the id no longer resolves.
    """
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    def find(node):
        if node.get("id") == folder_id:
            return node
        for child in node.get("children", []):
            got = find(child)
            if got:
                return got
        return None

    def find_by_name(node):
        if node.get("type") == "folder" and node.get("name") == folder_name:
            return node
        for child in node.get("children", []):
            got = find_by_name(child)
            if got:
                return got
        return None

    target = None
    for root in data["roots"].values():
        if isinstance(root, dict):
            target = find(root)
            if target:
                break
    if not target:
        for root in data["roots"].values():
            if isinstance(root, dict):
                target = find_by_name(root)
                if target:
                    log("bookmark folder id %s not found — resolved by name %r "
                        "-> id %s" % (folder_id, folder_name,
                                       target.get("id")))
                    break
    if not target:
        raise SystemExit("bookmark folder %s (%s) not found in %s"
                         % (folder_id, folder_name, path))

    out = []
    for child in target.get("children", []):
        if child.get("type") != "url":
            continue
        url = child.get("url", "")
        if any(frag in url for frag in SKIP_URL_FRAGMENTS):
            continue
        out.append({"name": child.get("name", ""), "url": url})
    return out


# ---------------------------------------------------------------------------
# Per-station work
# ---------------------------------------------------------------------------

def settle(tab=1, seconds=LOAD_SECONDS):
    """Wait until the tab stops loading and has real content."""
    time.sleep(2.0)
    deadline = time.time() + seconds
    while time.time() < deadline:
        raw = js(
            "JSON.stringify({ready: document.readyState, len: document.body ? document.body.innerText.length : 0})",
            tab=tab,
        )
        ready, body_len = "", 0
        if raw:
            try:
                d = json.loads(raw)
                ready = d.get("ready", "")
                body_len = int(d.get("len", 0))
            except Exception:  # noqa: BLE001
                pass
        if ready == "complete":
            if body_len > 200:
                return True
            # new-api SPA: readyState complete but React may still mount
            time.sleep(1.5)
            again = js("document.body ? document.body.innerText.length : 0", tab=tab)
            try:
                if int(again) > 200:
                    return True
            except Exception:  # noqa: BLE001
                pass
        time.sleep(1.0)
    return False


def page_identity(tab=1):
    """Return (href, body_len, title) as seen by the PAGE ITSELF.

    Comparing the page's own location.href with the URL we asked for is the
    only reliable way to know the document has actually committed. Reading a
    page that is still the previous station produces perfectly plausible but
    completely wrong rewards/balances — the classic silent-stale-read bug.
    """
    raw = js(
        "JSON.stringify({"
        "  href: location.href,"
        "  len: document.body ? document.body.innerText.length : 0,"
        "  title: document.title || ''"
        "})",
        tab=tab,
    )
    if not raw:
        return "", 0, ""
    try:
        data = json.loads(raw)
        return data.get("href", ""), int(data.get("len", 0)), data.get("title", "")
    except Exception:  # noqa: BLE001
        return "", 0, ""


def open_station(url, tab=1, retries=3):
    """Navigate + wait for content, retrying up to `retries` times.

    Returns (final_url, ok). ok=False means the site never produced content —
    the caller reports it as "暂时失联" rather than "签到失败".
    """
    want_host = (urlparse(url).hostname or "").lower()
    for attempt in range(1, retries + 1):
        # Go via about:blank so the target page always performs a FRESH load.
        # Chrome will not re-request the document when the URL is unchanged, and
        # the auto-check-in detection relies on this load's network entries.
        navigate("about:blank", tab=tab)
        time.sleep(0.5)
        navigate(url, tab=tab)
        # Some stations redirect (e.g. /profile -> /dashboard/overview) or bounce
        # through the LinuxDO OAuth callback. Wait until we leave chrome-error://.
        wait_for(
            lambda: current_url(tab) if (
                current_url(tab).startswith("http")
                and "chrome-error" not in current_url(tab)
            ) else "",
            timeout=40, poll=2.0,
        )

        # 🚨 关键：遇到 Cloudflare 人机验证/5秒盾/Turnstile 时，明确等待验证通过！
        cf_passed = wait_cf_pass(tab=tab, timeout=60, poll=2.0, log_fn=log)
        if not cf_passed:
            log("     [CF验证] 超时未能通过 Cloudflare 验证！")

        settle(tab=tab, seconds=LOAD_SECONDS)

        # ---- identity check: is the document the one we asked for? ----
        deadline = time.time() + 15
        committed = False
        while time.time() < deadline:
            href, body_len, _title = page_identity(tab=tab)
            if (href.startswith("http")
                    and "chrome-error" not in href
                    and (want_host in href.lower() or want_host.split(".")[0] in href.lower())
                    and (body_len >= 20 or len(_title) > 0)):
                committed = True
                break
            time.sleep(1.5)

        final = current_url(tab)
        if committed:
            return final, True
        if attempt < retries:
            log("     重试 %d/%d ..." % (attempt + 1, retries))
            time.sleep(2)
    return current_url(tab), False


def linuxdo_login(tab=1):
    """Click the LinuxDO login button if the page shows one.

    Returns one of: 'not_needed' | 'clicked' | 'not_found'.
    """
    # 坑 12：先勾选 User Agreement 等复选框（Pigeonw 等站点不勾选协议时点 OAuth 按钮无反应）
    js_prep = r"""
    (function(){
      var cbs = document.querySelectorAll('input[type="checkbox"]');
      for (var i=0; i<cbs.length; i++){
        if (!cbs[i].checked) {
          try {
            cbs[i].checked = true;
            cbs[i].dispatchEvent(new Event('input', {bubbles: true}));
            cbs[i].dispatchEvent(new Event('change', {bubbles: true}));
          }catch(e){}
        }
      }
    })()
    """
    js(js_prep, tab=tab)

    js_expr = r"""
    (function(){
      function vis(e){
        var r=e.getBoundingClientRect(), s=getComputedStyle(e);
        return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';
      }
      var all=Array.from(document.querySelectorAll('button, a, [role=button], div, span'));
      var cand=all.filter(function(e){
        var tx=(e.textContent||'').trim();
        if(!tx||tx.length>40) return false;
        if(!/linux[\s._-]*do/i.test(tx)) return false;
        if(/已绑定|管理|解除/i.test(tx)) return false;
        if(!vis(e)) return false;
        return true;
      });
      if(!cand.length) return 'NO_LINUXDO_BUTTON';
      // Rank button/a ahead of div/span, then by area
      cand.sort(function(a,b){
        var tagA = a.tagName.toUpperCase(), tagB = b.tagName.toUpperCase();
        var prioA = (tagA === 'BUTTON' || tagA === 'A') ? 0 : 1;
        var prioB = (tagB === 'BUTTON' || tagB === 'A') ? 0 : 1;
        if (prioA !== prioB) return prioA - prioB;
        var ra=a.getBoundingClientRect(), rb=b.getBoundingClientRect();
        return (ra.width*ra.height)-(rb.width*rb.height);
      });
      var e=cand[0];
      var tx=(e.textContent||'').trim();
      e.scrollIntoView({block:'center'});
      e.click();
      return 'CLICKED:'+tx.slice(0,24);
    })()
    """
    res = js_retry(js_expr, tab=tab)
    if not res:
        return "not_found"
    if res.startswith("CLICKED"):
        return "clicked"
    return "not_found"


def handle_linuxdo_oauth_authorize(tab=1, timeout=45):
    """Wait for and click the authorize button on connect.linux.do or linux.do."""
    deadline = time.time() + timeout
    seen_oauth = False
    while time.time() < deadline:
        u = current_url(tab)
        if "connect.linux.do" in u or "linux.do/session" in u:
            seen_oauth = True
        elif seen_oauth and "connect.linux.do" not in u and "linux.do/session" not in u:
            # 已经授权并跳回原站
            return "redirected_away"
        elif "linux.do/login" in u:
            # 用户的 LinuxDO 自身掉登录了
            return "linuxdo_session_logged_out"

        if seen_oauth:
            # 坑 26：授权页本身可能触发 Cloudflare 验证，等待通过后重置 deadline，防止耗尽授权窗口
            is_cf, _ = is_cf_challenge(tab=tab)
            if is_cf:
                passed = wait_cf_pass(tab=tab, timeout=45, poll=1.5, log_fn=log)
                if passed:
                    deadline = time.time() + timeout

            auth_js = r"""
            (function(){
              var b = Array.from(document.querySelectorAll('button, a, input[type=submit]'))
                .filter(function(e){ return /授权|同意|允许|Authorize|Allow|Confirm/i.test((e.textContent||e.value||'').trim()); });
              if (!b.length) return 'NO_AUTH_BUTTON';
              b[0].click();
              return 'AUTH_CLICKED:' + (b[0].textContent||b[0].value||'').trim();
            })()
            """
            res = js(auth_js, tab=tab)
            if res and res.startswith("AUTH_CLICKED"):
                return res
        time.sleep(1.0)
    return "AUTH_TIMEOUT"


def process_station(entry, tab=1, dry_run=False, do_login=True):
    """Check in one station. Returns a result dict."""
    name = entry["name"]
    url = entry["url"]
    result = {
        "name": name,
        "url": url,
        "final_url": "",
        "state": "unknown",
        "reward": None,
        "balance": None,
        "evidence": "",
        "action": "",
        "attempts": None,
        "error": "",
    }

    try:
        final, ok = open_station(url, tab=tab, retries=3)
        result["final_url"] = final
        result["attempts"] = 3 if not ok else None

        if not ok:
            # 3 retries exhausted -> site is temporarily unreachable.
            result["state"] = "unreachable"
            result["evidence"] = "重试 3 次仍无法打开（站点暂时失联）"
            return result

        # Some stations fetch the check-in state asynchronously well after the
        # body looks complete (链趣 shows 「正在读取签到状态」). Probing too early
        # reads a loading placeholder and reports a false `pending`.
        _extra = extra_settle_for(url)
        if _extra:
            time.sleep(_extra)

        page = probe(tab=tab)
        if page.get("error"):
            result["error"] = "probe failed: %s" % page["error"][:120]

        # Guard against a stale document: the probe must be looking at the
        # station we navigated to, not the previous one.
        want_host = (urlparse(url).hostname or "").lower()
        seen_host = (urlparse(page.get("url", "") or "").hostname or "").lower()
        if seen_host and want_host and want_host not in seen_host:
            result["state"] = "unknown"
            result["evidence"] = "页面未提交（读到的是 %s 而非 %s）" % (seen_host, want_host)
            return result
        result["seen_host"] = seen_host

        state = classify(page)
        # SPA (如 CM-API-公益站) 偶发初次 probe 尚未完成 React 挂载，重试一次
        if state["state"] == "unknown" and not page.get("hits") and not page.get("apiHits"):
            time.sleep(3.0)
            page = probe(tab=tab)
            state = classify(page)
        result["state"] = state["state"]
        result["reward"] = state["reward"]
        result["balance"] = state["balance"]
        result["evidence"] = state["evidence"]

        # --- not logged in -> LinuxDO OAuth ---
        if state["state"] == "logged_out":
            result["action"] = "needs_login"
            if do_login and not dry_run:
                log("     [登录] 页面未登录，正在通过 LinuxDO 授权登录...")
                act = linuxdo_login(tab=tab)
                result["evidence"] += " | 登录点击=%s" % act
                if act == "clicked":
                    time.sleep(3)
                    auth_res = handle_linuxdo_oauth_authorize(tab=tab, timeout=45)
                    result["evidence"] += " 授权=%s" % auth_res
                    if auth_res in ("linuxdo_session_logged_out", "AUTH_TIMEOUT"):
                        result["state"] = "logged_out"
                        result["evidence"] += " | LinuxDO授权未完成(%s)" % auth_res
                        log("     🔴 [需登录] LinuxDO 授权未完成: %s" % auth_res)
                    else:
                        # 等待跳回原站（排除 connect.linux.do 以及 linux.do/session 授权中途页面）
                        wait_for(lambda: current_url(tab) if ("connect.linux.do" not in current_url(tab) and "linux.do/session" not in current_url(tab)) else "", timeout=35)
                        time.sleep(2)
                        wait_cf_pass(tab=tab, timeout=45, poll=1.5, log_fn=log)
                        settle(tab=tab, seconds=LOAD_SECONDS)

                        # 检查跳回后的 URL 是否偏离了目标签到页（例如 /sign-in -> /dashboard/overview，但签到页是 /profile）
                        curr_u = current_url(tab)
                        target_path = urlparse(url).path
                        if target_path and target_path not in curr_u and "linux.do" not in curr_u:
                            log("     [OAuth后重定向] 当前在 %s，导航回目标签到页 %s ..." % (curr_u, url))
                            navigate(url, tab=tab)
                            time.sleep(2)
                            wait_cf_pass(tab=tab, timeout=30, poll=1.5, log_fn=log)
                            settle(tab=tab, seconds=LOAD_SECONDS)

                        page2 = probe(tab=tab)
                        state2 = classify(page2)
                        result["state"] = state2["state"]
                        result["reward"] = state2["reward"]
                        result["balance"] = state2["balance"]
                        result["evidence"] += " | 登录后=" + state2["evidence"]
                        result["final_url"] = current_url(tab)

        host = (urlparse(url).hostname or "").lower()

        # 1. 薄荷公益站 (up.x666.me): 点击转盘 -> 等待动画 -> 刷新确认
        if "up.x666.me" in host and result["state"] == "pending" and not dry_run:
            log("     [薄荷转盘] 触发开始转动...")
            click_res = click_checkin(tab=tab)
            result["action"] = "clicked_spin"
            result["evidence"] += " | 点击=%s" % click_res
            # 等待 5 秒转盘动画
            time.sleep(5)
            log("     [薄荷转盘] 动画结束，刷新页面确认签到结果...")
            navigate(url, tab=tab)
            time.sleep(3)
            settle(tab=tab, seconds=LOAD_SECONDS)
            p_spin = probe(tab=tab)
            s_spin = classify(p_spin)
            result["state"] = s_spin["state"]
            result["reward"] = s_spin["reward"] or result["reward"]
            result["balance"] = s_spin["balance"] or result["balance"]
            result["evidence"] += " | 刷新后=" + s_spin["evidence"]
            result["final_url"] = current_url(tab)
            if result["state"] == "done":
                log("     ✅ [明确确认成功] 薄荷公益站签到成功！奖励: %s | 余额: %s" % (result["reward"] or "—", result["balance"] or "—"))

        # 2. 常规 pending 站点的点击与确认闭环 (Verification Loop)
        elif result["state"] == "pending" and not dry_run:
            log("     [签到动作] 点击待签到按钮...")
            clicked = click_checkin(tab=tab)
            result["action"] = "clicked" if clicked.startswith("CLICKED") else "click_failed"
            result["evidence"] += " | 点击=%s" % clicked

            # 🚨 核心要求：明确签到成功才进行下一个！循环验证与确认（支持等待 CF Turnstile 弹窗完成）
            log("     [验证确认] 等待签到结果确认与状态翻转（遇到CF盾/Turnstile持续等待）...")
            verified = False
            for v_round in range(1, 15):  # 最多等 30 秒，给 CF 充分时间
                time.sleep(2.0)
                activate_tab(tab=tab)
                # 辅助尝试点击可能出现的 Turnstile checkbox
                js(r"""
                (function(){
                  var iframes = document.querySelectorAll('iframe[src*="challenges.cloudflare.com"], iframe[src*="turnstile"]');
                  for(var i=0; i<iframes.length; i++){
                    try {
                      var doc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                      var box = doc.querySelector('input[type="checkbox"], .ctp-checkbox-label, #challenge-stage');
                      if(box) box.click();
                    }catch(e){}
                  }
                })()
                """, tab=tab)

                page_v = probe(tab=tab)
                state_v = classify(page_v)

                v_body = page_v.get("body", "")
                v_toasts = page_v.get("toasts", "")
                has_toast_done = bool(re.search(
                    r"Check-?in successful|签到成功|今日已打卡|明日再来|You can only check in once per day|Do not repeat check-in",
                    v_toasts, re.I
                )) or bool(re.search(r"Check-?in successful|签到成功|今日已打卡|明日再来", v_body, re.I))

                # 必须明确翻转为 done/auto，或者命中明确的完成 toast（解决 Aether API 按钮不翻转但弹窗提示 once per day 的问题）
                if state_v["state"] in ("done", "auto") or has_toast_done:
                    result["state"] = "done"
                    # 坑 27：优先从 Toast 回执提取奖励金额（支持 LDC, Payload, 🍥, BTC 等非标币种）
                    toast_rew = None
                    if v_toasts:
                        m_rew = re.search(
                            r"(?:Received|获得|奖励)\s*([+-]?\s*(?:BTC|LDC|Payload|[$¥€￥¤🍥])?\s*\d[\d,]*(?:\.\d+)?\s*(?:BTC|LDC|Payload|[$¥€￥¤🍥元点额度])?)",
                            v_toasts,
                            re.I,
                        )
                        if m_rew:
                            toast_rew = _money(m_rew.group(1))
                    result["reward"] = state_v["reward"] or toast_rew or result["reward"]
                    result["balance"] = state_v["balance"] or result["balance"]
                    result["evidence"] += " | 明确确认成功=" + (state_v["evidence"] if state_v["state"] in ("done", "auto") else ("Toast提示←" + v_toasts[:34]))
                    result["final_url"] = current_url(tab)
                    verified = True
                    log("     ✅ [明确确认成功] 签到已成功完成！奖励: %s | 余额: %s" % (result["reward"] or "—", result["balance"] or "—"))
                    break
                elif state_v["state"] == "blocked_captcha":
                    result["state"] = "blocked_captcha"
                    result["reward"] = state_v["reward"] or result["reward"]
                    result["balance"] = state_v["balance"] or result["balance"]
                    result["evidence"] += " | " + state_v["evidence"]
                    result["final_url"] = current_url(tab)
                    if save_captcha_image(tab=tab):
                        result["evidence"] += " (已提取验证码至 /tmp/gongyi_captcha.png)"
                        log("     📸 [验证码已保存] 验证码已提取并保存至 /tmp/gongyi_captcha.png")
                    verified = True
                    log("     🔒 [需人工验证] %s" % state_v["evidence"])
                    break
                elif v_round == 8 and state_v["state"] == "pending":
                    # 仅在确认无 CF Turnstile 质询或验证码弹窗时才重试点击，避免重置 Turnstile
                    cf_active, _ = is_cf_challenge(tab=tab)
                    has_captcha = bool((page_v.get("captcha") or {}).get("hasModal"))
                    if not cf_active and not has_captcha:
                        log("     [重试] 按钮仍未翻转且无验证弹窗，再次点击...")
                        click_checkin(tab=tab)
                    else:
                        log("     [等待质询] 检测到 CF Turnstile 或验证码进行中，保持等待不重复点击...")

            if not verified:
                page_final = probe(tab=tab)
                state_final = classify(page_final)
                result["state"] = state_final["state"]
                result["reward"] = state_final["reward"] or result["reward"]
                result["balance"] = state_final["balance"] or result["balance"]
                result["evidence"] += " | 最终状态=" + state_final["evidence"]
                result["final_url"] = current_url(tab)

        elif result["state"] == "pending":
            result["action"] = "dry_run_pending"

        elif result["state"] in ("done", "auto"):
            result["action"] = "already_done"
            log("     ✅ [已签到] 该站点今日已签到！奖励: %s | 余额: %s" % (result["reward"] or "—", result["balance"] or "—"))

    except Exception as exc:  # noqa: BLE001
        result["error"] = "%s: %s" % (type(exc).__name__, exc)

    return result


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

STATE_LABEL = {
    "done": "✅ 签到成功",
    "auto": "✅ 签到成功(打开即签到)",
    "pending": "🟡 待签到(未点击)",
    "logged_out": "🔴 需登录",
    "unreachable": "⚫ 暂时失联",
    "blocked_captcha": "🔒 需人工验证",
    "unsupported": "ℹ️ 未启用签到",
    "unknown": "⚠️ 状态未知",
}


def render_report(results, meta):
    lines = []
    lines.append("# 公益站签到报告 — %s" % meta["date"])
    lines.append("")
    lines.append("- 书签文件夹：`daily-check-in` (id %s)，共 %d 个站点"
                 % (meta["folder_id"], meta["total"]))
    lines.append("- 完成时间：%s" % meta["finished_at"])
    lines.append("")

    ok = [r for r in results if r["state"] in ("done", "auto")]
    unsupported = [r for r in results if r["state"] == "unsupported"]
    bad = [r for r in results
           if r["state"] in ("logged_out", "unreachable", "unknown", "blocked_captcha")]
    pending = [r for r in results if r["state"] == "pending"]

    lines.append("## 总览")
    lines.append("")
    lines.append("| 结果 | 数量 |")
    lines.append("| --- | --- |")
    lines.append("| ✅ 签到成功 | %d |" % len(ok))
    lines.append("| 🟡 待签到 | %d |" % len(pending))
    lines.append("| 🔴 需登录 | %d |"
                 % len([r for r in results if r["state"] == "logged_out"]))
    lines.append("| ⚫ 暂时失联(重试3次) | %d |"
                 % len([r for r in results if r["state"] == "unreachable"]))
    lines.append("| 🔒 需人工验证 | %d |"
                 % len([r for r in results if r["state"] == "blocked_captcha"]))
    lines.append("| ℹ️ 未启用签到 | %d |" % len(unsupported))
    lines.append("| ⚠️ 状态未知 | %d |" % len([r for r in results if r["state"] == "unknown"]))
    lines.append("")

    def money(v):
        return v if v else "—"

    total_reward = 0.0
    has_reward = False
    for r in ok:
        if r.get("reward"):
            has_reward = True
            digits = "".join(ch for ch in r["reward"] if ch.isdigit() or ch == ".")
            try:
                total_reward += float(digits)
            except ValueError:
                pass

    if has_reward:
        lines.append("## 签到奖励合计")
        lines.append("")
        lines.append("本次签到获得奖励合计约 **%.4f**（各站币种/单位不同，仅供参考）"
                     % total_reward)
        lines.append("")

    lines.append("## ✅ 签到成功（%d）" % len(ok))
    lines.append("")
    lines.append("| 站点 | 状态 | 奖励 | 余额 | 依据 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for r in ok:
        lines.append("| %s | %s | %s | %s | %s |" % (
            r["name"], STATE_LABEL.get(r["state"], r["state"]),
            money(r.get("reward")), money(r.get("balance")),
            (r.get("evidence") or "").replace("|", "／")[:70],
        ))
    lines.append("")

    if pending:
        lines.append("## 🟡 待签到（%d）" % len(pending))
        lines.append("")
        lines.append("| 站点 | 余额 | 依据 |")
        lines.append("| --- | --- | --- |")
        for r in pending:
            lines.append("| %s | %s | %s |" % (
                r["name"], money(r.get("balance")),
                (r.get("evidence") or "").replace("|", "／")[:70]))
        lines.append("")

    if unsupported:
        lines.append("## ℹ️ 未启用签到模块（%d）" % len(unsupported))
        lines.append("")
        lines.append("| 站点 | 余额 | 详情 |")
        lines.append("| --- | --- | --- |")
        for r in unsupported:
            lines.append("| %s | %s | %s |" % (
                r["name"], money(r.get("balance")),
                (r.get("evidence") or "").replace("|", "／")[:80]))
        lines.append("")

    if bad:
        lines.append("## ❌ 签到失败（%d）" % len(bad))
        lines.append("")
        lines.append("| 站点 | 原因 | 详情 |")
        lines.append("| --- | --- | --- |")
        for r in bad:
            lines.append("| %s | %s | %s |" % (
                r["name"], STATE_LABEL.get(r["state"], r["state"]),
                ((r.get("error") or r.get("evidence") or "")
                 .replace("|", "／")[:80])))
        lines.append("")

    return "\n".join(lines)


def archive_experience(results, meta):
    """Append this run's outcome to the runtime log so the next run inherits it.

    IMPORTANT: this writes to `data/run-log.md`, NOT to the tracked
    `EXPERIENCE.md`. Daily runs contain real account balances and station
    states; those must never land in a file that gets committed to a public
    repo. `EXPERIENCE.md` is for hand-written, sanitized lessons only.

    Only appends sites whose result differs from the previous run's file
    (new site, changed state, or changed reward) — keeps the file useful
    instead of growing a duplicate line every day.
    """
    exp_path = os.path.join(DATA_DIR, "run-log.md")
    os.makedirs(DATA_DIR, exist_ok=True)

    prev = {}
    if os.path.exists(json_path_prev := os.path.join(DATA_DIR, "prev-run.json")):
        try:
            with open(json_path_prev, encoding="utf-8") as fh:
                for row in json.load(fh).get("results", []):
                    prev[row.get("name")] = row
        except Exception:  # noqa: BLE001
            prev = {}

    lines = []
    for r in results:
        old = prev.get(r["name"])
        changed = (
            old is None
            or old.get("state") != r.get("state")
            or old.get("reward") != r.get("reward")
        )
        if not changed:
            continue
        note = "- %s %s — %s" % (
            meta["date"], r["name"],
            {"done": "✅ 签到成功", "auto": "✅ 打开即签到",
             "pending": "🟡 待签到", "logged_out": "🔴 需登录",
             "unreachable": "⚫ 暂时失联", "blocked_captcha": "🔒 需人工验证",
             "unsupported": "ℹ️ 未启用签到", "unknown": "⚠️ 状态未知"}.get(
                r.get("state"), r.get("state")),
        )
        if r.get("reward"):
            note += " 奖励 %s" % r["reward"]
        if r.get("balance"):
            note += " 余额 %s" % r["balance"]
        lines.append(note)

    if not lines:
        return None

    # First run: the log file does not exist yet — start it from scratch.
    content = ""
    if os.path.exists(exp_path):
        with open(exp_path, encoding="utf-8") as fh:
            content = fh.read()
    header = "# 公益站签到 · 运行归档（自动追加，含真实余额，勿入库）\n"
    marker = "## 本次运行归档"
    block = "### %s\n\n%s\n\n" % (meta["date"], "\n".join(lines))
    if marker in content:
        content = content.split(marker)[0].rstrip() + "\n\n" + marker + "\n\n" + block
    else:
        content = header + "\n" + content.rstrip() + "\n\n" + marker + "\n\n" + block
    with open(exp_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return exp_path

def claim_scratch_tab():
    """Open a dedicated scratch tab and return its index.

    The script MUST NOT reuse the user's tab 1 — the daily Chrome usually has
    the user's real work open (linux.do threads, project boards, Feishu).
    Navigating tab 1 away would destroy that state, and closing "extra" tabs
    would close their work too. So: append one scratch tab, use it, and close
    only that one at the end.
    """
    before = count_tabs()
    new_tab("about:blank")
    deadline = time.time() + 15
    while time.time() < deadline:
        after = count_tabs()
        if after > before:
            # the new tab is the last one
            return after
        time.sleep(0.5)
    raise ChromeError("Timed out creating scratch tab (before=%d, after=%d)" % (before, count_tabs()))


def release_scratch_tab(index):
    """Close only our scratch tab (never the user's)."""
    if not index or index <= 1:
        return
    try:
        osa(
            'tell application "Google Chrome"\n'
            "  try\n"
            "    set totalTabs to count of tabs of front window\n"
            "    set tIdx to %d\n"
            "    if tIdx > 1 and tIdx <= totalTabs then close tab tIdx of front window\n"
            "  end try\n"
            "end tell\n" % index,
            timeout=30,
        )
    except Exception:  # noqa: BLE001
        pass


def main():
    ap = argparse.ArgumentParser(description="公益站每日签到")
    ap.add_argument("--dry-run", action="store_true", help="只探测不点击")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 个站点")
    ap.add_argument("--url", default="", help="只处理指定 URL")
    ap.add_argument("--name", default="", help="指定站点名（配合 --url）")
    ap.add_argument("--folder-id", default=DEFAULT_FOLDER_ID)
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--resume", action="store_true", help="从上次中断的断点继续运行（保留已确认为终态的站点）")
    ap.add_argument("--no-login", action="store_true", help="不尝试 LinuxDO 登录")
    ap.add_argument("--keep-tabs", type=int, default=1,
                    help="兼容参数：不再使用（脚本只关自己的临时标签，不动用户标签）")
    args = ap.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    json_path = os.path.join(DATA_DIR, "last-run.json")
    md_path = os.path.join(DATA_DIR, "last-run.md")

    if args.report_only:
        if not os.path.exists(json_path):
            raise SystemExit("no previous run at %s" % json_path)
        with open(json_path, encoding="utf-8") as fh:
            payload = json.load(fh)
        md = render_report(payload["results"], payload["meta"])
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(md)
        return 0

    # 坑 15：Mac 锁屏时不向 GUI 应用投递 AppleEvent，会误报 Chrome 没开
    try:
        import subprocess
        out = subprocess.check_output(
            "ioreg -n Root -d1 -a | grep -A1 CGSSessionScreenIsLocked",
            shell=True, stderr=subprocess.DEVNULL
        ).decode("utf-8", "ignore")
        if "true" in out.lower():
            raise SystemExit("macOS 当前处于锁屏状态（CGSSessionScreenIsLocked=true），系统拒绝投递 AppleEvent。请解锁屏幕后再运行！")
    except subprocess.CalledProcessError:
        pass  # key 不存在即未锁屏

    # sanity: Chrome must be running
    n_tabs = tab_count()
    if n_tabs.startswith("__") or "error" in n_tabs.lower():
        raise SystemExit("cannot talk to Chrome (tabs=%s). Is Chrome running?" % n_tabs)
    log("Chrome tabs=%s" % n_tabs)

    # 坑 17 / 坑 33：多 Chrome 实例启动竞争检测与诊断提示
    try:
        ps_out = subprocess.check_output(
            "ps -Ao pid,command | grep -E 'MacOS/Google Chrome( |$)' | grep -v Helper",
            shell=True, stderr=subprocess.DEVNULL
        ).decode("utf-8", "ignore").strip().splitlines()
        if len(ps_out) > 1:
            log("⚠️ [多实例警告] 检测到 %d 个 Chrome 进程同时运行！" % len(ps_out))
            try:
                win_name = osa('tell application "Google Chrome" to get name of window 1', timeout=5).strip()
                log("   当前 AppleScript 绑定窗口 1: %s" % win_name)
                if any(w in win_name for w in ("微信", "视频号", "抖音", "创作者", "Bilibili", "New Tab", "chrome://")):
                    log("   🚨 警告：当前绑定的疑似为后台流水线 Chrome (mcp-chrome)！")
                    log("   建议先终止 browser_daemon.py 与流水线 Chrome，释放 AppleScript 绑定给用户日常 Chrome。")
            except Exception:
                pass
    except Exception:
        pass

    if args.url:
        stations = [{"name": args.name or urlparse(args.url).hostname, "url": args.url}]
    else:
        stations = read_bookmarks(args.folder_id)
        if args.limit:
            stations = stations[: args.limit]
    log("stations=%d" % len(stations))

    results = []
    if args.resume and os.path.exists(json_path):
        try:
            with open(json_path, encoding="utf-8") as fh:
                prev_data = json.load(fh)
                prev_results = prev_data.get("results", [])
                # 坑 29：断点恢复状态机必须保留所有合法终态（done, auto, unreachable, unsupported）
                while prev_results and prev_results[-1].get("state") not in ("done", "auto", "unreachable", "unsupported"):
                    prev_results.pop()
                if [r.get("url") for r in prev_results] == [e.get("url") for e in stations[:len(prev_results)]]:
                    results = prev_results
                    log("断点恢复：已保留前 %d 站结果，从第 %d 站继续" % (len(results), len(results) + 1))
        except Exception as e:
            log("恢复断点失败，将重新从头开始: %s" % e)
            results = []

    started = datetime.now()
    scratch = claim_scratch_tab()
    log("scratch tab=%d (user tabs untouched)" % scratch)
    try:
        for idx, entry in enumerate(stations[len(results):], start=len(results) + 1):
            log("[%2d/%2d] %s" % (idx, len(stations), entry["name"]))
            res = process_station(entry, tab=scratch, dry_run=args.dry_run,
                                  do_login=not args.no_login)
            results.append(res)
            log("     -> state=%s reward=%s balance=%s | %s"
                % (res["state"], res["reward"], res["balance"],
                   (res.get("evidence") or "")[:100]))
            sys.stdout.flush()
            # 实时保存中间进度
            meta_mid = {
                "date": started.strftime("%Y-%m-%d"),
                "started_at": started.strftime("%Y-%m-%d %H:%M:%S"),
                "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "folder_id": args.folder_id,
                "total": len(stations),
                "processed": len(results),
                "unprocessed": max(0, len(stations) - len(results)),
                "dry_run": args.dry_run,
            }
            with open(json_path, "w", encoding="utf-8") as fh:
                json.dump({"meta": meta_mid, "results": results}, fh, ensure_ascii=False, indent=2)
            with open(md_path, "w", encoding="utf-8") as fh:
                fh.write(render_report(results, meta_mid))
    finally:
        release_scratch_tab(scratch)

    meta = {
        "date": started.strftime("%Y-%m-%d"),
        "started_at": started.strftime("%Y-%m-%d %H:%M:%S"),
        "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "folder_id": args.folder_id,
        "total": len(results),
        "dry_run": args.dry_run,
    }
    payload = {"meta": meta, "results": results}
    # keep the previous run so archive_experience can diff against it
    if os.path.exists(json_path):
        try:
            import shutil
            shutil.copy(json_path, os.path.join(DATA_DIR, "prev-run.json"))
        except Exception:  # noqa: BLE001
            pass
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    md = render_report(results, meta)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(md)

    try:
        exp = archive_experience(results, meta)
        if exp:
            log("archived experience -> %s" % exp)
    except Exception as exc:  # noqa: BLE001
        log("archive_experience failed: %s" % exc)

    log("\n" + md)
    log("\nsaved %s / %s" % (json_path, md_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
