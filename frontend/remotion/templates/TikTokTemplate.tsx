import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Sequence,
  Img,
} from 'remotion';
import { VideoTemplateProps } from '../types';
import { HookScene, IntroScene, BodyScene, CTAScene, OutroScene } from '../scenes';

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
          <SceneByType block={block} branding={branding} />
        </Sequence>
      ))}

      {/* Logo (Bottom Center) */}
      {branding.logo && (
        <AbsoluteFill
          style={{
            justifyContent: 'flex-end',
            alignItems: 'center',
            paddingBottom: 120
          }}
        >
          <Img src={branding.logo} style={{ width: 80, opacity: 0.85 }} />
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
