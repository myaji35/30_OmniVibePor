'use client'

import { useState } from 'react'
import { Clock, Sparkles } from 'lucide-react'

interface DurationSelectorProps {
    onGenerate: (duration: number) => void
    isLoading?: boolean
}

const PRESET_DURATIONS = [
    { label: '15초 (숏폼)', value: 15, icon: '⚡', color: 'bg-yellow-500' },
    { label: '30초 (틱톡)', value: 30, icon: '🎵', color: 'bg-pink-500' },
    { label: '60초 (인스타)', value: 60, icon: '📸', color: 'bg-purple-500' },
    { label: '100초 (표준)', value: 100, icon: '🎬', color: 'bg-blue-500' },
    { label: '3분 (유튜브 숏츠)', value: 180, icon: '▶️', color: 'bg-red-500' },
    { label: '5분 (유튜브)', value: 300, icon: '🎥', color: 'bg-green-500' },
    { label: '10분 (롱폼)', value: 600, icon: '📺', color: 'bg-indigo-500' },
]

export default function DurationSelector({ onGenerate, isLoading = false }: DurationSelectorProps) {
    const [selectedDuration, setSelectedDuration] = useState(60)
    const [customDuration, setCustomDuration] = useState('')
    const [showCustom, setShowCustom] = useState(false)

    const handleGenerate = () => {
        const duration = showCustom && customDuration
            ? parseInt(customDuration)
            : selectedDuration

        if (duration > 0 && duration <= 3600) {
            onGenerate(duration)
        } else {
            alert('1초에서 3600초(1시간) 사이의 값을 입력해주세요')
        }
    }

    return (
        <div className="space-y-4">
            {/* 헤더 */}
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold flex items-center gap-2">
                    <Clock className="w-5 h-5 text-purple-400" />
                    영상 분량 선택
                </h3>
                <button
                    onClick={() => setShowCustom(!showCustom)}
                    className="text-sm text-purple-400 hover:text-purple-300 transition-colors"
                >
                    {showCustom ? '프리셋 선택' : '직접 입력'}
                </button>
            </div>

            {/* 프리셋 선택 */}
            {!showCustom ? (
                <div className="grid grid-cols-2 gap-2">
                    {PRESET_DURATIONS.map((preset) => (
                        <button
                            key={preset.value}
                            onClick={() => setSelectedDuration(preset.value)}
                            className={`
                p-3 rounded-lg border-2 transition-all text-left
                ${selectedDuration === preset.value
                                    ? 'border-purple-500 bg-purple-500/20'
                                    : 'border-gray-700 bg-[#1a1a1a] hover:border-gray-600'
                                }
              `}
                        >
                            <div className="flex items-center gap-2 mb-1">
                                <span className="text-xl">{preset.icon}</span>
                                <span className={`px-2 py-0.5 rounded text-xs font-semibold text-white ${preset.color}`}>
                                    {preset.value}초
                                </span>
                            </div>
                            <div className="text-sm text-gray-300">{preset.label}</div>
                        </button>
                    ))}
                </div>
            ) : (
                /* 커스텀 입력 */
                <div className="space-y-2">
                    <label className="block text-sm text-gray-300">
                        원하는 분량 (초)
                    </label>
                    <div className="flex items-center gap-2">
                        <input
                            type="number"
                            value={customDuration}
                            onChange={(e) => setCustomDuration(e.target.value)}
                            placeholder="예: 100"
                            min="1"
                            max="3600"
                            className="flex-1 px-4 py-2 bg-[#1a1a1a] border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                        <span className="text-sm text-gray-400">초</span>
                    </div>
                    <p className="text-xs text-gray-500">
                        1초 ~ 3600초(1시간) 사이로 입력하세요
                    </p>
                </div>
            )}

            {/* 예상 정보 */}
            <div className="p-3 bg-[#1a1a1a] border border-gray-700 rounded-lg">
                <div className="text-sm space-y-1">
                    <div className="flex items-center justify-between">
                        <span className="text-gray-400">총 분량</span>
                        <span className="font-semibold text-white">
                            {showCustom && customDuration ? customDuration : selectedDuration}초
                            ({formatDuration(showCustom && customDuration ? parseInt(customDuration) : selectedDuration)})
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-gray-400">예상 블록 수</span>
                        <span className="font-semibold text-purple-400">
                            {estimateBlockCount(showCustom && customDuration ? parseInt(customDuration) : selectedDuration)}개
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-gray-400">예상 글자 수</span>
                        <span className="font-semibold text-blue-400">
                            약 {estimateCharCount(showCustom && customDuration ? parseInt(customDuration) : selectedDuration)}자
                        </span>
                    </div>
                </div>
            </div>

            {/* 생성 버튼 */}
            <button
                onClick={handleGenerate}
                disabled={isLoading || (showCustom && !customDuration)}
                className="w-full px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
            >
                <Sparkles className="w-5 h-5" />
                {isLoading ? '스크립트 생성 중...' : 'AI 스크립트 생성'}
            </button>

            {/* 안내 메시지 */}
            <div className="text-xs text-gray-500 space-y-1">
                <p>💡 AI가 분량에 맞춰 스크립트를 자동 생성합니다</p>
                <p>🎬 콘티 블록도 자동으로 분할되어 편집하기 쉽습니다</p>
            </div>
        </div>
    )
}

function formatDuration(seconds: number): string {
    if (seconds < 60) {
        return `${seconds}초`
    } else if (seconds < 3600) {
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return secs > 0 ? `${mins}분 ${secs}초` : `${mins}분`
    } else {
        const hours = Math.floor(seconds / 3600)
        const mins = Math.floor((seconds % 3600) / 60)
        return mins > 0 ? `${hours}시간 ${mins}분` : `${hours}시간`
    }
}

function estimateBlockCount(seconds: number): number {
    // 평균 블록당 5-8초로 추정
    return Math.ceil(seconds / 6)
}

function estimateCharCount(seconds: number): number {
    // 초당 약 4.5자 (한글 기준)
    return Math.ceil(seconds * 4.5)
}
