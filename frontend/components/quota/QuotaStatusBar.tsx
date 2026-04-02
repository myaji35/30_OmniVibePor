'use client'

/**
 * QuotaStatusBar — 현재 Quota 사용량 + 업그레이드 유도 바
 *
 * 대시보드/프로덕션 상단에 배치하여 사용량 가시성 확보.
 * 80% 초과 시 경고, 100% 도달 시 업그레이드 프롬프트.
 */

import { useState, useEffect, useCallback } from 'react'
import { Zap, AlertTriangle, ArrowUpRight } from 'lucide-react'

interface QuotaItem {
  type: string
  label: string
  used: number
  limit: number  // -1 = 무제한
}

interface QuotaStatusBarProps {
  onUpgradeClick?: () => void
}

const PLAN_LABELS: Record<string, string> = {
  free: 'Free',
  creator: 'Creator',
  pro: 'Pro',
  enterprise: 'Enterprise',
}

export default function QuotaStatusBar({ onUpgradeClick }: QuotaStatusBarProps) {
  const [plan, setPlan] = useState('free')
  const [quotas, setQuotas] = useState<QuotaItem[]>([])
  const [loading, setLoading] = useState(true)

  const fetchQuota = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/billing/usage', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      })
      if (!res.ok) throw new Error('Failed to fetch quota')
      const data = await res.json()

      setPlan(data.plan || 'free')
      setQuotas([
        { type: 'render', label: '영상 렌더', used: data.render_used ?? 0, limit: data.render_limit ?? 3 },
        { type: 'audio', label: '오디오 생성', used: data.audio_used ?? 0, limit: data.audio_limit ?? 10 },
        { type: 'voice_clone', label: '음성 클론', used: data.voice_clone_used ?? 0, limit: data.voice_clone_limit ?? 0 },
      ])
    } catch {
      // 기본값 (백엔드 미연결 시)
      setPlan('free')
      setQuotas([
        { type: 'render', label: '영상 렌더', used: 0, limit: 3 },
        { type: 'audio', label: '오디오 생성', used: 0, limit: 10 },
        { type: 'voice_clone', label: '음성 클론', used: 0, limit: 0 },
      ])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchQuota() }, [fetchQuota])

  const isNearLimit = quotas.some(q => q.limit > 0 && q.used >= q.limit * 0.8)
  const isAtLimit = quotas.some(q => q.limit >= 0 && q.used >= q.limit && q.limit !== -1)
  const showUpgrade = plan !== 'enterprise'

  if (loading) return null

  return (
    <div className={`flex items-center gap-4 px-4 py-2.5 rounded-lg border text-sm
      ${isAtLimit
        ? 'bg-red-50 border-red-200'
        : isNearLimit
          ? 'bg-amber-50 border-amber-200'
          : 'bg-white border-gray-200'
      }`}
    >
      {/* 플랜 뱃지 */}
      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold"
        style={{
          background: plan === 'enterprise' ? '#16325C' : plan === 'pro' ? '#00A1E0' : plan === 'creator' ? '#4BCA81' : '#706E6B',
          color: 'white',
        }}
      >
        <Zap className="w-3 h-3" />
        {PLAN_LABELS[plan] || 'Free'}
      </span>

      {/* Quota 바 */}
      <div className="flex items-center gap-4 flex-1">
        {quotas.filter(q => q.limit !== 0).map(q => (
          <QuotaMeter key={q.type} item={q} />
        ))}
      </div>

      {/* 경고 + 업그레이드 */}
      {isAtLimit && (
        <span className="flex items-center gap-1 text-xs font-semibold text-red-600">
          <AlertTriangle className="w-3.5 h-3.5" />
          한도 도달
        </span>
      )}

      {showUpgrade && (
        <button
          onClick={onUpgradeClick}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold
            bg-[#00A1E0] text-white hover:bg-[#0088C7] transition-colors"
        >
          업그레이드
          <ArrowUpRight className="w-3 h-3" />
        </button>
      )}
    </div>
  )
}

function QuotaMeter({ item }: { item: QuotaItem }) {
  const isUnlimited = item.limit === -1
  const pct = isUnlimited ? 0 : item.limit > 0 ? Math.min(100, (item.used / item.limit) * 100) : 0
  const isWarning = !isUnlimited && pct >= 80
  const isDanger = !isUnlimited && pct >= 100

  return (
    <div className="flex items-center gap-2 min-w-[140px]">
      <span className="text-xs text-gray-500 w-[72px] text-right">{item.label}</span>
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            isDanger ? 'bg-red-500' : isWarning ? 'bg-amber-400' : 'bg-[#00A1E0]'
          }`}
          style={{ width: isUnlimited ? '0%' : `${pct}%` }}
        />
      </div>
      <span className={`text-[11px] font-mono tabular-nums ${
        isDanger ? 'text-red-600 font-bold' : isWarning ? 'text-amber-600' : 'text-gray-500'
      }`}>
        {isUnlimited ? '무제한' : `${item.used}/${item.limit}`}
      </span>
    </div>
  )
}
