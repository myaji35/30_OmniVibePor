import React from 'react';
import { Composition } from 'remotion';
import { YouTubeTemplate } from './templates/YouTubeTemplate';
import { AutoTemplate } from './templates/AutoTemplate';
import { InstagramTemplate } from './templates/InstagramTemplate';
import { TikTokTemplate } from './templates/TikTokTemplate';
import { PromoVideo } from './promo/PromoVideo';
import { ChopdPromo } from './promo/ChopdPromo';
import { InsureGraphPromo } from './promo/InsureGraphPromo';
import { BobotSafetyPromo } from './promo/BobotSafetyPromo';
import { LowVisionPromo, LOWVISION_TOTAL } from './promo/LowVisionPromo';
import { EN, KO } from './promo/i18n';
import type { VideoTemplateProps } from './types';
import { SmokeTestComposition } from './SmokeTest';

const calculateDuration = (
  props: VideoTemplateProps
): { durationInFrames: number } => {
  if (props.blocks.length === 0) {
    return { durationInFrames: 900 }; // 30 seconds default
  }
  const totalDuration = props.blocks.reduce(
    (max, b) => Math.max(max, b.startTime + b.duration),
    0
  );
  return { durationInFrames: Math.max(Math.ceil(totalDuration * 30), 30) };
};

const DEFAULT_PROPS: VideoTemplateProps = {
  blocks: [],
  audioUrl: '',
  branding: {
    logo: '',
    primaryColor: '#00A1E0',
  },
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Auto Template — 스크립트→영상 자동 생성 */}
      <Composition
        id="auto"
        component={AutoTemplate}
        durationInFrames={900}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={DEFAULT_PROPS}
        calculateMetadata={async ({ props }: { props: VideoTemplateProps }) => calculateDuration(props)}
      />

      {/* YouTube Template (1920x1080) */}
      <Composition
        id="youtube"
        component={YouTubeTemplate}
        durationInFrames={900}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={DEFAULT_PROPS}
        calculateMetadata={async ({ props }: { props: VideoTemplateProps }) => calculateDuration(props)}
      />

      {/* Instagram Template (1080x1350) */}
      <Composition
        id="instagram"
        component={InstagramTemplate}
        durationInFrames={900}
        fps={30}
        width={1080}
        height={1350}
        defaultProps={DEFAULT_PROPS}
        calculateMetadata={async ({ props }: { props: VideoTemplateProps }) => calculateDuration(props)}
      />

      {/* TikTok Template (1080x1920) */}
      <Composition
        id="tiktok"
        component={TikTokTemplate}
        durationInFrames={900}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={DEFAULT_PROPS}
        calculateMetadata={async ({ props }: { props: VideoTemplateProps }) => calculateDuration(props)}
      />
      {/* Promo — English (1920x1080, 45s) */}
      <Composition
        id="promo"
        component={PromoVideo}
        durationInFrames={1350}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ texts: EN }}
      />
      {/* Promo — 한국어 (1920x1080, 45s) */}
      <Composition
        id="promo-ko"
        component={PromoVideo}
        durationInFrames={1350}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ texts: KO }}
      />
      {/* InsureGraph Pro — 나레이션 싱크 (78s) */}
      <Composition
        id="insuregraph"
        component={InsureGraphPromo}
        durationInFrames={Math.ceil(78 * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      {/* 보봇 안전성 — 나레이션 싱크 (113s) */}
      <Composition
        id="bobot-safety"
        component={BobotSafetyPromo}
        durationInFrames={Math.ceil(113 * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      {/* 저시력인협회 — 나피디 홍보 영상 (85s) */}
      <Composition
        id="lowvision"
        component={LowVisionPromo}
        durationInFrames={LOWVISION_TOTAL}
        fps={30}
        width={1920}
        height={1080}
      />
      {/* chopd — 나레이션 싱크 (70s) */}
      <Composition
        id="chopd"
        component={ChopdPromo}
        durationInFrames={Math.ceil(70 * 30)}
        fps={30}
        width={1920}
        height={1080}
      />
      {/* ISS-162 — Phase B Gate G3-a smoke 테스트 (5s, 150 frames) */}
      <Composition
        id="SmokeTest"
        component={SmokeTestComposition}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
