'use client'

import { useState, useEffect } from 'react'

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
      setSteps(prev => prev.map(step => ({ ...step, status: 'pending' })))
      return
    }

    const newSteps = [...steps]

    switch (currentStep) {
      case 'generate_tts':
        newSteps[0].status = 'completed'
        newSteps[1].status = 'in_progress'
        newSteps[1].message = `시도 ${attempt}/${maxAttempts}`
        break

      case 'verify_stt':
        newSteps[1].status = 'completed'
        newSteps[2].status = 'in_progress'
        break

      case 'check_accuracy':
        newSteps[2].status = 'completed'
        newSteps[3].status = 'in_progress'
        newSteps[3].message = similarity > 0 ? `유사도: ${(similarity * 100).toFixed(1)}%` : ''
        newSteps[3].progress = similarity * 100
        break

      case 'save_audio':
        newSteps[3].status = 'completed'
        newSteps[4].status = 'in_progress'
        break

      case 'completed':
        newSteps.forEach(step => step.status = 'completed')
        newSteps[4].status = 'completed'
        newSteps[4].message = '생성 완료!'
        break

      case 'failed':
        newSteps.forEach(step => {
          if (step.status === 'in_progress') step.status = 'failed'
        })
        break
    }

    setSteps(newSteps)
  }, [currentStep, isGenerating, similarity, attempt, maxAttempts])

  if (!isGenerating && currentStep !== 'completed') return null

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
      <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
        <span className="animate-pulse">🎵</span>
        오디오 생성 진행 상황
      </h3>

      <div className="space-y-4">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center gap-4">
            {/* Status Icon */}
            <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center border-2 ${
              step.status === 'completed'
                ? 'bg-green-500 border-green-400'
                : step.status === 'in_progress'
                ? 'bg-blue-500 border-blue-400 animate-pulse'
                : step.status === 'failed'
                ? 'bg-red-500 border-red-400'
                : 'bg-gray-700 border-gray-600'
            }`}>
              {step.status === 'completed' && '✓'}
              {step.status === 'in_progress' && (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              )}
              {step.status === 'failed' && '✗'}
              {step.status === 'pending' && index + 1}
            </div>

            {/* Step Info */}
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <h4 className={`font-semibold ${
                  step.status === 'completed' ? 'text-green-400'
                  : step.status === 'in_progress' ? 'text-blue-400'
                  : step.status === 'failed' ? 'text-red-400'
                  : 'text-gray-400'
                }`}>
                  {step.label}
                </h4>
                {step.message && (
                  <span className="text-sm text-gray-300">{step.message}</span>
                )}
              </div>

              {/* Progress Bar */}
              {step.status === 'in_progress' && step.progress !== undefined && (
                <div className="mt-2 w-full bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      step.progress >= 85 ? 'bg-green-500'
                      : step.progress >= 70 ? 'bg-yellow-500'
                      : 'bg-blue-500'
                    }`}
                    style={{ width: `${step.progress}%` }}
                  />
                </div>
              )}

              {/* Connecting Line */}
              {index < steps.length - 1 && (
                <div className={`ml-5 mt-2 w-0.5 h-8 ${
                  step.status === 'completed' ? 'bg-green-500' : 'bg-gray-700'
                }`} />
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Retry Info */}
      {attempt > 1 && attempt <= maxAttempts && (
        <div className="mt-6 p-4 bg-yellow-500/20 border border-yellow-500/30 rounded-lg">
          <p className="text-sm text-yellow-200">
            ⚠️ 정확도 임계값 미달로 재시도 중... ({attempt}/{maxAttempts})
          </p>
        </div>
      )}

      {/* Success Message */}
      {currentStep === 'completed' && (
        <div className="mt-6 p-4 bg-green-500/20 border border-green-500/30 rounded-lg">
          <p className="text-sm text-green-200">
            ✅ 오디오 생성 완료! 유사도: {(similarity * 100).toFixed(1)}%
          </p>
        </div>
      )}
    </div>
  )
}
