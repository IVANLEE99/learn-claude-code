import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { loadFont } from '@remotion/google-fonts/NotoSansSC';
import { COLORS } from '../styles';

const { fontFamily } = loadFont();

interface TextOverlayProps {
  title: string;
  subtitle: string;
  features: string[];
  rating: number;
  color: string;
  efficiency: string;
}

export const TextOverlay: React.FC<TextOverlayProps> = ({
  title,
  subtitle,
  features,
  rating,
  color,
  efficiency,
}) => {
  const frame = useCurrentFrame();

  // Title slide in from left
  const titleX = interpolate(frame, [30, 60], [-200, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const titleOpacity = interpolate(frame, [30, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Subtitle fade in
  const subtitleOpacity = interpolate(frame, [50, 80], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Efficiency badge pop in
  const badgeScale = interpolate(frame, [70, 100], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.34, 1.56, 0.64, 1),
  });

  return (
    <div
      style={{
        position: 'absolute',
        left: 80,
        top: 120,
        width: 700,
        fontFamily,
      }}
    >
      {/* Tool name */}
      <div
        style={{
          fontSize: 72,
          fontWeight: 'bold',
          color: COLORS.textPrimary,
          transform: `translateX(${titleX}px)`,
          opacity: titleOpacity,
          textShadow: '0 4px 20px rgba(0,0,0,0.8)',
          marginBottom: 12,
        }}
      >
        {title}
      </div>

      {/* Subtitle */}
      <div
        style={{
          fontSize: 28,
          color: COLORS.textSecondary,
          opacity: subtitleOpacity,
          marginBottom: 30,
          textShadow: '0 2px 10px rgba(0,0,0,0.6)',
        }}
      >
        {subtitle}
      </div>

      {/* Efficiency badge */}
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 10,
          background: color,
          padding: '10px 24px',
          borderRadius: 12,
          marginBottom: 36,
          transform: `scale(${badgeScale})`,
          boxShadow: `0 4px 20px ${color}66`,
        }}
      >
        <span style={{ fontSize: 22, color: '#fff', fontWeight: 'bold' }}>
          效率提升
        </span>
        <span style={{ fontSize: 36, color: '#fff', fontWeight: 'bold' }}>
          {efficiency}
        </span>
      </div>

      {/* Features list */}
      {features.map((feature, i) => {
        const delay = 100 + i * 40;
        const featureOpacity = interpolate(frame, [delay, delay + 30], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        const featureX = interpolate(frame, [delay, delay + 30], [40, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        });

        return (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              marginBottom: 18,
              opacity: featureOpacity,
              transform: `translateX(${featureX}px)`,
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: color,
                flexShrink: 0,
                boxShadow: `0 0 8px ${color}88`,
              }}
            />
            <span
              style={{
                fontSize: 26,
                color: COLORS.textPrimary,
                textShadow: '0 2px 8px rgba(0,0,0,0.6)',
              }}
            >
              {feature}
            </span>
          </div>
        );
      })}

      {/* Star rating */}
      <div style={{ marginTop: 30, display: 'flex', gap: 6 }}>
        {Array.from({ length: 5 }).map((_, i) => {
          const starDelay = 260 + i * 10;
          const starScale = interpolate(
            frame,
            [starDelay, starDelay + 15],
            [0, 1],
            {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
              easing: Easing.bezier(0.34, 1.56, 0.64, 1),
            },
          );
          return (
            <span
              key={i}
              style={{
                fontSize: 32,
                transform: `scale(${starScale})`,
                display: 'inline-block',
              }}
            >
              {i < rating ? '\u2605' : '\u2606'}
            </span>
          );
        })}
      </div>
    </div>
  );
};
