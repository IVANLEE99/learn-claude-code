#!/bin/bash
# Initialize a new Remotion video project
# Usage: bash init-project.sh <project_name>

set -e

PROJECT_NAME="${1:-video-project}"

echo "Creating Remotion project: $PROJECT_NAME"

# Create directory structure
mkdir -p "$PROJECT_NAME"/src/components
mkdir -p "$PROJECT_NAME"/src/scenes
mkdir -p "$PROJECT_NAME"/public/images
mkdir -p "$PROJECT_NAME"/public/voiceover
mkdir -p "$PROJECT_NAME"/out

# Create package.json
cat > "$PROJECT_NAME/package.json" << 'EOF'
{
  "name": "ai-video",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "remotion studio",
    "build": "remotion bundle",
    "render": "remotion render",
    "upgrade": "remotion upgrade"
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

# Create tsconfig.json
cat > "$PROJECT_NAME/tsconfig.json" << 'EOF'
{
  "compilerOptions": {
    "target": "ES2018",
    "module": "commonjs",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "moduleResolution": "node"
  },
  "include": ["src/**/*"]
}
EOF

# Create index.ts entry point
cat > "$PROJECT_NAME/src/index.ts" << 'EOF'
import { registerRoot } from 'remotion';
import { RemotionRoot } from './Root';

registerRoot(RemotionRoot);
EOF

# Create Root.tsx
cat > "$PROJECT_NAME/src/Root.tsx" << 'EOF'
import React from 'react';
import { Composition } from 'remotion';
import { MainComposition } from './Composition';

const FPS = 30;
const DURATION_IN_FRAMES = 10974; // Update based on your audio durations

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
EOF

# Create Composition.tsx
cat > "$PROJECT_NAME/src/Composition.tsx" << 'EOF'
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { TransitionSeries, linearTiming } from '@remotion/transitions';
import { fade } from '@remotion/transitions/fade';
import { SceneWithAudio } from './components/SceneWithAudio';
import { Subtitles } from './components/Subtitles';

const TRANSITION_DURATION = 15; // 0.5s at 30fps
const SCENE_DURATIONS = {
  scene1: 816,
  scene2: 1839,
  scene3: 1704,
  scene4: 1683,
  scene5: 1533,
  scene6: 1485,
  scene7: 2004,
};

export const MainComposition: React.FC = () => {
  return (
    <AbsoluteFill>
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={SCENE_DURATIONS.scene1}>
          <SceneWithAudio audioFile="scene1.mp3">
            {/* Add your scene component here */}
            <div style={{ width: '100%', height: '100%', background: '#1a1a2e' }} />
          </SceneWithAudio>
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_DURATION })}
        />
        {/* Add more scenes here */}
      </TransitionSeries>
      <Subtitles />
    </AbsoluteFill>
  );
};
EOF

# Create SceneWithAudio.tsx
cat > "$PROJECT_NAME/src/components/SceneWithAudio.tsx" << 'EOF'
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
EOF

# Create Subtitles.tsx
cat > "$PROJECT_NAME/src/components/Subtitles.tsx" << 'EOF'
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
  const { durationInFrames } = useVideoConfig();

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
EOF

# Create README with instructions
cat > "$PROJECT_NAME/README.md" << 'EOF'
# AI Video Project

This project uses Remotion to create videos with AI-generated images, TTS voiceover, and subtitles.

## Setup

```bash
npm install
```

## Development

```bash
npm run dev
```

## Render Video

```bash
npm run render
```

## Project Structure

```
├── src/
│   ├── Root.tsx          # Remotion root
│   ├── Composition.tsx   # Main composition
│   ├── components/
│   │   ├── SceneWithAudio.tsx
│   │   └── Subtitles.tsx
│   └── scenes/           # Scene components
├── public/
│   ├── images/           # Scene images
│   ├── voiceover/        # Audio files
│   └── captions.json     # Subtitles
└── out/                  # Rendered videos
```

## Adding Scenes

1. Add images to `public/images/`
2. Add audio to `public/voiceover/`
3. Update `captions.json` with subtitle timing
4. Add scene components to `src/scenes/`
5. Update `Composition.tsx` with new scenes
6. Update `Root.tsx` with total duration
EOF

# Install dependencies
echo "Installing dependencies..."
cd "$PROJECT_NAME" && npm install

echo ""
echo "Project created successfully!"
echo ""
echo "Next steps:"
echo "1. Add scene images to $PROJECT_NAME/public/images/"
echo "2. Add voiceover audio to $PROJECT_NAME/public/voiceover/"
echo "3. Create captions.json in $PROJECT_NAME/public/"
echo "4. Create scene components in $PROJECT_NAME/src/scenes/"
echo "5. Update Composition.tsx with your scenes"
echo "6. Run: cd $PROJECT_NAME && npm run dev"
