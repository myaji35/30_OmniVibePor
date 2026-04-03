/**
 * Presentation Page
 *
 * PDF 프리젠테이션 영상 생성 테스트 페이지
 * REALPLAN.md Phase 7
 */

"use client";

import React, { useState } from "react";
import PresentationMode from "@/components/PresentationMode";
import AppShell from "@/components/AppShell";

export default function PresentationPage() {
  const [projectId] = useState("test_project_001");
  const [presentationId, setPresentationId] = useState<string | null>(null);

  const handleComplete = (videoPath: string) => {
    console.log("Video generation completed:", videoPath);
  };

  return (
    <AppShell>
      <PresentationMode
        projectId={projectId}
        presentationId={presentationId}
        onComplete={handleComplete}
      />
    </AppShell>
  );
}
