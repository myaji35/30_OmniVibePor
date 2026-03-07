/**
 * Infographic — 카운터/수치 중앙집중 레이아웃
 * 통계, 퍼센트, 수치 강조 씬에 사용
 */
import React from 'react'
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion'
import { MONO_DARK, ANIM_CONFIG } from '../styles/monoDark'
import type { SceneProps } from './types'

// 텍스트에서 숫자 + 단위 추출
function extractStat(text: string): { number: string; unit: string; label: string } | null {
  const m = text.match(/([+-]?\d[\d,.]*)([%억원만천배개명]+)?(.*)/)
  if (!m) return null
  return {
    number: m[1],
    unit:   m[2] || '',
    label:  m[3]?.trim() || text,
  }
}

export const Infographic: React.FC<SceneProps> = ({
  subtitles, sceneStartFrame, sceneId, devMode,
}) => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const localFrame = frame - sceneStartFrame

  // 전체 등장 spring
  const appear = spring({ frame: localFrame, fps, config: { stiffness: 120, damping: 18 } })

  // 메인 자막 (수치가 있는 자막) 찾기
  const mainSub = subtitles.find(s => /\d+/.test(s.text)) || subtitles[subtitles.length - 1]
  const restSubs = subtitles.filter(s => s !== mainSub)
  const stat = mainSub ? extractStat(mainSub.text) : null

  // 카운터 애니메이션: 0 → 실제값
  const targetNum = stat ? parseFloat(stat.number.replace(/,/g, '')) : 0
  const countProgress = interpolate(localFrame, [0, fps * 1.2], [0, 1], { extrapolateRight: 'clamp' })
  const currentNum = Math.round(targetNum * countProgress)

  return (
    <AbsoluteFill style={{ background: MONO_DARK.background, justifyContent: 'center', alignItems: 'center' }}>
      {/* 중앙 포인트 글로우 */}
      <div style={{
        position: 'absolute',
        width: 800, height: 800, borderRadius: '50%',
        background: `radial-gradient(circle, ${MONO_DARK.highlight}12 0%, transparent 65%)`,
        top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
      }} />

      {/* 중앙 집중 레이아웃 */}
      <div style={{
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        opacity: appear,
        transform: `scale(${interpolate(appear, [0, 1], [0.85, 1])})`,
      }}>
        {/* 보조 자막 (상단) */}
        {restSubs.slice(0, 1).map(sub => (
          <div key={sub.index} style={{
            fontFamily: MONO_DARK.fontMono,
            fontSize: MONO_DARK.fontSize.caption,
            color: MONO_DARK.textSecondary,
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            marginBottom: 32,
          }}>
            {sub.text}
          </div>
        ))}

        {/* 핵심 수치 */}
        {stat && (
          <div style={{
            display: 'flex', alignItems: 'flex-end', gap: 8,
            marginBottom: 24,
          }}>
            <span style={{
              fontFamily: MONO_DARK.fontMono,
              fontSize: MONO_DARK.fontSize.display,
              fontWeight: 700,
              color: MONO_DARK.highlight,
              lineHeight: 1,
              letterSpacing: '-0.04em',
            }}>
              {currentNum.toLocaleString()}
            </span>
            <span style={{
              fontFamily: MONO_DARK.fontMono,
              fontSize: MONO_DARK.fontSize.title,
              fontWeight: 700,
              color: MONO_DARK.highlight,
              lineHeight: 1.2,
              marginBottom: 12,
            }}>
              {stat.unit}
            </span>
          </div>
        )}

        {/* 구분선 */}
        <div style={{
          width: interpolate(localFrame, [10, 35], [0, 400], { extrapolateRight: 'clamp' }),
          height: 2,
          background: `linear-gradient(90deg, transparent, ${MONO_DARK.highlight}, transparent)`,
          marginBottom: 28,
        }} />

        {/* 레이블 */}
        {stat && stat.label && (
          <div style={{
            fontFamily: MONO_DARK.fontDisplay,
            fontSize: MONO_DARK.fontSize.heading,
            color: MONO_DARK.textPrimary,
            textAlign: 'center',
          }}>
            {stat.label}
          </div>
        )}
      </div>

      {devMode && <SceneOverlay sceneId={sceneId} layout="infographic" />}
    </AbsoluteFill>
  )
}

const SceneOverlay: React.FC<{ sceneId: number; layout: string }> = ({ sceneId, layout }) => (
  <AbsoluteFill style={{ pointerEvents: 'none' }}>
    <div style={{ position: 'absolute', top: 20, right: 20, background: 'rgba(220,38,38,0.9)', color: '#fff', padding: '6px 18px', fontFamily: 'monospace', fontSize: 22, fontWeight: 700, borderRadius: 4 }}>SCENE {sceneId}</div>
    <div style={{ position: 'absolute', top: 20, left: 20, background: 'rgba(37,99,235,0.9)', color: '#fff', padding: '6px 18px', fontFamily: 'monospace', fontSize: 18, borderRadius: 4 }}>{layout}</div>
  </AbsoluteFill>
)
