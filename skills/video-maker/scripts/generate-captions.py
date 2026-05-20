#!/usr/bin/env python3
"""Generate captions JSON with precise timing matched to audio."""
import json
import os
import re
import sys

def count_chars(text):
    """Count meaningful characters (Chinese + English + numbers)."""
    return len(re.sub(r'[^\u4e00-\u9fff\w]', '', text))

def split_into_phrases(text):
    """Split text by punctuation marks."""
    parts = re.split(r'([。！？，；：、])', text)
    phrases = []
    i = 0
    while i < len(parts):
        phrase = parts[i]
        if i + 1 < len(parts) and parts[i + 1] in '。！？，；：、':
            phrase += parts[i + 1]
            i += 2
        else:
            i += 1
        if phrase.strip():
            phrases.append(phrase)
    return phrases

def generate_captions(scenes, durations, output_path, transition_sec=0.5):
    """Generate captions with timing proportional to character count."""
    all_captions = []
    offset = 0.0

    for scene in scenes:
        scene_id = scene["id"]
        total_duration = durations[scene_id]
        phrases = split_into_phrases(scene["text"])
        char_counts = [count_chars(p) for p in phrases]
        total_chars = sum(char_counts)

        current_time = 0.0
        for phrase, char_count in zip(phrases, char_counts):
            phrase_duration = total_duration * (char_count / total_chars)
            start_ms = (offset + current_time) * 1000
            end_ms = (offset + current_time + phrase_duration) * 1000

            all_captions.append({
                "text": phrase,
                "startMs": round(start_ms),
                "endMs": round(end_ms),
                "timestampMs": round(start_ms),
                "confidence": 1.0,
            })
            current_time += phrase_duration

        offset += total_duration - transition_sec

    # Save captions
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_captions, f, ensure_ascii=False, indent=2)

    return len(all_captions)

def main():
    if len(sys.argv) < 4:
        print("Usage: generate-captions.py <scenes_file> <durations_file> <output_file>")
        print("  scenes_file: JSON file with scenes [{id, text}, ...]")
        print("  durations_file: JSON file with audio durations {scene_id: seconds, ...}")
        print("  output_file: Output captions.json path")
        sys.exit(1)

    scenes_file = sys.argv[1]
    durations_file = sys.argv[2]
    output_file = sys.argv[3]

    with open(scenes_file, 'r', encoding='utf-8') as f:
        scenes = json.load(f)

    with open(durations_file, 'r', encoding='utf-8') as f:
        durations = json.load(f)

    num_captions = generate_captions(scenes, durations, output_file)
    print(f"Generated {num_captions} captions")
    print(f"Saved to: {output_file}")

if __name__ == "__main__":
    main()
