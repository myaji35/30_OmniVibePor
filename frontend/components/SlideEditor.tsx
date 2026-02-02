"use client";

/**
 * SlideEditor - 슬라이드 타이밍, 전환 효과, BGM 편집 컴포넌트
 *
 * 기능:
 * - 슬라이드 이미지 프리뷰
 * - 타이밍 조정 (start/end time + duration)
 * - 전환 효과 선택 (fade/slide/zoom)
 * - BGM 설정 (enable/volume/fade)
 * - Auto-adjust 버튼 (Whisper 타이밍 스냅)
 * - 인접 슬라이드 중복 검증
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import Image from 'next/image';

// ========================
// Type Definitions
// ========================

export interface SlideData {
  slide_id: string;
  slide_number: number;
  image_path: string;
  extracted_text: string;
  title?: string;
}

export interface SlideTiming {
  start_time: number;  // 초
  end_time: number;    // 초
  duration: number;    // 초 (read-only, calculated)
}

export interface BGMSettings {
  enabled: boolean;
  volume: number;           // 0.0-1.0
  fade_in_duration: number; // 초
  fade_out_duration: number; // 초
  custom_file_path?: string;
}

export type TransitionEffect = 'fade' | 'slide' | 'zoom';

export interface SlideEditorProps {
  slide: SlideData;
  timing: SlideTiming;
  transitionEffect: TransitionEffect;
  bgmSettings?: BGMSettings;
  adjacentSlides?: {
    previous?: { end_time: number };
    next?: { start_time: number };
  };
  whisperTiming?: {
    start_time: number;
    end_time: number;
  };
  onTimingChange?: (start: number, end: number) => void;
  onTransitionChange?: (effect: TransitionEffect) => void;
  onBGMChange?: (settings: BGMSettings) => void;
}

// ========================
// Transition Effect Options
// ========================

const TRANSITION_OPTIONS = [
  {
    value: 'fade' as TransitionEffect,
    label: '페이드',
    icon: '🌫️',
    description: '부드러운 교차 페이드',
  },
  {
    value: 'slide' as TransitionEffect,
    label: '슬라이드',
    icon: '➡️',
    description: '좌우로 밀어내기',
  },
  {
    value: 'zoom' as TransitionEffect,
    label: '줌',
    icon: '🔍',
    description: '확대/축소 효과',
  },
];

// ========================
// SlideEditor Component
// ========================

export default function SlideEditor({
  slide,
  timing,
  transitionEffect,
  bgmSettings,
  adjacentSlides,
  whisperTiming,
  onTimingChange,
  onTransitionChange,
  onBGMChange,
}: SlideEditorProps) {
  // State
  const [startTime, setStartTime] = useState(timing.start_time);
  const [endTime, setEndTime] = useState(timing.end_time);
  const [selectedTransition, setSelectedTransition] = useState(transitionEffect);
  const [bgm, setBgm] = useState<BGMSettings>(
    bgmSettings || {
      enabled: false,
      volume: 0.5,
      fade_in_duration: 1,
      fade_out_duration: 1,
    }
  );
  const [validationError, setValidationError] = useState<string | null>(null);
  const [imageLoading, setImageLoading] = useState(true);
  const [imageError, setImageError] = useState(false);

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Calculate duration
  const duration = endTime - startTime;

  // Sync with props
  useEffect(() => {
    setStartTime(timing.start_time);
    setEndTime(timing.end_time);
  }, [timing]);

  useEffect(() => {
    setSelectedTransition(transitionEffect);
  }, [transitionEffect]);

  // Validation
  const validateTiming = useCallback(
    (start: number, end: number): string | null => {
      if (end <= start) {
        return '종료 시간은 시작 시간보다 커야 합니다';
      }

      if (adjacentSlides?.previous && start < adjacentSlides.previous.end_time) {
        return `이전 슬라이드와 중복됩니다 (이전 종료: ${adjacentSlides.previous.end_time.toFixed(1)}초)`;
      }

      if (adjacentSlides?.next && end > adjacentSlides.next.start_time) {
        return `다음 슬라이드와 중복됩니다 (다음 시작: ${adjacentSlides.next.start_time.toFixed(1)}초)`;
      }

      if (start < 0) {
        return '시작 시간은 0보다 커야 합니다';
      }

      return null;
    },
    [adjacentSlides]
  );

  // Debounced timing change
  const debouncedTimingChange = useCallback(
    (start: number, end: number) => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      debounceTimerRef.current = setTimeout(() => {
        const error = validateTiming(start, end);
        setValidationError(error);

        if (!error) {
          onTimingChange?.(start, end);
        }
      }, 500);
    },
    [onTimingChange, validateTiming]
  );

  // Handle start time change
  const handleStartTimeChange = (value: number) => {
    setStartTime(value);
    debouncedTimingChange(value, endTime);
  };

  // Handle end time change
  const handleEndTimeChange = (value: number) => {
    setEndTime(value);
    debouncedTimingChange(startTime, value);
  };

  // Handle transition change
  const handleTransitionChange = (effect: TransitionEffect) => {
    setSelectedTransition(effect);
    onTransitionChange?.(effect);
  };

  // Handle BGM settings change
  const handleBGMChange = (updates: Partial<BGMSettings>) => {
    const newBgm = { ...bgm, ...updates };
    setBgm(newBgm);
    onBGMChange?.(newBgm);
  };

  // Auto-adjust to Whisper timing
  const handleAutoAdjust = () => {
    if (whisperTiming) {
      setStartTime(whisperTiming.start_time);
      setEndTime(whisperTiming.end_time);
      debouncedTimingChange(whisperTiming.start_time, whisperTiming.end_time);
    }
  };

  // Format time display (MM:SS.ms)
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}:${secs.padStart(4, '0')}`;
  };

  return (
    <div className="p-6 bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-900">
          슬라이드 #{slide.slide_number} 편집
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          {slide.title || slide.extracted_text.slice(0, 50) + '...'}
        </p>
      </div>

      {/* Validation Error */}
      {validationError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
          ⚠️ {validationError}
        </div>
      )}

      {/* Slide Preview */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-3">
          슬라이드 프리뷰
        </label>
        <div className="relative w-full bg-gray-100 rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
          {imageError ? (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-200">
              <div className="text-center">
                <div className="text-4xl mb-2">📄</div>
                <p className="text-sm text-gray-600">이미지를 불러올 수 없습니다</p>
                <p className="text-xs text-gray-500 mt-1">{slide.image_path}</p>
              </div>
            </div>
          ) : (
            <>
              {imageLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-200">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
                </div>
              )}
              <Image
                src={`http://localhost:8000${slide.image_path}`}
                alt={`Slide ${slide.slide_number}`}
                fill
                className="object-contain"
                onLoadingComplete={() => setImageLoading(false)}
                onError={() => {
                  setImageLoading(false);
                  setImageError(true);
                }}
                unoptimized
              />
            </>
          )}
        </div>
      </div>

      {/* Timing Adjustment */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-semibold text-gray-900">타이밍 조정</h4>
          {whisperTiming && (
            <button
              onClick={handleAutoAdjust}
              className="px-3 py-1 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 transition-colors"
            >
              🎯 자동 조정 (Whisper)
            </button>
          )}
        </div>

        {/* Start Time */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">시작 시간</label>
            <span className="text-sm font-semibold text-blue-600">
              {formatTime(startTime)}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min="0"
              max={endTime - 0.1}
              step="0.1"
              value={startTime}
              onChange={(e) => handleStartTimeChange(parseFloat(e.target.value))}
              className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            />
            <input
              type="number"
              min="0"
              max={endTime - 0.1}
              step="0.1"
              value={startTime}
              onChange={(e) => handleStartTimeChange(parseFloat(e.target.value))}
              className="w-20 px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* End Time */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">종료 시간</label>
            <span className="text-sm font-semibold text-blue-600">
              {formatTime(endTime)}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min={startTime + 0.1}
              max="300"
              step="0.1"
              value={endTime}
              onChange={(e) => handleEndTimeChange(parseFloat(e.target.value))}
              className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            />
            <input
              type="number"
              min={startTime + 0.1}
              max="300"
              step="0.1"
              value={endTime}
              onChange={(e) => handleEndTimeChange(parseFloat(e.target.value))}
              className="w-20 px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Duration Display */}
        <div className="bg-white border border-gray-300 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">지속 시간</span>
            <span className="text-lg font-bold text-gray-900">
              {duration.toFixed(1)}초
            </span>
          </div>
        </div>
      </div>

      {/* Transition Effect Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-3">
          전환 효과
        </label>
        <div className="grid grid-cols-3 gap-3">
          {TRANSITION_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => handleTransitionChange(option.value)}
              className={`p-4 border-2 rounded-lg text-center transition-all ${
                selectedTransition === option.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
              }`}
            >
              <div className="text-3xl mb-2">{option.icon}</div>
              <div className="font-medium text-gray-900 text-sm">{option.label}</div>
              <div className="text-xs text-gray-600 mt-1">{option.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* BGM Settings */}
      <div className="border-t border-gray-200 pt-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-semibold text-gray-900">BGM 설정</h4>
          <button
            onClick={() => handleBGMChange({ enabled: !bgm.enabled })}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              bgm.enabled ? 'bg-blue-600' : 'bg-gray-300'
            }`}
            aria-label="BGM 활성화/비활성화"
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                bgm.enabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {bgm.enabled && (
          <div className="space-y-4">
            {/* Volume */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">볼륨</label>
                <span className="text-sm font-semibold text-blue-600">
                  {Math.round(bgm.volume * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={bgm.volume}
                onChange={(e) => handleBGMChange({ volume: parseFloat(e.target.value) })}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
            </div>

            {/* Fade In */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">페이드 인</label>
                <span className="text-sm font-semibold text-blue-600">
                  {bgm.fade_in_duration.toFixed(1)}초
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="5"
                step="0.1"
                value={bgm.fade_in_duration}
                onChange={(e) =>
                  handleBGMChange({ fade_in_duration: parseFloat(e.target.value) })
                }
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
            </div>

            {/* Fade Out */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">페이드 아웃</label>
                <span className="text-sm font-semibold text-blue-600">
                  {bgm.fade_out_duration.toFixed(1)}초
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="5"
                step="0.1"
                value={bgm.fade_out_duration}
                onChange={(e) =>
                  handleBGMChange({ fade_out_duration: parseFloat(e.target.value) })
                }
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
            </div>

            {/* Custom BGM File (Optional) */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs text-blue-800">
                💡 커스텀 BGM 파일 업로드는 향후 지원 예정입니다
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Custom Slider Styles */}
      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 18px;
          height: 18px;
          background: #3b82f6;
          cursor: pointer;
          border-radius: 50%;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .slider::-moz-range-thumb {
          width: 18px;
          height: 18px;
          background: #3b82f6;
          cursor: pointer;
          border-radius: 50%;
          border: none;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .slider::-webkit-slider-thumb:hover {
          background: #2563eb;
        }

        .slider::-moz-range-thumb:hover {
          background: #2563eb;
        }
      `}</style>
    </div>
  );
}
