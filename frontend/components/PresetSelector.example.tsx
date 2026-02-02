/**
 * PresetSelector 사용 예시
 *
 * 이 컴포넌트는 플랫폼별 프리셋과 커스텀 프리셋을 선택할 수 있는 UI를 제공합니다.
 */

import React, { useState } from 'react';
import PresetSelector from './PresetSelector';

// ==================== Example 1: 기본 사용 ====================

export function BasicExample() {
  const projectId = 'project-123';

  return (
    <div className="p-8">
      <PresetSelector projectId={projectId} />
    </div>
  );
}

// ==================== Example 2: 콜백 함수 활용 ====================

export function WithCallbacksExample() {
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<'platform' | 'custom' | null>(null);
  const [isApplied, setIsApplied] = useState(false);

  return (
    <div className="p-8">
      <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">선택 정보</h3>
        <p className="text-sm text-blue-700">
          선택한 프리셋: {selectedPresetId || '없음'} ({selectedType || 'N/A'})
        </p>
        <p className="text-sm text-blue-700">적용 상태: {isApplied ? '✓ 적용됨' : '미적용'}</p>
      </div>

      <PresetSelector
        projectId="project-123"
        onPresetSelected={(presetId, type) => {
          setSelectedPresetId(presetId);
          setSelectedType(type);
          setIsApplied(false);
        }}
        onPresetApplied={() => {
          setIsApplied(true);
          alert('프리셋이 성공적으로 적용되었습니다!');
        }}
      />
    </div>
  );
}

// ==================== Example 3: 모달 내부 사용 ====================

export function ModalExample() {
  const [showModal, setShowModal] = useState(false);

  return (
    <div className="p-8">
      <button
        onClick={() => setShowModal(true)}
        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        프리셋 선택 모달 열기
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex justify-between items-center">
              <h2 className="text-xl font-bold">프리셋 선택</h2>
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-900"
              >
                닫기
              </button>
            </div>

            <div className="p-6">
              <PresetSelector
                projectId="project-123"
                onPresetApplied={() => {
                  setShowModal(false);
                  alert('프리셋이 적용되었습니다!');
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== Example 4: 워크플로우 통합 ====================

export function WorkflowIntegrationExample() {
  const [step, setStep] = useState<'select-preset' | 'configure' | 'done'>('select-preset');
  const [selectedPreset, setSelectedPreset] = useState<{
    id: string;
    type: 'platform' | 'custom';
  } | null>(null);

  return (
    <div className="p-8">
      {/* Progress Steps */}
      <div className="mb-8 flex items-center justify-center">
        <div className="flex items-center gap-4">
          <div
            className={`px-4 py-2 rounded-lg ${
              step === 'select-preset'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-600'
            }`}
          >
            1. 프리셋 선택
          </div>
          <div className="w-8 h-0.5 bg-gray-300" />
          <div
            className={`px-4 py-2 rounded-lg ${
              step === 'configure' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
            }`}
          >
            2. 세부 설정
          </div>
          <div className="w-8 h-0.5 bg-gray-300" />
          <div
            className={`px-4 py-2 rounded-lg ${
              step === 'done' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
            }`}
          >
            3. 완료
          </div>
        </div>
      </div>

      {/* Step Content */}
      {step === 'select-preset' && (
        <PresetSelector
          projectId="project-123"
          onPresetSelected={(presetId, type) => {
            setSelectedPreset({ id: presetId, type });
          }}
          onPresetApplied={() => {
            setStep('configure');
          }}
        />
      )}

      {step === 'configure' && (
        <div className="text-center py-12">
          <h3 className="text-2xl font-bold mb-4">세부 설정</h3>
          <p className="text-gray-600 mb-6">
            선택한 프리셋: {selectedPreset?.id} ({selectedPreset?.type})
          </p>
          <button
            onClick={() => setStep('done')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            설정 완료
          </button>
        </div>
      )}

      {step === 'done' && (
        <div className="text-center py-12">
          <h3 className="text-2xl font-bold mb-4 text-green-600">완료!</h3>
          <p className="text-gray-600 mb-6">프리셋이 성공적으로 적용되었습니다.</p>
          <button
            onClick={() => {
              setStep('select-preset');
              setSelectedPreset(null);
            }}
            className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            다시 시작
          </button>
        </div>
      )}
    </div>
  );
}

// ==================== 사용 예시 모음 ====================

export default function PresetSelectorExamples() {
  const [activeExample, setActiveExample] = useState<
    'basic' | 'callbacks' | 'modal' | 'workflow'
  >('basic');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Example Selector */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold mb-4">PresetSelector 사용 예시</h1>
          <div className="flex gap-2">
            {[
              { id: 'basic', label: '기본 사용' },
              { id: 'callbacks', label: '콜백 활용' },
              { id: 'modal', label: '모달 사용' },
              { id: 'workflow', label: '워크플로우 통합' },
            ].map((example) => (
              <button
                key={example.id}
                onClick={() =>
                  setActiveExample(example.id as 'basic' | 'callbacks' | 'modal' | 'workflow')
                }
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeExample === example.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {example.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Example Content */}
      <div className="max-w-7xl mx-auto">
        {activeExample === 'basic' && <BasicExample />}
        {activeExample === 'callbacks' && <WithCallbacksExample />}
        {activeExample === 'modal' && <ModalExample />}
        {activeExample === 'workflow' && <WorkflowIntegrationExample />}
      </div>
    </div>
  );
}
