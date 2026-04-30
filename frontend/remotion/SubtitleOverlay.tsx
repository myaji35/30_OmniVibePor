/**
 * SubtitleOverlay — ISS-151: Remotion <SubtitleOverlay> 슬롯
 *
 * overlay_generator_service(ISS-152 구현 예정)가 생성한 청크 단위 자막을
 * Remotion Composition에 합성하는 슬롯.
 * brand-dna.json design_tokens 기반 폰트/색상 자동 적용.
 *
 * Plan: docs/01-plan/features/video-use-integration.plan.md
 * SoT: backend/app/services/overlay_generator_service.py
 *
 * 주의: frontend/remotion/components/SubtitleOverlay.tsx 는 word-level
 * (기존 Whisper wordTimestamps 기반)이고, 이 파일은 청크 단위(OverlayOutput
 * 파이프라인 기반)로 역할이 다름. 네임스페이스 충돌 없음.
 */
import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";
import type { SubtitleChunkTS, BrandTokensTS } from "./types/overlay";

export interface SubtitleOverlayProps {
  chunks: SubtitleChunkTS[];
  brandTokens?: BrandTokensTS;
  fps?: number;
  position?: "bottom" | "center" | "top";
  uppercase?: boolean;
}

export const SubtitleOverlay: React.FC<SubtitleOverlayProps> = ({
  chunks,
  brandTokens,
  fps = 30,
  position = "bottom",
  uppercase = true,
}) => {
  const frame = useCurrentFrame();
  const currentSec = frame / fps;

  const activeChunk = chunks.find(
    (c) => currentSec >= c.start && currentSec <= c.end,
  );

  if (!activeChunk) return null;

  // 페이드 인/아웃: 100ms (3 frames @ 30fps)
  const chunkStartFrame = activeChunk.start * fps;
  const chunkEndFrame = activeChunk.end * fps;
  const opacity = interpolate(
    frame,
    [chunkStartFrame, chunkStartFrame + 3, chunkEndFrame - 3, chunkEndFrame],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const textColor = brandTokens?.colors?.textPrimary ?? "#F5F5F5";
  const fontFamily =
    brandTokens?.typography?.fontHeading ?? "Inter, Pretendard, sans-serif";

  const verticalStyle: React.CSSProperties =
    position === "bottom"
      ? { alignItems: "flex-end", paddingBottom: 80 }
      : position === "top"
        ? { alignItems: "flex-start", paddingTop: 80 }
        : { alignItems: "center" };

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        ...verticalStyle,
      }}
    >
      <div
        style={{
          opacity,
          color: textColor,
          fontFamily,
          fontSize: 64,
          fontWeight: 800,
          letterSpacing: 1,
          textShadow: "0 4px 16px rgba(0,0,0,0.6)",
          padding: "12px 32px",
          background: "rgba(0,0,0,0.4)",
          borderRadius: 8,
          maxWidth: "80%",
          textAlign: "center",
        }}
      >
        {uppercase ? activeChunk.text.toUpperCase() : activeChunk.text}
      </div>
    </AbsoluteFill>
  );
};
