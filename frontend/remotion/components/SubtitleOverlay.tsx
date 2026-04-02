/**
 * SubtitleOverlay — Remotion 씬 위에 word-level 자막 렌더링
 *
 * WordTimestamp[]를 받아 현재 프레임에 맞는 단어를 하이라이트.
 * subtitleStyle에 따라 4가지 프리셋 적용.
 */
import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from 'remotion';
import { WordTimestamp } from '../types';

interface SubtitleOverlayProps {
  words: WordTimestamp[];
  style?: 'default' | 'bold-center' | 'lower-third' | 'karaoke';
  blockStartTime: number; // seconds — 씬 시작 시간 (글로벌)
}

export const SubtitleOverlay: React.FC<SubtitleOverlayProps> = ({
  words,
  style = 'default',
  blockStartTime,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 현재 프레임의 글로벌 시간 (초)
  const currentTime = blockStartTime + frame / fps;

  // 현재 표시할 단어들: 현재 시간 기준으로 활성 상태인 단어
  const activeWords = words.filter(
    (w) => currentTime >= w.start && currentTime <= w.end + 0.1
  );

  // 현재 하이라이트 중인 단어
  const currentWord = words.find(
    (w) => currentTime >= w.start && currentTime <= w.end
  );

  if (words.length === 0) return null;

  // 전체 문장을 구성 (자막이 보여야 할 시간 범위의 단어들)
  const visibleStart = Math.max(0, currentTime - 3);
  const visibleEnd = currentTime + 0.5;
  const visibleWords = words.filter(
    (w) => w.start >= visibleStart && w.start <= visibleEnd
  );

  if (style === 'karaoke') {
    return <KaraokeSubtitle words={words} currentTime={currentTime} fps={fps} frame={frame} />;
  }

  if (style === 'lower-third') {
    return <LowerThirdSubtitle words={visibleWords} currentWord={currentWord} frame={frame} fps={fps} />;
  }

  if (style === 'bold-center') {
    return <BoldCenterSubtitle words={visibleWords} currentWord={currentWord} frame={frame} fps={fps} />;
  }

  // default
  return <DefaultSubtitle words={visibleWords} currentWord={currentWord} frame={frame} fps={fps} />;
};

// ───── Default: 하단 중앙, 현재 단어 하이라이트 ─────
const DefaultSubtitle: React.FC<{
  words: WordTimestamp[];
  currentWord?: WordTimestamp;
  frame: number;
  fps: number;
}> = ({ words, currentWord, frame, fps }) => {
  const fadeIn = interpolate(frame, [0, 5], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-end',
        alignItems: 'center',
        paddingBottom: 80,
        opacity: fadeIn,
      }}
    >
      <div
        style={{
          background: 'rgba(0,0,0,0.7)',
          borderRadius: 8,
          padding: '12px 24px',
          maxWidth: '80%',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          gap: 6,
        }}
      >
        {words.map((w, i) => (
          <span
            key={i}
            style={{
              fontSize: 36,
              fontWeight: currentWord?.word === w.word && currentWord?.start === w.start ? 700 : 400,
              color: currentWord?.word === w.word && currentWord?.start === w.start ? '#00FF88' : '#FFFFFF',
              fontFamily: 'Inter, sans-serif',
              transition: 'color 0.1s',
            }}
          >
            {w.word}
          </span>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ───── Bold Center: 중앙 대형, 현재 단어 강조 ─────
const BoldCenterSubtitle: React.FC<{
  words: WordTimestamp[];
  currentWord?: WordTimestamp;
  frame: number;
  fps: number;
}> = ({ words, currentWord, frame, fps }) => (
  <AbsoluteFill
    style={{
      justifyContent: 'center',
      alignItems: 'center',
      padding: 60,
    }}
  >
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: 12,
        maxWidth: '85%',
      }}
    >
      {words.map((w, i) => {
        const isActive = currentWord?.word === w.word && currentWord?.start === w.start;
        const wordSpring = spring({
          frame: isActive ? 0 : 10,
          fps,
          config: { damping: 20, stiffness: 200 },
        });
        const scale = isActive ? interpolate(wordSpring, [0, 1], [1.1, 1]) : 1;

        return (
          <span
            key={i}
            style={{
              fontSize: 64,
              fontWeight: 800,
              color: isActive ? '#00FF88' : 'rgba(255,255,255,0.6)',
              fontFamily: 'Inter, sans-serif',
              textShadow: isActive ? '0 0 40px rgba(0,255,136,0.4)' : 'none',
              transform: `scale(${scale})`,
            }}
          >
            {w.word}
          </span>
        );
      })}
    </div>
  </AbsoluteFill>
);

// ───── Lower Third: 하단 좌측 L자형 ─────
const LowerThirdSubtitle: React.FC<{
  words: WordTimestamp[];
  currentWord?: WordTimestamp;
  frame: number;
  fps: number;
}> = ({ words, currentWord, frame, fps }) => {
  const slideIn = spring({ frame, fps, config: { damping: 18, stiffness: 150 } });
  const translateX = interpolate(slideIn, [0, 1], [-200, 0]);

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-end',
        alignItems: 'flex-start',
        paddingBottom: 60,
        paddingLeft: 60,
      }}
    >
      <div
        style={{
          background: 'linear-gradient(90deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 100%)',
          borderLeft: '4px solid #00FF88',
          padding: '16px 32px',
          maxWidth: '70%',
          transform: `translateX(${translateX}px)`,
          display: 'flex',
          flexWrap: 'wrap',
          gap: 6,
        }}
      >
        {words.map((w, i) => (
          <span
            key={i}
            style={{
              fontSize: 32,
              fontWeight: currentWord?.word === w.word && currentWord?.start === w.start ? 700 : 400,
              color: currentWord?.word === w.word && currentWord?.start === w.start ? '#00FF88' : '#E5E5E5',
              fontFamily: '"JetBrains Mono", monospace',
            }}
          >
            {w.word}
          </span>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ───── Karaoke: 단어별 순차 하이라이트 (가라오케) ─────
const KaraokeSubtitle: React.FC<{
  words: WordTimestamp[];
  currentTime: number;
  fps: number;
  frame: number;
}> = ({ words, currentTime, fps, frame }) => {
  // 현재 줄에 해당하는 단어 그룹 (5~8단어씩 묶기)
  const WORDS_PER_LINE = 6;
  const currentWordIdx = words.findIndex(
    (w) => currentTime >= w.start && currentTime <= w.end
  );
  const lineStart = Math.max(0, Math.floor((currentWordIdx >= 0 ? currentWordIdx : 0) / WORDS_PER_LINE) * WORDS_PER_LINE);
  const lineWords = words.slice(lineStart, lineStart + WORDS_PER_LINE);

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-end',
        alignItems: 'center',
        paddingBottom: 100,
      }}
    >
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          gap: 8,
          maxWidth: '80%',
        }}
      >
        {lineWords.map((w, i) => {
          const isPast = currentTime > w.end;
          const isActive = currentTime >= w.start && currentTime <= w.end;
          const progress = isActive
            ? Math.min(1, (currentTime - w.start) / (w.end - w.start))
            : isPast ? 1 : 0;

          return (
            <span
              key={lineStart + i}
              style={{
                fontSize: 48,
                fontWeight: 700,
                fontFamily: 'Inter, sans-serif',
                position: 'relative',
                color: 'rgba(255,255,255,0.3)',
                textShadow: '0 2px 8px rgba(0,0,0,0.8)',
              }}
            >
              {/* 하이라이트 오버레이 */}
              <span
                style={{
                  position: 'absolute',
                  inset: 0,
                  overflow: 'hidden',
                  width: `${progress * 100}%`,
                  color: '#00FF88',
                  whiteSpace: 'nowrap',
                }}
              >
                {w.word}
              </span>
              {w.word}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
