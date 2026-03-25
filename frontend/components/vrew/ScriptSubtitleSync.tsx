'use client'

/**
 * ScriptSubtitleSync — 씬(ScriptBlock) ↔ 자막 동기화 편집기 (경로 A)
 *
 * 기능:
 * - 씬별 자막 토큰 목록 표시
 * - 씬 분할 / 병합
 * - 자막 스타일 프리셋 선택
 * - 백엔드 API로 Whisper 타이밍 재요청
 */

import { useState, useCallback } from 'react'
import { Scissors, Merge, RefreshCw, ChevronDown } from 'lucide-react'
import SubtitleTimeline, { SubtitleToken } from './SubtitleTimeline'

export interface ScriptBlock {
  id:       string
  type:     'hook' | 'body' | 'cta' | 'custom'
  text:     string
  startMs:  number
  endMs:    number
  audioUrl: string
}

export type SubtitleStyle = 'default' | 'bold-center' | 'lower-third' | 'karaoke'

const STYLE_PRESETS: { value: SubtitleStyle; label: string; preview: string }[] = [
  { value: 'default',     label: '기본',         preview: '중앙 / 화이트 / fade' },
  { value: 'bold-center', label: '볼드 중앙',    preview: '중앙 / 대형 / 볼드' },
  { value: 'lower-third', label: '하단 자막',    preview: '하단 L자형 / 뉴스체' },
  { value: 'karaoke',     label: '가라오케',     preview: '단어별 하이라이트' },
]

interface ScriptSubtitleSyncProps {
  blocks:        ScriptBlock[]
  subtitlesMap:  Record<string, SubtitleToken[]>  // blockId → tokens
  totalDuration: number
  onSubtitlesChange: (blockId: string, tokens: SubtitleToken[]) => void
  onStyleChange:     (blockId: string, style: SubtitleStyle)    => void
  onRequestWhisper?: (blockId: string) => Promise<void>
}

export default function ScriptSubtitleSync({
  blocks,
  subtitlesMap,
  totalDuration,
  onSubtitlesChange,
  onStyleChange,
  onRequestWhisper,
}: ScriptSubtitleSyncProps) {
  const [expandedBlock, setExpandedBlock] = useState<string | null>(blocks[0]?.id ?? null)
  const [styleMap,      setStyleMap]      = useState<Record<string, SubtitleStyle>>({})
  const [loadingWsp,    setLoadingWsp]    = useState<string | null>(null)

  const handleWhisper = useCallback(async (blockId: string) => {
    if (!onRequestWhisper) return
    setLoadingWsp(blockId)
    try {
      await onRequestWhisper(blockId)
    } finally {
      setLoadingWsp(null)
    }
  }, [onRequestWhisper])

  const handleStyleChange = useCallback((blockId: string, style: SubtitleStyle) => {
    setStyleMap(prev => ({ ...prev, [blockId]: style }))
    onStyleChange(blockId, style)
  }, [onStyleChange])

  const BLOCK_TYPE_COLORS: Record<string, string> = {
    hook:   'text-[#00FF88] border-[#00FF88]/30 bg-[#00FF88]/10',
    body:   'text-white/70 border-white/10 bg-white/5',
    cta:    'text-[#00CFFF] border-[#00CFFF]/30 bg-[#00CFFF]/10',
    custom: 'text-[#A855F7] border-[#A855F7]/30 bg-[#A855F7]/10',
  }

  return (
    <div className="space-y-2">
      {blocks.map(block => {
        const isExpanded = expandedBlock === block.id
        const tokens     = subtitlesMap[block.id] ?? []
        const blockDur   = block.endMs - block.startMs
        const style      = styleMap[block.id] ?? 'default'
        const typeColor  = BLOCK_TYPE_COLORS[block.type] ?? BLOCK_TYPE_COLORS.custom

        return (
          <div key={block.id}
            className="rounded-xl border border-white/[0.07] bg-[#141414] overflow-hidden">
            {/* 씬 헤더 */}
            <button
              className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-white/[0.03] transition-colors"
              onClick={() => setExpandedBlock(isExpanded ? null : block.id)}
            >
              {/* 타입 뱃지 */}
              <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase
                tracking-widest border ${typeColor}`}>
                {block.type}
              </span>

              {/* 씬 텍스트 미리보기 */}
              <span className="flex-1 text-[12px] text-white/60 truncate">{block.text}</span>

              {/* 자막 토큰 수 */}
              <span className="text-[10px] font-mono text-white/30">
                {tokens.length}개 토큰
              </span>

              {/* 시간 */}
              <span className="text-[10px] font-mono text-white/30">
                {(blockDur / 1000).toFixed(1)}s
              </span>

              <ChevronDown className={`w-3.5 h-3.5 text-white/30 transition-transform
                ${isExpanded ? 'rotate-180' : ''}`} />
            </button>

            {/* 확장 영역 */}
            {isExpanded && (
              <div className="px-4 pb-4 space-y-3 border-t border-white/[0.05]">
                {/* 도구 버튼 */}
                <div className="flex items-center gap-2 pt-3">
                  {/* Whisper 재분석 */}
                  <button
                    disabled={!!loadingWsp}
                    onClick={() => handleWhisper(block.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px]
                      font-semibold bg-white/[0.05] border border-white/10 text-white/50
                      hover:text-white/80 hover:bg-white/[0.08] transition-all
                      disabled:opacity-40"
                  >
                    <RefreshCw className={`w-3 h-3 ${loadingWsp === block.id ? 'animate-spin' : ''}`} />
                    Whisper 재분석
                  </button>

                  {/* 씬 분할 */}
                  <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px]
                    font-semibold bg-white/[0.05] border border-white/10 text-white/50
                    hover:text-white/80 hover:bg-white/[0.08] transition-all">
                    <Scissors className="w-3 h-3" />
                    씬 분할
                  </button>

                  {/* 스타일 프리셋 */}
                  <div className="ml-auto flex items-center gap-2">
                    <span className="text-[10px] text-white/30">스타일:</span>
                    <select
                      value={style}
                      onChange={e => handleStyleChange(block.id, e.target.value as SubtitleStyle)}
                      className="text-[11px] bg-white/[0.05] border border-white/10
                        text-white/60 rounded-md px-2 py-1 outline-none
                        focus:border-purple-500/50 transition-colors"
                    >
                      {STYLE_PRESETS.map(p => (
                        <option key={p.value} value={p.value}>{p.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* 타임라인 */}
                {tokens.length > 0 ? (
                  <SubtitleTimeline
                    audioUrl={block.audioUrl}
                    subtitles={tokens}
                    duration={blockDur}
                    onChange={updated => onSubtitlesChange(block.id, updated)}
                  />
                ) : (
                  <div className="h-20 flex items-center justify-center rounded-lg
                    border border-dashed border-white/10 text-[12px] text-white/30">
                    자막 토큰 없음 — Whisper 재분석을 실행하세요
                  </div>
                )}

                {/* 토큰 목록 미니뷰 */}
                {tokens.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {tokens.map((t, i) => (
                      <span key={i}
                        className="px-2 py-0.5 rounded text-[10px] font-mono
                          bg-white/[0.04] border border-white/[0.07] text-white/50">
                        {t.text}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
