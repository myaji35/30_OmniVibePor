'use client'

import { StoryboardBlock, getTransitionIcon } from '@/lib/blocks/storyboard-types'
import { Image, Clock, Tag } from 'lucide-react'

interface StoryboardBlockCardProps {
  block: StoryboardBlock
  isSelected: boolean
  onSelect: () => void
  onUpdate: (updates: Partial<StoryboardBlock>) => void
}

export default function StoryboardBlockCard({
  block,
  isSelected,
  onSelect,
  onUpdate
}: StoryboardBlockCardProps) {
  const duration = block.end_time - block.start_time

  return (
    <div
      className={`
        relative rounded-lg overflow-hidden cursor-pointer
        transition-all duration-200
        ${isSelected
          ? 'ring-2 ring-purple-500 shadow-lg shadow-purple-500/30'
          : 'hover:shadow-md hover:ring-1 hover:ring-gray-600'
        }
      `}
      onClick={onSelect}
    >
      {/* 배경 이미지 미리보기 */}
      <div className="relative h-40 bg-gray-800">
        {block.background_url ? (
          <img
            src={block.background_url}
            alt={block.script}
            className="w-full h-full object-cover"
          />
        ) : block.background_color ? (
          <div
            className="w-full h-full"
            style={{ backgroundColor: block.background_color }}
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-gray-500">
            <Image className="w-8 h-8 mb-2" />
            <span className="text-xs">배경 없음</span>
          </div>
        )}

        {/* 블록 번호 */}
        <div className="absolute top-2 left-2 bg-black/80 text-white px-2 py-1 rounded text-xs font-semibold backdrop-blur-sm">
          #{block.order + 1}
        </div>

        {/* 전환 효과 아이콘 */}
        <div className="absolute top-2 right-2 bg-black/80 text-white px-2 py-1 rounded text-xs backdrop-blur-sm">
          {getTransitionIcon(block.transition_effect)}
        </div>

        {/* 배경 타입 뱃지 */}
        {block.background_url && (
          <div className="absolute bottom-2 left-2">
            {getBackgroundTypeBadge(block.background_type)}
          </div>
        )}
      </div>

      {/* 스크립트 */}
      <div className="p-3 bg-gray-900">
        <p className="text-sm text-gray-300 line-clamp-2 leading-relaxed mb-2">
          {block.script}
        </p>

        {/* 키워드 태그 */}
        {block.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {block.keywords.slice(0, 3).map(keyword => (
              <span
                key={keyword}
                className="inline-flex items-center gap-1 text-xs bg-purple-600/30 text-purple-300 px-2 py-0.5 rounded"
              >
                <Tag className="w-3 h-3" />
                {keyword}
              </span>
            ))}
            {block.keywords.length > 3 && (
              <span className="text-xs text-gray-500">
                +{block.keywords.length - 3}
              </span>
            )}
          </div>
        )}

        {/* 시간 및 자막 프리셋 */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{block.start_time.toFixed(1)}s - {block.end_time.toFixed(1)}s</span>
          </div>
          <span className="text-gray-400">
            {duration.toFixed(1)}s
          </span>
        </div>

        {/* 자막 프리셋 */}
        <div className="mt-2 text-xs">
          <span className="px-2 py-0.5 bg-blue-600/30 text-blue-300 rounded">
            {getSubtitlePresetLabel(block.subtitle_preset)}
          </span>
        </div>
      </div>
    </div>
  )
}

function getBackgroundTypeBadge(type: StoryboardBlock['background_type']) {
  switch (type) {
    case 'uploaded':
      return (
        <span className="text-xs bg-green-600/80 text-white px-2 py-0.5 rounded backdrop-blur-sm">
          업로드
        </span>
      )
    case 'ai_generated':
      return (
        <span className="text-xs bg-purple-600/80 text-white px-2 py-0.5 rounded backdrop-blur-sm">
          AI 생성
        </span>
      )
    case 'stock':
      return (
        <span className="text-xs bg-blue-600/80 text-white px-2 py-0.5 rounded backdrop-blur-sm">
          스톡
        </span>
      )
    case 'solid_color':
      return (
        <span className="text-xs bg-gray-600/80 text-white px-2 py-0.5 rounded backdrop-blur-sm">
          단색
        </span>
      )
    default:
      return null
  }
}

function getSubtitlePresetLabel(preset: StoryboardBlock['subtitle_preset']) {
  switch (preset) {
    case 'normal':
      return '일반'
    case 'bold':
      return '굵게'
    case 'minimal':
      return '미니멀'
    case 'news':
      return '뉴스'
    default:
      return preset
  }
}
