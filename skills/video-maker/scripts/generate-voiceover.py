#!/usr/bin/env python3
"""Generate voiceover audio using macOS say command."""
import subprocess
import json
import os
import sys

def generate_voiceover(text, output_path, voice="Meijia"):
    """Generate voiceover using macOS say command."""
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Generate AIFF
    aiff_path = output_path.replace('.mp3', '.aiff')
    subprocess.run(["say", "-v", voice, "-o", aiff_path, text], check=True)

    # Convert to MP3 using ffmpeg
    subprocess.run([
        "ffmpeg", "-i", aiff_path, "-codec:a", "libmp3lame", "-qscale:a", "2",
        output_path, "-y"
    ], check=True, capture_output=True)

    # Remove AIFF
    os.remove(aiff_path)

    # Get duration using ffprobe
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", output_path
    ], capture_output=True, text=True)

    return float(result.stdout.strip())

def main():
    if len(sys.argv) < 3:
        print("Usage: generate-voiceover.py <text_file> <output_dir> [voice]")
        print("  text_file: Path to text file with scene text")
        print("  output_dir: Directory to save MP3 files")
        print("  voice: TTS voice (default: Meijia)")
        sys.exit(1)

    text_file = sys.argv[1]
    output_dir = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else "Meijia"

    # Read scenes from text file
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse scenes (assuming ## Scene N: format)
    import re
    scenes = []
    parts = re.split(r'## Scene \d+:', content)
    headers = re.findall(r'## Scene \d+: (.+)', content)

    for i, (header, text) in enumerate(zip(headers, parts[1:]), 1):
        scenes.append({
            "id": f"scene{i}",
            "text": text.strip()
        })

    # Generate voiceover for each scene
    durations = {}
    for scene in scenes:
        output_path = os.path.join(output_dir, f"{scene['id']}.mp3")
        print(f"Generating {scene['id']}...")
        duration = generate_voiceover(scene["text"], output_path, voice)
        durations[scene["id"]] = duration
        print(f"  {scene['id']}: {duration:.2f}s")

    # Save durations
    durations_path = os.path.join(output_dir, "durations.json")
    with open(durations_path, "w") as f:
        json.dump(durations, f, indent=2)

    print(f"\nGenerated {len(durations)} voiceover files")
    print(f"Durations saved to: {durations_path}")

if __name__ == "__main__":
    main()
