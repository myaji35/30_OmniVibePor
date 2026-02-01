"use client";

/**
 * ProductionDashboard - 통합 프로덕션 대시보드
 *
 * REALPLAN.md Phase 2.1 구현
 *
 * 4단계 진행 바 + WriterPanel/DirectorPanel 자동 전환
 */

import React, { useEffect } from 'react';
import {
  useProduction,
  getStepName,
  type ProductionStep,
} from '@/lib/contexts/ProductionContext';
import WriterPanel from './WriterPanel';
import DirectorPanel from './DirectorPanel';

export default function ProductionDashboard() {
  const { state, setStep, canProceedToDirector, canProceedToMarketer, canProceedToDeployment } =
    useProduction();

  // 자동 저장 복구 (Phase 2.4에서 구현 예정)
  useEffect(() => {
    // TODO: localStorage에서 자동 저장된 데이터 복구
  }, []);

  const steps: ProductionStep[] = ['writer', 'director', 'marketer', 'deployment'];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          {/* Project Info */}
          {state.projectId ? (
            <div className="flex justify-between items-center mb-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{state.projectTitle}</h1>
                <p className="text-sm text-gray-600 mt-1">{state.projectTopic}</p>
              </div>
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium capitalize">
                {state.platform}
              </span>
            </div>
          ) : (
            <h1 className="text-2xl font-bold text-gray-900 mb-4">영상 제작</h1>
          )}

          {/* Progress Steps */}
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const isActive = state.currentStep === step;
              const isCompleted = steps.indexOf(step) < steps.indexOf(state.currentStep);
              const isEnabled =
                step === 'writer' ||
                (step === 'director' && canProceedToDirector) ||
                (step === 'marketer' && canProceedToMarketer) ||
                (step === 'deployment' && canProceedToDeployment);

              return (
                <React.Fragment key={step}>
                  {/* Step Button */}
                  <button
                    onClick={() => isEnabled && setStep(step)}
                    disabled={!isEnabled}
                    className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-all ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-lg'
                        : isCompleted
                        ? 'bg-green-100 text-green-800 hover:bg-green-200'
                        : isEnabled
                        ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        : 'bg-gray-50 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {/* Icon */}
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${
                        isActive
                          ? 'bg-white text-blue-600'
                          : isCompleted
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-200 text-gray-600'
                      }`}
                    >
                      {isCompleted ? (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={3}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      ) : (
                        index + 1
                      )}
                    </div>

                    {/* Label */}
                    <span className="font-medium">{getStepName(step)}</span>
                  </button>

                  {/* Connector */}
                  {index < steps.length - 1 && (
                    <div className="flex-1 h-1 mx-2">
                      <div
                        className={`h-full rounded transition-all ${
                          isCompleted ? 'bg-green-500' : 'bg-gray-200'
                        }`}
                      />
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {/* Progress Bar */}
          <div className="mt-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-medium text-gray-600">전체 진행률</span>
              <span className="text-xs font-semibold text-gray-900">{state.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${state.progress}%` }}
              />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Display */}
        {state.error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <svg className="w-5 h-5 text-red-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-900">오류 발생</h3>
              <p className="text-sm text-red-700 mt-1">{state.error}</p>
            </div>
          </div>
        )}

        {/* Step Panels */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
          {state.currentStep === 'writer' && <WriterPanel />}
          {state.currentStep === 'director' && <DirectorPanel />}
          {state.currentStep === 'marketer' && <MarketerPanel />}
          {state.currentStep === 'deployment' && <DeploymentPanel />}
        </div>
      </main>
    </div>
  );
}

// ==================== Placeholder Panels ====================

function MarketerPanel() {
  return (
    <div className="p-8 text-center">
      <div className="max-w-md mx-auto">
        <div className="text-6xl mb-4">🎨</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Marketer Agent</h2>
        <p className="text-gray-600">
          썸네일과 마케팅 카피를 생성하는 기능은 Phase 4에서 구현됩니다.
        </p>
      </div>
    </div>
  );
}

function DeploymentPanel() {
  return (
    <div className="p-8 text-center">
      <div className="max-w-md mx-auto">
        <div className="text-6xl mb-4">🚀</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Deployment</h2>
        <p className="text-gray-600">
          플랫폼 배포 기능은 Phase 5에서 구현됩니다.
        </p>
      </div>
    </div>
  );
}
