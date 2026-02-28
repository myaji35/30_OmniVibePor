'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  X,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Loader2,
  CheckCircle2,
  Play,
} from 'lucide-react'

interface AIPlannerModalProps {
  onClose: () => void
}

type Step = 1 | 2 | 3 | 4 | 5

interface PlannerState {
  intent: string
  platform: string
  tone: string
  duration: string
  selectedTemplateId: string | null
}

interface RecommendedTemplate {
  id: string
  name: string
  reason: string
  thumbnailColor: string
  matchScore: number
}

interface ScriptBlock {
  type: 'hook' | 'intro' | 'body' | 'cta' | 'outro'
  label: string
  text: string
}

const STEP_TITLES: Record<Step, string> = {
  1: '어떤 영상을 만들고 싶으신가요?',
  2: '세부 정보를 선택해주세요',
  3: 'AI 추천 템플릿',
  4: '스크립트 초안',
  5: '준비 완료!',
}

const PLATFORM_OPTIONS = [
  { value: 'youtube', label: 'YouTube', color: 'border-blue-400 bg-blue-50 text-blue-700' },
  { value: 'instagram', label: 'Instagram', color: 'border-pink-400 bg-pink-50 text-pink-700' },
  { value: 'tiktok', label: 'TikTok', color: 'border-gray-700 bg-gray-100 text-gray-800' },
]

const TONE_OPTIONS = [
  { value: 'professional', label: '전문적' },
  { value: 'emotional', label: '감성적' },
  { value: 'trendy', label: '트렌디' },
]

const DURATION_OPTIONS = [
  { value: '30', label: '30초' },
  { value: '60', label: '60초' },
  { value: '90', label: '90초' },
  { value: '180', label: '3분' },
]

function generateMockRecommendations(state: PlannerState): RecommendedTemplate[] {
  const intent = state.intent.toLowerCase()
  const results: RecommendedTemplate[] = []

  if (intent.includes('스타트업') || intent.includes('투자') || intent.includes('it')) {
    results.push(
      { id: 'tech-minimal', name: 'Tech Minimal', reason: 'IT/스타트업 영상에 최적화된 미니멀한 디자인', thumbnailColor: '#1a1a2e', matchScore: 95 },
      { id: 'startup-bold', name: 'Startup Bold', reason: '투자자 피칭에 적합한 임팩트 있는 구성', thumbnailColor: '#e94560', matchScore: 88 },
      { id: 'corporate-pro', name: 'Corporate Pro', reason: '비즈니스 전문성을 강조하는 구성', thumbnailColor: '#16325C', matchScore: 82 },
    )
  } else if (intent.includes('교육') || intent.includes('튜토리얼') || intent.includes('설명')) {
    results.push(
      { id: 'learn-step', name: 'Learn Step', reason: '단계별 교육 콘텐츠에 최적화', thumbnailColor: '#2d6a4f', matchScore: 94 },
      { id: 'tutorial-clean', name: 'Tutorial Clean', reason: '깔끔한 설명 중심의 레이아웃', thumbnailColor: '#40916c', matchScore: 87 },
      { id: 'explain-simple', name: 'Explain Simple', reason: '복잡한 내용을 단순하게 전달', thumbnailColor: '#52b788', matchScore: 80 },
    )
  } else if (intent.includes('브이로그') || intent.includes('일상') || intent.includes('여행')) {
    results.push(
      { id: 'life-vlog', name: 'Life Vlog', reason: '자연스러운 브이로그 스타일', thumbnailColor: '#f4845f', matchScore: 93 },
      { id: 'travel-cinematic', name: 'Travel Cinematic', reason: '시네마틱한 여행 영상 구성', thumbnailColor: '#f7b267', matchScore: 86 },
      { id: 'daily-story', name: 'Daily Story', reason: '일상을 매력적으로 담는 구성', thumbnailColor: '#f25c54', matchScore: 79 },
    )
  } else {
    results.push(
      { id: 'corporate-pro', name: 'Corporate Pro', reason: '범용적으로 활용 가능한 전문 구성', thumbnailColor: '#16325C', matchScore: 90 },
      { id: 'fun-kinetic', name: 'Fun Kinetic', reason: '역동적인 모션으로 주목도를 높이는 구성', thumbnailColor: '#ff6b6b', matchScore: 84 },
      { id: 'tech-minimal', name: 'Tech Minimal', reason: '깔끔하고 세련된 디자인', thumbnailColor: '#1a1a2e', matchScore: 78 },
    )
  }

  return results
}

function generateMockScript(templateId: string): ScriptBlock[] {
  return [
    {
      type: 'hook',
      label: 'Hook (0~5초)',
      text: '지금 이 영상을 놓치면, 당신의 경쟁자가 먼저 알게 됩니다.',
    },
    {
      type: 'intro',
      label: 'Intro (5~15초)',
      text: '안녕하세요, 오늘은 많은 분들이 궁금해하시는 핵심 전략을 공개합니다.',
    },
    {
      type: 'body',
      label: 'Body (15~45초)',
      text: '첫 번째 포인트는 데이터 기반의 의사결정입니다. 실제 사례를 통해 보여드리겠습니다. 두 번째로, 자동화 도구를 활용한 효율 극대화 방법입니다.',
    },
    {
      type: 'cta',
      label: 'CTA (45~55초)',
      text: '더 자세한 내용이 궁금하시다면 아래 링크를 확인해주세요. 구독과 좋아요도 부탁드립니다!',
    },
    {
      type: 'outro',
      label: 'Outro (55~60초)',
      text: '다음 영상에서는 더 깊은 내용을 다룰 예정입니다. 그때 또 만나요!',
    },
  ]
}

const blockTypeColors: Record<string, string> = {
  hook: 'border-l-red-500 bg-red-50',
  intro: 'border-l-blue-500 bg-blue-50',
  body: 'border-l-green-500 bg-green-50',
  cta: 'border-l-amber-500 bg-amber-50',
  outro: 'border-l-purple-500 bg-purple-50',
}

export default function AIPlannerModal({ onClose }: AIPlannerModalProps) {
  const router = useRouter()
  const [step, setStep] = useState<Step>(1)
  const [isLoading, setIsLoading] = useState(false)
  const [state, setState] = useState<PlannerState>({
    intent: '',
    platform: '',
    tone: '',
    duration: '',
    selectedTemplateId: null,
  })
  const [recommendations, setRecommendations] = useState<RecommendedTemplate[]>([])
  const [scriptBlocks, setScriptBlocks] = useState<ScriptBlock[]>([])

  const canProceed = useCallback((): boolean => {
    switch (step) {
      case 1:
        return state.intent.trim().length > 0
      case 2:
        return true
      case 3:
        return state.selectedTemplateId !== null
      case 4:
        return true
      case 5:
        return true
      default:
        return false
    }
  }, [step, state.intent, state.selectedTemplateId])

  const handleNext = async () => {
    if (step === 2) {
      setIsLoading(true)
      await new Promise((resolve) => setTimeout(resolve, 1500))
      const recs = generateMockRecommendations(state)
      setRecommendations(recs)
      setIsLoading(false)
      setStep(3)
      return
    }

    if (step === 3 && state.selectedTemplateId) {
      const blocks = generateMockScript(state.selectedTemplateId)
      setScriptBlocks(blocks)
      setStep(4)
      return
    }

    if (step === 4) {
      setStep(5)
      return
    }

    if (step < 5) {
      setStep((step + 1) as Step)
    }
  }

  const handleBack = () => {
    if (step > 1) {
      setStep((step - 1) as Step)
    }
  }

  const handleGoToStudio = () => {
    const scriptPreset = encodeURIComponent(JSON.stringify(scriptBlocks))
    router.push(`/studio?template=${state.selectedTemplateId}&scriptPreset=${scriptPreset}`)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#DDDBDA]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-r from-[#00A1E0] to-[#5867E8] rounded-lg flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="text-base font-bold text-[#16325C]">AI 기획 도우미</h2>
              <p className="text-xs text-[#706E6B]">
                Step {step}/5 - {STEP_TITLES[step]}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-[#F3F2F2] rounded transition-colors"
          >
            <X className="w-5 h-5 text-[#706E6B]" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="h-1 bg-[#F3F2F2]">
          <div
            className="h-full bg-gradient-to-r from-[#00A1E0] to-[#5867E8] transition-all duration-300"
            style={{ width: `${(step / 5) * 100}%` }}
          />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Step 1: Intent Input */}
          {step === 1 && (
            <div>
              <label className="block text-sm font-semibold text-[#16325C] mb-2">
                어떤 영상을 만들고 싶으신가요?
              </label>
              <textarea
                value={state.intent}
                onChange={(e) => setState({ ...state, intent: e.target.value })}
                placeholder='예: "IT 스타트업 투자자 소개 영상", "요리 튜토리얼", "여행 브이로그"'
                className="w-full h-32 px-4 py-3 border border-[#DDDBDA] rounded-lg text-sm text-[#3E3E3C] placeholder:text-[#DDDBDA] focus:outline-none focus:border-[#00A1E0] focus:ring-1 focus:ring-[#00A1E0] resize-none"
                autoFocus
              />
              <p className="mt-2 text-xs text-[#706E6B]">
                영상의 주제, 목적, 타겟 등을 자유롭게 입력해주세요.
              </p>
            </div>
          )}

          {/* Step 2: Details Selection */}
          {step === 2 && (
            <div className="space-y-6">
              {/* Platform */}
              <div>
                <label className="block text-sm font-semibold text-[#16325C] mb-2">
                  목표 플랫폼
                </label>
                <div className="flex gap-2">
                  {PLATFORM_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setState({ ...state, platform: opt.value })}
                      className={`px-4 py-2 rounded-lg border text-sm font-medium transition-all ${
                        state.platform === opt.value
                          ? opt.color + ' border-2'
                          : 'border-[#DDDBDA] text-[#706E6B] hover:border-[#00A1E0]'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tone */}
              <div>
                <label className="block text-sm font-semibold text-[#16325C] mb-2">
                  분위기
                </label>
                <div className="flex gap-2">
                  {TONE_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setState({ ...state, tone: opt.value })}
                      className={`px-4 py-2 rounded-lg border text-sm font-medium transition-all ${
                        state.tone === opt.value
                          ? 'border-[#00A1E0] bg-[#00A1E0]/10 text-[#00A1E0] border-2'
                          : 'border-[#DDDBDA] text-[#706E6B] hover:border-[#00A1E0]'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Duration */}
              <div>
                <label className="block text-sm font-semibold text-[#16325C] mb-2">
                  영상 길이
                </label>
                <div className="flex gap-2">
                  {DURATION_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setState({ ...state, duration: opt.value })}
                      className={`px-4 py-2 rounded-lg border text-sm font-medium transition-all ${
                        state.duration === opt.value
                          ? 'border-[#00A1E0] bg-[#00A1E0]/10 text-[#00A1E0] border-2'
                          : 'border-[#DDDBDA] text-[#706E6B] hover:border-[#00A1E0]'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 3: AI Recommendations */}
          {step === 3 && (
            <div>
              {isLoading ? (
                <div className="flex flex-col items-center justify-center py-16">
                  <Loader2 className="w-8 h-8 text-[#00A1E0] animate-spin mb-3" />
                  <p className="text-sm text-[#706E6B]">AI가 최적의 템플릿을 찾고 있습니다...</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {recommendations.map((rec) => (
                    <button
                      key={rec.id}
                      onClick={() => setState({ ...state, selectedTemplateId: rec.id })}
                      className={`w-full text-left flex items-start gap-4 p-4 rounded-lg border transition-all ${
                        state.selectedTemplateId === rec.id
                          ? 'border-[#00A1E0] bg-[#00A1E0]/5 shadow-sm'
                          : 'border-[#DDDBDA] hover:border-[#00A1E0]/50'
                      }`}
                    >
                      {/* Thumbnail */}
                      <div
                        className="w-20 h-14 rounded-md flex items-center justify-center shrink-0"
                        style={{ backgroundColor: rec.thumbnailColor }}
                      >
                        <span className="text-white text-xs font-bold text-center px-1 truncate">
                          {rec.name}
                        </span>
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-bold text-[#16325C]">{rec.name}</span>
                          <span className="text-[10px] font-semibold text-[#00A1E0] bg-[#00A1E0]/10 px-1.5 py-0.5 rounded">
                            {rec.matchScore}% 일치
                          </span>
                        </div>
                        <p className="text-xs text-[#706E6B]">{rec.reason}</p>
                      </div>

                      {/* Selected indicator */}
                      {state.selectedTemplateId === rec.id && (
                        <CheckCircle2 className="w-5 h-5 text-[#00A1E0] shrink-0 mt-1" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Step 4: Script Draft */}
          {step === 4 && (
            <div className="space-y-3">
              <p className="text-xs text-[#706E6B] mb-4">
                선택한 템플릿을 기반으로 생성된 스크립트 초안입니다. 스튜디오에서 자유롭게 수정할 수 있습니다.
              </p>
              {scriptBlocks.map((block, index) => (
                <div
                  key={index}
                  className={`border-l-4 rounded-r-lg p-4 ${blockTypeColors[block.type]}`}
                >
                  <div className="text-xs font-bold text-[#16325C] mb-1">{block.label}</div>
                  <p className="text-sm text-[#3E3E3C] leading-relaxed">{block.text}</p>
                </div>
              ))}
            </div>
          )}

          {/* Step 5: Ready */}
          {step === 5 && (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="w-16 h-16 bg-[#4BCA81]/10 rounded-full flex items-center justify-center mb-4">
                <CheckCircle2 className="w-8 h-8 text-[#4BCA81]" />
              </div>
              <h3 className="text-lg font-bold text-[#16325C] mb-2">모든 준비가 완료되었습니다!</h3>
              <p className="text-sm text-[#706E6B] text-center mb-6 max-w-sm">
                선택한 템플릿과 스크립트 초안이 스튜디오에 자동으로 적용됩니다.
                스튜디오에서 세부 편집을 진행해주세요.
              </p>
              <button
                onClick={handleGoToStudio}
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#00A1E0] to-[#5867E8] text-white font-semibold rounded-lg hover:from-[#0090c7] hover:to-[#4a58d4] transition-all shadow-md"
              >
                <Play className="w-4 h-4" />
                스튜디오에서 편집하기
              </button>
            </div>
          )}
        </div>

        {/* Footer Navigation */}
        {step < 5 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-[#DDDBDA]">
            <button
              onClick={handleBack}
              disabled={step === 1}
              className={`flex items-center gap-1 text-sm font-medium transition-colors ${
                step === 1
                  ? 'text-[#DDDBDA] cursor-not-allowed'
                  : 'text-[#706E6B] hover:text-[#16325C]'
              }`}
            >
              <ArrowLeft className="w-4 h-4" />
              이전
            </button>

            <button
              onClick={handleNext}
              disabled={!canProceed() || isLoading}
              className={`flex items-center gap-1 px-5 py-2 text-sm font-semibold rounded-lg transition-all ${
                canProceed() && !isLoading
                  ? 'bg-[#00A1E0] text-white hover:bg-[#0090c7]'
                  : 'bg-[#DDDBDA] text-white cursor-not-allowed'
              }`}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  분석 중...
                </>
              ) : (
                <>
                  다음
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
