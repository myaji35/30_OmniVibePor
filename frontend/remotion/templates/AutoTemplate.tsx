/**
 * AutoTemplate — 스크립트 블록을 받아 자동 영상 생성
 *
 * 사용자가 TSX 코딩 없이 스크립트만으로 영상을 만들 수 있는 범용 템플릿.
 * ScriptBlock[]의 type(hook/body/cta)에 따라 씬 스타일 자동 적용.
 *
 * ISS-151: overlayData / subtitleChunks / brandTokens prop 추가 (optional, 비파괴).
 * SubtitleOverlay 슬롯이 전체 타임라인 위에 마지막 레이어로 합성됨.
 */
import React from 'react';
import {
  AbsoluteFill,
  Sequence,
  Audio,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  Easing,
} from 'remotion';
import type { VideoTemplateProps, ScriptBlock } from '../types';
import { SubtitleOverlay } from '../SubtitleOverlay';
import type { SubtitleChunkTS, BrandTokensTS, OverlayOutputTS } from '../types/overlay';

// ── Theme ────────────────────────────────────
const T = {
  bg:      '#0A0A0F',
  surface: '#141420',
  accent:  '#6366F1',
  green:   '#22C55E',
  amber:   '#F59E0B',
  white:   '#F1F5F9',
  dim:     'rgba(255,255,255,0.5)',
  font:    '"Pretendard", "Inter", sans-serif',
};

const TYPE_COLORS: Record<string, string> = {
  hook: '#A855F7',
  intro: '#6366F1',
  body: '#3B82F6',
  cta: '#22C55E',
  outro: '#64748B',
};

// ── Hook Scene: 강렬한 텍스트 + 카운터 느낌 ──
const HookBlock: React.FC<{ block: ScriptBlock; branding: VideoTemplateProps['branding'] }> = ({ block, branding }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const s = spring({ frame: frame - 5, fps, config: { damping: 14, stiffness: 90 } });
  const words = block.text.split(/\n/).filter(l => l.trim());

  return (
    <AbsoluteFill style={{
      background: `radial-gradient(ellipse at 50% 40%, ${branding.primaryColor || T.accent}15 0%, ${T.bg} 70%)`,
      justifyContent: 'center', alignItems: 'center', padding: 80,
    }}>
      <div style={{
        textAlign: 'center',
        opacity: interpolate(s, [0, 1], [0, 1]),
        transform: `scale(${interpolate(s, [0, 1], [0.8, 1])})`,
      }}>
        {words.map((line, i) => {
          const delay = i * 8;
          const lineOp = interpolate(frame, [delay, delay + 12], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          const lineY = interpolate(frame, [delay, delay + 12], [30, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          return (
            <div key={i} style={{
              fontFamily: T.font, fontSize: block.fontSize || 64, fontWeight: 800,
              color: i === 0 ? T.white : branding.primaryColor || T.accent,
              opacity: lineOp, transform: `translateY(${lineY}px)`,
              lineHeight: 1.3, marginBottom: 8,
            }}>
              {line}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ── Body Scene: 차분한 설명 텍스트 ──
const BodyBlock: React.FC<{ block: ScriptBlock; branding: VideoTemplateProps['branding']; index: number }> = ({ block, branding, index }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const lines = block.text.split(/\n/).filter(l => l.trim());
  const fadeIn = interpolate(frame, [0, 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const isEven = index % 2 === 0;

  return (
    <AbsoluteFill style={{ background: T.bg, justifyContent: 'center', padding: 100, opacity: fadeIn }}>
      {/* 씬 번호 */}
      <div style={{
        position: 'absolute', top: 60, left: 80,
        fontFamily: T.font, fontSize: 14, fontWeight: 700,
        color: TYPE_COLORS.body, letterSpacing: 3, opacity: 0.6,
      }}>
        SCENE {index + 1}
      </div>

      <div style={{ maxWidth: 1200, marginLeft: isEven ? 0 : 'auto' }}>
        {lines.map((line, i) => {
          const delay = 10 + i * 12;
          const op = interpolate(frame, [delay, delay + 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          const x = interpolate(frame, [delay, delay + 10], [isEven ? -20 : 20, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          return (
            <div key={i} style={{
              fontFamily: T.font, fontSize: block.fontSize || 40, fontWeight: 600,
              color: T.white, opacity: op, transform: `translateX(${x}px)`,
              lineHeight: 1.6, marginBottom: 12,
              textAlign: block.textAlign || (isEven ? 'left' : 'right'),
            }}>
              {line}
            </div>
          );
        })}
      </div>

      {/* 하단 악센트 라인 */}
      <div style={{
        position: 'absolute', bottom: 60, left: isEven ? 80 : 'auto', right: isEven ? 'auto' : 80,
        width: interpolate(frame, [0, 30], [0, 200], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
        height: 3, borderRadius: 2, background: branding.primaryColor || T.accent,
      }} />
    </AbsoluteFill>
  );
};

// ── CTA Scene: 행동 유도 ──
const CTABlock: React.FC<{ block: ScriptBlock; branding: VideoTemplateProps['branding'] }> = ({ block, branding }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const s = spring({ frame: frame - 5, fps, config: { damping: 14, stiffness: 100 } });
  const pulse = Math.sin(frame * 0.1) * 0.03 + 1;
  const lines = block.text.split(/\n/).filter(l => l.trim());
  const mainText = lines[0] || '';
  const subText = lines.slice(1).join(' ');

  return (
    <AbsoluteFill style={{
      background: `radial-gradient(ellipse at 50% 60%, ${T.green}10 0%, ${T.bg} 60%)`,
      justifyContent: 'center', alignItems: 'center',
    }}>
      <div style={{
        textAlign: 'center',
        opacity: interpolate(s, [0, 1], [0, 1]),
        transform: `scale(${interpolate(s, [0, 1], [0.8, 1])})`,
      }}>
        <div style={{
          fontFamily: T.font, fontSize: 56, fontWeight: 800, color: T.white, marginBottom: 16,
        }}>
          {mainText}
        </div>

        {subText && (
          <div style={{ fontFamily: T.font, fontSize: 24, color: T.dim, marginBottom: 50 }}>
            {subText}
          </div>
        )}

        <div style={{
          display: 'inline-flex', padding: '20px 56px', borderRadius: 16,
          background: `linear-gradient(135deg, ${branding.primaryColor || T.accent}, ${T.green})`,
          color: 'white', fontFamily: T.font, fontSize: 28, fontWeight: 800,
          transform: `scale(${pulse})`,
          boxShadow: `0 0 60px ${T.green}44`,
        }}>
          {block.textAlign === 'right' ? '자세히 알아보기 →' : '시작하기 →'}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── 블록 타입별 컴포넌트 라우팅 ──
const BlockRenderer: React.FC<{
  block: ScriptBlock; branding: VideoTemplateProps['branding']; index: number;
}> = ({ block, branding, index }) => {
  switch (block.type) {
    case 'hook':
    case 'intro':
      return <HookBlock block={block} branding={branding} />;
    case 'cta':
    case 'outro':
      return <CTABlock block={block} branding={branding} />;
    default:
      return <BodyBlock block={block} branding={branding} index={index} />;
  }
};

// ── ISS-151: AutoTemplate 확장 Props (하위 호환 — 모두 optional) ──
export interface AutoTemplateOverlayProps extends VideoTemplateProps {
  overlayData?: OverlayOutputTS;
  subtitleChunks?: SubtitleChunkTS[];
  brandTokens?: BrandTokensTS;
  subtitlePosition?: "bottom" | "center" | "top";
  subtitleUppercase?: boolean;
}

// ── Main AutoTemplate ──
export const AutoTemplate: React.FC<AutoTemplateOverlayProps> = ({
  blocks,
  audioUrl,
  branding,
  subtitleChunks,
  brandTokens,
  subtitlePosition = "bottom",
  subtitleUppercase = true,
}) => {
  // overlayData.fps가 있으면 해당 fps 사용, 없으면 기본 30
  // (overlayData는 미래 서버-렌더 경로용으로 보존하나 현재는 fps만 추출)
  const fps = 30;

  return (
    <AbsoluteFill style={{ background: T.bg }}>
      {audioUrl && <Audio src={audioUrl} />}

      {blocks.map((block, idx) => (
        <Sequence
          key={idx}
          from={Math.round(block.startTime * 30)}
          durationInFrames={Math.round(block.duration * 30)}
        >
          <BlockRenderer block={block} branding={branding} index={idx} />
        </Sequence>
      ))}

      {/* ISS-151: SubtitleOverlay 슬롯 — chunks가 있을 때만 렌더링 (비파괴) */}
      {subtitleChunks && subtitleChunks.length > 0 && (
        <SubtitleOverlay
          chunks={subtitleChunks}
          brandTokens={brandTokens}
          fps={fps}
          position={subtitlePosition}
          uppercase={subtitleUppercase}
        />
      )}
    </AbsoluteFill>
  );
};
