import React from 'react';
import {
  useCurrentFrame,
  interpolate,
  Img,
  staticFile,
  AbsoluteFill,
} from 'remotion';
import { ComparisonTable } from '../components/ComparisonTable';
import { COLORS } from '../styles';

export const Scene7Summary: React.FC = () => {
  const frame = useCurrentFrame();

  // Background Ken Burns
  const scale = interpolate(frame, [0, 1350], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Background fade in
  const bgOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill>
      {/* Background image */}
      <AbsoluteFill
        style={{
          opacity: bgOpacity,
          transform: `scale(${scale})`,
        }}
      >
        <Img
          src={staticFile('images/scene7_summary.png')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </AbsoluteFill>

      {/* Dark overlay for readability */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at center, ${COLORS.background}dd 0%, ${COLORS.background}f5 100%)`,
        }}
      />

      {/* Comparison table */}
      <ComparisonTable />
    </AbsoluteFill>
  );
};
