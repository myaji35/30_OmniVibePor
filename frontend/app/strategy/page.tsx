'use client'

/**
 * 전략 수립 대시보드 — AI Director가 포맷별 전략 + 콘텐츠 캘린더 자동 생성
 * ISS-007: Phase 5 핵심 UI
 */

import { useState, useCallback } from 'react'
import {
  Sparkles, Target, Calendar, TrendingUp, Loader2, Play, Film,
  FileText, ChevronDown, ChevronRight,
  Zap, BarChart3, Clock, ArrowRight,
} from 'lucide-react'
import AppShell from '@/components/AppShell'

// ── Types ────────────────────────────────────────
interface ChannelStrategy {
  channel: string
  goal: string
  content_type: string
  posting_frequency: string
  key_topics: string[]
  tone: string
  cta: string
  kpi: string
}

interface CalendarItem {
  week: number
  day: string
  channel: string
  content_type: string
  topic: string
  hook: string
  cta: string
  status: string
  estimated_duration?: number
}

interface StrategyResult {
  brand_name: string
  business_goal: string
  target_audience: string
  overall_strategy: string
  channel_strategies: ChannelStrategy[]
  content_calendar: CalendarItem[]
  total_contents: number
  estimated_weekly_hours: number
  generated_at: string
}

// ── Constants ────────────────────────────────────
const FORMATS = [
  { id: 'promo', label: '홍보 영상', icon: <Film className="w-4 h-4" /> },
  { id: 'explainer', label: '설명 영상', icon: <Play className="w-4 h-4" /> },
  { id: 'presentation', label: '프레젠테이션', icon: <FileText className="w-4 h-4" /> },
  { id: 'shorts', label: '숏폼 (60초)', icon: <Zap className="w-4 h-4" /> },
]

const FORMAT_COLORS: Record<string, string> = {
  promo: '#A855F7',
  explainer: '#3B82F6',
  presentation: '#00A1E0',
  shorts: '#F59E0B',
}

const TONES = [
  { value: 'professional', label: '전문적' },
  { value: 'friendly', label: '친근한' },
  { value: 'humorous', label: '유머러스' },
  { value: 'educational', label: '교육적' },
]

const INDUSTRIES = [
  { value: 'general', label: '일반' },
  { value: 'insurance', label: '보험/금융' },
  { value: 'tech', label: '기술/IT' },
  { value: 'education', label: '교육' },
  { value: 'ecommerce', label: '이커머스' },
  { value: 'beauty', label: '뷰티/패션' },
  { value: 'food', label: '식품/외식' },
  { value: 'real_estate', label: '부동산' },
]

export default function StrategyPage() {
  // 입력 상태
  const [brandName, setBrandName] = useState('')
  const [businessGoal, setBusinessGoal] = useState('')
  const [targetAudience, setTargetAudience] = useState('')
  const [industry, setIndustry] = useState('general')
  const [tone, setTone] = useState('professional')
  const [formats, setFormats] = useState(['promo', 'explainer'])
  const [weeks, setWeeks] = useState(4)
  const [budget, setBudget] = useState('medium')

  // 결과 상태
  const [result, setResult] = useState<StrategyResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedWeek, setExpandedWeek] = useState<number | null>(1)

  const toggleFormat = (f: string) => {
    setFormats(prev =>
      prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
    )
  }

  const handleGenerate = useCallback(async (preview = false) => {
    if (!brandName || !businessGoal || !targetAudience) {
      setError('브랜드명, 비즈니스 목표, 타겟 오디언스를 입력하세요.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const endpoint = preview ? '/api/v1/strategy/preview' : '/api/v1/strategy/generate'
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand_name: brandName,
          business_goal: businessGoal,
          target_audience: targetAudience,
          industry,
          tone,
          channels: formats,
          duration_weeks: weeks,
          budget_level: budget,
        }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setResult(data)
      setExpandedWeek(1)
    } catch (e: any) {
      setError(e.message || '전략 생성 실패')
    } finally {
      setLoading(false)
    }
  }, [brandName, businessGoal, targetAudience, industry, tone, formats, weeks, budget])

  // 주차별 캘린더 그룹핑
  const calendarByWeek = result?.content_calendar.reduce<Record<number, CalendarItem[]>>((acc, item) => {
    if (!acc[item.week]) acc[item.week] = []
    acc[item.week].push(item)
    return acc
  }, {}) ?? {}

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto py-8 px-6">
        {/* 헤더 */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-[#6366F1]/10 flex items-center justify-center">
            <Target className="w-5 h-5 text-[#6366F1]" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">전략 수립</h1>
            <p className="text-sm text-white/40">AI Director가 포맷별 전략 + 콘텐츠 캘린더를 자동 생성합니다</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* ── 좌측: 입력 폼 ──────────────── */}
          <div className="lg:col-span-1 space-y-4">
            <div className="rounded-xl bg-[#141414] border border-white/[0.07] p-5 space-y-4">
              <h2 className="text-sm font-bold text-white/60 uppercase tracking-wider">비즈니스 정보</h2>

              {/* 브랜드명 */}
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">브랜드명</label>
                <input value={brandName} onChange={e => setBrandName(e.target.value)}
                  placeholder="예: InsureGraph Pro"
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]" />
              </div>

              {/* 비즈니스 목표 */}
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">비즈니스 목표</label>
                <textarea value={businessGoal} onChange={e => setBusinessGoal(e.target.value)}
                  placeholder="예: 3개월 내 신규 고객 100명 확보"
                  rows={2}
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]" />
              </div>

              {/* 타겟 */}
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">타겟 오디언스</label>
                <input value={targetAudience} onChange={e => setTargetAudience(e.target.value)}
                  placeholder="예: 30~40대 직장인, 보험 관심자"
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]" />
              </div>

              {/* 산업 */}
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">산업</label>
                <select value={industry} onChange={e => setIndustry(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-[#141414] focus:outline-none focus:border-[#6366F1]">
                  {INDUSTRIES.map(i => <option key={i.value} value={i.value}>{i.label}</option>)}
                </select>
              </div>

              {/* 톤 */}
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">톤앤매너</label>
                <div className="flex flex-wrap gap-2">
                  {TONES.map(t => (
                    <button key={t.value} onClick={() => setTone(t.value)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all
                        ${tone === t.value
                          ? 'bg-[#6366F1] text-white'
                          : 'bg-white/[0.05] text-white/40 border border-white/10 hover:text-white/70'
                        }`}>{t.label}</button>
                  ))}
                </div>
              </div>

              {/* 영상 포맷 */}
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">영상 포맷</label>
                <div className="flex flex-wrap gap-2">
                  {FORMATS.map(f => (
                    <button key={f.id} onClick={() => toggleFormat(f.id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all
                        ${formats.includes(f.id)
                          ? 'text-white border'
                          : 'bg-white/[0.05] text-white/30 border border-white/10'
                        }`}
                      style={formats.includes(f.id) ? {
                        background: `${FORMAT_COLORS[f.id]}20`,
                        borderColor: `${FORMAT_COLORS[f.id]}40`,
                        color: FORMAT_COLORS[f.id],
                      } : undefined}
                    >
                      {f.icon} {f.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* 기간 */}
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">기간: {weeks}주</label>
                <input type="range" min={1} max={12} value={weeks}
                  onChange={e => setWeeks(Number(e.target.value))}
                  className="w-full accent-[#6366F1]" />
              </div>

              {/* 에러 */}
              {error && (
                <div className="text-xs text-red-400 bg-red-500/10 px-3 py-2 rounded-lg">{error}</div>
              )}

              {/* 버튼 */}
              <div className="flex gap-2 pt-2">
                <button onClick={() => handleGenerate(true)} disabled={loading}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold
                    bg-white/[0.05] border border-white/10 text-white/50
                    hover:text-white/80 hover:bg-white/[0.08] transition-all disabled:opacity-30">
                  미리보기
                </button>
                <button onClick={() => handleGenerate(false)} disabled={loading}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-bold
                    bg-[#6366F1] text-white hover:bg-[#5558E6] transition-all disabled:opacity-50">
                  {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> 생성 중...</>
                    : <><Sparkles className="w-4 h-4" /> AI 전략 생성</>}
                </button>
              </div>
            </div>
          </div>

          {/* ── 우측: 결과 ──────────────────── */}
          <div className="lg:col-span-2 space-y-4">
            {!result ? (
              <div className="h-96 flex items-center justify-center rounded-xl bg-[#141414] border border-white/[0.07]">
                <div className="text-center text-white/20">
                  <Target className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p className="text-sm">비즈니스 정보를 입력하고 AI 전략을 생성하세요</p>
                </div>
              </div>
            ) : (
              <>
                {/* KPI 카드 */}
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { icon: <Calendar className="w-4 h-4" />, n: `${result.total_contents}개`, l: '총 콘텐츠', c: '#6366F1' },
                    { icon: <Clock className="w-4 h-4" />, n: `${result.estimated_weekly_hours.toFixed(1)}h`, l: '주당 예상 시간', c: '#22C55E' },
                    { icon: <BarChart3 className="w-4 h-4" />, n: `${result.channel_strategies.length}개`, l: '영상 포맷', c: '#00A1E0' },
                  ].map((k, i) => (
                    <div key={i} className="rounded-xl bg-[#141414] border border-white/[0.07] p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span style={{ color: k.c }}>{k.icon}</span>
                        <span className="text-xs text-white/40">{k.l}</span>
                      </div>
                      <div className="text-2xl font-bold text-white">{k.n}</div>
                    </div>
                  ))}
                </div>

                {/* 전체 전략 요약 */}
                <div className="rounded-xl bg-[#141414] border border-white/[0.07] p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Zap className="w-4 h-4 text-[#6366F1]" />
                    <h3 className="text-sm font-bold text-white/70">전체 전략</h3>
                  </div>
                  <p className="text-sm text-white/60 leading-relaxed">{result.overall_strategy}</p>
                </div>

                {/* 포맷별 전략 */}
                <div className="rounded-xl bg-[#141414] border border-white/[0.07] p-5">
                  <h3 className="text-sm font-bold text-white/70 mb-4">포맷별 전략</h3>
                  <div className="space-y-3">
                    {result.channel_strategies.map((cs, i) => (
                      <div key={i} className="rounded-lg bg-white/[0.02] border border-white/[0.05] p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="w-2 h-2 rounded-full" style={{ background: FORMAT_COLORS[cs.channel] || '#6366F1' }} />
                          <span className="text-sm font-bold text-white">{cs.channel.toUpperCase()}</span>
                          <span className="text-xs text-white/30 ml-auto">{cs.posting_frequency}</span>
                        </div>
                        <p className="text-xs text-white/50 mb-2">{cs.goal}</p>
                        <div className="flex flex-wrap gap-1.5">
                          {cs.key_topics.map((t, j) => (
                            <span key={j} className="px-2 py-0.5 rounded text-[10px] bg-white/[0.04] text-white/40 border border-white/[0.07]">{t}</span>
                          ))}
                        </div>
                        <div className="mt-2 text-[11px] text-white/30">KPI: {cs.kpi}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 콘텐츠 캘린더 */}
                <div className="rounded-xl bg-[#141414] border border-white/[0.07] p-5">
                  <h3 className="text-sm font-bold text-white/70 mb-4">콘텐츠 캘린더</h3>
                  <div className="space-y-2">
                    {Object.entries(calendarByWeek).map(([week, items]) => {
                      const w = Number(week)
                      const isExpanded = expandedWeek === w
                      return (
                        <div key={w} className="rounded-lg border border-white/[0.05] overflow-hidden">
                          <button onClick={() => setExpandedWeek(isExpanded ? null : w)}
                            className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/[0.02] transition-colors">
                            {isExpanded ? <ChevronDown className="w-3.5 h-3.5 text-white/30" /> : <ChevronRight className="w-3.5 h-3.5 text-white/30" />}
                            <span className="text-sm font-semibold text-white">Week {w}</span>
                            <span className="text-xs text-white/30 ml-auto">{items.length}개 콘텐츠</span>
                          </button>
                          {isExpanded && (
                            <div className="px-4 pb-3 space-y-2">
                              {items.map((item, j) => (
                                <div key={j} className="flex items-center gap-3 py-2 border-t border-white/[0.03]">
                                  <span className="text-xs font-mono text-white/25 w-6">{item.day}</span>
                                  <span className="w-2 h-2 rounded-full flex-shrink-0"
                                    style={{ background: FORMAT_COLORS[item.channel] || '#6366F1' }} />
                                  <span className="text-xs text-white/40 w-16">{item.channel}</span>
                                  <span className="text-xs text-white/60 flex-1">{item.topic}</span>
                                  <span className="text-[10px] text-white/20 truncate max-w-[200px]">"{item.hook}"</span>
                                  {item.estimated_duration && (
                                    <span className="text-[10px] font-mono text-white/20">{item.estimated_duration}s</span>
                                  )}
                                  <button className="px-2 py-0.5 rounded text-[10px] bg-[#6366F1]/10 text-[#6366F1] border border-[#6366F1]/20 hover:bg-[#6366F1]/20 transition-colors">
                                    <ArrowRight className="w-3 h-3" />
                                  </button>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
