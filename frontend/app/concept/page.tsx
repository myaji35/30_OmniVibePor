'use client'

/**
 * 컨셉 기획기 — 전략 → 컨셉 → 스크립트 → 스토리보드 3단계 자동 흐름
 * ISS-008: Phase 5.2
 *
 * URL: /concept?topic=...&channel=...&brand=...
 * 또는 직접 입력
 */

import { useState, useCallback, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import {
  Lightbulb, FileText, Film, ArrowRight, Loader2, Sparkles,
  ChevronDown, ChevronRight, Copy, Check, GripVertical,
} from 'lucide-react'
import AppShell from '@/components/AppShell'

// ── Types ────────────────────────────────────────
interface StoryboardCard {
  id: string
  type: 'hook' | 'body' | 'cta'
  text: string
  visual: string
  duration: number
  notes: string
}

type Phase = 'concept' | 'script' | 'storyboard'

// ── Component ────────────────────────────────────
export default function ConceptPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-96 text-white/30">로딩 중...</div>}>
      <ConceptContent />
    </Suspense>
  )
}

function ConceptContent() {
  const searchParams = useSearchParams()

  // URL params (전략 페이지에서 넘어온 경우)
  const paramTopic = searchParams.get('topic') || ''
  const paramChannel = searchParams.get('channel') || ''
  const paramBrand = searchParams.get('brand') || ''

  // Phase 상태
  const [phase, setPhase] = useState<Phase>('concept')

  // Phase 1: 컨셉
  const [topic, setTopic] = useState(paramTopic)
  const [channel, setChannel] = useState(paramChannel || 'youtube')
  const [brand, setBrand] = useState(paramBrand)
  const [audience, setAudience] = useState('')
  const [angle, setAngle] = useState('')  // AI가 생성하는 차별화 앵글

  // Phase 2: 스크립트
  const [script, setScript] = useState('')
  const [hook, setHook] = useState('')
  const [cta, setCta] = useState('')
  const [estimatedDuration, setEstimatedDuration] = useState(0)

  // Phase 3: 스토리보드
  const [cards, setCards] = useState<StoryboardCard[]>([])
  const [draggedIdx, setDraggedIdx] = useState<number | null>(null)

  // UI 상태
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  // ── Phase 1 → 2: 컨셉 → 스크립트 생성 ──────────
  const handleGenerateScript = useCallback(async () => {
    if (!topic) return
    setLoading(true)

    try {
      const res = await fetch('/api/writer-generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          platform: channel,
          target_duration: channel === 'tiktok' ? 30 : channel === 'instagram' ? 60 : 120,
          campaign_name: brand,
        }),
      })

      if (res.ok) {
        const data = await res.json()
        setScript(data.script || data.result?.script || '')
        setHook(data.hook || data.result?.hook || '')
        setCta(data.cta || data.result?.cta || '')
        setEstimatedDuration(data.estimated_duration || 60)
        setAngle(data.angle || `${topic}에 대한 ${channel} 최적화 콘텐츠`)
      } else {
        // Fallback: 템플릿 스크립트
        const tpl = generateFallbackScript(topic, channel, brand)
        setScript(tpl.script)
        setHook(tpl.hook)
        setCta(tpl.cta)
        setEstimatedDuration(tpl.duration)
        setAngle(`${topic} — ${channel} 최적화`)
      }

      setPhase('script')
    } catch {
      const tpl = generateFallbackScript(topic, channel, brand)
      setScript(tpl.script)
      setHook(tpl.hook)
      setCta(tpl.cta)
      setEstimatedDuration(tpl.duration)
      setAngle(`${topic} — ${channel} 최적화`)
      setPhase('script')
    } finally {
      setLoading(false)
    }
  }, [topic, channel, brand])

  // ── Phase 2 → 3: 스크립트 → 스토리보드 ──────────
  const handleGenerateStoryboard = useCallback(() => {
    if (!script) return

    const lines = script.split('\n').filter(l => l.trim())
    const hookLines = lines.slice(0, Math.max(1, Math.floor(lines.length * 0.2)))
    const bodyLines = lines.slice(hookLines.length, -Math.max(1, Math.floor(lines.length * 0.15)))
    const ctaLines = lines.slice(-Math.max(1, Math.floor(lines.length * 0.15)))

    const newCards: StoryboardCard[] = [
      {
        id: 'card-hook',
        type: 'hook',
        text: hookLines.join('\n'),
        visual: '강렬한 텍스트 + 배경 이미지',
        duration: Math.round(estimatedDuration * 0.15),
        notes: hook || '첫 3초 주목',
      },
      ...bodyLines.map((line, i) => ({
        id: `card-body-${i}`,
        type: 'body' as const,
        text: line,
        visual: `씬 ${i + 1}: 핵심 비주얼`,
        duration: Math.round(estimatedDuration * 0.65 / Math.max(bodyLines.length, 1)),
        notes: '',
      })),
      {
        id: 'card-cta',
        type: 'cta',
        text: ctaLines.join('\n'),
        visual: 'CTA 버튼 + 로고',
        duration: Math.round(estimatedDuration * 0.2),
        notes: cta || '행동 유도',
      },
    ]

    setCards(newCards)
    setPhase('storyboard')
  }, [script, hook, cta, estimatedDuration])

  // ── DnD 카드 재정렬 ────────────────────────────
  const handleDragStart = (idx: number) => setDraggedIdx(idx)
  const handleDragOver = (e: React.DragEvent, idx: number) => {
    e.preventDefault()
    if (draggedIdx === null || draggedIdx === idx) return
    const newCards = [...cards]
    const [removed] = newCards.splice(draggedIdx, 1)
    newCards.splice(idx, 0, removed)
    setCards(newCards)
    setDraggedIdx(idx)
  }
  const handleDragEnd = () => setDraggedIdx(null)

  // ── 스크립트 복사 ──────────────────────────────
  const handleCopy = () => {
    navigator.clipboard.writeText(script)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // ── 콘텐츠 생산 트리거 ─────────────────────────
  const handleProduce = (type: 'video' | 'presentation') => {
    const params = new URLSearchParams({
      script: script.slice(0, 500),
      channel,
      brand,
      type,
    })
    window.location.href = `/production?${params.toString()}`
  }

  const PHASE_STEPS = [
    { id: 'concept', label: '컨셉', icon: <Lightbulb className="w-4 h-4" /> },
    { id: 'script', label: '스크립트', icon: <FileText className="w-4 h-4" /> },
    { id: 'storyboard', label: '스토리보드', icon: <Film className="w-4 h-4" /> },
  ]

  const TYPE_COLORS: Record<string, string> = {
    hook: '#00FF88',
    body: '#3B82F6',
    cta: '#F59E0B',
  }

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto py-8 px-6">
        {/* 헤더 */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
            <Lightbulb className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">컨셉 기획</h1>
            <p className="text-sm text-white/40">전략 → 컨셉 → 스크립트 → 스토리보드</p>
          </div>
        </div>

        {/* 단계 표시 */}
        <div className="flex items-center gap-2 mb-8">
          {PHASE_STEPS.map((step, i) => (
            <div key={step.id} className="flex items-center gap-2">
              <button
                onClick={() => {
                  if (step.id === 'concept') setPhase('concept')
                  else if (step.id === 'script' && script) setPhase('script')
                  else if (step.id === 'storyboard' && cards.length) setPhase('storyboard')
                }}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all
                  ${phase === step.id
                    ? 'bg-[#6366F1] text-white'
                    : step.id === 'concept' || (step.id === 'script' && script) || (step.id === 'storyboard' && cards.length)
                      ? 'bg-white/[0.05] text-white/50 hover:text-white/80'
                      : 'bg-white/[0.02] text-white/20 cursor-not-allowed'
                  }`}
              >
                {step.icon} {step.label}
              </button>
              {i < PHASE_STEPS.length - 1 && <ArrowRight className="w-4 h-4 text-white/20" />}
            </div>
          ))}
        </div>

        {/* ── Phase 1: 컨셉 입력 ────────────── */}
        {phase === 'concept' && (
          <div className="rounded-xl bg-[#141414] border border-white/[0.07] p-6 space-y-4">
            <h2 className="text-sm font-bold text-white/60 uppercase tracking-wider mb-4">콘텐츠 컨셉</h2>

            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1.5">토픽</label>
              <input value={topic} onChange={e => setTopic(e.target.value)}
                placeholder="예: AI 보험 분석으로 월 100만원 절약하는 방법"
                className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">브랜드</label>
                <input value={brand} onChange={e => setBrand(e.target.value)}
                  placeholder="예: InsureGraph Pro"
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">채널</label>
                <select value={channel} onChange={e => setChannel(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-[#141414] focus:outline-none focus:border-[#6366F1]">
                  <option value="youtube">YouTube</option>
                  <option value="instagram">Instagram</option>
                  <option value="tiktok">TikTok</option>
                  <option value="blog">블로그</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1.5">타겟 오디언스 (선택)</label>
              <input value={audience} onChange={e => setAudience(e.target.value)}
                placeholder="예: 30대 직장인, 보험 신규 가입 고려 중"
                className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]" />
            </div>

            <button onClick={handleGenerateScript} disabled={!topic || loading}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-bold
                bg-[#6366F1] text-white hover:bg-[#5558E6] transition-all disabled:opacity-50">
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> 스크립트 생성 중...</>
                : <><Sparkles className="w-4 h-4" /> AI 스크립트 생성</>}
            </button>
          </div>
        )}

        {/* ── Phase 2: 스크립트 편집 ────────── */}
        {phase === 'script' && (
          <div className="space-y-4">
            {/* 앵글 */}
            {angle && (
              <div className="rounded-lg bg-[#6366F1]/10 border border-[#6366F1]/20 px-4 py-3">
                <span className="text-xs font-bold text-[#6366F1] mr-2">차별화 앵글:</span>
                <span className="text-sm text-white/70">{angle}</span>
              </div>
            )}

            <div className="rounded-xl bg-[#141414] border border-white/[0.07] p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-bold text-white/60 uppercase tracking-wider">스크립트</h2>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-white/30">예상 {estimatedDuration}초</span>
                  <button onClick={handleCopy}
                    className="flex items-center gap-1 px-2 py-1 rounded text-xs text-white/40 hover:text-white/70 transition-colors">
                    {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                    {copied ? '복사됨' : '복사'}
                  </button>
                </div>
              </div>

              <textarea value={script} onChange={e => setScript(e.target.value)}
                rows={12}
                className="w-full px-4 py-3 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] font-mono leading-relaxed
                  placeholder-gray-500 focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1] resize-none" />

              <div className="flex gap-3 mt-4">
                <button onClick={() => setPhase('concept')}
                  className="px-4 py-2.5 rounded-lg text-sm font-semibold bg-white/[0.05] border border-white/10 text-white/50 hover:text-white/80 transition-all">
                  컨셉 수정
                </button>
                <button onClick={handleGenerateStoryboard}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-bold
                    bg-[#6366F1] text-white hover:bg-[#5558E6] transition-all">
                  <Film className="w-4 h-4" /> 스토리보드 생성
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Phase 3: 스토리보드 카드 ──────── */}
        {phase === 'storyboard' && (
          <div className="space-y-4">
            <div className="rounded-xl bg-[#141414] border border-white/[0.07] p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-bold text-white/60 uppercase tracking-wider">스토리보드</h2>
                <span className="text-xs text-white/30">{cards.length}개 카드 · 드래그로 재정렬</span>
              </div>

              <div className="space-y-2">
                {cards.map((card, idx) => (
                  <div key={card.id}
                    draggable
                    onDragStart={() => handleDragStart(idx)}
                    onDragOver={e => handleDragOver(e, idx)}
                    onDragEnd={handleDragEnd}
                    className={`flex gap-3 p-4 rounded-lg border transition-all cursor-move
                      ${draggedIdx === idx ? 'opacity-50 border-[#6366F1]' : 'border-white/[0.06] hover:border-white/[0.12]'}
                      bg-white/[0.02]`}
                  >
                    <GripVertical className="w-4 h-4 text-white/20 mt-1 flex-shrink-0" />

                    <div className="flex-shrink-0 w-16 text-center">
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider"
                        style={{
                          color: TYPE_COLORS[card.type],
                          background: `${TYPE_COLORS[card.type]}15`,
                          border: `1px solid ${TYPE_COLORS[card.type]}30`,
                        }}>
                        {card.type}
                      </span>
                      <div className="text-[10px] font-mono text-white/25 mt-1">{card.duration}s</div>
                    </div>

                    <div className="flex-1 min-w-0">
                      <textarea value={card.text}
                        onChange={e => {
                          const updated = [...cards]
                          updated[idx] = { ...card, text: e.target.value }
                          setCards(updated)
                        }}
                        rows={2}
                        className="w-full px-2 py-1 text-sm text-white/70 bg-transparent border-none outline-none resize-none" />
                    </div>

                    <div className="flex-shrink-0 w-48">
                      <input value={card.visual}
                        onChange={e => {
                          const updated = [...cards]
                          updated[idx] = { ...card, visual: e.target.value }
                          setCards(updated)
                        }}
                        className="w-full px-2 py-1 text-[11px] text-white/40 bg-transparent border-b border-white/[0.06] outline-none"
                        placeholder="비주얼 메모" />
                    </div>
                  </div>
                ))}
              </div>

              {/* 생산 트리거 버튼 */}
              <div className="flex gap-3 mt-6">
                <button onClick={() => setPhase('script')}
                  className="px-4 py-2.5 rounded-lg text-sm font-semibold bg-white/[0.05] border border-white/10 text-white/50 hover:text-white/80 transition-all">
                  스크립트 수정
                </button>
                <button onClick={() => handleProduce('video')}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-bold
                    bg-[#00FF88]/10 border border-[#00FF88]/20 text-[#00FF88] hover:bg-[#00FF88]/20 transition-all">
                  <Film className="w-4 h-4" /> 영상 제작
                </button>
                <button onClick={() => handleProduce('presentation')}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-bold
                    bg-[#00A1E0]/10 border border-[#00A1E0]/20 text-[#00A1E0] hover:bg-[#00A1E0]/20 transition-all">
                  <FileText className="w-4 h-4" /> 프레젠테이션
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  )
}

// ── Fallback 스크립트 생성 (API 없을 때) ─────────
function generateFallbackScript(topic: string, channel: string, brand: string) {
  const dur = channel === 'tiktok' ? 30 : channel === 'instagram' ? 60 : 120
  return {
    script: `[Hook]\n${topic}에 대해 알고 계셨나요?\n\n[Body]\n오늘은 ${brand || '우리'}의 ${topic}에 대해 이야기해보겠습니다.\n이 방법을 사용하면 시간을 절약하고 효율을 높일 수 있습니다.\n구체적인 사례를 통해 알아보겠습니다.\n\n[CTA]\n더 자세한 내용은 프로필 링크에서 확인하세요.\n좋아요와 구독도 부탁드립니다.`,
    hook: `${topic}에 대해 알고 계셨나요?`,
    cta: '프로필 링크에서 확인하세요',
    duration: dur,
  }
}
