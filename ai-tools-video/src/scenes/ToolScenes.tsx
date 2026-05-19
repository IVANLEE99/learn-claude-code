import React from 'react';
import {
  useCurrentFrame,
  interpolate,
  Img,
  staticFile,
  AbsoluteFill,
} from 'remotion';
import { TextOverlay } from '../components/TextOverlay';
import { tools } from '../data/tools';
import { COLORS } from '../styles';

interface ToolSceneProps {
  toolIndex: number;
}

const ToolScene: React.FC<ToolSceneProps> = ({ toolIndex }) => {
  const frame = useCurrentFrame();
  const tool = tools[toolIndex];

  // Background image Ken Burns pan
  const scale = interpolate(frame, [0, 1350], [1.0, 1.12], {
    extrapolateRight: 'clamp',
  });
  const panX = interpolate(frame, [0, 1350], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Background fade in
  const bgOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Right side accent bar
  const barHeight = interpolate(frame, [60, 150], [0, 600], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill>
      {/* Background image */}
      <AbsoluteFill
        style={{
          opacity: bgOpacity,
          transform: `scale(${scale}) translateX(${panX}px)`,
        }}
      >
        <Img
          src={staticFile(`images/${tool.image}`)}
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
          background: `linear-gradient(90deg, ${COLORS.background}ee 0%, ${COLORS.background}cc 40%, transparent 70%)`,
        }}
      />

      {/* Right accent bar */}
      <div
        style={{
          position: 'absolute',
          right: 0,
          top: '50%',
          transform: 'translateY(-50%)',
          width: 6,
          height: barHeight,
          background: tool.color,
          boxShadow: `0 0 30px ${tool.color}88`,
        }}
      />

      {/* Text overlay */}
      <TextOverlay
        title={tool.name}
        subtitle={tool.subtitle}
        features={tool.features}
        rating={tool.rating}
        color={tool.color}
        efficiency={tool.efficiency}
      />
    </AbsoluteFill>
  );
};

export const Scene2ClaudeCode: React.FC = () => <ToolScene toolIndex={0} />;
export const Scene3Cursor: React.FC = () => <ToolScene toolIndex={1} />;
export const Scene4Copilot: React.FC = () => <ToolScene toolIndex={2} />;
export const Scene5V0: React.FC = () => <ToolScene toolIndex={3} />;
export const Scene6Bolt: React.FC = () => <ToolScene toolIndex={4} />;
