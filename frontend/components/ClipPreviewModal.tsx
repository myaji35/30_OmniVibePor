'use client';

import React, { useRef, useEffect } from 'react';
import { Clip } from '@/lib/api/clips';

interface ClipPreviewModalProps {
  clip: Clip | null;
  isOpen: boolean;
  onClose: () => void;
  onReplace: (clipId: string) => Promise<void>;
  isCurrentClip?: boolean;
}

const ClipPreviewModal: React.FC<ClipPreviewModalProps> = ({
  clip,
  isOpen,
  onClose,
  onReplace,
  isCurrentClip = false,
}) => {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isReplacing, setIsReplacing] = React.useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen && clip) {
      dialog.showModal();
    } else {
      dialog.close();
    }
  }, [isOpen, clip]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleClose = () => {
      if (videoRef.current) {
        videoRef.current.pause();
      }
      onClose();
    };

    dialog.addEventListener('close', handleClose);
    return () => dialog.removeEventListener('close', handleClose);
  }, [onClose]);

  const handleReplace = async () => {
    if (!clip || isCurrentClip) return;

    setIsReplacing(true);
    try {
      await onReplace(clip.clip_id);
      onClose();
    } catch (error) {
      console.error('Failed to replace clip:', error);
    } finally {
      setIsReplacing(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDialogElement>) => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const rect = dialog.getBoundingClientRect();
    const isInDialog =
      e.clientX >= rect.left &&
      e.clientX <= rect.right &&
      e.clientY >= rect.top &&
      e.clientY <= rect.bottom;

    if (!isInDialog) {
      onClose();
    }
  };

  const getVariationBadge = (variation?: 'camera_angle' | 'lighting' | 'color_tone') => {
    if (!variation) return null;

    const badges = {
      camera_angle: { label: '카메라 앵글', color: 'bg-purple-500' },
      lighting: { label: '조명', color: 'bg-orange-500' },
      color_tone: { label: '색감', color: 'bg-pink-500' },
    };

    const badge = badges[variation];
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold text-white ${badge.color}`}>
        {badge.label}
      </span>
    );
  };

  if (!clip) return null;

  return (
    <dialog
      ref={dialogRef}
      onClick={handleBackdropClick}
      className="backdrop:bg-black backdrop:bg-opacity-70 bg-transparent p-0 max-w-4xl w-full rounded-lg"
    >
      <div className="bg-white rounded-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-gray-800">클립 미리보기</h2>
            {getVariationBadge(clip.variation)}
            {isCurrentClip && (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500 text-white">
                현재 사용 중
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="닫기"
          >
            <svg
              className="w-6 h-6 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Video Player */}
        <div className="relative bg-black">
          <video
            ref={videoRef}
            src={clip.video_path}
            controls
            className="w-full max-h-[60vh] object-contain"
            poster={clip.thumbnail_url}
          >
            Your browser does not support the video tag.
          </video>
        </div>

        {/* Prompt */}
        <div className="p-4 bg-gray-50 border-t border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">프롬프트</h3>
          <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
            {clip.prompt}
          </p>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between p-4 border-t border-gray-200 bg-white">
          <div className="text-xs text-gray-500">
            생성일: {new Date(clip.created_at).toLocaleString('ko-KR')}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors font-medium"
            >
              닫기
            </button>
            {!isCurrentClip && (
              <button
                onClick={handleReplace}
                disabled={isReplacing}
                className={`
                  px-6 py-2 rounded-lg font-medium transition-colors
                  ${
                    isReplacing
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-500 hover:bg-blue-600 text-white'
                  }
                `}
              >
                {isReplacing ? (
                  <span className="flex items-center gap-2">
                    <svg
                      className="animate-spin h-4 w-4"
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
                    교체 중...
                  </span>
                ) : (
                  '이 클립으로 교체'
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </dialog>
  );
};

export default ClipPreviewModal;
