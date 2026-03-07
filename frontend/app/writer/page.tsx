'use client'

import { useState } from 'react'
import { PenTool, Wand2, Copy, Check, Loader2, ArrowRight } from 'lucide-react'
import AppShell from '@/components/AppShell'
import Link from 'next/link'

interface NormalizeResponse {
  original: string
  normalized: string
  mappings: Record<string, string>
}

interface GeneratedScript {
  campaign_name: string
  topic: string
  platform: string
  script: string
  hook?: string
  cta?: string
  estimated_duration?: number
  target_audience?: string
  tone?: string
}

const ASPECT_RATIOS = {
  'YouTube': '16:9',
  'YouTube Shorts': '9:16',
  'Instagram Feed': '1:1',
  'Instagram Reels': '9:16',
  'TikTok': '9:16',
  'Facebook': '16:9',
  'LinkedIn': '16:9',
} as const

type PlatformKey = keyof typeof ASPECT_RATIOS

const CARD = 'rounded-2xl border p-6'
const CARD_S = { background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.08)' }
const INPUT_CLS = 'w-full px-4 py-3 rounded-xl text-sm text-white placeholder-white/25 focus:outline-none transition-all'
const INPUT_S = { background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }

function Label({ children }: { children: React.ReactNode }) {
  return <p className="text-[10px] font-black text-white/50 uppercase tracking-widest mb-2">{children}</p>
}

export default function WriterPage() {
  const [text, setText] = useState('')
  const [normalizeResult, setNormalizeResult] = useState<NormalizeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [platform, setPlatform] = useState<PlatformKey>('YouTube')
  const [campaignName, setCampaignName] = useState('')
  const [topic, setTopic] = useState('')
  const [generatedScript, setGeneratedScript] = useState<GeneratedScript | null>(null)
  const [copied, setCopied] = useState(false)

  const normalizeText = async () => {
    if (!text.trim()) { alert('텍스트를 입력해주세요'); return }
    setLoading(true)
    try {
      const res = await fetch('/api/audio-normalize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      const data = await res.json()
      if (res.ok) setNormalizeResult(data)
      else alert(`정규화 실패: ${data.message || '오류'}`)
    } catch { alert('오류가 발생했습니다') }
    finally { setLoading(false) }
  }

  const generateScript = async () => {
    if (!campaignName.trim() || !topic.trim()) { alert('캠페인명과 주제를 입력해주세요'); return }
    setLoading(true)
    try {
      const res = await fetch('/api/writer-generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaign_name: campaignName, topic, platform }),
      })
      const data = await res.json()
      if (res.ok) setGeneratedScript(data)
      else alert(`스크립트 생성 실패: ${data.message || '오류'}`)
    } catch { alert('오류가 발생했습니다') }
    finally { setLoading(false) }
  }

  const copyText = (txt: string) => {
    navigator.clipboard.writeText(txt)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <AppShell
      title="Writer Agent"
      subtitle="AI 스크립트 생성 및 한국어 텍스트 정규화"
      actions={
        <Link href="/audio"
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white/60 hover:text-white/90 transition-colors border border-white/10 hover:border-white/20">
          오디오 생성
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* ── 좌측: 입력 ── */}
        <div className="space-y-4">

          {/* 플랫폼 선택 */}
          <div className={CARD} style={CARD_S}>
            <Label>플랫폼 선택</Label>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(ASPECT_RATIOS).map(([name, ratio]) => {
                const isActive = platform === name
                return (
                  <button
                    key={name}
                    onClick={() => setPlatform(name as PlatformKey)}
                    className="px-3 py-2.5 rounded-xl text-left transition-all"
                    style={{
                      background: isActive ? 'rgba(168,85,247,0.15)' : 'rgba(255,255,255,0.03)',
                      border: isActive ? '1px solid rgba(168,85,247,0.4)' : '1px solid rgba(255,255,255,0.07)',
                    }}
                  >
                    <div className={`text-xs font-bold ${isActive ? 'text-purple-300' : 'text-white/60'}`}>{name}</div>
                    <div className="text-[10px] font-mono mt-0.5" style={{ color: isActive ? 'rgba(168,85,247,0.8)' : 'rgba(255,255,255,0.25)' }}>{ratio}</div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* 캠페인 정보 */}
          <div className={CARD} style={CARD_S}>
            <Label>스크립트 생성</Label>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-white/40 mb-1.5">캠페인명</label>
                <input type="text" value={campaignName} onChange={(e) => setCampaignName(e.target.value)}
                  placeholder="예: AI 자동화 시리즈" className={INPUT_CLS} style={INPUT_S} />
              </div>
              <div>
                <label className="block text-xs text-white/40 mb-1.5">주제 / 소제목</label>
                <input type="text" value={topic} onChange={(e) => setTopic(e.target.value)}
                  placeholder="예: Zero-Fault Audio 시스템 소개" className={INPUT_CLS} style={INPUT_S} />
              </div>
            </div>
            <button
              onClick={generateScript}
              disabled={loading}
              className="mt-4 w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-black uppercase tracking-wider transition-all disabled:opacity-50 active:scale-95"
              style={{ background: 'linear-gradient(135deg, #a855f7, #6366f1)', boxShadow: '0 0 20px rgba(168,85,247,0.25)' }}
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <PenTool className="w-4 h-4" />}
              스크립트 생성
            </button>
          </div>

          {/* 텍스트 정규화 */}
          <div className={CARD} style={CARD_S}>
            <Label>한국어 텍스트 정규화</Label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="예: 2024년 1월 15일, 사과 3개를 2,000원에 샀습니다."
              rows={4}
              className={INPUT_CLS}
              style={{ ...INPUT_S, resize: 'none' }}
            />
            <div className="mt-2 space-y-1">
              {[
                '2024년 → 이천이십사년',
                '3개 → 세개',
                '25살 → 스물다섯살',
                '010-1234-5678 → 공일공 일이삼사 오육칠팔',
              ].map((ex) => (
                <p key={ex} className="text-[11px] text-white/45 font-mono">{ex}</p>
              ))}
            </div>
            <button
              onClick={normalizeText}
              disabled={loading}
              className="mt-4 w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-bold transition-all disabled:opacity-50"
              style={{ background: 'rgba(99,102,241,0.2)', border: '1px solid rgba(99,102,241,0.3)', color: '#a5b4fc' }}
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
              텍스트 정규화
            </button>
          </div>
        </div>

        {/* ── 우측: 결과 ── */}
        <div className="space-y-4">

          {/* 생성된 스크립트 */}
          {generatedScript && (
            <div className={CARD} style={{ background: 'rgba(168,85,247,0.05)', borderColor: 'rgba(168,85,247,0.2)' }}>
              <div className="flex items-center justify-between mb-3">
                <Label>생성된 스크립트</Label>
                <button onClick={() => copyText(generatedScript.script)}
                  className="flex items-center gap-1 text-[11px] text-purple-400 hover:text-purple-300 transition-colors">
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? '복사됨' : '복사'}
                </button>
              </div>

              <div className="space-y-3">
                {generatedScript.hook && (
                  <div className="p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.05)' }}>
                    <p className="text-[10px] text-purple-400/70 uppercase tracking-widest mb-1">Hook</p>
                    <p className="text-sm text-white/80">{generatedScript.hook}</p>
                  </div>
                )}
                <div className="p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <p className="text-[10px] text-white/50 uppercase tracking-widest mb-1">Script</p>
                  <p className="text-sm text-white/70 leading-relaxed whitespace-pre-line">{generatedScript.script}</p>
                </div>
                {generatedScript.cta && (
                  <div className="p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.05)' }}>
                    <p className="text-[10px] text-indigo-400/70 uppercase tracking-widest mb-1">CTA</p>
                    <p className="text-sm text-white/80">{generatedScript.cta}</p>
                  </div>
                )}
                {generatedScript.estimated_duration && (
                  <div className="flex items-center justify-between px-3 py-2 rounded-lg"
                    style={{ background: 'rgba(255,255,255,0.03)' }}>
                    <span className="text-xs text-white/30">예상 길이</span>
                    <span className="text-xs font-bold text-purple-400">{generatedScript.estimated_duration}초</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 정규화 결과 */}
          {normalizeResult && (
            <div className={CARD} style={{ background: 'rgba(52,211,153,0.04)', borderColor: 'rgba(52,211,153,0.15)' }}>
              <div className="flex items-center justify-between mb-3">
                <Label>정규화 결과</Label>
                <button onClick={() => copyText(normalizeResult.normalized)}
                  className="flex items-center gap-1 text-[11px] text-emerald-400 hover:text-emerald-300 transition-colors">
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? '복사됨' : '복사'}
                </button>
              </div>

              <div className="space-y-2">
                <div className="p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <p className="text-[10px] text-white/50 uppercase tracking-widest mb-1">원본</p>
                  <p className="text-sm text-white/60">{normalizeResult.original}</p>
                </div>
                <div className="p-3 rounded-xl" style={{ background: 'rgba(52,211,153,0.08)' }}>
                  <p className="text-[10px] text-emerald-500/70 uppercase tracking-widest mb-1">정규화됨</p>
                  <p className="text-sm text-emerald-300 font-semibold">{normalizeResult.normalized}</p>
                </div>

                {Object.keys(normalizeResult.mappings).length > 0 && (
                  <div className="p-3 rounded-xl space-y-1" style={{ background: 'rgba(255,255,255,0.03)' }}>
                    <p className="text-[10px] text-white/50 uppercase tracking-widest mb-2">변환 매핑</p>
                    {Object.entries(normalizeResult.mappings).map(([orig, conv]) => (
                      <div key={orig} className="flex items-center gap-2 text-xs">
                        <span className="text-red-400 font-mono">{orig}</span>
                        <span className="text-white/20">→</span>
                        <span className="text-emerald-400 font-mono font-semibold">{conv}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 가이드 */}
          {!generatedScript && !normalizeResult && (
            <div className={CARD} style={CARD_S}>
              <Label>사용 가이드</Label>
              <div className="space-y-2">
                {[
                  { n: '01', title: '플랫폼 선택', desc: '영상을 배포할 플랫폼의 최적 비율을 선택하세요.' },
                  { n: '02', title: '캠페인 정보 입력', desc: '캠페인명과 주제를 입력하면 AI가 스크립트를 생성합니다.' },
                  { n: '03', title: '텍스트 정규화', desc: '숫자를 한글로 변환하여 TTS 발음 일관성을 확보합니다.' },
                  { n: '04', title: '오디오 변환', desc: '생성된 스크립트를 Zero-Fault Audio로 변환합니다.' },
                ].map(({ n, title, desc }) => (
                  <div key={n} className="flex items-start gap-3 p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)' }}>
                    <span className="text-[10px] font-black font-mono text-purple-400/70 shrink-0 mt-0.5">{n}</span>
                    <div>
                      <p className="text-xs font-bold text-white/70">{title}</p>
                      <p className="text-[11px] text-white/50 mt-0.5">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* 비율 참고 */}
              <div className="mt-4 space-y-1.5">
                <Label>영상 비율 참고</Label>
                {[
                  { label: '가로 (Landscape)', ratio: '16:9', color: 'text-blue-400' },
                  { label: '정사각형 (Square)', ratio: '1:1', color: 'text-emerald-400' },
                  { label: '세로 (Portrait)', ratio: '9:16', color: 'text-purple-400' },
                ].map(({ label, ratio, color }) => (
                  <div key={label} className="flex items-center justify-between px-3 py-2 rounded-lg"
                    style={{ background: 'rgba(255,255,255,0.03)' }}>
                    <span className="text-xs text-white/40">{label}</span>
                    <span className={`text-xs font-mono font-bold ${color}`}>{ratio}</span>
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
