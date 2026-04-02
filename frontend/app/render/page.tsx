'use client'

/**
 * 영상 렌더링 관리 — MP4 렌더 + 다운로드 + 삭제
 */
import { useState, useEffect, useCallback } from 'react'
import { Film, Download, Trash2, Loader2, Play, CheckCircle, AlertCircle } from 'lucide-react'
import AppShell from '@/components/AppShell'

interface RenderedFile {
  name: string
  compositionId: string
  downloadUrl: string
  size: number
  sizeHuman: string
  createdAt: string
}

const COMPOSITIONS = [
  { id: 'promo', label: 'OmniVibe Pro (EN)', desc: 'Remotion Feature Showcase — 영어 45초' },
  { id: 'promo-ko', label: 'OmniVibe Pro (KO)', desc: 'Remotion Feature Showcase — 한국어 45초' },
  { id: 'chopd', label: 'chopd (imPD)', desc: 'AI 브랜드 관리 — 여성 더빙 70초' },
  { id: 'insuregraph', label: 'InsureGraph Pro', desc: '보험 분석 AI — 남성 더빙 78초' },
  { id: 'bobot-safety', label: '보봇 안전성', desc: '"보봇은 왜 안전한가?" — 남성 더빙 113초' },
]

export default function RenderPage() {
  const [files, setFiles] = useState<RenderedFile[]>([])
  const [rendering, setRendering] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const fetchFiles = useCallback(async () => {
    try {
      const res = await fetch('/api/render-promo')
      const data = await res.json()
      setFiles(data.files || [])
    } catch { /* ignore */ }
  }, [])

  useEffect(() => { fetchFiles() }, [fetchFiles])

  const handleRender = useCallback(async (compositionId: string) => {
    setRendering(compositionId)
    setError(null)
    setSuccess(null)

    try {
      const res = await fetch('/api/render-promo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ compositionId }),
      })
      const data = await res.json()

      if (data.success) {
        setSuccess(`${compositionId}.mp4 렌더링 완료 (${data.sizeHuman})`)
        fetchFiles()
      } else {
        setError(data.error || '렌더링 실패')
      }
    } catch (e: any) {
      setError(e.message)
    } finally {
      setRendering(null)
    }
  }, [fetchFiles])

  const handleDelete = useCallback(async (compositionId: string) => {
    try {
      await fetch('/api/render-promo', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ compositionId }),
      })
      fetchFiles()
    } catch { /* ignore */ }
  }, [fetchFiles])

  const getFile = (id: string) => files.find(f => f.compositionId === id)

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto py-8 px-6">
        <div className="flex items-center gap-3 mb-8">
          <Film className="w-6 h-6 text-[#00A1E0]" />
          <h1 className="text-2xl font-bold text-white">영상 렌더링</h1>
        </div>

        {/* 알림 */}
        {error && (
          <div className="flex items-center gap-2 mb-4 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">
            <AlertCircle className="w-4 h-4 flex-shrink-0" /> {error}
          </div>
        )}
        {success && (
          <div className="flex items-center gap-2 mb-4 px-4 py-3 bg-green-500/10 border border-green-500/20 rounded-lg text-sm text-green-400">
            <CheckCircle className="w-4 h-4 flex-shrink-0" /> {success}
          </div>
        )}

        {/* Composition 목록 */}
        <div className="space-y-3">
          {COMPOSITIONS.map(comp => {
            const file = getFile(comp.id)
            const isRendering = rendering === comp.id

            return (
              <div key={comp.id} className="flex items-center gap-4 p-4 rounded-xl
                bg-[#141414] border border-white/[0.07] hover:border-white/[0.12] transition-colors">

                {/* 상태 아이콘 */}
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center
                  ${file ? 'bg-green-500/10 text-green-400' : 'bg-white/[0.05] text-white/30'}`}>
                  {isRendering ? (
                    <Loader2 className="w-5 h-5 animate-spin text-[#00A1E0]" />
                  ) : file ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : (
                    <Film className="w-5 h-5" />
                  )}
                </div>

                {/* 정보 */}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-white">{comp.label}</div>
                  <div className="text-xs text-white/40 mt-0.5">{comp.desc}</div>
                  {file && (
                    <div className="text-[11px] text-white/25 mt-1 font-mono">
                      {file.sizeHuman} · {new Date(file.createdAt).toLocaleString('ko-KR')}
                    </div>
                  )}
                </div>

                {/* 액션 버튼 */}
                <div className="flex items-center gap-2">
                  {/* 프리뷰 */}
                  <a
                    href={`http://localhost:3030/?composition=${comp.id}`}
                    target="_blank"
                    rel="noopener"
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold
                      bg-white/[0.05] border border-white/10 text-white/50
                      hover:text-white/80 hover:bg-white/[0.08] transition-all"
                  >
                    <Play className="w-3 h-3" />
                    프리뷰
                  </a>

                  {/* 렌더링 */}
                  <button
                    onClick={() => handleRender(comp.id)}
                    disabled={isRendering}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold
                      bg-[#00A1E0]/10 border border-[#00A1E0]/20 text-[#00A1E0]
                      hover:bg-[#00A1E0]/20 transition-all
                      disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {isRendering ? (
                      <><Loader2 className="w-3 h-3 animate-spin" /> 렌더링 중...</>
                    ) : (
                      <><Film className="w-3 h-3" /> {file ? '재렌더' : 'MP4 렌더'}</>
                    )}
                  </button>

                  {/* 다운로드 */}
                  {file && (
                    <a
                      href={file.downloadUrl}
                      download={file.name}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold
                        bg-green-500/10 border border-green-500/20 text-green-400
                        hover:bg-green-500/20 transition-all"
                    >
                      <Download className="w-3 h-3" />
                      다운로드
                    </a>
                  )}

                  {/* 삭제 */}
                  {file && (
                    <button
                      onClick={() => handleDelete(comp.id)}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold
                        bg-red-500/10 border border-red-500/20 text-red-400
                        hover:bg-red-500/20 transition-all"
                    >
                      <Trash2 className="w-3 h-3" />
                      삭제
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* 도움말 */}
        <div className="mt-8 p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
          <p className="text-xs text-white/30">
            렌더링된 MP4 파일은 <code className="text-white/50">frontend/public/rendered/</code> 에 저장됩니다.
            렌더링 시간은 영상 길이에 따라 1~5분 소요됩니다.
          </p>
        </div>
      </div>
    </AppShell>
  )
}
