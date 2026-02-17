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

  // localStorage 자동 저장 복구
  useEffect(() => {
    try {
      const saved = localStorage.getItem('production_state');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.projectId && parsed.currentStep) {
          // 복구 가능한 상태가 있을 경우 콘솔에만 로그 (실제 복구는 ProductionContext에서 처리)
          console.log('[Production] 저장된 작업 상태 발견:', parsed.projectId);
        }
      }
    } catch {
      // 저장된 상태가 없거나 파싱 실패 시 무시
    }
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

// ==================== Marketer Panel ====================

function MarketerPanel() {
  const { state } = useProduction();
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [thumbnailPrompt, setThumbnailPrompt] = React.useState('');
  const [marketingCopy, setMarketingCopy] = React.useState<{
    title: string;
    description: string;
    hashtags: string[];
  } | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const generateMarketingContent = async () => {
    if (!state.script?.content) {
      setError('스크립트가 없습니다. Director 단계를 먼저 완료하세요.');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const res = await fetch('/api/writer-generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: state.projectTopic || '영상 제목',
          platform: state.platform || 'YouTube',
          mode: 'marketing',
          script: state.script.content,
        }),
      });

      if (!res.ok) throw new Error('마케팅 카피 생성 실패');

      const data = await res.json();
      setMarketingCopy({
        title: data.title || `${state.projectTopic} - ${state.platform}`,
        description: data.description || state.script.content.slice(0, 150) + '...',
        hashtags: data.hashtags || ['#AI영상', '#자동화', '#콘텐츠'],
      });

      const concept = [state.projectTopic, state.platform, 'professional thumbnail'].join(', ');
      setThumbnailPrompt(data.thumbnail_prompt || concept);
    } catch (err) {
      setError(err instanceof Error ? err.message : '생성 중 오류가 발생했습니다');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900">Marketer Agent</h2>
        <p className="text-sm text-gray-600 mt-1">썸네일 프롬프트와 마케팅 카피를 생성합니다.</p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 썸네일 프롬프트 */}
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-5 h-5 text-[#00A1E0]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <h3 className="font-semibold text-gray-900">썸네일 프롬프트</h3>
          </div>
          {thumbnailPrompt ? (
            <div className="bg-gray-50 rounded p-3 text-sm text-gray-700 min-h-[80px]">
              {thumbnailPrompt}
            </div>
          ) : (
            <div className="bg-gray-50 rounded p-3 text-sm text-gray-400 min-h-[80px] flex items-center justify-center">
              생성 버튼을 클릭하세요
            </div>
          )}
        </div>

        {/* 마케팅 카피 */}
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-5 h-5 text-[#00A1E0]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="font-semibold text-gray-900">마케팅 카피</h3>
          </div>
          {marketingCopy ? (
            <div className="space-y-2">
              <div>
                <span className="text-xs font-medium text-gray-500">제목</span>
                <p className="text-sm text-gray-900 font-medium">{marketingCopy.title}</p>
              </div>
              <div>
                <span className="text-xs font-medium text-gray-500">설명</span>
                <p className="text-sm text-gray-700 line-clamp-3">{marketingCopy.description}</p>
              </div>
              <div className="flex flex-wrap gap-1">
                {marketingCopy.hashtags.map((tag) => (
                  <span key={tag} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-sm text-gray-400 min-h-[80px] flex items-center justify-center">
              생성 버튼을 클릭하세요
            </div>
          )}
        </div>
      </div>

      <div className="mt-6 flex justify-end">
        <button
          onClick={generateMarketingContent}
          disabled={isGenerating}
          className="px-6 py-2.5 bg-[#00A1E0] text-white rounded-lg font-medium text-sm
            hover:bg-[#0088BF] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isGenerating ? (
            <>
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              생성 중...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              마케팅 콘텐츠 생성
            </>
          )}
        </button>
      </div>
    </div>
  );
}

// ==================== Deployment Panel ====================

function DeploymentPanel() {
  const { state } = useProduction();
  const [selectedPlatforms, setSelectedPlatforms] = React.useState<string[]>([]);
  const [isDeploying, setIsDeploying] = React.useState(false);
  const [deployStatus, setDeployStatus] = React.useState<'idle' | 'success' | 'error'>('idle');

  const platforms = [
    { id: 'youtube', name: 'YouTube', icon: '▶', color: 'bg-red-100 text-red-700 border-red-200' },
    { id: 'instagram', name: 'Instagram', icon: '◈', color: 'bg-pink-100 text-pink-700 border-pink-200' },
    { id: 'tiktok', name: 'TikTok', icon: '◎', color: 'bg-gray-100 text-gray-700 border-gray-200' },
  ];

  const togglePlatform = (id: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const handleDeploy = async () => {
    if (selectedPlatforms.length === 0) return;
    if (!state.video?.file_path) {
      alert('영상이 없습니다. Director 단계를 완료하세요.');
      return;
    }

    setIsDeploying(true);
    setDeployStatus('idle');

    // 배포 시뮬레이션 (실제 플랫폼 API 연동 시 여기를 교체)
    await new Promise((resolve) => setTimeout(resolve, 2000));

    setIsDeploying(false);
    setDeployStatus('success');
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900">Deployment</h2>
        <p className="text-sm text-gray-600 mt-1">완성된 영상을 플랫폼에 배포합니다.</p>
      </div>

      {/* 영상 상태 확인 */}
      <div className="mb-6 p-4 border border-gray-200 rounded-lg">
        <h3 className="font-semibold text-gray-900 mb-3">배포 준비 상태</h3>
        <div className="space-y-2">
          {[
            { label: '스크립트', done: !!state.script },
            { label: '오디오', done: !!state.audio },
            { label: '영상', done: !!state.video },
          ].map(({ label, done }) => (
            <div key={label} className="flex items-center gap-2 text-sm">
              <div className={`w-4 h-4 rounded-full flex items-center justify-center ${done ? 'bg-green-500' : 'bg-gray-200'}`}>
                {done && (
                  <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </div>
              <span className={done ? 'text-gray-900' : 'text-gray-400'}>{label}</span>
              {!done && <span className="text-gray-400 text-xs">(미완료)</span>}
            </div>
          ))}
        </div>
      </div>

      {/* 플랫폼 선택 */}
      <div className="mb-6">
        <h3 className="font-semibold text-gray-900 mb-3">배포 플랫폼 선택</h3>
        <div className="flex flex-wrap gap-3">
          {platforms.map((platform) => (
            <button
              key={platform.id}
              onClick={() => togglePlatform(platform.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border-2 text-sm font-medium transition-all ${
                selectedPlatforms.includes(platform.id)
                  ? platform.color + ' border-current'
                  : 'bg-white text-gray-500 border-gray-200 hover:border-gray-300'
              }`}
            >
              <span>{platform.icon}</span>
              {platform.name}
              {selectedPlatforms.includes(platform.id) && (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 배포 결과 */}
      {deployStatus === 'success' && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="text-sm font-medium text-green-900">배포 완료!</p>
            <p className="text-sm text-green-700">
              {selectedPlatforms.map((id) => platforms.find((p) => p.id === id)?.name).join(', ')}에
              성공적으로 배포 요청을 전달했습니다.
            </p>
          </div>
        </div>
      )}

      <div className="flex justify-end">
        <button
          onClick={handleDeploy}
          disabled={isDeploying || selectedPlatforms.length === 0 || !state.video}
          className="px-6 py-2.5 bg-[#16325C] text-white rounded-lg font-medium text-sm
            hover:bg-[#0d1e38] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isDeploying ? (
            <>
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              배포 중...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              배포하기 {selectedPlatforms.length > 0 && `(${selectedPlatforms.length}개)`}
            </>
          )}
        </button>
      </div>
    </div>
  );
}
