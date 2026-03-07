/**
 * FullVisual — 전체 배경 + 자막 오버레이 레이아웃
 * 경로 A에서 AI/스톡 영상 소스가 있을 때 사용
 * 경로 B에서는 다크 그라디언트 배경 사용
 */
import React from 'react'
import { AbsoluteFill, useCurrentFrame, useVideoConfig, Video, spring, interpolate } from 'remotion'
import { MONO_DARK, ANIM_CONFIG } from '../styles/monoDark'
import type { SceneProps } from './types'

export const FullVisual: React.FC<SceneProps> = ({
  subtitles, sceneStartFrame, videoSrc, sceneId, devMode,
}) => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const localFrame = frame - sceneStartFrame

  return (
    <AbsoluteFill>
      {/* 배경: 영상 소스 있으면 영상, 없으면 그라디언트 */}
      {videoSrc ? (
        <Video src={videoSrc} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      ) : (
        <div style={{
          width: '100%', height: '100%',
          background: `linear-gradient(135deg, #0A0A0A 0%, #141428 50%, #0A0A0A 100%)`,
        }} />
      )}

      {/* 하단 그라디언트 (자막 가독성) */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: 300,
        background: 'linear-gradient(transparent, rgba(0,0,0,0.85))',
      }} />

      {/* 자막 (하단 중앙) */}
      <div style={{
        position: 'absolute', bottom: 80, left: 0, right: 0,
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        gap: 16, padding: `0 ${MONO_DARK.padding.outer}px`,
      }}>
        {subtitles.map((sub) => {
          const subStartMs = sub.startMs - subtitles[0].startMs
          const subStartFrame = Math.round(subStartMs / 1000 * fps)
          const subFrame = localFrame - subStartFrame
          const isVisible = subFrame >= 0

          const opacity = isVisible
            ? spring({ frame: subFrame, fps, config: { stiffness: ANIM_CONFIG.stiffness, damping: ANIM_CONFIG.damping } })
            : 0
          const translateY = isVisible
            ? interpolate(subFrame, [0, ANIM_CONFIG.enterFrames], [20, 0], { extrapolateRight: 'clamp' })
            : 20

          return (
            <div key={sub.index} style={{
              opacity,
              transform: `translateY(${translateY}px)`,
              fontFamily: MONO_DARK.fontDisplay,
              fontSize: MONO_DARK.fontSize.body,
              fontWeight: 600,
              color: MONO_DARK.textAccent,
              textAlign: 'center',
              textShadow: '0 2px 8px rgba(0,0,0,0.8)',
              lineHeight: 1.4,
            }}>
              {sub.text}
            </div>
          )
        })}
      </div>

      {devMode && <SceneOverlay sceneId={sceneId} layout="full-visual" />}
    </AbsoluteFill>
  )
}

const SceneOverlay: React.FC<{ sceneId: number; layout: string }> = ({ sceneId, layout }) => (
  <AbsoluteFill style={{ pointerEvents: 'none' }}>
    <div style={{ position: 'absolute', top: 20, right: 20, background: 'rgba(220,38,38,0.9)', color: '#fff', padding: '6px 18px', fontFamily: 'monospace', fontSize: 22, fontWeight: 700, borderRadius: 4 }}>SCENE {sceneId}</div>
    <div style={{ position: 'absolute', top: 20, left: 20, background: 'rgba(37,99,235,0.9)', color: '#fff', padding: '6px 18px', fontFamily: 'monospace', fontSize: 18, borderRadius: 4 }}>{layout}</div>
  </AbsoluteFill>
)
