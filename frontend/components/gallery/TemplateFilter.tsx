'use client'

import { RotateCcw } from 'lucide-react'

export interface FilterState {
  platforms: string[]
  tones: string[]
  duration: string | null
}

interface TemplateFilterProps {
  filters: FilterState
  onFiltersChange: (filters: FilterState) => void
}

const PLATFORM_OPTIONS = [
  { value: 'youtube', label: 'YouTube' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'tiktok', label: 'TikTok' },
]

const TONE_OPTIONS = [
  { value: 'professional', label: '전문적' },
  { value: 'emotional', label: '감성적' },
  { value: 'trendy', label: '트렌디' },
  { value: 'minimal', label: '미니멀' },
  { value: 'dynamic', label: '다이나믹' },
]

const DURATION_OPTIONS = [
  { value: 'short', label: '~30초' },
  { value: 'medium', label: '30~60초' },
  { value: 'long', label: '60초+' },
]

export default function TemplateFilter({ filters, onFiltersChange }: TemplateFilterProps) {
  const togglePlatform = (platform: string) => {
    const next = filters.platforms.includes(platform)
      ? filters.platforms.filter((p) => p !== platform)
      : [...filters.platforms, platform]
    onFiltersChange({ ...filters, platforms: next })
  }

  const toggleTone = (tone: string) => {
    const next = filters.tones.includes(tone)
      ? filters.tones.filter((t) => t !== tone)
      : [...filters.tones, tone]
    onFiltersChange({ ...filters, tones: next })
  }

  const setDuration = (duration: string) => {
    onFiltersChange({
      ...filters,
      duration: filters.duration === duration ? null : duration,
    })
  }

  const resetFilters = () => {
    onFiltersChange({ platforms: [], tones: [], duration: null })
  }

  const hasActiveFilters =
    filters.platforms.length > 0 || filters.tones.length > 0 || filters.duration !== null

  return (
    <div className="w-60 shrink-0 bg-white border border-[#DDDBDA] rounded-lg p-4 h-fit sticky top-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-[#16325C]">필터</h3>
        {hasActiveFilters && (
          <button
            onClick={resetFilters}
            className="flex items-center gap-1 text-[11px] text-[#00A1E0] hover:text-[#0090c7] transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            초기화
          </button>
        )}
      </div>

      {/* Platform Section */}
      <div className="mb-5">
        <h4 className="text-xs font-semibold text-[#706E6B] uppercase tracking-wider mb-2">
          플랫폼
        </h4>
        <div className="space-y-1.5">
          {PLATFORM_OPTIONS.map((option) => (
            <label
              key={option.value}
              className="flex items-center gap-2 cursor-pointer group"
            >
              <input
                type="checkbox"
                checked={filters.platforms.includes(option.value)}
                onChange={() => togglePlatform(option.value)}
                className="w-3.5 h-3.5 rounded border-[#DDDBDA] text-[#00A1E0] focus:ring-[#00A1E0] focus:ring-offset-0"
              />
              <span className="text-sm text-[#3E3E3C] group-hover:text-[#16325C] transition-colors">
                {option.label}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Tone Section */}
      <div className="mb-5">
        <h4 className="text-xs font-semibold text-[#706E6B] uppercase tracking-wider mb-2">
          분위기
        </h4>
        <div className="space-y-1.5">
          {TONE_OPTIONS.map((option) => (
            <label
              key={option.value}
              className="flex items-center gap-2 cursor-pointer group"
            >
              <input
                type="checkbox"
                checked={filters.tones.includes(option.value)}
                onChange={() => toggleTone(option.value)}
                className="w-3.5 h-3.5 rounded border-[#DDDBDA] text-[#00A1E0] focus:ring-[#00A1E0] focus:ring-offset-0"
              />
              <span className="text-sm text-[#3E3E3C] group-hover:text-[#16325C] transition-colors">
                {option.label}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Duration Section */}
      <div>
        <h4 className="text-xs font-semibold text-[#706E6B] uppercase tracking-wider mb-2">
          길이
        </h4>
        <div className="space-y-1.5">
          {DURATION_OPTIONS.map((option) => (
            <label
              key={option.value}
              className="flex items-center gap-2 cursor-pointer group"
            >
              <input
                type="radio"
                name="duration"
                checked={filters.duration === option.value}
                onChange={() => setDuration(option.value)}
                className="w-3.5 h-3.5 border-[#DDDBDA] text-[#00A1E0] focus:ring-[#00A1E0] focus:ring-offset-0"
              />
              <span className="text-sm text-[#3E3E3C] group-hover:text-[#16325C] transition-colors">
                {option.label}
              </span>
            </label>
          ))}
        </div>
      </div>
    </div>
  )
}
