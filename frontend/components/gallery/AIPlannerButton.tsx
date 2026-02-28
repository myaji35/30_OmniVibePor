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
        className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all active:scale-95"
        style={{ background: 'linear-gradient(135deg, #a855f7, #6366f1)', boxShadow: '0 0 16px rgba(168,85,247,0.3)' }}
      >
        <Sparkles className="w-3.5 h-3.5" />
        AI 기획 도우미
      </button>

      {isOpen && <AIPlannerModal onClose={() => setIsOpen(false)} />}
    </>
  )
}
