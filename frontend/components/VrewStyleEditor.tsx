'use client'

import React, { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd'
import { Trash2, GripVertical } from 'lucide-react'

/**
 * 스크립트 블록 타입 정의
 */
interface ScriptBlock {
  id: string
  type: 'hook' | 'main' | 'cta'
  script: string
  duration: number // 예상 시간 (초)
  order: number
}

interface VrewStyleEditorProps {
  initialBlocks?: ScriptBlock[]
  onChange?: (blocks: ScriptBlock[]) => void
}

/**
 * VrewStyleEditor: Vrew AI 스타일의 블록 기반 스크립트 편집기
 *
 * 기능:
 * - Enter: 블록 분할
 * - Backspace (맨 앞): 이전 블록과 합치기
 * - Delete: 블록 전체 삭제
 * - Arrow Up/Down: 블록 간 이동
 * - Drag & Drop: 블록 순서 변경
 */
export default function VrewStyleEditor({ initialBlocks, onChange }: VrewStyleEditorProps) {
  const [blocks, setBlocks] = useState<ScriptBlock[]>(
    initialBlocks || [
      {
        id: 'block-1',
        type: 'hook',
        script: '안녕하세요! 오늘은 AI 영상 자동화에 대해 알아보겠습니다.',
        duration: 0,
        order: 0,
      },
      {
        id: 'block-2',
        type: 'main',
        script: 'OmniVibe Pro는 구글 시트 기반 전략 수립부터 AI 에이전트 협업, 영상 생성까지 전 과정을 자동화합니다.',
        duration: 0,
        order: 1,
      },
      {
        id: 'block-3',
        type: 'cta',
        script: '지금 바로 시작해보세요!',
        duration: 0,
        order: 2,
      },
    ]
  )

  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null)
  const textareaRefs = useRef<{ [key: string]: HTMLTextAreaElement | null }>({})

  /**
   * 예상 시간 계산
   * - 한글: 1글자당 0.3초
   * - 영어: 1단어당 0.5초
   */
  const calculateDuration = (text: string): number => {
    const koreanChars = (text.match(/[가-힣]/g) || []).length
    const englishWords = (text.match(/[a-zA-Z]+/g) || []).length

    return Math.round((koreanChars * 0.3 + englishWords * 0.5) * 10) / 10
  }

  /**
   * 블록 업데이트 및 부모 컴포넌트에 전달
   */
  const updateBlocks = (newBlocks: ScriptBlock[]) => {
    const updatedBlocks = newBlocks.map((block, index) => ({
      ...block,
      order: index,
      duration: calculateDuration(block.script),
    }))
    setBlocks(updatedBlocks)
    onChange?.(updatedBlocks)
  }

  /**
   * 스크립트 수정 핸들러
   */
  const updateBlockScript = (blockId: string, newScript: string) => {
    const newBlocks = blocks.map((block) =>
      block.id === blockId ? { ...block, script: newScript } : block
    )
    updateBlocks(newBlocks)
  }

  /**
   * Enter 키: 블록 분할
   * - 커서 앞 텍스트 → 현재 블록
   * - 커서 뒤 텍스트 → 새 블록
   */
  const handleEnterKey = (blockId: string, cursorPosition: number) => {
    const blockIndex = blocks.findIndex((b) => b.id === blockId)
    if (blockIndex === -1) return

    const currentBlock = blocks[blockIndex]
    const textBefore = currentBlock.script.substring(0, cursorPosition)
    const textAfter = currentBlock.script.substring(cursorPosition)

    const newBlock: ScriptBlock = {
      id: `block-${Date.now()}`,
      type: currentBlock.type,
      script: textAfter,
      duration: 0,
      order: blockIndex + 1,
    }

    const newBlocks = [
      ...blocks.slice(0, blockIndex),
      { ...currentBlock, script: textBefore },
      newBlock,
      ...blocks.slice(blockIndex + 1),
    ]

    updateBlocks(newBlocks)

    // 새 블록에 포커스
    setTimeout(() => {
      textareaRefs.current[newBlock.id]?.focus()
      textareaRefs.current[newBlock.id]?.setSelectionRange(0, 0)
    }, 0)
  }

  /**
   * Backspace (맨 앞): 이전 블록과 합치기
   */
  const handleBackspace = (blockId: string) => {
    const blockIndex = blocks.findIndex((b) => b.id === blockId)
    if (blockIndex <= 0) return // 첫 번째 블록은 합칠 수 없음

    const currentBlock = blocks[blockIndex]
    const prevBlock = blocks[blockIndex - 1]
    const prevTextLength = prevBlock.script.length

    const mergedBlock = {
      ...prevBlock,
      script: prevBlock.script + currentBlock.script,
    }

    const newBlocks = [
      ...blocks.slice(0, blockIndex - 1),
      mergedBlock,
      ...blocks.slice(blockIndex + 1),
    ]

    updateBlocks(newBlocks)

    // 이전 블록의 합친 지점에 커서 위치
    setTimeout(() => {
      textareaRefs.current[prevBlock.id]?.focus()
      textareaRefs.current[prevBlock.id]?.setSelectionRange(prevTextLength, prevTextLength)
    }, 0)
  }

  /**
   * Delete 키: 블록 전체 삭제
   */
  const handleDelete = (blockId: string) => {
    if (blocks.length <= 1) return // 최소 1개 블록은 유지

    const newBlocks = blocks.filter((b) => b.id !== blockId)
    updateBlocks(newBlocks)

    // 다음 블록 또는 이전 블록에 포커스
    const deletedIndex = blocks.findIndex((b) => b.id === blockId)
    const nextBlockId = newBlocks[deletedIndex]?.id || newBlocks[deletedIndex - 1]?.id
    if (nextBlockId) {
      setTimeout(() => {
        textareaRefs.current[nextBlockId]?.focus()
      }, 0)
    }
  }

  /**
   * Arrow Up/Down: 블록 간 이동
   */
  const handleArrowKey = (blockId: string, direction: 'up' | 'down') => {
    const blockIndex = blocks.findIndex((b) => b.id === blockId)
    if (blockIndex === -1) return

    if (direction === 'up' && blockIndex > 0) {
      const prevBlockId = blocks[blockIndex - 1].id
      textareaRefs.current[prevBlockId]?.focus()
    } else if (direction === 'down' && blockIndex < blocks.length - 1) {
      const nextBlockId = blocks[blockIndex + 1].id
      textareaRefs.current[nextBlockId]?.focus()
    }
  }

  /**
   * 키보드 이벤트 핸들러
   */
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>, blockId: string) => {
    const textarea = e.currentTarget
    const cursorPosition = textarea.selectionStart

    // Enter 키: 블록 분할 (Shift+Enter는 줄바꿈)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleEnterKey(blockId, cursorPosition)
    }

    // Backspace (맨 앞): 이전 블록과 합치기
    if (e.key === 'Backspace' && cursorPosition === 0) {
      e.preventDefault()
      handleBackspace(blockId)
    }

    // Delete 키 (Cmd/Ctrl + Delete): 블록 전체 삭제
    if (e.key === 'Delete' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      handleDelete(blockId)
    }

    // Arrow Up/Down: 블록 간 이동
    if (e.key === 'ArrowUp' && cursorPosition === 0) {
      e.preventDefault()
      handleArrowKey(blockId, 'up')
    }

    const isAtEnd = cursorPosition === textarea.value.length
    if (e.key === 'ArrowDown' && isAtEnd) {
      e.preventDefault()
      handleArrowKey(blockId, 'down')
    }
  }

  /**
   * Drag & Drop: 블록 순서 변경
   */
  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return

    const sourceIndex = result.source.index
    const destIndex = result.destination.index

    if (sourceIndex === destIndex) return

    const newBlocks = Array.from(blocks)
    const [movedBlock] = newBlocks.splice(sourceIndex, 1)
    newBlocks.splice(destIndex, 0, movedBlock)

    updateBlocks(newBlocks)
  }

  /**
   * 블록 타입별 색상
   */
  const getBlockTypeColor = (type: ScriptBlock['type']) => {
    switch (type) {
      case 'hook':
        return 'bg-purple-500/20 border-purple-500/50'
      case 'main':
        return 'bg-blue-500/20 border-blue-500/50'
      case 'cta':
        return 'bg-green-500/20 border-green-500/50'
      default:
        return 'bg-gray-500/20 border-gray-500/50'
    }
  }

  /**
   * 블록 타입 라벨
   */
  const getBlockTypeLabel = (type: ScriptBlock['type']) => {
    switch (type) {
      case 'hook':
        return '훅'
      case 'main':
        return '본문'
      case 'cta':
        return 'CTA'
      default:
        return ''
    }
  }

  // 전체 예상 시간 계산
  const totalDuration = blocks.reduce((sum, block) => sum + block.duration, 0)

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-gray-900 rounded-lg shadow-xl">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">스크립트 편집기</h2>
        <div className="text-sm text-gray-400">
          총 예상 시간: <span className="font-bold text-white">{totalDuration.toFixed(1)}초</span>
        </div>
      </div>

      {/* 블록 리스트 */}
      <DragDropContext onDragEnd={handleDragEnd}>
        <Droppable droppableId="script-blocks">
          {(provided) => (
            <div
              {...provided.droppableProps}
              ref={provided.innerRef}
              className="space-y-3"
            >
              {blocks.map((block, index) => (
                <Draggable key={block.id} draggableId={block.id} index={index}>
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      className={`
                        flex items-start gap-3 p-4 rounded-lg border-2 transition-all
                        ${snapshot.isDragging ? 'bg-gray-700 shadow-2xl' : 'bg-gray-800'}
                        ${selectedBlockId === block.id ? 'border-purple-500' : 'border-gray-700'}
                        hover:bg-gray-700
                      `}
                    >
                      {/* Drag Handle */}
                      <div
                        {...provided.dragHandleProps}
                        className="flex-shrink-0 mt-2 cursor-grab active:cursor-grabbing text-gray-500 hover:text-gray-300"
                      >
                        <GripVertical size={20} />
                      </div>

                      {/* 블록 번호 */}
                      <div className="flex-shrink-0 w-8 mt-2">
                        <div className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-700 text-white text-sm font-bold">
                          {index + 1}
                        </div>
                      </div>

                      {/* 블록 타입 태그 */}
                      <div className="flex-shrink-0 mt-2">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${getBlockTypeColor(block.type)}`}>
                          {getBlockTypeLabel(block.type)}
                        </span>
                      </div>

                      {/* Textarea */}
                      <div className="flex-1">
                        <textarea
                          ref={(el) => {
                            textareaRefs.current[block.id] = el
                          }}
                          value={block.script}
                          onChange={(e) => updateBlockScript(block.id, e.target.value)}
                          onKeyDown={(e) => handleKeyDown(e, block.id)}
                          onFocus={() => setSelectedBlockId(block.id)}
                          className="w-full min-h-[80px] p-3 bg-gray-900 text-white rounded-lg border border-gray-700 focus:border-purple-500 focus:outline-none resize-none"
                          placeholder="스크립트를 입력하세요..."
                        />
                        <div className="mt-1 text-xs text-gray-500">
                          예상 시간: {block.duration.toFixed(1)}초
                        </div>
                      </div>

                      {/* 삭제 버튼 */}
                      <button
                        onClick={() => handleDelete(block.id)}
                        disabled={blocks.length <= 1}
                        className={`
                          flex-shrink-0 mt-2 p-2 rounded-lg transition-colors
                          ${blocks.length <= 1
                            ? 'text-gray-600 cursor-not-allowed'
                            : 'text-gray-400 hover:text-red-500 hover:bg-red-500/10'
                          }
                        `}
                        title="블록 삭제 (Cmd/Ctrl + Delete)"
                      >
                        <Trash2 size={20} />
                      </button>
                    </div>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </DragDropContext>

      {/* 사용 가이드 */}
      <div className="mt-6 p-4 bg-gray-800 rounded-lg border border-gray-700">
        <h3 className="text-sm font-bold text-white mb-2">키보드 단축키</h3>
        <ul className="text-xs text-gray-400 space-y-1">
          <li>• <span className="font-mono bg-gray-700 px-1 rounded">Enter</span>: 블록 분할 (Shift+Enter: 줄바꿈)</li>
          <li>• <span className="font-mono bg-gray-700 px-1 rounded">Backspace</span> (맨 앞): 이전 블록과 합치기</li>
          <li>• <span className="font-mono bg-gray-700 px-1 rounded">Cmd/Ctrl + Delete</span>: 블록 삭제</li>
          <li>• <span className="font-mono bg-gray-700 px-1 rounded">↑/↓</span> (맨 앞/끝): 블록 간 이동</li>
          <li>• <span className="font-mono bg-gray-700 px-1 rounded">드래그</span>: 블록 순서 변경</li>
        </ul>
      </div>
    </div>
  )
}
