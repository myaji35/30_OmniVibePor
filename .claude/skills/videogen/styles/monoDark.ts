/**
 * VIDEOGEN — Mono Dark Design Token System
 * 모노 다크 테마 글로벌 디자인 토큰 (1920×1080 기준)
 */

export const MONO_DARK = {
  // ── 배경 ──────────────────────────────────────────
  background:  '#0A0A0A',   // 페이지 배경 (거의 검정)
  surface:     '#141414',   // 카드/패널 배경
  surfaceAlt:  '#1C1C1C',   // 보조 패널
  surfaceHigh: '#242424',   // 강조 패널
  border:      '#2A2A2A',   // 구분선
  borderLight: '#3A3A3A',   // 연한 구분선

  // ── 텍스트 ────────────────────────────────────────
  textPrimary:   '#E5E5E5', // 메인 텍스트
  textSecondary: '#A0A0A0', // 보조 텍스트
  textTertiary:  '#666666', // 3차 텍스트
  textAccent:    '#FFFFFF', // 강조 흰색

  // ── 포인트 컬러 ────────────────────────────────────
  highlight:    '#00FF88',  // 네온 그린 (수치/핵심 강조)
  highlightAlt: '#00CFFF', // 네온 블루 (보조 강조)
  warning:      '#FFB800',  // 경고/주목
  danger:       '#FF4444',  // 위험/감소
  purple:       '#A855F7',  // 보라 (포인트)

  // ── 타이포그래피 ──────────────────────────────────
  fontMono:    '"JetBrains Mono", "Fira Code", "SF Mono", monospace',
  fontDisplay: '"Pretendard", "Inter", "Noto Sans KR", sans-serif',

  // ── 폰트 크기 (px, 1920×1080 기준) ─────────────────
  fontSize: {
    display:  140, // 훅 임팩트 텍스트 (단어 1~2개)
    hero:     100, // 씬 핵심 메시지
    title:     72, // 씬 제목
    heading:   52, // 소제목
    body:      40, // 본문
    caption:   30, // 자막 오버레이
    small:     24, // 보조 텍스트
  },

  // ── 여백 ──────────────────────────────────────────
  padding: {
    outer: 80,   // 화면 외곽 여백
    inner: 48,   // 요소 내부 여백
    tight: 24,   // 밀착 여백
  },

  // ── 캔버스 ────────────────────────────────────────
  width:  1920,
  height: 1080,
  fps:    30,
} as const

export type MonoDarkTheme = typeof MONO_DARK

// ── 애니메이션 공통 설정 ──────────────────────────────
export const ANIM_CONFIG = {
  enterFrames:  15, // 등장 애니메이션 길이 (0.5초)
  exitFrames:    8, // 퇴장 애니메이션 길이
  stiffness:   200, // spring 강성
  damping:      20, // spring 감쇠
} as const

// ── 씬 타입별 기본 배경색 ────────────────────────────
export const SCENE_BG: Record<string, string> = {
  hook:  '#0A0A0A',
  intro: '#0D0D0D',
  body:  '#0A0A0A',
  cta:   '#111111',
}
