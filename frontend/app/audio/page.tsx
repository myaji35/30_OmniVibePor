'use client'

import { useState, useRef } from 'react'
import { Mic2, Wand2, Download, RotateCcw, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
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

const CARD = 'rounded-2xl border p-6'
const CARD_STYLE = { background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.08)' }

const INPUT_CLS = 'w-full px-4 py-3 rounded-xl text-sm text-white placeholder-white/25 focus:outline-none transition-all'
const INPUT_STYLE = {
  background: 'rgba(255,255,255,0.05)',
  border: '1px solid rgba(255,255,255,0.1)',
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <p className="text-[10px] font-black text-white/50 uppercase tracking-widest mb-2">{children}</p>
}

export default function AudioPage() {
  const [text, setText] = useState('')
  const [voiceId, setVoiceId] = useState('ko-injoon')
  const [language, setLanguage] = useState('ko')
  const [accuracyThreshold, setAccuracyThreshold] = useState(0.95)
  const [maxAttempts, setMaxAttempts] = useState(5)
  const [loading, setLoading] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  // ISS-062: useRef로 stale closure 회피. setState는 비동기라 setInterval 콜백에서 최신 값을 못 읽음.
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const generateAudio = async () => {
    if (!text.trim()) { alert('텍스트를 입력해주세요'); return }
    // 이전 polling 정리
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
    // 즉시 1회 조회 후 interval 시작 (첫 2초 wait 제거)
    checkTaskStatus(id)
    const interval = setInterval(() => checkTaskStatus(id), 1500)  // 2초 → 1.5초로 단축
    pollingIntervalRef.current = interval
  }

  const checkTaskStatus = async (id: string) => {
    try {
      // cache-busting timestamp로 프록시 캐싱 방어
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
        <div className="space-y-4">

          {/* 텍스트 입력 */}
          <div className={CARD} style={CARD_STYLE}>
            <SectionLabel>변환할 텍스트</SectionLabel>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="오디오로 변환할 텍스트를 입력하세요..."
              rows={6}
              className={INPUT_CLS}
              style={{ ...INPUT_STYLE, resize: 'none' }}
            />
            <p className="text-[11px] text-white/45 mt-2 font-mono">{text.length} / 5000</p>

            <SectionLabel>샘플 텍스트</SectionLabel>
            <div className="grid grid-cols-1 gap-1.5">
              {SAMPLE_TEXTS.map((sample, idx) => (
                <button
                  key={idx}
                  onClick={() => setText(sample)}
                  className="px-3 py-2 rounded-lg text-xs text-left text-white/50 hover:text-white/80 transition-all hover:bg-white/5 border border-transparent hover:border-white/10"
                >
                  {sample}
                </button>
              ))}
            </div>
          </div>

          {/* 설정 */}
          <div className={CARD} style={CARD_STYLE}>
            <SectionLabel>음성 설정</SectionLabel>
            <div className="space-y-4">
              <div>
                <label className="block text-xs text-white/40 mb-1.5">음성 ID</label>
                <select value={voiceId} onChange={(e) => setVoiceId(e.target.value)}
                  className={INPUT_CLS} style={INPUT_STYLE}>
                  <optgroup label="한국어 네이티브">
                    <option value="ko-injoon">인준 (남성, 차분)</option>
                    <option value="ko-sunhi">선희 (여성, 밝음)</option>
                    <option value="ko-hyunsu">현수 (남성, 다국어)</option>
                  </optgroup>
                  <optgroup label="다국어 (한국어 가능)">
                    <option value="multi-andrew">Andrew (남성, 깊은 톤)</option>
                    <option value="multi-ava">Ava (여성, 부드러움)</option>
                    <option value="multi-brian">Brian (남성, 힘 있는 톤)</option>
                    <option value="multi-emma">Emma (여성, 명확한 톤)</option>
                    <option value="multi-vivienne">Vivienne (여성, 우아한 톤)</option>
                    <option value="multi-florian">Florian (남성, 낮은 톤)</option>
                  </optgroup>
                </select>
              </div>

              <div>
                <label className="block text-xs text-white/40 mb-1.5">언어</label>
                <select value={language} onChange={(e) => setLanguage(e.target.value)}
                  className={INPUT_CLS} style={INPUT_STYLE}>
                  <option value="ko">한국어</option>
                  <option value="en">English</option>
                </select>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs text-white/40">정확도 임계값</label>
                  <span className="text-xs font-bold text-purple-400">{(accuracyThreshold * 100).toFixed(0)}%</span>
                </div>
                <input type="range" min="0.8" max="1.0" step="0.01"
                  value={accuracyThreshold}
                  onChange={(e) => setAccuracyThreshold(parseFloat(e.target.value))}
                  className="w-full accent-purple-500" />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs text-white/40">최대 재시도 횟수</label>
                  <span className="text-xs font-bold text-indigo-400">{maxAttempts}회</span>
                </div>
                <input type="range" min="1" max="10" step="1"
                  value={maxAttempts}
                  onChange={(e) => setMaxAttempts(parseInt(e.target.value))}
                  className="w-full accent-indigo-500" />
              </div>
            </div>

            <button
              onClick={generateAudio}
              disabled={loading}
              className="mt-5 w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-black uppercase tracking-wider transition-all disabled:opacity-50 active:scale-95"
              style={{ background: loading ? 'rgba(168,85,247,0.3)' : 'linear-gradient(135deg, #a855f7, #6366f1)', boxShadow: loading ? 'none' : '0 0 20px rgba(168,85,247,0.3)' }}
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
              {loading ? '생성 중...' : '오디오 생성'}
            </button>
          </div>
        </div>

        {/* ── 우측: 결과 ── */}
        <div className="space-y-4">

          {/* 진행 상태 */}
          {isProcessing && (
            <div className={CARD} style={CARD_STYLE}>
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
            <div className={CARD} style={{ background: 'rgba(52,211,153,0.05)', borderColor: 'rgba(52,211,153,0.2)' }}>
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span className="font-black text-emerald-300">생성 완료</span>
              </div>

              <div className="space-y-2 mb-4">
                {[
                  { label: '시도 횟수', value: `${taskStatus.result?.attempts || 0}회` },
                  { label: '최종 유사도', value: `${((taskStatus.result?.final_similarity || 0) * 100).toFixed(2)}%`, color: 'text-emerald-400' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="flex items-center justify-between px-3 py-2 rounded-lg"
                    style={{ background: 'rgba(255,255,255,0.04)' }}>
                    <span className="text-xs text-white/40">{label}</span>
                    <span className={`text-xs font-bold ${color || 'text-white/80'}`}>{value}</span>
                  </div>
                ))}
              </div>

              <audio controls className="w-full mb-3 rounded-xl"
                src={`/api/audio/download/${taskId}`} />

              <button onClick={downloadAudio}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-bold transition-all"
                style={{ background: 'rgba(52,211,153,0.15)', border: '1px solid rgba(52,211,153,0.3)', color: '#34d399' }}>
                <Download className="w-4 h-4" />
                오디오 다운로드
              </button>
            </div>
          )}

          {/* 실패 */}
          {taskStatus?.status === 'FAILURE' && (
            <div className={CARD} style={{ background: 'rgba(239,68,68,0.05)', borderColor: 'rgba(239,68,68,0.2)' }}>
              <div className="flex items-center gap-2 mb-3">
                <XCircle className="w-5 h-5 text-red-400" />
                <span className="font-black text-red-300">생성 실패</span>
              </div>
              <p className="text-sm text-white/50">{taskStatus.error || '알 수 없는 오류'}</p>
              <button onClick={() => { setTaskStatus(null); setTaskId(null) }}
                className="mt-3 flex items-center gap-1.5 text-xs text-white/40 hover:text-white/70 transition-colors">
                <RotateCcw className="w-3.5 h-3.5" />
                다시 시도
              </button>
            </div>
          )}

          {/* 검증 결과 */}
          {taskStatus?.result && (
            <div className={CARD} style={CARD_STYLE}>
              <SectionLabel>검증 결과</SectionLabel>
              <div className="space-y-3">
                {[
                  { label: '원본 텍스트', value: taskStatus.result.original_text, color: 'text-white/70' },
                  taskStatus.result.normalized_text !== taskStatus.result.original_text
                    ? { label: '정규화됨', value: taskStatus.result.normalized_text, color: 'text-emerald-400' }
                    : null,
                  { label: 'STT 변환 결과', value: taskStatus.result.transcribed_text, color: 'text-blue-400' },
                ].filter(Boolean).map((item) => item && (
                  <div key={item.label} className="p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
                    <p className="text-[10px] text-white/50 uppercase tracking-widest mb-1">{item.label}</p>
                    <p className={`text-sm ${item.color}`}>{item.value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Zero-Fault 가이드 */}
          {!taskId && !loading && (
            <div className={CARD} style={CARD_STYLE}>
              <SectionLabel>Zero-Fault 파이프라인</SectionLabel>
              <div className="space-y-2">
                {[
                  { step: '01', label: 'TTS 생성', desc: 'ElevenLabs API로 고품질 음성 합성', color: '#a855f7' },
                  { step: '02', label: 'STT 검증', desc: 'OpenAI Whisper v3로 역변환 검증', color: '#6366f1' },
                  { step: '03', label: '유사도 비교', desc: '원본 텍스트와 STT 결과 정밀 비교', color: '#3b82f6' },
                  { step: '04', label: '자동 재생성', desc: `임계값 미달 시 최대 ${maxAttempts}회 반복`, color: '#22d3ee' },
                ].map(({ step, label, desc, color }) => (
                  <div key={step} className="flex items-start gap-3 p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)' }}>
                    <span className="text-[10px] font-black font-mono shrink-0 mt-0.5" style={{ color }}>{step}</span>
                    <div>
                      <p className="text-xs font-bold text-white/80">{label}</p>
                      <p className="text-[11px] text-white/50 mt-0.5">{desc}</p>
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
