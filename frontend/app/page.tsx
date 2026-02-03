'use client'

import { useEffect, useState } from 'react'
import { LogIn, User } from 'lucide-react'
import { useAuth } from '../lib/contexts/AuthContext'
import AuthModal from '../components/AuthModal'
import { Button } from '../components/ui/Button'

interface APIStatus {
  status: string
  service: string
  version: string
  message: string
  features: {
    voice_cloning: string
    zero_fault_audio: string
    performance_tracking: string
    thumbnail_learning: string
  }
}

export default function Home() {
  const [apiStatus, setApiStatus] = useState<APIStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const { user, isAuthenticated, logout } = useAuth()

  useEffect(() => {
    fetch('/api/backend-status')
      .then(res => res.json())
      .then(data => {
        setApiStatus(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('API 연결 실패:', err)
        setLoading(false)
      })
  }, [])

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      <div className="container mx-auto px-4 py-16">
        {/* Auth Button */}
        <div className="absolute top-4 right-4">
          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <div className="bg-white/10 backdrop-blur-lg rounded-lg px-4 py-2 border border-white/20">
                <div className="flex items-center gap-2">
                  <User size={20} />
                  <span className="font-medium">{user?.name}</span>
                </div>
              </div>
              <Button
                onClick={logout}
                variant="danger"
                size="md"
              >
                로그아웃
              </Button>
            </div>
          ) : (
            <Button
              onClick={() => setShowAuthModal(true)}
              variant="ghost"
              size="md"
              className="flex items-center gap-2"
            >
              <LogIn size={20} />
              로그인
            </Button>
          )}
        </div>

        <div className="text-center mb-12">
          <h1 className="heading-1 mb-4 bg-clip-text text-transparent bg-gradient-to-r from-brand-primary-400 to-brand-secondary-600">
            OmniVibe Pro
          </h1>
          <p className="body-large text-gray-300">
            AI-powered Omnichannel Video Automation
          </p>
        </div>

        {loading ? (
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500 mx-auto"></div>
            <p className="mt-4 text-gray-400">API 서버 연결 중...</p>
          </div>
        ) : apiStatus ? (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 mb-8 border border-white/20">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-bold">API Status</h2>
                <span className="px-4 py-2 bg-green-500 text-white rounded-full text-sm font-semibold">
                  {apiStatus.status}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="bg-white/5 rounded-lg p-4">
                  <p className="text-gray-400 text-sm">Service</p>
                  <p className="text-xl font-semibold">{apiStatus.service}</p>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <p className="text-gray-400 text-sm">Version</p>
                  <p className="text-xl font-semibold">{apiStatus.version}</p>
                </div>
              </div>

              <p className="text-lg mb-6">{apiStatus.message}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-lg p-4 border border-purple-500/30">
                  <p className="text-sm text-gray-300">Voice Cloning</p>
                  <p className="text-lg font-semibold">{apiStatus.features?.voice_cloning ?? 'Loading...'}</p>
                </div>
                <div className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-lg p-4 border border-blue-500/30">
                  <p className="text-sm text-gray-300">Zero-Fault Audio</p>
                  <p className="text-lg font-semibold">{apiStatus.features?.zero_fault_audio ?? 'Loading...'}</p>
                </div>
                <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 rounded-lg p-4 border border-green-500/30">
                  <p className="text-sm text-gray-300">Performance Tracking</p>
                  <p className="text-lg font-semibold">{apiStatus.features?.performance_tracking ?? 'Loading...'}</p>
                </div>
                <div className="bg-gradient-to-br from-orange-500/20 to-yellow-500/20 rounded-lg p-4 border border-orange-500/30">
                  <p className="text-sm text-gray-300">Thumbnail Learning</p>
                  <p className="text-lg font-semibold">{apiStatus.features?.thumbnail_learning ?? 'Loading...'}</p>
                </div>
              </div>
            </div>

            {/* 통합 스튜디오 */}
            <div className="mb-8">
              <a
                href="/studio"
                className="block bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-2xl p-8 transition-all hover:scale-[1.02] shadow-2xl"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-3xl font-bold mb-2">🎬 통합 스튜디오</h2>
                    <p className="text-lg text-purple-100">모든 기능을 하나의 화면에서 - 프로 영상 편집 환경</p>
                  </div>
                  <div className="text-6xl">→</div>
                </div>
              </a>
            </div>

            {/* AI 에이전트 */}
            <div className="mb-8">
              <h2 className="text-2xl font-bold mb-4 text-center">🤖 AI 에이전트</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <a
                  href="/studio"
                  className="bg-gradient-to-br from-green-500/20 to-blue-500/20 hover:from-green-500/30 hover:to-blue-500/30 backdrop-blur-lg rounded-xl p-6 border border-green-500/30 transition-all hover:scale-105"
                >
                  <h3 className="text-xl font-bold mb-2">🎬 Studio</h3>
                  <p className="text-gray-300 text-sm">캠페인 관리 및 영상 제작</p>
                </a>

                <a
                  href="/schedule"
                  className="bg-gradient-to-br from-cyan-500/20 to-teal-500/20 hover:from-cyan-500/30 hover:to-teal-500/30 backdrop-blur-lg rounded-xl p-6 border border-cyan-500/30 transition-all hover:scale-105"
                >
                  <h3 className="text-xl font-bold mb-2">📅 스케줄 관리</h3>
                  <p className="text-gray-300 text-sm">SQLite CRUD + Pagination + Filter</p>
                </a>

                <a
                  href="/writer"
                  className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 hover:from-purple-500/30 hover:to-pink-500/30 backdrop-blur-lg rounded-xl p-6 border border-purple-500/30 transition-all hover:scale-105"
                >
                  <h3 className="text-xl font-bold mb-2">✍️ Writer Agent</h3>
                  <p className="text-gray-300 text-sm">스크립트 생성 및 정규화</p>
                </a>

                <a
                  href="/audio"
                  className="bg-gradient-to-br from-blue-500/20 to-indigo-500/20 hover:from-blue-500/30 hover:to-indigo-500/30 backdrop-blur-lg rounded-xl p-6 border border-blue-500/30 transition-all hover:scale-105"
                >
                  <h3 className="text-xl font-bold mb-2">🎵 Zero-Fault Audio</h3>
                  <p className="text-gray-300 text-sm">TTS → STT 검증 루프</p>
                </a>

                <a
                  href="/production"
                  className="bg-gradient-to-br from-red-500/20 to-orange-500/20 hover:from-red-500/30 hover:to-orange-500/30 backdrop-blur-lg rounded-xl p-6 border border-red-500/30 transition-all hover:scale-105"
                >
                  <h3 className="text-xl font-bold mb-2">🎬 Director Agent</h3>
                  <p className="text-gray-300 text-sm">영상 생성 및 콘티 편집</p>
                </a>

                <a
                  href="/presentation"
                  className="bg-gradient-to-br from-yellow-500/20 to-amber-500/20 hover:from-yellow-500/30 hover:to-amber-500/30 backdrop-blur-lg rounded-xl p-6 border border-yellow-500/30 transition-all hover:scale-105"
                >
                  <h3 className="text-xl font-bold mb-2">📊 Presentation Mode</h3>
                  <p className="text-gray-300 text-sm">PDF → 나레이션 영상</p>
                </a>
              </div>
            </div>

            {/* 개발 도구 */}
            <div>
              <h2 className="text-2xl font-bold mb-4 text-center">🛠️ 개발 도구</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  className="bg-white/10 hover:bg-white/20 backdrop-blur-lg rounded-xl p-6 border border-white/20 transition-all hover:scale-105"
                >
                  <h3 className="text-xl font-bold mb-2">📚 API Docs</h3>
                  <p className="text-gray-300 text-sm">Swagger UI 문서</p>
                </a>

                <a
                  href="http://localhost:8000/redoc"
                  target="_blank"
                  className="bg-white/10 hover:bg-white/20 backdrop-blur-lg rounded-xl p-6 border border-white/20 transition-all hover:scale-105"
                >
                  <h3 className="text-xl font-bold mb-2">📖 ReDoc</h3>
                  <p className="text-gray-300 text-sm">API 상세 문서</p>
                </a>

                <a
                  href="http://localhost:7474"
                  target="_blank"
                  className="bg-white/10 hover:bg-white/20 backdrop-blur-lg rounded-xl p-6 border border-white/20 transition-all hover:scale-105"
                >
                  <h3 className="text-xl font-bold mb-2">🔗 Neo4j</h3>
                  <p className="text-gray-300 text-sm">GraphRAG 브라우저</p>
                </a>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center bg-red-500/20 backdrop-blur-lg rounded-2xl p-8 border border-red-500/30">
            <h2 className="text-2xl font-bold mb-4">⚠️ API 서버 연결 실패</h2>
            <p className="text-gray-300">백엔드 서버가 실행 중인지 확인해주세요.</p>
            <p className="text-sm text-gray-400 mt-2">Expected: http://localhost:8000</p>
          </div>
        )}
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />
    </main>
  )
}
