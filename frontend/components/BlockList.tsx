'use client'

import { useState, useEffect, useRef } from 'react'
import { ScriptBlock } from '@/lib/blocks/types'
import { Edit2, Trash2, Copy, GripVertical, Check, X } from 'lucide-react'

interface BlockListProps {
    blocks: ScriptBlock[]
    selectedBlockId: string | null
    onBlockSelect: (id: string) => void
    onBlockUpdate: (id: string, updates: Partial<ScriptBlock>) => void
    onBlockDelete: (id: string) => void
    onBlockDuplicate: (id: string) => void
    onBlockReorder: (blocks: ScriptBlock[]) => void
}

export default function BlockList({
    blocks,
    selectedBlockId,
    onBlockSelect,
    onBlockUpdate,
    onBlockDelete,
    onBlockDuplicate,
    onBlockReorder
}: BlockListProps) {
    const [editingBlockId, setEditingBlockId] = useState<string | null>(null)
    const [editContent, setEditContent] = useState('')
    const textareaRef = useRef<HTMLTextAreaElement>(null)

    // 편집 모드 진입
    const startEditing = (block: ScriptBlock) => {
        setEditingBlockId(block.id)
        setEditContent(block.content)
        setTimeout(() => textareaRef.current?.focus(), 0)
    }

    // 편집 저장
    const saveEdit = () => {
        if (editingBlockId && editContent.trim()) {
            onBlockUpdate(editingBlockId, { content: editContent.trim() })
        }
        setEditingBlockId(null)
    }

    // 편집 취소
    const cancelEdit = () => {
        setEditingBlockId(null)
        setEditContent('')
    }

    // 키보드 단축키
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

    return (
        <div className="space-y-6">
            {blocks.map((block) => {
                const isSelected = block.id === selectedBlockId
                const isEditing = block.id === editingBlockId

                return (
                    <div
                        key={block.id}
                        onClick={() => !isEditing && onBlockSelect(block.id)}
                        className={`
                            group relative p-8 rounded-[2rem] border-2 transition-all duration-500 cursor-pointer
                            ${isSelected
                                ? 'border-brand-primary-500/50 bg-brand-primary-500/[0.03] shadow-[0_20px_50px_-10px_rgba(168,85,247,0.2)]'
                                : 'border-white/5 bg-white/[0.02] hover:border-white/10 hover:bg-white/[0.04]'
                            }
                        `}
                    >
                        {/* 활성 상태 표시 바 */}
                        {isSelected && (
                            <div className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-brand-primary-500 rounded-r-full shadow-[0_0_15px_rgba(168,85,247,1)]" />
                        )}

                        {/* 드래그 핸들 */}
                        <div className="absolute -left-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-all duration-300">
                            <div className="p-2 bg-white/5 rounded-full border border-white/10 backdrop-blur-md">
                                <GripVertical className="w-4 h-4 text-brand-primary-400" />
                            </div>
                        </div>

                        {/* 블록 헤더 */}
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-4">
                                <div className={`px-4 py-1.5 rounded-full text-[10px] font-black tracking-[0.2em] text-white uppercase shadow-lg
                                    ${block.type === 'hook' ? 'bg-gradient-to-r from-red-600 to-orange-600 shadow-red-500/20' :
                                        block.type === 'body' ? 'bg-gradient-to-r from-brand-primary-600 to-brand-accent-600 shadow-purple-500/20' :
                                            'bg-gradient-to-r from-green-600 to-emerald-600 shadow-emerald-500/20'}
                                `}>
                                    {block.type}
                                </div>
                                <div className="flex items-center gap-2 px-3 py-1 bg-white/5 rounded-full border border-white/5">
                                    <div className="w-1.5 h-1.5 rounded-full bg-brand-primary-500 animate-pulse" />
                                    <span className="text-[10px] font-bold text-gray-500 tracking-wider">
                                        {block.duration} SECS
                                    </span>
                                </div>
                            </div>

                            {/* 액션 버튼 */}
                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-2 group-hover:translate-x-0">
                                {!isEditing ? (
                                    <>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); startEditing(block); }}
                                            className="p-3 bg-white/5 hover:bg-brand-primary-600/20 rounded-2xl border border-white/5 hover:border-brand-primary-500/30 transition-all group/btn"
                                        >
                                            <Edit2 className="w-4 h-4 text-gray-500 group-hover:text-brand-primary-400 group-active:scale-90 transition-all" />
                                        </button>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); onBlockDuplicate(block.id); }}
                                            className="p-3 bg-white/5 hover:bg-brand-primary-600/20 rounded-2xl border border-white/5 hover:border-brand-primary-500/30 transition-all group/btn"
                                        >
                                            <Copy className="w-4 h-4 text-gray-500 group-hover:text-brand-primary-400 group-active:scale-90 transition-all" />
                                        </button>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); if (confirm('이 블록을 삭제하시겠습니까?')) onBlockDelete(block.id); }}
                                            className="p-3 bg-white/5 hover:bg-red-600/20 rounded-2xl border border-white/5 hover:border-red-500/30 transition-all group/btn"
                                        >
                                            <Trash2 className="w-4 h-4 text-gray-500 group-hover:text-red-400 group-active:scale-90 transition-all" />
                                        </button>
                                    </>
                                ) : (
                                    <>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); saveEdit(); }}
                                            className="px-6 py-2.5 bg-brand-primary-600 hover:bg-brand-primary-500 rounded-xl text-xs font-black text-white transition-all shadow-xl shadow-purple-500/20 flex items-center gap-2"
                                        >
                                            <Check className="w-4 h-4" /> SAVE
                                        </button>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); cancelEdit(); }}
                                            className="p-2.5 bg-white/5 hover:bg-white/10 rounded-xl transition-all"
                                        >
                                            <X className="w-4 h-4 text-gray-500" />
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>

                        {/* 블록 내용 */}
                        <div className="relative">
                            {isEditing ? (
                                <div className="space-y-4">
                                    <textarea
                                        ref={textareaRef}
                                        value={editContent}
                                        onChange={(e) => setEditContent(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        onClick={(e) => e.stopPropagation()}
                                        className="w-full px-6 py-5 bg-black/40 border-2 border-brand-primary-500/30 rounded-3xl text-lg font-medium leading-relaxed resize-none focus:outline-none focus:border-brand-primary-500 focus:ring-4 focus:ring-brand-primary-500/10 transition-all"
                                        rows={4}
                                        placeholder="스크립트 대본을 입력하세요..."
                                    />
                                    <div className="flex items-center gap-3 text-[10px] font-black text-gray-600 uppercase tracking-widest pl-2">
                                        <span className="flex items-center gap-1"><kbd className="px-1.5 py-0.5 bg-white/5 rounded border border-white/10 uppercase font-mono">⌘</kbd> + <kbd className="px-1.5 py-0.5 bg-white/5 rounded border border-white/10 uppercase font-mono">ENTER</kbd> TO SAVE</span>
                                        <div className="w-1 h-1 rounded-full bg-gray-800" />
                                        <span><kbd className="px-1.5 py-0.5 bg-white/5 rounded border border-white/10 uppercase font-mono">ESC</kbd> TO CANCEL</span>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    <p className="text-xl font-medium text-white leading-[1.6] tracking-tight">
                                        {block.content || <span className="text-white/10 italic italic uppercase tracking-widest text-sm font-black">Empty Script Block Content</span>}
                                    </p>

                                    <div className="flex items-center justify-between">
                                        {/* 효과 배지 */}
                                        <div className="flex flex-wrap gap-2">
                                            {Object.entries(block.effects).map(([key, value]) => {
                                                if (!value) return null;
                                                return (
                                                    <div key={key} className="flex items-center gap-2 px-3 py-1 bg-white/5 rounded-lg border border-white/5">
                                                        <div className="w-1 h-1 rounded-full bg-brand-accent-500 shadow-[0_0_5px_#3b82f6]" />
                                                        <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
                                                            {key.replace(/([A-Z])/g, ' $1')}
                                                        </span>
                                                    </div>
                                                );
                                            })}
                                        </div>

                                        {/* 타이밍 */}
                                        <div className="flex items-center gap-2 text-[10px] font-black font-mono text-gray-600 tracking-widest uppercase italic">
                                            <span>{formatTime(block.timing.start)}</span>
                                            <div className="w-4 h-px bg-gray-800" />
                                            <span>{formatTime(block.timing.end)}</span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )
            })}
        </div>
    )
}

function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
}
