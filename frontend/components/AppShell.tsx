'use client'

import { useState, useEffect, useCallback } from 'react'
import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { Zap, LogIn, Menu, X, ChevronRight } from 'lucide-react'
import { useAuth } from '@/lib/contexts/AuthContext'
import AuthModal from './AuthModal'

interface AppShellProps {
  children: React.ReactNode
  title: string
  subtitle?: string
  actions?: React.ReactNode
}

const NAV_ITEMS = [
  { href: '/studio', label: '스튜디오' },
  { href: '/dashboard', label: '대시보드' },
  { href: '/gallery', label: '템플릿' },
  { href: '/upload', label: '업로드' },
  { href: '/audio', label: '오디오' },
  { href: '/writer', label: '라이터' },
]

export default function AppShell({ children, title, subtitle, actions }: AppShellProps) {
  const pathname = usePathname()
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const { user, isAuthenticated, logout } = useAuth()

  const handleScroll = useCallback(() => setScrolled(window.scrollY > 40), [])
  useEffect(() => {
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [handleScroll])

  return (
    <div className="min-h-screen bg-[#050505] text-white overflow-x-hidden font-inter">
      {/* Ambient background glow */}
      <div className="fixed -top-24 -left-24 w-[700px] h-[700px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(ellipse, rgba(168,85,247,0.06) 0%, transparent 70%)' }} />
      <div className="fixed bottom-0 right-0 w-[500px] h-[500px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(ellipse, rgba(99,102,241,0.04) 0%, transparent 70%)' }} />

      {/* ── Sticky Nav ── */}
      <nav className={`fixed top-0 inset-x-0 h-16 z-50 px-6 md:px-10 flex items-center justify-between transition-all duration-300 ${
        scrolled ? 'bg-[#050505]/90 backdrop-blur-xl border-b border-white/[0.06]' : ''
      }`}>
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-[0_4px_16px_-4px_rgba(168,85,247,0.5)] group-hover:scale-110 transition-transform duration-200">
            <Zap className="w-4 h-4 text-white fill-white/20" />
          </div>
          <span className="text-sm font-black tracking-tighter" style={{
            background: 'linear-gradient(135deg, #a855f7, #6366f1)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>OMNIVIBE</span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_ITEMS.map(({ href, label }) => {
            const isActive = pathname === href
            return (
              <Link
                key={href}
                href={href}
                className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold uppercase tracking-widest transition-all ${
                  isActive
                    ? 'bg-purple-500/15 text-purple-300 border border-purple-500/25'
                    : 'text-white/40 hover:text-white/70 hover:bg-white/5'
                }`}
              >
                {label}
              </Link>
            )
          })}
        </div>

        {/* Auth + Mobile Toggle */}
        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <>
              <div className="hidden md:flex items-center gap-2 px-4 py-1.5 bg-white/[0.03] border border-white/[0.06] rounded-lg">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] font-black text-white/50 uppercase tracking-widest">{user?.name}</span>
              </div>
              <button onClick={logout}
                className="hidden md:block px-4 py-1.5 bg-white/5 hover:bg-red-500/15 border border-white/10 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all">
                Logout
              </button>
            </>
          ) : (
            <button
              onClick={() => setShowAuthModal(true)}
              className="hidden md:flex items-center gap-1.5 px-5 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-purple-500/20"
              style={{ background: 'linear-gradient(135deg, #9333ea, #6366f1)' }}
            >
              <LogIn className="w-3.5 h-3.5" />
              로그인
            </button>
          )}

          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
          >
            {mobileOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="fixed inset-x-0 top-16 z-40 bg-[#0a0a0f]/95 backdrop-blur-xl border-b border-white/[0.06] p-4 md:hidden">
          <div className="flex flex-col gap-1">
            {NAV_ITEMS.map(({ href, label }) => (
              <Link key={href} href={href}
                onClick={() => setMobileOpen(false)}
                className={`px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                  pathname === href
                    ? 'bg-purple-500/15 text-purple-300'
                    : 'text-white/50 hover:text-white/80 hover:bg-white/5'
                }`}>
                {label}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* ── Page Header ── */}
      <header className="relative pt-24 pb-8 px-6 md:px-10 border-b border-white/[0.05]"
        style={{ background: 'linear-gradient(to bottom, rgba(168,85,247,0.04) 0%, transparent 100%)' }}>
        <div className="max-w-7xl mx-auto">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-[11px] text-white/30 mb-3 font-mono uppercase tracking-widest">
            <Link href="/" className="hover:text-white/60 transition-colors">Home</Link>
            <ChevronRight className="w-3 h-3" />
            <span className="text-purple-400">{title}</span>
          </div>

          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-black tracking-tight text-white">{title}</h1>
              {subtitle && <p className="text-sm text-white/40 mt-1">{subtitle}</p>}
            </div>
            {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
          </div>
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="max-w-7xl mx-auto px-6 md:px-10 py-8">
        {children}
      </main>

      {showAuthModal && <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />}
    </div>
  )
}
