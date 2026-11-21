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
  python3 run_checkin.py --prepare-captcha URL --name X
                                         # open+click, leave verification tab in front
  python3 run_checkin.py --submit-captcha CODE --host HOST
                                         # fill a graphic captcha into that live tab

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
# 空壳页（body 为空、主包还在下载）最长等待秒数，见 probe/classify 后的兜底分支
SHELL_WAIT_SECONDS = 240
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
            # 大体积主包兜底（2026-11-20 新增，ArcaneAI / AzureKilnAPI 形态）：
            # 这两站的 index.*.js 有 4~5MB 且源站限速（curl 实测 ~27KB/s，需数分钟），
            # 8 秒 settle 后页面只剩 "New API" 空壳（bodyLen=0、readyState=interactive、
            # 主包不出现在 resource entries 里），探针读不到任何证据就报 unknown。
            # 此处仅对「空壳页」长轮询等挂载；任何正常站点都走不到这一步，无额外耗时。
            if (state["state"] == "unknown" and not page.get("hits")
                    and not page.get("apiHits") and not (page.get("bodyLen") or 0)):
                deadline = time.time() + SHELL_WAIT_SECONDS
                log("     [空壳等待] body 为空，主包可能仍在下载，最多等 %ds ..."
                    % SHELL_WAIT_SECONDS)
                waited = 0
                while time.time() < deadline:
                    time.sleep(5)
                    waited += 5
                    page = probe(tab=tab)
                    state = classify(page)
                    if (page.get("hits") or page.get("apiHits")
                            or (page.get("bodyLen") or 0)):
                        log("     [空壳等待] 页面已挂载（bodyLen=%s，等待 %ds）"
                            % (page.get("bodyLen"), waited))
                        break
                else:
                    log("     [空壳等待] 超时 %ds 仍未挂载" % SHELL_WAIT_SECONDS)
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
                    else:
                        log("     🔒 [需人工验证] 非图形码验证（滑块/图片点选），需前台人工完成")
                    verified = True
                    log("     🔒 [需人工验证] %s" % state_v["evidence"])
                    break
                elif v_round == 8 and state_v["state"] == "pending":
                    # 仅在确认无 CF Turnstile 质询或验证码弹窗时才重试点击，避免重置 Turnstile
                    cf_active, _ = is_cf_challenge(tab=tab)
                    c_info = page_v.get("captcha") or {}
                    has_captcha = bool(c_info.get("hasModal") or c_info.get("hasSlider")
                                       or c_info.get("hasVerify") or c_info.get("blocking"))
                    if not cf_active and not has_captcha:
                        log("     [重试] 按钮仍未翻转且无验证弹窗，再次点击...")
                        click_checkin(tab=tab)
                    else:
                        log("     [等待质询] 检测到 CF Turnstile 或验证码进行中，保持等待不重复点击...")

            if not verified:
                page_final = probe(tab=tab)
                state_final = classify(page_final)
                c_final = page_final.get("captcha") or {}
                captcha_open = bool(c_final.get("hasModal") or c_final.get("hasSlider")
                                    or c_final.get("hasVerify") or c_final.get("blocking"))
                # 坑 41：点击后 SPA 可能不翻页（iGrok / Pigeonw 2026-11-21 首轮仍 pending/unknown），
                # 重新打开同一 URL 才会显示已签到。无验证弹窗时刷新一次再判，避免漏记成功。
                if (state_final["state"] in ("pending", "unknown") and not captcha_open
                        and clicked.startswith("CLICKED")):
                    log("     [刷新复核] 点击后仍未确认且无验证弹窗，刷新页面再判一次...")
                    navigate(url, tab=tab)
                    time.sleep(2)
                    wait_cf_pass(tab=tab, timeout=20, poll=1.5, log_fn=log)
                    settle(tab=tab, seconds=LOAD_SECONDS)
                    page_final = probe(tab=tab)
                    state_final = classify(page_final)
                    result["evidence"] += " | 刷新复核=" + state_final["evidence"]
                result["state"] = state_final["state"]
                result["reward"] = state_final["reward"] or result["reward"]
                result["balance"] = state_final["balance"] or result["balance"]
                result["evidence"] += " | 最终状态=" + state_final["evidence"]
                result["final_url"] = current_url(tab)
                if result["state"] in ("done", "auto"):
                    log("     ✅ [明确确认成功] 刷新后签到已确认！奖励: %s | 余额: %s"
                        % (result["reward"] or "—", result["balance"] or "—"))

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


def patch_today_archive(json_path, md_path, today, choose, mutate):
    """Update chosen rows in today's last-run and re-render the markdown.

    choose(results) returns the row dicts to mutate in place. Returns how many
    rows changed, or 0 when the archive is missing, not from today, or unmatched.
    Used by --submit-captcha and by --prepare-captcha when a recheck lands on
    done (坑 40: prepare used to print done and leave last-run stale).
    """
    try:
        with open(json_path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception:  # noqa: BLE001
        return 0
    meta = payload.get("meta") or {}
    if meta.get("date") != today:
        return 0
    results = payload.get("results") or []
    chosen = list(choose(results) or [])
    if not chosen:
        return 0
    for row in chosen:
        mutate(row)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_report(results, meta))
    return len(chosen)


def merge_into_today_archive(json_path, results, today):
    """Merge a single-station rerun back into today's full-run archive.

    Returns (merged_results, merged_bool). See 坑 36: a `--url` rerun used to
    overwrite last-run.json/md with one row, destroying the day's report.
    """
    try:
        with open(json_path, encoding="utf-8") as fh:
            prev_payload = json.load(fh)
        prev_results = prev_payload.get("results") or []
        prev_date = (prev_payload.get("meta") or {}).get("date")
        if prev_date != today or len(prev_results) <= len(results):
            return results, False

        def _url_key(row):
            return (row.get("url") or "").rstrip("/").lower()

        def _name_key(row):
            return (row.get("name") or "").lower()

        merged = list(prev_results)
        by_url = {_url_key(row): i for i, row in enumerate(merged) if _url_key(row)}
        by_name = {_name_key(row): i for i, row in enumerate(merged) if _name_key(row)}
        for row in results:
            # URL 精确匹配优先（同一站可能换了书签路径）；退回站名匹配，
            # 避免补跑地址带/不带尾部 #hash 时在同一份报告里出现重复条目。
            pos = by_url.get(_url_key(row))
            if pos is None:
                pos = by_name.get(_name_key(row))
            if pos is None:
                merged.append(row)
            else:
                merged[pos] = row
        return merged, True
    except Exception:  # noqa: BLE001
        return results, False


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


# ---------------------------------------------------------------------------
# Manual-captcha workflow (2026-11-15)
# ---------------------------------------------------------------------------
# The full run reuses ONE scratch tab, so a captcha modal cannot survive to the
# next station. These two commands formalise what was previously ad-hoc:
#   1) --prepare-captcha URL  : open + click, leave the verification tab IN PLACE
#   2) --submit-captcha CODE  : fill the graphic code into that live tab
# Image-grid / slider verifications are never solved by the script; the tab is
# simply left in front so a human can finish it.

def find_tab_by_host(host):
    """Return the last front-window tab index whose URL contains host (0 if none)."""
    safe = (host or "").replace('"', "")
    raw = osa(
        'tell application "Google Chrome"\n'
        '  set out to ""\n'
        "  set n to count of tabs of front window\n"
        "  repeat with i from 1 to n\n"
        '    if (URL of tab i of front window) contains "%s" then\n'
        '      set out to (out & i & ",")\n'
        "    end if\n"
        "  end repeat\n"
        "  return out\n"
        "end tell\n" % safe,
        timeout=30,
    )
    idx = [int(x) for x in re.split(r"[, ]+", (raw or "").strip()) if x.isdigit()]
    return idx[-1] if idx else 0


def prepare_captcha(url, name="", close_if_done=True):
    """Open one station, trigger check-in, and leave the verification UI open.

    Returns a dict (printed as JSON by main). For graphic captchas the image is
    saved to data/captcha.png so the agent can read it and call submit_captcha.
    """
    tab = claim_scratch_tab()
    info = {"tab": tab, "url": url, "name": name, "kind": "", "prompt": "",
            "page": "", "image": "", "state": "", "evidence": "", "left_open": True}
    try:
        final, ok = open_station(url, tab=tab, retries=2)
        info["final_url"] = final
        if not ok:
            info["state"] = "unreachable"
            info["evidence"] = "open failed: %s" % final
            return info
        settle(tab=tab, seconds=LOAD_SECONDS)
        page = probe(tab=tab)
        state = classify(page)
        info["state"] = state["state"]
        info["evidence"] = state["evidence"]

        # 已有验证弹窗时绝不再点（会重置验证）；只有真正可点的待签到页才触发。
        c0 = page.get("captcha") or {}
        if (state["state"] not in ("done", "auto", "unsupported", "blocked_captcha")
                and not c0.get("blocking")):
            info["action"] = click_checkin(tab=tab)
            deadline = time.time() + 15
            while time.time() < deadline:
                time.sleep(1.5)
                page = probe(tab=tab)
                state = classify(page)
                c = page.get("captcha") or {}
                if (c.get("hasModal") or c.get("hasSlider")
                        or c.get("hasVerify") or c.get("blocking")):
                    break
                if state["state"] in ("done", "auto"):
                    break
            state = classify(page)
            info["state"] = state["state"]
            info["evidence"] = state["evidence"]

        c = page.get("captcha") or {}
        if c.get("hasModal"):
            info["kind"] = "graphic"
        elif c.get("hasVerify"):
            info["kind"] = "verify"
        elif c.get("hasSlider"):
            info["kind"] = "slider"
        info["prompt"] = c.get("prompt") or ""
        info["page"] = c.get("page") or ""

        # 2026-11-16：点选/滑块验证弹窗可能在停留数秒后自行通过或关闭。
        # PM-Plan 实测：prepare 返回 blocked_captcha，再次 probe 时弹窗已消失、
        # 页面已是「已完成签到」。发现此类验证后先短暂重探，已翻转为 done/auto
        # 就不要让人白跑一趟（图形码不会自行通过，不在此等待）。
        if info["kind"] in ("verify", "slider") or (
                state["state"] == "blocked_captcha" and not info["kind"]):
            deadline = time.time() + 10
            while time.time() < deadline:
                time.sleep(2.5)
                page = probe(tab=tab)
                state = classify(page)
                info["state"] = state["state"]
                info["evidence"] = state["evidence"]
                if state["state"] in ("done", "auto"):
                    info["resolved_after_wait"] = True
                    info["kind"] = ""
                    info["prompt"] = ""
                    info["page"] = ""
                    break
                c2 = page.get("captcha") or {}
                if not (c2.get("hasModal") or c2.get("hasSlider")
                        or c2.get("hasVerify") or c2.get("blocking")):
                    break

        if info["kind"] == "graphic":
            os.makedirs(DATA_DIR, exist_ok=True)
            out_path = os.path.join(DATA_DIR, "captcha.png")
            if save_captcha_image(tab=tab, out_path=out_path):
                info["image"] = out_path
        info["reward"] = state.get("reward")
        info["balance"] = state.get("balance")
        if state["state"] in ("done", "auto", "unsupported") and close_if_done:
            release_scratch_tab(tab)
            info["left_open"] = False
        return info
    except Exception as exc:  # noqa: BLE001
        info["error"] = "%s: %s" % (type(exc).__name__, exc)
        return info


def submit_captcha(host, code, close_tab=False):
    """Fill a graphic captcha code into the tab left open by prepare_captcha."""
    tab = find_tab_by_host(host)
    info = {"host": host, "tab": tab, "submitted": False, "state": "",
            "evidence": "", "reward": None, "balance": None}
    if not tab:
        info["error"] = "no open tab for host %s (先跑 --prepare-captcha)" % host
        return info
    url = current_url(tab)
    if host.lower() not in (url or "").lower():
        info["error"] = "tab %d is not the target host (url=%s)" % (tab, url)
        return info
    info["submit"] = solve_react_captcha(tab=tab, code=code)
    info["submitted"] = True

    state = None
    deadline = time.time() + 40
    while time.time() < deadline:
        time.sleep(2.5)
        page = probe(tab=tab)
        state = classify(page)
        info["state"] = state["state"]
        info["reward"] = state["reward"]
        info["balance"] = state["balance"]
        info["evidence"] = state["evidence"]
        if state["state"] in ("done", "auto"):
            break
        c = page.get("captcha") or {}
        if c.get("hasModal"):
            out_path = os.path.join(DATA_DIR, "captcha-next.png")
            if save_captcha_image(tab=tab, out_path=out_path):
                info["next_image"] = out_path
            break

    if close_tab and state and state["state"] in ("done", "auto"):
        release_scratch_tab(tab)
        info["closed"] = True
    return info


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
    ap.add_argument("--prepare-captcha", metavar="URL", default="",
                    help="打开站点并触发签到，把验证弹窗留在前台（人工或 agent 继续）")
    ap.add_argument("--submit-captcha", metavar="CODE", default="",
                    help="向 --prepare-captcha 留下的图形验证码标签页提交识别结果")
    ap.add_argument("--host", default="", help="配合 --submit-captcha：目标站点域名")
    ap.add_argument("--close-tab", action="store_true",
                    help="配合 --submit-captcha：成功后关闭该标签页（默认保留）")
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

    # ---- 人工验证码两段式模式（不进入全量站点循环）----
    if args.prepare_captcha:
        info = prepare_captcha(args.prepare_captcha, name=args.name)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        # 坑 40：复核已经是 done/auto 时回写当天归档，避免 last-run 停在 blocked_captcha。
        if info.get("state") in ("done", "auto") and os.path.exists(json_path):
            host = (urlparse(info.get("final_url") or args.prepare_captcha).hostname or "").lower()
            name = (args.name or info.get("name") or "").strip()
            today = datetime.now().strftime("%Y-%m-%d")

            def choose(rows, host=host, name=name):
                hits = [r for r in rows if host and host in (r.get("url") or "").lower()]
                if not name:
                    return hits
                exact = [r for r in hits if (r.get("name") or "") == name]
                if exact:
                    return exact
                partial = [r for r in hits if len(name) >= 4 and name in (r.get("name") or "")]
                if len(partial) == 1:
                    return partial
                return hits if len(hits) == 1 else []

            def mutate(row, info=info):
                row["state"] = "done"
                if info.get("reward"):
                    row["reward"] = info["reward"]
                if info.get("balance"):
                    row["balance"] = info["balance"]
                note = "prepare 复核已签到=" + (info.get("evidence") or "")[:80]
                ev = row.get("evidence") or ""
                if note not in ev:
                    row["evidence"] = (ev + " | " + note).strip(" |")

            try:
                n = patch_today_archive(json_path, md_path, today, choose, mutate)
                if n:
                    log("updated archive from prepare-captcha (%d)" % n)
                else:
                    log("prepare-captcha archive not updated (not today, or no matching row)")
            except Exception as exc:  # noqa: BLE001
                log("archive update failed: %s" % exc)
        return 0 if not info.get("error") else 1

    if args.submit_captcha:
        host = args.host or (urlparse(args.url).hostname if args.url else "")
        if not host:
            raise SystemExit("--submit-captcha 需要 --host（或配合 --url）指定站点域名")
        info = submit_captcha(host, args.submit_captcha, close_tab=args.close_tab)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        if info.get("state") in ("done", "auto") and os.path.exists(json_path):
            host_l = host.lower()
            today = datetime.now().strftime("%Y-%m-%d")

            def choose(rows, host_l=host_l):
                return [r for r in rows if host_l in (r.get("url") or "").lower()]

            def mutate(row, info=info):
                row["state"] = "done"
                row["reward"] = info.get("reward") or row.get("reward")
                row["balance"] = info.get("balance") or row.get("balance")
                row["evidence"] = (row.get("evidence") or "") + \
                    " | 人工验证码提交成功=" + (info.get("evidence") or "")[:80]
                if info.get("tab") and not info.get("closed"):
                    try:
                        row["final_url"] = current_url(info["tab"])
                    except Exception:  # noqa: BLE001
                        pass

            try:
                n = patch_today_archive(json_path, md_path, today, choose, mutate)
                if n:
                    log("updated archive for %s" % host)
                else:
                    log("archive update skipped for %s (not today, or no matching row)" % host)
            except Exception as exc:  # noqa: BLE001
                log("archive update failed: %s" % exc)
        return 0 if info.get("state") in ("done", "auto") else 1

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
            # 实时保存中间进度。
            # 坑 36 回归（2026-11-20）：单站补跑（--url）不能在这里落盘，
            # 否则会把当天全量归档覆盖成 1 条，merge_into_today_archive 再读时已无全量可合。
            if not args.url:
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

    # 2026-11-16：单站补跑（--url）不得覆盖当天的全量归档（坑 36）。
    # dry-run 不合并：只用探测结果替换真实签到结果会污染归档。
    if args.url and not args.dry_run:
        merged, did_merge = merge_into_today_archive(
            json_path, results, started.strftime("%Y-%m-%d"))
        if did_merge:
            results = merged
            log("单站补跑已合并进当日全量归档（%d 站）" % len(results))

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
