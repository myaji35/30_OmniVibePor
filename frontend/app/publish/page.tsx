'use client'

/**
 * 멀티채널 배포 — 예약 발행 + 성과 추적
 * ISS-010: Phase 5.4
 */

import { useState, useCallback, useEffect } from 'react'
import {
  Send, Calendar, BarChart3, Youtube, Instagram, Play, FileText,
  Loader2, CheckCircle, Clock, AlertCircle, TrendingUp, Eye, Heart,
  MessageCircle, Share2, ArrowRight, RefreshCw,
} from 'lucide-react'
import AppShell from '@/components/AppShell'

interface Channel {
  id: string
  name: string
  formats: string[]
  status: string
  api_connected: boolean
  description: string
}

interface PublishItem {
  id: number
  topic: string
  platform: string
  status: string
  publish_date: string
}

const CHANNEL_ICONS: Record<string, React.ReactNode> = {
  youtube: <Youtube className="w-4 h-4" />,
  instagram: <Instagram className="w-4 h-4" />,
  tiktok: <Play className="w-4 h-4" />,
  blog: <FileText className="w-4 h-4" />,
}

const CHANNEL_COLORS: Record<string, string> = {
  youtube: '#FF0000',
  instagram: '#E4405F',
  tiktok: '#00F2EA',
  blog: '#00A1E0',
}

const STATUS_MAP: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  draft: { label: '초안', color: '#706E6B', icon: <FileText className="w-3 h-3" /> },
  scheduled: { label: '예약됨', color: '#F59E0B', icon: <Clock className="w-3 h-3" /> },
  publishing: { label: '발행 중', color: '#3B82F6', icon: <Loader2 className="w-3 h-3 animate-spin" /> },
  published: { label: '발행됨', color: '#22C55E', icon: <CheckCircle className="w-3 h-3" /> },
  failed: { label: '실패', color: '#EF4444', icon: <AlertCircle className="w-3 h-3" /> },
}

export default function PublishPage() {
  const [channels, setChannels] = useState<Channel[]>([])
  const [history, setHistory] = useState<PublishItem[]>([])
  const [loading, setLoading] = useState(true)

  // 배포 폼
  const [title, setTitle] = useState('')
  const [channel, setChannel] = useState('youtube')
  const [contentUrl, setContentUrl] = useState('')
  const [description, setDescription] = useState('')
  const [scheduleAt, setScheduleAt] = useState('')
  const [publishing, setPublishing] = useState(false)
  const [publishResult, setPublishResult] = useState<string | null>(null)

  // 성과 입력
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackId, setFeedbackId] = useState('')
  const [feedbackScore, setFeedbackScore] = useState(7)
  const [feedbackViews, setFeedbackViews] = useState(0)
  const [feedbackLikes, setFeedbackLikes] = useState(0)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [chRes, hRes] = await Promise.all([
        fetch('/api/v1/publish/channels'),
        fetch('/api/v1/publish/history?limit=20'),
      ])
      if (chRes.ok) setChannels((await chRes.json()).channels || [])
      if (hRes.ok) setHistory((await hRes.json()).items || [])
    } catch { /* ignore */ }
    setLoading(false)
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const handlePublish = useCallback(async () => {
    if (!title || !contentUrl) return
    setPublishing(true)
    setPublishResult(null)

    try {
      const res = await fetch('/api/v1/publish/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title, channel, content_url: contentUrl,
          description: description || undefined,
          schedule_at: scheduleAt || undefined,
          tags: [],
        }),
      })
      const data = await res.json()
      setPublishResult(data.message || '발행 완료')
      fetchData()
    } catch (e: any) {
      setPublishResult(`실패: ${e.message}`)
    } finally {
      setPublishing(false)
    }
  }, [title, channel, contentUrl, description, scheduleAt, fetchData])

  const handleFeedback = useCallback(async () => {
    try {
      await fetch('/api/v1/publish/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content_id: feedbackId, channel,
          views: feedbackViews, likes: feedbackLikes,
          comments: 0, shares: 0,
          engagement_rate: feedbackViews > 0 ? (feedbackLikes / feedbackViews) * 100 : 0,
          watch_time_avg: 0, score: feedbackScore,
          collected_at: new Date().toISOString(),
        }),
      })
      setShowFeedback(false)
      setPublishResult('성과 데이터가 GraphRAG에 저장되었습니다')
    } catch { /* ignore */ }
  }, [feedbackId, channel, feedbackViews, feedbackLikes, feedbackScore])

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto py-8 px-6">
        {/* 헤더 */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-[#22C55E]/10 flex items-center justify-center">
            <Send className="w-5 h-5 text-[#22C55E]" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">멀티채널 배포</h1>
            <p className="text-sm text-white/40">예약 발행 + 성과 추적 → GraphRAG 피드백 루프</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* ── 좌측: 배포 폼 ──────────────── */}
          <div className="lg:col-span-1 space-y-4">
            <div className="rounded-xl bg-[#141414] border border-white/[0.07] p-5 space-y-4">
              <h2 className="text-sm font-bold text-white/60 uppercase tracking-wider">콘텐츠 배포</h2>

              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">제목</label>
                <input value={title} onChange={e => setTitle(e.target.value)} placeholder="콘텐츠 제목"
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#22C55E] focus:ring-1 focus:ring-[#22C55E]" />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">채널</label>
                <div className="grid grid-cols-2 gap-2">
                  {['youtube', 'instagram', 'tiktok', 'blog'].map(ch => (
                    <button key={ch} onClick={() => setChannel(ch)}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-all
                        ${channel === ch ? 'text-white border' : 'bg-white/[0.03] text-white/30 border border-white/10'}`}
                      style={channel === ch ? {
                        background: `${CHANNEL_COLORS[ch]}20`,
                        borderColor: `${CHANNEL_COLORS[ch]}40`,
                        color: CHANNEL_COLORS[ch],
                      } : undefined}
                    >
                      {CHANNEL_ICONS[ch]} {ch}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">콘텐츠 URL</label>
                <input value={contentUrl} onChange={e => setContentUrl(e.target.value)}
                  placeholder="/rendered/chopd.mp4"
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#22C55E] focus:ring-1 focus:ring-[#22C55E]" />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">예약 시간 (비워두면 즉시)</label>
                <input type="datetime-local" value={scheduleAt} onChange={e => setScheduleAt(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-[#141414] focus:outline-none focus:border-[#22C55E]" />
              </div>

              {publishResult && (
                <div className={`text-xs px-3 py-2 rounded-lg ${publishResult.startsWith('실패') ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'}`}>
                  {publishResult}
                </div>
              )}

              <button onClick={handlePublish} disabled={publishing || !title || !contentUrl}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-bold
                  bg-[#22C55E] text-white hover:bg-[#1ea750] transition-all disabled:opacity-50">
                {publishing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                {scheduleAt ? '예약 발행' : '즉시 발행'}
              </button>

              {/* 성과 피드백 */}
              <div className="pt-3 border-t border-white/[0.05]">
                <button onClick={() => setShowFeedback(!showFeedback)}
                  className="flex items-center gap-2 text-xs text-white/40 hover:text-white/70 transition-colors">
                  <TrendingUp className="w-3.5 h-3.5" /> 성과 데이터 입력 (GraphRAG 피드백)
                </button>

                {showFeedback && (
                  <div className="mt-3 space-y-3">
                    <input value={feedbackId} onChange={e => setFeedbackId(e.target.value)}
                      placeholder="콘텐츠 ID" className="w-full px-3 py-2 border border-gray-600 rounded-lg text-xs text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#6366F1]" />
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <label className="text-[10px] text-white/30">조회수</label>
                        <input type="number" value={feedbackViews} onChange={e => setFeedbackViews(Number(e.target.value))}
                          className="w-full px-2 py-1.5 border border-gray-600 rounded text-xs text-white bg-white/[0.03] focus:outline-none focus:border-[#6366F1]" />
                      </div>
                      <div>
                        <label className="text-[10px] text-white/30">좋아요</label>
                        <input type="number" value={feedbackLikes} onChange={e => setFeedbackLikes(Number(e.target.value))}
                          className="w-full px-2 py-1.5 border border-gray-600 rounded text-xs text-white bg-white/[0.03] focus:outline-none focus:border-[#6366F1]" />
                      </div>
                      <div>
                        <label className="text-[10px] text-white/30">점수 (0~10)</label>
                        <input type="number" min={0} max={10} value={feedbackScore} onChange={e => setFeedbackScore(Number(e.target.value))}
                          className="w-full px-2 py-1.5 border border-gray-600 rounded text-xs text-white bg-white/[0.03] focus:outline-none focus:border-[#6366F1]" />
                      </div>
                    </div>
                    <button onClick={handleFeedback}
                      className="w-full px-3 py-2 rounded-lg text-xs font-semibold bg-[#6366F1]/10 border border-[#6366F1]/20 text-[#6366F1] hover:bg-[#6366F1]/20 transition-all">
                      GraphRAG에 저장
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* ── 우측: 채널 + 이력 ──────────── */}
          <div className="lg:col-span-2 space-y-4">
            {/* 채널 카드 */}
            <div className="grid grid-cols-2 gap-3">
              {channels.map(ch => (
                <div key={ch.id} className="rounded-xl bg-[#141414] border border-white/[0.07] p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span style={{ color: CHANNEL_COLORS[ch.id] }}>{CHANNEL_ICONS[ch.id]}</span>
                    <span className="text-sm font-bold text-white">{ch.name}</span>
                    <span className={`ml-auto text-[10px] px-2 py-0.5 rounded-full ${ch.api_connected ? 'bg-green-500/10 text-green-400' : 'bg-white/[0.05] text-white/30'}`}>
                      {ch.api_connected ? '연동됨' : '미연동'}
                    </span>
                  </div>
                  <p className="text-[11px] text-white/40">{ch.description}</p>
                  <div className="flex gap-1.5 mt-2">
                    {ch.formats.map(f => (
                      <span key={f} className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.04] text-white/30 border border-white/[0.06]">{f}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* 발행 이력 */}
            <div className="rounded-xl bg-[#141414] border border-white/[0.07] p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-white/60">발행 이력</h3>
                <button onClick={fetchData} className="text-white/30 hover:text-white/60 transition-colors">
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>

              {loading ? (
                <div className="h-20 flex items-center justify-center">
                  <Loader2 className="w-4 h-4 animate-spin text-white/20" />
                </div>
              ) : history.length === 0 ? (
                <div className="h-20 flex items-center justify-center text-xs text-white/20">
                  아직 발행된 콘텐츠가 없습니다
                </div>
              ) : (
                <div className="space-y-2">
                  {history.map((item, i) => {
                    const st = STATUS_MAP[item.status] || STATUS_MAP.draft
                    return (
                      <div key={i} className="flex items-center gap-3 py-2.5 border-b border-white/[0.03] last:border-0">
                        <span style={{ color: CHANNEL_COLORS[item.platform?.toLowerCase()] || '#706E6B' }}>
                          {CHANNEL_ICONS[item.platform?.toLowerCase()] || <FileText className="w-4 h-4" />}
                        </span>
                        <span className="text-sm text-white/70 flex-1 truncate">{item.topic}</span>
                        <span className="flex items-center gap-1 text-[11px]" style={{ color: st.color }}>
                          {st.icon} {st.label}
                        </span>
                        {item.publish_date && (
                          <span className="text-[10px] font-mono text-white/20">
                            {new Date(item.publish_date).toLocaleDateString('ko-KR')}
                          </span>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* 파이프라인 안내 */}
            <div className="rounded-xl bg-white/[0.02] border border-white/[0.05] p-4">
              <div className="flex items-center gap-8 justify-center text-xs text-white/30">
                {[
                  { label: '전략', href: '/strategy', color: '#6366F1' },
                  { label: '컨셉', href: '/concept', color: '#F59E0B' },
                  { label: '생산', href: '/produce', color: '#00FF88' },
                  { label: '배포', href: '/publish', color: '#22C55E', active: true },
                ].map((step, i) => (
                  <a key={i} href={step.href}
                    className="flex items-center gap-2 hover:text-white/60 transition-colors">
                    {i > 0 && <ArrowRight className="w-3 h-3 text-white/10" />}
                    <span className={`px-2 py-1 rounded text-[11px] font-semibold ${step.active ? 'text-white' : ''}`}
                      style={step.active ? { background: `${step.color}20`, color: step.color } : undefined}>
                      {step.label}
                    </span>
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
