'use client'

import { useState } from 'react'

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

// 플랫폼별 영상 비율 정의
const ASPECT_RATIOS = {
  'YouTube': '16:9 (가로)',
  'YouTube Shorts': '9:16 (세로)',
  'Instagram Feed': '1:1 (정사각형)',
  'Instagram Reels': '9:16 (세로)',
  'TikTok': '9:16 (세로)',
  'Facebook': '16:9 (가로)',
  'LinkedIn': '16:9 (가로)',
} as const

type PlatformKey = keyof typeof ASPECT_RATIOS

export default function WriterPage() {
  const [text, setText] = useState('')
  const [normalizeResult, setNormalizeResult] = useState<NormalizeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [platform, setPlatform] = useState<PlatformKey>('YouTube')
  const [campaignName, setCampaignName] = useState('')
  const [topic, setTopic] = useState('')
  const [generatedScript, setGeneratedScript] = useState<GeneratedScript | null>(null)

  // 텍스트 정규화
  const normalizeText = async () => {
    if (!text.trim()) {
      alert('텍스트를 입력해주세요')
      return
    }

    setLoading(true)
    try {
      const res = await fetch('/api/audio-normalize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      })

      const data = await res.json()

      if (res.ok) {
        setNormalizeResult(data)
      } else {
        alert(`정규화 실패: ${data.message || '알 수 없는 오류'}`)
      }
    } catch (err) {
      console.error('정규화 실패:', err)
      alert('정규화 중 오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      <div className="container mx-auto px-4 py-16">
        {/* 헤더 */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
            ✍️ Writer Agent
          </h1>
          <p className="text-xl text-gray-300">
            AI 작가 에이전트 - 스크립트 생성 및 텍스트 정규화
          </p>
        </div>

        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 왼쪽: 입력 섹션 */}
          <div className="space-y-6">
            {/* 플랫폼 선택 */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h2 className="text-2xl font-bold mb-4">🎯 플랫폼 및 영상 비율</h2>

              <div className="grid grid-cols-2 gap-3">
                {Object.entries(ASPECT_RATIOS).map(([platformName, ratio]) => (
                  <button
                    key={platformName}
                    onClick={() => setPlatform(platformName as PlatformKey)}
                    className={`px-4 py-3 rounded-lg transition-all text-left ${
                      platform === platformName
                        ? 'bg-gradient-to-r from-purple-500 to-pink-600 font-semibold'
                        : 'bg-white/5 hover:bg-white/10'
                    }`}
                  >
                    <div className="font-semibold">{platformName}</div>
                    <div className="text-xs text-gray-300 mt-1">{ratio}</div>
                  </button>
                ))}
              </div>

              <div className="mt-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <p className="text-sm">
                  <span className="font-semibold">선택된 플랫폼:</span> {platform}
                </p>
                <p className="text-sm mt-1">
                  <span className="font-semibold">영상 비율:</span> {ASPECT_RATIOS[platform]}
                </p>
              </div>
            </div>

            {/* 캠페인 정보 */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h2 className="text-2xl font-bold mb-4">📋 캠페인 정보</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-300 mb-2">
                    캠페인명
                  </label>
                  <input
                    type="text"
                    value={campaignName}
                    onChange={(e) => setCampaignName(e.target.value)}
                    placeholder="예: AI 자동화 시리즈"
                    className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">
                    주제/소제목
                  </label>
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="예: Zero-Fault Audio 시스템 소개"
                    className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
            </div>

            {/* 텍스트 정규화 */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h2 className="text-2xl font-bold mb-4">🔤 한국어 텍스트 정규화</h2>

              <div className="mb-4">
                <label className="block text-sm text-gray-300 mb-2">
                  입력 텍스트 (숫자 포함)
                </label>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="예: 2024년 1월 15일, 사과 3개를 2,000원에 샀습니다."
                  rows={4}
                  className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <button
                onClick={normalizeText}
                disabled={loading}
                className="w-full px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-lg font-semibold disabled:opacity-50"
              >
                {loading ? '정규화 중...' : '🔄 텍스트 정규화'}
              </button>

              <div className="mt-4 text-xs text-gray-400 space-y-1">
                <p>• 2024년 → 이천이십사년 (한자어)</p>
                <p>• 3개 → 세개 (고유어)</p>
                <p>• 25살 → 스물다섯살 (고유어)</p>
                <p>• 010-1234-5678 → 공일공 일이삼사 오육칠팔</p>
              </div>
            </div>
          </div>

          {/* 오른쪽: 결과 섹션 */}
          <div className="space-y-6">
            {/* 정규화 결과 */}
            {normalizeResult && (
              <div className="bg-gradient-to-br from-green-900/50 to-blue-900/50 backdrop-blur-lg rounded-2xl p-6 border border-green-500/30">
                <h2 className="text-2xl font-bold mb-4">✅ 정규화 결과</h2>

                <div className="mb-4 bg-white/5 rounded-lg p-4">
                  <p className="text-sm text-gray-400 mb-1">원본:</p>
                  <p className="text-sm">{normalizeResult.original}</p>
                </div>

                <div className="mb-4 bg-white/5 rounded-lg p-4">
                  <p className="text-sm text-gray-400 mb-1">정규화됨:</p>
                  <p className="text-sm font-semibold text-green-400">{normalizeResult.normalized}</p>
                </div>

                {Object.keys(normalizeResult.mappings).length > 0 && (
                  <div className="bg-white/5 rounded-lg p-4">
                    <p className="text-sm text-gray-400 mb-2">변환 매핑:</p>
                    <div className="space-y-1">
                      {Object.entries(normalizeResult.mappings).map(([original, converted]) => (
                        <div key={original} className="flex items-center gap-2 text-xs">
                          <span className="text-red-400">{original}</span>
                          <span>→</span>
                          <span className="text-green-400 font-semibold">{converted}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  onClick={() => {
                    navigator.clipboard.writeText(normalizeResult.normalized)
                    alert('정규화된 텍스트가 클립보드에 복사되었습니다!')
                  }}
                  className="mt-4 w-full px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm font-semibold"
                >
                  📋 정규화된 텍스트 복사
                </button>
              </div>
            )}

            {/* 사용 가이드 */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h2 className="text-xl font-bold mb-4">📖 사용 가이드</h2>

              <div className="space-y-3 text-sm text-gray-300">
                <div className="bg-white/5 rounded-lg p-3">
                  <p className="font-semibold mb-1">1️⃣ 플랫폼 선택</p>
                  <p className="text-xs text-gray-400">
                    영상을 배포할 플랫폼을 선택하세요. 플랫폼마다 최적 비율이 다릅니다.
                  </p>
                </div>

                <div className="bg-white/5 rounded-lg p-3">
                  <p className="font-semibold mb-1">2️⃣ 캠페인 정보 입력</p>
                  <p className="text-xs text-gray-400">
                    캠페인명과 주제를 입력하면 구글 시트와 연동됩니다.
                  </p>
                </div>

                <div className="bg-white/5 rounded-lg p-3">
                  <p className="font-semibold mb-1">3️⃣ 텍스트 정규화</p>
                  <p className="text-xs text-gray-400">
                    TTS 생성 전 숫자를 한글로 변환하여 발음 일관성을 보장합니다.
                  </p>
                </div>

                <div className="bg-white/5 rounded-lg p-3">
                  <p className="font-semibold mb-1">4️⃣ 영상 비율 자동 적용</p>
                  <p className="text-xs text-gray-400">
                    선택한 플랫폼의 최적 비율로 영상이 생성됩니다.
                  </p>
                </div>
              </div>
            </div>

            {/* 영상 비율 참고 */}
            <div className="bg-gradient-to-br from-orange-900/50 to-yellow-900/50 backdrop-blur-lg rounded-2xl p-6 border border-orange-500/30">
              <h2 className="text-xl font-bold mb-4">📐 영상 비율 참고</h2>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center bg-white/5 rounded p-2">
                  <span>가로 (Landscape)</span>
                  <span className="font-mono text-blue-400">16:9</span>
                </div>
                <div className="flex justify-between items-center bg-white/5 rounded p-2">
                  <span>정사각형 (Square)</span>
                  <span className="font-mono text-green-400">1:1</span>
                </div>
                <div className="flex justify-between items-center bg-white/5 rounded p-2">
                  <span>세로 (Portrait)</span>
                  <span className="font-mono text-purple-400">9:16</span>
                </div>
              </div>

              <p className="mt-4 text-xs text-gray-400">
                💡 영상 비율은 Director Agent에서 자동으로 적용됩니다.
              </p>
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
