#!/bin/bash
# mimo-tts: MiMo V2.5 语音合成脚本
# 支持预置音色、风格控制、声音克隆、音色设计、音色档案

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VOICES_DIR="$(dirname "$SCRIPT_DIR")/voices"
PROFILES_FILE="$VOICES_DIR/profiles.json"

# === 默认值 ===
TEXT=""
VOICE="mimo_default"
STYLE=""
SINGING="false"
CLONE_AUDIO=""
VOICE_DESC=""
OUTPUT=""
MODEL=""
PROFILE=""
LIST_PROFILES="false"
SAVE_PROFILE=""

# === 参数解析 ===
while [[ $# -gt 0 ]]; do
    case "$1" in
        --text)          TEXT="$2"; shift 2 ;;
        --voice)         VOICE="$2"; shift 2 ;;
        --style)         STYLE="$2"; shift 2 ;;
        --singing)       SINGING="true"; shift ;;
        --clone)         CLONE_AUDIO="$2"; shift 2 ;;
        --voice-desc)    VOICE_DESC="$2"; shift 2 ;;
        --output)        OUTPUT="$2"; shift 2 ;;
        --model)         MODEL="$2"; shift 2 ;;
        --profile)       PROFILE="$2"; shift 2 ;;
        --list-profiles) LIST_PROFILES="true"; shift ;;
        --save-profile)  SAVE_PROFILE="$2"; shift 2 ;;
        -h|--help)
            echo "用法: $0 --text \"文本\" [选项]"
            echo ""
            echo "选项:"
            echo "  --text TEXT          待合成文本（必填，除非 --list-profiles）"
            echo "  --voice VOICE        预置音色 ID（默认: mimo_default）"
            echo "  --style STYLE        风格标签，空格分隔多个"
            echo "  --singing            唱歌模式"
            echo "  --clone FILE         克隆音色的音频文件路径（mp3/wav）"
            echo "  --voice-desc DESC    音色设计描述"
            echo "  --profile NAME       使用已保存的音色档案"
            echo "  --save-profile NAME  将当前 --clone 音频保存为档案"
            echo "  --list-profiles      列出所有已保存的音色档案"
            echo "  --output PATH        输出文件路径"
            echo "  --model MODEL        强制指定模型"
            echo ""
            echo "预置音色: mimo_default, 冰糖, 茉莉, 苏打, 白桦, Mia, Chloe, Milo, Dean"
            echo ""
            echo "示例:"
            echo "  $0 --text \"你好\" --voice \"冰糖\""
            echo "  $0 --text \"你好\" --profile 曼波"
            echo "  $0 --text \"你好\" --clone voice.mp3 --save-profile 我的声音"
            echo "  $0 --list-profiles"
            exit 0
            ;;
        *)
            if [ -z "$TEXT" ]; then
                TEXT="$1"
            elif [ "$VOICE" = "mimo_default" ]; then
                VOICE="$1"
            elif [ -z "$STYLE" ]; then
                STYLE="$1"
            elif [ "$SINGING" = "false" ]; then
                SINGING="$1"
            elif [ -z "$OUTPUT" ]; then
                OUTPUT="$1"
            fi
            shift
            ;;
    esac
done

# === 列出音色档案 ===
if [ "$LIST_PROFILES" = "true" ]; then
    if [ ! -f "$PROFILES_FILE" ]; then
        echo "暂无已保存的音色档案"
        exit 0
    fi
    echo "已保存的音色档案:"
    echo ""
    python3 -c "
import json
with open('$PROFILES_FILE') as f:
    profiles = json.load(f)
if not profiles:
    print('  (空)')
else:
    for name, info in profiles.items():
        desc = info.get('description', '')
        added = info.get('added', '')
        print(f'  {name}')
        if desc: print(f'    描述: {desc}')
        if added: print(f'    添加: {added}')
        print(f'    文件: {info.get(\"file\", \"\")}')
        print()
"
    exit 0
fi

# === 保存音色档案 ===
if [ -n "$SAVE_PROFILE" ]; then
    if [ -z "$CLONE_AUDIO" ]; then
        echo "错误: --save-profile 需要配合 --clone 使用" >&2
        exit 1
    fi

    # 确保源文件存在
    CLONE_ABS=$(cd "$(dirname "$CLONE_AUDIO")" && pwd)/$(basename "$CLONE_AUDIO")
    if [ ! -f "$CLONE_ABS" ]; then
        echo "错误: 音频文件不存在: $CLONE_AUDIO" >&2
        exit 1
    fi

    mkdir -p "$VOICES_DIR"

    # 复制文件到 voices 目录
    EXT="${CLONE_ABS##*.}"
    DEST_FILE="${SAVE_PROFILE}.${EXT}"
    cp "$CLONE_ABS" "$VOICES_DIR/$DEST_FILE"

    # 更新 profiles.json
    python3 -c "
import json, os, sys

profiles_file = '$PROFILES_FILE'
name = sys.argv[1]
dest_file = sys.argv[2]
desc = sys.argv[3] if len(sys.argv) > 3 else ''

try:
    with open(profiles_file) as f:
        profiles = json.load(f)
except:
    profiles = {}

from datetime import date
profiles[name] = {
    'file': dest_file,
    'description': desc or f'{name} 音色克隆',
    'added': str(date.today())
}

with open(profiles_file, 'w') as f:
    json.dump(profiles, f, indent=2, ensure_ascii=False)
print(f'音色档案 \"{name}\" 已保存')
" "$SAVE_PROFILE" "$DEST_FILE" "${VOICE_DESC:-}"

    # 如果没有 --text，直接退出
    [ -z "$TEXT" ] && exit 0

    # 如果有 --text，继续合成
    PROFILE="$SAVE_PROFILE"
    CLONE_AUDIO="$VOICES_DIR/$DEST_FILE"
fi

# === 加载音色档案 ===
if [ -n "$PROFILE" ] && [ -z "$CLONE_AUDIO" ]; then
    if [ ! -f "$PROFILES_FILE" ]; then
        echo "错误: 未找到音色档案 \"$PROFILE\"" >&2
        exit 1
    fi

    CLONE_AUDIO=$(python3 -c "
import json, sys, os

name = sys.argv[1]
voices_dir = sys.argv[2]

with open(os.path.join(voices_dir, 'profiles.json')) as f:
    profiles = json.load(f)

if name not in profiles:
    print(f'错误: 未找到音色档案 \"{name}\"', file=sys.stderr)
    print(f'可用档案: {\", \".join(profiles.keys())}', file=sys.stderr)
    sys.exit(1)

profile = profiles[name]
file_path = os.path.join(voices_dir, profile['file'])
if not os.path.exists(file_path):
    print(f'错误: 音色文件不存在: {file_path}', file=sys.stderr)
    sys.exit(1)

print(file_path)
" "$PROFILE" "$VOICES_DIR")

    if [ $? -ne 0 ]; then
        exit 1
    fi
fi

# === 参数检查 ===
if [ -z "$TEXT" ]; then
    echo "错误: 必须提供 --text 参数" >&2
    exit 1
fi

# === 读取 API 配置 ===
CONFIG=$(python3 -c "
import json, os
settings_path = os.path.expanduser('~/.claude/settings.json')
try:
    with open(settings_path) as f:
        s = json.load(f)
    env = s.get('env', {})
    url = env.get('MIMO_TTS_API_URL', 'https://token-plan-cn.xiaomimimo.com')
    key = env.get('MIMO_TTS_API_KEY', '')
    print(f'{url}')
    print(f'{key}')
except Exception:
    print('https://token-plan-cn.xiaomimimo.com')
    print('')
" 2>/dev/null)

API_URL=$(echo "$CONFIG" | sed -n '1p')
API_KEY=$(echo "$CONFIG" | sed -n '2p')

if [ -z "$API_KEY" ]; then
    echo "错误: 未找到 API Key，请在 ~/.claude/settings.json 的 env 中配置 MIMO_TTS_API_KEY" >&2
    exit 1
fi

# === 确定模型 ===
if [ -n "$CLONE_AUDIO" ]; then
    MODEL="${MODEL:-mimo-v2.5-tts-voiceclone}"
elif [ -n "$VOICE_DESC" ]; then
    MODEL="${MODEL:-mimo-v2.5-tts-voicedesign}"
else
    MODEL="${MODEL:-mimo-v2.5-tts}"
fi

# === 自动生成输出路径 ===
if [ -z "$OUTPUT" ]; then
    OUTPUT_DIR="$HOME/Documents/learn-claude-code/generated-audio"
    mkdir -p "$OUTPUT_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    OUTPUT="${OUTPUT_DIR}/mimo_tts_${TIMESTAMP}.wav"
fi

OUTPUT_DIR=$(dirname "$OUTPUT")
mkdir -p "$OUTPUT_DIR"

# === 构建请求体 ===
REQUEST_BODY=$(python3 -c "
import json, sys, base64, os

text = sys.argv[1]
voice = sys.argv[2]
style = sys.argv[3]
singing = sys.argv[4]
clone_audio = sys.argv[5]
voice_desc = sys.argv[6]
model = sys.argv[7]
profile = sys.argv[8]

# 构建 assistant content（目标文本）
content = text
if singing == 'true':
    content = '(唱歌)' + content
elif style:
    content = '(' + style + ')' + content

# 构建 user content
user_content = ''
if voice_desc:
    user_content = voice_desc

# 构建 audio 参数
audio = {'format': 'wav'}

if model == 'mimo-v2.5-tts-voiceclone' and clone_audio:
    audio_path = os.path.expanduser(clone_audio)
    with open(audio_path, 'rb') as f:
        audio_data = f.read()
    b64 = base64.b64encode(audio_data).decode('utf-8')
    ext = os.path.splitext(audio_path)[1].lower()
    mime = 'audio/wav' if ext == '.wav' else 'audio/mpeg'
    audio['voice'] = f'data:{mime};base64,{b64}'
elif model == 'mimo-v2.5-tts':
    audio['voice'] = voice

body = {
    'model': model,
    'messages': [
        {'role': 'user', 'content': user_content},
        {'role': 'assistant', 'content': content}
    ],
    'audio': audio
}
print(json.dumps(body, ensure_ascii=False))
" "$TEXT" "$VOICE" "$STYLE" "$SINGING" "$CLONE_AUDIO" "$VOICE_DESC" "$MODEL" "$PROFILE")

# === 调用 API ===
echo "正在合成语音..."
echo "  模型: $MODEL"
echo "  文本: ${TEXT:0:60}$([ ${#TEXT} -gt 60 ] && echo '...')"
[ "$VOICE" != "mimo_default" ] && [ "$MODEL" = "mimo-v2.5-tts" ] && echo "  音色: $VOICE"
[ "$SINGING" = "true" ] && echo "  模式: 唱歌"
[ -n "$STYLE" ] && echo "  风格: $STYLE"
[ -n "$PROFILE" ] && echo "  音色档案: $PROFILE"
[ -n "$VOICE_DESC" ] && echo "  音色描述: ${VOICE_DESC:0:40}"

RESPONSE=$(curl -s --max-time 120 "${API_URL}/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "api-key: ${API_KEY}" \
    -d "$REQUEST_BODY")

# === 检查响应 ===
if [ -z "$RESPONSE" ]; then
    echo "错误: API 无响应，请检查网络连接" >&2
    exit 1
fi

# === 解析并保存音频 ===
export MIMO_OUTPUT="$OUTPUT"
echo "$RESPONSE" | python3 -c "
import base64, json, sys, os

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

audio_data = choices[0].get('message', {}).get('audio', {}).get('data', '')
if not audio_data:
    print('错误: 响应中未包含音频数据', file=sys.stderr)
    sys.exit(1)

output_path = os.environ['MIMO_OUTPUT']
audio_bytes = base64.b64decode(audio_data)
with open(output_path, 'wb') as f:
    f.write(audio_bytes)

size_kb = len(audio_bytes) / 1024
print(f'已保存: {output_path}')
print(f'大小: {size_kb:.1f} KB')
print('完成！语音合成成功')
"
