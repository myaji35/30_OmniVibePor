import React from 'react';
import { AbsoluteFill, Audio, Sequence, Img, useCurrentFrame, interpolate } from 'remotion';
import { VideoTemplateProps } from '../types';

export const InstagramTemplate: React.FC<VideoTemplateProps> = ({
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
          <InstagramScene block={block} branding={branding} />
        </Sequence>
      ))}

      {/* Logo (Top Center) */}
      {branding.logo && (
        <AbsoluteFill
          style={{
            justifyContent: 'flex-start',
            alignItems: 'center',
            padding: 30
          }}
        >
          <Img src={branding.logo} style={{ width: 100, opacity: 0.9 }} />
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

const InstagramScene: React.FC<{
  block: VideoTemplateProps['blocks'][0];
  branding: VideoTemplateProps['branding'];
}> = ({ block, branding }) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: 'clamp'
  });

  return (
    <AbsoluteFill style={{ opacity }}>
      {/* Background */}
      {block.backgroundUrl && (
        <Img
          src={block.backgroundUrl}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover'
          }}
        />
      )}

      {/* Gradient Overlay */}
      <AbsoluteFill
        style={{
          background: 'linear-gradient(to bottom, rgba(0,0,0,0.7), transparent 30%, rgba(0,0,0,0.8) 80%)'
        }}
      />

      {/* Text (Bottom Third) */}
      <AbsoluteFill
        style={{
          justifyContent: 'flex-end',
          alignItems: 'center',
          padding: 80
        }}
      >
        <div
          style={{
            fontSize: block.fontSize || 48,
            fontWeight: 'bold',
            color: '#FFFFFF',
            textAlign: 'center',
            textShadow: '0 2px 20px rgba(0,0,0,0.8)',
            maxWidth: '90%',
            lineHeight: 1.2
          }}
        >
          {block.text}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
