'use client'

import { ScriptBlock } from '@/lib/blocks/types'

interface BlockEffectsEditorProps {
    block: ScriptBlock | null
    onUpdate: (effects: ScriptBlock['effects']) => void
}

export default function BlockEffectsEditor({ block, onUpdate }: BlockEffectsEditorProps) {
    if (!block) {
        return (
            <div className="p-4 bg-[#1a1a1a] rounded-lg border border-gray-700">
                <p className="text-sm text-gray-500 text-center">
                    블록을 선택하면 효과를 편집할 수 있습니다
                </p>
            </div>
        )
    }

    const toggleEffect = (key: keyof ScriptBlock['effects'], value?: any) => {
        onUpdate({
            ...block.effects,
            [key]: value !== undefined ? value : !block.effects[key]
        })
    }

    return (
        <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                </svg>
                블록 효과
            </h3>

            {/* 페이드 효과 */}
            <div className="space-y-2">
                <p className="text-xs text-gray-400 font-medium">페이드</p>
                <div className="grid grid-cols-2 gap-2">
                    <label className="flex items-center gap-2 p-2 bg-[#1a1a1a] rounded-lg cursor-pointer hover:bg-gray-800 transition-colors">
                        <input
                            type="checkbox"
                            checked={block.effects.fadeIn || false}
                            onChange={() => toggleEffect('fadeIn')}
                            className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="text-sm text-gray-300">페이드인</span>
                    </label>
                    <label className="flex items-center gap-2 p-2 bg-[#1a1a1a] rounded-lg cursor-pointer hover:bg-gray-800 transition-colors">
                        <input
                            type="checkbox"
                            checked={block.effects.fadeOut || false}
                            onChange={() => toggleEffect('fadeOut')}
                            className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="text-sm text-gray-300">페이드아웃</span>
                    </label>
                </div>
            </div>

            {/* 줌 효과 */}
            <div className="space-y-2">
                <p className="text-xs text-gray-400 font-medium">줌</p>
                <div className="grid grid-cols-2 gap-2">
                    <label className="flex items-center gap-2 p-2 bg-[#1a1a1a] rounded-lg cursor-pointer hover:bg-gray-800 transition-colors">
                        <input
                            type="checkbox"
                            checked={block.effects.zoomIn || false}
                            onChange={() => toggleEffect('zoomIn')}
                            className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="text-sm text-gray-300">줌인</span>
                    </label>
                    <label className="flex items-center gap-2 p-2 bg-[#1a1a1a] rounded-lg cursor-pointer hover:bg-gray-800 transition-colors">
                        <input
                            type="checkbox"
                            checked={block.effects.zoomOut || false}
                            onChange={() => toggleEffect('zoomOut')}
                            className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="text-sm text-gray-300">줌아웃</span>
                    </label>
                </div>
            </div>

            {/* 슬라이드 효과 */}
            <div className="space-y-2">
                <p className="text-xs text-gray-400 font-medium">슬라이드</p>
                <select
                    value={block.effects.slide || ''}
                    onChange={(e) => toggleEffect('slide', e.target.value || null)}
                    className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-purple-500"
                >
                    <option value="">없음</option>
                    <option value="left">왼쪽에서</option>
                    <option value="right">오른쪽에서</option>
                    <option value="up">위에서</option>
                    <option value="down">아래에서</option>
                </select>
            </div>

            {/* 강조 효과 */}
            <div className="space-y-2">
                <p className="text-xs text-gray-400 font-medium">기타</p>
                <label className="flex items-center gap-2 p-2 bg-[#1a1a1a] rounded-lg cursor-pointer hover:bg-gray-800 transition-colors">
                    <input
                        type="checkbox"
                        checked={block.effects.highlight || false}
                        onChange={() => toggleEffect('highlight')}
                        className="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="text-sm text-gray-300">강조</span>
                </label>
            </div>

            {/* 미리보기 */}
            <div className="p-3 bg-[#0a0a0a] rounded-lg border border-gray-700">
                <p className="text-xs text-gray-400 mb-2">적용된 효과</p>
                <div className="flex flex-wrap gap-1">
                    {Object.entries(block.effects).filter(([_, v]) => v).length === 0 ? (
                        <span className="text-xs text-gray-500">없음</span>
                    ) : (
                        <>
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
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}
