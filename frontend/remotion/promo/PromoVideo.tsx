/**
 * OmniVibe Pro — Promotional Video (English)
 *
 * 60s YouTube promo: Hook → Problem → Solution → Features → CTA
 * Mono dark theme with #00FF88 neon accents
 */
import React from 'react';
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  Easing,
} from 'remotion';

// ── Theme Tokens ─────────────────────────────────
const T = {
  bg: '#0A0A0A',
  surface: '#141414',
  accent: '#00FF88',
  accentAlt: '#00CFFF',
  text: '#E5E5E5',
  textWeak: 'rgba(255,255,255,0.5)',
  font: '"Inter", "SF Pro Display", sans-serif',
  mono: '"JetBrains Mono", "Fira Code", monospace',
};

// ── Utility ─────────────────────────────────────
const FadeIn: React.FC<{ children: React.ReactNode; delay?: number }> = ({ children, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const o = interpolate(frame - delay, [0, 12], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const y = interpolate(frame - delay, [0, 12], [30, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return <div style={{ opacity: o, transform: `translateY(${y}px)` }}>{children}</div>;
};

const GlowText: React.FC<{ children: string; size?: number; color?: string }> = ({
  children, size = 72, color = T.accent,
}) => (
  <span style={{
    fontSize: size, fontWeight: 900, color,
    fontFamily: T.font,
    textShadow: `0 0 60px ${color}44, 0 0 120px ${color}22`,
  }}>
    {children}
  </span>
);

// ── Scene 1: Hook (0–5s) ─────────────────────────
const HookScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = spring({ frame, fps, config: { damping: 12, stiffness: 100 } });
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{
      background: `radial-gradient(ellipse at 40% 40%, ${T.accent}11 0%, ${T.bg} 70%)`,
      justifyContent: 'center', alignItems: 'center',
    }}>
      <div style={{ opacity, transform: `scale(${scale})`, textAlign: 'center' }}>
        <GlowText size={88}>What if one script</GlowText>
        <br />
        <FadeIn delay={20}>
          <GlowText size={88} color={T.accentAlt}>became a video?</GlowText>
        </FadeIn>
      </div>
      {/* Subtitle */}
      <div style={{
        position: 'absolute', bottom: 80,
        fontFamily: T.mono, fontSize: 20, color: T.textWeak,
        opacity: interpolate(frame, [40, 55], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
      }}>
        Automatically. In minutes.
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 2: Problem (5–12s) ─────────────────────
const ProblemScene: React.FC = () => {
  const frame = useCurrentFrame();
  const problems = [
    'Writing scripts takes hours',
    'Editing video is tedious',
    'Hiring voice actors is expensive',
    'Managing multi-platform is chaos',
  ];

  return (
    <AbsoluteFill style={{
      background: T.bg, justifyContent: 'center', alignItems: 'center', padding: 100,
    }}>
      <FadeIn>
        <div style={{ fontFamily: T.mono, fontSize: 16, color: T.accent, marginBottom: 30, letterSpacing: 4 }}>
          THE PROBLEM
        </div>
      </FadeIn>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        {problems.map((p, i) => {
          const delay = 15 + i * 18;
          const o = interpolate(frame, [delay, delay + 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          const x = interpolate(frame, [delay, delay + 10], [-40, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          return (
            <div key={i} style={{
              opacity: o, transform: `translateX(${x}px)`,
              display: 'flex', alignItems: 'center', gap: 16,
            }}>
              <span style={{ fontSize: 28, color: '#EA001E' }}>×</span>
              <span style={{ fontFamily: T.font, fontSize: 36, fontWeight: 600, color: T.text }}>{p}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 3: Solution Reveal (12–18s) ───────────
const SolutionScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - 10, fps, config: { damping: 14, stiffness: 110 } });
  const logoScale = interpolate(s, [0, 1], [0.5, 1]);
  const logoOpacity = interpolate(s, [0, 1], [0, 1]);

  return (
    <AbsoluteFill style={{
      background: `radial-gradient(circle at 50% 50%, ${T.accent}0A 0%, ${T.bg} 60%)`,
      justifyContent: 'center', alignItems: 'center',
    }}>
      {/* Logo text */}
      <div style={{ opacity: logoOpacity, transform: `scale(${logoScale})`, textAlign: 'center' }}>
        <div style={{ fontFamily: T.font, fontSize: 28, fontWeight: 600, color: T.textWeak, marginBottom: 20 }}>
          Introducing
        </div>
        <div style={{ fontFamily: T.font, fontSize: 96, fontWeight: 900, color: T.text }}>
          OmniVibe <span style={{ color: T.accent }}>Pro</span>
        </div>
        <FadeIn delay={30}>
          <div style={{ fontFamily: T.mono, fontSize: 22, color: T.textWeak, marginTop: 20 }}>
            AI-Powered Video Automation SaaS
          </div>
        </FadeIn>
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 4: Features (18–42s) ──────────────────
const FeaturesScene: React.FC = () => {
  const frame = useCurrentFrame();
  const features = [
    { icon: '🎤', title: 'Zero-Fault Audio', desc: 'ElevenLabs TTS + Whisper verification loop → 99% accuracy', time: 0 },
    { icon: '✂️', title: 'VREW Timeline Editor', desc: 'Word-level subtitle timing with drag & drop', time: 90 },
    { icon: '🎬', title: 'Remotion Rendering', desc: 'React-based video engine — YouTube, Instagram, TikTok', time: 180 },
    { icon: '🧠', title: 'AI Director Agent', desc: 'LangGraph orchestration — script → storyboard → render', time: 270 },
    { icon: '📊', title: 'GraphRAG Memory', desc: 'Neo4j-powered learning — every video improves the next', time: 360 },
    { icon: '💰', title: 'Smart Quota System', desc: '4-tier pricing with real-time usage tracking', time: 450 },
  ];

  return (
    <AbsoluteFill style={{ background: T.bg, padding: 80 }}>
      <FadeIn>
        <div style={{ fontFamily: T.mono, fontSize: 16, color: T.accent, letterSpacing: 4, marginBottom: 50 }}>
          FEATURES
        </div>
      </FadeIn>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 40 }}>
        {features.map((f, i) => {
          const delay = f.time / (30 / 5); // spread across scene
          const o = interpolate(frame, [delay, delay + 12], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          const y = interpolate(frame, [delay, delay + 12], [20, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          return (
            <div key={i} style={{
              opacity: o, transform: `translateY(${y}px)`,
              background: T.surface, borderRadius: 16,
              border: `1px solid rgba(255,255,255,0.06)`,
              padding: '28px 32px',
            }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>{f.icon}</div>
              <div style={{ fontFamily: T.font, fontSize: 26, fontWeight: 700, color: T.text, marginBottom: 8 }}>
                {f.title}
              </div>
              <div style={{ fontFamily: T.font, fontSize: 18, color: T.textWeak, lineHeight: 1.5 }}>
                {f.desc}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 5: Tech Stack (42–48s) ────────────────
const TechStackScene: React.FC = () => {
  const frame = useCurrentFrame();
  const stack = [
    { label: 'Frontend', items: 'Next.js 14 · React 18 · TypeScript · Tailwind' },
    { label: 'Video', items: 'Remotion 4 · WaveSurfer.js · FFmpeg' },
    { label: 'AI', items: 'GPT-4 · Claude · ElevenLabs · Whisper' },
    { label: 'Backend', items: 'FastAPI · Celery · Redis · Neo4j' },
    { label: 'Infra', items: 'Docker · Nginx · Vultr · Stripe' },
  ];

  return (
    <AbsoluteFill style={{
      background: T.bg, justifyContent: 'center', alignItems: 'center', padding: 100,
    }}>
      <FadeIn>
        <div style={{ fontFamily: T.mono, fontSize: 16, color: T.accent, letterSpacing: 4, marginBottom: 40, textAlign: 'center' }}>
          TECH STACK
        </div>
      </FadeIn>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, width: '100%', maxWidth: 900 }}>
        {stack.map((s, i) => {
          const delay = 10 + i * 12;
          const o = interpolate(frame, [delay, delay + 8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          return (
            <div key={i} style={{
              opacity: o, display: 'flex', alignItems: 'center', gap: 24,
              background: T.surface, borderRadius: 12, padding: '16px 28px',
              border: `1px solid rgba(255,255,255,0.06)`,
            }}>
              <span style={{
                fontFamily: T.mono, fontSize: 14, fontWeight: 700, color: T.accent,
                width: 100, textTransform: 'uppercase', letterSpacing: 2,
              }}>{s.label}</span>
              <span style={{ fontFamily: T.font, fontSize: 22, color: T.text }}>{s.items}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ── Scene 6: CTA (48–60s) ───────────────────────
const CTAScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pulse = Math.sin(frame / 15) * 0.03 + 1;
  const s = spring({ frame: frame - 5, fps, config: { damping: 16, stiffness: 120 } });

  return (
    <AbsoluteFill style={{
      background: `radial-gradient(ellipse at 50% 60%, ${T.accent}15 0%, ${T.bg} 60%)`,
      justifyContent: 'center', alignItems: 'center',
    }}>
      <div style={{ textAlign: 'center', transform: `scale(${interpolate(s, [0, 1], [0.8, 1])})` }}>
        <div style={{
          fontFamily: T.font, fontSize: 72, fontWeight: 900, color: T.text, marginBottom: 20,
          opacity: interpolate(s, [0, 1], [0, 1]),
        }}>
          Start Creating
        </div>
        <GlowText size={80}>Today</GlowText>

        <FadeIn delay={25}>
          <div style={{
            marginTop: 50, display: 'inline-flex', alignItems: 'center', gap: 12,
            background: T.accent, color: T.bg, borderRadius: 16,
            padding: '20px 48px', fontFamily: T.font, fontSize: 28, fontWeight: 800,
            transform: `scale(${pulse})`,
            boxShadow: `0 0 60px ${T.accent}44`,
          }}>
            Try OmniVibe Pro Free →
          </div>
        </FadeIn>

        <FadeIn delay={40}>
          <div style={{ fontFamily: T.mono, fontSize: 18, color: T.textWeak, marginTop: 30 }}>
            omnivibepro.com
          </div>
        </FadeIn>
      </div>
    </AbsoluteFill>
  );
};

// ── Main Composition ─────────────────────────────
export const PromoVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: T.bg }}>
      {/* Scene 1: Hook (0–5s = 0–150 frames) */}
      <Sequence from={0} durationInFrames={150}>
        <HookScene />
      </Sequence>

      {/* Scene 2: Problem (5–12s = 150–360) */}
      <Sequence from={150} durationInFrames={210}>
        <ProblemScene />
      </Sequence>

      {/* Scene 3: Solution (12–18s = 360–540) */}
      <Sequence from={360} durationInFrames={180}>
        <SolutionScene />
      </Sequence>

      {/* Scene 4: Features (18–42s = 540–1260) */}
      <Sequence from={540} durationInFrames={720}>
        <FeaturesScene />
      </Sequence>

      {/* Scene 5: Tech Stack (42–48s = 1260–1440) */}
      <Sequence from={1260} durationInFrames={180}>
        <TechStackScene />
      </Sequence>

      {/* Scene 6: CTA (48–60s = 1440–1800) */}
      <Sequence from={1440} durationInFrames={360}>
        <CTAScene />
      </Sequence>
    </AbsoluteFill>
  );
};
