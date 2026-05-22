#!/bin/bash

# Fish Audio S2 语音合成脚本
# 用法: ./tts.sh "要合成的文本" [输出文件名] [参考音频路径] [参考文本]

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FISH_SPEECH_DIR="$(cd "$(dirname "$SCRIPT_DIR")/../.." && pwd)/fish-speech"
CHECKPOINT_PATH="checkpoints/s2-pro"
CODEC_PATH="checkpoints/s2-pro/codec.pth"
# 自动检测设备：MPS (Apple Silicon) > CUDA > CPU
if python3 -c "import torch; exit(0 if torch.backends.mps.is_available() else 1)" 2>/dev/null; then
    DEVICE="mps"
elif python3 -c "import torch; exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
    DEVICE="cuda"
else
    DEVICE="cpu"
fi
MAX_NEW_TOKENS=64

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 帮助信息
show_help() {
    echo "Fish Audio S2 语音合成脚本"
    echo ""
    echo "用法:"
    echo "  $0 \"要合成的文本\" [输出文件名] [参考音频路径] [参考文本]"
    echo ""
    echo "参数:"
    echo "  文本         要合成的文本内容（必填）"
    echo "  输出文件名   输出音频文件名（默认: output.wav）"
    echo "  参考音频     参考音频文件路径（可选，用于声音克隆）"
    echo "  参考文本     参考音频对应的文本（可选）"
    echo ""
    echo "示例:"
    echo "  $0 \"你好世界\" hello.wav"
    echo "  $0 \"用这个声音说话\" cloned.wav reference.wav \"这是参考文本\""
    echo ""
    echo "情感标签:"
    echo "  [excited] 兴奋  [whisper] 低语  [angry] 生气"
    echo "  [sad] 悲伤  [pause] 停顿  [laughing] 笑声"
}

# 检查参数
if [ $# -lt 1 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

TEXT="$1"
OUTPUT_FILE="${2:-output.wav}"
REFERENCE_AUDIO="${3:-}"
REFERENCE_TEXT="${4:-}"

echo -e "${GREEN}Fish Audio S2 语音合成${NC}"
echo "================================"
echo -e "文本: ${YELLOW}${TEXT}${NC}"
echo -e "输出: ${YELLOW}${OUTPUT_FILE}${NC}"

if [ -n "$REFERENCE_AUDIO" ]; then
    echo -e "参考音频: ${YELLOW}${REFERENCE_AUDIO}${NC}"
    echo -e "参考文本: ${YELLOW}${REFERENCE_TEXT}${NC}"
fi
echo ""

# 进入 fish-speech 目录
echo "DEBUG: FISH_SPEECH_DIR=$FISH_SPEECH_DIR"
cd "$FISH_SPEECH_DIR" || { echo "Failed to cd to $FISH_SPEECH_DIR"; exit 1; }
pwd

# 激活虚拟环境
source venv/bin/activate || { echo "Failed to activate venv"; exit 1; }

# 步骤 1: 如果有参考音频，生成 VQ tokens
PROMPT_TOKENS=""
if [ -n "$REFERENCE_AUDIO" ]; then
    echo -e "${GREEN}[1/3] 生成参考音频 VQ tokens...${NC}"
    python fish_speech/models/dac/inference.py \
        -i "$REFERENCE_AUDIO" \
        --checkpoint-path "$CODEC_PATH" \
        --device "$DEVICE" \
        -o "fake.wav"

    PROMPT_TOKENS="--prompt-tokens fake.npy --prompt-text \"$REFERENCE_TEXT\""
    echo -e "${GREEN}VQ tokens 生成完成${NC}"
    echo ""
else
    echo -e "${YELLOW}[1/3] 跳过参考音频（未提供）${NC}"
    echo ""
fi

# 步骤 2: 文本转语义 tokens
echo -e "${GREEN}[2/3] 文本转语义 tokens...${NC}"
mkdir -p output

EVAL_CMD="python fish_speech/models/text2semantic/inference.py"
EVAL_CMD="$EVAL_CMD --text \"$TEXT\""
EVAL_CMD="$EVAL_CMD --max-new-tokens $MAX_NEW_TOKENS"
EVAL_CMD="$EVAL_CMD --device $DEVICE"
EVAL_CMD="$EVAL_CMD --checkpoint-path $CHECKPOINT_PATH"
EVAL_CMD="$EVAL_CMD --output-dir output"

if [ -n "$PROMPT_TOKENS" ]; then
    EVAL_CMD="$EVAL_CMD $PROMPT_TOKENS"
fi

eval $EVAL_CMD
echo -e "${GREEN}语义 tokens 生成完成${NC}"
echo ""

# 步骤 3: 语义 tokens 转音频
echo -e "${GREEN}[3/3] 生成最终音频...${NC}"
python fish_speech/models/dac/inference.py \
    -i "output/codes_0.npy" \
    --checkpoint-path "$CODEC_PATH" \
    --device "$DEVICE" \
    -o "$OUTPUT_FILE"

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}合成完成！${NC}"
echo -e "输出文件: ${YELLOW}${OUTPUT_FILE}${NC}"

# 显示文件信息
if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
    echo -e "文件大小: ${YELLOW}${FILE_SIZE}${NC}"
fi

# 清理临时文件
rm -f fake.wav fake.npy output/codes_0.npy
