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

// 使用系统字体，避免 Google Fonts 网络加载超时
const fontFamily = '"PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif';

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
      setCaptions(Array.isArray(data) ? data : data.captions);
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
        // v3.21.0: 前 5s Hook 字幕字号 +20%（治 2s 跳出 44%，强化封面承诺兑现）
        const isHook = caption.startMs < 5000;

        return (
          <Sequence
            key={index}
            from={startFrame}
            durationInFrames={durationInFrames}
          >
            <SubtitleLine text={caption.text} enlarged={isHook} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const SubtitleLine: React.FC<{ text: string; enlarged?: boolean }> = ({ text, enlarged }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 4, durationInFrames],
    [1, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.in(Easing.cubic),
    }
  );
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
            // v3.21.0: Hook 字幕（前 5s）字号 +20%（40 → 48），强化封面承诺兑现
            fontSize: enlarged ? 48 : 40,
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
