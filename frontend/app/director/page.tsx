'use client'

import { useState } from 'react'
import { Play, Download, DollarSign, Film, Music } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function DirectorPage() {
  const [activeTab, setActiveTab] = useState<'audio' | 'video'>('audio')

  // Audio state
  const [audioScript, setAudioScript] = useState('')
  const [campaignName, setCampaignName] = useState('')
  const [topic, setTopic] = useState('')
  const [audioLoading, setAudioLoading] = useState(false)
  const [audioResult, setAudioResult] = useState<any>(null)

  // Video state
  const [videoScript, setVideoScript] = useState('')
  const [videoLoading, setVideoLoading] = useState(false)
  const [videoResult, setVideoResult] = useState<any>(null)

  const handleGenerateAudio = async () => {
    if (!audioScript || !campaignName || !topic) {
      alert('모든 필드를 입력해주세요')
      return
    }

    setAudioLoading(true)
    setAudioResult(null)

    try {
      const response = await fetch(`${API_URL}/api/v1/director/generate-audio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script: audioScript,
          campaign_name: campaignName,
          topic: topic,
          accuracy_threshold: 0.95,
          max_attempts: 5
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '오디오 생성 실패')
      }

      const data = await response.json()
      setAudioResult(data)
    } catch (error: any) {
      alert(error.message || '오디오 생성 중 오류가 발생했습니다')
    } finally {
      setAudioLoading(false)
    }
  }

  const handleGenerateVideo = async () => {
    if (!videoScript) {
      alert('스크립트를 입력해주세요')
      return
    }

    setVideoLoading(true)
    setVideoResult(null)

    try {
      const response = await fetch(`${API_URL}/api/v1/director/generate-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script: videoScript,
          project_name: '테스트 프로젝트',
          resolution: '1920x1080',
          fps: 30
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '비디오 생성 실패')
      }

      const data = await response.json()
      setVideoResult(data)
    } catch (error: any) {
      alert(error.message || '비디오 생성 중 오류가 발생했습니다')
    } finally {
      setVideoLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">🎬 Director Agent</h1>
          <p className="text-gray-400">
            Zero-Fault Audio Loop & AI Video Generation
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('audio')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition ${
              activeTab === 'audio'
                ? 'bg-blue-600 text-white'
                : 'bg-white/10 text-gray-400 hover:bg-white/20'
            }`}
          >
            <Music size={20} />
            오디오 생성
          </button>
          <button
            onClick={() => setActiveTab('video')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition ${
              activeTab === 'video'
                ? 'bg-purple-600 text-white'
                : 'bg-white/10 text-gray-400 hover:bg-white/20'
            }`}
          >
            <Film size={20} />
            비디오 생성
          </button>
        </div>

        {/* Audio Tab */}
        {activeTab === 'audio' && (
          <div className="space-y-6">
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <h2 className="text-2xl font-bold mb-4">🎙️ Zero-Fault Audio Loop</h2>
              <p className="text-gray-300 mb-6">
                ElevenLabs TTS → OpenAI Whisper STT → 정확도 검증 (95% 이상)
              </p>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">캠페인명</label>
                    <input
                      type="text"
                      value={campaignName}
                      onChange={(e) => setCampaignName(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2"
                      placeholder="예: 2025년 1월 캠페인"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">소제목</label>
                    <input
                      type="text"
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2"
                      placeholder="예: AI 기술 소개"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">스크립트</label>
                  <textarea
                    value={audioScript}
                    onChange={(e) => setAudioScript(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 h-40"
                    placeholder="오디오로 변환할 스크립트를 입력하세요..."
                  />
                </div>

                <button
                  onClick={handleGenerateAudio}
                  disabled={audioLoading}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-medium py-3 rounded-lg transition flex items-center justify-center gap-2"
                >
                  {audioLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white" />
                      생성 중... (최대 5회 시도)
                    </>
                  ) : (
                    <>
                      <Play size={20} />
                      오디오 생성
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Audio Result */}
            {audioResult && (
              <div className="bg-green-500/10 backdrop-blur-lg rounded-xl p-6 border border-green-500/30">
                <h3 className="text-xl font-bold mb-4 text-green-400">✅ 오디오 생성 완료</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white/5 rounded-lg p-4">
                    <p className="text-gray-400 text-sm">정확도</p>
                    <p className="text-2xl font-bold">
                      {(audioResult.similarity_score * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <p className="text-gray-400 text-sm">시도 횟수</p>
                    <p className="text-2xl font-bold">{audioResult.attempts}회</p>
                  </div>
                </div>
                {audioResult.audio_file_path && (
                  <a
                    href={`${API_URL}${audioResult.audio_file_path}`}
                    target="_blank"
                    className="mt-4 inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition"
                  >
                    <Download size={20} />
                    오디오 다운로드
                  </a>
                )}
              </div>
            )}
          </div>
        )}

        {/* Video Tab */}
        {activeTab === 'video' && (
          <div className="space-y-6">
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <h2 className="text-2xl font-bold mb-4">🎥 AI Video Generation</h2>
              <p className="text-gray-300 mb-6">
                Google Veo + Nano Banana → 일관된 캐릭터 영상 생성
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">스크립트</label>
                  <textarea
                    value={videoScript}
                    onChange={(e) => setVideoScript(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 h-40"
                    placeholder="비디오로 생성할 스크립트를 입력하세요..."
                  />
                </div>

                <button
                  onClick={handleGenerateVideo}
                  disabled={videoLoading}
                  className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white font-medium py-3 rounded-lg transition flex items-center justify-center gap-2"
                >
                  {videoLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white" />
                      비디오 생성 중...
                    </>
                  ) : (
                    <>
                      <Film size={20} />
                      비디오 생성
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Video Result */}
            {videoResult && (
              <div className="bg-purple-500/10 backdrop-blur-lg rounded-xl p-6 border border-purple-500/30">
                <h3 className="text-xl font-bold mb-4 text-purple-400">✅ 비디오 생성 완료</h3>
                <p className="text-gray-300 mb-4">프로젝트 ID: {videoResult.project_id}</p>
                {videoResult.video_path && (
                  <a
                    href={`${API_URL}${videoResult.video_path}`}
                    target="_blank"
                    className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg transition"
                  >
                    <Download size={20} />
                    비디오 다운로드
                  </a>
                )}
              </div>
            )}
          </div>
        )}

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          <div className="bg-white/5 backdrop-blur-lg rounded-lg p-4 border border-white/10">
            <h4 className="font-bold mb-2">🎯 Zero-Fault Loop</h4>
            <p className="text-sm text-gray-400">
              TTS 생성 후 STT로 검증하여 95% 이상 정확도 보장
            </p>
          </div>
          <div className="bg-white/5 backdrop-blur-lg rounded-lg p-4 border border-white/10">
            <h4 className="font-bold mb-2">🎨 일관된 캐릭터</h4>
            <p className="text-sm text-gray-400">
              Nano Banana 레퍼런스로 모든 영상에서 동일한 캐릭터 유지
            </p>
          </div>
          <div className="bg-white/5 backdrop-blur-lg rounded-lg p-4 border border-white/10">
            <h4 className="font-bold mb-2">📊 Neo4j 저장</h4>
            <p className="text-sm text-gray-400">
              모든 생성 기록을 GraphRAG에 영구 저장
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
