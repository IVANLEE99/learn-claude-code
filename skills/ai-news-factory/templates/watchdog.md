# 定时任务与看门狗模板（v3.80.0 / 1103 期实测）

> 用户明确要求：「任务执行后每 3 分钟检查一次任务是否正在跑，如果正在执行则跳过此次执行，如果任务中断则继续上次执行，直到任务成功。」
>
> 1103 实测：看门狗从 22:35 跑到 09:14（**10 小时 39 分**），日志只有 **4 行**（1102 同期写出 51 KB 噪声）。抓取链 413 帖 / 28 批 / err=0，一次跑完。

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
while [ "$(date '+%s')" -lt "$TARGET_EPOCH" ]; do sleep 30; done
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
