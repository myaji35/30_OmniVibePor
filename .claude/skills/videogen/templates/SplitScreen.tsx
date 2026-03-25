/**
 * SplitScreen — 2분할 비교/대조 레이아웃
 * Before/After, A vs B, 비교 씬에 사용
 */
import React from 'react'
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion'
import { MONO_DARK, ANIM_CONFIG } from '../styles/monoDark'
import type { SceneProps } from './types'

export const SplitScreen: React.FC<SceneProps> = ({
  subtitles,
  sceneStartFrame,
  animation,
  sceneId,
  devMode,
}) => {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const localFrame = frame - sceneStartFrame

  // 자막을 좌/우 두 그룹으로 나눔
  const mid = Math.ceil(subtitles.length / 2)
  const leftSubs  = subtitles.slice(0, mid)
  const rightSubs = subtitles.slice(mid)

  // 분할선 진입 애니메이션
  const dividerProgress = spring({
    frame: localFrame,
    fps,
    config: { stiffness: 80, damping: 20 },
  })
  const dividerHeight = interpolate(dividerProgress, [0, 1], [0, height])

  const renderSide = (subs: typeof subtitles, side: 'left' | 'right', label: string) => {
    const isLeft = side === 'left'
    const bgColor = isLeft ? MONO_DARK.surface : MONO_DARK.surfaceAlt
    const accentColor = isLeft ? MONO_DARK.highlight : MONO_DARK.highlightAlt

    return (
      <div style={{
        width: '50%',
        height: '100%',
        background: bgColor,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: MONO_DARK.padding.inner,
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* 배경 그라디언트 포인트 */}
        <div style={{
          position: 'absolute',
          width: 400, height: 400,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${accentColor}0A 0%, transparent 70%)`,
          top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none',
        }} />

        {/* 라벨 (Before / After 등) */}
        <div style={{
          position: 'absolute',
          top: MONO_DARK.padding.outer,
          fontFamily: MONO_DARK.fontMono,
          fontSize: MONO_DARK.fontSize.small,
          color: accentColor,
          letterSpacing: 4,
          textTransform: 'uppercase',
          fontWeight: 700,
          opacity: interpolate(localFrame, [0, 15], [0, 1], { extrapolateRight: 'clamp' }),
        }}>
          {label}
        </div>

        {/* 자막 순차 렌더 */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
          alignItems: 'center',
          textAlign: 'center',
          maxWidth: 700,
          zIndex: 1,
        }}>
          {subs.map((sub, i) => {
            const subStartMs = sub.startMs - subtitles[0].startMs
            const subStartFrame = Math.round(subStartMs / 1000 * fps)
            const subFrame = localFrame - subStartFrame
            const isVisible = subFrame >= 0

            const opacity = isVisible
              ? spring({ frame: subFrame, fps, config: { stiffness: ANIM_CONFIG.stiffness, damping: ANIM_CONFIG.damping } })
              : 0

            const slideDir = isLeft ? -60 : 60
            const translateX = isVisible
              ? interpolate(subFrame, [0, ANIM_CONFIG.enterFrames], [slideDir, 0], { extrapolateRight: 'clamp' })
              : slideDir

            const isFirst = i === 0
            const fontSize = isFirst ? MONO_DARK.fontSize.heading : MONO_DARK.fontSize.body

            return (
              <div key={i} style={{
                opacity,
                transform: `translateX(${translateX}px)`,
                fontFamily: MONO_DARK.fontDisplay,
                fontSize,
                fontWeight: isFirst ? 800 : 400,
                color: isFirst ? MONO_DARK.textAccent : MONO_DARK.textPrimary,
                lineHeight: 1.3,
              }}>
                {sub.text}
              </div>
            )
          })}
        </div>

        {/* 하단 강조선 */}
        <div style={{
          position: 'absolute',
          bottom: 0,
          left: '10%',
          width: `${interpolate(localFrame, [10, 40], [0, 80], { extrapolateRight: 'clamp' })}%`,
          height: 3,
          background: accentColor,
          opacity: 0.7,
        }} />
      </div>
    )
  }

  return (
    <AbsoluteFill style={{ background: MONO_DARK.background, flexDirection: 'row' }}>
      {/* 왼쪽 패널 */}
      {renderSide(leftSubs, 'left', 'BEFORE')}

      {/* 중앙 분할선 */}
      <div style={{
        width: 2,
        height: dividerHeight,
        background: `linear-gradient(to bottom, transparent, ${MONO_DARK.highlight}, transparent)`,
        alignSelf: 'center',
        flexShrink: 0,
      }} />

      {/* 오른쪽 패널 */}
      {renderSide(rightSubs, 'right', 'AFTER')}

      {/* DEV 오버레이 */}
      {devMode && (
        <div style={{
          position: 'absolute', top: 20, right: 20,
          background: 'rgba(255,165,0,0.85)', color: '#000',
          fontFamily: MONO_DARK.fontMono, fontSize: 22,
          padding: '6px 16px', borderRadius: 6, fontWeight: 700, zIndex: 9999,
        }}>
          SCENE {sceneId} · split-screen
        </div>
      )}
    </AbsoluteFill>
  )
}
