/**
 * 한국저시력인협회 홍보 영상 — "보이지 않는 곳에서 보이는 변화" (80초)
 *
 * 나피디(NaPD) x 저시력인협회 시나리오
 * 남성 더빙 (InJoon, 차분한 톤) + A minor BGM
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
  staticFile,
  Easing,
} from 'remotion';

const C = {
  bg:      '#0B1120',
  surface: '#152238',
  accent:  '#60A5FA',   // 소프트 블루 (접근성/신뢰)
  warm:    '#F59E0B',   // 따뜻한 앰버
  green:   '#34D399',
  white:   '#F1F5F9',
  dim:     'rgba(255,255,255,0.5)',
  dimmer:  'rgba(255,255,255,0.3)',
  font:    '"Pretendard", "Inter", sans-serif',
  mono:    '"JetBrains Mono", monospace',
};

// ── Scene 1: Hook — 흐릿한 시야 시뮬레이션 (0–14.4s) ──
const HookScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 블러 효과: 시작 시 흐릿 → 점점 선명
  const blur = interpolate(frame, [0, 120], [20, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const titleOp = interpolate(frame, [30, 50], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const statOp = interpolate(frame, [80, 100], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // 카운터: 0 → 250,000
  const count = Math.round(interpolate(frame, [80, 130], [0, 250000], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  }));

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {/* 블러 오버레이 (저시력 시뮬레이션) */}
      <AbsoluteFill style={{
        background: `radial-gradient(ellipse at 50% 50%, ${C.accent}15 0%, ${C.bg} 60%)`,
        filter: `blur(${blur}px)`,
      }}>
        <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
          <div style={{ textAlign: 'center', opacity: titleOp }}>
            <div style={{ fontFamily: C.font, fontSize: 72, fontWeight: 900, color: C.white, lineHeight: 1.2 }}>
              당신의 눈앞이
            </div>
            <div style={{ fontFamily: C.font, fontSize: 72, fontWeight: 900, lineHeight: 1.2 }}>
              <span style={{ color: C.accent }}>흐릿하게</span>
              <span style={{ color: C.white }}> 보인다면?</span>
            </div>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>

      {/* 통계 */}
      <div style={{
        position: 'absolute', bottom: 80, left: 0, right: 0,
        display: 'flex', justifyContent: 'center', gap: 60, opacity: statOp,
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontFamily: C.mono, fontSize: 48, fontWeight: 900, color: C.warm }}>{count.toLocaleString()}</div>
          <div style={{ fontFamily: C.font, fontSize: 18, color: C.dim }}>대한민국 시각장애인</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontFamily: C.mono, fontSize: 48, fontWeight: 900, color: C.accent }}>85%</div>
          <div style={{ fontFamily: C.font, fontSize: 18, color: C.dim }}>저시력인 비율</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 2: 문제 — 저시력이란? (14.4–34s) ──
const ProblemScene: React.FC = () => {
  const frame = useCurrentFrame();

  const items = [
    { label: '흐릿하게 보이는 세상', delay: 10 },
    { label: '좁은 시야, 한쪽만 보이는 세상', delay: 60 },
    { label: '안경으로도 수술로도 회복 불가', delay: 120 },
    { label: '대부분의 사람들은 모릅니다', delay: 180 },
  ];

  return (
    <AbsoluteFill style={{ background: C.bg, justifyContent: 'center', padding: 120 }}>
      <div style={{ fontFamily: C.font, fontSize: 20, color: C.accent, letterSpacing: 4, marginBottom: 40 }}>
        저시력이란?
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
        {items.map((item, i) => {
          const op = interpolate(frame, [item.delay, item.delay + 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          const x = interpolate(frame, [item.delay, item.delay + 15], [-30, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          return (
            <div key={i} style={{ opacity: op, transform: `translateX(${x}px)`, display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ width: 8, height: 8, borderRadius: 4, background: i < 3 ? C.warm : C.accent, flexShrink: 0 }} />
              <span style={{ fontFamily: C.font, fontSize: 36, fontWeight: 600, color: C.white }}>{item.label}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 3: 미션 — 협회 소개 (34–52.7s) ──
const MissionScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame: frame - 5, fps, config: { damping: 16, stiffness: 90 } });
  const missions = [
    { icon: '🔍', text: '보조 기기 지원', delay: 30 },
    { icon: '📚', text: '접근성 교육', delay: 60 },
    { icon: '🤝', text: '사회 인식 개선', delay: 90 },
  ];

  return (
    <AbsoluteFill style={{ background: `linear-gradient(135deg, ${C.bg} 0%, ${C.surface} 100%)` }}>
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{
          textAlign: 'center',
          opacity: interpolate(titleSpring, [0, 1], [0, 1]),
          transform: `scale(${interpolate(titleSpring, [0, 1], [0.9, 1])})`,
        }}>
          <div style={{ fontFamily: C.font, fontSize: 24, color: C.accent, marginBottom: 16 }}>
            한국저시력인협회
          </div>
          <div style={{ fontFamily: C.font, fontSize: 56, fontWeight: 800, color: C.white, marginBottom: 50 }}>
            보이지 않는 곳에서<br /><span style={{ color: C.green }}>보이는 변화</span>를 만듭니다
          </div>
        </div>

        {/* 미션 카드 */}
        <div style={{ display: 'flex', gap: 32 }}>
          {missions.map((m, i) => {
            const op = interpolate(frame, [m.delay, m.delay + 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
            const y = interpolate(frame, [m.delay, m.delay + 15], [20, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
            return (
              <div key={i} style={{
                opacity: op, transform: `translateY(${y}px)`,
                background: C.surface, borderRadius: 20, padding: '32px 40px',
                border: '1px solid rgba(255,255,255,0.06)', textAlign: 'center', minWidth: 200,
              }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>{m.icon}</div>
                <div style={{ fontFamily: C.font, fontSize: 22, fontWeight: 700, color: C.white }}>{m.text}</div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ── Scene 4: 임팩트 — 숫자로 보는 성과 (52.7–70.6s) ──
const ImpactScene: React.FC = () => {
  const frame = useCurrentFrame();

  const stats = [
    { value: 1200, suffix: '명', label: '보조 기기 전달', color: C.accent, delay: 10 },
    { value: 87, suffix: '%', label: '일상 생활 개선', color: C.green, delay: 40 },
    { value: 15, suffix: '개', label: '지역 교육 센터', color: C.warm, delay: 70 },
  ];

  return (
    <AbsoluteFill style={{ background: C.bg, justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ fontFamily: C.font, fontSize: 20, color: C.dim, letterSpacing: 4, marginBottom: 60 }}>
        지난 한 해의 성과
      </div>
      <div style={{ display: 'flex', gap: 80 }}>
        {stats.map((s, i) => {
          const progress = interpolate(frame, [s.delay, s.delay + 40], [0, 1], {
            extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
          });
          const val = Math.round(s.value * progress);
          return (
            <div key={i} style={{ textAlign: 'center' }}>
              <div style={{ fontFamily: C.mono, fontSize: 72, fontWeight: 900, color: s.color }}>
                {val.toLocaleString()}<span style={{ fontSize: 36, color: C.dim }}>{s.suffix}</span>
              </div>
              <div style={{ fontFamily: C.font, fontSize: 20, color: C.dim, marginTop: 8 }}>{s.label}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 5: CTA — 후원 유도 (70.6–85s) ──
const CTAScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame: frame - 5, fps, config: { damping: 14, stiffness: 100 } });
  const pulse = Math.sin(frame * 0.1) * 0.03 + 1;

  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 60%, ${C.accent}10 0%, ${C.bg} 60%)` }}>
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{
          textAlign: 'center',
          opacity: interpolate(titleSpring, [0, 1], [0, 1]),
          transform: `scale(${interpolate(titleSpring, [0, 1], [0.8, 1])})`,
        }}>
          <div style={{ fontFamily: C.font, fontSize: 56, fontWeight: 800, color: C.white, marginBottom: 12 }}>
            당신의 관심이 곧 <span style={{ color: C.accent }}>변화</span>입니다
          </div>
          <div style={{ fontFamily: C.font, fontSize: 28, color: C.dim, marginBottom: 50 }}>
            월 1만원의 후원으로, 한 사람의 세상이 달라집니다
          </div>

          <div style={{
            display: 'inline-flex', padding: '22px 56px', borderRadius: 16,
            background: `linear-gradient(135deg, ${C.accent}, ${C.green})`,
            color: 'white', fontFamily: C.font, fontSize: 28, fontWeight: 800,
            transform: `scale(${pulse})`,
            boxShadow: `0 0 60px ${C.accent}44`,
          }}>
            후원하기 →
          </div>

          <div style={{
            marginTop: 40, fontFamily: C.font, fontSize: 20, color: C.dimmer,
            opacity: interpolate(frame, [40, 60], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
          }}>
            한국저시력인협회 · lowvision.or.kr
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ── MAIN ──
// 나레이션 실측: s1=13.4s, s2=18.6s, s3=17.7s, s4=16.9s, s5=14.2s
const T = {
  s1: { from: 0, dur: Math.ceil(14.4 * 30) },
  s2: { from: Math.ceil(14.4 * 30), dur: Math.ceil(19.6 * 30) },
  s3: { from: Math.ceil(34 * 30), dur: Math.ceil(18.7 * 30) },
  s4: { from: Math.ceil(52.7 * 30), dur: Math.ceil(17.9 * 30) },
  s5: { from: Math.ceil(70.6 * 30), dur: Math.ceil(15.2 * 30) },
};
export const LOWVISION_TOTAL = T.s5.from + T.s5.dur;

export const LowVisionPromo: React.FC = () => (
  <AbsoluteFill style={{ background: C.bg }}>
    <Audio src={staticFile('lowvision/bgm.wav')} volume={0.12} />
    <Sequence from={T.s1.from}><Audio src={staticFile('lowvision/narr_s1_hook.mp3')} volume={0.9} /></Sequence>
    <Sequence from={T.s2.from}><Audio src={staticFile('lowvision/narr_s2_problem.mp3')} volume={0.9} /></Sequence>
    <Sequence from={T.s3.from}><Audio src={staticFile('lowvision/narr_s3_mission.mp3')} volume={0.9} /></Sequence>
    <Sequence from={T.s4.from}><Audio src={staticFile('lowvision/narr_s4_impact.mp3')} volume={0.9} /></Sequence>
    <Sequence from={T.s5.from}><Audio src={staticFile('lowvision/narr_s5_cta.mp3')} volume={0.9} /></Sequence>

    <Sequence from={T.s1.from} durationInFrames={T.s1.dur}><HookScene /></Sequence>
    <Sequence from={T.s2.from} durationInFrames={T.s2.dur}><ProblemScene /></Sequence>
    <Sequence from={T.s3.from} durationInFrames={T.s3.dur}><MissionScene /></Sequence>
    <Sequence from={T.s4.from} durationInFrames={T.s4.dur}><ImpactScene /></Sequence>
    <Sequence from={T.s5.from} durationInFrames={T.s5.dur}><CTAScene /></Sequence>
  </AbsoluteFill>
);
