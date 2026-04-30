/**
 * overlay.ts — ISS-151: SubtitleOverlay 슬롯용 TypeScript 타입
 *
 * Backend OverlayOutput (backend/app/services/overlay_generator_service.py) 과
 * 1:1 매칭. SoT는 Python 서비스 측이며 이 파일은 미러링.
 *
 * Plan: docs/01-plan/features/video-use-integration.plan.md
 */

export type OverlayStyleType = "subtitle" | "emphasis" | "animation";

/**
 * 단어 단위 타임스탬프 (Whisper STT 결과 기반).
 * 기존 WordTimestamp(remotion/types.ts)와 동일 구조지만
 * 오버레이 파이프라인 전용으로 확장(speakerId, confidence 포함).
 */
export interface WordTimestampTS {
  word: string;
  start: number; // seconds
  end: number; // seconds
  speakerId?: string | null;
  confidence?: number | null;
}

/**
 * overlay_generator_service.OverlayOutput 미러링.
 * remotionJsx는 서버 렌더 경로용으로 클라이언트에서 eval하지 않음.
 */
export interface OverlayOutputTS {
  remotionJsx: string; // 향후 동적 컴포넌트 로드용 (현재 미사용)
  compositionId: string;
  durationFrames: number;
  assetPaths: string[];
  fps: number; // 기본 30
}

/**
 * brand-dna.json design_tokens 중 오버레이에 필요한 최소 토큰.
 */
export interface BrandTokensTS {
  colors?: {
    hero?: string;
    textPrimary?: string;
    surface?: string;
    surfaceAlt?: string;
    accent?: string;
  };
  typography?: {
    fontHeading?: string;
    fontBody?: string;
    fontMono?: string;
  };
}

/**
 * overlay_generator_service가 생성하는 청크 단위 자막.
 * 2~7단어 그룹 기준, start/end는 글로벌 타임라인(초).
 */
export interface SubtitleChunkTS {
  text: string;
  start: number; // seconds (global timeline)
  end: number; // seconds (global timeline)
  wordCount: number;
}
