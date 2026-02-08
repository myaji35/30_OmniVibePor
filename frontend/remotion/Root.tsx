import { Composition } from 'remotion';
import { YouTubeTemplate } from './templates/YouTubeTemplate';
import { InstagramTemplate } from './templates/InstagramTemplate';
import { TikTokTemplate } from './templates/TikTokTemplate';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* YouTube Template (1920x1080) */}
      <Composition
        id="youtube"
        component={YouTubeTemplate}
        durationInFrames={900} // 30 seconds @ 30fps
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          blocks: [],
          audioUrl: '',
          branding: {
            logo: '',
            primaryColor: '#00A1E0'
          }
        }}
      />

      {/* Instagram Template (1080x1350) */}
      <Composition
        id="instagram"
        component={InstagramTemplate}
        durationInFrames={900}
        fps={30}
        width={1080}
        height={1350}
        defaultProps={{
          blocks: [],
          audioUrl: '',
          branding: {
            logo: '',
            primaryColor: '#00A1E0'
          }
        }}
      />

      {/* TikTok Template (1080x1920) */}
      <Composition
        id="tiktok"
        component={TikTokTemplate}
        durationInFrames={900}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          blocks: [],
          audioUrl: '',
          branding: {
            logo: '',
            primaryColor: '#00A1E0'
          }
        }}
      />
    </>
  );
};
