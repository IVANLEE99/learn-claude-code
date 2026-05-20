#!/bin/bash
# Render video from scenes
# Usage: bash render-video.sh <project_dir> [output_file]

set -e

PROJECT_DIR="${1:-.}"
OUTPUT_FILE="${2:-out/video.mp4}"

echo "Rendering video from: $PROJECT_DIR"

# Check if project exists
if [ ! -f "$PROJECT_DIR/package.json" ]; then
    echo "Error: No package.json found in $PROJECT_DIR"
    exit 1
fi

# Check if node_modules exist
if [ ! -d "$PROJECT_DIR/node_modules" ]; then
    echo "Installing dependencies..."
    cd "$PROJECT_DIR" && npm install
fi

# Check for captions.json
if [ ! -f "$PROJECT_DIR/public/captions.json" ]; then
    echo "Warning: No captions.json found, video will have no subtitles"
fi

# Check for voiceover files
if [ ! -d "$PROJECT_DIR/public/voiceover" ] || [ -z "$(ls -A $PROJECT_DIR/public/voiceover/*.mp3 2>/dev/null)" ]; then
    echo "Warning: No voiceover files found"
fi

# Render video
echo "Starting render..."
cd "$PROJECT_DIR" && npx remotion render AIVideo "$OUTPUT_FILE" --codec h264 --crf 18

# Get file size
if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo ""
    echo "Video rendered successfully!"
    echo "Output: $OUTPUT_FILE"
    echo "Size: $FILE_SIZE"
else
    echo "Error: Video render failed"
    exit 1
fi
