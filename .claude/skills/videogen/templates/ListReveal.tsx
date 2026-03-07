/**
 * ListReveal — 목록 순차 등장 레이아웃
 * 자막 4개 이상 or 목록형 텍스트 씬에 사용
 */
import React from 'react'
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion'
import { MONO_DARK, ANIM_CONFIG } from '../styles/monoDark'
import type { SceneProps } from './types'

export const ListReveal: React.FC<SceneProps> = ({
  subtitles, sceneStartFrame, sceneId, devMode,
}) => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const localFrame = frame - sceneStartFrame

  return (
    <AbsoluteFill style={{
      background: MONO_DARK.background,
      justifyContent: 'center', alignItems: 'flex-start',
      paddingLeft: MONO_DARK.padding.outer + 40,
      paddingRight: MONO_DARK.padding.outer,
    }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 32, justifyContent: 'center', height: '100%' }}>
        {subtitles.map((sub, i) => {
          const subStartMs = sub.startMs - subtitles[0].startMs
          const subStartFrame = Math.round(subStartMs / 1000 * fps)
          const subFrame = localFrame - subStartFrame
          const isVisible = subFrame >= 0

          const opacity = isVisible
            ? spring({ frame: subFrame, fps, config: { stiffness: 160, damping: 22 } })
            : 0
          const translateX = isVisible
            ? interpolate(subFrame, [0, ANIM_CONFIG.enterFrames], [-60, 0], { extrapolateRight: 'clamp' })
            : -60

          return (
            <div
              key={sub.index}
              style={{
                display: 'flex', alignItems: 'center', gap: 28,
                opacity,
                transform: `translateX(${translateX}px)`,
              }}
            >
              {/* 번호 배지 */}
              <div style={{
                width: 52, height: 52, borderRadius: '50%',
                border: `2px solid ${MONO_DARK.highlight}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontFamily: MONO_DARK.fontMono,
                fontSize: MONO_DARK.fontSize.caption,
                color: MONO_DARK.highlight,
                fontWeight: 700,
                flexShrink: 0,
              }}>
                {String(i + 1).padStart(2, '0')}
              </div>

              {/* 텍스트 */}
              <div style={{
                fontFamily: MONO_DARK.fontDisplay,
                fontSize: MONO_DARK.fontSize.body,
                color: MONO_DARK.textPrimary,
                fontWeight: i === subtitles.length - 1 ? 700 : 400,
                lineHeight: 1.4,
              }}>
                {sub.text}
              </div>
            </div>
          )
        })}
      </div>

      {devMode && <SceneOverlay sceneId={sceneId} layout="list-reveal" />}
    </AbsoluteFill>
  )
}

const SceneOverlay: React.FC<{ sceneId: number; layout: string }> = ({ sceneId, layout }) => (
  <AbsoluteFill style={{ pointerEvents: 'none' }}>
    <div style={{ position: 'absolute', top: 20, right: 20, background: 'rgba(220,38,38,0.9)', color: '#fff', padding: '6px 18px', fontFamily: 'monospace', fontSize: 22, fontWeight: 700, borderRadius: 4 }}>SCENE {sceneId}</div>
    <div style={{ position: 'absolute', top: 20, left: 20, background: 'rgba(37,99,235,0.9)', color: '#fff', padding: '6px 18px', fontFamily: 'monospace', fontSize: 18, borderRadius: 4 }}>{layout}</div>
  </AbsoluteFill>
)
