"use client";

/**
 * SubtitleEditor - 자막 스타일 편집 컴포넌트
 *
 * 기능:
 * - 폰트, 배경, 위치, 정렬, 아웃라인, 그림자 설정
 * - 실시간 미리보기
 * - 플랫폼별 프리셋 (YouTube, TikTok, Instagram, Minimal)
 * - API 통합 (GET/PATCH/POST)
 * - Debounce 자동 저장
 */

import React, { useState, useEffect, useCallback } from 'react';
import debounce from 'lodash.debounce';
import {
  SubtitleStyle,
  SubtitleEditorProps,
  SubtitleAPIResponse,
  SubtitlePreviewResponse,
} from '@/lib/types/subtitle';
import {
  DEFAULT_SUBTITLE_STYLE,
  SUBTITLE_PRESETS,
  FONT_FAMILIES,
  POSITION_OPTIONS,
  ALIGNMENT_OPTIONS,
} from '@/lib/constants/subtitlePresets';

export default function SubtitleEditor({
  projectId,
  initialStyle,
  onStyleChange,
  onPreviewRequest,
}: SubtitleEditorProps) {
  // State
  const [style, setStyle] = useState<SubtitleStyle>(
    initialStyle || DEFAULT_SUBTITLE_STYLE
  );
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // API Base URL
  const API_BASE_URL = 'http://localhost:8000/api/v1';

  // Load existing style on mount
  useEffect(() => {
    loadSubtitleStyle();
  }, [projectId]);

  // Debounced save function
  const debouncedSave = useCallback(
    debounce(async (newStyle: SubtitleStyle) => {
      await saveSubtitleStyle(newStyle);
    }, 1000),
    [projectId]
  );

  // Load subtitle style from API
  const loadSubtitleStyle = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/projects/${projectId}/subtitles`
      );

      if (!response.ok) {
        // If 404, use default style
        if (response.status === 404) {
          console.log('No existing subtitle style, using default');
          return;
        }
        throw new Error('Failed to load subtitle style');
      }

      const data: SubtitleAPIResponse = await response.json();
      setStyle(data.style);
      if (onStyleChange) {
        onStyleChange(data.style);
      }
    } catch (err: any) {
      console.error('Failed to load subtitle style:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Save subtitle style to API (debounced)
  const saveSubtitleStyle = async (newStyle: SubtitleStyle) => {
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/projects/${projectId}/subtitles`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ style: newStyle }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to save subtitle style');
      }

      const data: SubtitleAPIResponse = await response.json();
      setSuccessMessage('저장되었습니다');
      setTimeout(() => setSuccessMessage(null), 2000);
    } catch (err: any) {
      console.error('Failed to save subtitle style:', err);
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  // Generate preview
  const generatePreview = async () => {
    setIsGeneratingPreview(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/projects/${projectId}/subtitles/preview`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ style }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to generate preview');
      }

      const data: SubtitlePreviewResponse = await response.json();
      setPreviewUrl(data.preview_url);

      if (onPreviewRequest) {
        onPreviewRequest();
      }
    } catch (err: any) {
      console.error('Failed to generate preview:', err);
      setError(err.message);
    } finally {
      setIsGeneratingPreview(false);
    }
  };

  // Handle style change
  const handleStyleChange = (updates: Partial<SubtitleStyle>) => {
    const newStyle = { ...style, ...updates };
    setStyle(newStyle);
    debouncedSave(newStyle);
    if (onStyleChange) {
      onStyleChange(newStyle);
    }
  };

  // Apply preset
  const applyPreset = (presetKey: string) => {
    const preset = SUBTITLE_PRESETS[presetKey];
    if (preset) {
      setStyle(preset.style);
      saveSubtitleStyle(preset.style); // Immediate save for presets
      if (onStyleChange) {
        onStyleChange(preset.style);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col lg:flex-row gap-6 p-6">
      {/* Left Panel - Controls */}
      <div className="lg:w-1/2 space-y-6 overflow-y-auto">
        {/* Header */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900">자막 에디터</h2>
          <p className="text-sm text-gray-600 mt-1">
            자막 스타일을 실시간으로 조정하세요
          </p>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}
        {successMessage && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-sm text-green-800">{successMessage}</p>
          </div>
        )}
        {isSaving && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">저장 중...</p>
          </div>
        )}

        {/* Presets */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            프리셋 선택
          </label>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(SUBTITLE_PRESETS).map(([key, preset]) => (
              <button
                key={key}
                onClick={() => applyPreset(key)}
                className="p-4 border border-gray-300 rounded-lg text-left hover:border-blue-500 hover:bg-blue-50 transition-all"
              >
                <div className="font-medium text-gray-900">{preset.name}</div>
                <div className="text-xs text-gray-600 mt-1">
                  {preset.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Font Settings */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            폰트 설정
          </h3>
          <div className="space-y-4">
            {/* Font Family */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                폰트
              </label>
              <select
                value={style.font_family}
                onChange={(e) =>
                  handleStyleChange({ font_family: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {FONT_FAMILIES.map((font) => (
                  <option key={font.value} value={font.value}>
                    {font.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Font Size */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                크기: {style.font_size}px
              </label>
              <input
                type="range"
                min="24"
                max="72"
                value={style.font_size}
                onChange={(e) =>
                  handleStyleChange({ font_size: parseInt(e.target.value) })
                }
                className="w-full"
              />
            </div>

            {/* Font Color */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                색상
              </label>
              <div className="flex gap-2 items-center">
                <input
                  type="color"
                  value={style.font_color}
                  onChange={(e) =>
                    handleStyleChange({ font_color: e.target.value })
                  }
                  className="h-10 w-20 border border-gray-300 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={style.font_color}
                  onChange={(e) =>
                    handleStyleChange({ font_color: e.target.value })
                  }
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="#FFFFFF"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Background Settings */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            배경 설정
          </h3>
          <div className="space-y-4">
            {/* Background Color */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                색상
              </label>
              <div className="flex gap-2 items-center">
                <input
                  type="color"
                  value={style.background_color}
                  onChange={(e) =>
                    handleStyleChange({ background_color: e.target.value })
                  }
                  className="h-10 w-20 border border-gray-300 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={style.background_color}
                  onChange={(e) =>
                    handleStyleChange({ background_color: e.target.value })
                  }
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="#000000"
                />
              </div>
            </div>

            {/* Background Opacity */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                투명도: {(style.background_opacity * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={style.background_opacity}
                onChange={(e) =>
                  handleStyleChange({
                    background_opacity: parseFloat(e.target.value),
                  })
                }
                className="w-full"
              />
            </div>
          </div>
        </div>

        {/* Position & Alignment */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            위치 및 정렬
          </h3>
          <div className="space-y-4">
            {/* Position */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                위치
              </label>
              <div className="grid grid-cols-3 gap-2">
                {POSITION_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleStyleChange({ position: option.value })}
                    className={`px-4 py-2 border rounded-lg transition-all ${
                      style.position === option.value
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Vertical Offset */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                수직 오프셋: {style.vertical_offset}px
              </label>
              <input
                type="range"
                min="0"
                max="200"
                value={style.vertical_offset}
                onChange={(e) =>
                  handleStyleChange({
                    vertical_offset: parseInt(e.target.value),
                  })
                }
                className="w-full"
              />
            </div>

            {/* Alignment */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                정렬
              </label>
              <div className="grid grid-cols-3 gap-2">
                {ALIGNMENT_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() =>
                      handleStyleChange({ alignment: option.value })
                    }
                    className={`px-4 py-2 border rounded-lg transition-all ${
                      style.alignment === option.value
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Outline Settings */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            아웃라인 설정
          </h3>
          <div className="space-y-4">
            {/* Outline Width */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                두께: {style.outline_width}px
              </label>
              <input
                type="range"
                min="0"
                max="8"
                value={style.outline_width}
                onChange={(e) =>
                  handleStyleChange({
                    outline_width: parseInt(e.target.value),
                  })
                }
                className="w-full"
              />
            </div>

            {/* Outline Color */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                색상
              </label>
              <div className="flex gap-2 items-center">
                <input
                  type="color"
                  value={style.outline_color}
                  onChange={(e) =>
                    handleStyleChange({ outline_color: e.target.value })
                  }
                  className="h-10 w-20 border border-gray-300 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={style.outline_color}
                  onChange={(e) =>
                    handleStyleChange({ outline_color: e.target.value })
                  }
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="#000000"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Shadow Settings */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            그림자 설정
          </h3>
          <div className="space-y-4">
            {/* Shadow Enabled */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="shadow-enabled"
                checked={style.shadow_enabled}
                onChange={(e) =>
                  handleStyleChange({ shadow_enabled: e.target.checked })
                }
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label
                htmlFor="shadow-enabled"
                className="text-sm font-medium text-gray-700"
              >
                그림자 활성화
              </label>
            </div>

            {/* Shadow Offset X */}
            {style.shadow_enabled && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  X 오프셋: {style.shadow_offset_x}px
                </label>
                <input
                  type="range"
                  min="-10"
                  max="10"
                  value={style.shadow_offset_x}
                  onChange={(e) =>
                    handleStyleChange({
                      shadow_offset_x: parseInt(e.target.value),
                    })
                  }
                  className="w-full"
                />
              </div>
            )}

            {/* Shadow Offset Y */}
            {style.shadow_enabled && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Y 오프셋: {style.shadow_offset_y}px
                </label>
                <input
                  type="range"
                  min="-10"
                  max="10"
                  value={style.shadow_offset_y}
                  onChange={(e) =>
                    handleStyleChange({
                      shadow_offset_y: parseInt(e.target.value),
                    })
                  }
                  className="w-full"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Panel - Preview */}
      <div className="lg:w-1/2 space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            실시간 미리보기
          </h3>

          {/* Preview Container */}
          <div
            className="relative w-full bg-gray-900 rounded-lg overflow-hidden"
            style={{ aspectRatio: '16/9' }}
          >
            {/* Background Image/Video Placeholder */}
            <div className="absolute inset-0 bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
              <span className="text-gray-600 text-sm">영상 배경</span>
            </div>

            {/* Subtitle Preview */}
            <div
              className="absolute inset-0 flex items-center justify-center"
              style={{
                alignItems:
                  style.position === 'top'
                    ? 'flex-start'
                    : style.position === 'bottom'
                    ? 'flex-end'
                    : 'center',
                paddingTop:
                  style.position === 'top' ? `${style.vertical_offset}px` : 0,
                paddingBottom:
                  style.position === 'bottom'
                    ? `${style.vertical_offset}px`
                    : 0,
              }}
            >
              <div
                className="px-4 py-2 max-w-[90%]"
                style={{
                  backgroundColor: `${style.background_color}${Math.round(
                    style.background_opacity * 255
                  )
                    .toString(16)
                    .padStart(2, '0')}`,
                  textAlign: style.alignment,
                }}
              >
                <p
                  style={{
                    fontFamily: style.font_family,
                    fontSize: `${style.font_size * 0.5}px`, // Scale down for preview
                    color: style.font_color,
                    textShadow: style.shadow_enabled
                      ? `${style.shadow_offset_x}px ${style.shadow_offset_y}px 4px rgba(0,0,0,0.5)`
                      : 'none',
                    WebkitTextStroke: `${style.outline_width * 0.5}px ${
                      style.outline_color
                    }`,
                    margin: 0,
                  }}
                >
                  이것은 자막 미리보기입니다
                </p>
              </div>
            </div>
          </div>

          {/* Preview Actions */}
          <div className="mt-4 space-y-2">
            <button
              onClick={generatePreview}
              disabled={isGeneratingPreview}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {isGeneratingPreview ? '생성 중...' : '미리보기 영상 생성'}
            </button>

            {previewUrl && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-sm text-green-800 mb-2">
                  미리보기가 생성되었습니다
                </p>
                <a
                  href={previewUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline text-sm"
                >
                  새 탭에서 보기 →
                </a>
              </div>
            )}
          </div>

          {/* Style Info */}
          <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">현재 스타일</h4>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
              <div>폰트: {style.font_family}</div>
              <div>크기: {style.font_size}px</div>
              <div>위치: {style.position}</div>
              <div>정렬: {style.alignment}</div>
              <div>
                배경 투명도: {(style.background_opacity * 100).toFixed(0)}%
              </div>
              <div>아웃라인: {style.outline_width}px</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
