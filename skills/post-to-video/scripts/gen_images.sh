#!/bin/bash
# post-to-video: 按 manifest 批量生图（3:4 竖版 / 4:3 横版 / 双封面），走 gen-img skill
#
# 规则来源（ai-news-factory 实战坑位 + 2026-09-21 2924762，详见 references/experience.md）：
# - 断点续跑：已存在且 >5KB 的文件跳过，只补缺失（整批超时后禁止无条件重跑）
# - quality：gpt-image-2 可 high；grok-imagine-image 只认 low/medium（硬编码 high 会整批失败）
# - size fallback：3:4 1024x1536→1152x1536；4:3 1536x1152→1536x1024（grok 常拒 1152）
# - 封面正片只许 vertical-3-4.png / horizontal-4-3.png；其它 covers/* 改写进 .scratch/
# - 单张失败重试；日志不打印任何 API Key
#
# 用法:
#   gen_images.sh <slug_dir> [manifest_file]
#
# manifest 每行: <相对输出路径>|<size>|<prompt 文本文件（相对 slug_dir，可省）>
#   images/scene1-3x4.png|1024x1536|prompts/scene1-3x4.txt
#   images/scene1-4x3.png|1536x1152|prompts/scene1-4x3.txt
#   covers/.scratch/vertical-notext.png|1024x1536|prompts/cover-v.txt
#   covers/.scratch/horizontal-notext.png|1536x1024|prompts/cover-h.txt

set -uo pipefail

SLUG_DIR="${1:?用法: $0 <slug_dir> [manifest_file]}"
MANIFEST="${2:-manifest.txt}"
SLUG_DIR="$(cd "$SLUG_DIR" && pwd)"
MANIFEST_PATH="${SLUG_DIR}/${MANIFEST}"

if [ ! -f "$MANIFEST_PATH" ]; then
  echo "错误: 找不到 manifest: $MANIFEST_PATH" >&2
  exit 1
fi

GEN_IMG_SH="${HOME}/.claude/skills/gen-img/scripts/gen-img.sh"
if [ ! -f "$GEN_IMG_SH" ]; then
  GEN_IMG_SH="${HOME}/Documents/learn-claude-code/skills/gen-img/scripts/gen-img.sh"
fi
if [ ! -f "$GEN_IMG_SH" ]; then
  echo "错误: 找不到 gen-img 脚本（系统与项目目录均无）" >&2
  exit 1
fi

# 只读 model 名，用于 quality 策略；禁止打印 key / url
MODEL_NAME="$(python3 -c "
import json, os
p = os.path.expanduser('~/.claude/settings.json')
try:
    env = json.load(open(p)).get('env', {})
    print(env.get('GEN_IMG_MODEL') or os.environ.get('GEN_IMG_MODEL') or '')
except Exception:
    print(os.environ.get('GEN_IMG_MODEL') or '')
" 2>/dev/null)"
MODEL_LC="$(printf '%s' "$MODEL_NAME" | tr '[:upper:]' '[:lower:]')"

qualities_for_model() {
  case "$MODEL_LC" in
    *grok*|*imagine*) echo "medium low" ;;
    *) echo "high medium" ;;
  esac
}

fallback_size() {
  case "$1" in
    1024x1536) echo "1152x1536" ;;
    1152x1536) echo "1024x1536" ;;
    1536x1152) echo "1536x1024" ;;
    1536x1024) echo "1536x1152" ;;
    *) echo "" ;;
  esac
}

# grok 实测 4:3 只认 1536x1024，首选直接改，避免先打一发必失败
prefer_size() {
  local size="$1"
  case "$MODEL_LC" in
    *grok*|*imagine*)
      if [ "$size" = "1536x1152" ]; then
        echo "1536x1024"
        return
      fi
      ;;
  esac
  echo "$size"
}

normalize_out_rel() {
  local rel="$1"
  case "$rel" in
    covers/vertical-3-4.png|covers/horizontal-4-3.png|covers/.scratch/*)
      echo "$rel"
      ;;
    covers/*)
      echo "covers/.scratch/$(basename "$rel")"
      ;;
    *)
      echo "$rel"
      ;;
  esac
}

call_gen() {
  local prompt="$1" out_path="$2" size="$3" quality="$4"
  # 吞掉 curl 噪声，但保留脚本退出码；不把响应（可能含鉴权）打到终端
  bash "$GEN_IMG_SH" "$prompt" "$out_path" "$size" "$quality" "1" "png"
}

gen_one() {
  local out_rel_in="$1" size_in="$2" prompt_file="$3"
  local out_rel size
  out_rel="$(normalize_out_rel "$out_rel_in")"
  if [ "$out_rel" != "$out_rel_in" ]; then
    echo "[info] 非正片封面改写到 .scratch: ${out_rel_in} → ${out_rel}"
  fi
  size="$(prefer_size "${size_in:-1024x1536}")"
  if [ "$size" != "${size_in:-}" ] && [ -n "${size_in:-}" ]; then
    echo "[info] ${out_rel} size ${size_in} → ${size}（当前 model 不认原尺寸）"
  fi

  local out_path="${SLUG_DIR}/${out_rel}"

  if [ -f "$out_path" ] && [ "$(stat -f%z "$out_path")" -gt 5120 ]; then
    echo "[skip] ${out_rel} 已存在 ($(stat -f%z "$out_path") bytes)"
    return 0
  fi

  local prompt
  if [ -n "$prompt_file" ] && [ -f "${SLUG_DIR}/${prompt_file}" ]; then
    prompt="$(cat "${SLUG_DIR}/${prompt_file}")"
  else
    prompt="$(basename "$out_rel" | sed 's/\.[^.]*$//')"
    echo "[warn] ${out_rel} 无 prompt 文件，用文件名兜底"
  fi

  mkdir -p "$(dirname "$out_path")"
  local quals size2 q s
  quals="$(qualities_for_model)"
  size2="$(fallback_size "$size")"

  for q in $quals; do
    for s in "$size" $size2; do
      [ -z "$s" ] && continue
      echo "[gen ] ${out_rel} (${s} / ${q})…"
      if call_gen "$prompt" "$out_path" "$s" "$q"; then
        if [ -f "$out_path" ] && [ "$(stat -f%z "$out_path")" -gt 5120 ]; then
          echo "[ ok ] ${out_rel} ($(stat -f%z "$out_path") bytes) size=${s} quality=${q}"
          return 0
        fi
        echo "[fail] ${out_rel} 产物缺失或过小" >&2
      else
        echo "[fail] ${out_rel} gen-img 退出码 $?  size=${s} quality=${q}" >&2
      fi
      rm -f "$out_path"
      sleep 2
    done
  done
  return 1
}

echo "[info] GEN_IMG_MODEL=${MODEL_NAME:-unknown}  quality=$(qualities_for_model)"
echo "[info] 合规：封面正片仅 vertical-3-4.png / horizontal-4-3.png（见 合规检查.md）"

FAILED=0
while IFS='|' read -r out_rel size prompt_file; do
  [ -z "${out_rel// /}" ] && continue
  case "$out_rel" in \#*) continue;; esac
  gen_one "$out_rel" "${size:-1024x1536}" "${prompt_file:-}" || FAILED=$((FAILED+1))
done < "$MANIFEST_PATH"

echo
if [ -d "${SLUG_DIR}/covers" ]; then
  extra="$(find "${SLUG_DIR}/covers" -maxdepth 1 -type f \( -name '*.png' -o -name '*.jpg' \) ! -name 'vertical-3-4.png' ! -name 'horizontal-4-3.png' 2>/dev/null | wc -l | tr -d ' ')"
  if [ "${extra:-0}" -gt 0 ]; then
    echo "[warn] covers/ 根目录有 ${extra} 张非正片，应移入 covers/.scratch/（正片只许两张）" >&2
  fi
fi

if [ "$FAILED" -gt 0 ]; then
  echo "=== 完成，${FAILED} 张失败 ===" >&2
  echo "失败处理：缩短对应 prompt 后重跑（已生成的会跳过）；仍失败换英文 prompt；再不行报告错误，不编造图片。" >&2
  echo "gpt-image-2 若报预扣费额度失败：改用 settings.json 备用 GEN_IMG_*_001（grok-imagine-image），禁止在日志打印 Key。" >&2
  exit 1
fi
echo "=== 全部生图完成 ==="
ls -la "${SLUG_DIR}/images" "${SLUG_DIR}/covers" 2>/dev/null || true
echo "封面无字底图请再跑: python3 $(dirname "$0")/overlay_cover_text.py --dir \"${SLUG_DIR}\" --both"
