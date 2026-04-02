/**
 * 보봇(BoBot) — "보봇은 왜 안전한가?" 한글 홍보 영상 (60초)
 *
 * 5가지 안전 장치를 시각적으로 설명
 * 남성 더빙 (InJoon) + 신뢰감 있는 인디고 컬러
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

const C = {
  bg:      '#0F172A',
  surface: '#1E293B',
  accent:  '#6366F1',
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

// ── Shield Icon (SVG) ────────────────────────────
const ShieldIcon: React.FC<{ size?: number; color?: string }> = ({ size = 120, color = C.accent }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <polyline points="9 12 11 14 15 10" stroke={C.green} strokeWidth={2} />
  </svg>
);

// ── Scene 1: 타이틀 — "보봇은 왜 안전한가?" (0–8s) ──
const TitleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const shieldScale = spring({ frame: frame - 10, fps, config: { damping: 12, stiffness: 80 } });
  const titleOp = interpolate(frame, [30, 50], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const subOp = interpolate(frame, [60, 80], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 40%, ${C.surface} 0%, ${C.bg} 70%)` }}>
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        {/* Shield */}
        <div style={{
          transform: `scale(${interpolate(shieldScale, [0, 1], [0.3, 1])})`,
          opacity: interpolate(shieldScale, [0, 1], [0, 1]),
          marginBottom: 32,
        }}>
          <ShieldIcon size={140} />
        </div>

        <div style={{ opacity: titleOp, textAlign: 'center' }}>
          <div style={{ fontFamily: C.font, fontSize: 80, fontWeight: 900, color: C.white }}>
            보봇은 왜 <span style={{ color: C.green }}>안전</span>한가?
          </div>
        </div>

        <div style={{ opacity: subOp, marginTop: 20, textAlign: 'center' }}>
          <div style={{ fontFamily: C.font, fontSize: 28, color: C.dim }}>
            AI 보험 상담, 정말 믿어도 될까요?
          </div>
          <div style={{ fontFamily: C.font, fontSize: 24, color: C.dimmer, marginTop: 8 }}>
            보봇의 5가지 안전 장치를 소개합니다
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ── Safety Point Card Component ──────────────────
const SafetyPointScene: React.FC<{
  number: number;
  title: string;
  points: string[];
  color: string;
  icon: string;
}> = ({ number, title, points, color, icon }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const numSpring = spring({ frame: frame - 5, fps, config: { damping: 14, stiffness: 100 } });
  const cardSpring = spring({ frame: frame - 15, fps, config: { damping: 16, stiffness: 90 } });

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', padding: 120 }}>
        <div style={{ display: 'flex', gap: 60, alignItems: 'flex-start', maxWidth: 1400 }}>
          {/* 번호 + 아이콘 */}
          <div style={{
            textAlign: 'center', minWidth: 200,
            opacity: interpolate(numSpring, [0, 1], [0, 1]),
            transform: `scale(${interpolate(numSpring, [0, 1], [0.5, 1])})`,
          }}>
            <div style={{
              fontFamily: C.mono, fontSize: 120, fontWeight: 900, color,
              lineHeight: 1, textShadow: `0 0 60px ${color}33`,
            }}>
              {number}
            </div>
            <div style={{ fontSize: 60, marginTop: 8 }}>{icon}</div>
          </div>

          {/* 카드 */}
          <div style={{
            flex: 1,
            opacity: interpolate(cardSpring, [0, 1], [0, 1]),
            transform: `translateX(${interpolate(cardSpring, [0, 1], [60, 0])}px)`,
            background: C.surface, borderRadius: 20, padding: 48,
            border: `1px solid ${color}33`,
            boxShadow: `0 0 40px ${color}11`,
          }}>
            <div style={{
              fontFamily: C.font, fontSize: 38, fontWeight: 800, color: C.white, marginBottom: 24,
            }}>
              {title}
            </div>
            {points.map((p, i) => {
              const pointDelay = 30 + i * 15;
              const pointOp = interpolate(frame, [pointDelay, pointDelay + 10], [0, 1], {
                extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
              });
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 16,
                  opacity: pointOp,
                  transform: `translateY(${interpolate(frame, [pointDelay, pointDelay + 10], [10, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })}px)`,
                }}>
                  <span style={{ color, fontSize: 18, marginTop: 4 }}>✓</span>
                  <span style={{ fontFamily: C.font, fontSize: 22, color: C.dim, lineHeight: 1.5 }}>{p}</span>
                </div>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ── Scene 7: CTA (52–60s) ────────────────────────
const CTAScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame: frame - 5, fps, config: { damping: 14, stiffness: 100 } });
  const pulse = Math.sin(frame * 0.1) * 0.03 + 1;

  // 5개 방패 아이콘 순차 등장
  const shields = Array.from({ length: 5 }, (_, i) => {
    const delay = 20 + i * 8;
    const op = interpolate(frame, [delay, delay + 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const y = interpolate(frame, [delay, delay + 10], [20, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    return { op, y };
  });

  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 60%, ${C.green}0A 0%, ${C.bg} 60%)` }}>
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{
          textAlign: 'center',
          opacity: interpolate(titleSpring, [0, 1], [0, 1]),
          transform: `scale(${interpolate(titleSpring, [0, 1], [0.8, 1])})`,
        }}>
          {/* 방패 5개 */}
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginBottom: 40 }}>
            {shields.map((s, i) => (
              <div key={i} style={{ opacity: s.op, transform: `translateY(${s.y}px)` }}>
                <ShieldIcon size={48} color={[C.green, C.blue, C.accent, C.amber, C.green][i]} />
              </div>
            ))}
          </div>

          <div style={{ fontFamily: C.font, fontSize: 64, fontWeight: 900, color: C.white, marginBottom: 12 }}>
            보봇, <span style={{ color: C.green }}>안전한</span> AI 보험 상담
          </div>
          <div style={{ fontFamily: C.font, fontSize: 28, color: C.dim, marginBottom: 50 }}>
            금소법 준수 · 법적 증빙 · GA 감독 · 할루시네이션 방지 · 샌드박스 설계
          </div>

          <div style={{
            display: 'inline-flex', padding: '22px 56px', borderRadius: 16,
            background: `linear-gradient(135deg, ${C.green}, ${C.blue})`,
            color: 'white', fontFamily: C.font, fontSize: 28, fontWeight: 800,
            transform: `scale(${pulse})`,
            boxShadow: `0 0 60px ${C.green}44`,
          }}>
            InsureGraph Pro 시작하기 →
          </div>

          <div style={{
            marginTop: 30, fontFamily: C.mono, fontSize: 18, color: C.dimmer,
            opacity: interpolate(frame, [50, 70], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
          }}>
            insuregraph.com
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ── MAIN COMPOSITION ─────────────────────────────
// 나레이션 실측: bobot1=12.5s, bobot2=21.6s, bobot3=18.4s, bobot4=14.9s, bobot5=13.8s, bobot6=17.4s
// 씬 duration = 나레이션 + 1초 버퍼, fps=30
// 누적: 0, 13.5, 36.1, 55.5, 71.4, 86.2, 104.6 → 총 ~105초
const B = { // frames (duration in seconds * 30fps, rounded)
  s1: { from: 0,    dur: Math.ceil(13.5 * 30) },  // 0–13.5s  (narr 12.5s)
  s2: { from: Math.ceil(13.5 * 30), dur: Math.ceil(22.6 * 30) },  // 13.5–36.1s (narr 21.6s)
  s3: { from: Math.ceil(36.1 * 30), dur: Math.ceil(19.4 * 30) },  // 36.1–55.5s (narr 18.4s)
  s4: { from: Math.ceil(55.5 * 30), dur: Math.ceil(15.9 * 30) },  // 55.5–71.4s (narr 14.9s)
  s5: { from: Math.ceil(71.4 * 30), dur: Math.ceil(14.8 * 30) },  // 71.4–86.2s (narr 13.8s)
  s6: { from: Math.ceil(86.2 * 30), dur: Math.ceil(18.4 * 30) },  // 86.2–104.6s (narr 17.4s)
  cta: { from: Math.ceil(104.6 * 30), dur: Math.ceil(8 * 30) },   // 104.6–112.6s (아웃로)
};
const TOTAL_FRAMES = B.cta.from + B.cta.dur;

export const BobotSafetyPromo: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {/* BGM */}
      <Audio src={staticFile('insuregraph/bgm.wav')} volume={0.10} />

      {/* 씬별 나레이션 (개별 MP3 → 정확한 싱크) */}
      <Sequence from={B.s1.from}><Audio src={staticFile('insuregraph/narr_bobot1.mp3')} volume={0.9} /></Sequence>
      <Sequence from={B.s2.from}><Audio src={staticFile('insuregraph/narr_bobot2.mp3')} volume={0.9} /></Sequence>
      <Sequence from={B.s3.from}><Audio src={staticFile('insuregraph/narr_bobot3.mp3')} volume={0.9} /></Sequence>
      <Sequence from={B.s4.from}><Audio src={staticFile('insuregraph/narr_bobot4.mp3')} volume={0.9} /></Sequence>
      <Sequence from={B.s5.from}><Audio src={staticFile('insuregraph/narr_bobot5.mp3')} volume={0.9} /></Sequence>
      <Sequence from={B.s6.from}><Audio src={staticFile('insuregraph/narr_bobot6.mp3')} volume={0.9} /></Sequence>

      {/* 씬별 비주얼 */}
      <Sequence from={B.s1.from} durationInFrames={B.s1.dur}>
        <TitleScene />
      </Sequence>

      <Sequence from={B.s2.from} durationInFrames={B.s2.dur}>
        <SafetyPointScene number={1} title="금소법 6대 원칙 자동 준수" color={C.green} icon="⚖️"
          points={['적합성 원칙 · 적정성 원칙 실시간 검증', '설명 의무 · 불공정 영업 금지 자동 체크', '부당 권유 금지 · 허위 과장 금지 모니터링']} />
      </Sequence>

      <Sequence from={B.s3.from} durationInFrames={B.s3.dur}>
        <SafetyPointScene number={2} title="모든 AI 판단에 법적 증빙" color={C.blue} icon="📋"
          points={['ComplianceRecord에 상담 근거 자동 기록', '추천 이유 · 고객 동의 내역 추적', '금융감독원 검사 즉시 대응 가능']} />
      </Sequence>

      <Sequence from={B.s4.from} durationInFrames={B.s4.dur}>
        <SafetyPointScene number={3} title="GA법인 관리·감독 하에 운영" color={C.accent} icon="🏢"
          points={['독단적 계약 체결 불가', '모든 최종 결정은 담당 설계사 확인', 'AI는 보조 도구, 사람이 최종 판단']} />
      </Sequence>

      <Sequence from={B.s5.from} durationInFrames={B.s5.dur}>
        <SafetyPointScene number={4} title="할루시네이션 방지 — GraphRAG" color={C.amber} icon="🧠"
          points={['38,000개 약관 원문을 인용하며 답변', '출처를 명시하여 검증 가능', 'GraphRAG 기반 — 추론이 아닌 검색']} />
      </Sequence>

      <Sequence from={B.s6.from} durationInFrames={B.s6.dur}>
        <SafetyPointScene number={5} title="혁신금융서비스 샌드박스 기준" color={C.green} icon="🏛️"
          points={['금융위원회 승인 절차를 염두에 둔 설계', 'MyData API 헬스케어 연동 아키텍처', '컴플라이언스 퍼스트 접근']} />
      </Sequence>

      <Sequence from={B.cta.from} durationInFrames={B.cta.dur}>
        <CTAScene />
      </Sequence>
    </AbsoluteFill>
  );
};

export const BOBOT_TOTAL_FRAMES = TOTAL_FRAMES;
