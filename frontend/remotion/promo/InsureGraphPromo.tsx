/**
 * InsureGraph Pro — 한글 홍보 영상 (50초, 남성 더빙 + BGM)
 *
 * "38,888개 약관을 학습한 AI가 고객의 보장을 분석합니다"
 * GraphRAG 기반 보험 분석 SaaS — 보험 전문가 톤
 */
import React from 'react';
import {
  AbsoluteFill,
  Sequence,
  Img,
  Audio,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  staticFile,
  Easing,
} from 'remotion';

// ── Theme — InsureGraph 브랜드 (Salesforce Blue 기반) ──
const C = {
  bg:      '#0F172A',      // 슬레이트 네이비
  surface: '#1E293B',
  accent:  '#6366F1',      // 인디고 (InsureGraph 메인)
  blue:    '#3B82F6',
  green:   '#22C55E',
  amber:   '#F59E0B',
  red:     '#EF4444',
  white:   '#F1F5F9',
  dim:     'rgba(255,255,255,0.5)',
  dimmer:  'rgba(255,255,255,0.3)',
  font:    '"Pretendard", "Inter", sans-serif',
  mono:    '"JetBrains Mono", monospace',
};

// ── Scene 1: 히어로 랜딩 (0–7s) ─────────────────
const LandingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame: frame - 10, fps, config: { damping: 14, stiffness: 90 } });
  const imgSpring = spring({ frame: frame - 5, fps, config: { damping: 18, stiffness: 80 } });

  // Counter animation: 0 → 38,888
  const count = Math.min(38888, Math.round(interpolate(frame, [30, 90], [0, 38888], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  })));

  return (
    <AbsoluteFill style={{ background: `linear-gradient(135deg, ${C.bg} 0%, ${C.surface} 100%)` }}>
      {/* 배경 이미지 (블러) */}
      <AbsoluteFill style={{ opacity: 0.15 }}>
        <Img src={staticFile('insuregraph/landing.png')} style={{
          width: '100%', height: '100%', objectFit: 'cover', filter: 'blur(20px)',
        }} />
      </AbsoluteFill>

      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{
          textAlign: 'center',
          opacity: interpolate(titleSpring, [0, 1], [0, 1]),
          transform: `scale(${interpolate(titleSpring, [0, 1], [0.8, 1])})`,
        }}>
          {/* 로고 */}
          <div style={{ fontFamily: C.font, fontSize: 28, fontWeight: 600, color: C.accent, letterSpacing: 4, marginBottom: 24 }}>
            INSUREGRAPH PRO
          </div>

          {/* 카운터 */}
          <div style={{ fontFamily: C.mono, fontSize: 100, fontWeight: 900, color: C.white, lineHeight: 1.1 }}>
            {count.toLocaleString()}
            <span style={{ fontSize: 48, color: C.dim }}>개</span>
          </div>
          <div style={{ fontFamily: C.font, fontSize: 48, fontWeight: 700, color: C.white, marginTop: 12 }}>
            약관을 학습한 AI가
          </div>
          <div style={{ fontFamily: C.font, fontSize: 48, fontWeight: 700 }}>
            고객의 <span style={{ color: C.accent }}>보장을 분석</span>합니다
          </div>
        </div>
      </AbsoluteFill>

      {/* 하단 태그 */}
      <div style={{
        position: 'absolute', bottom: 60, left: 0, right: 0,
        display: 'flex', justifyContent: 'center', gap: 16,
        opacity: interpolate(frame, [80, 100], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
      }}>
        {['#GraphRAG', '#보장분석AI', '#보험SaaS'].map((tag, i) => (
          <span key={i} style={{
            padding: '8px 20px', borderRadius: 24,
            background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.3)',
            fontFamily: C.font, fontSize: 16, fontWeight: 600, color: C.accent,
          }}>{tag}</span>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 2: AI 대시보드 (7–15s) ─────────────────
const DashboardScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const imgScale = spring({ frame: frame - 8, fps, config: { damping: 16, stiffness: 80 } });
  const rotateY = interpolate(frame, [0, 120], [-15, 5], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{ background: C.bg, perspective: 1400 }}>
      <div style={{
        position: 'absolute', top: 60, left: 80,
        fontFamily: C.mono, fontSize: 14, color: C.accent, letterSpacing: 4,
        opacity: interpolate(frame, [5, 20], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
      }}>
        AI 대시보드 · 다크 모드
      </div>

      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{
          transform: `rotateY(${rotateY}deg) scale(${interpolate(imgScale, [0, 1], [0.6, 1])})`,
          opacity: interpolate(imgScale, [0, 1], [0, 1]),
          borderRadius: 20, overflow: 'hidden',
          boxShadow: `0 60px 120px rgba(0,0,0,0.7), 0 0 60px ${C.accent}15`,
          border: '1px solid rgba(255,255,255,0.08)',
        }}>
          <Img src={staticFile('insuregraph/dashboard.png')} style={{ width: 1300, height: 'auto' }} />
        </div>
      </AbsoluteFill>

      {/* KPI 오버레이 */}
      <div style={{
        position: 'absolute', bottom: 60, right: 80,
        display: 'flex', gap: 28,
        opacity: interpolate(frame, [80, 100], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
      }}>
        {[
          { n: '32건', l: '오늘 상담', color: C.blue },
          { n: '98.7%', l: 'AI 정확도', color: C.green },
          { n: '0건', l: '긴급 알림', color: C.amber },
        ].map((k, i) => (
          <div key={i} style={{ textAlign: 'center' }}>
            <div style={{ fontFamily: C.mono, fontSize: 28, fontWeight: 800, color: k.color }}>{k.n}</div>
            <div style={{ fontFamily: C.font, fontSize: 13, color: C.dim }}>{k.l}</div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 3: 보장 분석 (15–23s) ──────────────────
const CoverageScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 좌측에서 슬라이드 인
  const slideIn = spring({ frame: frame - 5, fps, config: { damping: 18, stiffness: 90 } });
  const textOp = interpolate(frame, [50, 70], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <div style={{
        position: 'absolute', top: 60, left: 80,
        fontFamily: C.mono, fontSize: 14, color: C.green, letterSpacing: 4,
        opacity: interpolate(frame, [5, 20], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
      }}>
        보장 분석 · 라이트 모드
      </div>

      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{
          transform: `translateX(${interpolate(slideIn, [0, 1], [-200, 0])}px)`,
          opacity: interpolate(slideIn, [0, 1], [0, 1]),
          borderRadius: 20, overflow: 'hidden',
          boxShadow: '0 40px 100px rgba(0,0,0,0.5)',
          border: '1px solid rgba(255,255,255,0.06)',
        }}>
          <Img src={staticFile('insuregraph/coverage.png')} style={{ width: 1200, height: 'auto' }} />
        </div>
      </AbsoluteFill>

      {/* 설명 */}
      <div style={{
        position: 'absolute', bottom: 60, left: 80, opacity: textOp,
      }}>
        <div style={{ fontFamily: C.font, fontSize: 22, fontWeight: 700, color: C.white }}>
          카테고리별 보장 현황 · 위험 등급 · AI 개선 제안
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 4: 보장 갭 리포트 (23–31s) ─────────────
const ReportScene: React.FC = () => {
  const frame = useCurrentFrame();

  const scale = interpolate(frame, [0, 240], [1, 1.08], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const labelOp = interpolate(frame, [10, 30], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const textOp = interpolate(frame, [60, 80], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <div style={{
        position: 'absolute', top: 60, left: 80, zIndex: 10,
        fontFamily: C.mono, fontSize: 14, color: C.red, letterSpacing: 4, opacity: labelOp,
      }}>
        보장 갭 분석 리포트 · 다크 모드
      </div>

      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', overflow: 'hidden' }}>
        <div style={{
          borderRadius: 20, overflow: 'hidden',
          boxShadow: `0 40px 100px rgba(0,0,0,0.6), 0 0 40px ${C.red}10`,
          border: '1px solid rgba(255,255,255,0.06)',
          transform: `scale(${scale})`,
        }}>
          <Img src={staticFile('insuregraph/report.png')} style={{ width: 1100, height: 'auto' }} />
        </div>
      </AbsoluteFill>

      <div style={{
        position: 'absolute', bottom: 60, right: 80, opacity: textOp, textAlign: 'right',
      }}>
        <div style={{ fontFamily: C.font, fontSize: 22, fontWeight: 700, color: C.white }}>
          부족 보장 · 중복 보장 · 추천 상품
        </div>
        <div style={{ fontFamily: C.font, fontSize: 16, color: C.dim, marginTop: 6 }}>
          고객 맞춤형 리포트 자동 생성
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 5: 포트폴리오 분석 (31–39s) ────────────
const PortfolioScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const imgSpring = spring({ frame: frame - 8, fps, config: { damping: 16, stiffness: 90 } });
  const rotateX = interpolate(frame, [0, 120], [12, -2], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{ background: C.bg, perspective: 1200 }}>
      <div style={{
        position: 'absolute', top: 60, left: 80,
        fontFamily: C.mono, fontSize: 14, color: C.blue, letterSpacing: 4,
        opacity: interpolate(frame, [5, 20], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
      }}>
        포트폴리오 분석 · 시각화
      </div>

      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{
          transform: `rotateX(${rotateX}deg) scale(${interpolate(imgSpring, [0, 1], [0.7, 1])})`,
          opacity: interpolate(imgSpring, [0, 1], [0, 1]),
          borderRadius: 20, overflow: 'hidden',
          boxShadow: '0 60px 120px rgba(0,0,0,0.6)',
          border: '1px solid rgba(255,255,255,0.08)',
        }}>
          <Img src={staticFile('insuregraph/portfolio.png')} style={{ width: 1200, height: 'auto' }} />
        </div>
      </AbsoluteFill>

      {/* 차트 지표 */}
      <div style={{
        position: 'absolute', bottom: 60, left: 80,
        display: 'flex', gap: 32,
        opacity: interpolate(frame, [70, 90], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
      }}>
        {[
          { n: '32명', l: '관리 고객', color: C.accent },
          { n: '14.3만', l: '총 보험료', color: C.blue },
          { n: '13건', l: '갱신 예정', color: C.amber },
        ].map((k, i) => (
          <div key={i} style={{ textAlign: 'center' }}>
            <div style={{ fontFamily: C.mono, fontSize: 26, fontWeight: 800, color: k.color }}>{k.n}</div>
            <div style={{ fontFamily: C.font, fontSize: 13, color: C.dim }}>{k.l}</div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 6: CTA (39–50s) ────────────────────────
const CTAScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame: frame - 5, fps, config: { damping: 14, stiffness: 100 } });
  const pulse = Math.sin(frame * 0.1) * 0.03 + 1;
  const ringRotate = frame * 0.5;

  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 60%, ${C.accent}0D 0%, ${C.bg} 60%)` }}>
      {/* Animated rings */}
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <svg width={500} height={500} style={{ position: 'absolute', opacity: 0.2 }}>
          <circle cx={250} cy={250} r={220} fill="none" stroke={C.accent} strokeWidth={1}
            strokeDasharray="15 10" transform={`rotate(${ringRotate}, 250, 250)`} />
          <circle cx={250} cy={250} r={170} fill="none" stroke={C.blue} strokeWidth={1}
            strokeDasharray="10 15" transform={`rotate(${-ringRotate * 0.7}, 250, 250)`} />
        </svg>
      </AbsoluteFill>

      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{
          textAlign: 'center',
          opacity: interpolate(titleSpring, [0, 1], [0, 1]),
          transform: `scale(${interpolate(titleSpring, [0, 1], [0.8, 1])})`,
        }}>
          <div style={{ fontFamily: C.font, fontSize: 28, fontWeight: 600, color: C.dim, marginBottom: 16 }}>
            GraphRAG 기반 보험 분석 AI
          </div>
          <div style={{ fontFamily: C.font, fontSize: 72, fontWeight: 900, color: C.white, marginBottom: 12 }}>
            <span style={{ color: C.accent }}>InsureGraph</span> Pro
          </div>
          <div style={{ fontFamily: C.font, fontSize: 28, color: C.dim, marginBottom: 50 }}>
            상담 품질을 혁신합니다
          </div>

          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 12,
            padding: '22px 56px', borderRadius: 16,
            background: `linear-gradient(135deg, ${C.accent}, ${C.blue})`,
            color: 'white', fontFamily: C.font, fontSize: 28, fontWeight: 800,
            transform: `scale(${pulse})`,
            boxShadow: `0 0 60px ${C.accent}44, 0 20px 60px rgba(0,0,0,0.5)`,
          }}>
            무료 체험 시작하기 →
          </div>

          <div style={{
            marginTop: 40, display: 'flex', gap: 40, justifyContent: 'center',
            opacity: interpolate(frame, [40, 60], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
          }}>
            {['38,888개 약관 학습', 'AI 보장 갭 분석', '자동 리포트 생성'].map((f, i) => (
              <span key={i} style={{
                fontFamily: C.font, fontSize: 16, color: C.dimmer,
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
                <span style={{ color: C.green }}>✓</span> {f}
              </span>
            ))}
          </div>

          <div style={{
            marginTop: 30, fontFamily: C.mono, fontSize: 18, color: C.dimmer,
            opacity: interpolate(frame, [60, 80], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
          }}>
            insuregraph.com
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ── MAIN COMPOSITION ─────────────────────────────
export const InsureGraphPromo: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {/* BGM (D minor corporate) */}
      <Audio src={staticFile('insuregraph/bgm.wav')} volume={0.12} />
      {/* 남성 나레이션 (InJoon) */}
      <Audio src={staticFile('insuregraph/narration_full.mp3')} volume={0.9} />

      {/* Scene 1: 랜딩 히어로 (0–7s = 0–210f) */}
      <Sequence from={0} durationInFrames={210}>
        <LandingScene />
      </Sequence>

      {/* Scene 2: 대시보드 (7–15s = 210–450f) */}
      <Sequence from={210} durationInFrames={240}>
        <DashboardScene />
      </Sequence>

      {/* Scene 3: 보장 분석 (15–23s = 450–690f) */}
      <Sequence from={450} durationInFrames={240}>
        <CoverageScene />
      </Sequence>

      {/* Scene 4: 갭 리포트 (23–31s = 690–930f) */}
      <Sequence from={690} durationInFrames={240}>
        <ReportScene />
      </Sequence>

      {/* Scene 5: 포트폴리오 (31–39s = 930–1170f) */}
      <Sequence from={930} durationInFrames={240}>
        <PortfolioScene />
      </Sequence>

      {/* Scene 6: CTA (39–50s = 1170–1500f) */}
      <Sequence from={1170} durationInFrames={330}>
        <CTAScene />
      </Sequence>
    </AbsoluteFill>
  );
};
