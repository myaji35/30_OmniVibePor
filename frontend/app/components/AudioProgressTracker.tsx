'use client'

import { useState, useEffect } from 'react'
import { Check, X, Loader2, Mic2 } from 'lucide-react'

interface ProgressStep {
  id: string
  label: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  message?: string
  progress?: number
}

interface AudioProgressTrackerProps {
  isGenerating: boolean
  currentStep?: string
  similarity?: number
  attempt?: number
  maxAttempts?: number
}

export default function AudioProgressTracker({
  isGenerating,
  currentStep = '',
  similarity = 0,
  attempt = 1,
  maxAttempts = 5
}: AudioProgressTrackerProps) {
  const [steps, setSteps] = useState<ProgressStep[]>([
    { id: 'load', label: '스크립트 로드', status: 'pending' },
    { id: 'tts', label: 'TTS 생성', status: 'pending' },
    { id: 'stt', label: 'STT 검증', status: 'pending' },
    { id: 'accuracy', label: '정확도 계산', status: 'pending' },
    { id: 'save', label: '오디오 저장', status: 'pending' }
  ])

  useEffect(() => {
    if (!isGenerating) {
      setSteps(prev => prev.map(step => ({ ...step, status: 'pending', message: undefined, progress: undefined })))
      return
    }

    const newSteps: ProgressStep[] = [
      { id: 'load', label: '스크립트 로드', status: 'pending' },
      { id: 'tts', label: 'TTS 생성', status: 'pending' },
      { id: 'stt', label: 'STT 검증', status: 'pending' },
      { id: 'accuracy', label: '정확도 계산', status: 'pending' },
      { id: 'save', label: '오디오 저장', status: 'pending' }
    ]

    switch (currentStep) {
      case 'load':
        newSteps[0].status = 'in_progress'
        break

      case 'generate_tts':
        newSteps[0].status = 'completed'
        newSteps[1].status = 'in_progress'
        newSteps[1].message = `시도 ${attempt}/${maxAttempts}`
        break

      case 'verify_stt':
        newSteps[0].status = 'completed'
        newSteps[1].status = 'completed'
        newSteps[2].status = 'in_progress'
        break

      case 'check_accuracy':
        newSteps[0].status = 'completed'
        newSteps[1].status = 'completed'
        newSteps[2].status = 'completed'
        newSteps[3].status = 'in_progress'
        newSteps[3].message = similarity > 0 ? `유사도: ${(similarity * 100).toFixed(1)}%` : ''
        newSteps[3].progress = similarity * 100
        break

      case 'save_audio':
        newSteps[0].status = 'completed'
        newSteps[1].status = 'completed'
        newSteps[2].status = 'completed'
        newSteps[3].status = 'completed'
        newSteps[4].status = 'in_progress'
        break

      case 'completed':
        newSteps.forEach(step => step.status = 'completed')
        newSteps[4].message = '생성 완료!'
        break

      case 'failed':
        newSteps[0].status = 'completed'
        // 마지막 in_progress였던 단계를 failed로
        for (let i = 1; i < newSteps.length; i++) {
          if (newSteps[i - 1].status === 'completed' && newSteps[i].status === 'pending') {
            newSteps[i].status = 'failed'
            break
          }
        }
        break
    }

    setSteps(newSteps)
  }, [currentStep, isGenerating, similarity, attempt, maxAttempts])

  if (!isGenerating && currentStep !== 'completed') return null

  return (
    <div>
      <div className="flex items-center gap-2 mb-5">
        <Mic2 className="w-5 h-5 text-purple-400" />
        <h3 className="text-base font-bold text-white/90">오디오 생성 진행 상황</h3>
      </div>

      <div className="relative">
        {steps.map((step, index) => {
          const isLast = index === steps.length - 1

          return (
            <div key={step.id} className="flex gap-4" style={{ minHeight: isLast ? 'auto' : '64px' }}>
              {/* 아이콘 + 연결선 컬럼 */}
              <div className="flex flex-col items-center">
                {/* 원형 아이콘 */}
                <div className={`relative z-10 w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold shrink-0 transition-all duration-300 ${
                  step.status === 'completed'
                    ? 'bg-emerald-500 text-white shadow-[0_0_12px_rgba(16,185,129,0.4)]'
                    : step.status === 'in_progress'
                    ? 'bg-purple-500 text-white shadow-[0_0_16px_rgba(168,85,247,0.5)]'
                    : step.status === 'failed'
                    ? 'bg-red-500 text-white shadow-[0_0_12px_rgba(239,68,68,0.4)]'
                    : 'bg-white/[0.08] text-white/30 border border-white/10'
                }`}>
                  {step.status === 'completed' && <Check className="w-4 h-4" strokeWidth={3} />}
                  {step.status === 'in_progress' && <Loader2 className="w-4 h-4 animate-spin" />}
                  {step.status === 'failed' && <X className="w-4 h-4" strokeWidth={3} />}
                  {step.status === 'pending' && <span className="text-xs">{index + 1}</span>}
                </div>

                {/* 연결선 */}
                {!isLast && (
                  <div className={`w-0.5 flex-1 my-1 transition-colors duration-300 ${
                    step.status === 'completed' ? 'bg-emerald-500/60' : 'bg-white/[0.06]'
                  }`} />
                )}
              </div>

              {/* 라벨 + 메시지 */}
              <div className="pt-1.5 pb-3 flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className={`text-sm font-semibold transition-colors duration-300 ${
                    step.status === 'completed' ? 'text-emerald-400'
                    : step.status === 'in_progress' ? 'text-white'
                    : step.status === 'failed' ? 'text-red-400'
                    : 'text-white/30'
                  }`}>
                    {step.label}
                  </span>
                  {step.message && (
                    <span className={`text-xs font-mono ${
                      step.status === 'in_progress' ? 'text-purple-300' : 'text-white/50'
                    }`}>
                      {step.message}
                    </span>
                  )}
                </div>

                {/* 프로그레스 바 (정확도 단계) */}
                {step.status === 'in_progress' && step.progress !== undefined && (
                  <div className="mt-2 w-full h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        step.progress >= 85 ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]'
                        : step.progress >= 70 ? 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.3)]'
                        : 'bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.3)]'
                      }`}
                      style={{ width: `${step.progress}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* 재시도 알림 */}
      {attempt > 1 && attempt <= maxAttempts && (
        <div className="mt-4 px-3 py-2.5 rounded-lg"
          style={{ background: 'rgba(251,191,36,0.1)', border: '1px solid rgba(251,191,36,0.25)' }}>
          <p className="text-xs text-amber-300 font-medium">
            정확도 임계값 미달로 재시도 중 ({attempt}/{maxAttempts})
          </p>
        </div>
      )}

      {/* 완료 메시지 */}
      {currentStep === 'completed' && (
        <div className="mt-4 px-3 py-2.5 rounded-lg"
          style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)' }}>
          <p className="text-xs text-emerald-300 font-medium">
            오디오 생성 완료 — 유사도 {(similarity * 100).toFixed(1)}%
          </p>
        </div>
      )}
    </div>
  )
}
