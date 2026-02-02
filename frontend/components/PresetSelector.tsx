"use client";

/**
 * PresetSelector - 프리셋 선택 UI 컴포넌트
 *
 * 기능:
 * - 플랫폼별 프리셋 목록 표시 (YouTube, Instagram, TikTok)
 * - 커스텀 프리셋 목록 표시
 * - 프리셋 카드 (썸네일, 이름, 설명)
 * - 프리셋 클릭 시 미리보기
 * - "적용" 버튼
 * - 검색 기능 (프리셋 이름)
 * - 필터 기능 (플랫폼별, 즐겨찾기)
 */

import React, { useState, useEffect } from 'react';
import { Search, Filter, Heart, Check, Youtube, Instagram, Music } from 'lucide-react';

// ==================== Types ====================

interface PlatformPreset {
  platform: string;
  name: string;
  resolution: { width: number; height: number };
  aspect_ratio: string;
  subtitle_style: any;
  bgm_settings: any;
  thumbnail_url?: string;
}

interface CustomPreset {
  preset_id: string;
  name: string;
  description?: string;
  subtitle_style: any;
  bgm_settings: any;
  video_settings: any;
  is_favorite: boolean;
  usage_count: number;
  created_at: string;
}

interface PresetSelectorProps {
  projectId: string;
  onPresetSelected?: (presetId: string, type: 'platform' | 'custom') => void;
  onPresetApplied?: () => void;
}

type TabType = 'platform' | 'custom';
type FilterType = 'all' | 'youtube' | 'instagram' | 'tiktok' | 'favorite';

// ==================== Helper Functions ====================

function getPlatformIcon(platform: string): React.ReactNode {
  const iconClass = "w-8 h-8";

  switch (platform.toLowerCase()) {
    case 'youtube':
      return <Youtube className={iconClass} />;
    case 'instagram':
      return <Instagram className={iconClass} />;
    case 'tiktok':
      return <Music className={iconClass} />;
    default:
      return <div className="w-8 h-8 bg-gray-300 rounded" />;
  }
}

function getPlatformColor(platform: string): string {
  switch (platform.toLowerCase()) {
    case 'youtube':
      return 'bg-red-500';
    case 'instagram':
      return 'bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500';
    case 'tiktok':
      return 'bg-black';
    default:
      return 'bg-gray-500';
  }
}

function getPlatformName(platform: string): string {
  switch (platform.toLowerCase()) {
    case 'youtube':
      return 'YouTube';
    case 'instagram':
      return 'Instagram';
    case 'tiktok':
      return 'TikTok';
    default:
      return platform;
  }
}

// ==================== Component ====================

export default function PresetSelector({
  projectId,
  onPresetSelected,
  onPresetApplied,
}: PresetSelectorProps) {
  // State
  const [activeTab, setActiveTab] = useState<TabType>('platform');
  const [platformPresets, setPlatformPresets] = useState<PlatformPreset[]>([]);
  const [customPresets, setCustomPresets] = useState<CustomPreset[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [selectedPreset, setSelectedPreset] = useState<{
    id: string;
    type: 'platform' | 'custom';
  } | null>(null);
  const [isApplying, setIsApplying] = useState(false);

  // Fetch presets on mount
  useEffect(() => {
    fetchPlatformPresets();
    fetchCustomPresets();
  }, []);

  // Fetch platform presets
  async function fetchPlatformPresets() {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/presets/platforms');

      if (!response.ok) {
        throw new Error(`Failed to fetch platform presets: ${response.statusText}`);
      }

      const data = await response.json();
      setPlatformPresets(data.presets || []);
    } catch (err: any) {
      setError(err.message);
      console.error('Failed to fetch platform presets:', err);
    } finally {
      setIsLoading(false);
    }
  }

  // Fetch custom presets
  async function fetchCustomPresets() {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/presets/custom');

      if (!response.ok) {
        throw new Error(`Failed to fetch custom presets: ${response.statusText}`);
      }

      const data = await response.json();
      setCustomPresets(data.presets || []);
    } catch (err: any) {
      setError(err.message);
      console.error('Failed to fetch custom presets:', err);
    } finally {
      setIsLoading(false);
    }
  }

  // Toggle favorite for custom preset
  async function toggleFavorite(presetId: string) {
    try {
      const preset = customPresets.find((p) => p.preset_id === presetId);
      if (!preset) return;

      const response = await fetch(
        `http://localhost:8000/api/v1/presets/custom/${presetId}/favorite`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            is_favorite: !preset.is_favorite,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to toggle favorite');
      }

      // Update local state
      setCustomPresets((prev) =>
        prev.map((p) =>
          p.preset_id === presetId ? { ...p, is_favorite: !p.is_favorite } : p
        )
      );
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
    }
  }

  // Apply preset
  async function applyPreset() {
    if (!selectedPreset) return;

    setIsApplying(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/projects/${projectId}/apply-preset`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            preset_id: selectedPreset.id,
            preset_type: selectedPreset.type,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to apply preset');
      }

      if (onPresetApplied) {
        onPresetApplied();
      }
    } catch (err: any) {
      setError(err.message);
      console.error('Failed to apply preset:', err);
    } finally {
      setIsApplying(false);
    }
  }

  // Filter presets based on search and filter type
  const filteredPlatformPresets = platformPresets.filter((preset) => {
    const matchesSearch = preset.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter =
      filterType === 'all' || filterType === preset.platform.toLowerCase();
    return matchesSearch && matchesFilter;
  });

  const filteredCustomPresets = customPresets.filter((preset) => {
    const matchesSearch = preset.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFavorite = filterType !== 'favorite' || preset.is_favorite;
    return matchesSearch && matchesFavorite;
  });

  // Handle preset selection
  function handleSelectPreset(presetId: string, type: 'platform' | 'custom') {
    setSelectedPreset({ id: presetId, type });

    if (onPresetSelected) {
      onPresetSelected(presetId, type);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">프리셋 선택</h2>
        <p className="text-gray-600 mt-1">플랫폼별 프리셋 또는 커스텀 프리셋을 선택하세요</p>
      </div>

      {/* Search & Filter */}
      <div className="flex gap-3">
        {/* Search */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="프리셋 검색..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Filter Dropdown */}
        <div className="relative">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as FilterType)}
            className="px-4 py-2 pr-10 border border-gray-300 rounded-lg appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
          >
            <option value="all">전체</option>
            {activeTab === 'platform' ? (
              <>
                <option value="youtube">YouTube</option>
                <option value="instagram">Instagram</option>
                <option value="tiktok">TikTok</option>
              </>
            ) : (
              <option value="favorite">즐겨찾기만</option>
            )}
          </select>
          <Filter className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none" />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => {
            setActiveTab('platform');
            setFilterType('all');
          }}
          className={`px-6 py-3 font-medium transition-colors relative ${
            activeTab === 'platform'
              ? 'text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          플랫폼 프리셋
          {activeTab === 'platform' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />
          )}
        </button>
        <button
          onClick={() => {
            setActiveTab('custom');
            setFilterType('all');
          }}
          className={`px-6 py-3 font-medium transition-colors relative ${
            activeTab === 'custom'
              ? 'text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          내 프리셋
          {activeTab === 'custom' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="bg-gray-100 rounded-lg h-48 animate-pulse" />
          ))}
        </div>
      )}

      {/* Platform Presets Grid */}
      {!isLoading && activeTab === 'platform' && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filteredPlatformPresets.map((preset, index) => {
            const isSelected =
              selectedPreset?.type === 'platform' &&
              selectedPreset.id === preset.platform;

            return (
              <div
                key={`${preset.platform}-${index}`}
                onClick={() => handleSelectPreset(preset.platform, 'platform')}
                className={`relative bg-white border-2 rounded-lg overflow-hidden cursor-pointer transition-all hover:shadow-lg ${
                  isSelected ? 'border-blue-500 shadow-lg' : 'border-gray-200'
                }`}
              >
                {/* Thumbnail */}
                <div
                  className={`h-32 flex items-center justify-center text-white ${getPlatformColor(
                    preset.platform
                  )}`}
                >
                  {getPlatformIcon(preset.platform)}
                </div>

                {/* Content */}
                <div className="p-4">
                  <h3 className="font-semibold text-gray-900 mb-1">{preset.name}</h3>
                  <p className="text-sm text-gray-600 mb-2">{preset.aspect_ratio}</p>
                  <p className="text-xs text-gray-500">
                    {preset.resolution.width} x {preset.resolution.height}
                  </p>
                </div>

                {/* Selected Badge */}
                {isSelected && (
                  <div className="absolute top-2 right-2 bg-blue-500 text-white rounded-full p-1">
                    <Check className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Custom Presets Grid */}
      {!isLoading && activeTab === 'custom' && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filteredCustomPresets.map((preset) => {
            const isSelected =
              selectedPreset?.type === 'custom' &&
              selectedPreset.id === preset.preset_id;

            return (
              <div
                key={preset.preset_id}
                onClick={() => handleSelectPreset(preset.preset_id, 'custom')}
                className={`relative bg-white border-2 rounded-lg overflow-hidden cursor-pointer transition-all hover:shadow-lg ${
                  isSelected ? 'border-blue-500 shadow-lg' : 'border-gray-200'
                }`}
              >
                {/* Thumbnail Placeholder */}
                <div className="h-32 bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
                  <div className="text-4xl font-bold text-blue-600">
                    {preset.name.charAt(0).toUpperCase()}
                  </div>
                </div>

                {/* Content */}
                <div className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-gray-900 flex-1 line-clamp-2">
                      {preset.name}
                    </h3>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleFavorite(preset.preset_id);
                      }}
                      className="ml-2 flex-shrink-0"
                    >
                      <Heart
                        className={`w-5 h-5 transition-colors ${
                          preset.is_favorite
                            ? 'fill-red-500 text-red-500'
                            : 'text-gray-400 hover:text-red-500'
                        }`}
                      />
                    </button>
                  </div>

                  {preset.description && (
                    <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                      {preset.description}
                    </p>
                  )}

                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>사용 {preset.usage_count}회</span>
                    <span>{new Date(preset.created_at).toLocaleDateString('ko-KR')}</span>
                  </div>
                </div>

                {/* Selected Badge */}
                {isSelected && (
                  <div className="absolute top-2 right-2 bg-blue-500 text-white rounded-full p-1">
                    <Check className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Empty State */}
      {!isLoading &&
        ((activeTab === 'platform' && filteredPlatformPresets.length === 0) ||
          (activeTab === 'custom' && filteredCustomPresets.length === 0)) && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">검색 결과가 없습니다</p>
            <p className="text-gray-400 text-sm mt-2">다른 검색어나 필터를 시도해보세요</p>
          </div>
        )}

      {/* Apply Button */}
      {selectedPreset && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 shadow-lg">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">선택한 프리셋</p>
              <p className="font-semibold text-gray-900">
                {selectedPreset.type === 'platform'
                  ? getPlatformName(selectedPreset.id)
                  : customPresets.find((p) => p.preset_id === selectedPreset.id)?.name}
              </p>
            </div>
            <button
              onClick={applyPreset}
              disabled={isApplying}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium transition-colors"
            >
              {isApplying ? '적용 중...' : '프리셋 적용'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
