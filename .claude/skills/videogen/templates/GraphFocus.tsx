/**
 * GraphFocus — 그래프/차트 중앙 집중 레이아웃
 * 데이터 시각화, 추이, 수치 비교 씬에 사용
 * drawLine 애니메이션으로 그래프 선이 점진적으로 그려짐
 */
import React from 'react'
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion'
import { MONO_DARK, ANIM_CONFIG } from '../styles/monoDark'
import type { SceneProps } from './types'

// 씬 텍스트에서 숫자 추출 헬퍼
function extractNumbers(text: string): number[] {
  return (text.match(/\d+\.?\d*/g) || []).map(Number)
}

// 그래프 포인트 생성 (텍스트 기반 더미 데이터)
function buildGraphPoints(subtitles: { text: string }[], w: number, h: number) {
  const chartH = h * 0.45
  const chartW = w * 0.70
  const paddingX = (w - chartW) / 2
  const paddingY = h * 0.28

  const allNums = subtitles.flatMap(s => extractNumbers(s.text))
  const values = allNums.length >= 3
    ? allNums.slice(0, 6)
    : [20, 45, 30, 70, 55, 90]   // 기본 상승 패턴

  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1

  return values.map((v, i) => ({
    x: paddingX + (i / (values.length - 1)) * chartW,
    y: paddingY + chartH - ((v - min) / range) * chartH,
    value: v,
  }))
}

export const GraphFocus: React.FC<SceneProps> = ({
  subtitles,
  sceneStartFrame,
  animation,
  sceneId,
  devMode,
}) => {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const localFrame = frame - sceneStartFrame

  const points = buildGraphPoints(subtitles, width, height)

  // drawLine 진행률 (0 → 1)
  const drawProgress = interpolate(
    localFrame,
    [0, ANIM_CONFIG.enterFrames * 2],
    [0, 1],
    { extrapolateRight: 'clamp' }
  )

  // 그려진 포인트 수
  const visibleSegments = Math.floor(drawProgress * (points.length - 1))
  const segmentProgress = (drawProgress * (points.length - 1)) % 1

  // SVG polyline 생성
  const buildPolyline = () => {
    const visible = points.slice(0, visibleSegments + 2)
    if (visible.length < 2) return ''
    // 마지막 포인트를 진행률에 따라 보간
    const last = visible[visible.length - 1]
    const prev = visible[visible.length - 2]
    const interpX = prev.x + (last.x - prev.x) * (visibleSegments < points.length - 1 ? segmentProgress : 1)
    const interpY = prev.y + (last.y - prev.y) * (visibleSegments < points.length - 1 ? segmentProgress : 1)
    const coords = [...visible.slice(0, -1).map(p => `${p.x},${p.y}`), `${interpX},${interpY}`]
    return coords.join(' ')
  }

  // 그라디언트 채우기 경로
  const buildFillPath = () => {
    const line = buildPolyline()
    if (!line) return ''
    const lastCoords = line.split(' ').pop()!.split(',')
    return `M ${points[0].x},${height * 0.73} L ${line.replace(/ /g, 'L ')} L ${lastCoords[0]},${height * 0.73} Z`
  }

  // 자막 렌더
  const mainSub = subtitles[subtitles.length - 1]
  const titleSub = subtitles[0]
  const titleOpacity = interpolate(localFrame, [0, 20], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <AbsoluteFill style={{ background: MONO_DARK.background }}>
      {/* 배경 그리드 */}
      <svg style={{ position: 'absolute', width: '100%', height: '100%', opacity: 0.06 }}>
        {[0.28, 0.4, 0.52, 0.64, 0.73].map((y, i) => (
          <line key={i} x1="15%" y1={`${y * 100}%`} x2="85%" y2={`${y * 100}%`}
            stroke={MONO_DARK.border} strokeWidth={1} />
        ))}
        {[0, 0.2, 0.4, 0.6, 0.8, 1].map((x, i) => {
          const px = width * 0.15 + x * width * 0.70
          return (
            <line key={i} x1={px} y1="28%" x2={px} y2="73%"
              stroke={MONO_DARK.border} strokeWidth={1} />
          )
        })}
      </svg>

      {/* 제목 */}
      <div style={{
        position: 'absolute',
        top: height * 0.08,
        width: '100%',
        textAlign: 'center',
        fontFamily: MONO_DARK.fontMono,
        fontSize: MONO_DARK.fontSize.small,
        color: MONO_DARK.textSecondary,
        letterSpacing: 6,
        textTransform: 'uppercase',
        opacity: titleOpacity,
      }}>
        {titleSub?.text || 'DATA VISUALIZATION'}
      </div>

      {/* SVG 그래프 */}
      <svg style={{ position: 'absolute', width: '100%', height: '100%' }}>
        <defs>
          <linearGradient id="fillGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={MONO_DARK.highlight} stopOpacity={0.3} />
            <stop offset="100%" stopColor={MONO_DARK.highlight} stopOpacity={0.0} />
          </linearGradient>
        </defs>

        {/* 채우기 영역 */}
        {buildFillPath() && (
          <path d={buildFillPath()} fill="url(#fillGrad)" />
        )}

        {/* 그래프 선 */}
        {buildPolyline() && (
          <polyline
            points={buildPolyline()}
            fill="none"
            stroke={MONO_DARK.highlight}
            strokeWidth={4}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {/* 데이터 포인트 */}
        {points.slice(0, visibleSegments + 1).map((p, i) => {
          const dotProgress = spring({
            frame: Math.max(0, localFrame - i * 8),
            fps,
            config: { stiffness: 200, damping: 12 },
          })
          return (
            <g key={i}>
              <circle cx={p.x} cy={p.y} r={interpolate(dotProgress, [0, 1], [0, 10])}
                fill={MONO_DARK.background} stroke={MONO_DARK.highlight} strokeWidth={3} />
              {/* 값 라벨 */}
              <text x={p.x} y={p.y - 20}
                textAnchor="middle"
                fontFamily={MONO_DARK.fontMono}
                fontSize={22}
                fill={MONO_DARK.highlight}
                opacity={dotProgress}
              >
                {p.value}
              </text>
            </g>
          )
        })}

        {/* X축 */}
        <line
          x1={`${15}%`} y1={`${73}%`} x2={`${85}%`} y2={`${73}%`}
          stroke={MONO_DARK.border} strokeWidth={2}
        />
      </svg>

      {/* 하단 핵심 메시지 */}
      {mainSub && (
        <div style={{
          position: 'absolute',
          bottom: height * 0.08,
          width: '100%',
          textAlign: 'center',
          fontFamily: MONO_DARK.fontDisplay,
          fontSize: MONO_DARK.fontSize.heading,
          fontWeight: 700,
          color: MONO_DARK.textAccent,
          opacity: interpolate(localFrame, [ANIM_CONFIG.enterFrames, ANIM_CONFIG.enterFrames + 20], [0, 1], { extrapolateRight: 'clamp' }),
        }}>
          {mainSub.text}
        </div>
      )}

      {/* DEV 오버레이 */}
      {devMode && (
        <div style={{
          position: 'absolute', top: 20, right: 20,
          background: 'rgba(255,165,0,0.85)', color: '#000',
          fontFamily: MONO_DARK.fontMono, fontSize: 22,
          padding: '6px 16px', borderRadius: 6, fontWeight: 700, zIndex: 9999,
        }}>
          SCENE {sceneId} · graph-focus
        </div>
      )}
    </AbsoluteFill>
  )
}
