---
name: video-maker
description: Generate videos from scripts using AI images, TTS voiceover, and Remotion. Trigger when user says "create video", "generate video", "make video", "制作视频", "生成视频", "剪辑视频", or wants to convert a script/text into a video.
version: 1.0.0
---

# video-maker — AI Video Creation Skill

Create videos from text scripts with AI-generated images, TTS voiceover, and subtitles using Remotion.

## Trigger Conditions

Activate when user requests:
- Create / generate / make a video from script
- "制作视频", "生成视频", "剪辑视频", "文字转视频"
- Any request to produce video content from text/script

## Prerequisites

- **Remotion project**: Must be initialized in the working directory
- **gen-img skill**: For AI image generation (`~/.claude/skills/gen-img/`)
- **macOS**: Uses `say` command for TTS (Chinese voice: Meijia)
- **ffmpeg**: For audio format conversion

## Environment Variables

None required. Uses system TTS and gen-img skill.

## Execution Steps

### Step 1: Parse User Request

Extract from the user's message:
- **script** (required): The video script text or file path
- **output** (optional): Output video path, default `out/video.mp4`
- **resolution** (optional): Video resolution, default `1920x1080`
- **fps** (optional): Frame rate, default `30`
- **voice** (optional): TTS voice, default `Meijia` (Chinese female)

### Step 2: Create Remotion Project

If no Remotion project exists, initialize one:

```bash
# Create project directory
mkdir -p video-project/src video-project/public/images video-project/public/voiceover

# Initialize package.json
cat > video-project/package.json << 'EOF'
{
  "name": "ai-video",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "remotion studio",
    "build": "remotion bundle",
    "render": "remotion render"
  },
  "dependencies": {
    "@remotion/cli": "4.0.463",
    "@remotion/google-fonts": "^4.0.463",
    "@remotion/media": "4.0.463",
    "@remotion/transitions": "^4.0.463",
    "react": "19.2.3",
    "react-dom": "19.2.3",
    "remotion": "4.0.463"
  },
  "devDependencies": {
    "@types/react": "19.2.7",
    "typescript": "5.9.3"
  }
}
EOF

# Install dependencies
cd video-project && npm install
```

### Step 3: Generate Scene Images

For each scene in the script, generate an image using gen-img skill:

```bash
# Use gen-img skill to generate images
bash ~/.claude/skills/gen-img/scripts/gen-img.sh "<SCENE_PROMPT>" "video-project/public/images/sceneN.png" "1536x1024" "auto" 1 "png"
```

**Image prompt guidelines:**
- Describe the scene visually (not the text content)
- Include style keywords: "cinematic", "professional", "modern"
- Specify aspect ratio: 16:9 for landscape video
- Use consistent style across all scenes

### Step 4: Generate Voiceover

Use macOS TTS to generate voiceover for each scene:

```python
#!/usr/bin/env python3
"""Generate voiceover audio using macOS say command."""
import subprocess
import json
import os

def generate_voiceover(text, output_path, voice="Meijia"):
    """Generate voiceover using macOS say command."""
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
    
    # Get duration
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", output_path
    ], capture_output=True, text=True)
    
    return float(result.stdout.strip())

# Example usage
scenes = [
    {"id": "scene1", "text": "Scene 1 narration text..."},
    {"id": "scene2", "text": "Scene 2 narration text..."},
]

durations = {}
for scene in scenes:
    output_path = f"video-project/public/voiceover/{scene['id']}.mp3"
    duration = generate_voiceover(scene["text"], output_path)
    durations[scene["id"]] = duration
    print(f"{scene['id']}: {duration:.2f}s")

# Save durations
with open("video-project/public/voiceover/durations.json", "w") as f:
    json.dump(durations, f, indent=2)
```

### Step 5: Generate Captions

Create captions.json with timing matched to audio:

```python
#!/usr/bin/env python3
"""Generate captions JSON with precise timing."""
import json
import os
import re

def count_chars(text):
    """Count meaningful characters."""
    return len(re.sub(r'[^\u4e00-\u9fff\w]', '', text))

def split_into_phrases(text):
    """Split text by punctuation."""
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

def generate_captions(scenes, durations, output_path):
    """Generate captions with timing proportional to character count."""
    all_captions = []
    offset = 0.0
    transition_sec = 0.5  # 15 frames at 30fps
    
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
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_captions, f, ensure_ascii=False, indent=2)
    
    return len(all_captions)
```

### Step 6: Create Remotion Components

Generate the necessary Remotion files:

#### Root.tsx
```tsx
import { Composition } from 'remotion';
import { MainComposition } from './Composition';

const FPS = 30;
// Calculate total duration from audio durations
const DURATION_IN_FRAMES = 10974; // Sum of all scene durations

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="AIVideo"
      component={MainComposition}
      durationInFrames={DURATION_IN_FRAMES}
      fps={FPS}
      width={1920}
      height={1080}
    />
  );
};
```

#### Composition.tsx
```tsx
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { TransitionSeries, linearTiming } from '@remotion/transitions';
import { fade } from '@remotion/transitions/fade';
import { SceneWithAudio } from './components/SceneWithAudio';
import { Subtitles } from './components/Subtitles';

const TRANSITION_DURATION = 15; // 0.5s at 30fps

export const MainComposition: React.FC = () => {
  return (
    <AbsoluteFill>
      <TransitionSeries>
        {/* Add scenes with transitions */}
        <TransitionSeries.Sequence durationInFrames={SCENE_DURATIONS.scene1}>
          <SceneWithAudio audioFile="scene1.mp3">
            {/* Scene component */}
          </SceneWithAudio>
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_DURATION })}
        />
        {/* More scenes... */}
      </TransitionSeries>
      <Subtitles />
    </AbsoluteFill>
  );
};
```

#### SceneWithAudio.tsx
```tsx
import React from 'react';
import { Audio } from '@remotion/media';
import { staticFile } from 'remotion';

interface SceneWithAudioProps {
  audioFile: string;
  children: React.ReactNode;
}

export const SceneWithAudio: React.FC<SceneWithAudioProps> = ({ audioFile, children }) => (
  <>
    <Audio src={staticFile(`voiceover/${audioFile}`)} />
    {children}
  </>
);
```

#### Subtitles.tsx
```tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  AbsoluteFill,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  useDelayRender,
  Sequence,
  interpolate,
  Easing,
} from 'remotion';
import { loadFont } from '@remotion/google-fonts/NotoSansSC';

const { fontFamily } = loadFont();

interface CaptionItem {
  text: string;
  startMs: number;
  endMs: number;
}

export const Subtitles: React.FC = () => {
  const [captions, setCaptions] = useState<CaptionItem[] | null>(null);
  const { delayRender, continueRender, cancelRender } = useDelayRender();
  const [handle] = useState(() => delayRender());
  const { fps } = useVideoConfig();

  const fetchCaptions = useCallback(async () => {
    try {
      const response = await fetch(staticFile('captions.json'));
      const data = await response.json();
      setCaptions(data);
      continueRender(handle);
    } catch (e) {
      cancelRender(e);
    }
  }, [continueRender, cancelRender, handle]);

  useEffect(() => {
    fetchCaptions();
  }, [fetchCaptions]);

  if (!captions) return null;

  return (
    <AbsoluteFill>
      {captions.map((caption, index) => {
        const startFrame = Math.round((caption.startMs / 1000) * fps);
        const endFrame = Math.round((caption.endMs / 1000) * fps);
        const durationInFrames = Math.max(1, endFrame - startFrame);

        return (
          <Sequence
            key={index}
            from={startFrame}
            durationInFrames={durationInFrames}
          >
            <SubtitleLine text={caption.text} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const SubtitleLine: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const fadeOut = interpolate(frame, [durationInFrames - 4, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.in(Easing.cubic),
  });
  const opacity = Math.min(fadeIn, fadeOut);

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-end',
        alignItems: 'center',
        paddingBottom: 80,
      }}
    >
      <div
        style={{
          background: 'rgba(0, 0, 0, 0.75)',
          borderRadius: 12,
          padding: '10px 24px',
          maxWidth: '85%',
          opacity,
        }}
      >
        <div
          style={{
            fontSize: 40,
            fontWeight: 'bold',
            fontFamily,
            color: '#FFFFFF',
            textAlign: 'center',
            lineHeight: 1.4,
            textShadow: '0 2px 8px rgba(0,0,0,0.8)',
          }}
        >
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};
```

### Step 7: Render Video

Execute the final render:

```bash
cd video-project && npx remotion render AIVideo out/video.mp4 --codec h264 --crf 18
```

**Render options:**
- `--codec h264`: H.264 video codec (widely compatible)
- `--crf 18`: Constant Rate Factor (lower = better quality, 18-28 recommended)
- `--codec prores`: For ProRes output (professional editing)

### Step 8: Output Result

Report:
- Output video path
- Video duration and resolution
- File size
- Number of scenes and captions

## Script Structure

A typical video script should follow this format:

```
# Video Title

## Scene 1: Opening
Narration text for scene 1...

## Scene 2: Main Content
Narration text for scene 2...

## Scene 3: Closing
Narration text for scene 3...
```

**Best practices:**
- Keep each scene 20-60 seconds
- Use clear punctuation for natural pauses
- Separate scenes with clear headings
- Total video length: 1-5 minutes recommended

## File Structure

```
video-project/
├── package.json
├── src/
│   ├── Root.tsx
│   ├── Composition.tsx
│   ├── components/
│   │   ├── SceneWithAudio.tsx
│   │   └── Subtitles.tsx
│   └── scenes/
│       └── Scene*.tsx
├── public/
│   ├── images/
│   │   ├── scene1.png
│   │   └── scene2.png
│   ├── voiceover/
│   │   ├── scene1.mp3
│   │   ├── scene2.mp3
│   │   └── durations.json
│   └── captions.json
└── out/
    └── video.mp4
```

## Error Handling

- **TTS fails**: Check if voice is installed (`say -v '?'` lists available voices)
- **Image generation fails**: Verify gen-img skill is installed and API keys are set
- **Render fails**: Check Remotion version compatibility and Node.js version
- **Audio sync issues**: Verify durations.json matches actual audio files

## Customization

### Scene Transitions
- Fade: `<TransitionSeries.Transition presentation={fade()} />`
- Slide: `<TransitionSeries.Transition presentation={slide({ direction: 'from-right' })} />`
- Custom: Create custom presentation functions

### Subtitle Style
- Font: Change `loadFont()` parameters
- Position: Modify `paddingBottom` in Subtitles.tsx
- Colors: Update `background` and `color` styles
- Animation: Adjust `interpolate` timing

### Voice Options
- Chinese: `Meijia` (female), `Ting-Ting` (female)
- English: `Samantha`, `Alex`
- List all: `say -v '?'`

## Notes

- Remotion requires Node.js 18+
- Chinese fonts load from Google Fonts (requires internet)
- Images are cached by Remotion during render
- Render time depends on duration and complexity (typically 2-5x realtime)
