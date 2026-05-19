import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
import { createTikTokStyleCaptions } from '@remotion/captions';
import { loadFont } from '@remotion/google-fonts/NotoSansSC';
import type { Caption } from '@remotion/captions';

const { fontFamily } = loadFont();

const SWITCH_CAPTIONS_EVERY_MS = 3000; // Show ~3 seconds of text at a time

export const Subtitles: React.FC = () => {
  const [captions, setCaptions] = useState<Caption[] | null>(null);
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

  const pages = useMemo(() => {
    if (!captions) return [];
    const { pages } = createTikTokStyleCaptions({
      captions,
      combineTokensWithinMilliseconds: SWITCH_CAPTIONS_EVERY_MS,
    });
    return pages;
  }, [captions]);

  if (!captions) return null;

  return (
    <AbsoluteFill>
      {pages.map((page, index) => {
        const nextPage = pages[index + 1] ?? null;
        const startFrame = (page.startMs / 1000) * fps;
        const endFrame = Math.min(
          nextPage ? (nextPage.startMs / 1000) * fps : Infinity,
          startFrame + (SWITCH_CAPTIONS_EVERY_MS / 1000) * fps,
        );
        const durationInFrames = Math.max(0, endFrame - startFrame);

        if (durationInFrames <= 0) return null;

        return (
          <Sequence
            key={index}
            from={Math.round(startFrame)}
            durationInFrames={Math.round(durationInFrames)}
          >
            <CaptionPage page={page} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const HIGHLIGHT_COLOR = '#7C3AED';

const CaptionPage: React.FC<{
  page: { startMs: number; tokens: Array<{ text: string; fromMs: number; toMs: number }> };
}> = ({ page }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const currentTimeMs = (frame / fps) * 1000;
  const absoluteTimeMs = page.startMs + currentTimeMs;

  // Fade in animation
  const opacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

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
          padding: '12px 28px',
          maxWidth: '80%',
          opacity,
        }}
      >
        <div
          style={{
            fontSize: 38,
            fontWeight: 'bold',
            fontFamily,
            color: '#FFFFFF',
            textAlign: 'center',
            lineHeight: 1.5,
            textShadow: '0 2px 8px rgba(0,0,0,0.8)',
            whiteSpace: 'pre-wrap',
          }}
        >
          {page.tokens.map((token, i) => {
            const isActive =
              token.fromMs <= absoluteTimeMs && token.toMs > absoluteTimeMs;
            return (
              <span
                key={`${token.fromMs}-${i}`}
                style={{
                  color: isActive ? HIGHLIGHT_COLOR : '#FFFFFF',
                  transition: 'color 0.1s',
                }}
              >
                {token.text}
              </span>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
