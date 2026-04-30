/**
 * SmokeTest.tsx — ISS-162: Remotion 실제 렌더 smoke 테스트용 컴포지션
 *
 * Phase B Gate G3-a 검증.
 * 30fps × 5초 = 150 frames. SubtitleOverlay 슬롯에 mock chunks 주입.
 *
 * 이슈: ISS-162 (RUN_TESTS, Eng P0)
 */
import React from "react";
import { AbsoluteFill } from "remotion";
import { SubtitleOverlay } from "./SubtitleOverlay";
import type { SubtitleChunkTS } from "./types/overlay";

const MOCK_CHUNKS: SubtitleChunkTS[] = [
  { text: "HELLO WORLD", start: 0.5, end: 2.0, wordCount: 2 },
  { text: "VIDEO USE", start: 2.2, end: 4.0, wordCount: 2 },
  { text: "PHASE A", start: 4.2, end: 5.0, wordCount: 2 },
];

export const SmokeTestComposition: React.FC = () => (
  <AbsoluteFill style={{ background: "#0F0E1A" }}>
    <AbsoluteFill
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#FFFFFF",
        fontSize: 32,
        fontFamily: "Pretendard, sans-serif",
      }}
    >
      OmniVibe Pro — Smoke
    </AbsoluteFill>
    <SubtitleOverlay
      chunks={MOCK_CHUNKS}
      brandTokens={{
        colors: { textPrimary: "#FFFFFF", hero: "#22D3EE" },
        typography: { fontHeading: "Pretendard, sans-serif" },
      }}
      fps={30}
      position="bottom"
      uppercase
    />
  </AbsoluteFill>
);
