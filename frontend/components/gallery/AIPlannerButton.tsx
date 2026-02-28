'use client'

import { useState } from 'react'
import { Sparkles } from 'lucide-react'
import AIPlannerModal from './AIPlannerModal'

export default function AIPlannerButton() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-[#00A1E0] to-[#5867E8] text-white text-sm font-semibold rounded-lg hover:from-[#0090c7] hover:to-[#4a58d4] transition-all shadow-sm hover:shadow-md"
      >
        <Sparkles className="w-4 h-4" />
        AI 기획 도우미
      </button>

      {isOpen && <AIPlannerModal onClose={() => setIsOpen(false)} />}
    </>
  )
}
