'use client'

/**
 * OnboardingTour — 신규 사용자 인터랙티브 가이드 투어
 *
 * 가입 후 10분 내 첫 영상 렌더링 달성을 목표로 한다.
 * localStorage로 완료 여부를 저장하며, 언제든 재실행 가능.
 */

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { X, ArrowRight, ChevronRight, Sparkles } from 'lucide-react'

export interface TourStep {
  id:          string
  title:       string
  description: string
  href?:       string       // 해당 페이지로 이동
  ctaLabel:    string
  icon:        string
}

const TOUR_STEPS: TourStep[] = [
  {
    id:          'gallery',
    title:       '① 템플릿 선택',
    description: '갤러리에서 마음에 드는 템플릿을 골라보세요. 유튜브·인스타·틱톡 형식을 지원합니다.',
    href:        '/gallery',
    ctaLabel:    '갤러리 열기',
    icon:        '🖼️',
  },
  {
    id:          'writer',
    title:       '② AI 스크립트 작성',
    description: '주제와 톤을 입력하면 AI가 30초 만에 완성된 스크립트를 작성합니다.',
    href:        '/writer',
    ctaLabel:    '스크립트 작성 시작',
    icon:        '✍️',
  },
  {
    id:          'audio',
    title:       '③ 오디오 생성',
    description: 'ElevenLabs TTS로 음성을 생성하고, Whisper로 99% 정확도를 검증합니다.',
    href:        '/audio',
    ctaLabel:    '오디오 생성하기',
    icon:        '🔊',
  },
  {
    id:          'studio',
    title:       '④ 스튜디오에서 미리보기',
    description: 'Remotion 기반 실시간 영상 미리보기로 최종 결과를 확인하세요.',
    href:        '/studio',
    ctaLabel:    '스튜디오 열기',
    icon:        '🎬',
  },
  {
    id:          'production',
    title:       '⑤ 배포',
    description: 'YouTube, Instagram, TikTok에 원클릭으로 배포하거나 MP4 파일을 다운로드하세요.',
    href:        '/production',
    ctaLabel:    '배포 페이지로',
    icon:        '🚀',
  },
]

const STORAGE_KEY = 'omnivibe_onboarding_completed'

interface OnboardingTourProps {
  /** 강제로 투어를 표시할 때 true (기본: localStorage 기반 자동 표시) */
  forceShow?: boolean
  onComplete?: () => void
}

export default function OnboardingTour({ forceShow = false, onComplete }: OnboardingTourProps) {
  const router = useRouter()
  const [visible,    setVisible]    = useState(false)
  const [stepIdx,    setStepIdx]    = useState(0)
  const [minimized,  setMinimized]  = useState(false)

  // 첫 방문 감지
  useEffect(() => {
    if (forceShow) { setVisible(true); return }
    const done = localStorage.getItem(STORAGE_KEY)
    if (!done) setVisible(true)
  }, [forceShow])

  const currentStep = TOUR_STEPS[stepIdx]
  const isLast      = stepIdx === TOUR_STEPS.length - 1
  const progress    = ((stepIdx + 1) / TOUR_STEPS.length) * 100

  const handleNext = useCallback(() => {
    if (currentStep.href) {
      router.push(currentStep.href)
    }
    if (isLast) {
      handleComplete()
    } else {
      setStepIdx(s => s + 1)
    }
  }, [currentStep, isLast, router])

  const handleComplete = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, '1')
    setVisible(false)
    onComplete?.()
  }, [onComplete])

  const handleSkip = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, '1')
    setVisible(false)
  }, [])

  if (!visible) return null

  // ── 최소화 상태 ──
  if (minimized) {
    return (
      <button
        onClick={() => setMinimized(false)}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5
          rounded-full shadow-xl transition-all hover:scale-105
          bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-[12px] font-bold"
      >
        <Sparkles className="w-3.5 h-3.5" />
        시작 가이드
        <span className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center text-[10px]">
          {stepIdx + 1}
        </span>
      </button>
    )
  }

  // ── 풀 투어 카드 ──
  return (
    <div className="fixed bottom-6 right-6 z-50 w-80 rounded-2xl shadow-2xl overflow-hidden
      bg-[#0f1117] border border-white/[0.10]
      shadow-[0_20px_60px_-10px_rgba(168,85,247,0.3)]"
    >
      {/* 헤더 */}
      <div className="px-4 py-3 flex items-center justify-between
        border-b border-white/[0.07]"
        style={{ background: 'linear-gradient(135deg,rgba(147,51,234,0.15),rgba(99,102,241,0.10))' }}
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-purple-400" />
          <span className="text-[11px] font-black text-white/80 uppercase tracking-widest">
            시작 가이드
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => setMinimized(true)}
            className="p-1 rounded text-white/30 hover:text-white/60 transition-colors text-[10px]">
            _
          </button>
          <button onClick={handleSkip}
            className="p-1 rounded text-white/30 hover:text-white/60 transition-colors">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 프로그레스 바 */}
      <div className="h-0.5 bg-white/[0.05]">
        <div
          className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* 스텝 내용 */}
      <div className="p-5 space-y-3">
        {/* 아이콘 + 제목 */}
        <div className="flex items-start gap-3">
          <div className="text-2xl">{currentStep.icon}</div>
          <div>
            <h3 className="text-[14px] font-bold text-white">{currentStep.title}</h3>
            <p className="text-[12px] text-white/50 mt-1 leading-relaxed">
              {currentStep.description}
            </p>
          </div>
        </div>

        {/* 스텝 점 */}
        <div className="flex items-center justify-center gap-1.5 py-1">
          {TOUR_STEPS.map((_, i) => (
            <button key={i} onClick={() => setStepIdx(i)}
              className={`rounded-full transition-all ${
                i === stepIdx
                  ? 'w-4 h-1.5 bg-purple-500'
                  : i < stepIdx
                    ? 'w-1.5 h-1.5 bg-emerald-500/60'
                    : 'w-1.5 h-1.5 bg-white/20'
              }`}
            />
          ))}
        </div>

        {/* CTA 버튼 */}
        <button
          onClick={handleNext}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl
            text-[13px] font-bold transition-all active:scale-95"
          style={{ background: 'linear-gradient(135deg,#9333ea,#6366f1)' }}
        >
          {currentStep.ctaLabel}
          {isLast ? <Sparkles className="w-3.5 h-3.5" /> : <ArrowRight className="w-3.5 h-3.5" />}
        </button>

        <button onClick={handleSkip}
          className="w-full text-[11px] text-white/25 hover:text-white/40 transition-colors py-1">
          건너뛰기
        </button>
      </div>
    </div>
  )
}

// 재실행 헬퍼
export function resetOnboardingTour() {
  localStorage.removeItem(STORAGE_KEY)
}
