'use client'

import React, { useState, useEffect } from 'react'
import { Film, Folder, Clock, TrendingUp, Plus, Play, Bell, ArrowRight, Loader2 } from 'lucide-react'
import AppShell from '@/components/AppShell'
import Link from 'next/link'

// ── SVG 차트 (다크 테마) ──────────────────────────────────────────────────────
function PerformanceChart({ period, totalVideos, activeCampaigns }: {
  period: '7' | '30' | '90'
  totalVideos: number
  activeCampaigns: number
}) {
  const days = parseInt(period)
  const chartData = Array.from({ length: days }, (_, i) => {
    const base = Math.max(1, Math.floor(totalVideos / days))
    return { day: i + 1, videos: Math.max(0, Math.round(base + Math.sin(i * 0.8) * 2 + Math.random() * 3)) }
  })
  const maxV = Math.max(...chartData.map((d) => d.videos), 1)
  const W = 560, H = 180, PL = 36, PB = 24
  const pw = W - PL - 12, ph = H - PB - 12

  const pts = chartData.map((d, i) => `${PL + (i / (days - 1)) * pw},${12 + ph - (d.videos / maxV) * ph}`)
  const area = [`${PL},${12 + ph}`, ...pts, `${PL + pw},${12 + ph}`].join(' ')

  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} className="min-w-[280px]">
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#a855f7" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0, 0.25, 0.5, 0.75, 1].map((r) => {
        const y = 12 + ph - r * ph
        return (
          <g key={r}>
            <line x1={PL} y1={y} x2={W - 12} y2={y} stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
            <text x={PL - 4} y={y + 4} textAnchor="end" fontSize="9" fill="rgba(255,255,255,0.2)">{Math.round(maxV * r)}</text>
          </g>
        )
      })}
      <polygon points={area} fill="url(#areaGrad)" />
      <polyline points={pts.join(' ')} fill="none" stroke="#a855f7" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
      {chartData.map((d, i) => {
        const x = PL + (i / (days - 1)) * pw
        const y = 12 + ph - (d.videos / maxV) * ph
        return <circle key={i} cx={x} cy={y} r="2.5" fill="#a855f7" stroke="rgba(168,85,247,0.3)" strokeWidth="4" />
      })}
    </svg>
  )
}

interface Campaign {
  id: number
  name: string
  status: string
  platform?: string
  content_count?: number
  created_at?: string
}

interface Stats {
  totalVideos: number
  activeCampaigns: number
  avgRenderTime: string
  videoGrowth: string
  campaignsNeedAttention: number
}

const CARD = 'rounded-2xl border'
const CARD_S = { background: 'rgba(22,25,35,0.9)', borderColor: 'rgba(255,255,255,0.10)' }

function SLabel({ children }: { children: React.ReactNode }) {
  return <p className="text-[10px] font-black text-white/45 uppercase tracking-widest mb-3">{children}</p>
}

export default function DashboardPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [chartPeriod, setChartPeriod] = useState<'7' | '30' | '90'>('7')
  const [stats, setStats] = useState<Stats>({
    totalVideos: 0, activeCampaigns: 0, avgRenderTime: '0m', videoGrowth: '+0%', campaignsNeedAttention: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/campaigns')
      .then((r) => r.ok ? r.json() : { campaigns: [] })
      .then((data) => {
        const list: Campaign[] = data.campaigns || []
        setCampaigns(list)
        const totalVideos = list.reduce((s, c) => s + (c.content_count || 0), 0)
        const activeCampaigns = list.filter((c) => c.status === 'active').length
        setStats({
          totalVideos, activeCampaigns,
          avgRenderTime: '1.8m',
          videoGrowth: totalVideos > 100 ? '+12%' : '+5%',
          campaignsNeedAttention: list.filter((c) => c.status === 'active' && (c.content_count || 0) < 3).length,
        })
      })
      .catch(() => {
        // 백엔드 미연결 시 데모 데이터
        setCampaigns([])
        setStats({ totalVideos: 0, activeCampaigns: 0, avgRenderTime: '—', videoGrowth: '—', campaignsNeedAttention: 0 })
      })
      .finally(() => setLoading(false))
  }, [])

  const KPI_ITEMS = [
    { label: '총 영상 수', value: stats.totalVideos.toString(), sub: `${stats.videoGrowth} this month`, icon: Film, color: '#a855f7', glow: 'rgba(168,85,247,0.15)' },
    { label: '활성 캠페인', value: stats.activeCampaigns.toString(), sub: stats.campaignsNeedAttention > 0 ? `${stats.campaignsNeedAttention}개 주의 필요` : '모두 정상', icon: Folder, color: '#34d399', glow: 'rgba(52,211,153,0.12)' },
    { label: '평균 렌더 시간', value: stats.avgRenderTime, sub: '-15% 향상', icon: Clock, color: '#60a5fa', glow: 'rgba(96,165,250,0.12)' },
  ]

  return (
    <AppShell
      title="대시보드"
      subtitle="캠페인 및 영상 생성 현황"
      actions={
        <Link href="/studio"
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all active:scale-95"
          style={{ background: 'linear-gradient(135deg, #a855f7, #6366f1)', boxShadow: '0 0 16px rgba(168,85,247,0.3)' }}>
          <Plus className="w-3.5 h-3.5" />
          새 캠페인
        </Link>
      }
    >
      {loading ? (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
        </div>
      ) : (
        <div className="space-y-6">

          {/* ── KPI Cards ── */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {KPI_ITEMS.map(({ label, value, sub, icon: Icon, color, glow }) => (
              <div key={label} className={`${CARD} p-5 relative overflow-hidden`} style={CARD_S}>
                <div className="absolute inset-0 rounded-2xl pointer-events-none"
                  style={{ background: `radial-gradient(ellipse at top left, ${glow} 0%, transparent 65%)` }} />
                <div className="relative flex items-start justify-between">
                  <div>
                    <p className="text-xs text-white/55 mb-2">{label}</p>
                    <p className="text-3xl font-black font-mono" style={{ color }}>{value}</p>
                    <p className="text-[11px] text-white/50 mt-1.5">{sub}</p>
                  </div>
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
                    style={{ background: `${glow}`, border: `1px solid ${color}25` }}>
                    <Icon className="w-4 h-4" style={{ color }} />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* ── 2열 레이아웃: 캠페인 목록 + 사이드바 ── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* 캠페인 목록 */}
            <div className="lg:col-span-2 space-y-4">

              {/* 퍼포먼스 차트 */}
              <div className={`${CARD} p-5`} style={CARD_S}>
                <div className="flex items-center justify-between mb-4">
                  <SLabel>퍼포먼스 오버뷰</SLabel>
                  <select
                    value={chartPeriod}
                    onChange={(e) => setChartPeriod(e.target.value as '7' | '30' | '90')}
                    className="text-xs text-white/40 rounded-lg px-2.5 py-1.5 focus:outline-none"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                  >
                    <option value="7">최근 7일</option>
                    <option value="30">최근 30일</option>
                    <option value="90">최근 90일</option>
                  </select>
                </div>
                <PerformanceChart period={chartPeriod} totalVideos={stats.totalVideos} activeCampaigns={stats.activeCampaigns} />
              </div>

              {/* 최근 캠페인 */}
              <div className={`${CARD} p-5`} style={CARD_S}>
                <div className="flex items-center justify-between mb-4">
                  <SLabel>최근 캠페인</SLabel>
                  <Link href="/campaigns" className="text-[11px] text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1">
                    전체 보기 <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>

                {campaigns.length === 0 ? (
                  <div className="py-10 text-center">
                    <p className="text-sm text-white/45 mb-4">캠페인이 없습니다.</p>
                    <Link href="/studio"
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all"
                      style={{ background: 'rgba(168,85,247,0.15)', border: '1px solid rgba(168,85,247,0.3)', color: '#c084fc' }}>
                      <Plus className="w-3.5 h-3.5" />
                      첫 캠페인 만들기
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {campaigns.slice(0, 5).map((c) => {
                      const pct = Math.min(100, Math.round(((c.content_count || 0) / 10) * 100))
                      const isActive = c.status === 'active'
                      const isDone = c.status === 'completed'
                      return (
                        <div key={c.id} className="flex items-center gap-4 p-3 rounded-xl transition-all hover:bg-white/[0.03]"
                          style={{ border: '1px solid rgba(255,255,255,0.09)' }}>
                          <div className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0"
                            style={{ background: 'rgba(168,85,247,0.12)', border: '1px solid rgba(168,85,247,0.2)' }}>
                            <Folder className="w-4 h-4 text-purple-400" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-white/85 truncate">{c.name}</p>
                            <p className="text-[11px] text-white/50">{c.content_count || 0}/10 videos · {c.platform || 'Multi'}</p>
                          </div>
                          <div className="flex items-center gap-3 shrink-0">
                            <div className="w-20">
                              <div className="h-1 rounded-full" style={{ background: 'rgba(255,255,255,0.08)' }}>
                                <div className="h-full rounded-full transition-all"
                                  style={{ width: `${pct}%`, background: isDone ? '#34d399' : isActive ? '#a855f7' : '#475569' }} />
                              </div>
                              <p className="text-[10px] text-white/45 mt-1 text-right font-mono">{pct}%</p>
                            </div>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                              style={{
                                color: isDone ? '#34d399' : isActive ? '#a855f7' : '#64748b',
                                background: isDone ? 'rgba(52,211,153,0.1)' : isActive ? 'rgba(168,85,247,0.1)' : 'rgba(100,116,139,0.1)',
                              }}>
                              {isDone ? '완료' : isActive ? '진행 중' : '초안'}
                            </span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* ── 우측 사이드바 ── */}
            <div className="space-y-4">

              {/* 빠른 액션 */}
              <div className={`${CARD} p-5`} style={CARD_S}>
                <SLabel>빠른 액션</SLabel>
                <div className="space-y-2">
                  {[
                    { href: '/studio', label: '새 영상 제작', icon: Play, color: '#a855f7' },
                    { href: '/upload', label: '파일 업로드', icon: Film, color: '#6366f1' },
                    { href: '/audio', label: 'Zero-Fault 오디오', icon: TrendingUp, color: '#3b82f6' },
                    { href: '/writer', label: 'AI 스크립트 생성', icon: Bell, color: '#22d3ee' },
                  ].map(({ href, label, icon: Icon, color }) => (
                    <Link key={href} href={href}
                      className="flex items-center gap-3 p-3 rounded-xl transition-all hover:bg-white/[0.04]"
                      style={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                      <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                        style={{ background: `${color}18`, border: `1px solid ${color}25` }}>
                        <Icon className="w-3.5 h-3.5" style={{ color }} />
                      </div>
                      <span className="text-xs font-semibold text-white/75">{label}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-white/40 ml-auto" />
                    </Link>
                  ))}
                </div>
              </div>

              {/* 최근 활동 */}
              <div className={`${CARD} p-5`} style={CARD_S}>
                <SLabel>최근 활동</SLabel>
                {campaigns.length === 0 ? (
                  <p className="text-xs text-white/45 text-center py-4">활동 내역이 없습니다</p>
                ) : (
                  <div className="space-y-3">
                    {campaigns.slice(0, 4).map((c) => (
                      <div key={c.id} className="flex items-start gap-2.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-purple-500/60 mt-1.5 shrink-0" />
                        <div>
                          <p className="text-xs text-white/75">{c.status === 'completed' ? '캠페인 완료' : c.status === 'active' ? '캠페인 진행 중' : '캠페인 생성'}</p>
                          <p className="text-[11px] text-white/45 mt-0.5 truncate">{c.name}</p>
                          {c.created_at && <p className="text-[10px] text-white/40 mt-0.5">{new Date(c.created_at).toLocaleDateString('ko')}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  )
}
