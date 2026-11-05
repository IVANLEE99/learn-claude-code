#!/usr/bin/env python3
"""gongyi-checkin — daily check-in runner for public-benefit API stations.

Reads the Chrome bookmark folder `daily-check-in` (id 6233), opens each station
in the logged-in daily Chrome, performs the daily check-in, and writes a report.

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
    ChromeError, classify, click_checkin, close_extra_tabs, count_tabs,
    current_url, js, js_retry, navigate, new_tab, osa, probe, tab_count,
    wait_for,
)

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_DIR, "data")
BOOKMARKS = os.path.expanduser(
    "~/Library/Application Support/Google/Chrome/Default/Bookmarks"
)
DEFAULT_FOLDER_ID = "6233"

# Stations that are known NOT to be check-in targets even though they live in
# the same bookmark folder (status pages, dashboards without a check-in).
SKIP_URL_FRAGMENTS = [
    "uptime-kuma",  # status monitoring page
]

# Load / settle times (seconds) per station, by page archetype.
LOAD_SECONDS = 8
SETTLE_SECONDS = 3
LOGIN_SETTLE_SECONDS = 6


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Bookmarks
# ---------------------------------------------------------------------------

def read_bookmarks(folder_id=DEFAULT_FOLDER_ID, path=BOOKMARKS):
    """Return [{'name','url'}] for the given bookmark folder id."""
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

    target = None
    for root in data["roots"].values():
        if isinstance(root, dict):
            target = find(root)
            if target:
                break
    if not target:
        raise SystemExit("bookmark folder %s not found in %s" % (folder_id, path))

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
    time.sleep(3)
    deadline = time.time() + seconds
    while time.time() < deadline:
        state = js(
            "document.readyState + '|' + (document.body ? document.body.innerText.length : 0)",
            tab=tab,
        )
        if state and "complete" in state.split("|")[0]:
            body_len = 0
            try:
                body_len = int(state.split("|")[1])
            except Exception:  # noqa: BLE001
                pass
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
        time.sleep(1.5)
    return False


def page_identity(tab=1):
    """Return (href, body_len, title) as seen by the PAGE ITSELF.

    Comparing the page's own location.href with the URL we asked for is the
    only reliable way to know the document has actually committed. Reading a
    page that is still the previous station produces perfectly plausible but
    completely wrong rewards/balances — the classic silent-stale-read bug.
    """
    raw = js(
        "location.href + '|' + (document.body ? document.body.innerText.length : 0) "
        "+ '|' + document.title",
        tab=tab,
    )
    parts = (raw or "").split("|")
    href = parts[0].strip() if parts else ""
    try:
        body_len = int(parts[1].strip()) if len(parts) > 1 else 0
    except ValueError:
        body_len = 0
    title = parts[2].strip() if len(parts) > 2 else ""
    return href, body_len, title


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
        time.sleep(0.6)
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
        settle(tab=tab, seconds=LOAD_SECONDS)

        # ---- identity check: is the document the one we asked for? ----
        deadline = time.time() + 12
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
    js_expr = r"""
(function(){
  function vis(e){
    var r=e.getBoundingClientRect(), s=getComputedStyle(e);
    return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';
  }
  var all=Array.from(document.querySelectorAll('a,button,[role=button],div,span'));
  var cand=all.filter(function(e){
    var tx=(e.textContent||'').trim();
    if(!tx||tx.length>40) return false;
    if(!/linux\s*do|linuxdo/i.test(tx)) return false;
    if(!vis(e)) return false;
    return true;
  });
  if(!cand.length) return 'NO_LINUXDO_BUTTON';
  cand.sort(function(a,b){
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
        result["state"] = state["state"]
        result["reward"] = state["reward"]
        result["balance"] = state["balance"]
        result["evidence"] = state["evidence"]

        # --- not logged in -> LinuxDO OAuth ---
        if state["state"] == "logged_out":
            result["action"] = "needs_login"
            if do_login and not dry_run:
                act = linuxdo_login(tab=tab)
                result["evidence"] += " | 登录点击=%s" % act
                if act == "clicked":
                    time.sleep(LOGIN_SETTLE_SECONDS)
                    # LinuxDO may show an authorize page -> click "授权/Authorize"
                    auth = js_retry(r"""
(function(){
  var b=Array.from(document.querySelectorAll('button,a,input[type=submit]'))
    .filter(function(e){return /授权|同意|允许|Authorize|Allow|Confirm/i.test((e.textContent||e.value||'').trim());});
  if(!b.length) return 'NO_AUTH_BUTTON';
  b[0].click(); return 'AUTH_CLICKED';
})()
""", tab=tab)
                    result["evidence"] += " 授权=%s" % auth
                    time.sleep(LOGIN_SETTLE_SECONDS)
                    settle(tab=tab, seconds=LOAD_SECONDS)
                    page2 = probe(tab=tab)
                    state2 = classify(page2)
                    result["state"] = state2["state"]
                    result["reward"] = state2["reward"]
                    result["balance"] = state2["balance"]
                    result["evidence"] += " | 登录后=" + state2["evidence"]
                    result["final_url"] = current_url(tab)

        # --- pending -> click the button ---
        if result["state"] == "pending" and not dry_run:
            clicked = click_checkin(tab=tab)
            result["action"] = "clicked" if clicked.startswith("CLICKED") else "click_failed"
            result["evidence"] += " | 点击=%s" % clicked
            time.sleep(SETTLE_SECONDS)
            page3 = probe(tab=tab)
            state3 = classify(page3)
            # After clicking, the button usually flips to disabled/"已签到"
            result["state"] = state3["state"]
            result["reward"] = state3["reward"] or result["reward"]
            result["balance"] = state3["balance"] or result["balance"]
            result["evidence"] += " | 点击后=" + state3["evidence"]
            result["final_url"] = current_url(tab)

        elif result["state"] == "pending":
            result["action"] = "dry_run_pending"

        elif result["state"] in ("done", "auto"):
            result["action"] = "already_done"

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
             "unreachable": "⚫ 暂时失联", "unknown": "⚠️ 状态未知"}.get(
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
    return before  # fall back to tab 1 if counting failed


def release_scratch_tab(index):
    """Close only our scratch tab (never the user's)."""
    if not index:
        return
    try:
        osa(
            'tell application "Google Chrome"\n'
            "  try\n"
            "    close tab %d of front window\n"
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

    # sanity: Chrome must be running
    n_tabs = tab_count()
    if n_tabs.startswith("__") or "error" in n_tabs.lower():
        raise SystemExit("cannot talk to Chrome (tabs=%s). Is Chrome running?" % n_tabs)
    log("Chrome tabs=%s" % n_tabs)

    if args.url:
        stations = [{"name": args.name or urlparse(args.url).hostname, "url": args.url}]
    else:
        stations = read_bookmarks(args.folder_id)
        if args.limit:
            stations = stations[: args.limit]
    log("stations=%d" % len(stations))

    results = []
    started = datetime.now()
    scratch = claim_scratch_tab()
    log("scratch tab=%d (user tabs untouched)" % scratch)
    try:
        for idx, entry in enumerate(stations):
            log("[%2d/%2d] %s" % (idx + 1, len(stations), entry["name"]))
            res = process_station(entry, tab=scratch, dry_run=args.dry_run,
                                  do_login=not args.no_login)
            results.append(res)
            log("     -> state=%s reward=%s balance=%s | %s"
                % (res["state"], res["reward"], res["balance"],
                   (res.get("evidence") or "")[:100]))
            sys.stdout.flush()
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
