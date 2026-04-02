'use client'

/**
 * UpgradePrompt — Quota 한도 초과 시 표시되는 업그레이드 유도 모달
 *
 * Quota 미들웨어가 403을 반환했을 때 표시.
 * 사용자의 현재 플랜 → 다음 플랜으로 업그레이드 안내.
 */

import { useCallback } from 'react'
import { X, Zap, Check, ArrowRight } from 'lucide-react'

interface UpgradePromptProps {
  isOpen: boolean
  onClose: () => void
  currentPlan: string
  quotaType: string  // 'render' | 'audio' | 'voice_clone'
  used: number
  limit: number
}

const PLANS = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    render: 3,
    audio: 10,
    voiceClone: 0,
    color: '#706E6B',
    features: ['영상 렌더 3회/월', '오디오 생성 10회/월', '기본 템플릿'],
  },
  {
    id: 'creator',
    name: 'Creator',
    price: 19,
    render: 30,
    audio: 100,
    voiceClone: 1,
    color: '#4BCA81',
    features: ['영상 렌더 30회/월', '오디오 생성 100회/월', '음성 클론 1개', '모든 템플릿'],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 49,
    render: 100,
    audio: -1,
    voiceClone: 3,
    color: '#00A1E0',
    features: ['영상 렌더 100회/월', '오디오 무제한', '음성 클론 3개', '우선 지원'],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 499,
    render: -1,
    audio: -1,
    voiceClone: 10,
    color: '#16325C',
    features: ['모두 무제한', '음성 클론 10개', '전담 지원', 'API 접근', '화이트 라벨'],
  },
]

const QUOTA_LABELS: Record<string, string> = {
  render: '영상 렌더',
  audio: '오디오 생성',
  voice_clone: '음성 클론',
}

export default function UpgradePrompt({
  isOpen,
  onClose,
  currentPlan,
  quotaType,
  used,
  limit,
}: UpgradePromptProps) {
  const currentIdx = PLANS.findIndex(p => p.id === currentPlan)
  const nextPlan = PLANS[currentIdx + 1] || PLANS[PLANS.length - 1]

  const handleUpgrade = useCallback(async (planId: string) => {
    try {
      const res = await fetch('/api/v1/billing/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({
          plan: planId,
          success_url: `${window.location.origin}/dashboard?upgraded=true`,
          cancel_url: window.location.href,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        if (data.checkout_url) {
          window.location.href = data.checkout_url
        }
      }
    } catch (error) {
      console.error('Upgrade failed:', error)
    }
  }, [])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* 헤더 */}
        <div className="bg-[#16325C] px-6 py-5 text-white relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-white/60 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-5 h-5 text-amber-300" />
            <h2 className="text-lg font-bold">{QUOTA_LABELS[quotaType] || quotaType} 한도 초과</h2>
          </div>
          <p className="text-sm text-white/70">
            이번 달 {QUOTA_LABELS[quotaType]} {used}회 사용 (한도: {limit}회).
            더 많은 기능을 위해 플랜을 업그레이드하세요.
          </p>
        </div>

        {/* 추천 플랜 */}
        <div className="p-6">
          <div
            className="rounded-xl border-2 p-5 mb-4"
            style={{ borderColor: nextPlan.color }}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span
                  className="px-2.5 py-1 rounded-full text-xs font-bold text-white"
                  style={{ background: nextPlan.color }}
                >
                  추천
                </span>
                <span className="text-lg font-bold text-[#16325C]">{nextPlan.name}</span>
              </div>
              <div className="text-right">
                <span className="text-2xl font-black text-[#16325C]">${nextPlan.price}</span>
                <span className="text-sm text-gray-500">/월</span>
              </div>
            </div>

            <ul className="space-y-2 mb-4">
              {nextPlan.features.map((f, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-gray-700">
                  <Check className="w-4 h-4 text-[#4BCA81] flex-shrink-0" />
                  {f}
                </li>
              ))}
            </ul>

            <button
              onClick={() => handleUpgrade(nextPlan.id)}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
                text-sm font-bold text-white transition-colors"
              style={{ background: nextPlan.color }}
            >
              {nextPlan.name}으로 업그레이드
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* 전체 플랜 보기 링크 */}
          <div className="text-center">
            <a
              href="/pricing"
              className="text-sm text-[#00A1E0] hover:underline"
            >
              전체 플랜 비교하기
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
