'use client'

import { useState } from 'react'
import AudioProgressTracker from '../components/AudioProgressTracker'

interface AudioGenerateResponse {
  status: string
  task_id: string
  message: string
  text_preview: string
}

interface TaskStatus {
  task_id: string
  status: string
  info: any
  result?: {
    status: string
    audio_path: string
    attempts: number
    final_similarity: number
    transcribed_text: string
    original_text: string
    normalized_text: string
    normalization_mappings?: Record<string, string>
  }
  error?: string
}

const SAMPLE_TEXTS = [
  "안녕하세요! 오늘은 2024년 1월 15일입니다.",
  "사과 3개를 2,000원에 샀습니다. 제 나이는 25살입니다.",
  "오후 2시 30분에 친구와 만났어요. 전화번호는 010-1234-5678입니다.",
  "AI 자동화 시스템의 성공률은 95.5%입니다. 정말 놀라운 결과입니다!",
]

export default function AudioPage() {
  const [text, setText] = useState('')
  const [voiceId, setVoiceId] = useState('pNInz6obpgDQGcFmaJgB')  // Adam (다국어 지원)
  const [language, setLanguage] = useState('ko')
  const [accuracyThreshold, setAccuracyThreshold] = useState(0.95)
  const [maxAttempts, setMaxAttempts] = useState(5)
  const [loading, setLoading] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null)

  // 오디오 생성 시작
  const generateAudio = async () => {
    if (!text.trim()) {
      alert('텍스트를 입력해주세요')
      return
    }

    setLoading(true)
    setTaskStatus(null)

    try {
      const res = await fetch('http://localhost:8000/api/v1/audio/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          voice_id: voiceId,
          language,
          accuracy_threshold: accuracyThreshold,
          max_attempts: maxAttempts
        })
      })

      const data: AudioGenerateResponse = await res.json()

      if (res.ok) {
        setTaskId(data.task_id)
        startPolling(data.task_id)
      } else {
        alert(`생성 실패: ${data.message || '알 수 없는 오류'}`)
        setLoading(false)
      }
    } catch (err) {
      console.error('Audio generation failed:', err)
      alert('오디오 생성 중 오류가 발생했습니다')
      setLoading(false)
    }
  }

  // 작업 상태 폴링 시작
  const startPolling = (taskId: string) => {
    const interval = setInterval(() => {
      checkTaskStatus(taskId)
    }, 2000) // 2초마다 확인

    setPollingInterval(interval)
  }

  // 작업 상태 확인
  const checkTaskStatus = async (taskId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/audio/status/${taskId}`)
      const data: TaskStatus = await res.json()

      setTaskStatus(data)

      // 완료 또는 실패 시 폴링 중지
      if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
        if (pollingInterval) {
          clearInterval(pollingInterval)
          setPollingInterval(null)
        }
        setLoading(false)
      }
    } catch (err) {
      console.error('Status check failed:', err)
    }
  }

  // 오디오 다운로드
  const downloadAudio = () => {
    if (!taskId) return
    window.open(`http://localhost:8000/api/v1/audio/download/${taskId}`, '_blank')
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 text-white">
      <div className="container mx-auto px-4 py-16">
        {/* 헤더 */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
            🎵 Zero-Fault Audio
          </h1>
          <p className="text-xl text-gray-300">
            TTS → STT → 검증 → 재생성 루프로 완벽한 오디오 생성
          </p>
        </div>

        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 왼쪽: 입력 섹션 */}
          <div className="space-y-6">
            {/* 텍스트 입력 */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h2 className="text-2xl font-bold mb-4">📝 텍스트 입력</h2>

              <div className="mb-4">
                <label className="block text-sm text-gray-300 mb-2">
                  변환할 텍스트
                </label>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="오디오로 변환할 텍스트를 입력하세요..."
                  rows={6}
                  className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-400 mt-2">
                  {text.length} / 5000 글자
                </p>
              </div>

              <div className="mb-4">
                <p className="text-sm text-gray-400 mb-2">샘플 텍스트:</p>
                <div className="grid grid-cols-1 gap-2">
                  {SAMPLE_TEXTS.map((sample, idx) => (
                    <button
                      key={idx}
                      onClick={() => setText(sample)}
                      className="px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-xs text-left transition-all"
                    >
                      {sample}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* 설정 */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h2 className="text-2xl font-bold mb-4">⚙️ 설정</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-300 mb-2">
                    음성 ID
                  </label>
                  <select
                    value={voiceId}
                    onChange={(e) => setVoiceId(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="pNInz6obpgDQGcFmaJgB">Adam (남성, 다국어 지원)</option>
                    <option value="EXAVITQu4vr4xnSDxMaL">Sarah (여성, 다국어 지원)</option>
                    <option value="cgSgspJ2msm6clMCkdW9">Jessica (여성, 다국어 지원)</option>
                    <option value="iP95p4xoKVk53GoZ742B">Chris (남성, 다국어 지원)</option>
                    <option value="onwK4e9ZLuTAKqWW03F9">Daniel (남성, 다국어 지원)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">
                    언어
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="ko">한국어</option>
                    <option value="en">English</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">
                    정확도 임계값: {(accuracyThreshold * 100).toFixed(0)}%
                  </label>
                  <input
                    type="range"
                    min="0.8"
                    max="1.0"
                    step="0.01"
                    value={accuracyThreshold}
                    onChange={(e) => setAccuracyThreshold(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">
                    최대 재시도 횟수: {maxAttempts}회
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    step="1"
                    value={maxAttempts}
                    onChange={(e) => setMaxAttempts(parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>
              </div>

              <button
                onClick={generateAudio}
                disabled={loading}
                className="mt-6 w-full px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-lg font-semibold disabled:opacity-50"
              >
                {loading ? '생성 중...' : '🎵 오디오 생성'}
              </button>
            </div>
          </div>

          {/* 오른쪽: 결과 섹션 */}
          <div className="space-y-6">
            {/* 진행 상태 - AudioProgressTracker 사용 */}
            {(loading || taskStatus?.status === 'STARTED' || taskStatus?.status === 'PENDING') && (
              <AudioProgressTracker
                isGenerating={loading || taskStatus?.status === 'STARTED' || taskStatus?.status === 'PENDING'}
                currentStep={
                  taskStatus?.status === 'STARTED' ? 'generate_tts' :
                  taskStatus?.status === 'PENDING' ? 'load' :
                  taskStatus?.status === 'SUCCESS' ? 'completed' :
                  taskStatus?.status === 'FAILURE' ? 'failed' :
                  ''
                }
                similarity={taskStatus?.result?.final_similarity || 0}
                attempt={taskStatus?.result?.attempts || 1}
                maxAttempts={maxAttempts}
              />
            )}

            {/* 완료 상태 */}
            {taskStatus && taskStatus.status === 'SUCCESS' && (
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
                <h2 className="text-2xl font-bold mb-4">✅ 생성 완료</h2>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">작업 ID:</span>
                    <span className="text-xs font-mono">{taskId}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">시도 횟수:</span>
                    <span className="font-semibold">{taskStatus.result.attempts}회</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">최종 유사도:</span>
                    <span className="font-semibold text-green-400">
                      {(taskStatus.result.final_similarity * 100).toFixed(2)}%
                    </span>
                  </div>

                  {/* 오디오 플레이어 */}
                  <div className="mt-4">
                    <p className="text-sm text-gray-400 mb-2">🎵 오디오 플레이어</p>
                    <audio
                      controls
                      className="w-full"
                      src={`http://localhost:8000/api/v1/audio/download/${taskId}`}
                    >
                      브라우저가 오디오 재생을 지원하지 않습니다.
                    </audio>
                  </div>

                  <button
                    onClick={downloadAudio}
                    className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm font-semibold transition-all"
                  >
                    ⬇️ 오디오 다운로드
                  </button>
                </div>
              </div>
            )}

            {/* 실패 상태 */}
            {taskStatus && taskStatus.status === 'FAILURE' && (
              <div className="bg-red-500/10 backdrop-blur-lg rounded-2xl p-6 border border-red-500/30">
                <h2 className="text-2xl font-bold mb-4 text-red-400">❌ 생성 실패</h2>
                <p className="text-sm text-gray-300">{taskStatus.error || '알 수 없는 오류가 발생했습니다.'}</p>
              </div>
            )}

            {/* 검증 결과 */}
            {taskStatus?.result && (
              <div className="bg-gradient-to-br from-purple-900/50 to-blue-900/50 backdrop-blur-lg rounded-2xl p-6 border border-purple-500/30">
                <h2 className="text-2xl font-bold mb-4">✅ 검증 결과</h2>

                <div className="space-y-4">
                  <div className="bg-white/5 rounded-lg p-4">
                    <p className="text-sm text-gray-400 mb-1">원본 텍스트:</p>
                    <p className="text-sm">{taskStatus.result.original_text}</p>
                  </div>

                  {taskStatus.result.normalized_text !== taskStatus.result.original_text && (
                    <div className="bg-white/5 rounded-lg p-4">
                      <p className="text-sm text-gray-400 mb-1">정규화됨:</p>
                      <p className="text-sm text-green-400">{taskStatus.result.normalized_text}</p>
                    </div>
                  )}

                  <div className="bg-white/5 rounded-lg p-4">
                    <p className="text-sm text-gray-400 mb-1">STT 변환 결과:</p>
                    <p className="text-sm text-blue-400">{taskStatus.result.transcribed_text}</p>
                  </div>

                  {taskStatus.result.normalization_mappings && Object.keys(taskStatus.result.normalization_mappings).length > 0 && (
                    <div className="bg-white/5 rounded-lg p-4">
                      <p className="text-sm text-gray-400 mb-2">정규화 매핑:</p>
                      <div className="space-y-1">
                        {Object.entries(taskStatus.result.normalization_mappings).map(([orig, conv]) => (
                          <div key={orig} className="flex items-center gap-2 text-xs">
                            <span className="text-red-400">{orig}</span>
                            <span>→</span>
                            <span className="text-green-400 font-semibold">{conv}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 사용 가이드 */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h2 className="text-xl font-bold mb-4">💡 Zero-Fault Audio란?</h2>

              <div className="space-y-3 text-sm text-gray-300">
                <div className="bg-white/5 rounded-lg p-3">
                  <p className="font-semibold mb-1">1️⃣ TTS 생성</p>
                  <p className="text-xs text-gray-400">
                    ElevenLabs API로 고품질 음성 생성
                  </p>
                </div>

                <div className="bg-white/5 rounded-lg p-3">
                  <p className="font-semibold mb-1">2️⃣ STT 검증</p>
                  <p className="text-xs text-gray-400">
                    OpenAI Whisper v3로 생성된 오디오를 텍스트로 변환
                  </p>
                </div>

                <div className="bg-white/5 rounded-lg p-3">
                  <p className="font-semibold mb-1">3️⃣ 유사도 비교</p>
                  <p className="text-xs text-gray-400">
                    원본 텍스트와 STT 결과의 유사도 계산
                  </p>
                </div>

                <div className="bg-white/5 rounded-lg p-3">
                  <p className="font-semibold mb-1">4️⃣ 재생성 루프</p>
                  <p className="text-xs text-gray-400">
                    정확도 임계값 미달 시 자동 재생성 (최대 {maxAttempts}회)
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 홈으로 돌아가기 */}
        <div className="text-center mt-12">
          <a
            href="/"
            className="inline-block px-6 py-3 bg-white/10 hover:bg-white/20 backdrop-blur-lg rounded-lg border border-white/20 transition-all"
          >
            ← 홈으로 돌아가기
          </a>
        </div>
      </div>
    </main>
  )
}
