'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  X,
  Play,
  Users,
  Clock,
  Film,
  Tag,
  ChevronRight,
} from 'lucide-react'
import type { Template } from './TemplateCard'

interface TemplatePreviewModalProps {
  template: Template
  onClose: () => void
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

const categoryLabels: Record<string, string> = {
  'it-startup': 'IT / 스타트업',
  education: '교육 / 튜토리얼',
  lifestyle: '라이프스타일',
  business: '비즈니스',
  entertainment: '엔터테인먼트',
}

// 씬 미리보기 목업 데이터 (템플릿당 sceneCount개)
function generateScenes(template: Template) {
  const sceneTypes = [
    { label: '오프닝', duration: Math.round(template.duration * 0.1) },
    { label: '메인 타이틀', duration: Math.round(template.duration * 0.15) },
    { label: '콘텐츠 A', duration: Math.round(template.duration * 0.2) },
    { label: '콘텐츠 B', duration: Math.round(template.duration * 0.2) },
    { label: '하이라이트', duration: Math.round(template.duration * 0.15) },
    { label: '클로징', duration: Math.round(template.duration * 0.1) },
    { label: '엔딩 CTA', duration: Math.round(template.duration * 0.1) },
    { label: '아웃트로', duration: Math.round(template.duration * 0.1) },
    { label: '보너스 씬', duration: Math.round(template.duration * 0.05) },
    { label: '크레딧', duration: Math.round(template.duration * 0.05) },
  ]
  return sceneTypes.slice(0, template.sceneCount)
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}초`
  const min = Math.floor(seconds / 60)
  const sec = seconds % 60
  return sec > 0 ? `${min}분 ${sec}초` : `${min}분`
}

export default function TemplatePreviewModal({ template, onClose }: TemplatePreviewModalProps) {
  const router = useRouter()
  const scenes = generateScenes(template)

  // ESC 키로 닫기
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  // 배경 스크롤 잠금
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  const handleUseTemplate = () => {
    router.push(`/studio?template=${template.id}`)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Modal */}
      <div
        className="relative bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 상단 썸네일 영역 */}
        <div
          className="relative w-full flex-shrink-0"
          style={{ height: 220, backgroundColor: template.thumbnailColor }}
        >
          {/* 씬 타임라인 바 */}
          <div className="absolute bottom-0 left-0 right-0 flex h-1.5">
            {scenes.map((scene, i) => (
              <div
                key={i}
                className="flex-1 opacity-60 hover:opacity-100 transition-opacity"
                style={{
                  backgroundColor: i % 2 === 0 ? 'rgba(255,255,255,0.6)' : 'rgba(255,255,255,0.3)',
                }}
                title={scene.label}
              />
            ))}
          </div>

          {/* 중앙 텍스트 */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-white text-3xl font-black drop-shadow-lg">{template.name}</span>
            <span className="text-white/70 text-sm mt-2">
              {template.sceneCount} scenes · {formatDuration(template.duration)}
            </span>
          </div>

          {/* PRO 뱃지 */}
          {template.isPremium && (
            <div className="absolute top-4 right-4 bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs font-bold px-3 py-1 rounded-full shadow">
              PRO
            </div>
          )}

          {/* 닫기 버튼 */}
          <button
            onClick={onClose}
            className="absolute top-4 left-4 w-8 h-8 bg-black/40 hover:bg-black/60 rounded-full flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4 text-white" />
          </button>
        </div>

        {/* 본문 — 스크롤 가능 */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-6 flex flex-col gap-6">

            {/* 기본 정보 */}
            <div>
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <h2 className="text-xl font-bold text-[#16325C]">{template.name}</h2>
                  <p className="text-sm text-[#706E6B] mt-1">{template.description}</p>
                </div>
                <span className="text-xs text-[#706E6B] bg-[#F3F2F2] px-2 py-1 rounded whitespace-nowrap">
                  {categoryLabels[template.category] || template.category}
                </span>
              </div>

              {/* 플랫폼 + 분위기 */}
              <div className="flex flex-wrap gap-2">
                {template.platform.map((p) => (
                  <span
                    key={p}
                    className={`${platformStyles[p].bg} ${platformStyles[p].text} text-xs font-semibold px-2.5 py-1 rounded-full`}
                  >
                    {platformStyles[p].label}
                  </span>
                ))}
                {template.tone.map((t) => (
                  <span key={t} className="text-xs text-[#706E6B] bg-[#F3F2F2] px-2.5 py-1 rounded-full">
                    {toneLabels[t]}
                  </span>
                ))}
              </div>
            </div>

            {/* 스탯 */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { icon: Film, label: '씬 수', value: `${template.sceneCount}개` },
                { icon: Clock, label: '총 길이', value: formatDuration(template.duration) },
                { icon: Users, label: '사용 횟수', value: `${template.usageCount.toLocaleString()}회` },
              ].map(({ icon: Icon, label, value }) => (
                <div key={label} className="flex flex-col items-center justify-center gap-1 p-3 bg-[#F3F2F2] rounded-xl">
                  <Icon className="w-4 h-4 text-[#00A1E0]" />
                  <span className="text-[10px] text-[#706E6B] font-medium">{label}</span>
                  <span className="text-sm font-bold text-[#16325C]">{value}</span>
                </div>
              ))}
            </div>

            {/* 씬 구성 미리보기 */}
            <div>
              <h3 className="text-sm font-bold text-[#16325C] mb-3 flex items-center gap-2">
                <Film className="w-4 h-4 text-[#00A1E0]" />
                씬 구성
              </h3>
              <div className="space-y-2">
                {scenes.map((scene, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 p-3 bg-[#F3F2F2] rounded-lg hover:bg-[#EBEBEA] transition-colors"
                  >
                    <div
                      className="w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-bold text-white flex-shrink-0"
                      style={{ backgroundColor: template.thumbnailColor }}
                    >
                      {i + 1}
                    </div>
                    <span className="text-sm text-[#3E3E3C] flex-1">{scene.label}</span>
                    <span className="text-xs text-[#706E6B] font-mono">{scene.duration}s</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 태그 */}
            {template.tags.length > 0 && (
              <div>
                <h3 className="text-sm font-bold text-[#16325C] mb-2 flex items-center gap-2">
                  <Tag className="w-4 h-4 text-[#00A1E0]" />
                  태그
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {template.tags.map((tag) => (
                    <span key={tag} className="text-xs text-[#00A1E0] bg-[#00A1E0]/10 px-2.5 py-1 rounded-full">
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 하단 CTA */}
        <div className="flex-shrink-0 p-4 border-t border-[#DDDBDA] bg-white flex items-center justify-between gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2.5 border border-[#DDDBDA] text-[#706E6B] text-sm font-medium rounded-lg hover:bg-[#F3F2F2] transition-colors"
          >
            닫기
          </button>
          <button
            onClick={handleUseTemplate}
            className="flex items-center gap-2 px-6 py-2.5 bg-[#00A1E0] hover:bg-[#0090c7] text-white text-sm font-bold rounded-lg transition-colors shadow-md shadow-[#00A1E0]/30"
          >
            <Play className="w-4 h-4" />
            이 템플릿으로 시작
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
