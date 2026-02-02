/**
 * Presentation Page
 *
 * PDF 프리젠테이션 영상 생성 테스트 페이지
 * REALPLAN.md Phase 7
 */

"use client";

import React, { useState } from "react";
import PresentationMode from "@/components/PresentationMode";

export default function PresentationPage() {
  // 실제 환경에서는 로그인한 사용자의 프로젝트 ID를 사용
  const [projectId] = useState("test_project_001");
  const [presentationId, setPresentationId] = useState<string | null>(null);

  const handleComplete = (videoPath: string) => {
    console.log("Video generation completed:", videoPath);
    alert(`영상 생성 완료! 경로: ${videoPath}`);
  };

  return (
    <div>
      <PresentationMode
        projectId={projectId}
        presentationId={presentationId}
        onComplete={handleComplete}
      />
    </div>
  );
}
