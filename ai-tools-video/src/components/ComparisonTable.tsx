import React from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';
import { loadFont } from '@remotion/google-fonts/NotoSansSC';
import { tools } from '../data/tools';
import { COLORS } from '../styles';

const { fontFamily } = loadFont();

const columns = ['工具', '类型', '核心优势', '效率提升', '评分'];

const rows = tools.map((t) => [
  t.name,
  t.id === 'claude-code'
    ? 'AI编程助手'
    : t.id === 'cursor'
      ? 'AI编辑器'
      : t.id === 'copilot'
        ? '代码补全'
        : t.id === 'v0'
          ? 'UI生成器'
          : '全栈构建器',
  t.features[0],
  t.efficiency,
  t.rating,
]);

export const ComparisonTable: React.FC = () => {
  const frame = useCurrentFrame();

  // Container fade in
  const containerOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Header slide down
  const headerY = interpolate(frame, [20, 50], [-60, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const headerOpacity = interpolate(frame, [20, 50], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Closing text
  const closingOpacity = interpolate(frame, [300, 340], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily,
        opacity: containerOpacity,
      }}
    >
      {/* Title */}
      <div
        style={{
          fontSize: 52,
          fontWeight: 'bold',
          color: COLORS.textPrimary,
          marginBottom: 40,
          transform: `translateY(${headerY}px)`,
          opacity: headerOpacity,
          textShadow: '0 4px 20px rgba(0,0,0,0.8)',
        }}
      >
        5大AI效率工具对比
      </div>

      {/* Table */}
      <div
        style={{
          width: 1600,
          background: COLORS.cardBg,
          borderRadius: 20,
          overflow: 'hidden',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        {/* Header row */}
        <div
          style={{
            display: 'flex',
            padding: '18px 24px',
            background: 'rgba(124, 58, 237, 0.3)',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          {columns.map((col, i) => (
            <div
              key={i}
              style={{
                flex: i === 0 ? 1.2 : 1,
                fontSize: 22,
                fontWeight: 'bold',
                color: COLORS.textPrimary,
                textAlign: i === 4 ? 'center' : 'left',
              }}
            >
              {col}
            </div>
          ))}
        </div>

        {/* Data rows */}
        {rows.map((row, rowIndex) => {
          const delay = 60 + rowIndex * 35;
          const rowOpacity = interpolate(frame, [delay, delay + 30], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const rowX = interpolate(frame, [delay, delay + 30], [-80, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          });

          const toolColor = tools[rowIndex].color;

          return (
            <div
              key={rowIndex}
              style={{
                display: 'flex',
                padding: '16px 24px',
                borderBottom:
                  rowIndex < rows.length - 1
                    ? '1px solid rgba(255,255,255,0.06)'
                    : 'none',
                opacity: rowOpacity,
                transform: `translateX(${rowX}px)`,
              }}
            >
              {/* Tool name with color dot */}
              <div
                style={{
                  flex: 1.2,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <div
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    background: toolColor,
                    boxShadow: `0 0 8px ${toolColor}88`,
                  }}
                />
                <span
                  style={{
                    fontSize: 22,
                    fontWeight: 'bold',
                    color: COLORS.textPrimary,
                  }}
                >
                  {row[0]}
                </span>
              </div>

              {/* Other columns */}
              {[1, 2, 3].map((colIdx) => (
                <div
                  key={colIdx}
                  style={{
                    flex: 1,
                    fontSize: 20,
                    color: COLORS.textSecondary,
                  }}
                >
                  {row[colIdx]}
                </div>
              ))}

              {/* Rating stars */}
              <div
                style={{
                  flex: 1,
                  textAlign: 'center',
                  fontSize: 22,
                  color: '#FBBF24',
                }}
              >
                {'\u2605'.repeat(row[4] as number)}
                {'\u2606'.repeat(5 - (row[4] as number))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Closing text */}
      <div
        style={{
          marginTop: 50,
          fontSize: 30,
          color: COLORS.textSecondary,
          opacity: closingOpacity,
          textShadow: '0 2px 10px rgba(0,0,0,0.6)',
        }}
      >
        工具不会让你变成高手，但能让你有更多时间思考真正重要的事
      </div>
    </div>
  );
};
