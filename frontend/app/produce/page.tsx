'use client'

/**
 * 멀티포맷 콘텐츠 생산 — 스크립트 → 영상/프레젠테이션/나레이션
 * ISS-009: Phase 5.3
 */

import { useState, useCallback, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import {
  Film, FileText, Mic, Loader2, Download, ExternalLink,
  CheckCircle, AlertCircle, Play,
} from 'lucide-react'
import AppShell from '@/components/AppShell'
import PipelineNav from '@/components/PipelineNav'

interface ProduceResult {
  type: 'video' | 'presentation' | 'narration'
  filename: string
  download_url: string
  srt_url?: string
  size_human?: string
  slide_count?: number
  voice?: string
}

const VOICES = [
  { id: 'ko-KR-SunHiNeural', name: '선희 (여성)', desc: '밝고 명확' },
  { id: 'ko-KR-InJoonNeural', name: '인준 (남성)', desc: '안정적 뉴스 톤' },
  { id: 'ko-KR-BongJinNeural', name: '봉진 (남성)', desc: '차분한 톤' },
  { id: 'ko-KR-YuJinNeural', name: '유진 (여성)', desc: '젊은 여성' },
]

function ProduceContent() {
  const searchParams = useSearchParams()

  const [script, setScript] = useState('')
  const [brand, setBrand] = useState('')
  const [channel, setChannel] = useState('youtube')

  // /concept에서 전달된 스크립트 복원
  useEffect(() => {
    const saved = sessionStorage.getItem('omnivibe_script')
    if (saved) { setScript(saved); sessionStorage.removeItem('omnivibe_script') }
    else if (searchParams.get('script')) setScript(searchParams.get('script')!)

    const savedBrand = sessionStorage.getItem('omnivibe_brand')
    if (savedBrand) { setBrand(savedBrand); sessionStorage.removeItem('omnivibe_brand') }
    else if (searchParams.get('brand')) setBrand(searchParams.get('brand')!)

    const savedCh = searchParams.get('channel')
    if (savedCh) setChannel(savedCh)
  }, [searchParams])
  const [theme, setTheme] = useState('dark')
  const [voice, setVoice] = useState('ko-KR-SunHiNeural')
  const [title, setTitle] = useState('')

  const [results, setResults] = useState<ProduceResult[]>([])
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const produce = useCallback(async (format: string) => {
    if (!script.trim()) {
      setError('스크립트를 입력하세요')
      return
    }

    setLoading(format)
    setError(null)

    try {
      let endpoint = ''
      if (format === 'presentation') endpoint = `/api/produce?type=presentation`
      else if (format === 'narration') endpoint = `/api/produce?type=narration`
      else if (format === 'video') endpoint = `/api/render-auto`
      else {
        setError('알 수 없는 포맷')
        setLoading(null)
        return
      }

      const payload = format === 'video'
        ? { script, brandName: brand || 'OmniVibe Pro', primaryColor: '#6366F1' }
        : { script, brand_name: brand || 'OmniVibe Pro', channel, format, title: title || undefined, theme, voice, voice_rate: '-5%' }

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || `HTTP ${res.status}`)
      }

      const data = await res.json()
      setResults(prev => [{
        type: format as any,
        filename: data.filename,
        download_url: data.download_url || data.downloadUrl,
        srt_url: data.srt_url,
        size_human: data.size_human || data.sizeHuman,
        slide_count: data.slide_count,
        voice: data.voice,
      }, ...prev])
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(null)
    }
  }, [script, brand, channel, theme, voice, title])

  const FORMAT_ICONS: Record<string, React.ReactNode> = {
    video: <Film className="w-4 h-4" />,
    presentation: <FileText className="w-4 h-4" />,
    narration: <Mic className="w-4 h-4" />,
  }

  return (
    <div className="max-w-5xl mx-auto py-8 px-6">
      <div className="mb-6"><PipelineNav /></div>
      {/* 헤더 */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-[#00FF88]/10 flex items-center justify-center">
          <Film className="w-5 h-5 text-[#00FF88]" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">콘텐츠 생산</h1>
          <p className="text-sm text-white/40">스크립트 → 영상 · 프레젠테이션 · 나레이션</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* 좌측: 입력 */}
        <div className="lg:col-span-3 space-y-4">
          <div className="rounded-xl bg-[#141414] border border-white/[0.07] p-5 space-y-4">
            {/* 제목 + 브랜드 */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">제목</label>
                <input value={title} onChange={e => setTitle(e.target.value)}
                  placeholder="자동 생성"
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#00FF88] focus:ring-1 focus:ring-[#00FF88]" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">브랜드</label>
                <input value={brand} onChange={e => setBrand(e.target.value)}
                  placeholder="OmniVibe Pro"
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#00FF88] focus:ring-1 focus:ring-[#00FF88]" />
              </div>
            </div>

            {/* 스크립트 */}
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1.5">스크립트</label>
              <textarea value={script} onChange={e => setScript(e.target.value)}
                rows={10} placeholder="[Hook]&#10;여기에 스크립트를 입력하세요&#10;&#10;[Body]&#10;본문 내용...&#10;&#10;[CTA]&#10;행동 유도..."
                className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-white/[0.03] placeholder-gray-500 focus:outline-none focus:border-[#00FF88] focus:ring-1 focus:ring-[#00FF88] font-mono resize-none" />
            </div>

            {/* 옵션 */}
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">테마</label>
                <select value={theme} onChange={e => setTheme(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-[#141414] focus:outline-none focus:border-[#00FF88]">
                  <option value="dark">다크</option>
                  <option value="light">라이트</option>
                  <option value="corporate">코퍼레이트</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">음성</label>
                <select value={voice} onChange={e => setVoice(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-[#141414] focus:outline-none focus:border-[#00FF88]">
                  {VOICES.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">채널</label>
                <select value={channel} onChange={e => setChannel(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-[#141414] focus:outline-none focus:border-[#00FF88]">
                  <option value="youtube">YouTube</option>
                  <option value="instagram">Instagram</option>
                  <option value="tiktok">TikTok</option>
                  <option value="blog">블로그</option>
                </select>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/10 px-3 py-2 rounded-lg">
                <AlertCircle className="w-3.5 h-3.5" /> {error}
              </div>
            )}

            {/* 생산 버튼 */}
            <div className="flex gap-3 pt-2">
              <button onClick={() => produce('presentation')} disabled={loading === 'presentation'}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-bold
                  bg-[#00A1E0]/10 border border-[#00A1E0]/20 text-[#00A1E0]
                  hover:bg-[#00A1E0]/20 transition-all disabled:opacity-50">
                {loading === 'presentation' ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                프레젠테이션
              </button>
              <button onClick={() => produce('narration')} disabled={loading === 'narration'}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-bold
                  bg-[#6366F1]/10 border border-[#6366F1]/20 text-[#6366F1]
                  hover:bg-[#6366F1]/20 transition-all disabled:opacity-50">
                {loading === 'narration' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mic className="w-4 h-4" />}
                나레이션 (TTS)
              </button>
              <button onClick={() => produce('video')} disabled={loading === 'video'}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-bold
                  bg-[#00FF88]/10 border border-[#00FF88]/20 text-[#00FF88]
                  hover:bg-[#00FF88]/20 transition-all disabled:opacity-50">
                {loading === 'video' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Film className="w-4 h-4" />}
                {loading === 'video' ? '영상 생성 중...' : 'AI 영상 생성'}
              </button>
            </div>
          </div>
        </div>

        {/* 우측: 결과 */}
        <div className="lg:col-span-2 space-y-3">
          <h2 className="text-sm font-bold text-white/50 uppercase tracking-wider">생산 결과</h2>
          {results.length === 0 ? (
            <div className="h-40 flex items-center justify-center rounded-xl bg-[#141414] border border-white/[0.07]">
              <p className="text-xs text-white/20">생산된 콘텐츠가 여기에 표시됩니다</p>
            </div>
          ) : (
            results.map((r, i) => (
              <div key={i} className="rounded-xl bg-[#141414] border border-white/[0.07] p-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-green-500/10 flex items-center justify-center text-green-400">
                    <CheckCircle className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold text-white truncate">{r.filename}</div>
                    <div className="text-[11px] text-white/30">
                      {r.type === 'presentation' && `${r.slide_count}슬라이드`}
                      {r.type === 'narration' && `${r.size_human} · ${r.voice}`}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {r.type === 'presentation' && (
                      <a href={r.download_url} target="_blank" rel="noopener"
                        className="p-2 rounded-lg bg-white/[0.05] text-white/40 hover:text-white/80 transition-colors">
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                    <a href={r.download_url} download
                      className="p-2 rounded-lg bg-white/[0.05] text-white/40 hover:text-white/80 transition-colors">
                      <Download className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default function ProducePage() {
  return (
    <AppShell>
      <Suspense fallback={<div className="flex items-center justify-center h-96 text-white/30">로딩 중...</div>}>
        <ProduceContent />
      </Suspense>
    </AppShell>
  )
}
