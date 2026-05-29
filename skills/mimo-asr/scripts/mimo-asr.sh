#!/bin/bash
# mimo-asr: MiMo V2.5 语音识别脚本
# 支持 API 模式（云端）和 Local 模式（本地 GPU）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# === 默认值 ===
AUDIO=""
LANGUAGE="auto"
OUTPUT=""
OUTPUT_DIR=""
MODE="api"
MODEL_DIR=""
MAX_TOKENS=4096

# === 参数解析 ===
while [[ $# -gt 0 ]]; do
    case "$1" in
        --audio)       AUDIO="$2"; shift 2 ;;
        --language)    LANGUAGE="$2"; shift 2 ;;
        --output)      OUTPUT="$2"; shift 2 ;;
        --output-dir)  OUTPUT_DIR="$2"; shift 2 ;;
        --mode)        MODE="$2"; shift 2 ;;
        --model-dir)   MODEL_DIR="$2"; shift 2 ;;
        --max-tokens)  MAX_TOKENS="$2"; shift 2 ;;
        -h|--help)
            echo "用法: $0 --audio <音频文件或URL> [选项]"
            echo ""
            echo "选项:"
            echo "  --audio AUDIO        音频文件路径或 URL（必填）"
            echo "  --language LANG      语言: zh / en / auto（默认: auto）"
            echo "  --output PATH        输出文件路径"
            echo "  --output-dir DIR     输出目录（自动生成文件名）"
            echo "  --mode MODE          api（默认）或 local"
            echo "  --model-dir DIR      本地模型目录（local 模式）"
            echo "  --max-tokens NUM     最大输出 token 数（默认: 4096）"
            echo ""
            echo "示例:"
            echo "  $0 --audio recording.wav"
            echo "  $0 --audio recording.wav --language zh --output result.txt"
            echo "  $0 --audio https://example.com/audio.wav"
            echo "  $0 --audio recording.wav --mode local"
            exit 0
            ;;
        *)
            echo "未知参数: $1" >&2
            exit 1
            ;;
    esac
done

# === 参数检查 ===
if [ -z "$AUDIO" ]; then
    echo "错误: 必须提供 --audio 参数" >&2
    exit 1
fi

# === 检测输入类型 ===
IS_URL="false"
if [[ "$AUDIO" =~ ^https?:// ]]; then
    IS_URL="true"
elif [ ! -f "$AUDIO" ]; then
    echo "错误: 音频文件不存在: $AUDIO" >&2
    exit 1
fi

# === Local 模式 ===
if [ "$MODE" = "local" ]; then
    echo "正在使用本地模型进行语音识别..."

    # 检查 Python 环境
    if ! command -v python3 &>/dev/null; then
        echo "错误: 未找到 python3" >&2
        exit 1
    fi

    # 查找模型目录
    if [ -z "$MODEL_DIR" ]; then
        # 尝试常见路径
        for dir in \
            "$HOME/models/MiMo-V2.5-ASR" \
            "$HOME/.cache/mimo-asr" \
            "$SCRIPT_DIR/../models" \
            "./models/MiMo-V2.5-ASR"; do
            if [ -d "$dir" ]; then
                MODEL_DIR="$dir"
                break
            fi
        done
    fi

    if [ -z "$MODEL_DIR" ] || [ ! -d "$MODEL_DIR" ]; then
        echo "错误: 未找到本地模型目录" >&2
        echo "请通过 --model-dir 指定模型路径，或下载模型:" >&2
        echo "  hf download XiaomiMiMo/MiMo-V2.5-ASR --local-dir ./models/MiMo-V2.5-ASR" >&2
        echo "  hf download XiaomiMiMo/MiMo-Audio-Tokenizer --local-dir ./models/MiMo-Audio-Tokenizer" >&2
        exit 1
    fi

    TOKENIZER_DIR=""
    for dir in \
        "$HOME/models/MiMo-Audio-Tokenizer" \
        "$HOME/.cache/mimo-audio-tokenizer" \
        "$(dirname "$MODEL_DIR")/MiMo-Audio-Tokenizer" \
        "./models/MiMo-Audio-Tokenizer"; do
        if [ -d "$dir" ]; then
            TOKENIZER_DIR="$dir"
            break
        fi
    done

    if [ -z "$TOKENIZER_DIR" ]; then
        echo "错误: 未找到 Audio Tokenizer 模型" >&2
        echo "请下载: hf download XiaomiMiMo/MiMo-Audio-Tokenizer --local-dir ./models/MiMo-Audio-Tokenizer" >&2
        exit 1
    fi

    AUDIO_ABS=$(cd "$(dirname "$AUDIO")" && pwd)/$(basename "$AUDIO")

    # 构建语言标签
    AUDIO_TAG=""
    case "$LANGUAGE" in
        zh) AUDIO_TAG='<chinese>' ;;
        en) AUDIO_TAG='<english>' ;;
        *)  AUDIO_TAG="" ;;
    esac

    python3 -c "
import sys
sys.path.insert(0, '$MODEL_DIR')
from src.mimo_audio.mimo_audio import MimoAudio

model = MimoAudio(
    model_path='$MODEL_DIR',
    tokenizer_path='$TOKENIZER_DIR',
)

audio_tag = '$AUDIO_TAG'
if audio_tag:
    text = model.asr_sft('$AUDIO_ABS', audio_tag=audio_tag)
else:
    text = model.asr_sft('$AUDIO_ABS')

print(text)
"
    exit $?
fi

# === API 模式 ===
echo "正在使用云端 API 进行语音识别..."

# === 读取 API 配置 ===
CONFIG=$(python3 -c "
import json, os

settings_path = os.path.expanduser('~/.claude/settings.json')
try:
    with open(settings_path) as f:
        s = json.load(f)
    env = s.get('env', {})
except Exception:
    env = {}

# 优先检查 ANTHROPIC_BASE_URL 是否包含 xiaomimimo.com
anthropic_url = env.get('ANTHROPIC_BASE_URL', os.environ.get('ANTHROPIC_BASE_URL', ''))
anthropic_token = env.get('ANTHROPIC_AUTH_TOKEN', os.environ.get('ANTHROPIC_AUTH_TOKEN', ''))

if 'xiaomimimo.com' in anthropic_url and anthropic_token:
    url = anthropic_url.rstrip('/')
    for suffix in ['/anthropic', '/v1', '/anthropic/v1']:
        if url.endswith(suffix):
            url = url[:-len(suffix)]
            break
    # ASR 使用 chat completions endpoint，需要 /v1
    if not url.endswith('/v1'):
        url = url + '/v1'
    print(f'{url}')
    print(f'{anthropic_token}')
else:
    url = env.get('MIMO_API_URL', 'https://api.xiaomimimo.com')
    key = env.get('MIMO_API_KEY', '')
    if not url.endswith('/v1'):
        url = url + '/v1'
    print(f'{url}')
    print(f'{key}')
" 2>/dev/null)

API_URL=$(echo "$CONFIG" | sed -n '1p')
API_KEY=$(echo "$CONFIG" | sed -n '2p')

if [ -z "$API_KEY" ]; then
    echo "错误: 未找到 API Key，请在 ~/.claude/settings.json 的 env 中配置 MIMO_API_KEY" >&2
    exit 1
fi

# === 自动生成输出路径 ===
if [ -z "$OUTPUT" ] && [ -n "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    OUTPUT="${OUTPUT_DIR}/mimo_asr_${TIMESTAMP}.txt"
fi

if [ -n "$OUTPUT" ]; then
    OUTPUT_DIR=$(dirname "$OUTPUT")
    mkdir -p "$OUTPUT_DIR" 2>/dev/null || true
fi

# === 构建请求体 ===
REQUEST_BODY_FILE=$(mktemp /tmp/mimo-asr-request-XXXXXX.json)
trap "rm -f '$REQUEST_BODY_FILE'" EXIT

# 构建语言提示
LANG_HINT=""
case "$LANGUAGE" in
    zh) LANG_HINT="请将音频内容逐字转录为中文文字，只输出转录结果，不要解释、分析或总结。" ;;
    en) LANG_HINT="Transcribe the audio content word-for-word into text. Output only the transcription, no explanation or analysis." ;;
    *)  LANG_HINT="请将音频内容逐字转录为文字，只输出转录结果，不要解释、分析或总结。如遇中英混合内容，请如实转录。" ;;
esac

python3 -c "
import json, sys, base64, os

audio_path = sys.argv[1]
is_url = sys.argv[2] == 'true'
lang_hint = sys.argv[3]
max_tokens = int(sys.argv[4])
output_file = sys.argv[5]

if is_url:
    audio_data = audio_path
else:
    audio_abs = os.path.expanduser(audio_path)
    with open(audio_abs, 'rb') as f:
        audio_bytes = f.read()
    b64 = base64.b64encode(audio_bytes).decode('utf-8')
    ext = os.path.splitext(audio_abs)[1].lower()
    mime_map = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.flac': 'audio/flac',
        '.m4a': 'audio/mp4',
        '.ogg': 'audio/ogg',
    }
    mime = mime_map.get(ext, 'audio/wav')
    audio_data = f'data:{mime};base64,{b64}'

body = {
    'model': 'mimo-v2.5',
    'messages': [
        {
            'role': 'system',
            'content': 'You are MiMo, an AI assistant developed by Xiaomi. You are an expert at transcribing audio content. Output ONLY the transcription text, nothing else. No analysis, no explanation, no timestamps.'
        },
        {
            'role': 'user',
            'content': [
                {
                    'type': 'input_audio',
                    'input_audio': {
                        'data': audio_data
                    }
                },
                {
                    'type': 'text',
                    'text': lang_hint
                }
            ]
        }
    ],
    'max_completion_tokens': max_tokens
}

with open(output_file, 'w') as f:
    json.dump(body, f, ensure_ascii=False)
" "$AUDIO" "$IS_URL" "$LANG_HINT" "$MAX_TOKENS" "$REQUEST_BODY_FILE"

# === 调用 API ===
echo "  模型: mimo-v2.5"
echo "  音频: ${AUDIO:0:60}$([ ${#AUDIO} -gt 60 ] && echo '...')"
echo "  语言: $LANGUAGE"
echo ""

RESPONSE=$(curl -s --max-time 300 "${API_URL}/chat/completions" \
    -H "Content-Type: application/json" \
    -H "api-key: ${API_KEY}" \
    -d "@${REQUEST_BODY_FILE}")

# === 检查响应 ===
if [ -z "$RESPONSE" ]; then
    echo "错误: API 无响应，请检查网络连接" >&2
    exit 1
fi

# === 解析并输出结果 ===
TRANSCRIPTION=$(echo "$RESPONSE" | python3 -c "
import json, sys, re

resp_text = sys.stdin.read()
try:
    resp = json.loads(resp_text)
except json.JSONDecodeError:
    print(f'错误: 无法解析 API 响应', file=sys.stderr)
    print(resp_text[:500], file=sys.stderr)
    sys.exit(1)

if 'error' in resp:
    err = resp['error']
    msg = err.get('message', str(err)) if isinstance(err, dict) else str(err)
    print(f'API 错误: {msg}', file=sys.stderr)
    sys.exit(1)

choices = resp.get('choices', [])
if not choices:
    print('错误: API 未返回数据', file=sys.stderr)
    sys.exit(1)

message = choices[0].get('message', {})
content = message.get('content', '').strip()
reasoning = message.get('reasoning_content', '').strip()

# 优先使用 content（如果非空）
if content:
    text = content
elif reasoning:
    # reasoning_content 可能包含模型的思考过程，尝试提取最终转录结果
    # 策略：找到最后一个看起来像转录文本的段落
    lines = [l.strip() for l in reasoning.split('\\n') if l.strip()]

    # 查找包含中文字符的最后几行作为转录结果
    transcription_lines = []
    for line in reversed(lines):
        # 跳过明显的推理/分析行
        if any(kw in line for kw in [
            'Analyze', 'analyze', 'Draft', 'draft', 'Decision', 'decision',
            'Verify', 'verify', 'Context', 'context', 'Format', 'format',
            'Self-Correction', 'correction', 'Double Check', 'Final Polish',
            'Final Output', 'think', 'Think', '步骤', '分析', '决定',
            '验证', '草稿', '最终', '检查', '输出生成'
        ]):
            break
        transcription_lines.insert(0, line)

    if transcription_lines:
        text = '\\n'.join(transcription_lines)
    else:
        # 回退：取最后 5 行
        text = '\\n'.join(lines[-5:]) if lines else reasoning
else:
    print('错误: 响应中未包含转录文本', file=sys.stderr)
    sys.exit(1)

# 清理文本：去除首尾引号和多余空白
text = text.strip().strip('\"').strip(\"'\")
# 去除时间戳标记如 00:00 00:04
text = re.sub(r'\\d{2}:\\d{2}\\s*', '', text).strip()

print(text)

# 输出 token 使用信息
usage = resp.get('usage', {})
if usage:
    total = usage.get('total_tokens', 0)
    print(f'\\n[token_usage:{total}]', file=sys.stderr)
" 2>&1)

# 分离输出和错误
TRANSCRIPTION_TEXT=$(echo "$TRANSCRIPTION" | grep -v '^\[token_usage:' || true)
TOKEN_INFO=$(echo "$TRANSCRIPTION" | grep '^\[token_usage:' | sed 's/\[token_usage://;s/\]//' || true)

if [ -z "$TRANSCRIPTION_TEXT" ]; then
    echo "转录失败" >&2
    exit 1
fi

# === 输出结果 ===
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$TRANSCRIPTION_TEXT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[ -n "$TOKEN_INFO" ] && echo "Token 使用: $TOKEN_INFO"

# === 保存到文件 ===
if [ -n "$OUTPUT" ]; then
    echo "$TRANSCRIPTION_TEXT" > "$OUTPUT"
    echo "已保存到: $OUTPUT"
fi

echo ""
echo "识别完成！"
