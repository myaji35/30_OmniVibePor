import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Sequence,
  Img,
} from 'remotion';
import { VideoTemplateProps } from '../types';
import { HookScene, IntroScene, BodyScene, CTAScene, OutroScene } from '../scenes';

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
          from={block.startTime * 30}
          durationInFrames={block.duration * 30}
        >
          <SceneByType block={block} branding={branding} />
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

const SceneByType: React.FC<{
  block: VideoTemplateProps['blocks'][0];
  branding: VideoTemplateProps['branding'];
}> = ({ block, branding }) => {
  switch (block.type) {
    case 'hook':
      return <HookScene block={block} branding={branding} />;
    case 'intro':
      return <IntroScene block={block} branding={branding} />;
    case 'body':
      return <BodyScene block={block} branding={branding} />;
    case 'cta':
      return <CTAScene block={block} branding={branding} />;
    case 'outro':
      return <OutroScene block={block} branding={branding} />;
    default:
      return <BodyScene block={block} branding={branding} />;
  }
};
