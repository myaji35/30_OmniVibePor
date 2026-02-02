'use client';

import React from 'react';
import SectionCard from './SectionCard';

interface SectionDetail {
  section_id: string;
  type: 'hook' | 'body' | 'cta';
  order: number;
  script: string;
  start_time: number;
  end_time: number;
  duration: number;
  thumbnail_url?: string;
  metadata: {
    word_count: number;
    estimated_duration: number;
    actual_duration: number;
  };
}

interface SectionListProps {
  sections: SectionDetail[];
  activeSectionId?: string;
  onSectionClick?: (sectionId: string, startTime: number) => void;
}

const SectionList: React.FC<SectionListProps> = ({
  sections,
  activeSectionId,
  onSectionClick,
}) => {
  // 섹션을 순서대로 정렬
  const sortedSections = [...sections].sort((a, b) => a.order - b.order);

  // 통계 계산
  const stats = {
    totalDuration: sections.reduce((sum, s) => sum + s.duration, 0),
    hookCount: sections.filter((s) => s.type === 'hook').length,
    bodyCount: sections.filter((s) => s.type === 'body').length,
    ctaCount: sections.filter((s) => s.type === 'cta').length,
    totalWords: sections.reduce((sum, s) => sum + s.metadata.word_count, 0),
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-col gap-4">
      {/* 헤더: 통계 정보 */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-100">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-800">콘티 섹션</h3>
          <span className="text-sm text-gray-600 font-mono">
            총 {formatDuration(stats.totalDuration)}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-white rounded-md p-3 border border-gray-200">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-xs text-gray-600 font-medium">훅</span>
            </div>
            <span className="text-xl font-bold text-gray-800">{stats.hookCount}</span>
          </div>

          <div className="bg-white rounded-md p-3 border border-gray-200">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="text-xs text-gray-600 font-medium">본문</span>
            </div>
            <span className="text-xl font-bold text-gray-800">{stats.bodyCount}</span>
          </div>

          <div className="bg-white rounded-md p-3 border border-gray-200">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-xs text-gray-600 font-medium">CTA</span>
            </div>
            <span className="text-xl font-bold text-gray-800">{stats.ctaCount}</span>
          </div>

          <div className="bg-white rounded-md p-3 border border-gray-200">
            <div className="flex items-center gap-2 mb-1">
              <svg
                className="w-3 h-3 text-gray-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <span className="text-xs text-gray-600 font-medium">단어</span>
            </div>
            <span className="text-xl font-bold text-gray-800">{stats.totalWords}</span>
          </div>
        </div>
      </div>

      {/* 섹션 리스트 */}
      {sortedSections.length === 0 ? (
        <div className="bg-gray-50 rounded-lg p-8 text-center border-2 border-dashed border-gray-300">
          <svg
            className="w-16 h-16 mx-auto mb-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
          <p className="text-gray-600 font-medium">섹션이 없습니다</p>
          <p className="text-sm text-gray-500 mt-1">
            콘티를 생성하면 여기에 표시됩니다
          </p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
          {sortedSections.map((section) => (
            <SectionCard
              key={section.section_id}
              section={section}
              isActive={section.section_id === activeSectionId}
              onClick={onSectionClick}
            />
          ))}
        </div>
      )}

      {/* 푸터: 액션 힌트 */}
      {sortedSections.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <svg
              className="w-5 h-5 text-blue-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>
              섹션 카드를 클릭하면 해당 구간부터 재생됩니다
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default SectionList;
