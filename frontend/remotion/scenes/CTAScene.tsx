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

interface CTASceneProps {
  block: ScriptBlock;
  branding: BrandingConfig;
}

export const CTAScene: React.FC<CTASceneProps> = ({ block, branding }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const primaryColor = branding.primaryColor || '#00A1E0';

  // Text entrance spring
  const textSpring = spring({
    frame,
    fps,
    config: {
      damping: 14,
      mass: 0.8,
      stiffness: 100,
    },
  });

  const textScale = interpolate(textSpring, [0, 1], [0.8, 1]);
  const textOpacity = interpolate(textSpring, [0, 1], [0, 1]);

  // CTA button pulse animation (looping)
  const pulsePhase = (frame % 30) / 30; // 1-second loop at 30fps
  const pulseScale = interpolate(
    Math.sin(pulsePhase * Math.PI * 2),
    [-1, 1],
    [1.0, 1.05]
  );

  // Button fade in (delayed)
  const buttonOpacity = interpolate(frame, [20, 35], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Arrow bounce animation
  const bouncePhase = (frame % 20) / 20;
  const arrowTranslateY = interpolate(
    Math.sin(bouncePhase * Math.PI * 2),
    [-1, 1],
    [-8, 8]
  );

  return (
    <AbsoluteFill>
      {/* Background */}
      {block.backgroundUrl ? (
        <>
          <Img
            src={block.backgroundUrl}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              opacity: 0.4,
            }}
          />
          <AbsoluteFill
            style={{
              background: `radial-gradient(circle at center, ${primaryColor}20 0%, rgba(0,0,0,0.8) 70%)`,
            }}
          />
        </>
      ) : (
        <AbsoluteFill
          style={{
            background: `radial-gradient(circle at center, ${primaryColor}25 0%, #0a0a0c 60%)`,
          }}
        />
      )}

      {/* CTA Content */}
      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'column',
          gap: 50,
        }}
      >
        {/* Main CTA text */}
        <div
          style={{
            transform: `scale(${textScale})`,
            opacity: textOpacity,
            textAlign: 'center',
            maxWidth: '80%',
          }}
        >
          <div
            style={{
              fontSize: block.fontSize || 64,
              fontWeight: 'bold',
              color: block.textColor || '#FFFFFF',
              fontFamily: branding.fontFamily || 'Inter, sans-serif',
              textShadow: `0 4px 30px rgba(0,0,0,0.8), 0 0 60px ${primaryColor}33`,
              lineHeight: 1.3,
            }}
          >
            {block.text}
          </div>
        </div>

        {/* CTA Button */}
        <div
          style={{
            opacity: buttonOpacity,
            transform: `scale(${pulseScale})`,
          }}
        >
          <div
            style={{
              background: `linear-gradient(135deg, ${primaryColor}, ${branding.secondaryColor || primaryColor})`,
              padding: '20px 60px',
              borderRadius: 50,
              boxShadow: `0 10px 40px ${primaryColor}55, 0 0 80px ${primaryColor}22`,
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <span
              style={{
                fontSize: 28,
                fontWeight: 'bold',
                color: '#FFFFFF',
                fontFamily: branding.fontFamily || 'Inter, sans-serif',
                letterSpacing: 1,
              }}
            >
              Click Here
            </span>

            {/* Arrow icon */}
            <div
              style={{
                transform: `translateY(${arrowTranslateY}px)`,
              }}
            >
              <svg
                width="28"
                height="28"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#FFFFFF"
                strokeWidth={2.5}
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="12" y1="5" x2="12" y2="19" />
                <polyline points="19 12 12 19 5 12" />
              </svg>
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
