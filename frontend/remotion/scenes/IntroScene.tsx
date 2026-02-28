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

interface IntroSceneProps {
  block: ScriptBlock;
  branding: BrandingConfig;
}

export const IntroScene: React.FC<IntroSceneProps> = ({ block, branding }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const primaryColor = branding.primaryColor || '#00A1E0';

  // Logo scale spring animation
  const logoScale = spring({
    frame,
    fps,
    config: {
      damping: 12,
      mass: 0.6,
      stiffness: 100,
    },
  });

  // Text fade in after logo
  const textOpacity = interpolate(frame, [15, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const textTranslateY = interpolate(frame, [15, 30], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill>
      {/* Radial gradient background based on brand color */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at center, ${primaryColor}30 0%, ${primaryColor}10 30%, #0a0a0c 70%)`,
        }}
      />

      {/* Background image if provided */}
      {block.backgroundUrl && (
        <Img
          src={block.backgroundUrl}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: 0.3,
          }}
        />
      )}

      {/* Logo or Title */}
      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'column',
          gap: 40,
        }}
      >
        {branding.logo ? (
          <div
            style={{
              transform: `scale(${logoScale})`,
            }}
          >
            <Img
              src={branding.logo}
              style={{
                width: 200,
                height: 'auto',
                filter: `drop-shadow(0 0 40px ${primaryColor}66)`,
              }}
            />
          </div>
        ) : (
          <div
            style={{
              transform: `scale(${logoScale})`,
              width: 140,
              height: 140,
              borderRadius: 32,
              background: `linear-gradient(135deg, ${primaryColor}, ${branding.secondaryColor || primaryColor}88)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: `0 0 60px ${primaryColor}44`,
            }}
          >
            <span
              style={{
                fontSize: 60,
                fontWeight: 'bold',
                color: '#fff',
                fontFamily: branding.fontFamily || 'Inter, sans-serif',
              }}
            >
              {block.text.charAt(0).toUpperCase()}
            </span>
          </div>
        )}

        {/* Title text */}
        <div
          style={{
            opacity: textOpacity,
            transform: `translateY(${textTranslateY}px)`,
            textAlign: 'center',
            maxWidth: '80%',
          }}
        >
          <div
            style={{
              fontSize: block.fontSize || 56,
              fontWeight: 'bold',
              color: block.textColor || '#FFFFFF',
              fontFamily: branding.fontFamily || 'Inter, sans-serif',
              textShadow: '0 4px 30px rgba(0,0,0,0.8)',
              lineHeight: 1.3,
            }}
          >
            {block.text}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
