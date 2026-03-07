/**
 * TextCenter — 중앙 대형 텍스트 레이아웃
 * 훅, CTA, 핵심 메시지 씬에 사용
 */
import React from 'react'
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion'
import { MONO_DARK, ANIM_CONFIG } from '../styles/monoDark'
import type { SceneProps } from './types'

export const TextCenter: React.FC<SceneProps> = ({
  subtitles,
  sceneStartFrame,
  animation,
  sceneId,
  devMode,
}) => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const localFrame = frame - sceneStartFrame

  return (
    <AbsoluteFill style={{ background: MONO_DARK.background, justifyContent: 'center', alignItems: 'center' }}>
      {/* 배경 그라디언트 포인트 */}
      <div style={{
        position: 'absolute',
        width: 600, height: 600,
        borderRadius: '50%',
        background: `radial-gradient(circle, ${MONO_DARK.highlight}08 0%, transparent 70%)`,
        top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
      }} />

      {/* 자막 순차 렌더 */}
      <div style={{
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: MONO_DARK.padding.outer,
        textAlign: 'center',
        maxWidth: 1400,
      }}>
        {subtitles.map((sub, i) => {
          // 이 자막의 로컬 시작 프레임
          const subStartMs = sub.startMs - subtitles[0].startMs
          const subStartFrame = Math.round(subStartMs / 1000 * fps)
          const subFrame = localFrame - subStartFrame
          const isVisible = subFrame >= 0

          const opacity = isVisible
            ? spring({ frame: subFrame, fps, config: { stiffness: ANIM_CONFIG.stiffness, damping: ANIM_CONFIG.damping } })
            : 0

          const translateY = isVisible
            ? interpolate(subFrame, [0, ANIM_CONFIG.enterFrames], [40, 0], { extrapolateRight: 'clamp' })
            : 40

          // 마지막 자막이면 큰 폰트, 나머지는 작게
          const isLast = i === subtitles.length - 1
          const fontSize = isLast
            ? (animation === 'glitch' ? MONO_DARK.fontSize.hero : MONO_DARK.fontSize.title)
            : MONO_DARK.fontSize.heading

          return (
            <div
              key={sub.index}
              style={{
                opacity,
                transform: `translateY(${translateY}px)`,
                fontFamily: MONO_DARK.fontDisplay,
                fontSize,
                fontWeight: 700,
                color: isLast ? MONO_DARK.textAccent : MONO_DARK.textSecondary,
                lineHeight: 1.2,
                marginBottom: 16,
                letterSpacing: '-0.02em',
              }}
            >
              {/* Glitch 효과: hook 씬 */}
              {animation === 'glitch' && isLast ? (
                <GlitchText text={sub.text} frame={subFrame} />
              ) : sub.text}
            </div>
          )
        })}
      </div>

      {/* DEV 오버레이 */}
      {devMode && <SceneOverlay sceneId={sceneId} layout="text-center" />}
    </AbsoluteFill>
  )
}

// ── Glitch 텍스트 효과 ────────────────────────────────
const GlitchText: React.FC<{ text: string; frame: number }> = ({ text, frame }) => {
  const glitchActive = frame < 10
  const offset = glitchActive ? Math.sin(frame * 3.7) * 4 : 0
  return (
    <span style={{ position: 'relative', display: 'inline-block' }}>
      {glitchActive && (
        <>
          <span style={{ position: 'absolute', left: offset, top: 0, color: '#FF0044', opacity: 0.7, clipPath: 'inset(30% 0 50% 0)' }}>{text}</span>
          <span style={{ position: 'absolute', left: -offset, top: 0, color: '#00FFFF', opacity: 0.7, clipPath: 'inset(60% 0 10% 0)' }}>{text}</span>
        </>
      )}
      <span style={{ position: 'relative', color: glitchActive ? '#FFFFFF' : undefined }}>{text}</span>
    </span>
  )
}

// ── DEV 오버레이 ──────────────────────────────────────
const SceneOverlay: React.FC<{ sceneId: number; layout: string }> = ({ sceneId, layout }) => (
  <AbsoluteFill style={{ pointerEvents: 'none' }}>
    <div style={{ position: 'absolute', top: 20, right: 20, background: 'rgba(220,38,38,0.9)', color: '#fff', padding: '6px 18px', fontFamily: 'monospace', fontSize: 22, fontWeight: 700, borderRadius: 4 }}>
      SCENE {sceneId}
    </div>
    <div style={{ position: 'absolute', top: 20, left: 20, background: 'rgba(37,99,235,0.9)', color: '#fff', padding: '6px 18px', fontFamily: 'monospace', fontSize: 18, borderRadius: 4 }}>
      {layout}
    </div>
  </AbsoluteFill>
)
