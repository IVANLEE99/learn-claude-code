#!/bin/bash
# GPT-Image 图片生成脚本
# 用法: ./generate-image.sh "图片描述" [output.png] [size]

set -euo pipefail

PROMPT="${1:?用法: $0 \"prompt\" [output] [size]}"
OUTPUT="${2:-output-$(date +%s).png}"
SIZE="${3:-1024x1024}"

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "错误: 请先设置 OPENAI_API_KEY 环境变量"
  exit 1
fi

echo "正在生成图片..."
RESPONSE=$(curl -s https://api.openai.com/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d "$(cat <<EOF
{
  "model": "gpt-image-1",
  "prompt": "$PROMPT",
  "n": 1,
  "size": "$SIZE",
  "quality": "medium"
}
EOF
)")

# 提取 base64 数据并保存为图片
echo "$RESPONSE" | python3 -c "
import sys, json, base64
data = json.load(sys.stdin)
if 'error' in data:
    print(f\"API 错误: {data['error']['message']}\", file=sys.stderr)
    sys.exit(1)
img_b64 = data['data'][0]['b64_json']
with open('$OUTPUT', 'wb') as f:
    f.write(base64.b64decode(img_b64))
print(f'图片已保存: $OUTPUT')
"
