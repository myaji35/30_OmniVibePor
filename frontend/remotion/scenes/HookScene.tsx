import React from 'react';
import {
  AbsoluteFill,
  Img,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from 'remotion';
import { ScriptBlock, BrandingConfig } from '../types';

interface HookSceneProps {
  block: ScriptBlock;
  branding: BrandingConfig;
}

export const HookScene: React.FC<HookSceneProps> = ({ block, branding }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = block.text.split(' ');
  const primaryColor = branding.primaryColor || '#00A1E0';

  const containerOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ opacity: containerOpacity }}>
      {/* Background */}
      {block.backgroundUrl ? (
        <Img
          src={block.backgroundUrl}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      ) : (
        <AbsoluteFill
          style={{
            background: `radial-gradient(ellipse at center, ${primaryColor}22 0%, #0a0a0c 70%)`,
          }}
        />
      )}

      {/* Dark overlay for readability */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.4) 50%, rgba(0,0,0,0.7) 100%)',
        }}
      />

      {/* Staggered word animation */}
      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          padding: 80,
        }}
      >
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: block.textAlign || 'center',
            alignItems: 'center',
            gap: 16,
            maxWidth: '90%',
          }}
        >
          {words.map((word, i) => {
            const delay = i * 3; // ~100ms stagger at 30fps (3 frames)
            const wordSpring = spring({
              frame: frame - delay,
              fps,
              config: {
                damping: 15,
                mass: 0.8,
                stiffness: 120,
              },
            });

            const translateY = interpolate(wordSpring, [0, 1], [40, 0]);
            const opacity = interpolate(wordSpring, [0, 1], [0, 1]);

            return (
              <span
                key={i}
                style={{
                  fontSize: block.fontSize || 80,
                  fontWeight: 'bold',
                  color: block.textColor || primaryColor,
                  fontFamily: branding.fontFamily || 'Inter, sans-serif',
                  textShadow: `0 4px 30px rgba(0,0,0,0.9), 0 0 40px ${primaryColor}33`,
                  transform: `translateY(${translateY}px)`,
                  opacity,
                  lineHeight: 1.2,
                }}
              >
                {word}
              </span>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
