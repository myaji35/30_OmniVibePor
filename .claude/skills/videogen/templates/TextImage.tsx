/**
 * TextImage — 텍스트 + 이미지 분할 레이아웃
 * 설명 + 시각 보조 씬에 사용 (좌: 텍스트 / 우: 이미지 플레이스홀더)
 * 경로 A에서는 videoSrc / 경로 B에서는 SVG 일러스트 플레이스홀더 사용
 */
import React from 'react'
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate, Img } from 'remotion'
import { MONO_DARK, ANIM_CONFIG } from '../styles/monoDark'
import type { SceneProps } from './types'

// 이미지 없을 때 보여줄 SVG 플레이스홀더
const ImagePlaceholder: React.FC<{ width: number; height: number; text: string }> = ({ width, height, text }) => (
  <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
    <rect width={width} height={height} fill={MONO_DARK.surfaceAlt} rx={12} />
    <rect x={width * 0.2} y={height * 0.25} width={width * 0.6} height={height * 0.5}
      fill="none" stroke={MONO_DARK.border} strokeWidth={2} strokeDasharray="12 6" rx={8} />
    {/* 이미지 아이콘 */}
    <circle cx={width * 0.35} cy={height * 0.42} r={width * 0.04}
      fill={MONO_DARK.textTertiary} />
    <polygon
      points={`${width * 0.2},${height * 0.62} ${width * 0.45},${height * 0.38} ${width * 0.6},${height * 0.52} ${width * 0.72},${height * 0.42} ${width * 0.8},${height * 0.62}`}
      fill={MONO_DARK.border}
    />
    {/* 라벨 */}
    <text x={width * 0.5} y={height * 0.75}
      textAnchor="middle"
      fontFamily={MONO_DARK.fontMono}
      fontSize={18}
      fill={MONO_DARK.textTertiary}
      letterSpacing={2}
    >
      {text || 'VISUAL'}
    </text>
  </svg>
)

export const TextImage: React.FC<SceneProps> = ({
  subtitles,
  sceneStartFrame,
  animation,
  sceneId,
  devMode,
  videoSrc,
}) => {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const localFrame = frame - sceneStartFrame

  // 좌측 텍스트 패널 너비 (60%)
  const textW = width * 0.55
  const imgW  = width * 0.45

  // 전체 패널 진입 애니메이션
  const panelProgress = spring({ frame: localFrame, fps, config: { stiffness: 60, damping: 18 } })
  const panelOpacity  = interpolate(panelProgress, [0, 1], [0, 1])

  // 이미지 슬라이드 인 (우→중앙)
  const imgSlide = interpolate(
    spring({ frame: localFrame, fps, config: { stiffness: 70, damping: 20 } }),
    [0, 1], [120, 0]
  )

  return (
    <AbsoluteFill style={{ background: MONO_DARK.background, flexDirection: 'row' }}>

      {/* ── 좌측: 텍스트 영역 ── */}
      <div style={{
        width: textW,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: `${MONO_DARK.padding.outer}px`,
        paddingRight: MONO_DARK.padding.inner,
        opacity: panelOpacity,
      }}>
        {/* 상단 장식선 */}
        <div style={{
          width: interpolate(localFrame, [0, 30], [0, 80], { extrapolateRight: 'clamp' }),
          height: 3,
          background: MONO_DARK.highlight,
          marginBottom: 32,
        }} />

        {/* 자막 순차 렌더 */}
        {subtitles.map((sub, i) => {
          const subStartMs = sub.startMs - subtitles[0].startMs
          const subStartFrame = Math.round(subStartMs / 1000 * fps)
          const subFrame = localFrame - subStartFrame
          const isVisible = subFrame >= 0

          const opacity = isVisible
            ? spring({ frame: subFrame, fps, config: { stiffness: ANIM_CONFIG.stiffness, damping: ANIM_CONFIG.damping } })
            : 0
          const translateX = isVisible
            ? interpolate(subFrame, [0, ANIM_CONFIG.enterFrames], [-50, 0], { extrapolateRight: 'clamp' })
            : -50

          const isFirst = i === 0
          const fontSize = isFirst ? MONO_DARK.fontSize.title : MONO_DARK.fontSize.body
          const fontWeight = isFirst ? 800 : 400
          const color = isFirst ? MONO_DARK.textAccent : MONO_DARK.textPrimary

          return (
            <div key={i} style={{
              opacity,
              transform: `translateX(${translateX}px)`,
              fontFamily: MONO_DARK.fontDisplay,
              fontSize,
              fontWeight,
              color,
              lineHeight: 1.35,
              marginBottom: isFirst ? 24 : 12,
            }}>
              {/* 첫 자막엔 네온 강조 처리 */}
              {isFirst ? (
                <span>
                  {sub.text.split(' ').map((word, wi) => (
                    <span key={wi} style={{
                      color: wi === 0 ? MONO_DARK.highlight : MONO_DARK.textAccent,
                    }}>
                      {word}{' '}
                    </span>
                  ))}
                </span>
              ) : sub.text}
            </div>
          )
        })}

        {/* 하단 보조 라벨 */}
        <div style={{
          marginTop: 40,
          fontFamily: MONO_DARK.fontMono,
          fontSize: MONO_DARK.fontSize.small,
          color: MONO_DARK.textTertiary,
          letterSpacing: 4,
          textTransform: 'uppercase',
          opacity: interpolate(localFrame, [30, 50], [0, 1], { extrapolateRight: 'clamp' }),
        }}>
          OmniVibe Pro
        </div>
      </div>

      {/* ── 우측: 이미지/비디오 영역 ── */}
      <div style={{
        width: imgW,
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transform: `translateX(${imgSlide}px)`,
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* 배경 그라디언트 */}
        <div style={{
          position: 'absolute', inset: 0,
          background: `linear-gradient(135deg, ${MONO_DARK.surface} 0%, ${MONO_DARK.background} 100%)`,
        }} />

        {/* 이미지 or 플레이스홀더 */}
        <div style={{
          width: imgW * 0.85,
          height: height * 0.65,
          borderRadius: 16,
          overflow: 'hidden',
          border: `1px solid ${MONO_DARK.border}`,
          position: 'relative',
          zIndex: 1,
          boxShadow: `0 0 60px ${MONO_DARK.highlight}20`,
        }}>
          {videoSrc ? (
            <Img
              src={videoSrc}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          ) : (
            <ImagePlaceholder
              width={imgW * 0.85}
              height={height * 0.65}
              text={subtitles[0]?.text.slice(0, 12) || 'VISUAL'}
            />
          )}
        </div>

        {/* 우측 하단 장식 도형 */}
        <div style={{
          position: 'absolute', bottom: 40, right: 40,
          width: 120, height: 120,
          borderRadius: '50%',
          border: `2px solid ${MONO_DARK.highlightAlt}30`,
          opacity: interpolate(localFrame, [20, 40], [0, 1], { extrapolateRight: 'clamp' }),
        }} />
      </div>

      {/* DEV 오버레이 */}
      {devMode && (
        <div style={{
          position: 'absolute', top: 20, right: 20,
          background: 'rgba(255,165,0,0.85)', color: '#000',
          fontFamily: MONO_DARK.fontMono, fontSize: 22,
          padding: '6px 16px', borderRadius: 6, fontWeight: 700, zIndex: 9999,
        }}>
          SCENE {sceneId} · text-image
        </div>
      )}
    </AbsoluteFill>
  )
}
