import React from 'react';
import { AbsoluteFill, Audio, Sequence, Img, useCurrentFrame, interpolate } from 'remotion';
import { VideoTemplateProps } from '../types';

export const TikTokTemplate: React.FC<VideoTemplateProps> = ({
  blocks,
  audioUrl,
  branding
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {/* Audio */}
      {audioUrl && <Audio src={audioUrl} />}

      {/* Scenes */}
      {blocks.map((block, idx) => (
        <Sequence
          key={idx}
          from={block.startTime * 30}
          durationInFrames={block.duration * 30}
        >
          <TikTokScene block={block} branding={branding} />
        </Sequence>
      ))}

      {/* Logo (Bottom Center) */}
      {branding.logo && (
        <AbsoluteFill
          style={{
            justifyContent: 'flex-end',
            alignItems: 'center',
            paddingBottom: 120 // Space for TikTok UI
          }}
        >
          <Img src={branding.logo} style={{ width: 80, opacity: 0.85 }} />
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

const TikTokScene: React.FC<{
  block: VideoTemplateProps['blocks'][0];
  branding: VideoTemplateProps['branding'];
}> = ({ block, branding }) => {
  const frame = useCurrentFrame();

  // Fast fade in (TikTok style)
  const opacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: 'clamp'
  });

  // Zoom in effect
  const scale = interpolate(frame, [0, 30], [1.1, 1], {
    extrapolateRight: 'clamp'
  });

  return (
    <AbsoluteFill style={{ opacity }}>
      {/* Background with zoom */}
      {block.backgroundUrl && (
        <div style={{ transform: `scale(${scale})`, width: '100%', height: '100%' }}>
          <Img
            src={block.backgroundUrl}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            }}
          />
        </div>
      )}

      {/* Subtle Gradient */}
      <AbsoluteFill
        style={{
          background: 'linear-gradient(to top, rgba(0,0,0,0.6), transparent 40%)'
        }}
      />

      {/* Text (Center - TikTok Caption Style) */}
      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          padding: 60
        }}
      >
        <div
          style={{
            fontSize: block.fontSize || 42,
            fontWeight: 'bold',
            color: '#FFFFFF',
            textAlign: 'center',
            textShadow: '0 3px 15px rgba(0,0,0,0.9)',
            maxWidth: '85%',
            lineHeight: 1.3,
            backgroundColor: 'rgba(0,0,0,0.4)',
            padding: '20px 30px',
            borderRadius: 12
          }}
        >
          {block.text}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
