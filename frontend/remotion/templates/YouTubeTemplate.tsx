import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Sequence,
  Img,
  useCurrentFrame,
  interpolate,
  spring,
  useVideoConfig
} from 'remotion';
import { VideoTemplateProps } from '../types';

export const YouTubeTemplate: React.FC<VideoTemplateProps> = ({
  blocks,
  audioUrl,
  branding
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {/* Zero-Fault Audio from ElevenLabs + Whisper */}
      {audioUrl && <Audio src={audioUrl} />}

      {/* Dynamic Scenes from Director Agent */}
      {blocks.map((block, idx) => (
        <Sequence
          key={idx}
          from={block.startTime * 30} // Convert seconds to frames (30fps)
          durationInFrames={block.duration * 30}
        >
          <SceneRenderer block={block} branding={branding} />
        </Sequence>
      ))}

      {/* Logo Watermark (Always Visible) */}
      {branding.logo && (
        <AbsoluteFill
          style={{
            justifyContent: 'flex-end',
            alignItems: 'flex-end',
            padding: 40
          }}
        >
          <Img
            src={branding.logo}
            style={{
              width: 120,
              height: 'auto',
              opacity: 0.8
            }}
          />
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

const SceneRenderer: React.FC<{
  block: VideoTemplateProps['blocks'][0];
  branding: VideoTemplateProps['branding'];
}> = ({ block, branding }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Animation: Fade in (0-0.5 seconds)
  const fadeInProgress = spring({
    frame,
    fps,
    config: {
      damping: 200
    }
  });

  // Animation: Slide up text
  const slideUpProgress = interpolate(
    frame,
    [0, 30], // 0-1 second
    [50, 0],
    {
      extrapolateRight: 'clamp'
    }
  );

  return (
    <AbsoluteFill>
      {/* Background Image/Video */}
      {block.backgroundUrl && (
        <Img
          src={block.backgroundUrl}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: fadeInProgress
          }}
        />
      )}

      {/* Gradient Overlay for Readability */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.5) 50%, transparent 100%)'
        }}
      />

      {/* Text Subtitle */}
      <AbsoluteFill
        style={{
          justifyContent: 'flex-end',
          alignItems: block.textAlign || 'center',
          padding: 100,
          opacity: fadeInProgress,
          transform: `translateY(${slideUpProgress}px)`
        }}
      >
        <div
          style={{
            fontSize: block.fontSize || 56,
            fontWeight: 'bold',
            color: block.textColor || '#FFFFFF',
            textAlign: block.textAlign || 'center',
            textShadow: '0 4px 30px rgba(0,0,0,0.9)',
            maxWidth: '90%',
            lineHeight: 1.3,
            fontFamily: branding.fontFamily || 'Inter, sans-serif'
          }}
        >
          {block.text}
        </div>
      </AbsoluteFill>

      {/* Block Type Indicator (Debug) */}
      {process.env.NODE_ENV === 'development' && (
        <div
          style={{
            position: 'absolute',
            top: 20,
            left: 20,
            backgroundColor: branding.primaryColor || '#00A1E0',
            color: 'white',
            padding: '8px 16px',
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 'bold',
            textTransform: 'uppercase'
          }}
        >
          {block.type}
        </div>
      )}
    </AbsoluteFill>
  );
};
