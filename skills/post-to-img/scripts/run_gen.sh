#!/bin/bash
# post-to-img: read prompt from slug dir and call gen-img
# 用法: run_gen.sh <slug_dir> [prompt_file]
# 例: run_gen.sh ~/Documents/learn-claude-code/generated-images/post-to-img/20260721_2609603

set -euo pipefail

SLUG_DIR="${1:?用法: $0 <slug_dir> [prompt_file]}"
PROMPT_FILE="${2:-prompt.txt}"
SLUG_DIR="$(cd "$SLUG_DIR" && pwd)"

PROMPT_PATH="${SLUG_DIR}/${PROMPT_FILE}"
META_PATH="${SLUG_DIR}/prompt.meta.json"
OUT_PATH="${SLUG_DIR}/poster.png"

if [ ! -f "$PROMPT_PATH" ]; then
  echo "错误: 找不到 prompt: $PROMPT_PATH" >&2
  exit 1
fi

SIZE="1536x1024"
QUALITY="high"
FORMAT="png"

if [ -f "$META_PATH" ]; then
  SIZE=$(python3 -c "import json;print(json.load(open('$META_PATH')).get('size','1536x1024'))")
  QUALITY=$(python3 -c "import json;print(json.load(open('$META_PATH')).get('quality','high'))")
  FORMAT=$(python3 -c "import json;print(json.load(open('$META_PATH')).get('format','png'))")
fi

# 若输出扩展名与 format 不一致则修正
OUT_PATH="${SLUG_DIR}/poster.${FORMAT}"

GEN_IMG_SH="${HOME}/.claude/skills/gen-img/scripts/gen-img.sh"
if [ ! -x "$GEN_IMG_SH" ]; then
  # fallback 项目目录
  GEN_IMG_SH="$(cd "$(dirname "$0")/../../gen-img/scripts" 2>/dev/null && pwd)/gen-img.sh" || true
fi
if [ ! -f "${HOME}/.claude/skills/gen-img/scripts/gen-img.sh" ]; then
  if [ -f "${HOME}/Documents/learn-claude-code/skills/gen-img/scripts/gen-img.sh" ]; then
    GEN_IMG_SH="${HOME}/Documents/learn-claude-code/skills/gen-img/scripts/gen-img.sh"
  fi
else
  GEN_IMG_SH="${HOME}/.claude/skills/gen-img/scripts/gen-img.sh"
fi

if [ ! -f "$GEN_IMG_SH" ]; then
  echo "错误: 找不到 gen-img.sh，请确认 gen-img skill 已安装" >&2
  exit 1
fi

# 通过 Python 安全读取 prompt，避免 shell 转义问题
export POST_TO_IMG_PROMPT_PATH="$PROMPT_PATH"
PROMPT=$(python3 -c "import os; print(open(os.environ['POST_TO_IMG_PROMPT_PATH'], encoding='utf-8').read())")

echo "=== post-to-img → gen-img ==="
echo "  slug: $SLUG_DIR"
echo "  prompt: $PROMPT_PATH (${#PROMPT} chars)"
echo "  out: $OUT_PATH"
echo "  size: $SIZE quality: $QUALITY"

bash "$GEN_IMG_SH" "$PROMPT" "$OUT_PATH" "$SIZE" "$QUALITY" "1" "$FORMAT"
