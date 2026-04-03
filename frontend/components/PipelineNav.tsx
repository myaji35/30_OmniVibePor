'use client'

/**
 * PipelineNav — 전략→컨셉→생산→추적 파이프라인 단계 안내
 * 현재 단계를 하이라이트하고, 다음 단계 CTA를 표시
 */

import { ArrowRight } from 'lucide-react'
import { usePathname } from 'next/navigation'

const STEPS = [
  { id: 'strategy', label: '전략', href: '/strategy', color: '#6366F1' },
  { id: 'concept', label: '컨셉', href: '/concept', color: '#F59E0B' },
  { id: 'produce', label: '생산', href: '/produce', color: '#22C55E' },
  { id: 'publish', label: '추적', href: '/publish', color: '#3B82F6' },
]

export default function PipelineNav() {
  const pathname = usePathname()
  const currentIdx = STEPS.findIndex(s => pathname.startsWith(s.href))
  const nextStep = currentIdx >= 0 && currentIdx < STEPS.length - 1 ? STEPS[currentIdx + 1] : null

  return (
    <div className="flex items-center justify-between px-4 py-3 rounded-xl bg-white/[0.02] border border-white/[0.05]">
      {/* 단계 표시 */}
      <div className="flex items-center gap-2">
        {STEPS.map((step, i) => {
          const isCurrent = i === currentIdx
          const isDone = i < currentIdx
          return (
            <div key={step.id} className="flex items-center gap-2">
              {i > 0 && <ArrowRight className="w-3 h-3 text-white/15" />}
              <a href={step.href}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all
                  ${isCurrent ? 'text-white' : isDone ? 'text-white/40' : 'text-white/20 hover:text-white/40'}`}
                style={isCurrent ? { background: `${step.color}20`, color: step.color, border: `1px solid ${step.color}30` } : undefined}
              >
                {isDone ? '✓ ' : ''}{step.label}
              </a>
            </div>
          )
        })}
      </div>

      {/* 다음 단계 CTA */}
      {nextStep && (
        <a href={nextStep.href}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all hover:opacity-80"
          style={{ background: `${nextStep.color}15`, color: nextStep.color, border: `1px solid ${nextStep.color}25` }}
        >
          다음: {nextStep.label} <ArrowRight className="w-3.5 h-3.5" />
        </a>
      )}
    </div>
  )
}
