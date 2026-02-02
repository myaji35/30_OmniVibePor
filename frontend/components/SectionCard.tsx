'use client';

import React from 'react';

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

interface SectionCardProps {
  section: SectionDetail;
  isActive?: boolean;
  onClick?: (sectionId: string, startTime: number) => void;
}

const SectionCard: React.FC<SectionCardProps> = ({ section, isActive = false, onClick }) => {
  const handleClick = () => {
    if (onClick) {
      onClick(section.section_id, section.start_time);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getBadgeStyles = (type: 'hook' | 'body' | 'cta') => {
    switch (type) {
      case 'hook':
        return 'bg-red-500 text-white';
      case 'body':
        return 'bg-blue-500 text-white';
      case 'cta':
        return 'bg-green-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getBadgeLabel = (type: 'hook' | 'body' | 'cta'): string => {
    switch (type) {
      case 'hook':
        return '훅';
      case 'body':
        return '본문';
      case 'cta':
        return 'CTA';
    }
  };

  const truncateScript = (script: string, lines: number = 3): string => {
    const lineBreaks = script.split('\n').slice(0, lines).join('\n');
    if (lineBreaks.length > 150) {
      return lineBreaks.substring(0, 150) + '...';
    }
    return lineBreaks;
  };

  return (
    <div
      className={`
        flex gap-4 p-4 rounded-lg border-2 cursor-pointer transition-all duration-200
        hover:shadow-lg hover:scale-[1.02]
        ${isActive
          ? 'border-blue-500 bg-blue-50 shadow-md'
          : 'border-gray-200 bg-white hover:border-gray-300'
        }
      `}
      onClick={handleClick}
    >
      {/* 썸네일 영역 */}
      <div className="flex-shrink-0 w-32 md:w-40 lg:w-48">
        <div className="aspect-video bg-gray-200 rounded-md overflow-hidden">
          {section.thumbnail_url ? (
            <img
              src={section.thumbnail_url}
              alt={`${getBadgeLabel(section.type)} 섹션 썸네일`}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
              <svg
                className="w-12 h-12"
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
            </div>
          )}
        </div>
      </div>

      {/* 콘텐츠 영역 */}
      <div className="flex-1 flex flex-col gap-2 min-w-0">
        {/* 상단: 배지 + 시간 */}
        <div className="flex items-center justify-between gap-2">
          <span
            className={`
              px-3 py-1 rounded-full text-xs font-semibold uppercase
              ${getBadgeStyles(section.type)}
            `}
          >
            {getBadgeLabel(section.type)}
          </span>
          <span className="text-sm text-gray-600 font-mono whitespace-nowrap">
            {formatTime(section.start_time)} - {formatTime(section.end_time)}
          </span>
        </div>

        {/* 중단: 스크립트 미리보기 */}
        <div className="flex-1">
          <p className="text-sm text-gray-700 leading-relaxed line-clamp-3 whitespace-pre-line">
            {truncateScript(section.script)}
          </p>
        </div>

        {/* 하단: 메타데이터 */}
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <svg
              className="w-4 h-4"
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
            <span>{section.metadata.word_count}단어</span>
          </div>
          <div className="flex items-center gap-1">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>{section.duration.toFixed(1)}초</span>
          </div>
          {section.metadata.estimated_duration !== section.metadata.actual_duration && (
            <div className="flex items-center gap-1 text-orange-500">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <span>실측 차이</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SectionCard;
