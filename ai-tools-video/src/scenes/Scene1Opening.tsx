import React from 'react';
import {
  useCurrentFrame,
  interpolate,
  Easing,
  Img,
  staticFile,
  AbsoluteFill,
} from 'remotion';
import { loadFont } from '@remotion/google-fonts/NotoSansSC';
import { COLORS } from '../styles';
import { tools } from '../data/tools';

const { fontFamily } = loadFont();

export const Scene1Opening: React.FC = () => {
  const frame = useCurrentFrame();

  // Ken Burns slow zoom
  const scale = interpolate(frame, [0, 900], [1.0, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Background fade in
  const bgOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Title slide up from bottom
  const titleY = interpolate(frame, [40, 90], [80, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const titleOpacity = interpolate(frame, [40, 90], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Subtitle fade in
  const subtitleOpacity = interpolate(frame, [80, 120], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Divider line width animation
  const dividerWidth = interpolate(frame, [100, 160], [0, 400], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  return (
    <AbsoluteFill>
      {/* Background image with Ken Burns */}
      <AbsoluteFill
        style={{
          opacity: bgOpacity,
          transform: `scale(${scale})`,
        }}
      >
        <Img
          src={staticFile('images/scene1_opening.png')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </AbsoluteFill>

      {/* Dark overlay */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(135deg, rgba(15,23,42,0.85) 0%, rgba(15,23,42,0.5) 50%, rgba(15,23,42,0.85) 100%)',
        }}
      />

      {/* Content */}
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily,
        }}
      >
        {/* Main title */}
        <div
          style={{
            fontSize: 80,
            fontWeight: 'bold',
            color: COLORS.textPrimary,
            transform: `translateY(${titleY}px)`,
            opacity: titleOpacity,
            textShadow: '0 4px 30px rgba(0,0,0,0.8)',
            textAlign: 'center',
            lineHeight: 1.2,
          }}
        >
          5个让效率翻倍的
          <br />
          <span style={{ color: '#7C3AED' }}>AI工具</span>实测
        </div>

        {/* Divider */}
        <div
          style={{
            width: dividerWidth,
            height: 3,
            background: 'linear-gradient(90deg, transparent, #7C3AED, transparent)',
            marginTop: 30,
            marginBottom: 30,
          }}
        />

        {/* Subtitle */}
        <div
          style={{
            fontSize: 32,
            color: COLORS.textSecondary,
            opacity: subtitleOpacity,
            textShadow: '0 2px 10px rgba(0,0,0,0.6)',
          }}
        >
          程序员必看 | 亲测有效 | 效率提升指南
        </div>

        {/* Tool icons row */}
        <div
          style={{
            display: 'flex',
            gap: 40,
            marginTop: 60,
          }}
        >
          {tools.map((tool, i) => {
            const iconDelay = 150 + i * 30;
            const iconOpacity = interpolate(
              frame,
              [iconDelay, iconDelay + 30],
              [0, 1],
              {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              },
            );
            const iconY = interpolate(
              frame,
              [iconDelay, iconDelay + 30],
              [30, 0],
              {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
                easing: Easing.bezier(0.16, 1, 0.3, 1),
              },
            );

            return (
              <div
                key={tool.id}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 10,
                  opacity: iconOpacity,
                  transform: `translateY(${iconY}px)`,
                }}
              >
                <div
                  style={{
                    width: 60,
                    height: 60,
                    borderRadius: 16,
                    background: tool.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 24,
                    fontWeight: 'bold',
                    color: '#fff',
                    boxShadow: `0 4px 20px ${tool.color}66`,
                  }}
                >
                  {tool.name.charAt(0)}
                </div>
                <span
                  style={{
                    fontSize: 16,
                    color: COLORS.textSecondary,
                  }}
                >
                  {tool.name}
                </span>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
