"use client";

/**
 * WriterPanel - 스크립트 작성 패널
 *
 * REALPLAN.md Phase 2.2 구현
 *
 * 기능:
 * - 스크립트 에디터 (textarea 기반, Monaco Editor는 추후 확장 가능)
 * - 실시간 저장 (debounce 5초)
 * - 글자 수 / 예상 시간 표시
 * - "다음" 버튼으로 Director로 자동 전환
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useProduction } from '@/lib/contexts/ProductionContext';

export default function WriterPanel() {
  const { state, setScript, setStep, setLoading, setError } = useProduction();

  const [scriptContent, setScriptContent] = useState('');
  const [wordCount, setWordCount] = useState(0);
  const [estimatedDuration, setEstimatedDuration] = useState(0); // 초 단위
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  // 기존 스크립트 로드
  useEffect(() => {
    if (state.script) {
      setScriptContent(state.script.content);
    }
  }, [state.script]);

  // 글자 수 및 예상 시간 계산
  useEffect(() => {
    const count = scriptContent.length;
    setWordCount(count);

    // 예상 시간 계산 (한국어: 분당 약 200자)
    const duration = Math.ceil((count / 200) * 60);
    setEstimatedDuration(duration);
  }, [scriptContent]);

  // 자동 저장 (debounce 5초)
  useEffect(() => {
    if (!scriptContent.trim()) return;

    const timer = setTimeout(() => {
      handleSave();
    }, 5000);

    return () => clearTimeout(timer);
  }, [scriptContent]);

  // 저장 함수
  const handleSave = useCallback(async () => {
    if (!scriptContent.trim()) return;

    setIsSaving(true);
    try {
      // TODO: Backend API 호출하여 스크립트 저장
      // const response = await fetch(`/api/v1/projects/${state.projectId}/scripts`, {...})

      setLastSaved(new Date());

      // Context에 스크립트 저장 (임시로 local state 사용)
      // setScript({
      //   script_id: 'temp_id',
      //   content: scriptContent,
      //   platform: state.platform || 'youtube',
      //   word_count: wordCount,
      //   estimated_duration: estimatedDuration,
      //   version: 1,
      //   created_at: new Date().toISOString(),
      // });
    } catch (err: any) {
      console.error('Failed to save script:', err);
    } finally {
      setIsSaving(false);
    }
  }, [scriptContent, wordCount, estimatedDuration]);

  // "다음" 버튼 클릭 (Director로 전환)
  const handleNext = async () => {
    if (!scriptContent.trim()) {
      setError('스크립트를 입력하세요');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 1. 스크립트 저장 (Backend API)
      if (!state.projectId) {
        throw new Error('프로젝트가 선택되지 않았습니다');
      }

      const response = await fetch(`http://localhost:8000/api/v1/projects/${state.projectId}/scripts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: scriptContent,
          platform: state.platform || 'youtube',
          word_count: wordCount,
          estimated_duration: estimatedDuration,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save script');
      }

      const savedScript = await response.json();

      // 2. Context 업데이트
      setScript(savedScript);

      // 3. Director 단계로 자동 전환
      setStep('director');
    } catch (err: any) {
      setError(err.message);
      console.error('Failed to proceed to director:', err);
    } finally {
      setLoading(false);
    }
  };

  // 키보드 단축키 (Cmd+S 저장, Cmd+Enter 다음)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        handleNext();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleSave, handleNext]);

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">스크립트 작성</h2>
          <p className="text-sm text-gray-600 mt-1">
            영상에 사용할 스크립트를 작성하세요
          </p>
        </div>

        {/* Stats */}
        <div className="flex gap-6 text-sm">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{wordCount}</div>
            <div className="text-gray-600">글자</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {Math.floor(estimatedDuration / 60)}:{(estimatedDuration % 60).toString().padStart(2, '0')}
            </div>
            <div className="text-gray-600">예상 시간</div>
          </div>
        </div>
      </div>

      {/* Editor */}
      <div className="mb-6">
        <textarea
          value={scriptContent}
          onChange={(e) => setScriptContent(e.target.value)}
          placeholder="여기에 스크립트를 입력하세요...

예:
안녕하세요! 오늘은 건강한 식습관에 대해 이야기해보려고 합니다.

첫 번째로, 아침 식사의 중요성입니다...
"
          className="w-full h-[500px] px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm"
        />

        {/* Save Status */}
        <div className="flex justify-between items-center mt-2 text-xs text-gray-500">
          <div>
            {isSaving && '저장 중...'}
            {!isSaving && lastSaved && `마지막 저장: ${lastSaved.toLocaleTimeString('ko-KR')}`}
            {!isSaving && !lastSaved && '자동 저장 (5초마다)'}
          </div>
          <div className="text-gray-400">
            <kbd className="px-2 py-1 bg-gray-100 rounded">⌘S</kbd> 저장 |{' '}
            <kbd className="px-2 py-1 bg-gray-100 rounded">⌘Enter</kbd> 다음
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <button
          onClick={handleSave}
          disabled={isSaving || !scriptContent.trim()}
          className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? '저장 중...' : '저장'}
        </button>

        <button
          onClick={handleNext}
          disabled={!scriptContent.trim() || state.isLoading}
          className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center gap-2"
        >
          {state.isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
              처리 중...
            </>
          ) : (
            <>
              다음: 오디오 생성
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </>
          )}
        </button>
      </div>

      {/* Help Text */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">💡 팁</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• 스크립트는 자동으로 5초마다 저장됩니다</li>
          <li>• 한국어 기준 분당 약 200자가 읽힙니다</li>
          <li>• 구두점(마침표, 쉼표)을 적절히 사용하면 자연스러운 음성이 생성됩니다</li>
          <li>• "다음" 버튼을 클릭하면 자동으로 오디오 생성 단계로 이동합니다</li>
        </ul>
      </div>
    </div>
  );
}
