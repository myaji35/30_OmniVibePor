/**
 * OmniVibe Pro — Remotion Feature Showcase (English)
 *
 * Demonstrates EVERY major Remotion capability:
 * 1. spring() — physics-based animations
 * 2. interpolate() — value mapping & easing
 * 3. useCurrentFrame() / useVideoConfig() — frame-aware rendering
 * 4. <Sequence> — timeline composition
 * 5. <Img> — static image import with Ken Burns effect
 * 6. <AbsoluteFill> — layer stacking
 * 7. SVG path animation — stroke-dashoffset
 * 8. Noise/particle simulation — procedural motion
 * 9. 3D CSS transforms — perspective rotation
 * 10. Dynamic text reveal — character-by-character
 * 11. Mask/clip-path wipes — cinematic transitions
 * 12. Data-driven bar chart animation
 */
import React from 'react';
import {
  AbsoluteFill,
  Sequence,
  Img,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  staticFile,
  Easing,
} from 'remotion';
import { PromoTexts, EN } from './i18n';

// ── Props ───────────────────────────────────────
export interface PromoVideoProps {
  texts?: PromoTexts;
}

// ── Theme ───────────────────────────────────────
const C = {
  bg:        '#0A0A0A',
  surface:   '#141414',
  accent:    '#00FF88',
  accentAlt: '#00CFFF',
  purple:    '#A855F7',
  amber:     '#FFB75D',
  red:       '#EA001E',
  text:      '#E5E5E5',
  dim:       'rgba(255,255,255,0.4)',
  font:      '"Inter", sans-serif',
  mono:      '"JetBrains Mono", monospace',
};

// ── 1. SCENE: Particle Hook (0–4s) — Noise + spring ──────────
const ParticleHookScene: React.FC<{ t: PromoTexts }> = ({ t }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // 50 particles with pseudo-random positions
  const particles = Array.from({ length: 50 }, (_, i) => {
    const seed = i * 137.508;
    const x = ((seed * 7.31) % width);
    const y = ((seed * 3.17) % height);
    const size = 2 + (i % 5) * 1.5;
    const speed = 0.3 + (i % 4) * 0.2;
    const delay = i * 0.6;

    const progress = interpolate(frame, [delay, delay + 40], [0, 1], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    });

    return { x, y, size, opacity: progress * 0.6, yOffset: Math.sin(frame * speed * 0.05) * 20 };
  });

  // Title spring
  const titleSpring = spring({ frame: frame - 15, fps, config: { damping: 12, stiffness: 80 } });
  const titleScale = interpolate(titleSpring, [0, 1], [0.3, 1]);
  const titleOpacity = interpolate(titleSpring, [0, 1], [0, 1]);

  // Subtitle
  const subOpacity = interpolate(frame, [50, 65], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {/* Particles */}
      {particles.map((p, i) => (
        <div key={i} style={{
          position: 'absolute',
          left: p.x, top: p.y + p.yOffset,
          width: p.size, height: p.size,
          borderRadius: '50%',
          background: i % 3 === 0 ? C.accent : i % 3 === 1 ? C.accentAlt : C.purple,
          opacity: p.opacity,
        }} />
      ))}

      {/* Radial glow */}
      <AbsoluteFill style={{
        background: `radial-gradient(circle at 50% 50%, ${C.accent}12 0%, transparent 60%)`,
      }} />

      {/* Title */}
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ opacity: titleOpacity, transform: `scale(${titleScale})`, textAlign: 'center' }}>
          <div style={{ fontFamily: C.font, fontSize: 96, fontWeight: 900, color: C.text,
            textShadow: `0 0 80px ${C.accent}33` }}>
            {t.hookTitle} <span style={{ color: C.accent }}>{t.hookHighlight}</span>
          </div>
        </div>
        <div style={{ opacity: subOpacity, marginTop: 24, fontFamily: C.mono, fontSize: 22, color: C.dim }}>
          {t.hookSub}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ── 2. SCENE: SVG Path Draw (4–9s) — stroke-dashoffset ──────
const SVGPathScene: React.FC<{ t: PromoTexts }> = ({ t }) => {
  const frame = useCurrentFrame();

  // Waveform path
  const pathLength = 800;
  const drawProgress = interpolate(frame, [0, 80], [pathLength, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Generate waveform points
  const points = Array.from({ length: 60 }, (_, i) => {
    const x = 160 + i * 27;
    const y = 540 + Math.sin(i * 0.5 + frame * 0.03) * 120 * Math.sin(i * 0.15);
    return `${i === 0 ? 'M' : 'L'}${x},${y}`;
  }).join(' ');

  const labelOpacity = interpolate(frame, [60, 75], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ background: C.bg, justifyContent: 'center', alignItems: 'center' }}>
      {/* Label */}
      <div style={{
        position: 'absolute', top: 80, left: 80,
        fontFamily: C.mono, fontSize: 14, color: C.accent, letterSpacing: 4,
      }}>
        {t.svgLabel}
      </div>

      {/* Animated waveform */}
      <svg width={1920} height={1080} style={{ position: 'absolute' }}>
        <path d={points} fill="none" stroke={C.accent} strokeWidth={3}
          strokeDasharray={pathLength} strokeDashoffset={drawProgress}
          strokeLinecap="round" />
        {/* Glow layer */}
        <path d={points} fill="none" stroke={C.accent} strokeWidth={8}
          strokeDasharray={pathLength} strokeDashoffset={drawProgress}
          strokeLinecap="round" opacity={0.15} />
      </svg>

      {/* "Audio Waveform" label */}
      <div style={{
        position: 'absolute', bottom: 120, opacity: labelOpacity, textAlign: 'center',
        fontFamily: C.font, fontSize: 36, fontWeight: 700, color: C.text,
      }}>
        {t.svgTitle}
      </div>
    </AbsoluteFill>
  );
};

// ── 3. SCENE: 3D CSS Transform (9–14s) — perspective ────────
const Transform3DScene: React.FC<{ t: PromoTexts }> = ({ t }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const rotateY = interpolate(frame, [0, 90], [-30, 15], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const rotateX = interpolate(frame, [0, 90], [20, -5], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const imgScale = spring({ frame: frame - 10, fps, config: { damping: 14, stiffness: 90 } });
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ background: C.bg, perspective: 1200 }}>
      <div style={{
        position: 'absolute', top: 80, left: 80,
        fontFamily: C.mono, fontSize: 14, color: C.purple, letterSpacing: 4,
      }}>
        {t.tdLabel}
      </div>

      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{
          opacity,
          transform: `rotateY(${rotateY}deg) rotateX(${rotateX}deg) scale(${interpolate(imgScale, [0, 1], [0.7, 1])})`,
          transformStyle: 'preserve-3d',
          borderRadius: 16, overflow: 'hidden',
          boxShadow: `0 40px 100px rgba(0,0,0,0.8), 0 0 60px ${C.purple}22`,
          border: `1px solid rgba(255,255,255,0.08)`,
        }}>
          <Img src={staticFile('promo/dashboard.png')} style={{ width: 1200, height: 'auto' }} />
        </div>
      </AbsoluteFill>

      {/* Floating badge */}
      <div style={{
        position: 'absolute', bottom: 100, right: 120,
        opacity: interpolate(frame, [60, 75], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
        background: C.purple, color: 'white', padding: '12px 24px', borderRadius: 12,
        fontFamily: C.font, fontSize: 20, fontWeight: 700,
        transform: `translateY(${interpolate(frame, [60, 75], [20, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })}px)`,
      }}>
        {t.tdBadge}
      </div>
    </AbsoluteFill>
  );
};

// ── 4. SCENE: Ken Burns Image (14–20s) — zoom + pan ─────────
const KenBurnsScene: React.FC<{ t: PromoTexts }> = ({ t }) => {
  const frame = useCurrentFrame();

  const scale = interpolate(frame, [0, 180], [1, 1.25], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.quad),
  });
  const translateX = interpolate(frame, [0, 180], [0, -60], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const translateY = interpolate(frame, [0, 180], [0, -30], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Overlay text
  const textOpacity = interpolate(frame, [30, 50], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <div style={{
        position: 'absolute', top: 80, left: 80, zIndex: 10,
        fontFamily: C.mono, fontSize: 14, color: C.amber, letterSpacing: 4,
      }}>
        {t.kbLabel}
      </div>

      {/* Image with Ken Burns */}
      <AbsoluteFill style={{ overflow: 'hidden' }}>
        <Img src={staticFile('promo/hero.png')} style={{
          width: '110%', height: '110%', objectFit: 'cover',
          transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`,
        }} />
      </AbsoluteFill>

      {/* Dark gradient overlay */}
      <AbsoluteFill style={{
        background: 'linear-gradient(0deg, rgba(10,10,10,0.95) 0%, rgba(10,10,10,0.3) 40%, rgba(10,10,10,0.1) 100%)',
      }} />

      {/* Text overlay */}
      <div style={{
        position: 'absolute', bottom: 100, left: 100, opacity: textOpacity,
      }}>
        <div style={{ fontFamily: C.font, fontSize: 56, fontWeight: 800, color: C.text, marginBottom: 12 }}>
          {t.kbTitle}
        </div>
        <div style={{ fontFamily: C.mono, fontSize: 20, color: C.dim }}>
          {t.kbSub}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── 5. SCENE: Clip-Path Wipe Transition (20–24s) ────────────
const ClipPathWipeScene: React.FC<{ t: PromoTexts }> = ({ t }) => {
  const frame = useCurrentFrame();

  const wipeProgress = interpolate(frame, [0, 60], [0, 100], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <div style={{
        position: 'absolute', top: 80, left: 80, zIndex: 20,
        fontFamily: C.mono, fontSize: 14, color: C.accentAlt, letterSpacing: 4,
      }}>
        {t.cpLabel}
      </div>

      {/* Before image */}
      <AbsoluteFill>
        <Img src={staticFile('promo/gallery.png')} style={{
          width: '100%', height: '100%', objectFit: 'cover', opacity: 0.6,
        }} />
      </AbsoluteFill>

      {/* After image — wiped in */}
      <AbsoluteFill style={{
        clipPath: `inset(0 ${100 - wipeProgress}% 0 0)`,
      }}>
        <Img src={staticFile('promo/miniplayer.png')} style={{
          width: '100%', height: '100%', objectFit: 'cover',
        }} />
      </AbsoluteFill>

      {/* Wipe line */}
      <div style={{
        position: 'absolute', top: 0, bottom: 0,
        left: `${wipeProgress}%`,
        width: 3, background: C.accentAlt,
        boxShadow: `0 0 20px ${C.accentAlt}, 0 0 60px ${C.accentAlt}44`,
        zIndex: 10,
      }} />

      {/* Labels */}
      <div style={{
        position: 'absolute', bottom: 60, left: 60,
        fontFamily: C.font, fontSize: 20, fontWeight: 600, color: C.dim,
        opacity: wipeProgress < 50 ? 1 : 0,
      }}>
        {t.cpBefore}
      </div>
      <div style={{
        position: 'absolute', bottom: 60, right: 60,
        fontFamily: C.font, fontSize: 20, fontWeight: 600, color: C.text,
        opacity: wipeProgress > 50 ? 1 : 0,
      }}>
        {t.cpAfter}
      </div>
    </AbsoluteFill>
  );
};

// ── 6. SCENE: Char-by-char Text Reveal (24–30s) ─────────────
const CharRevealScene: React.FC<{ t: PromoTexts }> = ({ t }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const lines = t.crLines;
  const colors = [C.accentAlt, C.text, C.accent, C.purple, C.accentAlt];

  let globalCharIdx = 0;

  return (
    <AbsoluteFill style={{ background: C.bg, justifyContent: 'center', padding: 160 }}>
      <div style={{
        position: 'absolute', top: 80, left: 80,
        fontFamily: C.mono, fontSize: 14, color: C.red, letterSpacing: 4,
      }}>
        {t.crLabel}
      </div>

      {/* Terminal window */}
      <div style={{
        background: '#1A1A2E', borderRadius: 16, padding: 40,
        border: '1px solid rgba(255,255,255,0.08)',
        boxShadow: '0 40px 80px rgba(0,0,0,0.6)',
      }}>
        {/* Terminal dots */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 30 }}>
          <div style={{ width: 12, height: 12, borderRadius: 6, background: '#FF5F57' }} />
          <div style={{ width: 12, height: 12, borderRadius: 6, background: '#FEBC2E' }} />
          <div style={{ width: 12, height: 12, borderRadius: 6, background: '#28C840' }} />
        </div>

        {lines.map((line, lineIdx) => {
          const lineStartChar = globalCharIdx;
          globalCharIdx += line.length;

          return (
            <div key={lineIdx} style={{
              fontFamily: C.mono, fontSize: 32, lineHeight: 1.8,
              display: 'flex', flexWrap: 'wrap',
            }}>
              {line.split('').map((char, charIdx) => {
                const absoluteIdx = lineStartChar + charIdx;
                const charDelay = absoluteIdx * 1.2;
                const charOpacity = interpolate(frame, [charDelay, charDelay + 3], [0, 1], {
                  extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
                });

                return (
                  <span key={charIdx} style={{
                    opacity: charOpacity, color: colors[lineIdx],
                    transform: `translateY(${interpolate(frame, [charDelay, charDelay + 3], [8, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })}px)`,
                  }}>
                    {char === ' ' ? '\u00A0' : char}
                  </span>
                );
              })}
            </div>
          );
        })}

        {/* Cursor blink */}
        <span style={{
          display: 'inline-block', width: 14, height: 32, background: C.accent,
          opacity: Math.sin(frame * 0.15) > 0 ? 1 : 0,
          marginLeft: 2, verticalAlign: 'bottom',
        }} />
      </div>
    </AbsoluteFill>
  );
};

// ── 7. SCENE: Data-Driven Bar Chart (30–36s) ────────────────
const BarChartScene: React.FC<{ t: PromoTexts }> = ({ t }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const barColors = [C.accent, C.accentAlt, C.purple, C.amber, C.red];
  const barValues = [95, 82, 70, 60, 45];
  const data = t.bcBars.map((label, i) => ({
    label,
    value: barValues[i] ?? 50,
    color: barColors[i] ?? C.accent,
  }));

  return (
    <AbsoluteFill style={{ background: C.bg, padding: 100 }}>
      <div style={{
        position: 'absolute', top: 80, left: 80,
        fontFamily: C.mono, fontSize: 14, color: C.accent, letterSpacing: 4,
      }}>
        {t.bcLabel}
      </div>

      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ width: 1200, display: 'flex', flexDirection: 'column', gap: 28 }}>
          {data.map((d, i) => {
            const barSpring = spring({ frame: frame - i * 10, fps, config: { damping: 16, stiffness: 100 } });
            const barWidth = interpolate(barSpring, [0, 1], [0, d.value]);
            const labelOpacity = interpolate(barSpring, [0, 0.3], [0, 1]);

            return (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
                <div style={{
                  width: 100, textAlign: 'right',
                  fontFamily: C.mono, fontSize: 18, color: C.dim, opacity: labelOpacity,
                }}>{d.label}</div>
                <div style={{
                  flex: 1, height: 40, background: 'rgba(255,255,255,0.04)',
                  borderRadius: 8, overflow: 'hidden',
                }}>
                  <div style={{
                    height: '100%', width: `${barWidth}%`,
                    background: `linear-gradient(90deg, ${d.color}, ${d.color}88)`,
                    borderRadius: 8,
                    boxShadow: `0 0 20px ${d.color}33`,
                  }} />
                </div>
                <div style={{
                  width: 50, fontFamily: C.mono, fontSize: 22, fontWeight: 700,
                  color: d.color, opacity: labelOpacity,
                }}>{Math.round(barWidth)}%</div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ── 8. SCENE: Multi-Layer Compositing + CTA (36–45s) ────────
const CTAScene: React.FC<{ t: PromoTexts }> = ({ t }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const ringRotate = frame * 0.8;
  const pulse = Math.sin(frame * 0.1) * 0.03 + 1;
  const titleSpring = spring({ frame: frame - 5, fps, config: { damping: 14, stiffness: 100 } });

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {/* Animated ring */}
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <svg width={600} height={600} style={{ position: 'absolute', opacity: 0.3 }}>
          <circle cx={300} cy={300} r={250} fill="none" stroke={C.accent} strokeWidth={1}
            strokeDasharray="20 10" transform={`rotate(${ringRotate}, 300, 300)`} />
          <circle cx={300} cy={300} r={200} fill="none" stroke={C.accentAlt} strokeWidth={1}
            strokeDasharray="15 15" transform={`rotate(${-ringRotate * 0.7}, 300, 300)`} />
          <circle cx={300} cy={300} r={150} fill="none" stroke={C.purple} strokeWidth={1}
            strokeDasharray="10 20" transform={`rotate(${ringRotate * 0.5}, 300, 300)`} />
        </svg>
      </AbsoluteFill>

      {/* Gradient overlay */}
      <AbsoluteFill style={{
        background: `radial-gradient(circle at 50% 50%, ${C.accent}0D 0%, transparent 50%)`,
      }} />

      {/* CTA content */}
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{
          textAlign: 'center',
          transform: `scale(${interpolate(titleSpring, [0, 1], [0.8, 1])})`,
          opacity: interpolate(titleSpring, [0, 1], [0, 1]),
        }}>
          <div style={{ fontFamily: C.font, fontSize: 72, fontWeight: 900, color: C.text, marginBottom: 16 }}>
            {t.ctaTitle} {t.ctaTitle && ' '}<span style={{ color: C.accent }}>{t.ctaHighlight}</span>
          </div>
          <div style={{ fontFamily: C.mono, fontSize: 24, color: C.dim, marginBottom: 50 }}>
            {t.ctaSub}
          </div>

          {/* CTA button */}
          <div style={{
            display: 'inline-flex', padding: '20px 56px', borderRadius: 16,
            background: C.accent, color: C.bg,
            fontFamily: C.font, fontSize: 28, fontWeight: 800,
            transform: `scale(${pulse})`,
            boxShadow: `0 0 60px ${C.accent}44, 0 20px 60px rgba(0,0,0,0.5)`,
          }}>
            {t.ctaButton}
          </div>

          <div style={{
            marginTop: 30, fontFamily: C.mono, fontSize: 18, color: C.dim,
            opacity: interpolate(frame, [40, 55], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
          }}>
            {t.ctaUrl}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ── MAIN COMPOSITION ─────────────────────────────
export const PromoVideo: React.FC<PromoVideoProps> = ({ texts }) => {
  const t = texts ?? EN;

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <Sequence from={0} durationInFrames={120}>
        <ParticleHookScene t={t} />
      </Sequence>
      <Sequence from={120} durationInFrames={150}>
        <SVGPathScene t={t} />
      </Sequence>
      <Sequence from={270} durationInFrames={150}>
        <Transform3DScene t={t} />
      </Sequence>
      <Sequence from={420} durationInFrames={180}>
        <KenBurnsScene t={t} />
      </Sequence>
      <Sequence from={600} durationInFrames={120}>
        <ClipPathWipeScene t={t} />
      </Sequence>
      <Sequence from={720} durationInFrames={180}>
        <CharRevealScene t={t} />
      </Sequence>
      <Sequence from={900} durationInFrames={180}>
        <BarChartScene t={t} />
      </Sequence>
      <Sequence from={1080} durationInFrames={270}>
        <CTAScene t={t} />
      </Sequence>
    </AbsoluteFill>
  );
};
