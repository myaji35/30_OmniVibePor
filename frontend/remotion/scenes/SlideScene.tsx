import React from 'react';
import {
  AbsoluteFill,
  Img,
  Audio,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from 'remotion';
import { BrandingConfig } from '../types';

export interface SlideBlock {
  id?: number;
  slideIndex: number;
  slideImageUrl: string;   // PDF에서 추출된 슬라이드 이미지 URL
  script: string;          // 해당 슬라이드 스크립트
  audioUrl?: string;       // 슬라이드별 음성 URL
  startTime: number;       // seconds
  duration: number;        // seconds
  wordTimestamps?: { word: string; start: number; end: number }[];
}

export interface SlideVideoProps {
  slides: SlideBlock[];
  globalAudioUrl?: string;  // 전체 오디오 (슬라이드별 오디오가 없을 때)
  branding: BrandingConfig;
  showSubtitles?: boolean;
}

// 단어별 자막 컴포넌트
const WordSubtitle: React.FC<{
  words: { word: string; start: number; end: number }[];
  slideStartTime: number;
  primaryColor: string;
}> = ({ words, slideStartTime, primaryColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentSecond = frame / fps + slideStartTime;

  const currentWordIdx = words.findIndex(
    (w, i) => currentSecond >= w.start && (i === words.length - 1 || currentSecond < words[i + 1].start)
  );

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: 8,
        maxWidth: '90%',
      }}
    >
      {words.map((w, i) => (
        <span
          key={i}
          style={{
            fontSize: 36,
            fontWeight: i === currentWordIdx ? 'bold' : 'normal',
            color: i === currentWordIdx ? primaryColor : '#FFFFFF',
            transition: 'all 0.1s',
            textShadow: '0 2px 8px rgba(0,0,0,0.9)',
          }}
        >
          {w.word}
        </span>
      ))}
    </div>
  );
};

// 슬라이드 씬 컴포넌트
export const SlideScene: React.FC<{
  slide: SlideBlock;
  branding: BrandingConfig;
  showSubtitles?: boolean;
}> = ({ slide, branding, showSubtitles = true }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const primaryColor = branding.primaryColor || '#00A1E0';

  // 슬라이드 등장 애니메이션
  const slideIn = spring({ frame, fps, config: { damping: 200, stiffness: 100 } });
  const opacity = interpolate(slideIn, [0, 1], [0, 1]);

  // Ken Burns 효과 (미세 확대)
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.03], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 마지막 0.5초 페이드아웃
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 12, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const finalOpacity = Math.min(opacity, fadeOut);

  // 자막 등장
  const subtitleDelay = 8;
  const subtitleOpacity = interpolate(frame - subtitleDelay, [0, 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ opacity: finalOpacity }}>
      {/* 슬라이드 이미지 (Ken Burns) */}
      {slide.slideImageUrl ? (
        <AbsoluteFill style={{ transform: `scale(${scale})`, transformOrigin: 'center center' }}>
          <Img
            src={slide.slideImageUrl}
            style={{ width: '100%', height: '100%', objectFit: 'contain', background: '#FFFFFF' }}
          />
        </AbsoluteFill>
      ) : (
        <AbsoluteFill
          style={{
            background: `linear-gradient(135deg, #1a1a2e 0%, ${primaryColor}22 100%)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div style={{ fontSize: 80, fontWeight: 'bold', color: primaryColor, opacity: 0.3 }}>
            {slide.slideIndex + 1}
          </div>
        </AbsoluteFill>
      )}

      {/* 슬라이드 번호 뱃지 */}
      <div
        style={{
          position: 'absolute',
          top: 24,
          right: 24,
          padding: '8px 16px',
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(8px)',
          borderRadius: 24,
          color: '#FFFFFF',
          fontSize: 18,
          fontWeight: 'bold',
          fontFamily: branding.fontFamily || 'Inter, sans-serif',
          border: `1px solid ${primaryColor}66`,
        }}
      >
        {slide.slideIndex + 1}
      </div>

      {/* 자막 영역 */}
      {showSubtitles && slide.script && (
        <AbsoluteFill
          style={{
            justifyContent: 'flex-end',
            alignItems: 'center',
            padding: '0 80px 60px',
            opacity: subtitleOpacity,
          }}
        >
          <div
            style={{
              background: 'rgba(0,0,0,0.75)',
              backdropFilter: 'blur(12px)',
              borderRadius: 16,
              padding: '20px 32px',
              maxWidth: '90%',
              border: `1px solid ${primaryColor}33`,
            }}
          >
            {slide.wordTimestamps && slide.wordTimestamps.length > 0 ? (
              <WordSubtitle
                words={slide.wordTimestamps}
                slideStartTime={slide.startTime}
                primaryColor={primaryColor}
              />
            ) : (
              <div
                style={{
                  fontSize: 34,
                  color: '#FFFFFF',
                  textAlign: 'center',
                  fontFamily: branding.fontFamily || 'Inter, sans-serif',
                  lineHeight: 1.5,
                  textShadow: '0 2px 8px rgba(0,0,0,0.8)',
                }}
              >
                {slide.script}
              </div>
            )}
          </div>
        </AbsoluteFill>
      )}

      {/* 슬라이드별 오디오 */}
      {slide.audioUrl && <Audio src={slide.audioUrl} />}
    </AbsoluteFill>
  );
};
