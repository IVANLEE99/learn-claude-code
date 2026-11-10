#!/bin/bash
# 新机 / 换机后的环境自检（ai-news-factory v3.87.0 坑 431）
#
# 用法：bash templates/env-preflight.sh [YYYY-MM-DD]
# 退出码：0 = 全通过；非 0 = 有 FAIL，先把环境修好再开流水线
#
# 背景：1110 期在一台新机上跑，踩到 6 处环境缺失（ffmpeg / edge-tts / faster-whisper /
# jieba / playwright / av 兼容），每一处都是跑到一半才炸。这个脚本把它们前置成一次检查。

set -u
DATE="${1:-$(date '+%Y-%m-%d')}"
FAIL=0
WARN=0

# 流水线必须用的解释器：python.org 3.14（--user 包装在这里）
PY="${PIPELINE_PY:-/Library/Frameworks/Python.framework/Versions/3.14/bin/python3}"

say() { printf '%s %s\n' "$1" "$2"; }
ok()   { say "✅" "$1"; }
bad()  { say "❌" "$1"; FAIL=$((FAIL+1)); }
warn() { say "⚠️ " "$1"; WARN=$((WARN+1)); }

echo "=== 环境自检 ($(date '+%Y-%m-%d %H:%M:%S')) DATE=$DATE ==="

# ---------- 1. Python 解释器与依赖 ----------
if [ -x "$PY" ]; then
  ok "pipeline python: $PY ($($PY -V 2>&1))"
else
  bad "pipeline python 不存在: $PY（用 PIPELINE_PY=... 覆盖）"
fi

if [ -x "$PY" ]; then
  MISSING=$("$PY" - <<'EOF'
import importlib.util, sys
need = ['PIL', 'jieba', 'faster_whisper', 'playwright', 'av']
sys.stdout.write(','.join(m for m in need if not importlib.util.find_spec(m)))
EOF
)
  if [ -z "$MISSING" ]; then
    ok "python deps: PIL / jieba / faster_whisper / playwright / av 全部可用"
  else
    bad "python deps 缺失: $MISSING  →  $PY -m pip install --user ${MISSING//,/ }"
  fi
fi

# ---------- 2. ffmpeg / ffprobe ----------
for b in ffmpeg ffprobe; do
  if command -v "$b" >/dev/null 2>&1; then
    ok "$b: $(command -v $b)"
  else
    bad "$b 缺失  →  brew install ffmpeg（或把某处静态版加进 PATH）"
  fi
done

# ---------- 3. ffmpeg 字幕滤镜（决定烧字幕还是 PIL overlay） ----------
if command -v ffmpeg >/dev/null 2>&1; then
  N=$(ffmpeg -hide_banner -filters 2>/dev/null | grep -cwE "ass|subtitles|drawtext" || true)
  if [ "${N:-0}" -gt 0 ]; then
    ok "ffmpeg 字幕滤镜可用（$N 个）→ 可直接 -vf ass="
  else
    warn "ffmpeg 无 ass/subtitles/drawtext → 必须走 templates/ffmpeg-fallback-compose.md 的 PIL overlay 路径"
  fi
fi

# ---------- 4. edge-tts ----------
if command -v edge-tts >/dev/null 2>&1; then
  V=$(edge-tts --version 2>&1 | head -1)
  case "$V" in
    *7.[3-9].*|*[89].*) ok "edge-tts: $V" ;;
    *) warn "edge-tts 版本偏低（$V）→ 7.3.1 以下会稳定 403，pip install -U edge-tts" ;;
  esac
else
  bad "edge-tts 缺失  →  $PY -m pip install --user 'edge-tts>=7.3.1'（装到 ~/Library/Python/3.14/bin）"
fi

# ---------- 5. node ≥ 18 ----------
if command -v node >/dev/null 2>&1; then
  NODE_MAJOR=$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)
  if [ "${NODE_MAJOR:-0}" -ge 18 ]; then
    ok "node v$(node -v | tr -d v)（≥18）"
  else
    bad "node v$(node -v) < 18 → 抓取脚本会报 'Playwright requires Node.js 18 or higher'（nvm use 20+ 并在脚本里注入 PATH）"
  fi
else
  bad "node 缺失 → 抓取链跑不起来（nvm install 20+）"
fi

# ---------- 6. playwright-core（Node 侧，抓取用） ----------
if command -v npm >/dev/null 2>&1; then
  GLOBAL_ROOT=$(npm root -g 2>/dev/null || true)
  if [ -n "$GLOBAL_ROOT" ] && [ -f "$GLOBAL_ROOT/playwright-core/package.json" ]; then
    PWV=$("$PY" -c "import json;print(json.load(open('$GLOBAL_ROOT/playwright-core/package.json'))['version'])" 2>/dev/null || echo '?')
    ok "playwright-core(npm global): $PWV  @ $GLOBAL_ROOT"
  else
    bad "playwright-core 未全局安装 → npm i -g playwright-core（版本要与本机 chromium revision 对齐）"
  fi
fi

# ---------- 7. chromium 缓存（版本必须与 playwright-core 对齐） ----------
CHROME_BASE="$HOME/Library/Caches/ms-playwright"
if [ -d "$CHROME_BASE" ]; then
  CAND=$(ls -d "$CHROME_BASE"/chromium-[0-9]* 2>/dev/null | sort -V | tail -1)
  if [ -n "${CAND:-}" ]; then
    ok "chromium 缓存: $(basename "$CAND")"
    REV=$(basename "$CAND" | sed 's/chromium-//')
    if command -v node >/dev/null 2>&1 && [ -n "${GLOBAL_ROOT:-}" ]; then
      WANT=$(node -e "const b=require('$GLOBAL_ROOT/playwright-core/browsers.json').browsers;const c=b.find(x=>x.name==='chromium');console.log(c.revision)" 2>/dev/null || echo '?')
      if [ "$WANT" = "$REV" ]; then
        ok "chromium revision 对齐（playwright-core 要 $WANT = 本机 $REV）"
      else
        bad "chromium revision 不匹配：playwright-core 要 $WANT，本机是 $REV → 换 playwright-core 版本或 playwright install chromium"
      fi
    fi
  else
    bad "无 chromium 缓存 → npx playwright install chromium"
  fi
else
  bad "$CHROME_BASE 不存在 → npx playwright install chromium"
fi

# ---------- 8. 上传 daemon profile ----------
PROFILE=$(ls -d "$HOME"/Library/Caches/ms-playwright*/mcp-chrome-* 2>/dev/null | head -1)
if [ -n "${PROFILE:-}" ]; then
  ok "上传 daemon profile: $PROFILE"
else
  bad "找不到 mcp-chrome-* profile → 上传链没有登录态（先手动登录一次各平台）"
fi

# ---------- 9. 上传 daemon 是否在跑 ----------
if command -v curl >/dev/null 2>&1; then
  if curl -s --max-time 6 http://127.0.0.1:9222/json/version >/dev/null 2>&1; then
    ok "CDP 9222 daemon 在线"
  else
    warn "CDP 9222 未监听 → 上传前需 nohup python3 templates/browser_daemon.py &（视频链不需要它）"
  fi
fi

# ---------- 10. Remotion compositor 可用性（决定视频链走哪条路） ----------
VP="${VIDEO_PROJECT:-news-pipeline/video-project}"
COMPDIR="$VP/node_modules/@remotion/compositor-darwin-arm64"
COMP="$COMPDIR/remotion"
if [ -x "$COMP" ]; then
  # 🔴 必须带 DYLD_LIBRARY_PATH 指向同目录，否则会报
  #    "Library not loaded: libavcodec.dylib"（compositor 依赖同目录的 7 个 dylib），
  #    这既不是"可用"也不是"OS 不兼容"，只是加载路径没给。
  # 三种结果要分开判：
  #   VERSION_OK  → 真可用
  #   LIB_MISSING → 只是没给 DYLD_LIBRARY_PATH，带路径再试
  #   TIMEOUT/空  → 二进制与本机 OS 不兼容（坑 427），必须走 ffmpeg 兜底
  probe() {
    local out
    out=$( ( DYLD_LIBRARY_PATH="$COMPDIR" "$COMP" --version < /dev/null 2>&1 & CPID=$!
             for _ in $(seq 1 10); do
               kill -0 "$CPID" 2>/dev/null || break
               sleep 0.5
             done
             if kill -0 "$CPID" 2>/dev/null; then kill -9 "$CPID" 2>/dev/null; echo "__TIMEOUT__"; fi
             wait "$CPID" 2>/dev/null ) 2>&1 | head -2 | tr '\n' ' ' )
    printf '%s' "$out"
  }
  OUT=$(probe)
  case "$OUT" in
    *__TIMEOUT__*|"")
      warn "remotion compositor 5s 内无响应（坑 427：SDK 26 二进制跑在 macOS 14 / dyld 未启动）→ 视频链改走 templates/ffmpeg-fallback-compose.md"
      ;;
    *"Library not loaded"*)
      warn "remotion compositor 缺 dylib（需 DYLD_LIBRARY_PATH=$COMPDIR）→ 脚本里显式设置后再试；仍失败则走 ffmpeg 兜底"
      ;;
    *[0-9].[0-9]*)
      ok "remotion compositor 可用: $(printf '%s' "$OUT" | cut -c1-60)"
      ;;
    *)
      warn "remotion compositor 输出异常: $(printf '%s' "$OUT" | cut -c1-80) → 走 ffmpeg 兜底"
      ;;
  esac
else
  warn "找不到 compositor（$COMP）→ 若要用 Remotion 先 npm ci；否则直接走 ffmpeg 兜底"
fi

# ---------- 11. 字体（PIL 字幕/封面用） ----------
for f in "/System/Library/Fonts/PingFang.ttc" "/System/Library/Fonts/Hiragino Sans GB.ttc"; do
  [ -f "$f" ] && ok "字体: $(basename "$f")" || warn "字体缺失: $f"
done

echo
echo "=== 结果：FAIL=$FAIL  WARN=$WARN ==="
if [ "$FAIL" -gt 0 ]; then
  echo "有 $FAIL 项硬失败，先修环境再开流水线。"
  exit 1
fi
if [ "$WARN" -gt 0 ]; then
  echo "无硬失败，但 $WARN 条警告决定了链路走法（字幕/视频合成），照提示选路径。"
fi
echo "环境自检通过。"
exit 0
