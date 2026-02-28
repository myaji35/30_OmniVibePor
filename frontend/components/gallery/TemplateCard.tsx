'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Play, Eye, Users } from 'lucide-react'

export interface Template {
  id: string
  name: string
  description: string
  platform: ('youtube' | 'instagram' | 'tiktok')[]
  tone: ('professional' | 'emotional' | 'trendy' | 'minimal' | 'dynamic')[]
  duration: number
  category: string
  thumbnailColor: string
  sceneCount: number
  usageCount: number
  tags: string[]
  isPremium: boolean
}

interface TemplateCardProps {
  template: Template
}

const platformStyles: Record<string, { bg: string; text: string; label: string }> = {
  youtube: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'YouTube' },
  instagram: { bg: 'bg-pink-100', text: 'text-pink-700', label: 'Instagram' },
  tiktok: { bg: 'bg-gray-900', text: 'text-white', label: 'TikTok' },
}

const toneLabels: Record<string, string> = {
  professional: '전문적',
  emotional: '감성적',
  trendy: '트렌디',
  minimal: '미니멀',
  dynamic: '다이나믹',
}

export default function TemplateCard({ template }: TemplateCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const router = useRouter()

  const handleUseTemplate = () => {
    router.push(`/studio?template=${template.id}`)
  }

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}초`
    const min = Math.floor(seconds / 60)
    const sec = seconds % 60
    return sec > 0 ? `${min}분 ${sec}초` : `${min}분`
  }

  return (
    <div
      className="bg-white rounded-lg shadow-sm border border-[#DDDBDA] overflow-hidden transition-all duration-200 hover:shadow-md hover:border-[#00A1E0]/30"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Thumbnail Preview Area - 16:9 */}
      <div
        className="relative w-full overflow-hidden"
        style={{ paddingBottom: '56.25%', backgroundColor: template.thumbnailColor }}
      >
        <div className="absolute inset-0 flex flex-col items-center justify-center p-4">
          <span className="text-white/90 text-lg font-bold text-center drop-shadow-md">
            {template.name}
          </span>
          <span className="text-white/60 text-xs mt-1">
            {template.sceneCount} scenes / {formatDuration(template.duration)}
          </span>
        </div>

        {/* Hover Overlay */}
        {isHovered && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center transition-opacity duration-200">
            <button
              className="flex items-center gap-2 px-4 py-2 bg-white/90 text-[#16325C] rounded-md text-sm font-semibold hover:bg-white transition-colors"
              onClick={(e) => {
                e.stopPropagation()
              }}
            >
              <Eye className="w-4 h-4" />
              미리보기
            </button>
          </div>
        )}

        {/* Premium Badge */}
        {template.isPremium && (
          <div className="absolute top-2 right-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
            PRO
          </div>
        )}
      </div>

      {/* Info Section */}
      <div className="p-4">
        <h3 className="text-sm font-bold text-[#16325C] mb-1 truncate">{template.name}</h3>
        <p className="text-xs text-[#706E6B] mb-3 line-clamp-2">{template.description}</p>

        {/* Platform Badges */}
        <div className="flex flex-wrap gap-1.5 mb-2">
          {template.platform.map((p) => (
            <span
              key={p}
              className={`${platformStyles[p].bg} ${platformStyles[p].text} text-[10px] font-semibold px-2 py-0.5 rounded-full`}
            >
              {platformStyles[p].label}
            </span>
          ))}
        </div>

        {/* Tone Tags */}
        <div className="flex flex-wrap gap-1 mb-3">
          {template.tone.map((t) => (
            <span
              key={t}
              className="text-[10px] text-[#706E6B] bg-[#F3F2F2] px-1.5 py-0.5 rounded"
            >
              {toneLabels[t]}
            </span>
          ))}
        </div>

        {/* Footer: Usage Count + CTA */}
        <div className="flex items-center justify-between pt-2 border-t border-[#DDDBDA]">
          <span className="flex items-center gap-1 text-[11px] text-[#706E6B]">
            <Users className="w-3 h-3" />
            {template.usageCount.toLocaleString()}회 사용
          </span>
          <button
            onClick={handleUseTemplate}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#00A1E0] text-white text-xs font-semibold rounded hover:bg-[#0090c7] transition-colors"
          >
            <Play className="w-3 h-3" />
            이 템플릿 사용
          </button>
        </div>
      </div>
    </div>
  )
}
