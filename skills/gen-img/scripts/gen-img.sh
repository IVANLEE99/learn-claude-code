#!/bin/bash
# gen-img: GPT-Image-2 图片生成脚本
# 用法: gen-img.sh "prompt" [output_path] [size] [quality] [n] [format]

set -euo pipefail

# === 参数解析 ===
PROMPT="${1:?用法: $0 \"prompt\" [output_path] [size] [quality] [n] [format]}"
OUTPUT="${2:-}"
SIZE="${3:-1024x1024}"
QUALITY="${4:-auto}"
N="${5:-1}"
FORMAT="${6:-png}"

# === 读取 API 配置 ===
CONFIG=$(python3 -c "
import json, os
settings_path = os.path.expanduser('~/.claude/settings.json')
try:
    with open(settings_path) as f:
        s = json.load(f)
    env = s.get('env', {})
    url = env.get('GEN_IMG_API_URL', 'https://sin.ioll.pp.ua')
    key = env.get('GEN_IMG_API_KEY', '')
    print(f'{url}')
    print(f'{key}')
except Exception:
    print('https://sin.ioll.pp.ua')
    print('')
" 2>/dev/null)

API_URL=$(echo "$CONFIG" | sed -n '1p')
API_KEY=$(echo "$CONFIG" | sed -n '2p')

if [ -z "$API_KEY" ]; then
    echo "错误: 未找到 API Key，请在 ~/.claude/settings.json 的 env 中配置 GEN_IMG_API_KEY" >&2
    exit 1
fi

# === 自动生成输出路径 ===
if [ -z "$OUTPUT" ]; then
    OUTPUT_DIR="$HOME/Documents/learn-claude-code/generated-images"
    mkdir -p "$OUTPUT_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    OUTPUT="${OUTPUT_DIR}/gen_${TIMESTAMP}.${FORMAT}"
fi

# 确保输出目录存在
OUTPUT_DIR=$(dirname "$OUTPUT")
mkdir -p "$OUTPUT_DIR"

# === 调用 API ===
echo "正在生成图片..."
echo "  Prompt: ${PROMPT:0:80}..."
echo "  Size: $SIZE | Quality: $QUALITY | Format: $FORMAT"

RESPONSE=$(curl -s --max-time 120 "${API_URL}/v1/images/generations" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${API_KEY}" \
    -d "$(python3 -c "
import json
body = {
    'model': 'gpt-image-2',
    'prompt': '''${PROMPT}''',
    'size': '${SIZE}',
    'quality': '${QUALITY}',
    'n': ${N},
    'output_format': '${FORMAT}',
    'response_format': 'b64_json'
}
print(json.dumps(body))
")")

# === 检查响应 ===
if [ -z "$RESPONSE" ]; then
    echo "错误: API 无响应，请检查网络连接" >&2
    exit 1
fi

# === 解析并保存图片 ===
python3 << PYEOF
import base64, json, sys, os

resp_text = '''${RESPONSE}'''
try:
    resp = json.loads(resp_text)
except json.JSONDecodeError:
    print(f"错误: 无法解析 API 响应", file=sys.stderr)
    print(resp_text[:500], file=sys.stderr)
    sys.exit(1)

if 'error' in resp:
    err = resp['error']
    msg = err.get('message', str(err)) if isinstance(err, dict) else str(err)
    print(f"API 错误: {msg}", file=sys.stderr)
    sys.exit(1)

data = resp.get('data', [])
if not data:
    print("错误: API 未返回图片数据", file=sys.stderr)
    sys.exit(1)

output_path = "${OUTPUT}"
saved_count = 0

for i, item in enumerate(data):
    b64 = item.get('b64_json', '')
    url = item.get('url', '')

    if b64:
        path = output_path if len(data) == 1 else f"{os.path.splitext(output_path)[0]}_{i+1}.{os.path.splitext(output_path)[1][1:]}"
        with open(path, 'wb') as f:
            f.write(base64.b64decode(b64))
        print(f"已保存: {path}")
        saved_count += 1
    elif url:
        print(f"图片 URL: {url}")
        saved_count += 1

    revised = item.get('revised_prompt', '')
    if revised:
        print(f"改写提示词: {revised[:200]}")

if saved_count == 0:
    print("错误: 未能保存任何图片", file=sys.stderr)
    sys.exit(1)

print(f"完成！共生成 {saved_count} 张图片")
PYEOF
