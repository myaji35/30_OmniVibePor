'use client'

/**
 * Pricing 페이지 — 4-Tier 플랜 비교 + Stripe Checkout 연동
 * SLDS 디자인 시스템 기반
 */

import { useState, useCallback } from 'react'
import { Check, X, Zap, Star, Building2, ArrowRight } from 'lucide-react'
import AppShell from '@/components/AppShell'

const PLANS = [
  {
    id: 'free',
    name: 'Free',
    description: '영상 자동화를 체험하세요',
    price: 0,
    color: '#706E6B',
    popular: false,
    limits: {
      render: '5회/월 (워터마크)',
      audio: '15회/월',
      voiceClone: '-',
      templates: '기본',
      support: '커뮤니티',
      api: false,
    },
    features: [
      { text: '영상 렌더 5회/월 (워터마크)', included: true },
      { text: '오디오 생성 15회/월', included: true },
      { text: '기본 템플릿', included: true },
      { text: '음성 클로닝', included: false },
      { text: 'API 접근', included: false },
      { text: '우선 지원', included: false },
    ],
  },
  {
    id: 'creator',
    name: 'Creator',
    description: '개인 크리에이터를 위한 플랜',
    price: 19,
    color: '#4BCA81',
    popular: false,
    limits: {
      render: '30회/월',
      audio: '100회/월',
      voiceClone: '1개',
      templates: '전체',
      support: '이메일',
      api: false,
    },
    features: [
      { text: '영상 렌더 30회/월', included: true },
      { text: '오디오 생성 100회/월', included: true },
      { text: '모든 템플릿', included: true },
      { text: '음성 클로닝 1개', included: true },
      { text: 'API 접근', included: false },
      { text: '우선 지원', included: false },
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    description: '팀과 에이전시를 위한 플랜',
    price: 49,
    color: '#00A1E0',
    popular: true,
    limits: {
      render: '100회/월',
      audio: '무제한',
      voiceClone: '3개',
      templates: '전체',
      support: '우선 지원',
      api: true,
    },
    features: [
      { text: '영상 렌더 100회/월', included: true },
      { text: '오디오 무제한', included: true },
      { text: '모든 템플릿', included: true },
      { text: '음성 클로닝 3개', included: true },
      { text: 'API 접근', included: true },
      { text: '우선 지원', included: true },
    ],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    description: '대규모 운영을 위한 맞춤 플랜',
    price: 499,
    color: '#16325C',
    popular: false,
    limits: {
      render: '무제한',
      audio: '무제한',
      voiceClone: '10개',
      templates: '커스텀',
      support: '전담 매니저',
      api: true,
    },
    features: [
      { text: '모든 기능 무제한', included: true },
      { text: '오디오 무제한', included: true },
      { text: '커스텀 템플릿', included: true },
      { text: '음성 클로닝 10개', included: true },
      { text: 'API 접근 + 화이트 라벨', included: true },
      { text: '전담 매니저', included: true },
    ],
  },
]

const ICON_MAP: Record<string, React.ReactNode> = {
  free: <Zap className="w-5 h-5" />,
  creator: <Star className="w-5 h-5" />,
  pro: <Zap className="w-5 h-5" />,
  enterprise: <Building2 className="w-5 h-5" />,
}

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly')

  const handleCheckout = useCallback(async (planId: string) => {
    if (planId === 'free') return

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
      console.error('Checkout failed:', error)
    }
  }, [])

  return (
    <AppShell>
    <div className="min-h-screen bg-[#0f1117]">
      {/* 헤더 */}
      <div className="bg-[#16325C] text-white py-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-3xl font-bold mb-3">
            나에게 맞는 플랜을 선택하세요
          </h1>
          <p className="text-white/70 text-base mb-8">
            모든 플랜에 14일 무료 체험이 포함됩니다. 언제든지 취소 가능합니다.
          </p>

          {/* 월간/연간 토글 */}
          <div className="inline-flex items-center gap-3 bg-white/10 rounded-lg p-1">
            <button
              onClick={() => setBillingPeriod('monthly')}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition-all
                ${billingPeriod === 'monthly'
                  ? 'bg-white text-[#16325C]'
                  : 'text-white/70 hover:text-white'
                }`}
            >
              월간
            </button>
            <button
              onClick={() => setBillingPeriod('yearly')}
              className={`px-4 py-2 rounded-md text-sm font-semibold transition-all
                ${billingPeriod === 'yearly'
                  ? 'bg-white text-[#16325C]'
                  : 'text-white/70 hover:text-white'
                }`}
            >
              연간 <span className="text-[#4BCA81] text-xs ml-1">2개월 무료</span>
            </button>
          </div>
        </div>
      </div>

      {/* 플랜 카드 */}
      <div className="max-w-5xl mx-auto px-4 -mt-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {PLANS.map(plan => {
            const price = billingPeriod === 'yearly'
              ? Math.round(plan.price * 10 / 12)  // 연간 = 10개월분 (2개월 무료)
              : plan.price

            return (
              <div
                key={plan.id}
                className={`relative bg-white rounded-xl border-2 shadow-sm overflow-hidden
                  ${plan.popular ? 'border-[#00A1E0] shadow-lg' : 'border-gray-200'}`}
              >
                {/* 인기 뱃지 */}
                {plan.popular && (
                  <div className="absolute top-0 left-0 right-0 bg-[#00A1E0] text-white
                    text-center text-xs font-bold py-1.5">
                    가장 인기
                  </div>
                )}

                <div className={`p-5 ${plan.popular ? 'pt-10' : ''}`}>
                  {/* 플랜 아이콘 + 이름 */}
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className="w-8 h-8 rounded-lg flex items-center justify-center text-white"
                      style={{ background: plan.color }}
                    >
                      {ICON_MAP[plan.id]}
                    </span>
                    <span className="text-lg font-bold text-[#16325C]">{plan.name}</span>
                  </div>
                  <p className="text-xs text-gray-500 mb-4">{plan.description}</p>

                  {/* 가격 */}
                  <div className="mb-5">
                    <span className="text-3xl font-black text-[#16325C]">
                      {price === 0 ? '무료' : `$${price}`}
                    </span>
                    {price > 0 && (
                      <span className="text-sm text-gray-500">/월</span>
                    )}
                  </div>

                  {/* CTA 버튼 */}
                  <button
                    onClick={() => handleCheckout(plan.id)}
                    className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-lg
                      text-sm font-bold transition-colors mb-5
                      ${plan.id === 'free'
                        ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        : 'text-white hover:opacity-90'
                      }`}
                    style={plan.id !== 'free' ? { background: plan.color } : undefined}
                  >
                    {plan.id === 'free' ? '현재 플랜' : plan.id === 'enterprise' ? '데모 요청' : '시작하기'}
                    {plan.id !== 'free' && <ArrowRight className="w-4 h-4" />}
                  </button>

                  {/* 기능 목록 */}
                  <ul className="space-y-2.5">
                    {plan.features.map((f, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm">
                        {f.included ? (
                          <Check className="w-4 h-4 text-[#4BCA81] flex-shrink-0" />
                        ) : (
                          <X className="w-4 h-4 text-gray-300 flex-shrink-0" />
                        )}
                        <span className={f.included ? 'text-gray-700' : 'text-gray-400'}>
                          {f.text}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* 비교 테이블 */}
      <div className="max-w-5xl mx-auto px-4 py-16">
        <h2 className="text-xl font-bold text-[#16325C] text-center mb-8">
          상세 비교
        </h2>
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left px-5 py-3 text-gray-500 font-semibold">기능</th>
                {PLANS.map(p => (
                  <th key={p.id} className="text-center px-4 py-3 font-bold text-[#16325C]">
                    {p.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                { label: '영상 렌더', key: 'render' as const },
                { label: '오디오 생성', key: 'audio' as const },
                { label: '음성 클론', key: 'voiceClone' as const },
                { label: '템플릿', key: 'templates' as const },
                { label: '지원', key: 'support' as const },
              ].map(row => (
                <tr key={row.key} className="border-b border-gray-100">
                  <td className="px-5 py-3 text-gray-600">{row.label}</td>
                  {PLANS.map(p => (
                    <td key={p.id} className="text-center px-4 py-3 text-gray-700">
                      {p.limits[row.key] === '-'
                        ? <X className="w-4 h-4 text-gray-300 mx-auto" />
                        : p.limits[row.key]
                      }
                    </td>
                  ))}
                </tr>
              ))}
              <tr className="border-b border-gray-100">
                <td className="px-5 py-3 text-gray-600">API 접근</td>
                {PLANS.map(p => (
                  <td key={p.id} className="text-center px-4 py-3">
                    {p.limits.api
                      ? <Check className="w-4 h-4 text-[#4BCA81] mx-auto" />
                      : <X className="w-4 h-4 text-gray-300 mx-auto" />
                    }
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    </AppShell>
  )
}
