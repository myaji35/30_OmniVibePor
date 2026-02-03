'use client'

import { ScriptBlock, getBlockColor } from '@/lib/blocks/types'
import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ZoomIn, ZoomOut } from 'lucide-react'

interface TimelineViewerProps {
    blocks: ScriptBlock[]
    currentTime: number // 현재 재생 위치 (초)
    totalDuration: number
    selectedBlockId: string | null
    onBlockClick: (blockId: string) => void
    onTimeSeek: (time: number) => void
}

// 블록 타입별 배경 색상 (더 선명한 색상)
const BLOCK_COLORS = {
    hook: '#EF4444', // 빨강
    body: '#3B82F6', // 파랑
    cta: '#10B981', // 초록
}

export default function TimelineViewer({
    blocks,
    currentTime,
    totalDuration,
    selectedBlockId,
    onBlockClick,
    onTimeSeek,
}: TimelineViewerProps) {
    const [zoom, setZoom] = useState(1) // 1 = 100%, 2 = 200%
    const [isDragging, setIsDragging] = useState(false)
    const timelineRef = useRef<HTMLDivElement>(null)

    // 줌 조정
    const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.5, 4))
    const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.5, 0.5))

    // 마우스 휠로 줌
    const handleWheel = (e: React.WheelEvent) => {
        if (e.ctrlKey || e.metaKey) {
            e.preventDefault()
            if (e.deltaY < 0) {
                handleZoomIn()
            } else {
                handleZoomOut()
            }
        }
    }

    // 타임라인 클릭 → 시간 탐색
    const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!timelineRef.current) return

        const rect = timelineRef.current.getBoundingClientRect()
        const x = e.clientX - rect.left
        const timelineWidth = rect.width
        const clickedTime = (x / timelineWidth) * totalDuration

        onTimeSeek(clickedTime)
    }

    // 블록 클릭
    const handleBlockClick = (blockId: string, e: React.MouseEvent) => {
        e.stopPropagation() // 타임라인 클릭 이벤트 전파 방지
        onBlockClick(blockId)
    }

    // 시간 포맷 (0:00 형식)
    const formatTime = (seconds: number): string => {
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    // 총 시간이 0이면 기본값 사용
    const effectiveDuration = totalDuration > 0 ? totalDuration : 100

    // 시간 눈금 생성 (1초 단위)
    const timeMarkers = []
    const markerInterval = zoom >= 2 ? 1 : zoom >= 1 ? 2 : 5 // 줌에 따라 간격 조정
    for (let i = 0; i <= effectiveDuration; i += markerInterval) {
        timeMarkers.push(i)
    }

    return (
        <div className="space-y-2">
            {/* 컨트롤 바 */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleZoomOut}
                        disabled={zoom <= 0.5}
                        className="p-2 bg-[#1a1a1a] border border-gray-700 rounded hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        title="축소"
                    >
                        <ZoomOut className="w-4 h-4" />
                    </button>
                    <span className="text-sm text-gray-400 min-w-[60px] text-center">
                        {(zoom * 100).toFixed(0)}%
                    </span>
                    <button
                        onClick={handleZoomIn}
                        disabled={zoom >= 4}
                        className="p-2 bg-[#1a1a1a] border border-gray-700 rounded hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        title="확대"
                    >
                        <ZoomIn className="w-4 h-4" />
                    </button>
                </div>

                <div className="text-sm text-gray-400">
                    {formatTime(currentTime)} / {formatTime(effectiveDuration)}
                </div>
            </div>

            {/* 타임라인 컨테이너 */}
            <div
                className="bg-[#1a1a1a] border border-gray-700 rounded-lg overflow-x-auto"
                onWheel={handleWheel}
            >
                <div
                    style={{
                        width: `${zoom * 100}%`,
                        minWidth: '100%',
                    }}
                >
                    {/* 시간 눈금 */}
                    <div className="relative h-8 border-b border-gray-700 px-2">
                        {timeMarkers.map((time) => {
                            const leftPercent = (time / effectiveDuration) * 100
                            return (
                                <div
                                    key={time}
                                    className="absolute top-0 h-full flex items-center"
                                    style={{ left: `${leftPercent}%` }}
                                >
                                    <div className="relative">
                                        <div className="w-px h-2 bg-gray-600"></div>
                                        <span className="absolute top-2 left-1/2 -translate-x-1/2 text-xs text-gray-500 whitespace-nowrap">
                                            {time}s
                                        </span>
                                    </div>
                                </div>
                            )
                        })}
                    </div>

                    {/* 블록 트랙 */}
                    <div
                        ref={timelineRef}
                        className="relative h-24 px-2 py-2 cursor-pointer"
                        onClick={handleTimelineClick}
                    >
                        {/* 블록들 */}
                        {blocks.map((block) => {
                            const leftPercent = (block.timing.start / effectiveDuration) * 100
                            const widthPercent = (block.duration / effectiveDuration) * 100
                            const isSelected = block.id === selectedBlockId

                            return (
                                <motion.div
                                    key={block.id}
                                    className={`
                                        absolute top-2 h-20 rounded-lg cursor-pointer
                                        flex items-center justify-center px-2
                                        transition-all duration-200
                                        ${isSelected ? 'ring-2 ring-white ring-offset-2 ring-offset-[#1a1a1a]' : ''}
                                    `}
                                    style={{
                                        left: `${leftPercent}%`,
                                        width: `${widthPercent}%`,
                                        backgroundColor: BLOCK_COLORS[block.type],
                                        minWidth: '40px', // 최소 너비 보장
                                    }}
                                    onClick={(e) => handleBlockClick(block.id, e)}
                                    whileHover={{ opacity: 0.8, scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.2 }}
                                >
                                    <div className="text-white text-xs font-semibold text-center overflow-hidden text-ellipsis">
                                        {block.type.toUpperCase()}
                                        <div className="text-[10px] opacity-80 mt-1">
                                            {block.duration}s
                                        </div>
                                    </div>
                                </motion.div>
                            )
                        })}

                        {/* Playhead (현재 재생 위치) */}
                        <motion.div
                            className="absolute top-0 bottom-0 w-0.5 bg-red-500 pointer-events-none z-10"
                            style={{
                                left: `${(currentTime / effectiveDuration) * 100}%`,
                            }}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.1 }}
                        >
                            {/* Playhead 헤드 */}
                            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3 h-3 bg-red-500 rounded-full -mt-1"></div>
                        </motion.div>
                    </div>

                    {/* 블록 상세 정보 (호버 시) */}
                    {blocks.map((block) => {
                        const leftPercent = (block.timing.start / effectiveDuration) * 100
                        const widthPercent = (block.duration / effectiveDuration) * 100

                        return (
                            <div
                                key={`tooltip-${block.id}`}
                                className="absolute hidden group-hover:block"
                                style={{
                                    left: `${leftPercent}%`,
                                    width: `${widthPercent}%`,
                                }}
                            ></div>
                        )
                    })}
                </div>
            </div>

            {/* 범례 */}
            <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: BLOCK_COLORS.hook }}></div>
                    <span className="text-gray-400">훅 (Hook)</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: BLOCK_COLORS.body }}></div>
                    <span className="text-gray-400">본문 (Body)</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: BLOCK_COLORS.cta }}></div>
                    <span className="text-gray-400">CTA</span>
                </div>
            </div>

            {/* 힌트 */}
            <div className="text-xs text-gray-500 space-y-1">
                <p>💡 블록을 클릭하면 해당 위치로 이동합니다</p>
                <p>🎯 Ctrl/Cmd + 마우스 휠로 확대/축소할 수 있습니다</p>
            </div>
        </div>
    )
}
