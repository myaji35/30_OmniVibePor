/**
 * BGMEditor 사용 예시
 *
 * DirectorPanel 또는 다른 영상 편집 컴포넌트에 통합하여 사용
 */

"use client";

import React, { useState } from 'react';
import BGMEditor, { BGMSettings } from '@/components/BGMEditor';

export default function ExampleUsage() {
  const [bgmSettings, setBgmSettings] = useState<BGMSettings | null>(null);

  const handleBGMChange = (settings: BGMSettings) => {
    console.log('BGM 설정 변경:', settings);
    setBgmSettings(settings);
  };

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">BGM Editor 예시</h1>

      {/* BGM Editor 컴포넌트 */}
      <BGMEditor
        projectId="example-project-123"
        initialSettings={{
          volume: 0.5,
          fade_in_duration: 2,
          fade_out_duration: 2,
          start_time: 0,
          loop: false,
          ducking_enabled: true,
          ducking_level: 0.3,
        }}
        onSettingsChange={handleBGMChange}
      />

      {/* 현재 설정 표시 */}
      {bgmSettings && (
        <div className="mt-8 p-4 bg-gray-100 rounded-lg">
          <h3 className="font-bold mb-2">현재 BGM 설정:</h3>
          <pre className="text-sm overflow-auto">
            {JSON.stringify(bgmSettings, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

/**
 * DirectorPanel에 통합 예시
 */
export function DirectorPanelWithBGM() {
  return (
    <div className="space-y-6">
      {/* 기존 오디오 생성 섹션 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">🎙️ 음성 생성</h3>
        {/* ... 기존 DirectorPanel 내용 ... */}
      </div>

      {/* BGM 편집 섹션 */}
      <BGMEditor
        projectId="current-project-id"
        onSettingsChange={(settings) => {
          console.log('BGM 설정 업데이트:', settings);
          // 필요 시 상위 컴포넌트 상태 업데이트
        }}
      />

      {/* 비디오 생성 섹션 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">🎬 비디오 생성</h3>
        {/* ... 기존 비디오 생성 내용 ... */}
      </div>
    </div>
  );
}
