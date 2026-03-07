/**
 * VIDEOGEN 레이아웃 컴포넌트 공통 타입
 */
import type { SubtitleToken } from '../scene-analyzer'

export interface SceneProps {
  sceneId: number
  subtitles: SubtitleToken[]
  sceneStartFrame: number      // 컴포지션 내 씬 시작 프레임
  animation: string            // 애니메이션 효과 타입
  devMode: boolean             // SCENE N 오버레이 표시 여부
  videoSrc?: string            // 경로 A에서만 사용 (AI/스톡 소스)
}
