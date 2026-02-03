'use client'

import VrewStyleEditor from '@/components/VrewStyleEditor'

/**
 * VrewStyleEditor 테스트 페이지
 *
 * 접근 경로: http://localhost:3020/script-editor
 */
export default function ScriptEditorTestPage() {
  const handleBlocksChange = (blocks: any[]) => {
    console.log('Blocks updated:', blocks)
  }

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="container mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-white mb-2">
            VrewStyleEditor 테스트
          </h1>
          <p className="text-gray-400">
            Vrew AI 스타일의 블록 기반 스크립트 편집기
          </p>
        </div>

        <VrewStyleEditor onChange={handleBlocksChange} />
      </div>
    </div>
  )
}
