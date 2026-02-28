'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Play, Eye, Users, Code2 } from 'lucide-react'
import TemplatePreviewModal from './TemplatePreviewModal'

export interface Template {
  id: string
  name: string
  description: string
  platform: ('youtube' | 'instagram' | 'tiktok' | 'web')[]
  tone: ('professional' | 'emotional' | 'trendy' | 'minimal' | 'dynamic')[]
  duration: number
  category: string
  thumbnailColor: string
  sceneCount: number
  usageCount: number
  tags: string[]
  isPremium: boolean
  // 실 사례 추가 필드
  sourceUrl?: string
  videoUrl?: string
  youtubeId?: string
  githubUrl?: string
  liveUrl?: string
  authorName?: string
  isReal?: boolean
  remotionProof?: 'official' | 'github' | 'story'
}

interface TemplateCardProps {
  template: Template
}

const platformStyles: Record<string, { bg: string; text: string; label: string }> = {
  youtube: { bg: 'bg-red-100', text: 'text-red-700', label: 'YouTube' },
  instagram: { bg: 'bg-pink-100', text: 'text-pink-700', label: 'Instagram' },
  tiktok: { bg: 'bg-gray-900', text: 'text-white', label: 'TikTok' },
  web: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Web' },
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
  const [showPreview, setShowPreview] = useState(false)
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
                setShowPreview(true)
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

        {/* YouTube Badge */}
        {template.youtubeId && !template.isPremium && (
          <div className="absolute top-2 right-2 bg-red-600/90 text-white text-[9px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
            <Play className="w-2.5 h-2.5 fill-white" />
            YouTube
          </div>
        )}
        {template.isReal && !template.youtubeId && !template.isPremium && (
          <div className="absolute top-2 right-2 bg-black/60 text-white text-[9px] font-bold px-2 py-0.5 rounded-full border border-white/20">
            실 사례
          </div>
        )}

        {/* Remotion 증거 뱃지 */}
        {template.remotionProof === 'official' && (
          <div className="absolute top-2 left-2 bg-[#0b0b0f]/90 text-white text-[9px] font-bold px-2 py-0.5 rounded-full border border-white/20 flex items-center gap-1">
            ✦ Remotion 공식
          </div>
        )}
        {template.remotionProof === 'github' && (
          <div className="absolute top-2 left-2 bg-[#24292f]/90 text-white text-[9px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
            ⌥ 소스 확인
          </div>
        )}
        {template.remotionProof === 'story' && (
          <div className="absolute top-2 left-2 bg-violet-700/80 text-white text-[9px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
            ★ 성공사례
          </div>
        )}
      </div>

      {/* Info Section */}
      <div className="p-4">
        <h3 className="text-sm font-bold text-[#16325C] mb-1 truncate">{template.name}</h3>
        <p className="text-xs text-[#706E6B] mb-3 line-clamp-2">{template.description}</p>

        {/* Platform Badges */}
        <div className="flex flex-wrap gap-1.5 mb-2">
          {template.platform
            .filter((p) => platformStyles[p])
            .map((p) => (
              <span
                key={p}
                className={`${platformStyles[p].bg} ${platformStyles[p].text} text-[10px] font-semibold px-2 py-0.5 rounded-full`}
              >
                {platformStyles[p].label}
              </span>
            ))}
          {/* 소스 코드 포함 뱃지 */}
          {template.githubUrl && (
            <span className="bg-violet-100 text-violet-700 text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-0.5">
              <Code2 className="w-2.5 h-2.5" />
              소스
            </span>
          )}
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

        {/* Author / Source */}
        {template.authorName && (
          <div className="flex items-center gap-1 mb-2">
            <span className="text-[10px] text-[#706E6B] truncate">by {template.authorName}</span>
            {template.githubUrl && (
              <a href={template.githubUrl} target="_blank" rel="noopener noreferrer"
                className="text-[10px] text-[#00A1E0] hover:underline shrink-0 ml-auto"
                onClick={(e) => e.stopPropagation()}>
                GitHub ↗
              </a>
            )}
          </div>
        )}

        {/* Footer: Usage Count + CTA */}
        <div className="flex items-center justify-between pt-2 border-t border-[#DDDBDA]">
          <span className="flex items-center gap-1 text-[11px] text-[#706E6B]">
            <Users className="w-3 h-3" />
            {template.usageCount.toLocaleString()}
            {template.isReal ? '★' : '회 사용'}
          </span>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setShowPreview(true)}
              className="flex items-center gap-1 px-2.5 py-1.5 border border-[#DDDBDA] text-[#706E6B] text-xs font-semibold rounded hover:bg-[#F3F2F2] transition-colors"
            >
              <Eye className="w-3 h-3" />
              미리보기
            </button>
            <button
              onClick={handleUseTemplate}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#00A1E0] text-white text-xs font-semibold rounded hover:bg-[#0090c7] transition-colors"
            >
              <Play className="w-3 h-3" />
              사용
            </button>
          </div>
        </div>
      </div>

      {/* Preview Modal */}
      {showPreview && (
        <TemplatePreviewModal
          template={template}
          onClose={() => setShowPreview(false)}
        />
      )}
    </div>
  )
}
