'use client'

import { ScriptBlock, getBlockColor, getBlockIcon } from '@/lib/blocks/types'
import { useState } from 'react'
import { Edit2, Trash2, Copy, GripVertical, Scissors, Sparkles, Link2 } from 'lucide-react'

interface ScriptBlockCardProps {
    block: ScriptBlock
    isSelected: boolean
    onSelect: () => void
    onUpdate: (block: ScriptBlock) => void
    onDelete: () => void
    onDuplicate: () => void
    onSplit: () => void
    onAutoSplit: () => void
    onMerge: () => void
}

export default function ScriptBlockCard({
    block,
    isSelected,
    onSelect,
    onUpdate,
    onDelete,
    onDuplicate,
    onSplit,
    onAutoSplit,
    onMerge
}: ScriptBlockCardProps) {
    const [isEditing, setIsEditing] = useState(false)
    const [editedContent, setEditedContent] = useState(block.content)

    const handleSave = () => {
        onUpdate({ ...block, content: editedContent })
        setIsEditing(false)
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && e.metaKey) {
            handleSave()
        } else if (e.key === 'Escape') {
            setEditedContent(block.content)
            setIsEditing(false)
        }
    }

    const blockColor = getBlockColor(block.type)
    const blockIcon = getBlockIcon(block.type)

    return (
        <div
            onClick={onSelect}
            className={`
        group relative p-4 rounded-lg border-2 transition-all cursor-pointer
        ${isSelected
                    ? 'border-purple-500 bg-purple-500/10 shadow-lg shadow-purple-500/20'
                    : 'border-gray-700 bg-[#1a1a1a] hover:border-gray-600'
                }
      `}
        >
            {/* 드래그 핸들 */}
            <div className="absolute left-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing">
                <GripVertical className="w-4 h-4 text-gray-500" />
            </div>

            {/* 블록 헤더 */}
            <div className="flex items-center justify-between mb-2 ml-6">
                <div className="flex items-center gap-2">
                    <span className="text-lg">{blockIcon}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold text-white ${blockColor}`}>
                        {block.type.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-400">
                        {block.duration}초
                    </span>
                </div>

                {/* 액션 버튼 */}
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                        onClick={(e) => {
                            e.stopPropagation()
                            setIsEditing(true)
                        }}
                        className="p-1.5 hover:bg-gray-700 rounded transition-colors"
                        title="편집"
                    >
                        <Edit2 className="w-3.5 h-3.5 text-gray-400" />
                    </button>
                    <button
                        onClick={(e) => {
                            e.stopPropagation()
                            onDuplicate()
                        }}
                        className="p-1.5 hover:bg-gray-700 rounded transition-colors"
                        title="복제"
                    >
                        <Copy className="w-3.5 h-3.5 text-gray-400" />
                    </button>
                    <button
                        onClick={(e) => {
                            e.stopPropagation()
                            if (confirm('이 블록을 2개로 분할하시겠습니까?')) {
                                onSplit()
                            }
                        }}
                        className="p-1.5 hover:bg-blue-600/20 rounded transition-colors"
                        title="분할"
                    >
                        <Scissors className="w-3.5 h-3.5 text-blue-400" />
                    </button>
                    <button
                        onClick={(e) => {
                            e.stopPropagation()
                            if (confirm('이 블록을 자동으로 분할하시겠습니까? (180초 기준)')) {
                                onAutoSplit()
                            }
                        }}
                        className="p-1.5 hover:bg-purple-600/20 rounded transition-colors"
                        title="자동 분할"
                    >
                        <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                    </button>
                    <button
                        onClick={(e) => {
                            e.stopPropagation()
                            if (confirm('다음 블록과 합치시겠습니까?')) {
                                onMerge()
                            }
                        }}
                        className="p-1.5 hover:bg-green-600/20 rounded transition-colors"
                        title="다음 블록과 합치기"
                    >
                        <Link2 className="w-3.5 h-3.5 text-green-400" />
                    </button>
                    <button
                        onClick={(e) => {
                            e.stopPropagation()
                            if (confirm('이 블록을 삭제하시겠습니까?')) {
                                onDelete()
                            }
                        }}
                        className="p-1.5 hover:bg-red-600/20 rounded transition-colors"
                        title="삭제"
                    >
                        <Trash2 className="w-3.5 h-3.5 text-red-400" />
                    </button>
                </div>
            </div>

            {/* 블록 내용 */}
            <div className="ml-6">
                {isEditing ? (
                    <div className="space-y-2">
                        <textarea
                            value={editedContent}
                            onChange={(e) => setEditedContent(e.target.value)}
                            onKeyDown={handleKeyDown}
                            onBlur={handleSave}
                            autoFocus
                            className="w-full px-3 py-2 bg-[#0a0a0a] border border-purple-500 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
                            rows={3}
                        />
                        <div className="flex items-center gap-2 text-xs text-gray-400">
                            <span>⌘ + Enter로 저장</span>
                            <span>•</span>
                            <span>ESC로 취소</span>
                        </div>
                    </div>
                ) : (
                    <p className="text-sm text-gray-200 leading-relaxed">
                        {block.content}
                    </p>
                )}
            </div>

            {/* 효과 표시 */}
            {Object.values(block.effects).some(Boolean) && (
                <div className="mt-3 ml-6 flex flex-wrap gap-1">
                    {block.effects.fadeIn && (
                        <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">
                            페이드인
                        </span>
                    )}
                    {block.effects.fadeOut && (
                        <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">
                            페이드아웃
                        </span>
                    )}
                    {block.effects.zoomIn && (
                        <span className="px-2 py-0.5 bg-green-500/20 text-green-400 rounded text-xs">
                            줌인
                        </span>
                    )}
                    {block.effects.zoomOut && (
                        <span className="px-2 py-0.5 bg-green-500/20 text-green-400 rounded text-xs">
                            줌아웃
                        </span>
                    )}
                    {block.effects.slide && (
                        <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs">
                            슬라이드 {block.effects.slide}
                        </span>
                    )}
                    {block.effects.highlight && (
                        <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 rounded text-xs">
                            강조
                        </span>
                    )}
                </div>
            )}

            {/* 타이밍 표시 */}
            <div className="mt-2 ml-6 text-xs text-gray-500">
                {formatTime(block.timing.start)} - {formatTime(block.timing.end)}
            </div>
        </div>
    )
}

function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
}
