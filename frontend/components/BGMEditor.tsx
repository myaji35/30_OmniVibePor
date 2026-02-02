"use client";

/**
 * BGMEditor - BGM 볼륨, 페이드, 덕킹 조정 컴포넌트
 *
 * 기능:
 * - BGM 파일 업로드 (드래그 앤 드롭 + 파일 선택)
 * - 볼륨 슬라이더 (0% ~ 100%)
 * - 페이드 인/아웃 슬라이더 (0 ~ 10초)
 * - 시작/종료 시간 설정
 * - 루프 토글
 * - 오디오 덕킹 토글 + 레벨 슬라이더
 * - BGM 미리듣기 플레이어
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';

// ========================
// Type Definitions
// ========================

export interface BGMSettings {
  bgm_file_path?: string;
  volume: number;  // 0.0-1.0
  fade_in_duration: number;  // 초
  fade_out_duration: number;  // 초
  start_time: number;
  end_time?: number;
  loop: boolean;
  ducking_enabled: boolean;
  ducking_level: number;  // 0.1-0.5
}

export interface BGMEditorProps {
  projectId: string;
  initialSettings?: BGMSettings;
  onSettingsChange?: (settings: BGMSettings) => void;
}

// ========================
// BGMEditor Component
// ========================

export default function BGMEditor({
  projectId,
  initialSettings,
  onSettingsChange,
}: BGMEditorProps) {
  // State
  const [settings, setSettings] = useState<BGMSettings>(
    initialSettings || {
      volume: 0.5,
      fade_in_duration: 2,
      fade_out_duration: 2,
      start_time: 0,
      loop: false,
      ducking_enabled: true,
      ducking_level: 0.3,
    }
  );

  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bgmFileName, setBgmFileName] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Debounce settings changes (1초)
  const debouncedSettingsChange = useCallback((newSettings: BGMSettings) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      onSettingsChange?.(newSettings);
      // API 호출: PATCH /api/v1/projects/{projectId}/bgm
      updateBGMSettings(newSettings);
    }, 1000);
  }, [projectId, onSettingsChange]);

  // Update settings
  const updateSettings = useCallback((partial: Partial<BGMSettings>) => {
    setSettings((prev) => {
      const newSettings = { ...prev, ...partial };
      debouncedSettingsChange(newSettings);
      return newSettings;
    });
  }, [debouncedSettingsChange]);

  // API: Update BGM settings
  const updateBGMSettings = async (settings: BGMSettings) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/projects/${projectId}/bgm`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(settings),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update BGM settings');
      }
    } catch (err) {
      console.error('Failed to update BGM settings:', err);
    }
  };

  // API: Load BGM settings
  useEffect(() => {
    const loadBGMSettings = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/v1/projects/${projectId}/bgm`
        );

        if (response.ok) {
          const data = await response.json();
          setSettings(data);
          if (data.bgm_file_path) {
            const fileName = data.bgm_file_path.split('/').pop();
            setBgmFileName(fileName);
          }
        }
      } catch (err) {
        console.error('Failed to load BGM settings:', err);
      }
    };

    loadBGMSettings();
  }, [projectId]);

  // Drag & Drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      await handleFileUpload(files[0]);
    }
  };

  // File validation
  const validateFile = (file: File): boolean => {
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/aac', 'audio/flac', 'audio/mp3'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|aac|flac)$/i)) {
      setError('지원하지 않는 파일 형식입니다. (MP3, WAV, AAC, FLAC만 가능)');
      return false;
    }

    if (file.size > maxSize) {
      setError('파일 크기가 10MB를 초과합니다.');
      return false;
    }

    return true;
  };

  // File upload handler
  const handleFileUpload = async (file: File) => {
    if (!validateFile(file)) return;

    setError(null);
    setIsUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const xhr = new XMLHttpRequest();

      // Upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = (e.loaded / e.total) * 100;
          setUploadProgress(progress);
        }
      });

      // Upload complete
      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const data = JSON.parse(xhr.responseText);
          updateSettings({ bgm_file_path: data.file_path });
          setBgmFileName(file.name);
          setIsUploading(false);
          setUploadProgress(100);
        } else {
          throw new Error('Upload failed');
        }
      });

      // Upload error
      xhr.addEventListener('error', () => {
        setError('업로드 중 오류가 발생했습니다.');
        setIsUploading(false);
      });

      xhr.open('POST', `http://localhost:8000/api/v1/projects/${projectId}/bgm/upload`);
      xhr.send(formData);
    } catch (err) {
      setError('업로드 중 오류가 발생했습니다.');
      setIsUploading(false);
    }
  };

  // File input click
  const handleFileInputClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  // Remove BGM
  const handleRemoveBGM = async () => {
    try {
      await fetch(`http://localhost:8000/api/v1/projects/${projectId}/bgm`, {
        method: 'DELETE',
      });

      updateSettings({ bgm_file_path: undefined });
      setBgmFileName(null);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
      }
    } catch (err) {
      console.error('Failed to remove BGM:', err);
    }
  };

  // Volume control with live preview
  const handleVolumeChange = (value: number) => {
    updateSettings({ volume: value });
    if (audioRef.current) {
      audioRef.current.volume = value;
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-900">🎵 BGM 설정</h3>
        <p className="text-sm text-gray-600 mt-1">
          배경음악을 업로드하고 볼륨, 페이드, 덕킹을 조정하세요
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
          {error}
        </div>
      )}

      {/* File Upload Area */}
      {!settings.bgm_file_path && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleFileInputClick}
          className={`mb-6 border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
            isDragging
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/mpeg,audio/wav,audio/aac,audio/flac,.mp3,.wav,.aac,.flac"
            onChange={handleFileInputChange}
            className="hidden"
          />

          {isUploading ? (
            <div>
              <div className="text-4xl mb-3">📤</div>
              <p className="text-gray-700 font-medium mb-2">업로드 중...</p>
              <div className="w-full bg-gray-200 rounded-full h-2 max-w-xs mx-auto">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 mt-2">{uploadProgress.toFixed(0)}%</p>
            </div>
          ) : (
            <div>
              <div className="text-4xl mb-3">🎵</div>
              <p className="text-gray-700 font-medium mb-1">
                BGM 파일을 드래그하거나 클릭하여 선택
              </p>
              <p className="text-sm text-gray-500">MP3, WAV, AAC, FLAC (최대 10MB)</p>
            </div>
          )}
        </div>
      )}

      {/* BGM File Info */}
      {settings.bgm_file_path && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-green-500 rounded-full p-2">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" />
                </svg>
              </div>
              <div>
                <p className="font-medium text-green-900">{bgmFileName}</p>
                <p className="text-xs text-green-700">BGM 업로드 완료</p>
              </div>
            </div>
            <button
              onClick={handleRemoveBGM}
              className="text-red-600 hover:text-red-700 text-sm font-medium"
            >
              제거
            </button>
          </div>
        </div>
      )}

      {/* Volume Slider */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
            </svg>
            볼륨
          </label>
          <span className="text-sm font-semibold text-blue-600">
            {Math.round(settings.volume * 100)}%
          </span>
        </div>
        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={settings.volume}
          onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        />
      </div>

      {/* Fade In Slider */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
            페이드 인
          </label>
          <span className="text-sm font-semibold text-blue-600">
            {settings.fade_in_duration.toFixed(1)}초
          </span>
        </div>
        <input
          type="range"
          min="0"
          max="10"
          step="0.1"
          value={settings.fade_in_duration}
          onChange={(e) => updateSettings({ fade_in_duration: parseFloat(e.target.value) })}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        />
      </div>

      {/* Fade Out Slider */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
            </svg>
            페이드 아웃
          </label>
          <span className="text-sm font-semibold text-blue-600">
            {settings.fade_out_duration.toFixed(1)}초
          </span>
        </div>
        <input
          type="range"
          min="0"
          max="10"
          step="0.1"
          value={settings.fade_out_duration}
          onChange={(e) => updateSettings({ fade_out_duration: parseFloat(e.target.value) })}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        />
      </div>

      {/* Advanced Settings Toggle */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="w-full mb-4 py-2 px-4 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium text-gray-700 flex items-center justify-between transition-colors"
      >
        <span>고급 설정</span>
        <svg
          className={`w-5 h-5 transition-transform ${showAdvanced ? 'rotate-180' : ''}`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>

      {/* Advanced Settings */}
      {showAdvanced && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-4">
          {/* Start Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              시작 시간 (초)
            </label>
            <input
              type="number"
              min="0"
              step="0.1"
              value={settings.start_time}
              onChange={(e) => updateSettings({ start_time: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* End Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              종료 시간 (초, 선택사항)
            </label>
            <input
              type="number"
              min="0"
              step="0.1"
              value={settings.end_time || ''}
              onChange={(e) =>
                updateSettings({ end_time: e.target.value ? parseFloat(e.target.value) : undefined })
              }
              placeholder="전체 길이"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Loop Toggle */}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-700">루프 재생</label>
            <button
              onClick={() => updateSettings({ loop: !settings.loop })}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.loop ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.loop ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Ducking Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700">오디오 덕킹</label>
              <p className="text-xs text-gray-500">음성 재생 시 BGM 볼륨 자동 감소</p>
            </div>
            <button
              onClick={() => updateSettings({ ducking_enabled: !settings.ducking_enabled })}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.ducking_enabled ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.ducking_enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Ducking Level Slider */}
          {settings.ducking_enabled && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">덕킹 레벨</label>
                <span className="text-sm font-semibold text-blue-600">
                  {Math.round(settings.ducking_level * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.5"
                step="0.05"
                value={settings.ducking_level}
                onChange={(e) => updateSettings({ ducking_level: parseFloat(e.target.value) })}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <p className="text-xs text-gray-500 mt-1">
                음성 재생 중 BGM 볼륨이 이 레벨로 감소됩니다
              </p>
            </div>
          )}
        </div>
      )}

      {/* Audio Preview Player */}
      {settings.bgm_file_path && (
        <div className="bg-gradient-to-br from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
          <p className="text-sm font-medium text-purple-900 mb-3">🎧 BGM 미리듣기</p>
          <audio
            ref={audioRef}
            controls
            className="w-full"
            src={`http://localhost:8000${settings.bgm_file_path}`}
          >
            Your browser does not support the audio element.
          </audio>
        </div>
      )}

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
