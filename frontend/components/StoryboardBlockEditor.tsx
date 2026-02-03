'use client'

import { StoryboardBlock } from '@/lib/blocks/storyboard-types'
import { useState } from 'react'
import { Upload, Sparkles, ImageIcon, Palette, Loader2 } from 'lucide-react'

interface StoryboardBlockEditorProps {
  block: StoryboardBlock
  onUpdate: (updates: Partial<StoryboardBlock>) => void
}

export default function StoryboardBlockEditor({
  block,
  onUpdate
}: StoryboardBlockEditorProps) {
  const [backgroundTab, setBackgroundTab] = useState<'upload' | 'ai' | 'stock' | 'color'>(
    block.background_type === 'uploaded' ? 'upload' :
    block.background_type === 'ai_generated' ? 'ai' :
    block.background_type === 'stock' ? 'stock' : 'color'
  )
  const [aiPrompt, setAiPrompt] = useState(block.background_prompt || '')
  const [stockQuery, setStockQuery] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [stockImages, setStockImages] = useState<string[]>([])

  const handleGenerateAI = async () => {
    if (!aiPrompt.trim()) return

    setIsGenerating(true)
    try {
      // TODO: AI 이미지 생성 API 연동
      const response = await fetch('/api/storyboard/generate-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: aiPrompt })
      })

      const data = await response.json()
      onUpdate({
        background_type: 'ai_generated',
        background_url: data.image_url,
        background_prompt: aiPrompt
      })
    } catch (error) {
      console.error('AI 이미지 생성 실패:', error)
      alert('AI 이미지 생성에 실패했습니다.')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleSearchStock = async () => {
    if (!stockQuery.trim()) return

    try {
      // TODO: Unsplash API 연동
      const response = await fetch(`/api/storyboard/search-stock?query=${encodeURIComponent(stockQuery)}`)
      const data = await response.json()
      setStockImages(data.images || [])
    } catch (error) {
      console.error('스톡 이미지 검색 실패:', error)
    }
  }

  const handleUploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // TODO: 파일 업로드 처리
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/storyboard/upload', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()
      onUpdate({
        background_type: 'uploaded',
        background_url: data.url
      })
    } catch (error) {
      console.error('파일 업로드 실패:', error)
      alert('파일 업로드에 실패했습니다.')
    }
  }

  return (
    <div className="h-full flex flex-col bg-gray-900 overflow-y-auto">
      <div className="p-6 space-y-6">
        <h2 className="text-lg font-semibold">블록 #{block.order + 1} 설정</h2>

        {/* 스크립트 */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-300">
            스크립트
          </label>
          <textarea
            value={block.script}
            onChange={(e) => onUpdate({ script: e.target.value })}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
            rows={3}
          />
        </div>

        {/* 타이밍 조정 */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-300">
              시작 시간 (초)
            </label>
            <input
              type="number"
              step="0.1"
              value={block.start_time}
              onChange={(e) => onUpdate({ start_time: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-300">
              종료 시간 (초)
            </label>
            <input
              type="number"
              step="0.1"
              value={block.end_time}
              onChange={(e) => onUpdate({ end_time: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>

        {/* 배경 설정 */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-300">
            배경
          </label>

          {/* 탭 */}
          <div className="flex gap-2 mb-3">
            <button
              onClick={() => setBackgroundTab('upload')}
              className={`flex items-center gap-1 px-3 py-1.5 text-sm rounded transition-colors ${
                backgroundTab === 'upload'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              <Upload className="w-3 h-3" />
              업로드
            </button>
            <button
              onClick={() => setBackgroundTab('ai')}
              className={`flex items-center gap-1 px-3 py-1.5 text-sm rounded transition-colors ${
                backgroundTab === 'ai'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              <Sparkles className="w-3 h-3" />
              AI 생성
            </button>
            <button
              onClick={() => setBackgroundTab('stock')}
              className={`flex items-center gap-1 px-3 py-1.5 text-sm rounded transition-colors ${
                backgroundTab === 'stock'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              <ImageIcon className="w-3 h-3" />
              스톡 이미지
            </button>
            <button
              onClick={() => setBackgroundTab('color')}
              className={`flex items-center gap-1 px-3 py-1.5 text-sm rounded transition-colors ${
                backgroundTab === 'color'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              <Palette className="w-3 h-3" />
              단색
            </button>
          </div>

          {/* 업로드 */}
          {backgroundTab === 'upload' && (
            <div className="space-y-2">
              <input
                type="file"
                accept="image/*,video/*"
                onChange={handleUploadFile}
                className="w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700 cursor-pointer"
              />
              <p className="text-xs text-gray-500">
                이미지 또는 영상 파일을 업로드하세요
              </p>
            </div>
          )}

          {/* AI 생성 */}
          {backgroundTab === 'ai' && (
            <div className="space-y-2">
              <input
                type="text"
                placeholder="프롬프트 입력 (예: Modern office workspace with natural light)"
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !isGenerating) {
                    handleGenerateAI()
                  }
                }}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <button
                onClick={handleGenerateAI}
                disabled={isGenerating || !aiPrompt.trim()}
                className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    생성 중...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    AI로 생성
                  </>
                )}
              </button>
            </div>
          )}

          {/* 스톡 이미지 검색 */}
          {backgroundTab === 'stock' && (
            <div className="space-y-2">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="검색 키워드 (예: technology, office)"
                  value={stockQuery}
                  onChange={(e) => setStockQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSearchStock()
                    }
                  }}
                  className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <button
                  onClick={handleSearchStock}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium transition-colors"
                >
                  검색
                </button>
              </div>

              {stockImages.length > 0 && (
                <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto">
                  {stockImages.map((url, index) => (
                    <div
                      key={index}
                      onClick={() => onUpdate({
                        background_type: 'stock',
                        background_url: url
                      })}
                      className="relative aspect-video rounded overflow-hidden cursor-pointer hover:ring-2 hover:ring-purple-500 transition-all"
                    >
                      <img
                        src={url}
                        alt={`Stock ${index + 1}`}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 단색 */}
          {backgroundTab === 'color' && (
            <div className="space-y-3">
              <input
                type="color"
                value={block.background_color || '#000000'}
                onChange={(e) => onUpdate({
                  background_type: 'solid_color',
                  background_color: e.target.value
                })}
                className="w-full h-24 rounded-lg cursor-pointer"
              />
              <div className="grid grid-cols-4 gap-2">
                {['#000000', '#ffffff', '#1a1a1a', '#2d2d2d', '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'].map(color => (
                  <button
                    key={color}
                    onClick={() => onUpdate({
                      background_type: 'solid_color',
                      background_color: color
                    })}
                    className="h-8 rounded border-2 border-gray-700 hover:border-purple-500 transition-colors"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 전환 효과 */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-300">
            전환 효과
          </label>
          <select
            value={block.transition_effect}
            onChange={(e) => onUpdate({ transition_effect: e.target.value as StoryboardBlock['transition_effect'] })}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="fade">Fade (페이드)</option>
            <option value="slide">Slide (슬라이드)</option>
            <option value="dissolve">Dissolve (디졸브)</option>
            <option value="zoom">Zoom (줌)</option>
          </select>
        </div>

        {/* 자막 스타일 */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-300">
            자막 스타일
          </label>
          <select
            value={block.subtitle_preset}
            onChange={(e) => onUpdate({ subtitle_preset: e.target.value as StoryboardBlock['subtitle_preset'] })}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="normal">Normal (일반)</option>
            <option value="bold">Bold (굵게)</option>
            <option value="minimal">Minimal (미니멀)</option>
            <option value="news">News (뉴스)</option>
          </select>
        </div>

        {/* 키워드 편집 */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-300">
            키워드
          </label>
          <div className="flex flex-wrap gap-2 mb-2">
            {block.keywords.map((keyword, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 px-2 py-1 bg-purple-600/30 text-purple-300 rounded text-xs"
              >
                {keyword}
                <button
                  onClick={() => {
                    const newKeywords = block.keywords.filter((_, i) => i !== index)
                    onUpdate({ keywords: newKeywords })
                  }}
                  className="hover:text-red-400"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
          <input
            type="text"
            placeholder="키워드 입력 후 Enter"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                const input = e.currentTarget
                const keyword = input.value.trim()
                if (keyword && !block.keywords.includes(keyword)) {
                  onUpdate({ keywords: [...block.keywords, keyword] })
                  input.value = ''
                }
              }
            }}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>
      </div>
    </div>
  )
}
