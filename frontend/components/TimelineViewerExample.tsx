'use client'

/**
 * TimelineViewer 사용 예제
 *
 * 이 파일은 TimelineViewer 컴포넌트를 사용하는 방법을 보여줍니다.
 * 실제 프로젝트에서는 VrewStyleEditor와 함께 사용하여 동기화를 구현합니다.
 */

import { useState, useEffect, useRef } from 'react'
import TimelineViewer from './TimelineViewer'
import { ScriptBlock, splitScriptIntoBlocks } from '@/lib/blocks/types'

export default function TimelineViewerExample() {
    const [blocks, setBlocks] = useState<ScriptBlock[]>([])
    const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null)
    const [currentTime, setCurrentTime] = useState(0)
    const [totalDuration, setTotalDuration] = useState(0)
    const [isPlaying, setIsPlaying] = useState(false)

    // 예제 스크립트로 블록 생성
    useEffect(() => {
        const sampleHook = "안녕하세요! 오늘은 정말 놀라운 이야기를 들려드리겠습니다."
        const sampleBody = "이 방법을 사용하면 여러분의 생산성이 3배나 향상될 수 있습니다. 실제로 많은 사람들이 이미 경험하고 있는 효과입니다."
        const sampleCta = "지금 바로 시작해보세요! 구독과 좋아요도 부탁드립니다."

        const generatedBlocks = splitScriptIntoBlocks(sampleHook, sampleBody, sampleCta)
        setBlocks(generatedBlocks)

        // 총 시간 계산
        const total = generatedBlocks.reduce((sum, block) => sum + block.duration, 0)
        setTotalDuration(total)
    }, [])

    // 재생 시뮬레이션
    useEffect(() => {
        if (!isPlaying) return

        const interval = setInterval(() => {
            setCurrentTime((prev) => {
                if (prev >= totalDuration) {
                    setIsPlaying(false)
                    return 0
                }
                return prev + 0.1
            })
        }, 100)

        return () => clearInterval(interval)
    }, [isPlaying, totalDuration])

    // 블록 클릭 핸들러
    const handleBlockClick = (blockId: string) => {
        setSelectedBlockId(blockId)

        // 해당 블록으로 시간 이동
        const block = blocks.find(b => b.id === blockId)
        if (block) {
            setCurrentTime(block.timing.start)
        }

        console.log('Block clicked:', blockId)
    }

    // 시간 탐색 핸들러
    const handleTimeSeek = (time: number) => {
        setCurrentTime(time)

        // 해당 시간에 있는 블록 찾기
        const activeBlock = blocks.find(
            b => b.timing.start <= time && b.timing.end >= time
        )
        if (activeBlock) {
            setSelectedBlockId(activeBlock.id)
        }

        console.log('Time seek:', time)
    }

    // 재생/일시정지 토글
    const togglePlayback = () => {
        setIsPlaying(!isPlaying)
    }

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white p-8">
            <div className="max-w-6xl mx-auto space-y-6">
                <h1 className="text-3xl font-bold">타임라인 뷰어 예제</h1>

                {/* 재생 컨트롤 */}
                <div className="flex items-center gap-4">
                    <button
                        onClick={togglePlayback}
                        className="px-6 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg font-semibold transition-colors"
                    >
                        {isPlaying ? '일시정지' : '재생'}
                    </button>
                    <button
                        onClick={() => {
                            setCurrentTime(0)
                            setIsPlaying(false)
                        }}
                        className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-semibold transition-colors"
                    >
                        처음으로
                    </button>
                </div>

                {/* 타임라인 뷰어 */}
                <div className="bg-[#1a1a1a] border border-gray-700 rounded-lg p-6">
                    <h2 className="text-xl font-bold mb-4">타임라인</h2>
                    <TimelineViewer
                        blocks={blocks}
                        currentTime={currentTime}
                        totalDuration={totalDuration}
                        selectedBlockId={selectedBlockId}
                        onBlockClick={handleBlockClick}
                        onTimeSeek={handleTimeSeek}
                    />
                </div>

                {/* 블록 정보 */}
                <div className="bg-[#1a1a1a] border border-gray-700 rounded-lg p-6">
                    <h2 className="text-xl font-bold mb-4">블록 정보</h2>
                    <div className="space-y-2">
                        {blocks.map((block) => (
                            <div
                                key={block.id}
                                className={`
                                    p-3 rounded-lg border-2 cursor-pointer transition-all
                                    ${block.id === selectedBlockId
                                        ? 'border-purple-500 bg-purple-500/10'
                                        : 'border-gray-700 hover:border-gray-600'
                                    }
                                `}
                                onClick={() => handleBlockClick(block.id)}
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-semibold">{block.type.toUpperCase()}</span>
                                    <span className="text-sm text-gray-400">
                                        {block.timing.start}s - {block.timing.end}s ({block.duration}s)
                                    </span>
                                </div>
                                <p className="text-sm text-gray-300">{block.content}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 사용 가이드 */}
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-6">
                    <h2 className="text-xl font-bold mb-4 text-blue-400">사용 가이드</h2>
                    <ul className="space-y-2 text-sm text-gray-300">
                        <li>• 타임라인에서 블록을 클릭하면 해당 블록으로 이동합니다</li>
                        <li>• 타임라인 배경을 클릭하면 해당 시간으로 이동합니다</li>
                        <li>• Ctrl/Cmd + 마우스 휠로 타임라인을 확대/축소할 수 있습니다</li>
                        <li>• 줌 버튼으로도 확대/축소가 가능합니다</li>
                        <li>• 빨간 선(playhead)은 현재 재생 위치를 나타냅니다</li>
                    </ul>
                </div>

                {/* 통합 가이드 */}
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-6">
                    <h2 className="text-xl font-bold mb-4 text-green-400">VrewStyleEditor와 통합하기</h2>
                    <pre className="bg-[#0a0a0a] p-4 rounded-lg text-xs overflow-x-auto">
{`// 1. 상태 공유
const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null)
const [currentTime, setCurrentTime] = useState(0)

// 2. TimelineViewer 설정
<TimelineViewer
  blocks={blocks}
  currentTime={currentTime}
  totalDuration={totalDuration}
  selectedBlockId={selectedBlockId}
  onBlockClick={(id) => {
    setSelectedBlockId(id)
    // 텍스트 에디터로 스크롤
    scrollToBlock(id)
  }}
  onTimeSeek={(time) => {
    setCurrentTime(time)
    // 해당 시간의 블록 찾기
    const block = findBlockAtTime(time)
    if (block) setSelectedBlockId(block.id)
  }}
/>

// 3. VrewStyleEditor 설정
<VrewStyleEditor
  blocks={blocks}
  selectedBlockId={selectedBlockId}
  onBlockSelect={(id) => {
    setSelectedBlockId(id)
    // 타임라인에서 하이라이트 (자동)
  }}
/>`}
                    </pre>
                </div>
            </div>
        </div>
    )
}
