'use client'

import VrewStyleEditor from '@/components/VrewStyleEditor'
import AppShell from '@/components/AppShell'

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
    <AppShell>
      <div className="max-w-5xl mx-auto py-8 px-6">
        <h1 className="text-2xl font-bold text-white mb-2">스크립트 편집기</h1>
        <p className="text-sm text-white/40 mb-6">블록 기반 스크립트 편집</p>
        <VrewStyleEditor onChange={handleBlocksChange} />
      </div>
    </AppShell>
  )
}
