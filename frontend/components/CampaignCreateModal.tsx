'use client'

import { useState } from 'react'
import { X, Upload, Music, Video, Mic } from 'lucide-react'

interface CampaignCreateModalProps {
  isOpen: boolean
  onClose: () => void
  clientId: number
  onSuccess: () => void
}

export default function CampaignCreateModal({
  isOpen,
  onClose,
  clientId,
  onSuccess
}: CampaignCreateModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    concept_gender: 'female',
    concept_tone: 'professional',
    concept_style: 'soft',
    target_duration: 180, // 3분
    voice_id: '',
    voice_name: '',
    bgm_volume: 0.3,
    publish_schedule: '',
    auto_deploy: false
  })

  const [files, setFiles] = useState({
    intro: null as File | null,
    outro: null as File | null,
    bgm: null as File | null
  })

  const [uploading, setUploading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setUploading(true)

    try {
      // 1. 캠페인 생성 (Frontend API → SQLite)
      const res = await fetch('/api/campaigns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: clientId,
          ...formData
        })
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.error || '캠페인 생성 실패')
      }

      const data = await res.json()
      const campaign = data.campaign

      // 2. 파일 업로드 (Backend API - Cloudinary)
      if (files.intro || files.outro || files.bgm) {
        const formDataObj = new FormData()
        if (files.intro) formDataObj.append('intro', files.intro)
        if (files.outro) formDataObj.append('outro', files.outro)
        if (files.bgm) formDataObj.append('bgm', files.bgm)

        const uploadRes = await fetch(`/api/campaigns/${campaign.id}/resources`, {
          method: 'POST',
          body: formDataObj
        })

        if (!uploadRes.ok) {
          const errorData = await uploadRes.json()
          throw new Error(errorData.error || '파일 업로드 실패')
        }
      }

      onSuccess()
      onClose()
    } catch (error) {
      console.error('Failed to create campaign:', error)
      alert(error instanceof Error ? error.message : '캠페인 생성 실패')
    } finally {
      setUploading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">새 캠페인 생성</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 기본 정보 */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              캠페인명 *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              placeholder="예: 2026 AI 트렌드 시리즈"
            />
          </div>

          {/* 컨셉 설정 */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                성별
              </label>
              <select
                value={formData.concept_gender}
                onChange={(e) => setFormData({ ...formData, concept_gender: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                <option value="female">여성</option>
                <option value="male">남성</option>
                <option value="neutral">중성</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                톤
              </label>
              <select
                value={formData.concept_tone}
                onChange={(e) => setFormData({ ...formData, concept_tone: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                <option value="professional">전문성</option>
                <option value="friendly">친근함</option>
                <option value="humorous">유머</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                스타일
              </label>
              <select
                value={formData.concept_style}
                onChange={(e) => setFormData({ ...formData, concept_style: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                <option value="soft">부드러움</option>
                <option value="strong">강렬함</option>
                <option value="calm">차분함</option>
              </select>
            </div>
          </div>

          {/* 목표 분량 */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              목표 분량 (초)
            </label>
            <input
              type="number"
              min="15"
              max="600"
              value={formData.target_duration}
              onChange={(e) => setFormData({ ...formData, target_duration: parseInt(e.target.value) })}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
            <p className="text-xs text-gray-400 mt-1">
              {Math.floor(formData.target_duration / 60)}분 {formData.target_duration % 60}초
            </p>
          </div>

          {/* 인트로 업로드 */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              <Video size={16} className="inline mr-2" />
              인트로 영상 (선택)
            </label>
            <input
              type="file"
              accept="video/*"
              onChange={(e) => setFiles({ ...files, intro: e.target.files?.[0] || null })}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700"
            />
            {files.intro && (
              <p className="text-xs text-green-400 mt-1">선택됨: {files.intro.name}</p>
            )}
          </div>

          {/* 엔딩 업로드 */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              <Video size={16} className="inline mr-2" />
              엔딩 영상 (선택)
            </label>
            <input
              type="file"
              accept="video/*"
              onChange={(e) => setFiles({ ...files, outro: e.target.files?.[0] || null })}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700"
            />
            {files.outro && (
              <p className="text-xs text-green-400 mt-1">선택됨: {files.outro.name}</p>
            )}
          </div>

          {/* BGM 업로드 */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              <Music size={16} className="inline mr-2" />
              배경음악 (선택)
            </label>
            <input
              type="file"
              accept="audio/*"
              onChange={(e) => setFiles({ ...files, bgm: e.target.files?.[0] || null })}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700"
            />
            {files.bgm && (
              <p className="text-xs text-green-400 mt-1">선택됨: {files.bgm.name}</p>
            )}
            <div className="mt-2">
              <label className="text-xs text-gray-400">BGM 볼륨: {Math.round(formData.bgm_volume * 100)}%</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={formData.bgm_volume}
                onChange={(e) => setFormData({ ...formData, bgm_volume: parseFloat(e.target.value) })}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-600"
              />
            </div>
          </div>

          {/* 버튼 */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-white transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={uploading}
              className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded text-white disabled:opacity-50 transition-colors"
            >
              {uploading ? '생성 중...' : '캠페인 생성'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
