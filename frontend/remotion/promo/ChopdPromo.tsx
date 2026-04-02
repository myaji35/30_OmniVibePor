/**
 * chopd (imPD) — 한글 홍보 영상 (45초, 사운드 포함)
 *
 * "AI가 당신의 브랜드를 관리합니다"
 * 6개 씬 + 배경 음악 + 효과음 톤
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

// ── Theme — chopd 브랜드 컬러 ───────────────────
const C = {
  bg:      '#0B1628',      // 네이비 딥블루
  surface: '#132240',
  accent:  '#38BDF8',      // 스카이 블루 (chopd 메인)
  accentG: '#22D3EE',      // 시안
  white:   '#F8FAFC',
  dim:     'rgba(255,255,255,0.5)',
  dimmer:  'rgba(255,255,255,0.3)',
  font:    '"Pretendard", "Inter", sans-serif',
  mono:    '"JetBrains Mono", monospace',
};

// ── Scene 1: 타이틀 (0–6s) ───────────────────────
const TitleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame: frame - 10, fps, config: { damping: 14, stiffness: 90 } });
  const subOpacity = interpolate(frame, [50, 70], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const tagOpacity = interpolate(frame, [80, 100], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Floating particles
  const particles = Array.from({ length: 30 }, (_, i) => {
    const x = ((i * 173.5) % 1920);
    const y = ((i * 97.3) % 1080);
    const s = 2 + (i % 4);
    const o = interpolate(frame, [i * 2, i * 2 + 20], [0, 0.4], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    return { x, y: y + Math.sin(frame * 0.03 + i) * 15, s, o };
  });

  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 40% 40%, ${C.surface} 0%, ${C.bg} 70%)` }}>
      {particles.map((p, i) => (
        <div key={i} style={{
          position: 'absolute', left: p.x, top: p.y,
          width: p.s, height: p.s, borderRadius: '50%',
          background: i % 2 === 0 ? C.accent : C.accentG, opacity: p.o,
        }} />
      ))}

      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{
          textAlign: 'center',
          opacity: interpolate(titleSpring, [0, 1], [0, 1]),
          transform: `scale(${interpolate(titleSpring, [0, 1], [0.7, 1])})`,
        }}>
          {/* 로고 텍스트 */}
          <div style={{ fontFamily: C.font, fontSize: 32, fontWeight: 500, color: C.dim, marginBottom: 16, letterSpacing: 6 }}>
            AI 브랜드 매니저
          </div>
          <div style={{ fontFamily: C.font, fontSize: 120, fontWeight: 900, color: C.white, lineHeight: 1.1 }}>
            AI가 당신의
          </div>
          <div style={{ fontFamily: C.font, fontSize: 120, fontWeight: 900, lineHeight: 1.1 }}>
            <span style={{ color: C.accent }}>브랜드</span>
            <span style={{ color: C.white }}>를 관리합니다</span>
          </div>
        </div>

        {/* 서브 카피 */}
        <div style={{
          position: 'absolute', bottom: 160, opacity: subOpacity, textAlign: 'center',
        }}>
          <div style={{ fontFamily: C.font, fontSize: 28, color: C.dim, lineHeight: 1.6 }}>
            블로그, SNS, 쇼핑몰을 하나로.
          </div>
          <div style={{ fontFamily: C.font, fontSize: 28, color: C.dim }}>
            AI 콘텐츠를 자동 생성하고 예약 발행합니다.
          </div>
        </div>

        {/* 태그 */}
        <div style={{
          position: 'absolute', bottom: 80, display: 'flex', gap: 16, opacity: tagOpacity,
        }}>
          {['#AI콘텐츠', '#브랜드자동화', '#imPD'].map((tag, i) => (
            <span key={i} style={{
              padding: '8px 20px', borderRadius: 24,
              background: 'rgba(56,189,248,0.15)', border: '1px solid rgba(56,189,248,0.3)',
              fontFamily: C.font, fontSize: 18, fontWeight: 600, color: C.accent,
            }}>{tag}</span>
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ── Scene 2: 히어로 이미지 3D (6–13s) ─────────────
const HeroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const rotateY = interpolate(frame, [0, 120], [-20, 5], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });
  const scale = spring({ frame: frame - 8, fps, config: { damping: 16, stiffness: 80 } });
  const labelOp = interpolate(frame, [80, 100], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ background: C.bg, perspective: 1400 }}>
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{
          transform: `rotateY(${rotateY}deg) scale(${interpolate(scale, [0, 1], [0.6, 1])})`,
          opacity: interpolate(scale, [0, 1], [0, 1]),
          borderRadius: 20, overflow: 'hidden',
          boxShadow: `0 60px 120px rgba(0,0,0,0.7), 0 0 80px ${C.accent}15`,
          border: '1px solid rgba(255,255,255,0.08)',
        }}>
          <Img src={staticFile('chopd/hero.png')} style={{ width: 1300, height: 'auto' }} />
        </div>
      </AbsoluteFill>

      {/* 라벨 */}
      <div style={{
        position: 'absolute', top: 60, left: 80, opacity: labelOp,
        fontFamily: C.mono, fontSize: 14, color: C.accent, letterSpacing: 4,
      }}>
        데스크톱 · AI 대시보드
      </div>

      {/* KPI 오버레이 */}
      <div style={{
        position: 'absolute', bottom: 80, right: 100, opacity: labelOp,
        display: 'flex', gap: 32,
      }}>
        {[
          { n: '500+', l: '활성 사용자' },
          { n: '4.9/5', l: '만족도' },
          { n: '87%', l: '시간 절약' },
        ].map((k, i) => (
          <div key={i} style={{ textAlign: 'center' }}>
            <div style={{ fontFamily: C.font, fontSize: 36, fontWeight: 800, color: C.accent }}>{k.n}</div>
            <div style={{ fontFamily: C.font, fontSize: 14, color: C.dim }}>{k.l}</div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 3: 모바일 + 데스크톱 듀얼 뷰 (13–20s) ───
const DualViewScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const desktopSlide = spring({ frame: frame - 5, fps, config: { damping: 18, stiffness: 90 } });
  const mobileSlide = spring({ frame: frame - 25, fps, config: { damping: 18, stiffness: 90 } });
  const textOp = interpolate(frame, [60, 80], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <div style={{
        position: 'absolute', top: 60, left: 80,
        fontFamily: C.mono, fontSize: 14, color: C.accentG, letterSpacing: 4,
      }}>
        반응형 디자인
      </div>

      {/* Desktop */}
      <div style={{
        position: 'absolute', left: 80, top: '50%',
        transform: `translateY(-50%) translateX(${interpolate(desktopSlide, [0, 1], [-300, 0])}px)`,
        opacity: interpolate(desktopSlide, [0, 1], [0, 1]),
        borderRadius: 16, overflow: 'hidden',
        boxShadow: '0 40px 80px rgba(0,0,0,0.5)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}>
        <Img src={staticFile('chopd/desktop.png')} style={{ width: 900, height: 'auto' }} />
      </div>

      {/* Mobile */}
      <div style={{
        position: 'absolute', right: 120, top: '50%',
        transform: `translateY(-50%) translateX(${interpolate(mobileSlide, [0, 1], [200, 0])}px)`,
        opacity: interpolate(mobileSlide, [0, 1], [0, 1]),
        borderRadius: 24, overflow: 'hidden',
        boxShadow: '0 40px 80px rgba(0,0,0,0.5)',
        border: '2px solid rgba(255,255,255,0.08)',
      }}>
        <Img src={staticFile('chopd/mobile.png')} style={{ width: 320, height: 'auto' }} />
      </div>

      {/* 텍스트 */}
      <div style={{
        position: 'absolute', bottom: 60, left: 80, opacity: textOp,
      }}>
        <div style={{ fontFamily: C.font, fontSize: 24, fontWeight: 700, color: C.white }}>
          어디서든 브랜드를 관리하세요
        </div>
        <div style={{ fontFamily: C.font, fontSize: 16, color: C.dim, marginTop: 8 }}>
          데스크톱과 모바일, 완벽한 반응형 UX
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 4: 풀페이지 스크롤 (20–28s) — Ken Burns ──
const FullPageScrollScene: React.FC = () => {
  const frame = useCurrentFrame();

  // 긴 풀페이지를 위에서 아래로 스크롤
  const scrollY = interpolate(frame, [0, 240], [0, -1200], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.quad),
  });

  const labelOp = interpolate(frame, [10, 30], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <div style={{
        position: 'absolute', top: 60, left: 80, zIndex: 10,
        fontFamily: C.mono, fontSize: 14, color: '#FFB75D', letterSpacing: 4, opacity: labelOp,
      }}>
        풀페이지 스크롤
      </div>

      {/* Mask */}
      <div style={{
        position: 'absolute', left: '50%', top: '50%',
        transform: 'translate(-50%, -50%)',
        width: 1400, height: 800, overflow: 'hidden',
        borderRadius: 20, border: '1px solid rgba(255,255,255,0.08)',
        boxShadow: '0 40px 100px rgba(0,0,0,0.6)',
      }}>
        <Img src={staticFile('chopd/fullpage.png')} style={{
          width: '100%', transform: `translateY(${scrollY}px)`,
        }} />
      </div>

      {/* Gradient overlay top/bottom */}
      <div style={{
        position: 'absolute', left: '50%', top: '50%',
        transform: 'translate(-50%, -50%)',
        width: 1400, height: 800, borderRadius: 20,
        background: 'linear-gradient(180deg, rgba(11,22,40,0.6) 0%, transparent 15%, transparent 85%, rgba(11,22,40,0.6) 100%)',
        pointerEvents: 'none',
      }} />

      {/* 설명 */}
      <div style={{
        position: 'absolute', bottom: 50, right: 80, opacity: labelOp,
        fontFamily: C.font, fontSize: 20, fontWeight: 600, color: C.dim,
      }}>
        올인원 플랫폼 · 5개 섹션 · 원페이지 랜딩
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 5: WeWork 스타일 공간 (28–35s) ──────────
const WeWorkScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const imgScale = interpolate(frame, [0, 210], [1, 1.15], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const overlayOp = interpolate(frame, [40, 60], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const textSpring = spring({ frame: frame - 40, fps, config: { damping: 16, stiffness: 100 } });

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {/* Background image with slow zoom */}
      <AbsoluteFill style={{ overflow: 'hidden' }}>
        <Img src={staticFile('chopd/wework.png')} style={{
          width: '110%', height: '110%', objectFit: 'cover',
          transform: `scale(${imgScale})`,
        }} />
      </AbsoluteFill>

      {/* Dark overlay */}
      <AbsoluteFill style={{
        background: 'linear-gradient(180deg, rgba(11,22,40,0.4) 0%, rgba(11,22,40,0.85) 100%)',
      }} />

      {/* Text overlay */}
      <div style={{
        position: 'absolute', bottom: 120, left: 100,
        opacity: interpolate(textSpring, [0, 1], [0, 1]),
        transform: `translateY(${interpolate(textSpring, [0, 1], [40, 0])}px)`,
      }}>
        <div style={{ fontFamily: C.font, fontSize: 56, fontWeight: 800, color: C.white, marginBottom: 16 }}>
          당신의 AI 파트너,
        </div>
        <div style={{ fontFamily: C.font, fontSize: 56, fontWeight: 800, marginBottom: 24 }}>
          <span style={{ color: C.accent }}>imPD</span>
          <span style={{ color: C.white }}> 하나면 충분합니다</span>
        </div>
        <div style={{ fontFamily: C.font, fontSize: 22, color: C.dim, lineHeight: 1.6 }}>
          블로그 · SNS · 쇼핑몰 · 콘텐츠 자동 생성 · 예약 발행
        </div>
      </div>

      {/* Label */}
      <div style={{
        position: 'absolute', top: 60, left: 80, opacity: overlayOp,
        fontFamily: C.mono, fontSize: 14, color: C.accent, letterSpacing: 4,
      }}>
        AI 브랜드 자동화
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 6: CTA (35–45s) ────────────────────────
const CTAScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame: frame - 5, fps, config: { damping: 14, stiffness: 100 } });
  const pulse = Math.sin(frame * 0.1) * 0.03 + 1;
  const featOp = interpolate(frame, [40, 60], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Animated ring
  const ringRotate = frame * 0.5;

  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 60%, ${C.accent}0D 0%, ${C.bg} 60%)` }}>
      {/* Rings */}
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <svg width={500} height={500} style={{ position: 'absolute', opacity: 0.2 }}>
          <circle cx={250} cy={250} r={220} fill="none" stroke={C.accent} strokeWidth={1}
            strokeDasharray="15 10" transform={`rotate(${ringRotate}, 250, 250)`} />
          <circle cx={250} cy={250} r={170} fill="none" stroke={C.accentG} strokeWidth={1}
            strokeDasharray="10 15" transform={`rotate(${-ringRotate * 0.7}, 250, 250)`} />
        </svg>
      </AbsoluteFill>

      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{
          textAlign: 'center',
          opacity: interpolate(titleSpring, [0, 1], [0, 1]),
          transform: `scale(${interpolate(titleSpring, [0, 1], [0.8, 1])})`,
        }}>
          <div style={{ fontFamily: C.font, fontSize: 72, fontWeight: 900, color: C.white, marginBottom: 12 }}>
            지금 바로 시작하세요
          </div>
          <div style={{ fontFamily: C.font, fontSize: 28, color: C.dim, marginBottom: 50 }}>
            AI가 당신의 브랜드를 24시간 관리합니다
          </div>

          {/* CTA Button */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 12,
            padding: '22px 56px', borderRadius: 16,
            background: `linear-gradient(135deg, ${C.accent}, ${C.accentG})`,
            color: C.bg, fontFamily: C.font, fontSize: 28, fontWeight: 800,
            transform: `scale(${pulse})`,
            boxShadow: `0 0 60px ${C.accent}44, 0 20px 60px rgba(0,0,0,0.5)`,
          }}>
            무료로 시작하기 →
          </div>

          {/* Features */}
          <div style={{
            marginTop: 40, display: 'flex', gap: 40, justifyContent: 'center', opacity: featOp,
          }}>
            {['신용카드 불필요', '3분 안에 시작', '언제든 취소'].map((f, i) => (
              <span key={i} style={{
                fontFamily: C.font, fontSize: 16, color: C.dimmer,
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
                <span style={{ color: C.accent }}>✓</span> {f}
              </span>
            ))}
          </div>

          <div style={{
            marginTop: 30, fontFamily: C.mono, fontSize: 18, color: C.dimmer,
            opacity: interpolate(frame, [60, 80], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
          }}>
            chopd.io
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ── MAIN COMPOSITION ─────────────────────────────
// 나레이션 실측: s1=12.5s, s2=9.1s, s3=8.5s, s4=8.7s, s5=11.9s, s6=10.5s → 합계 61.1s
// 씬 duration = 나레이션 + 1초 버퍼
const CD = {
  s1: { from: 0,    dur: Math.ceil(13.5 * 30) },
  s2: { from: Math.ceil(13.5 * 30), dur: Math.ceil(10.1 * 30) },
  s3: { from: Math.ceil(23.6 * 30), dur: Math.ceil(9.5 * 30) },
  s4: { from: Math.ceil(33.1 * 30), dur: Math.ceil(9.7 * 30) },
  s5: { from: Math.ceil(42.8 * 30), dur: Math.ceil(12.9 * 30) },
  s6: { from: Math.ceil(55.7 * 30), dur: Math.ceil(11.5 * 30) },
};
const CD_TOTAL = CD.s6.from + CD.s6.dur + Math.ceil(3 * 30);

export const ChopdPromo: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <Audio src={staticFile('chopd/bgm.wav')} volume={0.15} />

      {/* 씬별 나레이션 (개별 MP3 → 정확한 싱크) */}
      <Sequence from={CD.s1.from}><Audio src={staticFile('chopd/narr_scene1.mp3')} volume={0.9} /></Sequence>
      <Sequence from={CD.s2.from}><Audio src={staticFile('chopd/narr_scene2.mp3')} volume={0.9} /></Sequence>
      <Sequence from={CD.s3.from}><Audio src={staticFile('chopd/narr_scene3.mp3')} volume={0.9} /></Sequence>
      <Sequence from={CD.s4.from}><Audio src={staticFile('chopd/narr_scene4.mp3')} volume={0.9} /></Sequence>
      <Sequence from={CD.s5.from}><Audio src={staticFile('chopd/narr_scene5.mp3')} volume={0.9} /></Sequence>
      <Sequence from={CD.s6.from}><Audio src={staticFile('chopd/narr_scene6.mp3')} volume={0.9} /></Sequence>

      <Sequence from={CD.s1.from} durationInFrames={CD.s1.dur}><TitleScene /></Sequence>
      <Sequence from={CD.s2.from} durationInFrames={CD.s2.dur}><HeroScene /></Sequence>
      <Sequence from={CD.s3.from} durationInFrames={CD.s3.dur}><DualViewScene /></Sequence>
      <Sequence from={CD.s4.from} durationInFrames={CD.s4.dur}><FullPageScrollScene /></Sequence>
      <Sequence from={CD.s5.from} durationInFrames={CD.s5.dur}><WeWorkScene /></Sequence>
      <Sequence from={CD.s6.from} durationInFrames={CD.s6.dur + Math.ceil(3 * 30)}><CTAScene /></Sequence>
    </AbsoluteFill>
  );
};

export const CD_TOTAL_FRAMES = CD_TOTAL;
