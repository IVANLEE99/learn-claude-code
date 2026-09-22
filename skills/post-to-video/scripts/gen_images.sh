#!/bin/bash
# post-to-video: 按 manifest 批量生图（3:4 竖版 / 4:3 横版 / 双封面），走 gen-img skill
#
# 规则来源（ai-news-factory 实战坑位，详见 references/experience.md）：
# - 断点续跑：已存在且 >5KB 的文件跳过，只补缺失（整批超时后禁止无条件重跑）
# - 单张失败重试 1 次；日志不打印任何 API Key
#
# 用法:
#   gen_images.sh <slug_dir> [manifest_file]
#
# manifest 每行: <相对输出路径>|<size>|<prompt 文本文件（相对 slug_dir，可省）>
#   images/scene1-3x4.png|1024x1536|prompts/scene1-3x4.txt
#   images/scene1-4x3.png|1536x1152|prompts/scene1-4x3.txt
#   covers/vertical-3-4.png|1024x1536|prompts/cover-v.txt
#   covers/horizontal-4-3.png|1536x1152|prompts/cover-h.txt
# prompt 文件省略时，把输出文件名去扩展名作为 prompt（兜底，不推荐）。
#
# 尺寸对照（v3.35.0 实测）：
#   3:4 → 1024x1536（接口不认再 1152x1536）
#   4:3 → 1536x1152（接口不认再 1536x1024）

set -uo pipefail

SLUG_DIR="${1:?用法: $0 <slug_dir> [manifest_file]}"
MANIFEST="${2:-manifest.txt}"
SLUG_DIR="$(cd "$SLUG_DIR" && pwd)"
MANIFEST_PATH="${SLUG_DIR}/${MANIFEST}"

if [ ! -f "$MANIFEST_PATH" ]; then
  echo "错误: 找不到 manifest: $MANIFEST_PATH" >&2
  exit 1
fi

# gen-img 脚本定位：系统 skill 优先，项目目录兜底
GEN_IMG_SH="${HOME}/.claude/skills/gen-img/scripts/gen-img.sh"
if [ ! -f "$GEN_IMG_SH" ]; then
  GEN_IMG_SH="${HOME}/Documents/learn-claude-code/skills/gen-img/scripts/gen-img.sh"
fi
if [ ! -f "$GEN_IMG_SH" ]; then
  echo "错误: 找不到 gen-img 脚本（系统与项目目录均无）" >&2
  exit 1
fi

gen_one() {
  local out_rel="$1" size="$2" prompt_file="$3"
  local out_path="${SLUG_DIR}/${out_rel}"

  # 断点续跑：>5KB 视为成功，跳过（v3.11.0）
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
  for attempt in 1 2; do
    echo "[gen ] ${out_rel} (${size}) 第 ${attempt} 次…"
    if bash "$GEN_IMG_SH" "$prompt" "$out_path" "$size" "high" "1" "png"; then
      if [ -f "$out_path" ] && [ "$(stat -f%z "$out_path")" -gt 5120 ]; then
        echo "[ ok ] ${out_rel} ($(stat -f%z "$out_path") bytes)"
        return 0
      fi
      echo "[fail] ${out_rel} 产物缺失或过小" >&2
    else
      echo "[fail] ${out_rel} gen-img 退出码 $?" >&2
    fi
    sleep 2
  done
  return 1
}

FAILED=0
while IFS='|' read -r out_rel size prompt_file; do
  # 跳过空行与注释
  [ -z "${out_rel// /}" ] && continue
  case "$out_rel" in \#*) continue;; esac
  gen_one "$out_rel" "${size:-1024x1536}" "${prompt_file:-}" || FAILED=$((FAILED+1))
done < "$MANIFEST_PATH"

echo
if [ "$FAILED" -gt 0 ]; then
  echo "=== 完成，${FAILED} 张失败 ===" >&2
  echo "失败处理：缩短对应 prompt 后重跑本脚本（已生成的会自动跳过）；仍失败换英文 prompt；再不行报告错误，不编造图片。" >&2
  exit 1
fi
echo "=== 全部生图完成 ==="
ls -la "${SLUG_DIR}/images" "${SLUG_DIR}/covers" 2>/dev/null || true
