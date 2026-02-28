import React from 'react';
import {
  AbsoluteFill,
  Img,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from 'remotion';
import { ScriptBlock, BrandingConfig } from '../types';

interface BodySceneProps {
  block: ScriptBlock;
  branding: BrandingConfig;
}

export const BodyScene: React.FC<BodySceneProps> = ({ block, branding }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const totalFrames = block.duration * fps;
  const accentColor = branding.secondaryColor || branding.primaryColor || '#00A1E0';

  // Ken Burns effect: slow zoom 1.0 -> 1.1
  const kenBurnsScale = interpolate(
    frame,
    [0, totalFrames],
    [1.0, 1.1],
    {
      extrapolateRight: 'clamp',
    }
  );

  // Subtitle container fade in
  const subtitleOpacity = interpolate(frame, [5, 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Split text into words for staggered fade
  const words = block.text.split(' ');

  return (
    <AbsoluteFill>
      {/* Background with Ken Burns effect */}
      {block.backgroundUrl ? (
        <div
          style={{
            width: '100%',
            height: '100%',
            transform: `scale(${kenBurnsScale})`,
            transformOrigin: 'center center',
          }}
        >
          <Img
            src={block.backgroundUrl}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        </div>
      ) : (
        <AbsoluteFill style={{ backgroundColor: '#0a0a0c' }} />
      )}

      {/* Gradient overlay for readability */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.4) 40%, transparent 70%)',
        }}
      />

      {/* Subtitle area at bottom */}
      <AbsoluteFill
        style={{
          justifyContent: 'flex-end',
          alignItems: block.textAlign || 'center',
          padding: 80,
          paddingBottom: 120,
          opacity: subtitleOpacity,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(0, 0, 0, 0.65)',
            backdropFilter: 'blur(10px)',
            borderRadius: 16,
            padding: '24px 40px',
            maxWidth: '90%',
          }}
        >
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: block.textAlign || 'center',
              gap: 8,
            }}
          >
            {words.map((word, i) => {
              const wordDelay = 5 + i * 2; // staggered fade per word
              const wordOpacity = interpolate(
                frame,
                [wordDelay, wordDelay + 8],
                [0, 1],
                {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                }
              );

              return (
                <span
                  key={i}
                  style={{
                    fontSize: block.fontSize || 48,
                    fontWeight: 'bold',
                    color: block.textColor || '#FFFFFF',
                    fontFamily: branding.fontFamily || 'Inter, sans-serif',
                    textShadow: '0 2px 20px rgba(0,0,0,0.8)',
                    opacity: wordOpacity,
                    lineHeight: 1.4,
                  }}
                >
                  {word}
                </span>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
