'use client'

import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors, DragEndEvent } from '@dnd-kit/core'
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { ScriptBlock } from '@/lib/blocks/types'
import { Edit2, Trash2, Copy, GripVertical, Check, X } from 'lucide-react'
import { useState, useRef } from 'react'

interface DraggableBlockListProps {
    blocks: ScriptBlock[]
    selectedBlockId: string | null
    onBlockSelect: (id: string) => void
    onBlockUpdate: (id: string, updates: Partial<ScriptBlock>) => void
    onBlockDelete: (id: string) => void
    onBlockDuplicate: (id: string) => void
    onBlockReorder: (blocks: ScriptBlock[]) => void
}

// 개별 블록 컴포넌트 (드래그 가능)
function SortableBlock({
    block,
    isSelected,
    onSelect,
    onUpdate,
    onDelete,
    onDuplicate,
    editingBlockId,
    setEditingBlockId
}: {
    block: ScriptBlock
    isSelected: boolean
    onSelect: () => void
    onUpdate: (updates: Partial<ScriptBlock>) => void
    onDelete: () => void
    onDuplicate: () => void
    editingBlockId: string | null
    setEditingBlockId: (id: string | null) => void
}) {
    const [editContent, setEditContent] = useState(block.content)
    const textareaRef = useRef<HTMLTextAreaElement>(null)

    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging
    } = useSortable({ id: block.id })

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1
    }

    const isEditing = block.id === editingBlockId

    const startEditing = () => {
        setEditingBlockId(block.id)
        setEditContent(block.content)
        setTimeout(() => textareaRef.current?.focus(), 0)
    }

    const saveEdit = () => {
        if (editContent.trim()) {
            onUpdate({ content: editContent.trim() })
        }
        setEditingBlockId(null)
    }

    const cancelEdit = () => {
        setEditingBlockId(null)
        setEditContent(block.content)
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && e.metaKey) {
            saveEdit()
        } else if (e.key === 'Escape') {
            cancelEdit()
        }
    }

    const getBlockColor = (type: ScriptBlock['type']) => {
        switch (type) {
            case 'hook': return 'bg-red-500'
            case 'body': return 'bg-blue-500'
            case 'cta': return 'bg-green-500'
            default: return 'bg-gray-500'
        }
    }

    const getBlockIcon = (type: ScriptBlock['type']) => {
        switch (type) {
            case 'hook': return '🔵'
            case 'body': return '🟢'
            case 'cta': return '🔴'
            default: return '⚪'
        }
    }

    const blockColor = getBlockColor(block.type)
    const blockIcon = getBlockIcon(block.type)

    return (
        <div
            ref={setNodeRef}
            style={style}
            onClick={() => !isEditing && onSelect()}
            className={`
        group relative p-4 rounded-lg border-2 transition-all cursor-pointer
        ${isSelected
                    ? 'border-purple-500 bg-purple-500/10 shadow-lg shadow-purple-500/20'
                    : 'border-gray-700 bg-[#1a1a1a] hover:border-gray-600'
                }
      `}
        >
            {/* 드래그 핸들 */}
            <div
                {...attributes}
                {...listeners}
                className="absolute left-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing"
            >
                <GripVertical className="w-4 h-4 text-gray-500" />
            </div>

            {/* 블록 헤더 */}
            <div className="flex items-center justify-between mb-2 ml-6">
                <div className="flex items-center gap-2">
                    <span className="text-lg">{blockIcon}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold text-white ${blockColor}`}>
                        {block.type.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-400">{block.duration}초</span>
                </div>

                {/* 액션 버튼 */}
                {!isEditing && (
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                            onClick={(e) => {
                                e.stopPropagation()
                                startEditing()
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
                )}

                {/* 편집 모드 버튼 */}
                {isEditing && (
                    <div className="flex items-center gap-1">
                        <button
                            onClick={(e) => {
                                e.stopPropagation()
                                saveEdit()
                            }}
                            className="p-1.5 bg-green-600 hover:bg-green-700 rounded transition-colors"
                            title="저장 (⌘+Enter)"
                        >
                            <Check className="w-3.5 h-3.5" />
                        </button>
                        <button
                            onClick={(e) => {
                                e.stopPropagation()
                                cancelEdit()
                            }}
                            className="p-1.5 bg-red-600 hover:bg-red-700 rounded transition-colors"
                            title="취소 (ESC)"
                        >
                            <X className="w-3.5 h-3.5" />
                        </button>
                    </div>
                )}
            </div>

            {/* 블록 내용 */}
            <div className="ml-6">
                {isEditing ? (
                    <div className="space-y-2">
                        <textarea
                            ref={textareaRef}
                            value={editContent}
                            onChange={(e) => setEditContent(e.target.value)}
                            onKeyDown={handleKeyDown}
                            onClick={(e) => e.stopPropagation()}
                            className="w-full px-3 py-2 bg-[#0a0a0a] border border-purple-500 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
                            rows={4}
                        />
                        <div className="flex items-center gap-2 text-xs text-gray-400">
                            <span>⌘ + Enter로 저장</span>
                            <span>•</span>
                            <span>ESC로 취소</span>
                        </div>
                    </div>
                ) : (
                    <p className="text-sm text-gray-200 leading-relaxed">{block.content}</p>
                )}
            </div>

            {/* 효과 표시 */}
            {Object.values(block.effects).some(Boolean) && !isEditing && (
                <div className="mt-3 ml-6 flex flex-wrap gap-1">
                    {block.effects.fadeIn && <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">페이드인</span>}
                    {block.effects.fadeOut && <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">페이드아웃</span>}
                    {block.effects.zoomIn && <span className="px-2 py-0.5 bg-green-500/20 text-green-400 rounded text-xs">줌인</span>}
                    {block.effects.zoomOut && <span className="px-2 py-0.5 bg-green-500/20 text-green-400 rounded text-xs">줌아웃</span>}
                    {block.effects.slide && <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs">슬라이드 {block.effects.slide}</span>}
                    {block.effects.highlight && <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 rounded text-xs">강조</span>}
                </div>
            )}

            {/* 타이밍 */}
            {!isEditing && (
                <div className="mt-2 ml-6 text-xs text-gray-500">
                    {formatTime(block.timing.start)} - {formatTime(block.timing.end)}
                </div>
            )}
        </div>
    )
}

// 메인 드래그 가능 블록 리스트
export default function DraggableBlockList(props: DraggableBlockListProps) {
    const [editingBlockId, setEditingBlockId] = useState<string | null>(null)

    const sensors = useSensors(
        useSensor(PointerSensor),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates
        })
    )

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event

        if (over && active.id !== over.id) {
            const oldIndex = props.blocks.findIndex(b => b.id === active.id)
            const newIndex = props.blocks.findIndex(b => b.id === over.id)

            const reorderedBlocks = arrayMove(props.blocks, oldIndex, newIndex)
            props.onBlockReorder(reorderedBlocks)
        }
    }

    return (
        <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
        >
            <SortableContext
                items={props.blocks.map(b => b.id)}
                strategy={verticalListSortingStrategy}
            >
                <div className="space-y-3">
                    {props.blocks.map((block) => (
                        <SortableBlock
                            key={block.id}
                            block={block}
                            isSelected={block.id === props.selectedBlockId}
                            onSelect={() => props.onBlockSelect(block.id)}
                            onUpdate={(updates) => props.onBlockUpdate(block.id, updates)}
                            onDelete={() => props.onBlockDelete(block.id)}
                            onDuplicate={() => props.onBlockDuplicate(block.id)}
                            editingBlockId={editingBlockId}
                            setEditingBlockId={setEditingBlockId}
                        />
                    ))}
                </div>
            </SortableContext>
        </DndContext>
    )
}

function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
}
