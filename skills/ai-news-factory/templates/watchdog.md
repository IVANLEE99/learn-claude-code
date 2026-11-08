# 定时任务与看门狗模板（v3.81.0 / 1104 期实测）

> 用户明确要求：「任务执行后每 3 分钟检查一次任务是否正在跑，如果正在执行则跳过此次执行，如果任务中断则继续上次执行，直到任务成功。」
>
> **1104 实测（本期）**：22:35:27 触发 → **23:07:22** 抓取+合并完成（**32 分钟**，372 帖 / 26 批 / err=0）→ 23:15 看门狗转 `READY_FOR_SESSION` → 04:33 会话收工 `touch 1104-DONE` → 下一次 tick 即 `verdict=DONE`，loop 自行退出。**看门狗全程日志 4 行。**
>
> 1103 实测：看门狗从 22:35 跑到 09:14（10 小时 39 分），日志 4 行（1102 同期 51 KB 噪声），抓取链 413 帖 / 28 批 / err=0。

## 0. 1104 新增的两条硬经验

**① 终态标记要「立刻生效」，不能等下一轮 180s。** 1104 收工时我手动跑了一次
`bash data/_watchdog_1104.sh`，它第一件事就命中 `DONE_MARK` 并输出 `verdict=DONE`，
接着 loop 在**同一次循环内**检测到标记并退出：

```
2026-11-04 04:36:19 VERDICT DONE action=terminal marker data/logs/1104-DONE present
===== watchdog loop 1104 end 2026-11-04 04:36:19 terminal marker =====
```

**② 触发后 40 分钟就要能看到 `READY_FOR_SESSION`。** 1104 的抓取窗口是 32 分钟，
23:07 合并完成、23:15 看门狗已切状态。**如果 60 分钟内还停在 `RUNNING`，先看 `crawl.log` 是否在增长，
而不是干等**——本期 burst 阶段从 22:35 到 23:07 每分钟约 1 批（15 帖）。

---

## 1. 架构：三层，各管一段

| 层 | 进程 | 职责 | 存活性 |
|---|---|---|---|
| **L1 launch wrapper** | `data/_launch_<issue>.sh`（常驻） | 睡到触发时刻 → 循环调 `_resume_<issue>.sh`（fetch→queue→crawl→merge）直到 `daily.total≥100` | `nohup` + `disown`，ppid=1 |
| **L2 看门狗 loop** | `data/_watchdog_<issue>_loop.sh`（常驻，180s） | 每 3 分钟跑一次单次判定 `_watchdog_<issue>.sh`，处理「在跑就跳过 / 断了就续跑」 | 同上；见到 `<issue>-DONE` 自行退出 |
| **L3 会话 cron** | `CronCreate`（session-only） | 只在会话活着且空闲时推进**会话型阶段**（report/press/PDF/视频/上传） | 会话结束即失效 |

**为什么必须分三层**：L1/L2 是纯 shell，不依赖 Claude 会话，**所以整夜无人也能把抓取跑完**。L3 只能做会话型工作，且历史证明 `CronCreate` 的 kickoff **屡次不触发**（10-03 / 10-04 / 10-11 / 1029 / 1030 / 1031）——**shell wrapper 才是主力，cron 只兜底**。

---

## 2. L1 launch wrapper 骨架

```bash
#!/bin/bash
# <issue> 期 launch wrapper：睡到 <trigger>，之后循环调 resume，直到 daily 达标。
set -u
cd /Users/youngsdream/Documents/learn-claude-code
mkdir -p data/logs
LOG=data/logs/<issue>-launch.log
PIDFILE=data/logs/<issue>-launch.pid

# pidfile 防重入
if [ -f "$PIDFILE" ]; then
  old=$(cat "$PIDFILE" 2>/dev/null || true)
  if [ -n "${old:-}" ] && kill -0 "$old" 2>/dev/null; then
    echo "launch wrapper already running pid $old" >&2; exit 0
  fi
fi
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT
exec >> "$LOG" 2>&1
echo "===== launch_<issue> start $(date '+%Y-%m-%d %H:%M:%S') pid=$$ ====="

# ---------- 1. 等触发时刻（墙钟，睡眠唤醒后自动追赶） ----------
TARGET_EPOCH=$(date -j -f '%Y-%m-%d %H:%M:%S' '<YYYY-MM-DD HH:MM:00>' '+%s')
# 坑422（v3.85.0）：pidfile 只在启动时检查一次 —— 反复试跑会留下多个 wrapper，
# 各自写 pidfile、各自睡到同一时刻，到点同时醒来抢跑（1106 实测残留 4 个）。
# 等待循环里必须每轮校验「pidfile 还指向我」，否则自行退出。
while [ "$(date '+%s')" -lt "$TARGET_EPOCH" ]; do
  [ "$(cat "$PIDFILE" 2>/dev/null)" = "$$" ] || { echo "superseded by $(cat "$PIDFILE" 2>/dev/null)"; exit 0; }
  sleep 30
done
echo "===== target reached $(date '+%Y-%m-%d %H:%M:%S') ====="

proxy_ok() { nc -z -w2 127.0.0.1 7897 >/dev/null 2>&1; }
profile_unlocked() { [ ! -e "$HOME/Library/Caches/ms-playwright-mcp/mcp-chrome-10b76e5/SingletonLock" ]; }

attempt=0
while true; do
  # ---------- 2. 收工判据 ----------
  if [ -f data/daily/<DATE>.json ]; then
    tot=$(python3 -c "import json;print(json.load(open('data/daily/<DATE>.json')).get('total',0))" 2>/dev/null || echo 0)
    if [ "${tot:-0}" -ge 100 ]; then
      echo "daily total=${tot} >= 100; done $(date '+%Y-%m-%d %H:%M:%S')"; exit 0
    fi
    echo "daily exists but total=${tot:-0} < 100 — NOT declaring done; 600s"
    sleep 600; continue
  fi
  # ---------- 3. 门禁 ----------
  if ! proxy_ok; then
    echo "GATE: proxy 7897 DOWN $(date '+%Y-%m-%d %H:%M:%S') — skip, 180s"; sleep 180; continue
  fi
  if ! profile_unlocked; then
    echo "GATE: crawl profile SingletonLock present $(date '+%Y-%m-%d %H:%M:%S') — skip, 180s"; sleep 180; continue
  fi
  # ---------- 4. 调 resume（内部 3 次尝试 + pidfile 防重入） ----------
  attempt=$((attempt+1))
  echo "--- attempt $attempt $(date '+%Y-%m-%d %H:%M:%S') ---"
  bash data/_resume_<issue>.sh; rc=$?
  echo "resume rc=$rc $(date '+%Y-%m-%d %H:%M:%S')"
  case "$rc" in
    0) sleep 10; continue ;;   # 自认完成 → 回顶部复核 daily
    2) echo "OFFICIAL WARNING — 停止重试，等用户决策"; exit 2 ;;
    3) echo "REFUSE REBUILD（batch 无对应 queue）— 数据完整性告警"; exit 3 ;;
    *) sleep 180; continue ;;  # 中断/失败 → 3 分钟后续跑
  esac
done
```

**`_resume_<issue>.sh` 的退出码约定**：

| rc | 含义 | wrapper 动作 |
|---|---|---|
| 0 | 本轮完成 | 回去复核 daily |
| 1 | 中断/失败 | 等 180s 再试 |
| 2 | 官方反自动化警告 | **停一切重试**，等用户 |
| 3 | batch 存在但 queue 缺失 | **拒绝重建**，数据完整性告警 |

---

## 3. L2 看门狗单次判定骨架

```bash
#!/bin/bash
# <issue> 期看门狗（单次执行即退出；由 loop 每 180s 唤起）
set -u
REPO=${WD_REPO:-/Users/youngsdream/Documents/learn-claude-code}
cd "$REPO" 2>/dev/null || { echo "REPO_UNREADABLE $REPO"; exit 1; }
mkdir -p data/logs

LOG=${WD_LOG:-$REPO/data/logs/<issue>-watchdog.log}
STATE=.pipeline-state-<DATE>.json
DONE_MARK=data/logs/<issue>-DONE
LAUNCH_PIDFILE=data/logs/<issue>-launch.pid
CRAWL_PIDFILE=data/logs/<issue>-crawl.pid
CRAWL_LOG=data/logs/<issue>-crawl.log
LAUNCH_LOG=data/logs/<issue>-launch.log
DAILY=data/daily/<DATE>.json
PDF=data/reports/<DATE>.pdf
VERDICT_FILE=data/logs/<issue>-watchdog.verdict
TRIGGER_EPOCH=$(date -j -f '%Y-%m-%d %H:%M:%S' '<YYYY-MM-DD HH:MM:00>' '+%s')
DEDUP_WINDOW=${WD_DEDUP:-1800}

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }

# ---------- 判定输出：30 分钟内同判定不重复写日志 ----------
emit() {
  local verdict="$1" action="$2" now last_ts prev_body new_body same age
  now=$(date '+%s'); same=0; last_ts=0
  if [ -f "$VERDICT_FILE" ]; then
    last_ts=$(head -1 "$VERDICT_FILE" | sed 's/^ts=//')
    case "${last_ts:-}" in ''|*[!0-9]*) last_ts=0 ;; esac
    prev_body=$(tail -n +2 "$VERDICT_FILE")
    new_body="verdict=$verdict
action=$action"
    [ "$prev_body" = "$new_body" ] && same=1
  fi
  age=$(( now - last_ts ))
  { echo "ts=$now"; echo "verdict=$verdict"; echo "action=$action"; } > "$VERDICT_FILE"
  if [ "$same" = "1" ] && [ "$age" -lt "$DEDUP_WINDOW" ]; then return 0; fi
  log "VERDICT $verdict action=$action"
}

# ---------- alive：pidfile + cmdline 双校验（防 pid 复用） ----------
alive() {
  local f="$1" pat="$2" pid
  [ -f "$f" ] || return 1
  pid=$(cat "$f" 2>/dev/null || true)
  case "${pid:-}" in ''|*[!0-9]*) return 1 ;; esac
  kill -0 "$pid" 2>/dev/null || return 1
  ps -p "$pid" -o command= 2>/dev/null | grep -q "$pat" || return 1
  return 0
}

start_launcher() { nohup bash data/_launch_<issue>.sh >/dev/null 2>&1 & disown 2>/dev/null || true; }
daily_total() { [ -f "$DAILY" ] && python3 -c "import json;print(json.load(open('$DAILY')).get('total',0))" 2>/dev/null || echo 0; }
stages_left() { # state 里未 done/skipped 的 stage；state=done 输出 done
  [ -f "$STATE" ] || { echo no_state; return; }
  python3 - "$STATE" <<'PY' 2>/dev/null || echo parse_error
import json, sys
try: d = json.load(open(sys.argv[1]))
except Exception: print('parse_error'); raise SystemExit
st = d.get('stages') or {}
left = [k for k, v in st.items() if (v or {}).get('status') not in ('done', 'skipped', 'skipped_by_user')]
if d.get('state') == 'done' and not left: print('done')
elif d.get('state') == 'done': print('todo:' + ','.join(left))
else: print(str(d.get('state','?')) + (':' + ','.join(left) if left else ''))
PY
}

# ═══════════ 判定顺序（先做完的先判） ═══════════
# 0. 终态
[ -f "$DONE_MARK" ] && { emit DONE "terminal marker present"; exit 0; }
[ "$(stages_left)" = "done" ] && { emit DONE "state=done"; exit 0; }

# 1. 触发前：不抓取，但确保 wrapper 常驻（wrapper 自有时刻门禁）
if [ "$(date '+%s')" -lt "$TRIGGER_EPOCH" ]; then
  if alive "$LAUNCH_PIDFILE" _launch_<issue>.sh; then
    emit GUARD "pre-trigger — wrapper pid $(cat "$LAUNCH_PIDFILE") armed"
  else
    start_launcher; sleep 2
    emit GUARD "pre-trigger — wrapper missing, restarted pid $(cat "$LAUNCH_PIDFILE" 2>/dev/null || echo '?')"
  fi
  exit 0
fi

# 2. ★ 先拦「看着在跑、其实永远跑不完」（坑 406）
if [ -f "$DAILY" ] && [ -f "$LAUNCH_LOG" ] \
   && grep -q "daily exists but total=" "$LAUNCH_LOG" 2>/dev/null \
   && [ -n "$(find "$LAUNCH_LOG" -mmin -21 2>/dev/null)" ]; then
  tot0=$(daily_total)
  [ "${tot0:-0}" -lt 100 ] && { emit ALERT "daily total=${tot0} < 100 且 wrapper 在 600s 空转（疑似 CF 拦截）— 须会话介入"; exit 0; }
fi

# 3. 正在执行 → 跳过
alive "$LAUNCH_PIDFILE" _launch_<issue>.sh && { emit RUNNING "skip (launch pid $(cat "$LAUNCH_PIDFILE"))"; exit 0; }
alive "$CRAWL_PIDFILE" _resume_<issue>.sh    && { emit RUNNING "skip (crawl pid $(cat "$CRAWL_PIDFILE"))"; exit 0; }
[ -f "$CRAWL_LOG" ] && [ -n "$(find "$CRAWL_LOG" -mmin -5 2>/dev/null)" ] && { emit RUNNING "skip (crawl.log <5min)"; exit 0; }
[ -f "$LAUNCH_LOG" ] && [ -n "$(find "$LAUNCH_LOG" -mmin -5 2>/dev/null)" ] && { emit RUNNING "skip (launch.log <5min)"; exit 0; }

# 4. 中断 → 续跑
tot=$(daily_total)
if [ ! -f "$DAILY" ] || [ "${tot:-0}" -lt 100 ]; then
  log "RESUME crawl chain"
  start_launcher; sleep 2
  emit RESUME "wrapper restarted (daily=$( [ -f "$DAILY" ] && echo "total=$tot" || echo missing ))"
  exit 0
fi

# 5. daily 就绪：会话型阶段只报状态
left=$(stages_left)
if [ -f "$PDF" ]; then
  probe=$(python3 data/_probe_genimg_<issue>.py 2>&1 | tail -1)
  case "$probe" in
    PROBE_OK*|PROBE_FIXED*) probe_tag=genimg=ok ;;
    *) probe_tag="genimg=NEEDS_ATTENTION" ;;
  esac
  emit READY_FOR_SESSION "daily=$tot pdf=yes stages=$left $probe_tag -> session runs video + uploads"
else
  emit READY_FOR_SESSION "daily=$tot pdf=pending stages=$left -> session writes report/press/PDF first"
fi
exit 0
```

---

## 4. L2 loop 骨架

```bash
#!/bin/bash
# 每 180 秒跑一次单次判定，见到终态标记/state=done 自行退出
set -u
cd /Users/youngsdream/Documents/learn-claude-code || exit 1
mkdir -p data/logs
PIDFILE=data/logs/<issue>-watchdog-loop.pid
LOG=data/logs/<issue>-watchdog.log

if [ -f "$PIDFILE" ]; then
  old=$(cat "$PIDFILE" 2>/dev/null || true)
  case "${old:-}" in
    ''|*[!0-9]*) : ;;
    *) if kill -0 "$old" 2>/dev/null && ps -p "$old" -o command= 2>/dev/null | grep -q _watchdog_<issue>_loop.sh; then
         echo "already running pid $old"; exit 0; fi ;;
  esac
fi
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT
echo "===== watchdog loop start $(date '+%Y-%m-%d %H:%M:%S') pid=$$ =====" >> "$LOG"

while true; do
  bash data/_watchdog_<issue>.sh
  [ -f data/logs/<issue>-DONE ] && { echo "===== loop end (DONE) $(date '+%Y-%m-%d %H:%M:%S') =====" >> "$LOG"; exit 0; }
  python3 -c "import json,sys;d=json.load(open('.pipeline-state-<DATE>.json'));sys.exit(0 if d.get('state')=='done' else 1)" 2>/dev/null \
    && { echo "===== loop end (state=done) $(date '+%Y-%m-%d %H:%M:%S') =====" >> "$LOG"; exit 0; }
  sleep 180
done
```

---

## 5. 启动与验证（每次都照这个跑）

```bash
cd /Users/youngsdream/Documents/learn-claude-code

# 启动（顺序无所谓，两者都幂等）
nohup bash data/_launch_<issue>.sh        >/dev/null 2>&1 &
disown 2>/dev/null || true
nohup bash data/_watchdog_<issue>_loop.sh >/dev/null 2>&1 &
disown 2>/dev/null || true

sleep 5
# 验证 ①：两个进程都活着，且 ppid=1（脱离终端）
for f in data/logs/<issue>-launch.pid data/logs/<issue>-watchdog-loop.pid; do
  pid=$(cat "$f" 2>/dev/null)
  kill -0 "$pid" 2>/dev/null && echo "OK $f pid=$pid ppid=$(ps -p $pid -o ppid=)" || echo "DEAD $f"
done

# 验证 ②：判定文件已生成
cat data/logs/<issue>-watchdog.verdict

# 验证 ③：日志只有 1-2 行（去重生效）
wc -l data/logs/<issue>-watchdog.log
```

**自愈演练（建议在触发前做一次）**：

```bash
kill $(cat data/logs/<issue>-launch.pid)   # 杀掉 wrapper
sleep 2
bash data/_watchdog_<issue>.sh             # 看门狗应判 RESUME 并重新拉起
cat data/logs/<issue>-watchdog.verdict    # 期望 verdict=RESUME
cat data/logs/<issue>-launch.pid           # 新 pid，且 kill -0 通过
```

---

## 6. 沙箱验证判定分支（改完看门狗必做）

改动判定逻辑后，**不要直接在真仓库上试**。复制到 `/tmp` 改 `REPO` 与 `TRIGGER_EPOCH`（改成「100 秒前」），逐条验：

```bash
T=/tmp/wd<issue>; mkdir -p $T/data/logs $T/data/daily $T/data/reports
sed -e "s#^REPO=\${WD_REPO:-.*}#REPO=$T#" \
    -e "s#^TRIGGER_EPOCH=.*#TRIGGER_EPOCH=\$(( \$(date +%s) - 100 ))#" \
    data/_watchdog_<issue>.sh > $T/wd.sh

# 造一个假 wrapper
cat > $T/data/_launch_<issue>.sh <<'EOF'
#!/bin/bash
echo $$ > /tmp/wd<issue>/data/logs/<issue>-launch.pid
trap 'rm -f /tmp/wd<issue>/data/logs/<issue>-launch.pid' EXIT
while true; do sleep 5; done
EOF
chmod +x $T/data/_launch_<issue>.sh
```

| # | 前置条件 | 期望 verdict |
|---|---|---|
| 1 | 触发前（TRIGGER 在未来），wrapper 活着 | `GUARD` |
| 2 | 触发后，无 wrapper、无 daily | `RESUME` |
| 3 | wrapper 活着、无 daily | `RUNNING` |
| 4 | daily total=42 + launch.log 刚写过空转行 | `ALERT` |
| 5 | 同上，但 launch.log 已 30 分钟未写 | `RUNNING` |
| 6 | daily total≥100、无 PDF | `READY_FOR_SESSION`（pdf=pending） |
| 7 | daily + PDF 都在 | `READY_FOR_SESSION`（pdf=yes） |
| 8 | `<issue>-DONE` 存在 | `DONE` |
| 9 | 无 marker，但 state=done 且 stages 全 done | `DONE` |
| 10 | state=scheduled 且有 pending stage | 不是 `DONE` |
| 11 | crawl pid 活、`crawl.log` 31 分钟无新行、Chrome History 最后导航 31 分钟前 | `ALERT`（crawl stalled） |

**验完记得清理沙箱进程**：`pkill -f "$T/data/_launch_<issue>.sh"`。

---

## 7. 已知边界（必须如实告诉用户）

| 边界 | 影响 | 缓解 |
|---|---|---|
| L1/L2 都是 `nohup` 进程 | 机器重启后消失 | 重跑两条 `nohup` 命令；脚本幂等 |
| launchd 形态不可用 | 1102 实测：launchd 读 `~/Documents` 被 TCC 拒绝（`exit 126 Operation not permitted`），`/bin/bash -c` 同样 `Permission denied` | **不要再用 launchd**，只用会话内 `nohup` |
| 电池态 `sleep 1` | 合盖会睡过触发时刻 | 提醒用户接电源；AC 电源 `sleep 0` 无此问题 |
| L3 cron 是 session-only | 会话结束即失效 | shell wrapper 是主力；cron 只兜底 |
| 陈旧的 `SingletonLock` | wrapper 永久卡门禁，日志刷 `GATE:` **看起来像在干活** | 看门狗应把连续 GATE 也计入告警（见 §8） |

---

## 8. 可选增强：GATE 卡死检测

`SingletonLock` 陈旧时 wrapper 会无限刷 `GATE: crawl profile SingletonLock present`，`alive` 恒真 → 看门狗报 `RUNNING`。加一条：

```bash
# 连续 GATE 超过 30 分钟 → ALERT
if [ -f "$LAUNCH_LOG" ] && [ -n "$(find "$LAUNCH_LOG" -mmin -6 2>/dev/null)" ] \
   && [ "$(grep -c '^GATE:' "$LAUNCH_LOG")" -ge 5 ]; then
  last_gate=$(grep '^GATE:' "$LAUNCH_LOG" | tail -1)
  # 只看最近 30 分钟内的 GATE
  if [ -n "$(find "$LAUNCH_LOG" -mmin -6 2>/dev/null)" ]; then
    emit ALERT "wrapper 连续 GATE（疑似陈旧 SingletonLock）: ${last_gate:0:80}"
    exit 0
  fi
fi
```

**人工解封**：确认没有抓取进程在跑后，`rm` 掉 `~/Library/Caches/ms-playwright-mcp/mcp-chrome-10b76e5/SingletonLock`（**先 `ps aux | grep mcp-chrome-10b76e5` 确认无进程持有**）。注意这是**抓取 profile**，不是上传 daemon 的 `ms-playwright/mcp-chrome-10b76e5`——两者差一个 `-mcp`，别搞错。

---

## 9. crawl stalled 检测（v3.84.0 新增，1106 实测）

**现象：wrapper pid 存活 → 看门狗恒报 `RUNNING`，实际 node 已卡死在 `page.evaluate`。** 1106 期 00:05 介入时：`crawl.log` 最后一行是 `batch 12/27 已保存...`（已 60 分钟无新行），Chrome History 最后导航 `2026-11-05 23:02:43`（60 分钟前），node 32942 `STAT=SN`、`%CPU 0.0`、阻塞在 `kevent`，renderer 60603 CPU time 仅 `0:00.20`（evaluate 从未返回）。既有两条判据都抓不到：§3 的 `find "$CRAWL_LOG" -mmin -5` 只证明「文件最近没写」，而 `alive "$CRAWL_PIDFILE"` 恒真 → 直接跳 `RUNNING`。**必须把「crawl.log 陈旧 + Chrome 无新导航」交叉成第三条判据。**

**单次判定新增分支（插在 §3「正在执行 → 跳过」的 `alive "$LAUNCH_PIDFILE"` 之前；三真才判，缺一不可）**：

```bash
# 3b. ★ crawl stalled：crawl pid 活着，但 30 分钟没有新行 + Chrome 没有新导航
if alive "$CRAWL_PIDFILE" _resume_<issue>.sh; then
  CHROME_HIST="$HOME/Library/Caches/ms-playwright-mcp/mcp-chrome-10b76e5/Default/History"
  HIST_TS=""
  if [ -f "$CHROME_HIST" ]; then
    cp "$CHROME_HIST" /tmp/h_<issue>.db 2>/dev/null      # 原库被 Chrome 锁住，必须复制
    HIST_TS=$(sqlite3 /tmp/h_<issue>.db \
      "select datetime(max(last_visit_time)/1000000-11644473600,'unixepoch','localtime') from urls" 2>/dev/null)
  fi
  if [ -n "$(find "$CRAWL_LOG" -mmin +30 2>/dev/null)" ] && [ -n "$HIST_TS" ]; then
    hist_epoch=$(date -j -f '%Y-%m-%d %H:%M:%S' "$HIST_TS" '+%s' 2>/dev/null || echo 0)
    if [ "$hist_epoch" -gt 0 ] && [ "$hist_epoch" -lt "$(( $(date '+%s') - 1800 ))" ]; then
      emit ALERT "crawl stalled: crawl.log 30min+ 无新行，Chrome last nav=${HIST_TS}，node pid=$(cat "$CRAWL_PIDFILE") 疑似 page.evaluate 卡死"
      exit 0
    fi
  fi
fi
```

**Chrome History 查询法**（SQLite 的修饰符必须带引号，裸写 `unixepoch` 会报 `no such column: unixepoch`）：

```bash
cp ~/Library/Caches/ms-playwright-mcp/mcp-chrome-10b76e5/Default/History /tmp/h.db
sqlite3 /tmp/h.db "select datetime(max(last_visit_time)/1000000-11644473600,'unixepoch','localtime') from urls"
```

**处置顺序（1106 实测一次恢复，别跳步）**：

1. 先归档该窗口内 node 抢写的全 error batch——1106 在浏览器被 kill 后，node 迅速写出 `batch14/15` 两条 15/15 err 的假批；若不归档，`_resume` 的 `isComplete()` 会把它们当成「已完成」跳过（归档到 `data/archive/`）。
2. `kill -TERM <node_pid>`；1106 实测 TERM 被忽略，必须补 `kill -KILL`。
3. kill 抓取 Chrome 进程树：`pkill -f 'ms-playwright-mcp/mcp-chrome-10b76e5'`（**带 `-mcp` 的那个 profile**；上传 daemon 是 `ms-playwright/mcp-chrome-10b76e5`，别误杀）。
4. 让 `_resume_<issue>.sh` 从当前批重抓：1106 的 batch13 在 kill 前已落盘 `n=15 valid=14 err=1`，`_resume` 按 `isComplete` 跳过 0-12、重抓 batch13，新 node 26500 + 新 Chrome（12 进程）恢复。

**沙箱用例（§6 表第 11 行）**：把 `crawl.log` 的 mtime 改成 31 分钟前、`CRAWL_PIDFILE` 指向一个 `sleep 300` 伪进程、Chrome History 用一份 31 分钟前的副本 → 期望唯一输出 `ALERT "crawl stalled..."`。门限是 `-mmin +30`，31 分钟才命中；30 分钟内仍应走 `RUNNING`。


---

## 10. 多 wrapper 并存与「归属校验」（v3.85.0 新增，坑 422，1107 实测）

`_launch_<issue>.sh` 的 pidfile 检查是**一次性**的（启动瞬间）。1106 上午为了试跑反复 `nohup bash data/_launch_1106.sh`，
留下了 **4 个** 进程：每个都通过了「pidfile 不存在或进程已死」的检查 → 每个都覆写 pidfile → 每个都进入
`while ... sleep 30` 睡到同一个 22:35。到点时 4 个同时醒来调 `_resume_<issue>.sh`。

本期没出事**纯属侥幸**：`_resume` 自己也有 pidfile，后到的 3 个直接被 `already running` 挡掉。
但若第一个 fail 得够快（例如 auth 失败），另外 3 个会依次接手并各自重试，很容易把「失败一次」放大成**三次全量重抓**。

**派生器加固（必须写进 `_launch_<issue>.sh` 的等待循环）**：

```bash
while [ "$(date '+%s')" -lt "$TARGET_EPOCH" ]; do
  [ "$(cat "$PIDFILE" 2>/dev/null)" = "$$" ] || { echo "superseded by $(cat "$PIDFILE" 2>/dev/null)"; exit 0; }
  sleep 30
done
```

**开工前自检**：

```bash
pgrep -fl "_launch_<issue>.sh" | wc -l     # 期望 1（或 0=尚未启动）；>1 立即 kill 多余进程
ps -o pid,ppid,etime,command -p $(cat data/logs/<issue>-launch.pid)
```

**收工后**（DONE 已写、loop 已退）顺手清理：

```bash
for p in $(pgrep -f "_launch_<issue>.sh"); do
  case "$(ps -p "$p" -o command=)" in *data/_launch_<issue>.sh*) kill "$p" && echo "killed $p";; esac
done
```

---

## 11. `connect_over_cdp` 超时的固定处置（v3.85.0 新增，坑 421，1107 两次实测）

症状：ws **已经连上**（日志里出现 `ws connected`），但 30 s 后抛 `BrowserType.connect_over_cdp: Timeout 30000ms exceeded`。

**固定顺序，不要跳步、不要重启浏览器**：

```bash
curl -s --max-time 8 http://127.0.0.1:9222/json/version     # 有 JSON = daemon 活着
python3 templates/revive_frozen_tabs.py                     # 末行 PLAYWRIGHT_OK 即可；DEAD: 是正常的
# 然后重跑原脚本
```

1107 实测：两次超时都是跑一次 `revive_frozen_tabs.py`（第一次 `DEAD 1 → revived 1`，第二次 `DEAD 2 → revived 2`）
之后立即恢复。**不要因为 ws 连上就判定「浏览器没问题」**——冻结的是 tab，不是 daemon。

**已知副作用**：revive 会把冻结的 tab 重新导航，长驻的 `mp` home 标签可能因此被关掉、`token` 变化。
下个脚本若报 `mp home tab not found`，按坑 403 用 `PUT /json/new?<home+token>` 补一个，
**登录态（cookie）不受影响**，不需要重新扫码。

## 12. 看门狗日志「只在状态变化时写」（v3.85.0 复核）

1107 全程看门狗日志**只有 4 行**（start / GUARD / READY / DONE），而 1102 同期写了 51 KB。差异全部来自 `emit()` 的
「同串 + `DEDUP_WINDOW` 内不重复」逻辑。派生时**不要**为了「看得到心跳」去掉去重——
排查靠 `data/logs/<issue>-watchdog.verdict`（每次 tick 都覆写），不是靠日志行数。
