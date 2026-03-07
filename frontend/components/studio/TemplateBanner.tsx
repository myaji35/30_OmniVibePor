'use client'

import { useState } from 'react'
import { Sparkles, ExternalLink, X } from 'lucide-react'

interface TemplateBannerProps {
  templateName: string
  githubUrl?: string
  liveUrl?: string
  authorName?: string
  onClose: () => void
}

export default function TemplateBanner({
  templateName,
  githubUrl,
  liveUrl,
  authorName,
  onClose,
}: TemplateBannerProps) {
  const [visible, setVisible] = useState(true)

  if (!visible) return null

  const handleClose = () => {
    setVisible(false)
    onClose()
  }

  return (
    <div
      className="flex items-center justify-between px-4 py-2.5 border-b"
      style={{
        background: 'rgba(168,85,247,0.08)',
        borderColor: 'rgba(168,85,247,0.2)',
      }}
    >
      <div className="flex items-center gap-2.5 text-sm">
        <Sparkles className="w-4 h-4 text-purple-400 flex-shrink-0" />
        <span className="text-purple-200">
          <span className="font-semibold text-purple-100">{templateName}</span> 템플릿 기반으로 시작합니다
        </span>
        {authorName && (
          <span className="text-purple-400/70 text-xs">by {authorName}</span>
        )}
      </div>

      <div className="flex items-center gap-2">
        {githubUrl && (
          <a
            href={githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs text-purple-300 hover:text-purple-100 transition-colors"
          >
            <ExternalLink className="w-3 h-3" />
            소스 보기
          </a>
        )}
        {liveUrl && !githubUrl && (
          <a
            href={liveUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs text-purple-300 hover:text-purple-100 transition-colors"
          >
            <ExternalLink className="w-3 h-3" />
            라이브 데모
          </a>
        )}
        <button
          onClick={handleClose}
          className="p-1 text-purple-400 hover:text-purple-100 transition-colors rounded"
          aria-label="배너 닫기"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}
