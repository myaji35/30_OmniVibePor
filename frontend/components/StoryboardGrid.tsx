'use client'

import { StoryboardBlock } from '@/lib/blocks/storyboard-types'
import StoryboardBlockCard from './StoryboardBlockCard'
import { Grid3x3, List } from 'lucide-react'
import { useState } from 'react'

interface StoryboardGridProps {
  blocks: StoryboardBlock[]
  selectedBlockId: string | null
  onBlockSelect: (block: StoryboardBlock) => void
  onBlockUpdate: (blockId: string, updates: Partial<StoryboardBlock>) => void
}

export default function StoryboardGrid({
  blocks,
  selectedBlockId,
  onBlockSelect,
  onBlockUpdate
}: StoryboardGridProps) {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  if (blocks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <Grid3x3 className="w-16 h-16 mb-4 opacity-50" />
        <p className="text-lg font-medium">콘티 블록이 없습니다</p>
        <p className="text-sm mt-2">AI로 콘티 블록을 자동 생성해보세요</p>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <div>
          <h2 className="text-lg font-semibold">콘티 블록</h2>
          <p className="text-sm text-gray-400 mt-0.5">
            총 {blocks.length}개 블록 • {getTotalDuration(blocks)}초
          </p>
        </div>

        {/* 뷰 모드 토글 */}
        <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-1.5 rounded transition-colors ${
              viewMode === 'grid'
                ? 'bg-purple-600 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
            title="그리드 뷰"
          >
            <Grid3x3 className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-1.5 rounded transition-colors ${
              viewMode === 'list'
                ? 'bg-purple-600 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
            title="리스트 뷰"
          >
            <List className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 그리드/리스트 */}
      <div className="flex-1 overflow-y-auto p-4">
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {blocks.map(block => (
              <StoryboardBlockCard
                key={block.id}
                block={block}
                isSelected={selectedBlockId === block.id}
                onSelect={() => onBlockSelect(block)}
                onUpdate={(updates) => onBlockUpdate(block.id, updates)}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {blocks.map(block => (
              <div
                key={block.id}
                className={`flex items-center gap-4 p-4 rounded-lg border cursor-pointer transition-all ${
                  selectedBlockId === block.id
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-gray-800 bg-gray-900 hover:border-gray-700'
                }`}
                onClick={() => onBlockSelect(block)}
              >
                {/* 블록 번호 */}
                <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gray-800 flex items-center justify-center font-semibold text-lg">
                  #{block.order + 1}
                </div>

                {/* 배경 미리보기 */}
                <div className="flex-shrink-0 w-24 h-16 rounded overflow-hidden bg-gray-800">
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
                    <div className="w-full h-full flex items-center justify-center text-gray-600 text-xs">
                      없음
                    </div>
                  )}
                </div>

                {/* 스크립트 */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-300 line-clamp-2">
                    {block.script}
                  </p>
                  <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                    <span>{block.start_time.toFixed(1)}s - {block.end_time.toFixed(1)}s</span>
                    <span>•</span>
                    <span>{block.transition_effect}</span>
                  </div>
                </div>

                {/* 키워드 */}
                {block.keywords.length > 0 && (
                  <div className="flex-shrink-0 flex flex-wrap gap-1 max-w-xs">
                    {block.keywords.slice(0, 2).map(keyword => (
                      <span
                        key={keyword}
                        className="px-2 py-0.5 bg-purple-600/30 text-purple-300 rounded text-xs"
                      >
                        {keyword}
                      </span>
                    ))}
                    {block.keywords.length > 2 && (
                      <span className="text-xs text-gray-500">
                        +{block.keywords.length - 2}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function getTotalDuration(blocks: StoryboardBlock[]): number {
  if (blocks.length === 0) return 0
  const lastBlock = blocks[blocks.length - 1]
  return Math.ceil(lastBlock.end_time)
}
