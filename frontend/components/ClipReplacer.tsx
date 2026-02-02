'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { useClipReplacer } from '@/hooks/useClipReplacer';
import ClipPreviewModal from './ClipPreviewModal';
import { Clip } from '@/lib/api/clips';

interface ClipReplacerProps {
  sectionId: string;
  onClipReplaced?: (clipId: string) => void;
}

const ClipReplacer: React.FC<ClipReplacerProps> = ({ sectionId, onClipReplaced }) => {
  const {
    data,
    isLoading,
    isGenerating,
    generationProgress,
    error,
    generateClips,
    replaceCurrentClip,
    deleteClip,
  } = useClipReplacer(sectionId);

  const [previewClip, setPreviewClip] = useState<Clip | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isCurrentClipPreview, setIsCurrentClipPreview] = useState(false);

  const handleClipClick = (clip: Clip, isCurrent: boolean = false) => {
    setPreviewClip(clip);
    setIsCurrentClipPreview(isCurrent);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setPreviewClip(null);
    setIsCurrentClipPreview(false);
  };

  const handleReplaceClip = async (clipId: string) => {
    await replaceCurrentClip(clipId);
    if (onClipReplaced) {
      onClipReplaced(clipId);
    }
  };

  const handleDeleteClip = async (clipId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('이 대체 클립을 삭제하시겠습니까?')) {
      await deleteClip(clipId);
    }
  };

  const getVariationBadge = (variation?: 'camera_angle' | 'lighting' | 'color_tone') => {
    if (!variation) return null;

    const badges = {
      camera_angle: { label: '카메라', color: 'bg-purple-500' },
      lighting: { label: '조명', color: 'bg-orange-500' },
      color_tone: { label: '색감', color: 'bg-pink-500' },
    };

    const badge = badges[variation];
    return (
      <span className={`px-2 py-1 rounded text-xs font-semibold text-white ${badge.color}`}>
        {badge.label}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="flex flex-col items-center gap-3">
          <svg
            className="animate-spin h-8 w-8 text-blue-500"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <p className="text-sm text-gray-600">클립 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center gap-2 text-red-800">
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          <span className="text-sm font-medium">{error}</span>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
      {/* Current Clip Section */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-3">현재 사용 중인 클립</h3>
        <div
          onClick={() => handleClipClick(data.current_clip, true)}
          className="relative group cursor-pointer overflow-hidden rounded-lg border-2 border-blue-500 bg-gradient-to-br from-blue-50 to-white transition-all hover:shadow-lg"
        >
          <div className="aspect-video bg-gray-200 overflow-hidden relative">
            {data.current_clip.thumbnail_url ? (
              <Image
                src={data.current_clip.thumbnail_url}
                alt="현재 클립 썸네일"
                fill
                className="object-cover group-hover:scale-105 transition-transform duration-300"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-400">
                <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
          <div className="absolute top-3 left-3">
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500 text-white shadow-md">
              현재 사용 중
            </span>
          </div>
          <div className="p-4 bg-white bg-opacity-95">
            <p className="text-sm text-gray-700 line-clamp-2">{data.current_clip.prompt}</p>
          </div>
        </div>
      </div>

      {/* Alternative Clips Gallery */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-3">대체 클립</h3>
        {data.alternatives.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {data.alternatives.map((clip) => (
              <div
                key={clip.clip_id}
                onClick={() => handleClipClick(clip, false)}
                className="relative group cursor-pointer overflow-hidden rounded-lg border-2 border-gray-200 hover:border-blue-400 transition-all hover:shadow-lg"
              >
                <div className="aspect-video bg-gray-200 overflow-hidden relative">
                  {clip.thumbnail_url ? (
                    <Image
                      src={clip.thumbnail_url}
                      alt={`대체 클립 썸네일`}
                      fill
                      className="object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                <div className="absolute top-2 left-2 flex gap-2">
                  {getVariationBadge(clip.variation)}
                </div>
                <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => handleDeleteClip(clip.clip_id, e)}
                    className="p-1.5 bg-red-500 hover:bg-red-600 text-white rounded-full shadow-md transition-colors"
                    aria-label="삭제"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
                <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                  <button className="w-full py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-semibold rounded transition-colors">
                    교체하기
                  </button>
                </div>
                <div className="p-3 bg-white">
                  <p className="text-xs text-gray-600 line-clamp-2">{clip.prompt}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 px-4 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-600">대체 클립이 아직 없습니다</p>
            <p className="text-xs text-gray-500">아래 버튼을 클릭하여 AI 대체 클립을 생성하세요</p>
          </div>
        )}
      </div>

      {/* Generate Button */}
      <div className="pt-4 border-t border-gray-200">
        <button
          onClick={generateClips}
          disabled={isGenerating}
          className={`
            w-full py-3 px-6 rounded-lg font-semibold transition-all
            ${
              isGenerating
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-md hover:shadow-lg'
            }
          `}
        >
          {isGenerating ? (
            <div className="flex items-center justify-center gap-3">
              <svg
                className="animate-spin h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <div className="flex flex-col items-start">
                <span>{generationProgress?.message || 'AI 영상 생성 중...'}</span>
                {generationProgress && generationProgress.progress > 0 && (
                  <div className="w-48 h-1.5 bg-white bg-opacity-30 rounded-full mt-1 overflow-hidden">
                    <div
                      className="h-full bg-white rounded-full transition-all duration-500"
                      style={{ width: `${generationProgress.progress}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              <span>대체 클립 생성</span>
            </div>
          )}
        </button>
        {isGenerating && (
          <p className="mt-2 text-xs text-center text-gray-500">
            약 50초 소요됩니다. 다른 작업을 진행하셔도 됩니다.
          </p>
        )}
      </div>

      {/* Preview Modal */}
      <ClipPreviewModal
        clip={previewClip}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onReplace={handleReplaceClip}
        isCurrentClip={isCurrentClipPreview}
      />
    </div>
  );
};

export default ClipReplacer;
