/**
 * PresentationMode Example Usage
 *
 * 다양한 사용 사례를 보여주는 예제 컴포넌트
 */

"use client";

import React, { useState } from "react";
import PresentationMode from "./PresentationMode";

// ==================== Example 1: Basic Usage ====================

export function BasicPresentationExample() {
  const handleComplete = (videoPath: string) => {
    alert(`영상 생성 완료! 경로: ${videoPath}`);
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">기본 사용 예제</h2>
      <PresentationMode projectId="demo_project_001" onComplete={handleComplete} />
    </div>
  );
}

// ==================== Example 2: With Existing Presentation ====================

export function ExistingPresentationExample() {
  const [presentationId] = useState("pres_abc123xyz");

  const handleComplete = (videoPath: string) => {
    console.log("Video ready:", videoPath);
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">기존 프리젠테이션 편집</h2>
      <p className="text-gray-600 mb-4">
        이미 업로드된 프리젠테이션을 다시 열어 편집할 수 있습니다.
      </p>
      <PresentationMode
        projectId="demo_project_001"
        presentationId={presentationId}
        onComplete={handleComplete}
      />
    </div>
  );
}

// ==================== Example 3: With Custom Callbacks ====================

export function CustomCallbacksExample() {
  const [status, setStatus] = useState<string>("대기 중");
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  const handleComplete = (videoPath: string) => {
    setStatus("완료");
    setVideoUrl(videoPath);

    // 커스텀 로직 (예: 다른 페이지로 이동)
    console.log("Redirecting to video player...");
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">커스텀 콜백 예제</h2>

      {/* Status Display */}
      <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-gray-600">현재 상태</p>
        <p className="text-lg font-semibold text-blue-900">{status}</p>
        {videoUrl && (
          <a
            href={videoUrl}
            className="text-blue-600 hover:underline text-sm"
            target="_blank"
            rel="noopener noreferrer"
          >
            영상 보기 →
          </a>
        )}
      </div>

      <PresentationMode
        projectId="demo_project_001"
        onComplete={handleComplete}
      />
    </div>
  );
}

// ==================== Example 4: Multiple Presentations ====================

export function MultiplePresentationsExample() {
  const [presentations, setPresentations] = useState<
    Array<{ id: string; projectId: string; videoPath?: string }>
  >([
    { id: "pres_001", projectId: "project_a" },
    { id: "pres_002", projectId: "project_b" },
  ]);
  const [activeIndex, setActiveIndex] = useState(0);

  const handleComplete = (videoPath: string) => {
    setPresentations((prev) =>
      prev.map((p, index) =>
        index === activeIndex ? { ...p, videoPath } : p
      )
    );
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">여러 프리젠테이션 관리</h2>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        {presentations.map((pres, index) => (
          <button
            key={pres.id}
            onClick={() => setActiveIndex(index)}
            className={`px-4 py-2 font-medium transition-colors ${
              activeIndex === index
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            프리젠테이션 {index + 1}
            {pres.videoPath && " ✓"}
          </button>
        ))}
      </div>

      {/* Active Presentation */}
      {presentations[activeIndex] && (
        <PresentationMode
          key={presentations[activeIndex].id}
          projectId={presentations[activeIndex].projectId}
          presentationId={presentations[activeIndex].id}
          onComplete={handleComplete}
        />
      )}
    </div>
  );
}

// ==================== Example 5: Integrated Dashboard ====================

export function IntegratedDashboardExample() {
  const [step, setStep] = useState<"create" | "edit" | "view">("create");
  const [currentPresentationId, setCurrentPresentationId] = useState<string | null>(null);
  const [videoPath, setVideoPath] = useState<string | null>(null);

  const handleComplete = (path: string) => {
    setVideoPath(path);
    setStep("view");
  };

  const handleNewPresentation = () => {
    setCurrentPresentationId(null);
    setVideoPath(null);
    setStep("create");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">프리젠테이션 대시보드</h1>
          <button
            onClick={handleNewPresentation}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            새 프리젠테이션
          </button>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-7xl mx-auto py-6">
        {step === "create" && (
          <PresentationMode
            projectId="dashboard_project"
            onComplete={handleComplete}
          />
        )}

        {step === "view" && videoPath && (
          <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
            <h2 className="text-2xl font-bold text-green-900 mb-4">영상 생성 완료!</h2>
            <p className="text-gray-600 mb-6">프리젠테이션 영상이 성공적으로 생성되었습니다.</p>
            <div className="flex gap-4 justify-center">
              <a
                href={videoPath}
                download
                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                다운로드
              </a>
              <button
                onClick={handleNewPresentation}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                새 프리젠테이션 만들기
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
