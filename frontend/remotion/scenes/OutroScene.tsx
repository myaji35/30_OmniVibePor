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

interface OutroSceneProps {
  block: ScriptBlock;
  branding: BrandingConfig;
}

export const OutroScene: React.FC<OutroSceneProps> = ({ block, branding }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const totalFrames = block.duration * fps;
  const primaryColor = branding.primaryColor || '#00A1E0';

  // Logo entrance
  const logoSpring = spring({
    frame,
    fps,
    config: {
      damping: 14,
      mass: 0.6,
      stiffness: 100,
    },
  });

  // Channel name fade in (delayed)
  const channelOpacity = interpolate(frame, [15, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Subscribe/Like text fade in (more delayed)
  const actionOpacity = interpolate(frame, [30, 45], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const actionTranslateY = interpolate(frame, [30, 45], [15, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Fade out in last 0.5 seconds (15 frames at 30fps)
  const fadeOutStart = totalFrames - 15;
  const fadeOut = interpolate(
    frame,
    [fadeOutStart, totalFrames],
    [1, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  return (
    <AbsoluteFill style={{ opacity: fadeOut }}>
      {/* Background */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at center, ${primaryColor}20 0%, #0a0a0c 60%)`,
        }}
      />

      {/* Logo + Channel Name */}
      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'column',
          gap: 30,
        }}
      >
        {/* Logo */}
        <div
          style={{
            transform: `scale(${logoSpring})`,
          }}
        >
          {branding.logo ? (
            <Img
              src={branding.logo}
              style={{
                width: 160,
                height: 'auto',
                filter: `drop-shadow(0 0 30px ${primaryColor}44)`,
              }}
            />
          ) : (
            <div
              style={{
                width: 120,
                height: 120,
                borderRadius: 28,
                background: `linear-gradient(135deg, ${primaryColor}, ${branding.secondaryColor || primaryColor}88)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: `0 0 50px ${primaryColor}33`,
              }}
            >
              <span
                style={{
                  fontSize: 50,
                  fontWeight: 'bold',
                  color: '#fff',
                  fontFamily: branding.fontFamily || 'Inter, sans-serif',
                }}
              >
                {block.text.charAt(0).toUpperCase()}
              </span>
            </div>
          )}
        </div>

        {/* Channel name / Title */}
        <div
          style={{
            opacity: channelOpacity,
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontSize: block.fontSize || 48,
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

        {/* Subscribe / Like actions */}
        <div
          style={{
            opacity: actionOpacity,
            transform: `translateY(${actionTranslateY}px)`,
            display: 'flex',
            gap: 40,
            marginTop: 20,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '12px 28px',
              backgroundColor: 'rgba(255,255,255,0.1)',
              borderRadius: 30,
              border: '1px solid rgba(255,255,255,0.2)',
            }}
          >
            {/* Bell icon */}
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFFFFF"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <span
              style={{
                fontSize: 20,
                fontWeight: 600,
                color: '#FFFFFF',
                fontFamily: branding.fontFamily || 'Inter, sans-serif',
              }}
            >
              Subscribe
            </span>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '12px 28px',
              backgroundColor: 'rgba(255,255,255,0.1)',
              borderRadius: 30,
              border: '1px solid rgba(255,255,255,0.2)',
            }}
          >
            {/* Thumbs up icon */}
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#FFFFFF"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
            </svg>
            <span
              style={{
                fontSize: 20,
                fontWeight: 600,
                color: '#FFFFFF',
                fontFamily: branding.fontFamily || 'Inter, sans-serif',
              }}
            >
              Like
            </span>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
