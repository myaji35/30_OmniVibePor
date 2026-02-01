"use client";

/**
 * ProductionWorkflow - 영상 제작 워크플로우 UI
 *
 * REALPLAN.md Phase 1.5 구현
 *
 * Writer → Director → Marketer → Deployment 단계별 진행
 */

import React from 'react';
import {
  useProduction,
  getStepName,
  getStepDescription,
  calculateStepProgress,
  type ProductionStep,
} from '@/lib/contexts/ProductionContext';

// ==================== Component ====================

export default function ProductionWorkflow() {
  const { state, setStep, canProceedToDirector, canProceedToMarketer, canProceedToDeployment } =
    useProduction();

  const steps: ProductionStep[] = ['writer', 'director', 'marketer', 'deployment'];

  // 단계 활성화 여부
  function isStepEnabled(step: ProductionStep): boolean {
    if (step === 'writer') return true;
    if (step === 'director') return canProceedToDirector;
    if (step === 'marketer') return canProceedToMarketer;
    if (step === 'deployment') return canProceedToDeployment;
    return false;
  }

  // 단계 완료 여부
  function isStepCompleted(step: ProductionStep): boolean {
    const currentIndex = steps.indexOf(state.currentStep);
    const stepIndex = steps.indexOf(step);
    return stepIndex < currentIndex;
  }

  return (
    <div className="space-y-8">
      {/* Project Info */}
      {state.projectId && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{state.projectTitle}</h2>
              <p className="text-gray-600 mt-1">{state.projectTopic}</p>
            </div>
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium capitalize">
              {state.platform}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="mt-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">전체 진행률</span>
              <span className="text-sm font-medium text-gray-900">{state.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${state.progress}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Step Navigation */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex justify-between items-center mb-8">
          {steps.map((step, index) => {
            const isActive = state.currentStep === step;
            const isCompleted = isStepCompleted(step);
            const isEnabled = isStepEnabled(step);

            return (
              <React.Fragment key={step}>
                {/* Step Circle */}
                <div className="flex flex-col items-center flex-1">
                  <button
                    onClick={() => isEnabled && setStep(step)}
                    disabled={!isEnabled}
                    className={`w-16 h-16 rounded-full flex items-center justify-center font-semibold transition-all ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-lg scale-110'
                        : isCompleted
                        ? 'bg-green-500 text-white'
                        : isEnabled
                        ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {isCompleted ? (
                      <svg
                        className="w-8 h-8"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    ) : (
                      index + 1
                    )}
                  </button>

                  <span
                    className={`mt-3 text-sm font-medium ${
                      isActive ? 'text-blue-600' : isEnabled ? 'text-gray-700' : 'text-gray-400'
                    }`}
                  >
                    {getStepName(step)}
                  </span>

                  <span className="mt-1 text-xs text-gray-500 text-center max-w-[100px]">
                    {getStepDescription(step)}
                  </span>
                </div>

                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div className="flex-1 h-1 mx-4 -mt-20">
                    <div
                      className={`h-full rounded ${
                        isCompleted ? 'bg-green-500' : 'bg-gray-200'
                      }`}
                    />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Current Step Details */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {getStepName(state.currentStep)} 단계
          </h3>
          <p className="text-gray-600">{getStepDescription(state.currentStep)}</p>

          {/* Error Display */}
          {state.error && (
            <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {state.error}
            </div>
          )}

          {/* Loading Indicator */}
          {state.isLoading && (
            <div className="mt-4 flex items-center gap-3 text-gray-600">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
              <span>처리 중...</span>
            </div>
          )}
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        {state.currentStep === 'writer' && <WriterStepContent />}
        {state.currentStep === 'director' && <DirectorStepContent />}
        {state.currentStep === 'marketer' && <MarketerStepContent />}
        {state.currentStep === 'deployment' && <DeploymentStepContent />}
      </div>
    </div>
  );
}

// ==================== Step Content Components ====================

function WriterStepContent() {
  const { state, setScript } = useProduction();

  return (
    <div className="space-y-4">
      <h4 className="font-semibold text-gray-900">스크립트 작성</h4>
      <p className="text-gray-600 text-sm">
        주제를 기반으로 AI가 스크립트를 자동으로 생성합니다. 생성된 스크립트를 검토하고 수정할 수
        있습니다.
      </p>

      {state.script ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex justify-between items-start mb-3">
            <h5 className="font-medium text-gray-900">스크립트 #{state.script.version}</h5>
            <span className="text-sm text-gray-600">
              {state.script.word_count}자 | {Math.floor(state.script.estimated_duration / 60)}분{' '}
              {state.script.estimated_duration % 60}초
            </span>
          </div>
          <p className="text-gray-700 text-sm whitespace-pre-wrap line-clamp-5">
            {state.script.content}
          </p>
          <button className="mt-3 text-blue-600 hover:text-blue-700 text-sm font-medium">
            전체 보기 →
          </button>
        </div>
      ) : (
        <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
          <p className="text-gray-500 mb-4">스크립트를 생성하려면 Writer Agent를 실행하세요</p>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            스크립트 생성
          </button>
        </div>
      )}
    </div>
  );
}

function DirectorStepContent() {
  const { state } = useProduction();

  return (
    <div className="space-y-6">
      <h4 className="font-semibold text-gray-900">오디오 & 비디오 생성</h4>

      {/* Audio Section */}
      <div>
        <h5 className="text-sm font-medium text-gray-700 mb-2">오디오</h5>
        {state.audio ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="font-medium text-green-900">오디오 생성 완료</p>
                <p className="text-sm text-green-700 mt-1">
                  정확도: {(state.audio.stt_accuracy * 100).toFixed(1)}% | 길이:{' '}
                  {state.audio.duration.toFixed(1)}초
                </p>
              </div>
              <button className="text-green-600 hover:text-green-700">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
            <p className="text-gray-600 text-sm mb-3">오디오를 생성하세요</p>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              오디오 생성
            </button>
          </div>
        )}
      </div>

      {/* Video Section */}
      <div>
        <h5 className="text-sm font-medium text-gray-700 mb-2">비디오</h5>
        {state.video ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="font-medium text-green-900">비디오 생성 완료</p>
                <p className="text-sm text-green-700 mt-1">
                  {state.video.resolution} | {state.video.format} |{' '}
                  {state.video.lipsync_enabled ? '립싱크 적용' : '립싱크 미적용'}
                </p>
              </div>
              <button className="text-green-600 hover:text-green-700">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
            <p className="text-gray-600 text-sm mb-3">비디오를 생성하세요</p>
            <button
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              disabled={!state.audio}
            >
              비디오 생성
            </button>
            {!state.audio && (
              <p className="text-xs text-gray-500 mt-2">오디오를 먼저 생성해야 합니다</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function MarketerStepContent() {
  return (
    <div className="space-y-4">
      <h4 className="font-semibold text-gray-900">썸네일 & 카피 생성</h4>
      <p className="text-gray-600 text-sm">
        AI가 플랫폼에 최적화된 썸네일과 마케팅 카피를 생성합니다.
      </p>
      <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
        <p className="text-gray-500">Marketer Agent는 추후 구현됩니다</p>
      </div>
    </div>
  );
}

function DeploymentStepContent() {
  return (
    <div className="space-y-4">
      <h4 className="font-semibold text-gray-900">플랫폼 배포</h4>
      <p className="text-gray-600 text-sm">
        완성된 영상을 선택한 플랫폼에 자동으로 배포합니다.
      </p>
      <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
        <p className="text-gray-500">Deployment 기능은 추후 구현됩니다</p>
      </div>
    </div>
  );
}
