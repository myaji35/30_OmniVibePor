'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { Check, Circle } from 'lucide-react'

// 프로덕션 파이프라인 단계 정의 — 실제 존재하는 페이지만 포함
const STEPS = [
  { href: '/writer',          label: '스크립트',   shortLabel: '01' },
  { href: '/director',        label: '디렉터',     shortLabel: '02' },
  { href: '/storyboard',      label: '스토리보드', shortLabel: '03' },
  { href: '/audio',           label: '오디오',     shortLabel: '04' },
  { href: '/subtitle-editor', label: '자막',       shortLabel: '05' },
  { href: '/studio',          label: '스튜디오',   shortLabel: '06' },
  { href: '/production',      label: '배포',       shortLabel: '07' },
]

interface ProductionStepperProps {
  /** 완료된 스텝 hrefs (미전달 시 pathname 기준 자동 계산) */
  completedSteps?: string[]
  className?: string
}

export default function ProductionStepper({
  completedSteps,
  className = '',
}: ProductionStepperProps) {
  const pathname = usePathname()
  const currentIdx = STEPS.findIndex(s => s.href === pathname)

  const getStatus = (idx: number): 'done' | 'active' | 'pending' => {
    if (completedSteps) {
      if (completedSteps.includes(STEPS[idx].href)) return 'done'
      if (idx === currentIdx) return 'active'
      return 'pending'
    }
    if (idx < currentIdx) return 'done'
    if (idx === currentIdx) return 'active'
    return 'pending'
  }

  return (
    <div className={`flex items-center w-full overflow-x-auto scrollbar-hide ${className}`}>
      {STEPS.map((step, idx) => {
        const status = getStatus(idx)
        const isLast = idx === STEPS.length - 1

        return (
          <div key={step.href} className="flex items-center shrink-0">
            {/* 스텝 노드 */}
            <Link href={step.href} className="flex flex-col items-center gap-1 group">
              {/* 원형 아이콘 */}
              <div className={`
                w-8 h-8 rounded-full flex items-center justify-center
                text-[11px] font-black transition-all duration-200
                ${status === 'done'
                  ? 'bg-emerald-500/20 border border-emerald-500/50 text-emerald-400'
                  : status === 'active'
                    ? 'bg-purple-500/20 border border-purple-400/70 text-purple-300 shadow-[0_0_12px_-2px_rgba(168,85,247,0.5)]'
                    : 'bg-white/[0.04] border border-white/10 text-white/30 group-hover:border-white/20 group-hover:text-white/50'
                }
              `}>
                {status === 'done'
                  ? <Check className="w-3.5 h-3.5" />
                  : status === 'active'
                    ? <Circle className="w-2.5 h-2.5 fill-current" />
                    : <span>{step.shortLabel}</span>
                }
              </div>
              {/* 라벨 */}
              <span className={`
                text-[10px] font-semibold whitespace-nowrap transition-colors
                ${status === 'active'  ? 'text-purple-300'
                : status === 'done'   ? 'text-emerald-400/70'
                : 'text-white/30 group-hover:text-white/50'}
              `}>
                {step.label}
              </span>
            </Link>

            {/* 연결선 */}
            {!isLast && (
              <div className={`
                h-px w-8 mx-1 mb-5 transition-colors
                ${status === 'done' ? 'bg-emerald-500/40' : 'bg-white/10'}
              `} />
            )}
          </div>
        )
      })}
    </div>
  )
}
