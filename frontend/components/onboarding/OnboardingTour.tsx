'use client'

/**
 * OnboardingTour — 신규 사용자 온보딩 투어
 *
 * 목표: 10분 내 첫 영상 완성
 * 5단계: 환영 → 템플릿 선택 → 스크립트 작성 → 오디오 생성 → 영상 렌더
 * 완주율 측정용 step 이벤트 기록
 */

import { useState, useCallback, useEffect } from 'react'
import {
  X, ArrowRight, ArrowLeft, Sparkles, FileText,
  Mic, Film, Check, Timer, Rocket,
} from 'lucide-react'

interface OnboardingTourProps {
  isOpen: boolean
  onClose: () => void
  onComplete: () => void
}

interface Step {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  action: string
  href: string
  tip: string
}

const STEPS: Step[] = [
  {
    id: 'welcome',
    title: '환영합니다!',
    description: 'OmniVibe Pro로 AI 영상을 자동 생성하세요. 10분 안에 첫 영상을 만들어 보겠습니다.',
    icon: <Sparkles className="w-6 h-6" />,
    action: '시작하기',
    href: '#',
    tip: '이 투어는 언제든 대시보드에서 다시 시작할 수 있습니다.',
  },
  {
    id: 'template',
    title: '1단계: 템플릿 선택',
    description: '갤러리에서 마음에 드는 영상 템플릿을 선택하세요. YouTube, Instagram, TikTok 등 다양한 포맷을 지원합니다.',
    icon: <Film className="w-6 h-6" />,
    action: '갤러리 열기',
    href: '/gallery',
    tip: 'YouTube 포맷(1920×1080)이 가장 보편적입니다.',
  },
  {
    id: 'script',
    title: '2단계: 스크립트 작성',
    description: 'AI Writer가 스크립트를 자동 생성합니다. 주제만 입력하면 Hook → Body → CTA 구조의 스크립트가 완성됩니다.',
    icon: <FileText className="w-6 h-6" />,
    action: '스크립트 작성',
    href: '/writer',
    tip: '"AI 영상 자동화로 월 100만원 절약하는 방법" 같은 구체적 주제가 좋습니다.',
  },
  {
    id: 'audio',
    title: '3단계: 오디오 생성',
    description: 'Zero-Fault Audio 기술로 99% 정확도의 AI 나레이션을 생성합니다. 음성 클로닝으로 나만의 목소리도 사용 가능합니다.',
    icon: <Mic className="w-6 h-6" />,
    action: '오디오 생성',
    href: '/audio',
    tip: 'ElevenLabs TTS + Whisper STT 검증 루프로 오류를 자동 교정합니다.',
  },
  {
    id: 'render',
    title: '4단계: 영상 렌더링',
    description: 'Remotion 엔진이 스크립트 + 오디오 + 자막을 결합하여 완성 영상을 렌더링합니다. 프로덕션 페이지에서 확인하세요.',
    icon: <Rocket className="w-6 h-6" />,
    action: '영상 만들기',
    href: '/production',
    tip: '렌더링은 보통 1~2분 소요됩니다. 완료되면 알림을 받습니다.',
  },
]

const STORAGE_KEY = 'omnivibe_onboarding'

export default function OnboardingTour({ isOpen, onClose, onComplete }: OnboardingTourProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set())
  const [startTime] = useState(Date.now())

  // 로컬 스토리지에서 진행 상태 복원
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const data = JSON.parse(saved)
        setCompletedSteps(new Set(data.completed || []))
        setCurrentStep(data.step || 0)
      } catch { /* ignore */ }
    }
  }, [])

  // 진행 상태 저장
  const saveProgress = useCallback((step: number, completed: Set<string>) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      step,
      completed: Array.from(completed),
      lastUpdated: Date.now(),
    }))
  }, [])

  const handleNext = useCallback(() => {
    const step = STEPS[currentStep]
    const newCompleted = new Set(completedSteps)
    newCompleted.add(step.id)
    setCompletedSteps(newCompleted)

    if (currentStep === STEPS.length - 1) {
      // 투어 완료
      const elapsedMin = Math.round((Date.now() - startTime) / 60000)
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        completed: Array.from(newCompleted),
        step: STEPS.length,
        finishedAt: Date.now(),
        elapsedMinutes: elapsedMin,
      }))
      onComplete()
      return
    }

    const next = currentStep + 1
    setCurrentStep(next)
    saveProgress(next, newCompleted)
  }, [currentStep, completedSteps, startTime, onComplete, saveProgress])

  const handlePrev = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }, [currentStep])

  const handleSkip = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      completed: Array.from(completedSteps),
      step: currentStep,
      skipped: true,
      skippedAt: Date.now(),
    }))
    onClose()
  }, [completedSteps, currentStep, onClose])

  if (!isOpen) return null

  const step = STEPS[currentStep]
  const progress = ((currentStep + 1) / STEPS.length) * 100
  const isLast = currentStep === STEPS.length - 1

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#141414] rounded-2xl border border-white/[0.08] shadow-2xl
        w-full max-w-md mx-4 overflow-hidden">

        {/* 진행률 바 */}
        <div className="h-1 bg-white/[0.05]">
          <div
            className="h-full bg-[#00FF88] transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* 닫기 + 타이머 */}
        <div className="flex items-center justify-between px-5 pt-4">
          <div className="flex items-center gap-2 text-[11px] text-white/40">
            <Timer className="w-3.5 h-3.5" />
            {currentStep + 1} / {STEPS.length}
          </div>
          <button onClick={handleSkip} className="text-white/30 hover:text-white/60 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 컨텐츠 */}
        <div className="px-6 py-5">
          {/* 아이콘 */}
          <div className="w-12 h-12 rounded-xl bg-[#00FF88]/10 border border-[#00FF88]/20
            flex items-center justify-center text-[#00FF88] mb-4">
            {step.icon}
          </div>

          <h2 className="text-lg font-bold text-white mb-2">{step.title}</h2>
          <p className="text-sm text-white/60 leading-relaxed mb-4">{step.description}</p>

          {/* 팁 */}
          <div className="bg-white/[0.03] border border-white/[0.06] rounded-lg px-4 py-3 mb-5">
            <p className="text-[11px] text-white/40">
              <span className="text-[#00FF88] font-bold mr-1">TIP</span>
              {step.tip}
            </p>
          </div>

          {/* 완료 체크 (이전 단계) */}
          {currentStep > 0 && (
            <div className="flex flex-wrap gap-2 mb-5">
              {STEPS.slice(0, currentStep).map(s => (
                <span key={s.id} className="flex items-center gap-1 px-2 py-0.5
                  rounded text-[10px] font-mono bg-[#00FF88]/10 text-[#00FF88]">
                  <Check className="w-3 h-3" />
                  {s.id}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* 액션 버튼 */}
        <div className="flex items-center gap-3 px-6 pb-5">
          {currentStep > 0 && (
            <button
              onClick={handlePrev}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-sm font-semibold
                bg-white/[0.05] border border-white/10 text-white/50
                hover:text-white/80 hover:bg-white/[0.08] transition-all"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              이전
            </button>
          )}

          <button
            onClick={handleNext}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
              text-sm font-bold bg-[#00FF88] text-[#0A0A0A] hover:bg-[#00FF88]/90 transition-all"
          >
            {isLast ? '투어 완료' : step.action}
            {isLast ? <Check className="w-4 h-4" /> : <ArrowRight className="w-4 h-4" />}
          </button>
        </div>

        {/* 스킵 링크 */}
        <div className="text-center pb-4">
          <button onClick={handleSkip} className="text-[11px] text-white/25 hover:text-white/50 transition-colors">
            나중에 하기
          </button>
        </div>
      </div>
    </div>
  )
}
