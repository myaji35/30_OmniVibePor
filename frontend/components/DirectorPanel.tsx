"use client";

/**
 * DirectorPanel - 오디오 & 비디오 생성 패널
 *
 * REALPLAN.md Phase 2.3 구현
 *
 * 기능:
 * - WriterPanel에서 스크립트 자동 전달
 * - 음성 선택 UI
 * - Zero-Fault Audio 생성 (ElevenLabs + Whisper)
 * - AudioProgressTracker 통합
 * - 생성 완료 시 AudioPlayer
 */

import React, { useState, useEffect } from 'react';
import { useProduction } from '@/lib/contexts/ProductionContext';
import { ProgressBar } from '@/components/ProgressBar';

// Voice 옵션
const VOICE_OPTIONS = [
  { id: 'rachel', name: 'Rachel', language: 'en', description: '밝고 친근한 여성 목소리' },
  { id: 'adam', name: 'Adam', language: 'en', description: '차분하고 신뢰감 있는 남성 목소리' },
  { id: 'aria', name: 'Aria', language: 'ko', description: '자연스러운 한국어 여성 목소리' },
  { id: 'josh', name: 'Josh', language: 'en', description: '에너지 넘치는 젊은 남성 목소리' },
];

export default function DirectorPanel() {
  const { state, setAudio, setError, setLoading, setProgress } = useProduction();

  const [selectedVoice, setSelectedVoice] = useState('aria');
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
  const [audioTaskId, setAudioTaskId] = useState<string | null>(null);

  // 스크립트가 없으면 에러
  useEffect(() => {
    if (!state.script) {
      setError('스크립트가 없습니다. Writer 단계로 돌아가세요.');
    }
  }, [state.script]);

  // 오디오 생성 함수
  const handleGenerateAudio = async () => {
    if (!state.script || !state.projectId) {
      setError('스크립트 또는 프로젝트 정보가 없습니다');
      return;
    }

    setIsGeneratingAudio(true);
    setError(null);
    setLoading(true);
    setProgress(40); // Director 시작: 40%

    try {
      // 1. 오디오 생성 API 호출
      const response = await fetch(
        `http://localhost:8000/api/v1/projects/${state.projectId}/audio`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            script_id: state.script.script_id,
            voice_id: selectedVoice,
            accuracy_threshold: 0.95,
            max_attempts: 5,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate audio');
      }

      const data = await response.json();
      setAudioTaskId(data.task_id);

      // 2. WebSocket으로 실시간 진행 상황 추적 (ProgressBar에서 자동 처리)
      // 폴링 제거: WebSocket이 자동으로 상태를 업데이트합니다
    } catch (err: any) {
      setError(err.message);
      setIsGeneratingAudio(false);
      setLoading(false);
      console.error('Failed to generate audio:', err);
    }
  };

  // WebSocket을 통한 오디오 생성 완료 처리
  const handleAudioCompleted = (result: any) => {
    console.log('[DirectorPanel] Audio generation completed:', result);

    // Context에 오디오 저장
    setAudio({
      audio_id: result.audio_id,
      file_path: result.file_path,
      voice_id: selectedVoice,
      duration: result.duration,
      stt_accuracy: result.accuracy,
      retry_count: result.attempt - 1,
      created_at: new Date().toISOString(),
    });

    setIsGeneratingAudio(false);
    setLoading(false);
    setProgress(60); // Audio 완료: 60%
  };

  // WebSocket을 통한 오디오 생성 에러 처리
  const handleAudioError = (error: string) => {
    console.error('[DirectorPanel] Audio generation failed:', error);
    setError(error || 'Audio generation failed');
    setIsGeneratingAudio(false);
    setLoading(false);
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">오디오 & 비디오 생성</h2>
        <p className="text-sm text-gray-600 mt-1">
          스크립트를 오디오와 비디오로 변환합니다
        </p>
      </div>

      {/* Script Preview */}
      {state.script && (
        <div className="mb-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex justify-between items-start mb-3">
            <h3 className="font-medium text-gray-900">스크립트</h3>
            <span className="text-sm text-gray-600">
              {state.script.word_count}자 | {Math.floor(state.script.estimated_duration / 60)}분{' '}
              {state.script.estimated_duration % 60}초
            </span>
          </div>
          <p className="text-gray-700 text-sm whitespace-pre-wrap line-clamp-4">
            {state.script.content}
          </p>
        </div>
      )}

      {/* Audio Section */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🎙️ 오디오 생성</h3>

        {!state.audio && !isGeneratingAudio && (
          <div className="space-y-4">
            {/* Voice Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">음성 선택</label>
              <div className="grid grid-cols-2 gap-3">
                {VOICE_OPTIONS.map((voice) => (
                  <button
                    key={voice.id}
                    onClick={() => setSelectedVoice(voice.id)}
                    className={`p-4 border rounded-lg text-left transition-all ${
                      selectedVoice === voice.id
                        ? 'border-blue-500 bg-blue-50 shadow-sm'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <div className="font-medium text-gray-900">{voice.name}</div>
                    <div className="text-xs text-gray-600 mt-1">{voice.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Generate Button */}
            <button
              onClick={handleGenerateAudio}
              disabled={!state.script}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              Zero-Fault 오디오 생성
            </button>

            {/* Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
              <p className="font-medium mb-2">🔬 Zero-Fault Audio Loop</p>
              <ol className="space-y-1 text-xs">
                <li>1. ElevenLabs API로 TTS 생성</li>
                <li>2. OpenAI Whisper로 STT 검증</li>
                <li>3. 원본과 유사도 비교 (목표: 95% 이상)</li>
                <li>4. 정확도 미달 시 자동 재생성 (최대 5회)</li>
              </ol>
            </div>
          </div>
        )}

        {/* Audio Progress - WebSocket 기반 실시간 진행률 */}
        {isGeneratingAudio && audioTaskId && (
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
            <div className="mb-4">
              <h4 className="font-medium text-blue-900 mb-1 flex items-center gap-2">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
                Zero-Fault 오디오 생성 중...
              </h4>
              <p className="text-sm text-blue-700">
                WebSocket을 통해 실시간으로 진행 상황을 추적합니다
              </p>
            </div>

            {/* ProgressBar 컴포넌트 */}
            <ProgressBar
              projectId={audioTaskId}
              onCompleted={handleAudioCompleted}
              onError={handleAudioError}
              className="mt-4"
              showConnectionStatus={true}
            />
          </div>
        )}

        {/* Audio Player */}
        {state.audio && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-start gap-4 mb-4">
              <div className="bg-green-500 rounded-full p-3">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-green-900 mb-1">오디오 생성 완료</h4>
                <p className="text-sm text-green-800">
                  정확도: {(state.audio.stt_accuracy * 100).toFixed(1)}% | 길이:{' '}
                  {state.audio.duration.toFixed(1)}초 | 재시도: {state.audio.retry_count}회
                </p>
              </div>
            </div>

            {/* Audio Player UI */}
            <audio controls className="w-full">
              <source src={`http://localhost:8000${state.audio.file_path}`} type="audio/mpeg" />
              Your browser does not support the audio element.
            </audio>
          </div>
        )}
      </div>

      {/* Video Section (Placeholder) */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🎬 비디오 생성</h3>
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <div className="text-4xl mb-3">🚧</div>
          <p className="text-gray-600">비디오 생성 기능은 Phase 4에서 구현됩니다</p>
          <p className="text-sm text-gray-500 mt-2">
            (Google Veo + Nano Banana + HeyGen/Wav2Lip 립싱크)
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center pt-6 border-t border-gray-200">
        <button
          onClick={() => window.history.back()}
          className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          ← 이전
        </button>

        <button
          disabled={!state.audio}
          className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          다음: 마케팅 →
        </button>
      </div>
    </div>
  );
}
