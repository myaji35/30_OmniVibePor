'use client'

import { useState } from 'react'
import { StoryboardBlock, generateStoryboardBlocks } from '@/lib/blocks/storyboard-types'
import StoryboardGrid from '@/components/StoryboardGrid'
import StoryboardBlockEditor from '@/components/StoryboardBlockEditor'
import { Sparkles, Download, Play, ArrowLeft } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function StoryboardPage() {
  const router = useRouter()
  const [blocks, setBlocks] = useState<StoryboardBlock[]>([])
  const [selectedBlock, setSelectedBlock] = useState<StoryboardBlock | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [scriptInput, setScriptInput] = useState('')
  const [showScriptInput, setShowScriptInput] = useState(true)

  const handleGenerateStoryboard = async () => {
    if (!scriptInput.trim()) {
      alert('스크립트를 입력해주세요')
      return
    }

    setIsGenerating(true)
    try {
      // 로컬에서 콘티 블록 생성
      const generatedBlocks = generateStoryboardBlocks(scriptInput, {
        mood: 'professional',
        color_tone: 'warm',
        style: 'modern'
      })

      setBlocks(generatedBlocks)
      setShowScriptInput(false)

      // 첫 번째 블록 자동 선택
      if (generatedBlocks.length > 0) {
        setSelectedBlock(generatedBlocks[0])
      }
    } catch (error) {
      console.error('콘티 블록 생성 실패:', error)
      alert('콘티 블록 생성에 실패했습니다.')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleBlockSelect = (block: StoryboardBlock) => {
    setSelectedBlock(block)
  }

  const handleBlockUpdate = (blockId: string, updates: Partial<StoryboardBlock>) => {
    setBlocks(prev => {
      const newBlocks = prev.map(block =>
        block.id === blockId ? { ...block, ...updates } : block
      )

      // 선택된 블록도 업데이트
      if (selectedBlock?.id === blockId) {
        setSelectedBlock({ ...selectedBlock, ...updates })
      }

      return newBlocks
    })
  }

  const handleExportStoryboard = () => {
    const dataStr = JSON.stringify(blocks, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `storyboard-${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const handleGenerateVideo = async () => {
    if (blocks.length === 0) {
      alert('콘티 블록이 없습니다')
      return
    }

    // TODO: 영상 생성 API 연동
    try {
      const response = await fetch('/api/storyboard/render', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ blocks })
      })

      const data = await response.json()
      console.log('영상 생성 요청:', data)
      alert('영상 생성이 시작되었습니다. 완료되면 알려드리겠습니다.')
    } catch (error) {
      console.error('영상 생성 실패:', error)
      alert('영상 생성 요청에 실패했습니다.')
    }
  }

  return (
    <div className="h-screen flex flex-col bg-[#0a0a0a] text-white">
      {/* 헤더 */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold">콘티 블록 편집기</h1>
            <p className="text-sm text-gray-400 mt-0.5">
              AI 기반 영상 콘티 자동 생성 및 편집
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {blocks.length > 0 && (
            <>
              <button
                onClick={handleExportStoryboard}
                className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <Download className="w-4 h-4" />
                내보내기
              </button>
              <button
                onClick={handleGenerateVideo}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors font-medium"
              >
                <Play className="w-4 h-4" />
                영상 생성
              </button>
            </>
          )}
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 스크립트 입력 모달 (초기 상태) */}
        {showScriptInput && blocks.length === 0 && (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="max-w-2xl w-full">
              <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-600/20 rounded-full mb-4">
                  <Sparkles className="w-8 h-8 text-purple-400" />
                </div>
                <h2 className="text-2xl font-bold mb-2">콘티 블록 자동 생성</h2>
                <p className="text-gray-400">
                  스크립트를 입력하면 AI가 자동으로 콘티 블록을 생성합니다
                </p>
              </div>

              <div className="space-y-4">
                <textarea
                  value={scriptInput}
                  onChange={(e) => setScriptInput(e.target.value)}
                  placeholder="스크립트를 입력하세요...&#10;&#10;예시:&#10;안녕하세요, 오늘은 AI 영상 제작 자동화에 대해 소개하겠습니다.&#10;구글 시트에서 전략을 수립하고, AI 에이전트가 자동으로 영상을 제작합니다.&#10;지금 바로 시작해보세요!"
                  className="w-full h-64 px-4 py-3 bg-gray-900 border border-gray-800 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
                />

                <button
                  onClick={handleGenerateStoryboard}
                  disabled={isGenerating || !scriptInput.trim()}
                  className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-800 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
                >
                  {isGenerating ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      생성 중...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      AI로 콘티 블록 생성
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 그리드 + 에디터 레이아웃 */}
        {blocks.length > 0 && (
          <>
            {/* 좌측: 그리드 */}
            <div className="flex-1 overflow-hidden">
              <StoryboardGrid
                blocks={blocks}
                selectedBlockId={selectedBlock?.id || null}
                onBlockSelect={handleBlockSelect}
                onBlockUpdate={handleBlockUpdate}
              />
            </div>

            {/* 우측: 에디터 */}
            <div className="w-96 border-l border-gray-800 overflow-hidden">
              {selectedBlock ? (
                <StoryboardBlockEditor
                  block={selectedBlock}
                  onUpdate={(updates) => handleBlockUpdate(selectedBlock.id, updates)}
                />
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-gray-500 p-8 text-center">
                  <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mb-4">
                    <Sparkles className="w-8 h-8" />
                  </div>
                  <p className="text-lg font-medium">블록을 선택하세요</p>
                  <p className="text-sm mt-2 text-gray-600">
                    좌측에서 편집할 콘티 블록을 클릭해주세요
                  </p>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
