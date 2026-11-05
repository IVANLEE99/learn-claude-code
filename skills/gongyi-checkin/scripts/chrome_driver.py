#!/usr/bin/env python3
"""gongyi-checkin — Chrome driver for public-benefit API station daily check-in.

Why AppleScript and not CDP (verified 2026-11-04):
  - Chrome 136+ refuses `--remote-debugging-port` on the *default* user-data-dir
    (the "user data directory is protected by Chrome" guard). The login sessions
    for these stations live ONLY in the daily Chrome profile
    (`~/Library/Application Support/Google/Chrome/Default`) — 26/28 stations have
    cookies there, 0/28 in the repo's mcp-chrome profile. So CDP is not an option.
  - `osascript` -> `execute javascript` works and can read AND click in ANY tab of
    the front window, including a non-active tab (`tell tab 1 of front window`).

Verified capabilities:
  - read JS   : `tell tab N of front window` -> execute javascript  -> OK
  - click JS  : same, element.click()                               -> OK
  - set URL   : `set URL of tab N of front window to "..."`          -> OK
  - new tab   : `make new tab at end of tabs of front window`       -> OK
  - close tabs: `close tab N of front window` (loop down)            -> OK

AppleScript string escaping is the #1 silent-failure source; use osa.js().
"""
import json
import os
import re
import subprocess
import time

CHROME = "Google Chrome"
DEFAULT_TAB = 1
DEFAULT_TIMEOUT = 90


class ChromeError(RuntimeError):
    pass


def osa(script, timeout=DEFAULT_TIMEOUT):
    """Run an AppleScript and return stdout (or stderr) as text."""
    try:
        out = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "__TIMEOUT__"
    except Exception as exc:  # noqa: BLE001
        return "__ERR__ %s" % exc
    return (out.stdout or out.stderr or "").strip()


def strip_js_comments(src):
    """Remove // line comments and /* */ block comments from JS source.

    CRITICAL: AppleScript string literals cannot span lines, so `esc()` rewrites
    newlines into spaces. If a `//` comment survives that rewrite, everything
    after it on the "line" is commented out — the IIFE then returns undefined
    and AppleScript reports "missing value", which looks exactly like a broken
    page. Strip comments BEFORE collapsing newlines.

    String and regex literals are respected so that a `//` inside 'https://...'
    is not mistaken for a comment.
    """
    out = []
    i = 0
    n = len(src)
    # prev significant char decides '/' == regex start vs division
    prev = ""
    while i < n:
        c = src[i]
        # --- string literals ---
        if c in "'\"":
            quote = c
            out.append(c)
            i += 1
            while i < n:
                out.append(src[i])
                if src[i] == "\\":
                    if i + 1 < n:
                        out.append(src[i + 1])
                        i += 2
                        continue
                elif src[i] == quote:
                    i += 1
                    break
                i += 1
            prev = quote
            continue
        # --- template literal ---
        if c == "`":
            out.append(c)
            i += 1
            while i < n:
                out.append(src[i])
                if src[i] == "\\" and i + 1 < n:
                    out.append(src[i + 1])
                    i += 2
                    continue
                if src[i] == "`":
                    i += 1
                    break
                i += 1
            prev = "`"
            continue
        # --- line comment ---
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        # --- block comment ---
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            i += 2
            while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                i += 1
            i += 2
            out.append(" ")
            continue
        out.append(c)
        if not c.isspace():
            prev = c
        i += 1
    return "".join(out)


def esc(js_expr):
    """Escape a JS expression for embedding in an AppleScript string literal.

    Order matters: strip comments, then backslash, then double-quote, then
    newlines. A raw newline or an unescaped quote makes osascript fail with a
    syntax error that is easy to misread as "the page is broken".
    """
    s = strip_js_comments(js_expr)
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace("\n", " ").replace("\r", " ")
    return s


def js(js_expr, tab=DEFAULT_TAB, timeout=DEFAULT_TIMEOUT):
    """Execute JS in the given tab of Chrome's front window and return the string."""
    script = (
        'tell application "%s"\n'
        "  activate\n"
        "  tell tab %d of front window\n"
        '    set r to execute javascript "%s"\n'
        "  end tell\n"
        "  return r\n"
        "end tell\n" % (CHROME, tab, esc(js_expr))
    )
    return osa(script, timeout=timeout)


def js_retry(js_expr, tab=DEFAULT_TAB, tries=3, pause=2.0, timeout=DEFAULT_TIMEOUT):
    """Retry transient AppleScript failures ('Access not allowed' / timeout)."""
    last = ""
    for _ in range(tries):
        last = js(js_expr, tab=tab, timeout=timeout)
        if last and not last.startswith(("__TIMEOUT__", "__ERR__")) and "(-" not in last[:60]:
            return last
        time.sleep(pause)
    return last


def navigate(url, tab=DEFAULT_TAB, timeout=DEFAULT_TIMEOUT):
    script = (
        'tell application "%s"\n'
        "  activate\n"
        '  set URL of tab %d of front window to "%s"\n'
        "end tell\n" % (CHROME, tab, url.replace('"', '\\"'))
    )
    return osa(script, timeout=timeout)


def current_url(tab=DEFAULT_TAB, timeout=30):
    script = (
        'tell application "%s"\n'
        "  get URL of tab %d of front window\n"
        "end tell\n" % (CHROME, tab)
    )
    return osa(script, timeout=timeout)


def new_tab(url, timeout=DEFAULT_TIMEOUT):
    script = (
        'tell application "%s"\n'
        "  activate\n"
        '  make new tab at end of tabs of front window with properties {URL:"%s"}\n'
        "end tell\n" % (CHROME, url.replace('"', '\\"'))
    )
    return osa(script, timeout=timeout)


def close_extra_tabs(keep=1, timeout=180):
    """Close tabs above `keep` (counting from the end). Keeps the window tidy."""
    script = (
        'tell application "%s"\n'
        "  set n to count of tabs of front window\n"
        "  repeat with i from n to %d by -1\n"
        "    close tab i of front window\n"
        "  end repeat\n"
        '  return "tabs_now=" & (count of tabs of front window)\n'
        "end tell\n" % (CHROME, keep + 1)
    )
    return osa(script, timeout=timeout)


def tab_count(timeout=30):
    return osa(
        'tell application "%s" to get count of tabs of front window\n' % CHROME,
        timeout=timeout,
    )


def count_tabs(timeout=30):
    """Number of tabs in the front window, as an int (0 on failure)."""
    raw = tab_count(timeout=timeout)
    m = re.search(r"-?\d+", raw or "")
    return int(m.group(0)) if m else 0


def wait_for(predicate, timeout=45, poll=2.0):
    """Poll `predicate()` (returns truthy string) until timeout."""
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        last = predicate()
        if last:
            return last
        time.sleep(poll)
    return last


# ---------------------------------------------------------------------------
# Page probes
# ---------------------------------------------------------------------------

# One JS expression that returns EVERYTHING needed to classify a station.
# Tuned against the 28 real stations on 2026-11-04.
PROBE_JS = r"""
(function(){
  function vis(e){
    var r=e.getBoundingClientRect(), s=getComputedStyle(e);
    return r.width>0 && r.height>0 &&
           s.display!=='none' && s.visibility!=='hidden' && s.opacity!=='0';
  }
  var all=document.querySelectorAll('*'), hits=[];
  for(var i=0;i<all.length;i++){
    var e=all[i], tx=(e.textContent||'').trim();
    if(!tx || tx.length>40) continue;
    if(!/签到|打卡|check[\s_-]?in/i.test(tx)) continue;
    // keep innermost match only (avoid parent+child duplicates)
    var deeper=false;
    for(var j=0;j<all.length;j++){
      var o=all[j];
      if(o!==e && o.contains && o.contains(e) && (o.textContent||'').trim()===tx){deeper=true;break;}
    }
    if(deeper) continue;
    var r=e.getBoundingClientRect();
    hits.push({tag:e.tagName, txt:tx,
      cls:(e.className||'').toString().slice(0,90),
      disabled:!!e.disabled, vis:vis(e),
      x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)});
  }
  // login / OAuth buttons
  var lg=[];
  for(var i=0;i<all.length;i++){
    var e=all[i], tx=(e.textContent||'').trim();
    if(!tx || tx.length>30) continue;
    if(!/linux\s*do|linuxdo/i.test(tx)) continue;
    var r=e.getBoundingClientRect();
    lg.push({tag:e.tagName, txt:tx, vis:vis(e),
      x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2),
      href:(e.getAttribute&&e.getAttribute('href')||'').slice(0,120)});
  }
  var body=(document.body.innerText||'');
  // Detect the check-in API call the page fired on load. Opening a station is
  // itself the check-in for these sites, so this is how we prove "auto" state.
  var apiHits=[];
  try{
    var res=performance.getEntriesByType('resource');
    for(var i=0;i<res.length;i++){
      var nm=res[i].name||'';
      if(/checkin|check_in|sign_?in|sign_in/i.test(nm)) apiHits.push(nm);
    }
  }catch(e){}
  // Label -> value pairs.
  //
  // DOM adjacency, NOT text scanning. Text scanning is ambiguous: on some
  // stations the value precedes its label ("$X Current balance"), on
  // others it follows it, and a naive scan happily binds a neighbouring
  // field's number (a user ID, a cumulative total) to the wrong label.
  // Here we find the element whose own text IS the label, then look for a
  // sibling element that holds the amount.
  var FIELD_LABELS=['可用余额','总余额','当前余额','账户余额','余额','可用额度','总额度',
              'Current balance','Current Balance','Available balance','BALANCE',
              '今日奖励','本次奖励','签到奖励','今日获得',
              'Consumption','TOTAL USAGE','总用量','总消耗额度','Total consumed quota',
              'Remaining quota','剩余配额','API REQUESTS','API 请求','Number of Requests',
              '累计获得','Total check-ins','总签到','Total received'];
  var labeled=[];
  try{
    function isLabel(t){
      for(var k=0;k<FIELD_LABELS.length;k++){
        if(t===FIELD_LABELS[k]) return true;
      }
      return false;
    }
    function findValueFor(labelText){
      var all=document.querySelectorAll('*');
      for(var i=0;i<all.length;i++){
        var e=all[i];
        var t=(e.textContent||'').trim();
        if(t!==labelText) continue;
        // must be the DEEPEST element carrying this text
        var dup=false;
        for(var j=0;j<e.children.length;j++){
          if((e.children[j].textContent||'').trim()===labelText) dup=true;
        }
        if(dup) continue;
        // climb looking for a sibling that holds a number
        var p=e.parentElement, hops=0;
        while(p && hops<3){
          for(var k=0;k<p.children.length;k++){
            var sib=p.children[k];
            if(sib===e) continue;
            var st=(sib.textContent||'').trim();
            if(!st || st.length>30) continue;
            if(!/[0-9]/.test(st)) continue;
            if(isLabel(st)) continue;
            var m=st.match(/[$¥€￥]?\s*\d+(?:[,\.]\d+)?/);
            if(m) return {value:m[0].trim(), raw:(labelText+' '+m[0].trim()).trim()};
          }
          p=p.parentElement; hops++;
        }
      }
      return null;
    }
    for(var i=0;i<FIELD_LABELS.length;i++){
      var got=findValueFor(FIELD_LABELS[i]);
      if(got) labeled.push({label:FIELD_LABELS[i], value:got.value, raw:got.raw});
    }
  }catch(e){}
  return JSON.stringify({
    url:location.href, title:document.title,
    hits:hits.slice(0,16), login:lg.slice(0,8),
    apiHits:apiHits.slice(0,6),
    labeled:labeled.slice(0,20),
    bodyLen:body.length,
    body:body.replace(/\s+/g,' ').slice(0,6000)
  });
})()
"""


def probe(tab=DEFAULT_TAB):
    """Read the current page's check-in state, buttons, and body text."""
    raw = js_retry(PROBE_JS, tab=tab)
    try:
        return json.loads(raw)
    except Exception:  # noqa: BLE001
        return {"url": current_url(tab), "error": raw[:300], "hits": [], "login": [],
                "body": "", "bodyLen": 0}


# Click a visible check-in button. Returns a short status string.
CLICK_JS = r"""
(function(){
  function vis(e){
    var r=e.getBoundingClientRect(), s=getComputedStyle(e);
    return r.width>0 && r.height>0 &&
           s.display!=='none' && s.visibility!=='hidden' && s.opacity!=='0';
  }
  var all=Array.from(document.querySelectorAll('button,a,[role=button]'));
  var cand=all.filter(function(e){
    var tx=(e.textContent||'').trim();
    if(!tx || tx.length>24) return false;
    if(!/签到|打卡|check[\s_-]?in/i.test(tx)) return false;
    if(/已签到|Checked in|已领取|明日|明天/i.test(tx)) return false;
    if(e.disabled) return false;
    if(!vis(e)) return false;
    return true;
  });
  if(!cand.length) return 'NO_PENDING_BUTTON';
  // prefer the tightest (smallest area) match -> the real button, not a wrapper
  cand.sort(function(a,b){
    var ra=a.getBoundingClientRect(), rb=b.getBoundingClientRect();
    return (ra.width*ra.height)-(rb.width*rb.height);
  });
  var e=cand[0];
  var tx=(e.textContent||'').trim();
  e.scrollIntoView({block:'center'});
  e.click();
  return 'CLICKED:'+tx.slice(0,20);
})()
"""


def click_checkin(tab=DEFAULT_TAB):
    """Click the pending check-in button (smallest visible enabled match)."""
    return js_retry(CLICK_JS, tab=tab)


# ---------------------------------------------------------------------------
# Station state extraction (reward / balance / done-ness)
# ---------------------------------------------------------------------------

BALANCE_LABELS = [
    "可用余额", "总余额", "当前余额", "账户余额", "余额",
    "可用额度", "总额度",
    "Current balance", "Current Balance", "Available balance",
    "BALANCE", "Balance", "balance",
]
# Reward labels must be qualified by "today" — a bare "奖励"/"获得" is usually a
# cumulative total (e.g. 薄荷 "累计获得: N 次"), not today's grant.
REWARD_LABELS = [
    "今日奖励", "本次奖励", "签到奖励", "今日获得", "今日获得奖励",
    "Today's reward", "today reward", "Daily reward",
]
# Labels that mean "cumulative", never "today's reward".
CUMULATIVE_HINTS = [
    "累计", "总共", "共获得", "总共获得", "历史", "总收入", "总收入",
    "total", "Total", "cumulative",
]
DONE_PATTERNS = [
    r"今日已签到", r"已签到", r"Checked in", r"checked in",
    r"明天\s*00:00", r"明日再来", r"今日已领取", r"今日已打卡",
]
PENDING_MARKERS = [
    r"每日签到", r"Daily Check-?in", r"签到领取", r"每天8点刷新",
]


def _clean(txt):
    return re.sub(r"\s+", " ", (txt or "").strip())


def _money(val):
    if not val:
        return None
    m = re.search(r"([$¥€￥])?\s*(\d+(?:[.,]\d+)?)", val)
    if not m:
        return None
    return "%s%s" % (m.group(1) or "", m.group(2).replace(",", ""))


def _find_money_after(body, labels):
    """Find `<label> <value>` pairs, preferring the longest label first so that
    '可用余额' wins over '余额' and '总余额' over '余额'."""
    for label in labels:
        for m in re.finditer(
            re.escape(label) + r"\s*[:：]?\s*([$¥€￥]?\s*\d+(?:[.,]\d+)?)", body
        ):
            val = _money(m.group(1))
            if val:
                return val, m.group(0)
    return None, None


def _balance_from_labeled(labeled):
    """Pick the balance out of the probe's label->value pairs.

    Prefer the spendable balance (可用余额 / 当前余额 / Current balance);
    fall back to 总余额 / 余额.
    """
    for label in ("可用余额", "当前余额", "Current balance", "Current Balance",
                  "Available balance", "BALANCE", "账户余额"):
        row = labeled.get(label)
        if row and row.get("value"):
            return _money(row["value"]), row.get("raw") or label
    for label in ("总余额", "总额度", "余额", "可用额度"):
        row = labeled.get(label)
        if row and row.get("value"):
            return _money(row["value"]), row.get("raw") or label
    return None, None


def _reward_from_labeled(labeled):
    """Pick today's reward out of the probe's label->value pairs."""
    for label in ("今日奖励", "本次奖励", "签到奖励", "今日获得"):
        row = labeled.get(label)
        if row and row.get("value"):
            raw = row.get("raw") or ""
            if any(h in raw for h in CUMULATIVE_HINTS):
                continue
            return _money(row["value"]), raw
    return None, None


def _find_balance(body):
    """Locate the account balance.

    Order matters. Some stations render a hover dropdown containing several
    amounts (可用余额 / 冻结金额 / 总余额) and some put the header balance
    BEFORE the check-in widget, so a bare "第一个金额" heuristic picks the
    wrong number. Prefer explicit balance labels; among them prefer the
    '可用余额/当前余额/Current balance' (spendable) one, then 总余额.
    """
    # 1) explicit, unambiguous balance labels
    for label in ("可用余额", "当前余额", "Current balance", "Current Balance",
                  "Available balance", "BALANCE", "账户余额"):
        m = re.search(
            re.escape(label) + r"\s*[:：]?\s*([$¥€￥]?\s*\d+(?:[.,]\d+)?)", body)
        if m:
            return _money(m.group(1)), m.group(0)
    # 2) 总余额 / 总额度
    for label in ("总余额", "总额度"):
        m = re.search(
            re.escape(label) + r"\s*[:：]?\s*([$¥€￥]?\s*\d+(?:[.,]\d+)?)", body)
        if m:
            return _money(m.group(1)), m.group(0)
    # 3) plain "余额" — but NOT when it is part of a longer phrase
    m = re.search(r"(?<!总)(?<!可用)(?<!当前)余额\s*[:：]?\s*([$¥€￥]?\s*\d+(?:[.,]\d+)?)",
                  body)
    if m:
        return _money(m.group(1)), m.group(0)
    # 4) "Balance" as a standalone word (not part of "Balance and top-up")
    m = re.search(r"\bBalance\b(?!\s+and\b)\s*[:：]?\s*([$¥€￥]?\s*\d+(?:[.,]\d+)?)",
                  body)
    if m:
        return _money(m.group(1)), m.group(0)
    return None, None


def classify(page):
    """Classify a probed page into a check-in state.

    Returns dict: state / reward / balance / evidence.
      state ∈ {done, pending, auto, logged_out, unreachable, unknown}
    """
    body = _clean(page.get("body", ""))
    hits = page.get("hits") or []
    login = page.get("login") or []
    url = page.get("url", "") or ""

    out = {"state": "unknown", "reward": None, "balance": None, "evidence": ""}

    # ---- unreachable? ----
    if url.startswith("chrome-error://") or "ERR_CONNECTION" in body or "can’t be reached" in body.lower():
        out["state"] = "unreachable"
        out["evidence"] = _clean(body[:90])
        return out

    # ---- not logged in? (a LinuxDO login button on an otherwise-empty page) ----
    if login and len(body) < 1200 and not re.search(
        r"已签到|Checked in|当前余额|Current balance|余额", body
    ):
        out["state"] = "logged_out"
        out["evidence"] = "linuxdo登录按钮: " + _clean(login[0].get("txt", ""))[:30]
        return out

    # ---- reward / balance ----
    # Prefer the label->value pairs captured by the probe: they were read from
    # textContent next to their label, so evidence and value cannot drift apart.
    labeled = {row.get("label", ""): row for row in (page.get("labeled") or [])}

    bal, bal_raw = _balance_from_labeled(labeled)
    if not bal:
        bal, bal_raw = _find_balance(body)
    rew, rew_raw = _reward_from_labeled(labeled)
    if not rew:
        rew, rew_raw = _find_money_after(body, REWARD_LABELS)

    # "今天 +$X" / "Today +$X" — the canonical new-api reward form.
    # A currency symbol (or an explicit '+') is REQUIRED: plain digits after
    # "today" are the check-in COUNT ("Checked in today 99 Total check-ins"),
    # not money.
    if not rew:
        m = re.search(
            r"(?:今天|今日|Today|today)\s*(?:\+\s*)?([$¥€￥]\s*\d+(?:[.,]\d+)?)", body)
        if m:
            rew, rew_raw = _money(m.group(1)), m.group(0)
    # Some cards only carry the amount inside the check-in button:
    #   "Daily Check-inChecked inToday +$X"  /  "每日签到已签到今天 +$X"
    if not rew:
        for h in hits:
            txt = _clean(h.get("txt", ""))
            m = re.search(
                r"(?:今天|今日|Today|today)\s*(?:\+\s*)?([$¥€￥]\s*\d+(?:[.,]\d+)?)", txt)
            if m:
                rew, rew_raw = _money(m.group(1)), m.group(0)
                break
    # Special archetype: 流光绘境 / chatgpt2api 类: "剩余额度 44 签到 19 已签到"
    if not rew:
        m = re.search(r"签到\s*(\d+)\s*已签到", body)
        if m:
            rew, rew_raw = "+" + m.group(1), m.group(0)
    # Guard: a cumulative figure ("累计获得: N") is NOT today's reward.
    if rew and any(h in (rew_raw or "") for h in CUMULATIVE_HINTS):
        rew, rew_raw = None, None
    out["balance"] = bal
    out["reward"] = rew
    if bal_raw:
        out["evidence"] += "余额←%s " % bal_raw[:34]
    if rew_raw:
        out["evidence"] += "奖励←%s " % rew_raw[:34]

    # ---- done-ness ----
    ck_text = " ".join(_clean(h.get("txt", "")) for h in hits)

    if any(re.search(p, body, re.I) for p in DONE_PATTERNS):
        out["state"] = "done"
        m = re.search(r"(今日已签到[^ ]{0,18}|已签到[^ ]{0,14}|Checked in[^ ]{0,22})", body, re.I)
        out["evidence"] += "状态←" + (m.group(0)[:34] if m else "已签到")
        return out

    if hits:
        # a visible, enabled check-in button that is not marked done
        pending = [
            h for h in hits
            if h.get("vis") and not h.get("disabled")
            and re.search(r"签到|check", _clean(h.get("txt", "")), re.I)
            and not re.search(r"已签到|Checked in|已领取", _clean(h.get("txt", "")), re.I)
        ]
        if pending:
            out["state"] = "pending"
            out["evidence"] += "待签到按钮←" + _clean(pending[0].get("txt", ""))[:28]
            return out

        # all visible check-in widgets are disabled -> already done
        disabled_ck = [h for h in hits if h.get("disabled")]
        if disabled_ck:
            out["state"] = "done"
            out["evidence"] += "按钮disabled←" + _clean(disabled_ck[0].get("txt", ""))[:24]
            return out

        if re.search(r"已签到|Checked in", ck_text, re.I):
            out["state"] = "done"
            out["evidence"] += "控件←" + ck_text[:30]
            return out

    if re.search(r"|".join(PENDING_MARKERS), body, re.I) and re.search(
        r"签到|check", body, re.I
    ):
        out["state"] = "auto"
        out["evidence"] += "打开即签到(无按钮)"

    # ---- no visible check-in UI, but the page fired a check-in API on load ----
    # (Any Router style: GET /api/user/sign_in). Opening the page IS the
    # check-in, and the station shows no check-in card at all.
    api_hits = page.get("apiHits") or []
    if api_hits and out["state"] == "unknown":
        out["state"] = "auto"
        out["evidence"] += "打开即签到←" + api_hits[0].split("/")[-1][:36]

    if not out["evidence"]:
        out["evidence"] = _clean(body[:110])
    return out


if __name__ == "__main__":
    import sys

    page = probe()
    result = classify(page)
    print(json.dumps({"page": {k: page.get(k) for k in ("url", "title", "bodyLen")},
                      "result": result}, ensure_ascii=False, indent=2))
