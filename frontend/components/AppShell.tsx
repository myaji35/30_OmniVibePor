'use client'

import { useState, useEffect, useCallback } from 'react'
import { usePathname } from 'next/navigation'
import Link from 'next/link'
import {
  Zap, LayoutDashboard, PenTool, Clapperboard, Layers,
  Volume2, FileText, Monitor, Rocket, Image, Upload,
  Presentation, CalendarDays, Settings, ChevronDown,
  ChevronRight, Menu, X, LogIn, CreditCard
} from 'lucide-react'
import { useAuth } from '@/lib/contexts/AuthContext'
import AuthModal from './AuthModal'

interface AppShellProps {
  children: React.ReactNode
  title: string
  subtitle?: string
  actions?: React.ReactNode
}

// ── 3-Tier 네비게이션 구조 ──────────────────────────────────────────
const NAV_GROUPS = [
  {
    label: '대시보드',
    items: [
      { href: '/dashboard', label: '대시보드', icon: LayoutDashboard },
    ],
  },
  {
    label: '프로덕션',
    collapsible: true,
    items: [
      { href: '/writer',          label: '스크립트 작성',  icon: PenTool },
      { href: '/director',        label: '디렉터',         icon: Clapperboard },
      { href: '/storyboard',      label: '스토리보드',     icon: Layers },
      { href: '/audio',           label: '오디오 생성',    icon: Volume2 },
      { href: '/subtitle-editor', label: '자막 편집',      icon: FileText },
      { href: '/studio',          label: '스튜디오',       icon: Monitor },
      { href: '/production',      label: '배포',           icon: Rocket },
    ],
  },
  {
    label: '리소스',
    collapsible: true,
    items: [
      { href: '/gallery',         label: '템플릿 갤러리',  icon: Image },
      { href: '/upload',          label: '업로드',         icon: Upload },
      { href: '/presentation',    label: '프레젠테이션',   icon: Presentation },
      { href: '/schedule',        label: '일정 관리',      icon: CalendarDays },
    ],
  },
  // TODO: /settings, /settings/billing 페이지 구현 후 활성화
  // {
  //   label: '설정',
  //   collapsible: true,
  //   items: [
  //     { href: '/settings/billing', label: '빌링',  icon: CreditCard },
  //     { href: '/settings',         label: '설정',  icon: Settings },
  //   ],
  // },
]

export default function AppShell({ children, title, subtitle, actions }: AppShellProps) {
  const pathname = usePathname()
  const { user, isAuthenticated, logout } = useAuth()
  const [mobileOpen, setMobileOpen]       = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [collapsed, setCollapsed]         = useState<Record<string, boolean>>({})

  // 현재 경로에 해당하는 그룹은 기본 열림
  useEffect(() => {
    const init: Record<string, boolean> = {}
    NAV_GROUPS.forEach(g => {
      if (g.collapsible) {
        init[g.label] = g.items.some(item => pathname === item.href)
      }
    })
    setCollapsed(init)
  }, [pathname])

  const toggleGroup = useCallback((label: string) => {
    setCollapsed(prev => ({ ...prev, [label]: !prev[label] }))
  }, [])

  return (
    <div className="flex h-screen bg-[#0f1117] text-white overflow-hidden">

      {/* ── 좌측 사이드바 ── */}
      <aside className={`
        fixed inset-y-0 left-0 z-40 flex flex-col
        w-56 bg-[#0a0a0f] border-r border-white/[0.07]
        transition-transform duration-200
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
        md:relative md:translate-x-0
      `}>
        {/* 로고 */}
        <div className="h-16 px-4 flex items-center border-b border-white/[0.07] shrink-0">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-7 h-7 rounded-md bg-gradient-to-br from-purple-500 to-indigo-600
              flex items-center justify-center shadow-[0_4px_12px_-2px_rgba(168,85,247,0.5)]
              group-hover:scale-110 transition-transform">
              <Zap className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-xs font-black tracking-tighter"
              style={{
                background: 'linear-gradient(135deg,#a855f7,#6366f1)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
              }}>
              OMNIVIBE
            </span>
          </Link>
        </div>

        {/* 네비게이션 */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {NAV_GROUPS.map(group => (
            <div key={group.label} className="mb-1">
              {/* 그룹 헤더 */}
              {group.collapsible ? (
                <button
                  onClick={() => toggleGroup(group.label)}
                  className="w-full flex items-center justify-between px-2 py-1.5
                    text-[10px] font-bold uppercase tracking-[0.12em]
                    text-white/30 hover:text-white/50 transition-colors"
                >
                  {group.label}
                  <ChevronDown className={`w-3 h-3 transition-transform duration-150
                    ${collapsed[group.label] ? 'rotate-180' : ''}`} />
                </button>
              ) : (
                <div className="px-2 py-1.5 text-[10px] font-bold uppercase
                  tracking-[0.12em] text-white/30">
                  {group.label}
                </div>
              )}

              {/* 그룹 아이템 */}
              {(!group.collapsible || collapsed[group.label]) && (
                <div className="space-y-0.5">
                  {group.items.map(({ href, label, icon: Icon }) => {
                    const isActive = pathname === href
                    return (
                      <Link key={href} href={href}
                        onClick={() => setMobileOpen(false)}
                        className={`
                          flex items-center gap-2.5 px-2.5 py-1.5 rounded-md
                          text-[12px] font-medium transition-all
                          ${isActive
                            ? 'bg-purple-500/15 text-purple-300 border border-purple-500/20'
                            : 'text-white/50 hover:text-white/80 hover:bg-white/[0.05]'}
                        `}>
                        <Icon className="w-3.5 h-3.5 shrink-0" />
                        {label}
                        {isActive && <ChevronRight className="w-3 h-3 ml-auto opacity-60" />}
                      </Link>
                    )
                  })}
                </div>
              )}
            </div>
          ))}
        </nav>

        {/* 하단 유저 영역 */}
        <div className="p-3 border-t border-white/[0.07] shrink-0">
          {isAuthenticated ? (
            <div className="flex items-center gap-2 px-2 py-1.5 rounded-md bg-white/[0.04]">
              <div className="w-5 h-5 rounded-full bg-gradient-to-br from-purple-400 to-indigo-500
                flex items-center justify-center text-[9px] font-black shrink-0">
                {user?.name?.[0] ?? 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[11px] font-semibold text-white/80 truncate">{user?.name}</div>
                <div className="text-[9px] text-white/40 truncate">{user?.email}</div>
              </div>
              <button onClick={logout}
                className="text-[9px] text-white/30 hover:text-red-400 transition-colors font-mono">
                OUT
              </button>
            </div>
          ) : (
            <button onClick={() => setShowAuthModal(true)}
              className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded-md
                text-[11px] font-bold transition-all"
              style={{ background: 'linear-gradient(135deg,#9333ea,#6366f1)' }}>
              <LogIn className="w-3.5 h-3.5" />
              로그인
            </button>
          )}
        </div>
      </aside>

      {/* 모바일 오버레이 */}
      {mobileOpen && (
        <div className="fixed inset-0 z-30 bg-black/60 md:hidden"
          onClick={() => setMobileOpen(false)} />
      )}

      {/* ── 우측 메인 영역 ── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

        {/* 상단 헤더 */}
        <header className="h-16 px-5 flex items-center justify-between
          border-b border-white/[0.07] bg-[#0f1117]/80 backdrop-blur-xl shrink-0">
          {/* 모바일 햄버거 */}
          <button onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-1.5 rounded-md bg-white/5 hover:bg-white/10 transition-colors mr-3">
            {mobileOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>

          {/* 브레드크럼 */}
          <div className="flex items-center gap-2 text-[11px] font-mono text-white/40">
            <Link href="/" className="hover:text-white/60 transition-colors">Home</Link>
            <ChevronRight className="w-3 h-3" />
            <span className="text-purple-400 font-semibold">{title}</span>
          </div>

          {/* 페이지 액션 */}
          <div className="flex items-center gap-2 ml-auto">
            {actions}
          </div>
        </header>

        {/* 페이지 제목 */}
        <div className="px-6 pt-5 pb-3 border-b border-white/[0.05] shrink-0">
          <h1 className="text-xl font-black tracking-tight text-white">{title}</h1>
          {subtitle && <p className="text-sm text-white/50 mt-0.5">{subtitle}</p>}
        </div>

        {/* 컨텐츠 */}
        <main className="flex-1 overflow-y-auto px-6 py-5">
          {children}
        </main>
      </div>

      {showAuthModal && (
        <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
      )}
    </div>
  )
}
