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

    String, template, and regex literals are respected so that a `//` inside
    'https://...' or `/https?:\\/\\//` is not mistaken for a comment.
    """
    out = []
    i = 0
    n = len(src)
    prev = ""
    last_word = ""

    REGEX_PREV_CHARS = {"", "(", "[", "{", ",", ";", ":", "!", "&", "|", "?", "=", "+", "-", "*", "%", "~", "^", "<", ">"}
    REGEX_PREV_WORDS = {"return", "typeof", "case", "delete", "throw", "void", "in", "instanceof", "new", "yield", "await"}

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
            last_word = ""
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
            last_word = ""
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
        # --- regex literal ---
        if c == "/" and (prev in REGEX_PREV_CHARS or last_word in REGEX_PREV_WORDS):
            out.append(c)
            i += 1
            in_char_class = False
            while i < n:
                rc = src[i]
                out.append(rc)
                if rc == "\\":
                    if i + 1 < n:
                        out.append(src[i + 1])
                        i += 2
                        continue
                elif rc == "[" and not in_char_class:
                    in_char_class = True
                elif rc == "]" and in_char_class:
                    in_char_class = False
                elif rc == "/" and not in_char_class:
                    i += 1
                    while i < n and src[i].isalpha():
                        out.append(src[i])
                        i += 1
                    break
                elif rc == "\n":
                    break
                i += 1
            prev = "/"
            last_word = ""
            continue

        out.append(c)
        if not c.isspace():
            prev = c
            if c.isalnum() or c == "_":
                last_word += c
            else:
                last_word = ""
        else:
            if last_word not in REGEX_PREV_WORDS:
                last_word = ""
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
        "  set totalTabs to count of tabs of front window\n"
        "  set tIdx to %d\n"
        "  if tIdx < 1 or tIdx > totalTabs then\n"
        '    error "Chrome tab index out of bounds: " & tIdx & " (total: " & totalTabs & ")"\n'
        "  end if\n"
        "  tell tab tIdx of front window\n"
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
    safe_url = url.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        'tell application "%s"\n'
        "  activate\n"
        "  set totalTabs to count of tabs of front window\n"
        "  set tIdx to %d\n"
        "  if tIdx < 1 or tIdx > totalTabs then\n"
        '    error "Chrome tab index out of bounds: " & tIdx & " (total: " & totalTabs & ")"\n'
        "  end if\n"
        '  set URL of tab tIdx of front window to "%s"\n'
        "end tell\n" % (CHROME, tab, safe_url)
    )
    return osa(script, timeout=timeout)


def current_url(tab=DEFAULT_TAB, timeout=30):
    script = (
        'tell application "%s"\n'
        "  set totalTabs to count of tabs of front window\n"
        "  set tIdx to %d\n"
        "  if tIdx < 1 or tIdx > totalTabs then\n"
        '    error "Chrome tab index out of bounds: " & tIdx & " (total: " & totalTabs & ")"\n'
        "  end if\n"
        "  get URL of tab tIdx of front window\n"
        "end tell\n" % (CHROME, tab)
    )
    return osa(script, timeout=timeout)


def new_tab(url, timeout=DEFAULT_TIMEOUT):
    safe_url = url.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        'tell application "%s"\n'
        "  activate\n"
        '  make new tab at end of tabs of front window with properties {URL:"%s"}\n'
        "end tell\n" % (CHROME, safe_url)
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


def activate_tab(tab=DEFAULT_TAB, timeout=30):
    """Set active tab in front window (important for Cloudflare turnstile visibility)."""
    script = (
        'tell application "%s"\n'
        "  set totalTabs to count of tabs of front window\n"
        "  set tIdx to %d\n"
        "  if tIdx < 1 or tIdx > totalTabs then\n"
        '    error "Chrome tab index out of bounds: " & tIdx & " (total: " & totalTabs & ")"\n'
        "  end if\n"
        "  set active tab index of front window to tIdx\n"
        "end tell\n" % (CHROME, tab)
    )
    return osa(script, timeout=timeout)


def is_cf_challenge(tab=DEFAULT_TAB):
    """Check if the tab is showing a Cloudflare 5s / turnstile / challenge page or modal."""
    res = js(r"""
    (function(){
      var t = document.title || '';
      var b = (document.body ? document.body.innerText : '') || '';
      var u = location.href || '';
      var isCfError = /Error\s*(?:1033|502|503|52[0-4])|Argo Tunnel error|Cloudflare Tunnel|Bad gateway/i.test(t + ' ' + b);
      if (isCfError) {
        return JSON.stringify({
          is_cf: false,
          is_error: true,
          title: t,
          url: u,
          len: b.length
        });
      }
      var hasCfTitle = /Just a moment|Attention Required|Security Challenge|Cloudflare|Please Wait/i.test(t);
      var hasCfText = /Verify you are human|Checking your browser|Checking if the site connection is secure|Cloudflare Ray ID|Enable JavaScript and cookies/i.test(b);
      var cfCandidates = document.querySelectorAll('#challenge-running, #challenge-stage, #cf-challenge-running, iframe[src*="challenges.cloudflare.com"], iframe[src*="turnstile"], div.cf-turnstile');
      var hasCfModal = false;
      for (var i = 0; i < cfCandidates.length; i++) {
        var el = cfCandidates[i];
        var r = el.getBoundingClientRect();
        var s = getComputedStyle(el);
        if (r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0') {
          hasCfModal = true;
          break;
        }
      }
      var isCfUrl = /challenges\.cloudflare\.com/i.test(u);
      var isRealSite = /每日签到|Daily Check-in|Current balance|可用余额|总余额|控制台|Dashboard|个人设置/i.test(b);
      var isCfPage = (hasCfTitle || hasCfText || isCfUrl) && !isRealSite;
      return JSON.stringify({
        is_cf: hasCfModal || isCfPage,
        is_error: false,
        title: t,
        url: u,
        len: b.length
      });
    })()
    """, tab=tab)
    try:
        data = json.loads(res)
        return data.get("is_cf", False), data.get("title", "")
    except Exception:
        return False, ""


def wait_cf_pass(tab=DEFAULT_TAB, timeout=60, poll=2.0, log_fn=print):
    """Poll and wait until Cloudflare verification completes."""
    deadline = time.time() + timeout
    activated = False
    first = True
    while time.time() < deadline:
        is_cf, title = is_cf_challenge(tab=tab)
        if not is_cf:
            if not first:
                log_fn("     [CF验证] Cloudflare 验证通过，页面已加载目标站点！")
            return True
        if first:
            log_fn("     [CF验证] 检测到 Cloudflare 验证盾 (title='%s')，明确等待验证通过..." % title)
            first = False
        if not activated:
            activate_tab(tab=tab)
            activated = True
        time.sleep(poll)
    return False


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
    if(!/签到|打卡|check[\s_-]?in|开始转动|转动|开始抽奖/i.test(tx)) continue;
    // keep innermost match only (avoid parent+child duplicates)
    var deeper=false;
    if(e.firstElementChild){
      var subs=e.querySelectorAll('*');
      for(var j=0;j<subs.length;j++){
        if((subs[j].textContent||'').trim()===tx){ deeper=true; break; }
      }
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
    if(/已绑定|管理|解除/i.test(tx)) continue;
    if(!vis(e)) continue;
    var r=e.getBoundingClientRect();
    lg.push({tag:e.tagName, txt:tx, vis:true,
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
              'Current balance','Current Balance','Available balance','BALANCE','Balance','balance',
              '今日奖励','本次奖励','本次获得','签到奖励','今日获得','今日获得奖励',
              'Today\'s reward','today reward','Daily reward',
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
        // Climb looking for a sibling that IS the amount.
        //
        // The sibling must be VALUE-SHAPED (整段就是一个金额), not merely
        // "contains a digit". 2026-11-06 lOXO: the label 今日奖励 sits next to
        // 待领取, and a digit-hungry scan climbed to a sibling carrying
        // "已连续签到 7 天" and bound 7 as today's reward.
        var VALUE_RE = /^[+-]?\s*(?:[$¥€￥]|BTC)?\s*\d[\d,]*(?:\.\d+)?\s*(?:元|额度|点|次|USD|BTC|credits?)?$/i;
        var p=e.parentElement, hops=0;
        while(p && hops<3){
          for(var k=0;k<p.children.length;k++){
            var sib=p.children[k];
            if(sib===e) continue;
            var st=(sib.textContent||'').trim();
            if(!st || st.length>30) continue;
            if(/待领取|未领取|暂无|未签到/.test(st)) continue;
            if(isLabel(st)) continue;
            if(!VALUE_RE.test(st)) continue;
            var m=st.match(/(?:[+-])?\s*(?:[$¥€￥]|BTC)?\s*\d[\d,]*(?:\.\d+)?\s*(?:元|额度|点|次|USD|BTC|credits?)?/i);
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
  var captchaImg = document.querySelector('img[src^="data:image"], img[src*="captcha"]');
  var captchaInput = document.querySelector('input[placeholder*="验证码"], input[placeholder*="code"], input[name*="captcha"]');
  var hasCaptchaModal = !!(captchaImg && captchaInput && vis(captchaImg) && vis(captchaInput));
  var captchaSrc = (hasCaptchaModal && captchaImg) ? captchaImg.src : '';
  var hasSlider = false;
  var sliderTexts = ['拖动滑块', '拼合缺口', '向右滑动', 'Slide to verify', 'drag the slider', '完成拼图'];
  for(var i=0; i<all.length; i++){
    var stx = (all[i].textContent||'').trim();
    if(stx && stx.length < 30 && vis(all[i])){
      for(var k=0; k<sliderTexts.length; k++){
        if(stx.indexOf(sliderTexts[k]) !== -1){ hasSlider = true; break; }
      }
      if(hasSlider) break;
    }
  }
  var toastEls = document.querySelectorAll('.ant-message-notice, .ant-notification-notice, .semi-toast, .Toastify__toast, [data-sonner-toast], .el-message, .v-toast');
  var toasts = Array.from(toastEls).filter(vis).map(function(e){ return (e.textContent||'').trim(); }).filter(Boolean).join(' ');
  return JSON.stringify({
    url:location.href, title:document.title,
    hits:hits.slice(0,16), login:lg.slice(0,8),
    apiHits:apiHits.slice(0,6),
    labeled:labeled.slice(0,20),
    captcha:{hasModal:hasCaptchaModal, src:captchaSrc.slice(0,400), hasSlider:hasSlider},
    toasts:toasts.slice(0,400),
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
  // 特殊站点辅助：Fengwind 先选 d1 有效期
  try {
    var vRadio = document.querySelector('input[name="checkin-validity"][value="d1"]');
    if (vRadio && !vRadio.checked) {
      vRadio.click();
      vRadio.checked = true;
      vRadio.dispatchEvent(new Event('change', {bubbles: true}));
    }
  } catch(e){}

  var all=Array.from(document.querySelectorAll('button,a,[role=button]'));
  var cand=all.filter(function(e){
    var tx=(e.textContent||'').trim();
    if(!tx || tx.length>30) return false;
    if(!/签到|打卡|check[\s_-]?in|开始转动|转动|开始抽奖/i.test(tx)) return false;
    if(/已签到|Checked in|已领取|明日|明天|转动中/i.test(tx)) return false;
    if(e.disabled) return false;
    if(!vis(e)) return false;
    return true;
  });
  if(!cand.length) return 'NO_PENDING_BUTTON';
  // Rank:
  // 1. BUTTON 优于 A
  // 2. 导航链接 (class 含 nav/menu/tab/sidebar) 降权
  // 3. 动作词 (立即/现在/领取/去签到/签到领/开始/Check in now) 优先
  // 4. 面积更小的优先
  function score(e){
    var t=(e.textContent||'').trim();
    var isButton = (e.tagName==='BUTTON' || e.getAttribute('role')==='button') ? 0 : 1;
    var action=/立即|现在|领取|去签到|签到领|开始转动|转动|开始|Check in now|Check-in now/i.test(t)?0:1;
    var navish=(e.tagName==='A' && /sidebar|nav|menu|tab/i.test((e.className||'').toString()))?1:0;
    var r=e.getBoundingClientRect();
    return [isButton, navish, action, r.width*r.height];
  }
  cand.sort(function(a,b){
    var sa=score(a), sb=score(b);
    for(var k=0; k<sa.length; k++){
      if(sa[k]!==sb[k]) return sa[k]-sb[k];
    }
    return 0;
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


def solve_react_captcha(tab=DEFAULT_TAB, code=""):
    """Inject graphical captcha code into React controlled input via native property setter and submit."""
    js_expr = r"""
    (function(){
      var input = document.querySelector('input[placeholder*="验证码"], input[placeholder*="code"], input[name*="captcha"]');
      if (!input) return 'NO_INPUT';
      var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(input, %s);
      input.dispatchEvent(new Event('input', {bubbles: true}));
      input.dispatchEvent(new Event('change', {bubbles: true}));
      var btn = Array.from(document.querySelectorAll('button, a, .ant-btn'))
        .filter(function(e){ return /确定|确认|Confirm|Submit|OK/i.test((e.textContent||'').trim()) && e.offsetWidth > 0; });
      if (btn.length > 0) {
        btn[0].click();
        return 'SUBMITTED';
      }
      return 'INPUT_SET';
    })()
    """ % json.dumps(code)
    return js(js_expr, tab=tab)


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
    "今日奖励", "本次奖励", "本次获得", "签到奖励", "今日获得", "今日获得奖励",
    "Today's reward", "today reward", "Daily reward",
]
# Labels that mean "cumulative", never "today's reward".
CUMULATIVE_HINTS = [
    "累计", "总共", "共获得", "总共获得", "历史", "总收入",
    "total", "Total", "cumulative",
]
DONE_PATTERNS = [
    r"今日已签到", r"已签到", r"Checked in", r"checked in",
    r"明天\s*00:00", r"明日再来", r"今日已领取", r"今日已打卡",
    r"已领取，明天再来",
]
PENDING_MARKERS = [
    r"每日签到", r"Daily Check-?in", r"签到领取", r"每天8点刷新",
]


def _clean(txt):
    return re.sub(r"\s+", " ", (txt or "").strip())


def _money(val):
    if not val:
        return None
    # 负余额是合法状态（2026-11-06 月城 当前余额 -$13.92），符号要紧贴货币符号
    # 允许 BTC, 货币符号，千分位逗号与浮点数
    m = re.search(
        r"([+-])?\s*([$¥€￥]|BTC)?\s*(\d[\d,]*(?:\.\d+)?)\s*([$¥€￥]|BTC|元|额度|点|次|USD)?",
        val,
        re.I,
    )
    if not m:
        return None
    sign = m.group(1) or ""
    cur_lead = m.group(2) or ""
    num = m.group(3).replace(",", "")
    cur_trail = m.group(4) or ""
    cur = cur_lead or cur_trail
    if sign == "+":
        return "+%s%s" % (cur, num) if cur else "+%s" % num
    return "%s%s%s" % (sign, cur, num)


def _find_money_after(body, labels):
    """Find `<label> <value>` pairs, preferring the longest label first so that
    '可用余额' wins over '余额' and '总余额' over '余额'."""
    for label in labels:
        for m in re.finditer(
            re.escape(label) + r"\s*[:：]?\s*([+-]?\s*(?:[$¥€￥]|BTC)?\s*\d[\d,]*(?:\.\d+)?\s*(?:[$¥€￥]|BTC|元|额度|点|次|USD)?)",
            body,
            re.I,
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
                  "Available balance", "BALANCE", "Balance", "balance", "账户余额"):
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
    for label in ("今日奖励", "本次奖励", "本次获得", "签到奖励", "今日获得", "今日获得奖励",
                  "Today's reward", "today reward", "Daily reward"):
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
                  "Available balance", "BALANCE", "Balance", "balance", "账户余额"):
        m = re.search(
            re.escape(label) + r"\s*[:：]?\s*([+-]?\s*(?:[$¥€￥]|BTC)?\s*\d[\d,]*(?:\.\d+)?\s*(?:[$¥€￥]|BTC|元|额度|点|次|USD)?)",
            body,
            re.I,
        )
        if m:
            return _money(m.group(1)), m.group(0)
    # 2) 总余额 / 总额度
    for label in ("总余额", "总额度"):
        m = re.search(
            re.escape(label) + r"\s*[:：]?\s*([+-]?\s*(?:[$¥€￥]|BTC)?\s*\d[\d,]*(?:\.\d+)?\s*(?:[$¥€￥]|BTC|元|额度|点|次|USD)?)",
            body,
            re.I,
        )
        if m:
            return _money(m.group(1)), m.group(0)
    # 3) plain "余额" — but NOT when it is part of a longer phrase
    m = re.search(
        r"(?<!总)(?<!可用)(?<!当前)余额\s*[:：]?\s*([+-]?\s*(?:[$¥€￥]|BTC)?\s*\d[\d,]*(?:\.\d+)?\s*(?:[$¥€￥]|BTC|元|额度|点|次|USD)?)",
        body,
        re.I,
    )
    if m:
        return _money(m.group(1)), m.group(0)
    # 4) "Balance" as a standalone word (not part of "Balance and top-up")
    m = re.search(
        r"\bBalance\b(?!\s+and\b)\s*[:：]?\s*([+-]?\s*(?:[$¥€￥]|BTC)?\s*\d[\d,]*(?:\.\d+)?\s*(?:[$¥€￥]|BTC|元|额度|点|次|USD)?)",
        body,
        re.I,
    )
    if m:
        return _money(m.group(1)), m.group(0)
    return None, None


def _find_gift_quota(body):
    """Gift/free quota — where check-in rewards actually land on some stations.

    2026-11-06 三水: header shows `付费 $0 免费 $16.12`. The paid balance really
    is $0; the sign-in reward ($3.03) tops up the FREE quota. Reporting "$0" is
    technically true but useless — so when the paid balance is zero, fall back
    to the gift quota.
    """
    m = re.search(
        r"(?:免费|赠送|赠金|赠送额度|Gift|Free)\s*[:：]?\s*([+-]?\s*(?:[$¥€￥]|BTC)?\s*\d[\d,]*(?:\.\d+)?\s*(?:[$¥€￥]|BTC|元|额度|点|次|USD)?)",
        body,
        re.I,
    )
    if m:
        return _money(m.group(1)), m.group(0)
    return None, None


def classify(page):
    """Classify a probed page into a check-in state.

    Returns dict: state / reward / balance / evidence.
      state ∈ {done, pending, auto, logged_out, unreachable, blocked_captcha, unsupported, unknown}
    """
    body = _clean(page.get("body", ""))
    hits = page.get("hits") or []
    login = page.get("login") or []
    url = page.get("url", "") or ""
    toast_text = _clean(page.get("toasts", ""))

    out = {"state": "unknown", "reward": None, "balance": None, "evidence": ""}

    # ---- unreachable / tunnel down / 5xx? ----
    if (url.startswith("chrome-error://")
            or re.search(r"ERR_CONNECTION|can[’']t be reached|Error\s*(?:1033|502|503|52[0-4])|Argo Tunnel error|Cloudflare Tunnel|Bad gateway", body, re.I)):
        out["state"] = "unreachable"
        if "1033" in body or "Cloudflare Tunnel error" in body:
            out["evidence"] = "Cloudflare Tunnel Error 1033 (HTTP 530)"
        else:
            m = re.search(r"Error\s*(?:1033|502|503|52[0-4])|Argo Tunnel error|Bad gateway", body, re.I)
            out["evidence"] = m.group(0) if m else _clean(body[:90])
        return out

    # ---- not logged in? (a LinuxDO login button on an otherwise-empty page or login URL) ----
    is_login_url = bool(re.search(r"/login|/sign-in", url, re.I))
    if login and (is_login_url or len(body) < 1200) and not re.search(
        r"已签到|Checked in|当前余额|Current balance|Available balance|可用额度|余额|每日签到|Check in", body, re.I
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
    # Paid balance is $0 but the station runs on gift quota (三水) → report the
    # free quota instead of a useless "$0".
    if not bal or re.fullmatch(r"[$¥€￥]?\s*0(?:\.0+)?", bal or ""):
        gift, gift_raw = _find_gift_quota(body)
        if gift:
            bal, bal_raw = gift, gift_raw
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
    # Special archetype: Fengwind 类: "本次获得 $3.00"
    if not rew:
        m = re.search(r"(?:本次获得|获得奖励|获得额度|Received)\s*([$¥€￥]\s*\d+(?:[.,]\d+)?)", body)
        if m:
            rew, rew_raw = _money(m.group(1)), m.group(0)
    # Guard: a cumulative figure ("累计获得: N") is NOT today's reward.
    if rew and any(h in (rew_raw or "") for h in CUMULATIVE_HINTS):
        rew, rew_raw = None, None
    out["balance"] = bal
    out["reward"] = rew
    if bal_raw:
        out["evidence"] += "余额←%s " % bal_raw[:34]
    if rew_raw:
        out["evidence"] += "奖励←%s " % rew_raw[:34]

    # ---- check-in module not enabled? (preserve balance e.g. 君の星辰) ----
    if "签到功能未启用" in body or "未启用签到" in body:
        out["state"] = "unsupported"
        out["evidence"] += "站长后台未启用签到功能"
        return out

    # ---- captcha modal (graphical or slider)? (preserve balance e.g. 简直了 / PM-Plan) ----
    c_info = page.get("captcha") or {}
    if c_info.get("hasModal") or c_info.get("hasSlider"):
        out["state"] = "blocked_captcha"
        out["evidence"] += "弹出滑块验证码" if c_info.get("hasSlider") else "弹出图形验证码"
        return out

    # ---- done-ness ----
    ck_text = " ".join(_clean(h.get("txt", "")) for h in hits)

    # 真正弹出的 Toast 提示（如 Aether API 的 "You can only check in once per day"）
    # 与日历底部静态说明区分开：只有命中 toast 容器里的才算服务端明确回复
    has_toast_done = bool(re.search(
        r"Check-?in successful|签到成功|今日已打卡|明日再来|You can only check in once per day|Do not repeat check-in",
        toast_text, re.I
    ))
    if has_toast_done:
        out["state"] = "done"
        out["evidence"] += "Toast提示←" + toast_text[:34]
        return out

    # 同页同时存在「可点的动作按钮」和「Checked in / 已签到」字样时，按钮才是真相。
    # 2026-11-06 咕咕嘎嘎 / HappyCoding：卡片上常驻一句 "Checked in"（未签时也在 DOM 里），
    # 且 new-api 系日历底部有静态规则说明 "You can only check in once per day"。
    # 绝对不能把这些静态规则当作硬完成标记，否则会击穿动作按钮导致漏签！
    _action_btn = [
        h for h in hits
        if h.get("vis", True) and not h.get("disabled")
        and (
            re.search(r"立即签到|立即领取|立即打卡|去签到|签到领取|签到领|开始转动|转动|开始抽奖|Check in now|Check-in now",
                      _clean(h.get("txt", "")), re.I)
            or re.match(r"^(?:今日)?签到(?:\s*\+.*)?$|^Check[ -]?in$", _clean(h.get("txt", "")), re.I)
        )
        and not re.search(r"已签到|Checked in|已领取|nav|sidebar|tab|menu", (h.get("cls", "") + " " + _clean(h.get("txt", ""))), re.I)
    ]
    _hard_done = re.search(
        r"今日已签到|今日已领取|今日已打卡|明天\s*00:00|明日再来|已领取，明天再来",
        body, re.I)

    # 只要存在可见未禁用的动作按钮，且页面没有硬完成标志，必须判 pending
    if _action_btn and not _hard_done:
        out["state"] = "pending"
        out["evidence"] += "待签到动作按钮←" + _clean(_action_btn[0].get("txt", ""))[:28]
        return out

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
