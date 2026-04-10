'use client'

import { useState, useRef } from 'react'
import { Mic2, Wand2, Download, RotateCcw, CheckCircle2, XCircle, Loader2, Play } from 'lucide-react'
import AppShell from '@/components/AppShell'
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
  '안녕하세요! 오늘은 2024년 1월 15일입니다.',
  '사과 3개를 2,000원에 샀습니다. 제 나이는 25살입니다.',
  '오후 2시 30분에 친구와 만났어요. 전화번호는 010-1234-5678입니다.',
  'AI 자동화 시스템의 성공률은 95.5%입니다. 정말 놀라운 결과입니다!',
]

export default function AudioPage() {
  const [text, setText] = useState('')
  const [voiceId, setVoiceId] = useState('pNInz6obpgDQGcFmaJgB')
  const [language, setLanguage] = useState('ko')
  const [accuracyThreshold, setAccuracyThreshold] = useState(0.95)
  const [maxAttempts, setMaxAttempts] = useState(5)
  const [loading, setLoading] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const generateAudio = async () => {
    if (!text.trim()) { alert('텍스트를 입력해주세요'); return }
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
    setLoading(true)
    setTaskStatus(null)
    try {
      const res = await fetch('/api/audio/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice_id: voiceId, language, accuracy_threshold: accuracyThreshold, max_attempts: maxAttempts }),
      })
      const data: AudioGenerateResponse = await res.json()
      if (res.ok) { setTaskId(data.task_id); startPolling(data.task_id) }
      else { alert(`생성 실패: ${data.message || '알 수 없는 오류'}`); setLoading(false) }
    } catch { alert('오디오 생성 중 오류가 발생했습니다'); setLoading(false) }
  }

  const startPolling = (id: string) => {
    checkTaskStatus(id)
    const interval = setInterval(() => checkTaskStatus(id), 1500)
    pollingIntervalRef.current = interval
  }

  const checkTaskStatus = async (id: string) => {
    try {
      const res = await fetch(`/api/audio/status/${id}?t=${Date.now()}`, { cache: 'no-store' })
      const data: TaskStatus = await res.json()
      setTaskStatus(data)
      if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current)
          pollingIntervalRef.current = null
        }
        setLoading(false)
      }
    } catch { /* ignore */ }
  }

  const downloadAudio = () => {
    if (!taskId) return
    window.open(`/api/audio/download/${taskId}`, '_blank')
  }

  const isProcessing = loading || taskStatus?.status === 'STARTED' || taskStatus?.status === 'PENDING'

  return (
    <AppShell
      title="Zero-Fault Audio"
      subtitle="TTS → STT → 검증 → 재생성 루프로 99% 정확도 오디오 생성"
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* ── 좌측: 입력 ── */}
        <div className="space-y-5">

          {/* 텍스트 입력 */}
          <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
            <label className="block text-xs font-semibold text-gray-600 mb-1.5">변환할 텍스트</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="오디오로 변환할 텍스트를 입력하세요..."
              rows={6}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#00A1E0] focus:ring-1 focus:ring-[#00A1E0] resize-none"
            />
            <p className="text-xs text-gray-400 mt-1.5 font-mono">{text.length} / 5000</p>

            <label className="block text-xs font-semibold text-gray-600 mb-1.5 mt-4">샘플 텍스트</label>
            <div className="grid grid-cols-1 gap-1">
              {SAMPLE_TEXTS.map((sample, idx) => (
                <button
                  key={idx}
                  onClick={() => setText(sample)}
                  className="px-3 py-2 rounded-md text-xs text-left text-gray-500 hover:text-gray-800 hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-200"
                >
                  {sample}
                </button>
              ))}
            </div>
          </div>

          {/* 설정 */}
          <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
            <label className="block text-xs font-semibold text-gray-600 mb-3">음성 설정</label>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">음성 ID</label>
                <select value={voiceId} onChange={(e) => setVoiceId(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 bg-white focus:outline-none focus:border-[#00A1E0] focus:ring-1 focus:ring-[#00A1E0]">
                  <option value="pNInz6obpgDQGcFmaJgB">Adam (남성, 다국어)</option>
                  <option value="EXAVITQu4vr4xnSDxMaL">Sarah (여성, 다국어)</option>
                  <option value="cgSgspJ2msm6clMCkdW9">Jessica (여성, 다국어)</option>
                  <option value="iP95p4xoKVk53GoZ742B">Chris (남성, 다국어)</option>
                  <option value="onwK4e9ZLuTAKqWW03F9">Daniel (남성, 다국어)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">언어</label>
                <select value={language} onChange={(e) => setLanguage(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 bg-white focus:outline-none focus:border-[#00A1E0] focus:ring-1 focus:ring-[#00A1E0]">
                  <option value="ko">한국어</option>
                  <option value="en">English</option>
                </select>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-gray-600">정확도 임계값</label>
                  <span className="text-xs font-bold text-[#00A1E0]">{(accuracyThreshold * 100).toFixed(0)}%</span>
                </div>
                <input type="range" min="0.8" max="1.0" step="0.01"
                  value={accuracyThreshold}
                  onChange={(e) => setAccuracyThreshold(parseFloat(e.target.value))}
                  className="w-full accent-[#00A1E0]" />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-gray-600">최대 재시도 횟수</label>
                  <span className="text-xs font-bold text-[#16325C]">{maxAttempts}회</span>
                </div>
                <input type="range" min="1" max="10" step="1"
                  value={maxAttempts}
                  onChange={(e) => setMaxAttempts(parseInt(e.target.value))}
                  className="w-full accent-[#00A1E0]" />
              </div>
            </div>

            <button
              onClick={generateAudio}
              disabled={loading}
              className="mt-5 w-full flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-bold text-white transition-all disabled:opacity-50 active:scale-[0.98]"
              style={{ backgroundColor: loading ? '#7FCCE8' : '#00A1E0' }}
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
              {loading ? '생성 중...' : '오디오 생성'}
            </button>
          </div>
        </div>

        {/* ── 우측: 결과 ── */}
        <div className="space-y-5">

          {/* 진행 상태 */}
          {isProcessing && (
            <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
              <AudioProgressTracker
                isGenerating={isProcessing}
                currentStep={
                  taskStatus?.status === 'STARTED' ? 'generate_tts' :
                  taskStatus?.status === 'PENDING' ? 'load' :
                  taskStatus?.status === 'SUCCESS' ? 'completed' :
                  taskStatus?.status === 'FAILURE' ? 'failed' : ''
                }
                similarity={taskStatus?.result?.final_similarity || 0}
                attempt={taskStatus?.result?.attempts || 1}
                maxAttempts={maxAttempts}
              />
            </div>
          )}

          {/* 완료 */}
          {taskStatus?.status === 'SUCCESS' && (
            <div className="bg-white rounded-lg border border-[#4BCA81] p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 className="w-5 h-5 text-[#4BCA81]" />
                <span className="font-bold text-[#16325C]">생성 완료</span>
              </div>

              <div className="space-y-2 mb-4">
                {[
                  { label: '시도 횟수', value: `${taskStatus.result?.attempts || 0}회` },
                  { label: '최종 유사도', value: `${((taskStatus.result?.final_similarity || 0) * 100).toFixed(2)}%`, color: 'text-[#4BCA81]' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="flex items-center justify-between px-3 py-2.5 rounded-md bg-gray-50">
                    <span className="text-xs text-gray-500">{label}</span>
                    <span className={`text-sm font-bold ${color || 'text-[#16325C]'}`}>{value}</span>
                  </div>
                ))}
              </div>

              <audio controls className="w-full mb-3 rounded-lg"
                src={`/api/audio/download/${taskId}`} />

              <button onClick={downloadAudio}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-bold text-white transition-all active:scale-[0.98]"
                style={{ backgroundColor: '#00A1E0' }}>
                <Download className="w-4 h-4" />
                오디오 다운로드
              </button>
            </div>
          )}

          {/* 실패 */}
          {taskStatus?.status === 'FAILURE' && (
            <div className="bg-white rounded-lg border border-[#EA001E] p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <XCircle className="w-5 h-5 text-[#EA001E]" />
                <span className="font-bold text-[#16325C]">생성 실패</span>
              </div>
              <p className="text-sm text-gray-600">{taskStatus.error || '알 수 없는 오류'}</p>
              <button onClick={() => { setTaskStatus(null); setTaskId(null) }}
                className="mt-3 flex items-center gap-1.5 text-xs text-gray-500 hover:text-[#00A1E0] transition-colors">
                <RotateCcw className="w-3.5 h-3.5" />
                다시 시도
              </button>
            </div>
          )}

          {/* 검증 결과 */}
          {taskStatus?.result && (
            <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
              <label className="block text-xs font-semibold text-gray-600 mb-3">검증 결과</label>
              <div className="space-y-3">
                {[
                  { label: '원본 텍스트', value: taskStatus.result.original_text, color: 'text-gray-700' },
                  taskStatus.result.normalized_text !== taskStatus.result.original_text
                    ? { label: '정규화됨', value: taskStatus.result.normalized_text, color: 'text-[#4BCA81]' }
                    : null,
                  { label: 'STT 변환 결과', value: taskStatus.result.transcribed_text, color: 'text-[#00A1E0]' },
                ].filter(Boolean).map((item) => item && (
                  <div key={item.label} className="p-3 rounded-md bg-gray-50">
                    <p className="text-xs font-semibold text-gray-500 mb-1">{item.label}</p>
                    <p className={`text-sm ${item.color}`}>{item.value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Zero-Fault 가이드 */}
          {!taskId && !loading && (
            <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
              <label className="block text-xs font-semibold text-gray-600 mb-3">Zero-Fault 파이프라인</label>
              <div className="space-y-2">
                {[
                  { step: '01', label: 'TTS 생성', desc: 'ElevenLabs API로 고품질 음성 합성', color: '#00A1E0' },
                  { step: '02', label: 'STT 검증', desc: 'OpenAI Whisper v3로 역변환 검증', color: '#5867E8' },
                  { step: '03', label: '유사도 비교', desc: '원본 텍스트와 STT 결과 정밀 비교', color: '#4BCA81' },
                  { step: '04', label: '자동 재생성', desc: `임계값 미달 시 최대 ${maxAttempts}회 반복`, color: '#16325C' },
                ].map(({ step, label, desc, color }) => (
                  <div key={step} className="flex items-start gap-3 p-3 rounded-md bg-gray-50">
                    <span className="text-xs font-bold font-mono shrink-0 mt-0.5 w-6 h-6 rounded-full flex items-center justify-center text-white" style={{ backgroundColor: color }}>{step}</span>
                    <div>
                      <p className="text-sm font-semibold text-[#16325C]">{label}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  )
}
