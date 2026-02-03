'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/Button'
import { Plus, Trash2, TrendingUp, BarChart3, Check } from 'lucide-react'

interface ABTest {
  id: number
  content_id: number
  variant_name: string
  script_version: string | null
  audio_url: string | null
  video_url: string | null
  views: number
  engagement_rate: number
  created_at: string
}

interface ABTestManagerProps {
  contentId: number | null
  onClose: () => void
}

export default function ABTestManager({ contentId, onClose }: ABTestManagerProps) {
  const [variants, setVariants] = useState<ABTest[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [bestVariant, setBestVariant] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newVariant, setNewVariant] = useState({
    variant_name: '',
    script_version: ''
  })

  // 변형 목록 로드
  const loadVariants = async () => {
    if (!contentId) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`http://localhost:8000/api/v1/ab-tests/${contentId}`)
      if (!response.ok) {
        throw new Error('변형 목록 로드 실패')
      }

      const data = await response.json()
      setVariants(data.tests)

      // 최고 성과 변형 자동 계산
      if (data.tests.length > 0) {
        const best = data.tests.reduce((prev: ABTest, current: ABTest) =>
          current.engagement_rate > prev.engagement_rate ? current : prev
        )
        setBestVariant(best.variant_name)
      }
    } catch (err: any) {
      setError(err.message || 'Unknown error')
      console.error('변형 로드 실패:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadVariants()
  }, [contentId])

  // 새 변형 생성
  const createVariant = async () => {
    if (!contentId || !newVariant.variant_name.trim()) {
      alert('변형 이름을 입력하세요 (예: A, B, C)')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/api/v1/ab-tests/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content_id: contentId,
          variant_name: newVariant.variant_name,
          script_version: newVariant.script_version || null
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '변형 생성 실패')
      }

      const created = await response.json()
      console.log('변형 생성 완료:', created)

      // 폼 초기화 및 목록 재로드
      setNewVariant({ variant_name: '', script_version: '' })
      setShowCreateForm(false)
      await loadVariants()
    } catch (err: any) {
      setError(err.message || 'Unknown error')
      console.error('변형 생성 실패:', err)
    } finally {
      setLoading(false)
    }
  }

  // 성과 업데이트
  const updatePerformance = async (testId: number, views: number, engagementRate: number) => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`http://localhost:8000/api/v1/ab-tests/${testId}/track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ views, engagement_rate: engagementRate })
      })

      if (!response.ok) {
        throw new Error('성과 업데이트 실패')
      }

      await loadVariants()
    } catch (err: any) {
      setError(err.message || 'Unknown error')
      console.error('성과 업데이트 실패:', err)
    } finally {
      setLoading(false)
    }
  }

  // 변형 삭제
  const deleteVariant = async (testId: number) => {
    if (!confirm('이 변형을 삭제하시겠습니까?')) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`http://localhost:8000/api/v1/ab-tests/${testId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error('변형 삭제 실패')
      }

      await loadVariants()
    } catch (err: any) {
      setError(err.message || 'Unknown error')
      console.error('변형 삭제 실패:', err)
    } finally {
      setLoading(false)
    }
  }

  if (!contentId) {
    return (
      <div className="bg-gray-900 text-white p-6 rounded-lg">
        <p className="text-gray-400">먼저 콘텐츠를 선택하세요</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 text-white p-6 rounded-lg space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="w-6 h-6" />
            A/B 테스트 관리
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            여러 변형을 생성하고 성과를 비교하세요
          </p>
        </div>
        <Button onClick={onClose} variant="ghost" size="sm">
          <span className="text-xl">×</span>
        </Button>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-400 p-3 rounded">
          {error}
        </div>
      )}

      {/* 새 변형 생성 버튼 */}
      {!showCreateForm && (
        <Button
          onClick={() => setShowCreateForm(true)}
          variant="primary"
          size="sm"
          className="w-full"
          disabled={loading}
        >
          <Plus className="w-4 h-4 mr-2" />
          새 변형 생성
        </Button>
      )}

      {/* 새 변형 생성 폼 */}
      {showCreateForm && (
        <div className="bg-gray-800 p-4 rounded space-y-3 border border-gray-700">
          <h3 className="font-semibold">새 변형 생성</h3>
          <div>
            <label className="block text-sm text-gray-400 mb-1">변형 이름 (예: A, B, C)</label>
            <input
              type="text"
              value={newVariant.variant_name}
              onChange={(e) => setNewVariant({ ...newVariant, variant_name: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              placeholder="A"
              maxLength={10}
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">스크립트 버전 (선택)</label>
            <textarea
              value={newVariant.script_version}
              onChange={(e) => setNewVariant({ ...newVariant, script_version: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 h-24"
              placeholder="스크립트 내용을 입력하세요..."
            />
          </div>
          <div className="flex gap-2">
            <Button onClick={createVariant} variant="primary" size="sm" disabled={loading}>
              생성
            </Button>
            <Button onClick={() => setShowCreateForm(false)} variant="secondary" size="sm">
              취소
            </Button>
          </div>
        </div>
      )}

      {/* 변형 목록 */}
      <div className="space-y-3">
        <h3 className="font-semibold text-lg">변형 목록 ({variants.length}개)</h3>
        {loading && variants.length === 0 && (
          <div className="text-center text-gray-400 py-8">로딩 중...</div>
        )}
        {!loading && variants.length === 0 && (
          <div className="text-center text-gray-400 py-8">
            아직 변형이 없습니다. 새 변형을 생성하세요.
          </div>
        )}
        {variants.map((variant) => (
          <div
            key={variant.id}
            className={`bg-gray-800 p-4 rounded space-y-3 border ${
              variant.variant_name === bestVariant
                ? 'border-green-500'
                : 'border-gray-700'
            }`}
          >
            {/* 변형 헤더 */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold">{variant.variant_name}</span>
                {variant.variant_name === bestVariant && (
                  <span className="bg-green-500 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" />
                    최고 성과
                  </span>
                )}
              </div>
              <Button
                onClick={() => deleteVariant(variant.id)}
                variant="ghost"
                size="sm"
                disabled={loading}
              >
                <Trash2 className="w-4 h-4 text-red-400" />
              </Button>
            </div>

            {/* 성과 지표 */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-400 mb-1">조회수</label>
                <input
                  type="number"
                  value={variant.views}
                  onChange={(e) =>
                    updatePerformance(
                      variant.id,
                      parseInt(e.target.value) || 0,
                      variant.engagement_rate
                    )
                  }
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">참여율 (%)</label>
                <input
                  type="number"
                  value={variant.engagement_rate}
                  onChange={(e) =>
                    updatePerformance(
                      variant.id,
                      variant.views,
                      parseFloat(e.target.value) || 0
                    )
                  }
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                  min="0"
                  max="100"
                  step="0.1"
                />
              </div>
            </div>

            {/* 스크립트 미리보기 */}
            {variant.script_version && (
              <div className="bg-gray-900 p-3 rounded text-sm text-gray-300 line-clamp-3">
                {variant.script_version}
              </div>
            )}

            {/* 미디어 URL */}
            {(variant.audio_url || variant.video_url) && (
              <div className="text-sm text-gray-400 space-y-1">
                {variant.audio_url && (
                  <div>
                    <span className="font-semibold">오디오:</span>{' '}
                    <a href={variant.audio_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 underline">
                      {variant.audio_url.substring(0, 40)}...
                    </a>
                  </div>
                )}
                {variant.video_url && (
                  <div>
                    <span className="font-semibold">비디오:</span>{' '}
                    <a href={variant.video_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 underline">
                      {variant.video_url.substring(0, 40)}...
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 비교 통계 */}
      {variants.length > 1 && (
        <div className="bg-gray-800 p-4 rounded border border-gray-700">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            비교 통계
          </h3>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">총 변형 수:</span>
              <span className="font-semibold">{variants.length}개</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">총 조회수:</span>
              <span className="font-semibold">
                {variants.reduce((sum, v) => sum + v.views, 0).toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">평균 참여율:</span>
              <span className="font-semibold">
                {(variants.reduce((sum, v) => sum + v.engagement_rate, 0) / variants.length).toFixed(2)}%
              </span>
            </div>
            {bestVariant && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">최고 변형:</span>
                <span className="font-semibold text-green-400">{bestVariant}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
