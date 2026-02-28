'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { LayoutGrid, Bookmark, ChevronLeft, ChevronRight } from 'lucide-react'
import TemplateCard, { type Template } from '@/components/gallery/TemplateCard'
import TemplateFilter, { type FilterState } from '@/components/gallery/TemplateFilter'
import AIPlannerButton from '@/components/gallery/AIPlannerButton'
import { REMOTION_SHOWCASE } from '@/data/remotion-showcase'

// ─── Real Remotion Showcase Data ───────────────────────────────────────────────
// RemotionShowcaseItem → Template 타입 매핑 (web 플랫폼 포함)
const REAL_TEMPLATES: Template[] = REMOTION_SHOWCASE.map((item) => ({
  ...item,
  // 'web' 플랫폼은 필터용으로 youtube로 포함 처리 (web 전용이면 빈 배열)
  platform: item.platform.filter((p): p is 'youtube' | 'instagram' | 'tiktok' | 'web' => true),
}))

// ─── Mock Template Data (20 templates) — 레거시 보관 ──────────────────────────

const MOCK_TEMPLATES: Template[] = [
  // IT / Startup (4)
  {
    id: 'tech-minimal',
    name: 'Tech Minimal',
    description: '깔끔한 라인과 모노톤으로 기술 브랜드의 전문성을 강조하는 미니멀 템플릿',
    platform: ['youtube', 'instagram'],
    tone: ['minimal', 'professional'],
    duration: 60,
    category: 'it-startup',
    thumbnailColor: '#1a1a2e',
    sceneCount: 6,
    usageCount: 2340,
    tags: ['테크', '미니멀', 'SaaS'],
    isPremium: false,
  },
  {
    id: 'startup-bold',
    name: 'Startup Bold',
    description: '대담한 타이포그래피와 강렬한 컬러로 스타트업 에너지를 전달하는 템플릿',
    platform: ['youtube', 'tiktok'],
    tone: ['dynamic', 'trendy'],
    duration: 45,
    category: 'it-startup',
    thumbnailColor: '#e94560',
    sceneCount: 5,
    usageCount: 1870,
    tags: ['스타트업', '피칭', '투자'],
    isPremium: true,
  },
  {
    id: 'code-story',
    name: 'Code Story',
    description: '개발자 스토리텔링에 최적화된 코드 에디터 스타일 영상 템플릿',
    platform: ['youtube'],
    tone: ['professional', 'minimal'],
    duration: 90,
    category: 'it-startup',
    thumbnailColor: '#0f3460',
    sceneCount: 8,
    usageCount: 1560,
    tags: ['개발자', '코딩', '테크 블로그'],
    isPremium: false,
  },
  {
    id: 'dev-journey',
    name: 'Dev Journey',
    description: '개발 여정과 프로젝트 과정을 타임라인으로 보여주는 스토리형 템플릿',
    platform: ['youtube', 'instagram'],
    tone: ['emotional', 'professional'],
    duration: 120,
    category: 'it-startup',
    thumbnailColor: '#533483',
    sceneCount: 10,
    usageCount: 980,
    tags: ['프로젝트', '포트폴리오', '회고'],
    isPremium: true,
  },

  // Education / Tutorial (4)
  {
    id: 'learn-step',
    name: 'Learn Step',
    description: '단계별 학습 과정을 시각적으로 전달하는 교육 최적화 템플릿',
    platform: ['youtube'],
    tone: ['professional', 'minimal'],
    duration: 90,
    category: 'education',
    thumbnailColor: '#2d6a4f',
    sceneCount: 8,
    usageCount: 3120,
    tags: ['교육', '단계별', '학습'],
    isPremium: false,
  },
  {
    id: 'tutorial-clean',
    name: 'Tutorial Clean',
    description: '화면 캡처와 설명을 깔끔하게 배치하는 튜토리얼 전용 템플릿',
    platform: ['youtube', 'instagram'],
    tone: ['professional'],
    duration: 60,
    category: 'education',
    thumbnailColor: '#40916c',
    sceneCount: 6,
    usageCount: 2780,
    tags: ['튜토리얼', '가이드', '설명'],
    isPremium: false,
  },
  {
    id: 'howto-modern',
    name: 'How-To Modern',
    description: '모던한 디자인으로 How-To 콘텐츠를 만드는 실용적 템플릿',
    platform: ['youtube', 'tiktok'],
    tone: ['trendy', 'professional'],
    duration: 45,
    category: 'education',
    thumbnailColor: '#52b788',
    sceneCount: 5,
    usageCount: 2150,
    tags: ['하우투', '팁', '노하우'],
    isPremium: false,
  },
  {
    id: 'explain-simple',
    name: 'Explain Simple',
    description: '복잡한 개념을 애니메이션과 인포그래픽으로 쉽게 설명하는 템플릿',
    platform: ['youtube', 'instagram'],
    tone: ['minimal', 'emotional'],
    duration: 60,
    category: 'education',
    thumbnailColor: '#74c69d',
    sceneCount: 7,
    usageCount: 1930,
    tags: ['설명', '인포그래픽', '애니메이션'],
    isPremium: true,
  },

  // Lifestyle (4)
  {
    id: 'life-vlog',
    name: 'Life Vlog',
    description: '자연스러운 일상을 매력적으로 담는 브이로그 스타일 템플릿',
    platform: ['youtube', 'instagram'],
    tone: ['emotional', 'trendy'],
    duration: 90,
    category: 'lifestyle',
    thumbnailColor: '#f4845f',
    sceneCount: 8,
    usageCount: 4560,
    tags: ['브이로그', '일상', '라이프'],
    isPremium: false,
  },
  {
    id: 'daily-story',
    name: 'Daily Story',
    description: '하루를 스토리로 풀어내는 감성적인 일일 콘텐츠 템플릿',
    platform: ['instagram', 'tiktok'],
    tone: ['emotional'],
    duration: 30,
    category: 'lifestyle',
    thumbnailColor: '#f25c54',
    sceneCount: 4,
    usageCount: 3890,
    tags: ['데일리', '스토리', '감성'],
    isPremium: false,
  },
  {
    id: 'wellness-journey',
    name: 'Wellness Journey',
    description: '건강과 웰니스 여정을 차분하게 기록하는 힐링 템플릿',
    platform: ['youtube', 'instagram'],
    tone: ['emotional', 'minimal'],
    duration: 60,
    category: 'lifestyle',
    thumbnailColor: '#b5838d',
    sceneCount: 6,
    usageCount: 1670,
    tags: ['웰니스', '건강', '힐링'],
    isPremium: false,
  },
  {
    id: 'travel-cinematic',
    name: 'Travel Cinematic',
    description: '시네마틱한 영상미로 여행의 감동을 전달하는 프리미엄 템플릿',
    platform: ['youtube'],
    tone: ['emotional', 'dynamic'],
    duration: 120,
    category: 'lifestyle',
    thumbnailColor: '#f7b267',
    sceneCount: 10,
    usageCount: 2940,
    tags: ['여행', '시네마틱', '풍경'],
    isPremium: true,
  },

  // Business (4)
  {
    id: 'corporate-pro',
    name: 'Corporate Pro',
    description: '기업 프레젠테이션에 적합한 프로페셔널 비즈니스 템플릿',
    platform: ['youtube'],
    tone: ['professional'],
    duration: 90,
    category: 'business',
    thumbnailColor: '#16325C',
    sceneCount: 8,
    usageCount: 5230,
    tags: ['기업', '프레젠테이션', 'B2B'],
    isPremium: false,
  },
  {
    id: 'b2b-slide',
    name: 'B2B Slide',
    description: 'B2B 마케팅 슬라이드 영상을 자동으로 생성하는 템플릿',
    platform: ['youtube', 'instagram'],
    tone: ['professional', 'minimal'],
    duration: 60,
    category: 'business',
    thumbnailColor: '#1b4965',
    sceneCount: 6,
    usageCount: 3470,
    tags: ['B2B', '슬라이드', '마케팅'],
    isPremium: false,
  },
  {
    id: 'business-report',
    name: 'Business Report',
    description: '데이터와 차트를 영상으로 변환하는 비즈니스 리포트 템플릿',
    platform: ['youtube'],
    tone: ['professional', 'minimal'],
    duration: 120,
    category: 'business',
    thumbnailColor: '#5fa8d3',
    sceneCount: 10,
    usageCount: 2100,
    tags: ['리포트', '데이터', '차트'],
    isPremium: true,
  },
  {
    id: 'executive-brief',
    name: 'Executive Brief',
    description: '경영진 브리핑용 핵심 요약 영상을 만드는 프리미엄 템플릿',
    platform: ['youtube'],
    tone: ['professional'],
    duration: 45,
    category: 'business',
    thumbnailColor: '#274c77',
    sceneCount: 5,
    usageCount: 1450,
    tags: ['경영진', '브리핑', '요약'],
    isPremium: true,
  },

  // Entertainment (4)
  {
    id: 'fun-kinetic',
    name: 'Fun Kinetic',
    description: '빠른 모션과 키네틱 타이포로 주목도를 높이는 재미있는 템플릿',
    platform: ['tiktok', 'instagram'],
    tone: ['dynamic', 'trendy'],
    duration: 30,
    category: 'entertainment',
    thumbnailColor: '#ff6b6b',
    sceneCount: 4,
    usageCount: 6780,
    tags: ['키네틱', '모션', '재미'],
    isPremium: false,
  },
  {
    id: 'viral-energy',
    name: 'Viral Energy',
    description: '바이럴 콘텐츠 제작에 특화된 에너지 넘치는 숏폼 템플릿',
    platform: ['tiktok', 'instagram', 'youtube'],
    tone: ['dynamic', 'trendy'],
    duration: 15,
    category: 'entertainment',
    thumbnailColor: '#fca311',
    sceneCount: 3,
    usageCount: 8920,
    tags: ['바이럴', '숏폼', '에너지'],
    isPremium: false,
  },
  {
    id: 'comedy-cut',
    name: 'Comedy Cut',
    description: '코미디 컷 편집 스타일로 웃음을 유발하는 엔터테인먼트 템플릿',
    platform: ['tiktok', 'youtube'],
    tone: ['dynamic'],
    duration: 30,
    category: 'entertainment',
    thumbnailColor: '#e63946',
    sceneCount: 5,
    usageCount: 4230,
    tags: ['코미디', '컷편집', '유머'],
    isPremium: false,
  },
  {
    id: 'trend-chaser',
    name: 'Trend Chaser',
    description: '최신 트렌드를 빠르게 반영하는 숏폼 콘텐츠 특화 템플릿',
    platform: ['tiktok', 'instagram'],
    tone: ['trendy', 'dynamic'],
    duration: 15,
    category: 'entertainment',
    thumbnailColor: '#a8dadc',
    sceneCount: 3,
    usageCount: 5670,
    tags: ['트렌드', '숏폼', '챌린지'],
    isPremium: true,
  },
]

// ─── Sorting & Pagination ─────────────────────────────────────────────────────

type SortOption = 'popularity' | 'latest'

const ITEMS_PER_PAGE = 9

function matchesDurationFilter(duration: number, filter: string): boolean {
  switch (filter) {
    case 'short':
      return duration <= 30
    case 'medium':
      return duration > 30 && duration <= 60
    case 'long':
      return duration > 60
    default:
      return true
  }
}

// ─── Gallery Page ─────────────────────────────────────────────────────────────

export default function GalleryPage() {
  const router = useRouter()
  const [filters, setFilters] = useState<FilterState>({
    platforms: [],
    tones: [],
    duration: null,
  })
  const [sortBy, setSortBy] = useState<SortOption>('popularity')
  const [currentPage, setCurrentPage] = useState(1)

  const filteredTemplates = useMemo(() => {
    let result = [...REAL_TEMPLATES]

    // Platform filter
    if (filters.platforms.length > 0) {
      result = result.filter((t) =>
        t.platform.some((p) => filters.platforms.includes(p))
      )
    }

    // Tone filter
    if (filters.tones.length > 0) {
      result = result.filter((t) =>
        t.tone.some((tone) => filters.tones.includes(tone))
      )
    }

    // Duration filter
    if (filters.duration) {
      result = result.filter((t) => matchesDurationFilter(t.duration, filters.duration!))
    }

    // Sort
    if (sortBy === 'popularity') {
      result.sort((a, b) => b.usageCount - a.usageCount)
    } else {
      result.sort((a, b) => a.id.localeCompare(b.id))
    }

    return result
  }, [filters, sortBy])

  const totalPages = Math.max(1, Math.ceil(filteredTemplates.length / ITEMS_PER_PAGE))
  const safeCurrentPage = Math.min(currentPage, totalPages)
  const paginatedTemplates = filteredTemplates.slice(
    (safeCurrentPage - 1) * ITEMS_PER_PAGE,
    safeCurrentPage * ITEMS_PER_PAGE
  )

  const handleFiltersChange = (newFilters: FilterState) => {
    setFilters(newFilters)
    setCurrentPage(1)
  }

  return (
    <div className="min-h-screen bg-[#F3F2F2]">
      {/* Header */}
      <header className="bg-white border-b border-[#DDDBDA] sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <LayoutGrid className="w-6 h-6 text-[#00A1E0]" />
            <h1 className="text-xl font-bold text-[#16325C]">Remotion Showcase</h1>
            <span className="text-xs text-[#706E6B] bg-[#F3F2F2] px-2 py-0.5 rounded-full">
              실 사례 {filteredTemplates.length}개
            </span>
          </div>

          <div className="flex items-center gap-3">
            <AIPlannerButton />
            <button
              onClick={() => router.push('/studio')}
              className="flex items-center gap-2 px-4 py-2.5 border border-[#DDDBDA] bg-white text-[#16325C] text-sm font-semibold rounded-lg hover:bg-[#F3F2F2] transition-colors"
            >
              <Bookmark className="w-4 h-4" />
              내 컬렉션
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-6 flex gap-6">
        {/* Filter Sidebar */}
        <TemplateFilter filters={filters} onFiltersChange={handleFiltersChange} />

        {/* Grid Area */}
        <div className="flex-1">
          {/* Sort Bar */}
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-[#706E6B]">
              {filteredTemplates.length}개의 템플릿
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setSortBy('popularity')}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                  sortBy === 'popularity'
                    ? 'bg-[#16325C] text-white'
                    : 'bg-white text-[#706E6B] border border-[#DDDBDA] hover:bg-[#F3F2F2]'
                }`}
              >
                인기순
              </button>
              <button
                onClick={() => setSortBy('latest')}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                  sortBy === 'latest'
                    ? 'bg-[#16325C] text-white'
                    : 'bg-white text-[#706E6B] border border-[#DDDBDA] hover:bg-[#F3F2F2]'
                }`}
              >
                최신순
              </button>
            </div>
          </div>

          {/* Template Grid */}
          {paginatedTemplates.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {paginatedTemplates.map((template) => (
                <TemplateCard key={template.id} template={template} />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <LayoutGrid className="w-12 h-12 text-[#DDDBDA] mb-4" />
              <p className="text-sm font-semibold text-[#16325C] mb-1">
                조건에 맞는 템플릿이 없습니다
              </p>
              <p className="text-xs text-[#706E6B]">필터를 조정하거나 초기화해 보세요.</p>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                onClick={() => setCurrentPage(Math.max(1, safeCurrentPage - 1))}
                disabled={safeCurrentPage === 1}
                className={`p-2 rounded transition-colors ${
                  safeCurrentPage === 1
                    ? 'text-[#DDDBDA] cursor-not-allowed'
                    : 'text-[#706E6B] hover:bg-white hover:text-[#16325C]'
                }`}
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`w-8 h-8 text-xs font-medium rounded transition-colors ${
                    page === safeCurrentPage
                      ? 'bg-[#00A1E0] text-white'
                      : 'text-[#706E6B] hover:bg-white hover:text-[#16325C]'
                  }`}
                >
                  {page}
                </button>
              ))}

              <button
                onClick={() => setCurrentPage(Math.min(totalPages, safeCurrentPage + 1))}
                disabled={safeCurrentPage === totalPages}
                className={`p-2 rounded transition-colors ${
                  safeCurrentPage === totalPages
                    ? 'text-[#DDDBDA] cursor-not-allowed'
                    : 'text-[#706E6B] hover:bg-white hover:text-[#16325C]'
                }`}
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
