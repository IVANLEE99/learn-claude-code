import React from 'react';
import { AbsoluteFill } from 'remotion';
import { TransitionSeries, linearTiming } from '@remotion/transitions';
import { fade } from '@remotion/transitions/fade';
import { slide } from '@remotion/transitions/slide';
import { Scene1Opening } from './scenes/Scene1Opening';
import {
  Scene2ClaudeCode,
  Scene3Cursor,
  Scene4Copilot,
  Scene5V0,
  Scene6Bolt,
} from './scenes/ToolScenes';
import { Scene7Summary } from './scenes/Scene7Summary';
import { SceneWithAudio } from './components/SceneWithAudio';
import { Subtitles } from './components/Subtitles';
import { SCENE_DURATIONS } from './utils';

const TRANSITION_DURATION = 15; // 0.5s

export const MainComposition: React.FC = () => {
  return (
    <AbsoluteFill>
      <TransitionSeries>
        {/* Scene 1: Opening */}
        <TransitionSeries.Sequence durationInFrames={SCENE_DURATIONS.scene1}>
          <SceneWithAudio audioFile="scene1_opening.mp3">
            <Scene1Opening />
          </SceneWithAudio>
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_DURATION })}
        />

        {/* Scene 2: Claude Code */}
        <TransitionSeries.Sequence durationInFrames={SCENE_DURATIONS.scene2}>
          <SceneWithAudio audioFile="scene2_claude_code.mp3">
            <Scene2ClaudeCode />
          </SceneWithAudio>
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={linearTiming({ durationInFrames: TRANSITION_DURATION })}
        />

        {/* Scene 3: Cursor */}
        <TransitionSeries.Sequence durationInFrames={SCENE_DURATIONS.scene3}>
          <SceneWithAudio audioFile="scene3_cursor.mp3">
            <Scene3Cursor />
          </SceneWithAudio>
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={linearTiming({ durationInFrames: TRANSITION_DURATION })}
        />

        {/* Scene 4: GitHub Copilot */}
        <TransitionSeries.Sequence durationInFrames={SCENE_DURATIONS.scene4}>
          <SceneWithAudio audioFile="scene4_copilot.mp3">
            <Scene4Copilot />
          </SceneWithAudio>
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={linearTiming({ durationInFrames: TRANSITION_DURATION })}
        />

        {/* Scene 5: v0.dev */}
        <TransitionSeries.Sequence durationInFrames={SCENE_DURATIONS.scene5}>
          <SceneWithAudio audioFile="scene5_v0.mp3">
            <Scene5V0 />
          </SceneWithAudio>
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={linearTiming({ durationInFrames: TRANSITION_DURATION })}
        />

        {/* Scene 6: bolt.new */}
        <TransitionSeries.Sequence durationInFrames={SCENE_DURATIONS.scene6}>
          <SceneWithAudio audioFile="scene6_bolt.mp3">
            <Scene6Bolt />
          </SceneWithAudio>
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_DURATION })}
        />

        {/* Scene 7: Summary */}
        <TransitionSeries.Sequence durationInFrames={SCENE_DURATIONS.scene7}>
          <SceneWithAudio audioFile="scene7_summary.mp3">
            <Scene7Summary />
          </SceneWithAudio>
        </TransitionSeries.Sequence>
      </TransitionSeries>

      {/* Subtitles overlay */}
      <Subtitles />
    </AbsoluteFill>
  );
};
