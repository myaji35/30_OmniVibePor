"use client";

import { useEffect, useState, useRef, useCallback, useMemo } from "react";
import {
  LogIn,
  Zap,
  MonitorPlay,
  Calendar,
  PenTool,
  Mic2,
  Layout,
  BookOpen,
  Activity,
  ArrowRight,
  Database,
  Share2,
  Sparkles,
  ShieldCheck,
  Cpu,
  LayoutGrid,
  Check,
  Play,
  Film,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "../lib/contexts/AuthContext";
import AuthModal from "../components/AuthModal";

// ── Scroll Fade-In Hook (0007 패턴) ──────────────────────────────────────────
function useScrollReveal<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.style.animationPlayState = "running";
          observer.unobserve(el);
        }
      },
      { threshold: 0.12 }
    );
    el.style.animationPlayState = "paused";
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return ref;
}

function FadeIn({ children, delay = 0, className = "" }: { children: React.ReactNode; delay?: number; className?: string }) {
  const ref = useScrollReveal<HTMLDivElement>();
  return (
    <div ref={ref} className={`animate-fade-in-up ${className}`} style={{ animationDelay: `${delay}s`, animationPlayState: "paused" }}>
      {children}
    </div>
  );
}

// ── CountUp 숫자 애니메이션 ──────────────────────────────────────────────────
function CountUp({ target, suffix = "", visible }: { target: number; suffix?: string; visible: boolean }) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!visible) return;
    let start: number | null = null;
    const duration = 1200;
    const step = (ts: number) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      setValue(Math.floor(ease * target));
      if (progress < 1) requestAnimationFrame(step);
      else setValue(target);
    };
    requestAnimationFrame(step);
  }, [visible, target]);
  return <>{value.toLocaleString()}{suffix}</>;
}

// ── Animated Pipeline Bar (히어로 우측 목업용) ──────────────────────────────
function PipelineBar({ steps, visible }: { steps: { label: string; pct: number; color: string; active?: boolean }[]; visible: boolean }) {
  return (
    <div className="space-y-2.5">
      {steps.map((s, i) => (
        <div key={s.label} className="flex items-center gap-3">
          <span className="text-sm text-slate-400 w-16 text-right shrink-0 font-mono">{s.label}</span>
          <div className="flex-1 h-2 bg-slate-700/60 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-1000 relative overflow-hidden"
              style={{
                width: visible ? `${s.pct}%` : "0%",
                backgroundColor: s.color,
                transitionDelay: `${i * 0.18}s`,
              }}
            >
              {/* 흐르는 하이라이트 */}
              {s.active && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-shimmer" />
              )}
            </div>
          </div>
          <span className="text-sm font-bold w-8 shrink-0" style={{ color: s.color }}>{s.pct}%</span>
        </div>
      ))}
    </div>
  );
}

// ── 히어로 미니 플레이어 (Remotion 샘플 느낌) ────────────────────────────────
// 갤러리 실 사례에서 youtubeId 있는 인기 TOP 항목 + Remotion 공식 데모 혼합
const HERO_SAMPLES = [
  {
    tag: "Trailer",
    title: "Remotion 공식 트레일러",
    author: "Jonny Burger",
    youtubeId: "gwlDorikqgY",
  },
  {
    tag: "Shorts",
    title: "Short Video Maker",
    author: "David Gyori",
    youtubeId: "jzsQpn-AciM",
  },
  {
    tag: "Mockup",
    title: "Mockoops — 스크린 애니메이션",
    author: "Mohit",
    youtubeId: "SSNmU3FXW4s",
  },
];

function MiniPlayer({ visible }: { visible: boolean }) {
  const [active, setActive] = useState(0);
  const [progress, setProgress] = useState(0);
  const INTERVAL_MS = 8000; // 8초마다 자동 넘김

  // 자동 캐러셀 + 진행 바
  useEffect(() => {
    if (!visible) return;
    setProgress(0);
    const startTime = Date.now();
    const rafId = { current: 0 };

    const tick = () => {
      const elapsed = Date.now() - startTime;
      const pct = Math.min((elapsed / INTERVAL_MS) * 100, 100);
      setProgress(pct);
      if (pct < 100) {
        rafId.current = requestAnimationFrame(tick);
      } else {
        setActive((a) => (a + 1) % HERO_SAMPLES.length);
      }
    };
    rafId.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId.current);
  }, [visible, active]);

  if (!visible) return null;

  const sample = HERO_SAMPLES[active];
  // autoplay=1 mute=1 controls=0 loop=1
  const embedUrl = `https://www.youtube.com/embed/${sample.youtubeId}?autoplay=1&mute=1&controls=0&loop=1&playlist=${sample.youtubeId}&modestbranding=1&rel=0&showinfo=0`;

  return (
    <div className="rounded-xl overflow-hidden"
      style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.08)" }}>

      {/* 탭 + 진행 바 */}
      <div className="flex gap-1 p-2 border-b border-white/[0.06]">
        {HERO_SAMPLES.map((s, i) => (
          <button key={i} onClick={() => setActive(i)}
            className="flex-1 text-xs font-bold py-1.5 rounded-lg transition-all relative overflow-hidden"
            style={{
              color: active === i ? "#fff" : "#64748b",
              background: active === i ? "rgba(99,102,241,0.25)" : "transparent",
              border: active === i ? "1px solid rgba(99,102,241,0.4)" : "1px solid transparent",
            }}>
            {/* 진행 바 (활성 탭만) */}
            {active === i && (
              <div className="absolute bottom-0 left-0 h-0.5 rounded-full"
                style={{ width: `${progress}%`, background: "linear-gradient(90deg,#a78bfa,#6366f1)", transition: "width 0.1s linear" }} />
            )}
            {s.tag}
          </button>
        ))}
      </div>

      {/* YouTube iframe */}
      <div className="relative aspect-video bg-black">
        <iframe
          key={sample.youtubeId}
          src={embedUrl}
          className="w-full h-full"
          allow="autoplay; encrypted-media"
          allowFullScreen
          style={{ border: "none" }}
        />
        {/* 상단 뱃지 */}
        <div className="absolute top-2 left-2 flex items-center gap-1.5 px-2 py-0.5 rounded-full pointer-events-none"
          style={{ background: "rgba(0,0,0,0.65)", backdropFilter: "blur(8px)", border: "1px solid rgba(255,255,255,0.15)" }}>
          <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
          <span className="text-xs font-bold text-white">Remotion</span>
        </div>
        {/* 하단 정보 */}
        <div className="absolute bottom-0 left-0 right-0 p-2 pointer-events-none"
          style={{ background: "linear-gradient(to top, rgba(0,0,0,0.75), transparent)" }}>
          <p className="text-sm font-bold text-white">{sample.title}</p>
          <p className="text-xs text-white/50">by {sample.author}</p>
        </div>
      </div>
    </div>
  );
}

// ── Studio Mockup (히어로 우측) ──────────────────────────────────────────────
function StudioMockup() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { setVisible(true); observer.unobserve(el); }
    }, { threshold: 0.2 });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // "생성 중" 작업 진행률 실시간 업데이트
  useEffect(() => {
    if (!visible) return;
    const id = setInterval(() => setTick((t) => t + 1), 800);
    return () => clearInterval(id);
  }, [visible]);

  const pipelineSteps = useMemo(() => [
    { label: "PDF 분석", pct: 100, color: "#a855f7", active: false },
    { label: "스크립트", pct: 100, color: "#8b5cf6", active: false },
    { label: "TTS 생성", pct: Math.min(100, 88 + (tick % 3)), color: "#6366f1", active: true },
    { label: "영상 렌더", pct: Math.min(98, 64 + (tick % 5) * 2), color: "#3b82f6", active: true },
  ], [tick]);

  return (
    <div ref={ref} className="relative">
      {/* 강한 외곽 글로우 — 배경과 확실히 분리 */}
      <div className="absolute -inset-4 rounded-3xl pointer-events-none"
        style={{ background: "radial-gradient(ellipse at center, rgba(99,102,241,0.35) 0%, rgba(168,85,247,0.15) 50%, transparent 75%)", filter: "blur(20px)" }} />
      <div className="absolute -inset-1 rounded-2xl pointer-events-none border border-indigo-500/30"
        style={{ boxShadow: "0 0 40px rgba(99,102,241,0.25), 0 0 80px rgba(168,85,247,0.1)" }} />

      {/* Browser Chrome — 밝은 딥 네이비로 배경과 대비 */}
      <div className="relative rounded-2xl overflow-hidden"
        style={{ background: "linear-gradient(160deg, #1e2035 0%, #161829 60%, #111327 100%)", border: "1px solid rgba(255,255,255,0.12)" }}>

        {/* 내부 상단 하이라이트 */}
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/25 to-transparent" />

        {/* Title bar */}
        <div className="px-4 py-3 flex items-center gap-3 border-b border-white/[0.07]"
          style={{ background: "rgba(255,255,255,0.03)" }}>
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/70 shadow-[0_0_6px_rgba(239,68,68,0.5)]" />
            <div className="w-3 h-3 rounded-full bg-amber-400/70 shadow-[0_0_6px_rgba(251,191,36,0.5)]" />
            <div className="w-3 h-3 rounded-full bg-emerald-400/70 shadow-[0_0_6px_rgba(52,211,153,0.5)]" />
          </div>
          <div className="flex-1 bg-white/[0.07] rounded-md h-5 text-sm text-slate-400 flex items-center px-3 font-mono">
            omnivibepro.com/studio
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]" />
            <span className="text-xs text-emerald-400 font-bold font-mono">LIVE</span>
          </div>
        </div>

        {/* Dashboard content */}
        <div className="p-4 space-y-3">
          {/* KPI row */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: "생성된 영상", value: 1240, suffix: "", color: "#a78bfa", glow: "rgba(167,139,250,0.2)" },
              { label: "Zero-Fault율", value: 99, suffix: "%", color: "#34d399", glow: "rgba(52,211,153,0.2)" },
              { label: "평균 생성", value: 4, suffix: "분", color: "#60a5fa", glow: "rgba(96,165,250,0.2)" },
            ].map(({ label, value, suffix, color, glow }) => (
              <div key={label} className="rounded-xl p-3 relative overflow-hidden"
                style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", boxShadow: `inset 0 1px 0 rgba(255,255,255,0.06)` }}>
                <div className="absolute inset-0 rounded-xl pointer-events-none" style={{ background: `radial-gradient(ellipse at top left, ${glow} 0%, transparent 70%)` }} />
                <p className="text-xs text-slate-400 mb-1 relative">{label}</p>
                <p className="text-xl font-black font-mono relative" style={{ color }}>
                  <CountUp target={value} suffix={suffix} visible={visible} />
                </p>
              </div>
            ))}
          </div>

          {/* Pipeline progress */}
          <div className="rounded-xl p-4"
            style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}>
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-black text-slate-300 uppercase tracking-widest">AI Pipeline</p>
              <span className="text-xs font-bold px-2.5 py-1 rounded-full animate-pulse"
                style={{ color: "#a78bfa", background: "rgba(167,139,250,0.15)", border: "1px solid rgba(167,139,250,0.3)" }}>
                ⚡ 처리 중
              </span>
            </div>
            <PipelineBar steps={pipelineSteps} visible={visible} />
          </div>

          {/* Recent jobs */}
          <div className="rounded-xl p-3"
            style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}>
            <p className="text-xs text-slate-400 uppercase tracking-widest mb-2.5 font-black">최근 작업</p>
            <div className="space-y-2">
              {[
                { name: "Q1_전략_브리핑.pdf", status: "완료", statusColor: "#34d399", bg: "rgba(52,211,153,0.1)", dot: "#34d399" },
                { name: "제품소개_2026.pdf", status: "생성 중", statusColor: "#a78bfa", bg: "rgba(167,139,250,0.1)", dot: "#a78bfa", pulse: true },
                { name: "채용공고_개발자.pdf", status: "대기", statusColor: "#64748b", bg: "rgba(100,116,139,0.1)", dot: "#64748b" },
              ].map(({ name, status, statusColor, bg, dot, pulse }) => (
                <div key={name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: dot, boxShadow: pulse ? `0 0 6px ${dot}` : "none" }} />
                    <span className="text-slate-300 font-mono text-sm">{name}</span>
                  </div>
                  <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{ color: statusColor, background: bg }}>
                    {status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 하단 — 미니 Remotion 샘플 플레이어 */}
          <MiniPlayer visible={visible} />
        </div>
      </div>
    </div>
  );
}

// ── API Status Interface ─────────────────────────────────────────────────────
interface APIStatus {
  status: string;
  service: string;
  version: string;
  message: string;
  features: {
    voice_cloning: string;
    zero_fault_audio: string;
    performance_tracking: string;
    thumbnail_learning: string;
  };
}

// ════════════════════════════════════════════════════════════════════════════
// Main Page
// ════════════════════════════════════════════════════════════════════════════
export default function Home() {
  const [apiStatus, setApiStatus] = useState<APIStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, isAuthenticated, logout } = useAuth();

  const handleScroll = useCallback(() => setScrolled(window.scrollY > 40), []);

  useEffect(() => {
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  useEffect(() => {
    fetch("/api/backend-status")
      .then((res) => res.json())
      .then((data) => { setApiStatus(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-[#0f1117] text-white selection:bg-brand-primary-500/30 overflow-x-hidden font-inter">
      {/* Ambient Background */}
      <div className="fixed -top-24 -left-24 w-[800px] h-[800px] bg-brand-primary-500/8 rounded-full blur-[150px] pointer-events-none" />
      <div className="fixed top-1/2 -right-24 w-[600px] h-[600px] bg-brand-secondary-500/5 rounded-full blur-[120px] pointer-events-none" />

      {/* ── Sticky Nav (모바일 반응형) ── */}
      <nav className={`fixed top-0 inset-x-0 z-50 px-5 md:px-10 transition-all duration-300 ${scrolled ? "bg-[#0f1117]/90 backdrop-blur-xl border-b border-white/5" : ""}`}>
        <div className="h-16 md:h-20 flex items-center justify-between">
          <a href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-gradient-to-br from-brand-primary-500 to-brand-secondary-600 flex items-center justify-center shadow-[0_8px_24px_-4px_rgba(168,85,247,0.5)] group-hover:scale-110 transition-all duration-300">
              <Zap className="w-4 h-4 md:w-5 md:h-5 text-white fill-white/20" />
            </div>
            <div className="flex flex-col">
              <h1 className="text-sm md:text-base font-black font-outfit premium-gradient-text tracking-tighter leading-none">OMNIVIBE PRO</h1>
            </div>
          </a>

          {/* 데스크톱 네비 */}
          <div className="hidden lg:flex items-center gap-6 text-sm font-semibold text-white/60">
            <a href="#features" className="hover:text-white/90 transition-colors">기능</a>
            <a href="/strategy" className="hover:text-white/90 transition-colors">전략 수립</a>
            <a href="/concept" className="hover:text-white/90 transition-colors">컨셉 기획</a>
            <a href="/produce" className="hover:text-white/90 transition-colors">콘텐츠 생산</a>
            <a href="/gallery" className="hover:text-white/90 transition-colors">템플릿</a>
            <a href="/pricing" className="hover:text-white/90 transition-colors">가격</a>
          </div>

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                <span className="hidden md:inline text-sm text-white/50">{user?.name}</span>
                <a href="/dashboard" className="px-4 py-2 bg-brand-primary-600 hover:bg-brand-primary-500 rounded-lg text-sm font-bold text-white transition-all">
                  대시보드
                </a>
              </>
            ) : (
              <button
                onClick={() => setShowAuthModal(true)}
                className="hidden md:flex items-center gap-2 px-5 py-2.5 bg-brand-primary-600 hover:bg-brand-primary-500 rounded-xl text-sm font-bold text-white transition-all shadow-lg shadow-purple-500/20 active:scale-95"
              >
                <LogIn className="w-4 h-4" />
                시작하기
              </button>
            )}

            {/* 모바일 햄버거 */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden flex flex-col gap-1.5 p-2"
              aria-label="메뉴 열기"
            >
              <span className={`w-5 h-0.5 bg-white/60 rounded transition-all ${mobileMenuOpen ? 'rotate-45 translate-y-2' : ''}`} />
              <span className={`w-5 h-0.5 bg-white/60 rounded transition-all ${mobileMenuOpen ? 'opacity-0' : ''}`} />
              <span className={`w-5 h-0.5 bg-white/60 rounded transition-all ${mobileMenuOpen ? '-rotate-45 -translate-y-2' : ''}`} />
            </button>
          </div>
        </div>

        {/* 모바일 메뉴 */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-white/5 bg-[#0f1117]/95 backdrop-blur-xl pb-6 pt-4 px-2">
            <div className="flex flex-col gap-1">
              {[
                { href: '/strategy', label: '전략 수립', icon: '📊' },
                { href: '/concept', label: '컨셉 기획', icon: '💡' },
                { href: '/produce', label: '콘텐츠 생산', icon: '🎬' },
                { href: '/publish', label: '멀티채널 배포', icon: '📡' },
                { href: '/gallery', label: '템플릿 갤러리', icon: '🎨' },
                { href: '/pricing', label: '가격', icon: '💰' },
                { href: '/dashboard', label: '대시보드', icon: '📋' },
              ].map(item => (
                <a key={item.href} href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold text-white/70 hover:text-white hover:bg-white/[0.05] transition-all">
                  <span>{item.icon}</span> {item.label}
                </a>
              ))}
            </div>
            {!isAuthenticated && (
              <button
                onClick={() => { setShowAuthModal(true); setMobileMenuOpen(false); }}
                className="w-full mt-4 px-5 py-3 bg-brand-primary-600 hover:bg-brand-primary-500 rounded-xl text-sm font-bold text-white transition-all"
              >
                무료로 시작하기
              </button>
            )}
          </div>
        )}
      </nav>

      {/* ════════════════════════════════════════════════
          Hero — Option A: 좌측 카피 + 우측 Product Mockup
      ════════════════════════════════════════════════ */}
      <section className="relative flex items-start pt-20 pb-10 overflow-hidden">
        {/* 좌측 그라디언트 페이드 */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#0f1117]/80 via-transparent to-transparent pointer-events-none" />

        <div className="container mx-auto px-10 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">

            {/* 좌측 — 카피 */}
            <div className="max-w-xl">
              {/* 뱃지 */}
              <div
                className="animate-fade-in inline-flex items-center gap-2.5 px-4 py-1.5 border rounded-full mb-8"
                style={{ borderColor: "rgba(168,85,247,0.35)", background: "rgba(168,85,247,0.06)", animationDelay: "0.1s" }}
              >
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-primary-400 opacity-75" />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-brand-primary-400" />
                </span>
                <span className="text-sm font-black text-brand-primary-400 uppercase tracking-wide">AI Video Synthesis Engine v2.0</span>
              </div>

              {/* 헤드라인 */}
              <h2
                className="animate-fade-in text-5xl md:text-7xl font-black font-outfit tracking-tighter leading-[0.95] mb-8"
                style={{ animationDelay: "0.2s" }}
              >
                <span className="text-white">영상 제작의</span>
                <br />
                <span className="premium-gradient-text">모든 것을 자동화.</span>
              </h2>

              {/* 서브카피 */}
              <p className="animate-fade-in text-lg text-gray-300 leading-relaxed mb-10" style={{ animationDelay: "0.32s" }}>
                PDF 하나면 충분합니다. AI가 스크립트를 쓰고,<br />
                <span className="text-white/80">목소리를 복제하고, 영상을 완성합니다.</span>
              </p>

              {/* CTA 버튼 — 전략부터 시작 */}
              <div className="animate-fade-in flex flex-col sm:flex-row gap-3 mb-10" style={{ animationDelay: "0.42s" }}>
                <a
                  href="/strategy"
                  className="flex items-center justify-center gap-2 px-7 py-4 rounded-xl text-base font-bold transition-all group active:scale-95"
                  style={{ background: "linear-gradient(135deg, #a855f7, #6366f1)", boxShadow: "0 0 24px rgba(168,85,247,0.35)" }}
                >
                  <Sparkles className="w-5 h-5" />
                  AI 전략부터 시작하기
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </a>
                <a
                  href="/gallery"
                  className="flex items-center justify-center gap-2 px-7 py-4 border border-white/10 bg-white/5 hover:bg-white/10 rounded-xl text-base font-bold transition-all"
                >
                  <LayoutGrid className="w-5 h-5" />
                  템플릿 갤러리
                </a>
              </div>

              {/* 신뢰 텍스트 */}
              <div className="animate-fade-in flex flex-wrap gap-5 text-xs text-gray-400" style={{ animationDelay: "0.52s" }}>
                {["PDF 업로드만으로 시작", "99% Zero-Fault 오디오", "20개 영상 템플릿 무료"].map((text) => (
                  <span key={text} className="flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-brand-primary-500" />
                    {text}
                  </span>
                ))}
              </div>

              {/* 플랫폼 지원 뱃지 */}
              <div className="animate-fade-in flex items-center gap-3 mt-10" style={{ animationDelay: "0.62s" }}>
                <span className="text-xs text-gray-400 uppercase tracking-widest">지원 플랫폼</span>
                <div className="flex gap-2">
                  {[
                    { label: "YouTube", color: "bg-red-500/20 text-red-400 border-red-500/20" },
                    { label: "Instagram", color: "bg-pink-500/20 text-pink-400 border-pink-500/20" },
                    { label: "TikTok", color: "bg-white/10 text-white/60 border-white/10" },
                  ].map(({ label, color }) => (
                    <span key={label} className={`text-xs font-bold px-2.5 py-1 rounded-full border ${color}`}>{label}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* 우측 — 스튜디오 목업 */}
            <div className="animate-fade-in hidden lg:block" style={{ animationDelay: "0.3s" }}>
              <StudioMockup />
            </div>
          </div>
        </div>
      </section>

      {/* ── 플랫폼 신뢰 스트립 ── */}
      <div className="border-y border-white/5 bg-white/[0.01] py-6">
        <div className="container mx-auto px-10">
          <FadeIn>
            <div className="flex items-center justify-center gap-10 flex-wrap">
              <span className="text-sm text-gray-400 uppercase tracking-widest">AI 파이프라인</span>
              {["ElevenLabs TTS", "OpenAI Whisper", "GPT-4 Writer", "Remotion Render", "Neo4j GraphRAG"].map((tech, i) => (
                <FadeIn key={tech} delay={i * 0.06}>
                  <span className="text-xs text-gray-400 font-mono">{tech}</span>
                </FadeIn>
              ))}
            </div>
          </FadeIn>
        </div>
      </div>

      {/* ── Pipeline Visualization ── */}
      <section className="py-16 relative z-10">
        <div className="container mx-auto px-5 md:px-10">
          <FadeIn className="mb-10">
            <h3 className="text-2xl md:text-3xl font-bold text-white text-center mb-3">AI가 전략부터 배포까지</h3>
            <p className="text-base text-gray-400 text-center">4단계 자동화 파이프라인</p>
          </FadeIn>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            {[
              { step: '01', label: '전략 수립', desc: 'AI가 채널별 전략과 주간 캘린더를 자동 생성', href: '/strategy', color: '#6366F1' },
              { step: '02', label: '컨셉 기획', desc: '스크립트 자동 생성 + 스토리보드 시각화', href: '/concept', color: '#F59E0B' },
              { step: '03', label: '콘텐츠 생산', desc: '영상 · 프레젠테이션 · 나레이션 자동 제작', href: '/produce', color: '#00FF88' },
              { step: '04', label: '멀티채널 배포', desc: '예약 발행 + 성과 추적 → AI 학습', href: '/publish', color: '#22C55E' },
            ].map((item, i) => (
              <FadeIn key={item.step} delay={i * 0.1}>
                <a href={item.href} className="group block p-5 md:p-6 rounded-2xl bg-white/[0.02] border border-white/[0.06] hover:border-white/[0.15] hover:bg-white/[0.04] transition-all text-center">
                  <div className="text-3xl md:text-4xl font-black mb-3" style={{ color: item.color }}>{item.step}</div>
                  <h4 className="text-base font-bold text-white mb-2">{item.label}</h4>
                  <p className="text-xs text-gray-400 leading-relaxed">{item.desc}</p>
                </a>
              </FadeIn>
            ))}
          </div>
          {/* 화살표 연결선 (데스크톱만) */}
          <div className="hidden md:flex justify-center mt-6 gap-2">
            {['전략', '→', '컨셉', '→', '생산', '→', '배포', '→', 'GraphRAG 피드백 ↩'].map((t, i) => (
              <span key={i} className={`text-sm ${t.includes('→') || t.includes('↩') ? 'text-white/20' : 'text-white/50 font-semibold'}`}>{t}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ── Social Proof ── */}
      <section className="py-12 border-y border-white/5 bg-white/[0.01]">
        <div className="container mx-auto px-5 md:px-10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            {[
              { value: '38,888', label: '학습된 약관', suffix: '개' },
              { value: '99', label: 'Zero-Fault 정확도', suffix: '%' },
              { value: '8', label: '한국어 AI 음성', suffix: '종' },
              { value: '22', label: '서비스 페이지', suffix: '개' },
            ].map((stat, i) => (
              <FadeIn key={stat.label} delay={i * 0.08}>
                <div>
                  <div className="text-3xl md:text-4xl font-black text-white mb-1">{stat.value}<span className="text-lg text-white/40">{stat.suffix}</span></div>
                  <div className="text-sm text-gray-400">{stat.label}</div>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" className="py-20 relative z-10">
        <div className="container mx-auto px-5 md:px-10">
          <FadeIn className="mb-12">
            <h3 className="text-2xl md:text-3xl font-bold text-white mb-2">핵심 기능</h3>
            <p className="text-base text-gray-400">영상 제작부터 멀티채널 배포까지 모든 도구</p>
          </FadeIn>

          {/* 카테고리: 전략 & 기획 */}
          <div className="mb-8">
            <h4 className="text-xs font-bold text-brand-primary-400 uppercase tracking-wider mb-4">전략 & 기획</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { href: "/strategy", title: "전략 수립", desc: "AI 채널별 전략 + 주간 캘린더", icon: Activity, color: "#6366F1" },
                { href: "/concept", title: "컨셉 기획", desc: "스크립트 → 스토리보드 자동화", icon: Sparkles, color: "#F59E0B" },
                { href: "/writer", title: "AI 라이터", desc: "GraphRAG 기반 스크립트 생성", icon: PenTool, color: "#8B5CF6" },
                { href: "/schedule", title: "스케줄러", desc: "콘텐츠 일정 관리 + CSV", icon: Calendar, color: "#06B6D4" },
              ].map((node, i) => (
                <FadeIn key={node.href} delay={i * 0.06}>
                  <a href={node.href} className="group flex items-start gap-4 p-5 bg-white/[0.02] border border-white/[0.06] rounded-2xl hover:bg-white/[0.05] hover:border-white/[0.12] transition-all">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: `${node.color}15`, border: `1px solid ${node.color}30` }}>
                      <node.icon className="w-5 h-5" style={{ color: node.color }} />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-white mb-1">{node.title}</h3>
                      <p className="text-sm text-gray-400">{node.desc}</p>
                    </div>
                  </a>
                </FadeIn>
              ))}
            </div>
          </div>

          {/* 카테고리: 콘텐츠 제작 */}
          <div className="mb-8">
            <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-4">콘텐츠 제작</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { href: "/produce", title: "콘텐츠 생산", desc: "영상 + 프레젠테이션 + 나레이션", icon: Film, color: "#22C55E" },
                { href: "/audio", title: "Zero-Fault 오디오", desc: "TTS + STT 검증 루프 99%", icon: Mic2, color: "#3B82F6" },
                { href: "/production", title: "영상 디렉터", desc: "비주얼 씬 + Remotion 렌더", icon: Layout, color: "#EF4444" },
                { href: "/presentation", title: "덱 엔진", desc: "PDF → 영상 자동 변환", icon: BookOpen, color: "#F97316" },
              ].map((node, i) => (
                <FadeIn key={node.href} delay={i * 0.06}>
                  <a href={node.href} className="group flex items-start gap-4 p-5 bg-white/[0.02] border border-white/[0.06] rounded-2xl hover:bg-white/[0.05] hover:border-white/[0.12] transition-all">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: `${node.color}15`, border: `1px solid ${node.color}30` }}>
                      <node.icon className="w-5 h-5" style={{ color: node.color }} />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-white mb-1">{node.title}</h3>
                      <p className="text-sm text-gray-400">{node.desc}</p>
                    </div>
                  </a>
                </FadeIn>
              ))}
            </div>
          </div>

          {/* 카테고리: 관리 & 배포 */}
          <div>
            <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-4">관리 & 배포</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { href: "/publish", title: "멀티채널 배포", desc: "예약 발행 + 성과 → GraphRAG", icon: Share2, color: "#06B6D4" },
                { href: "/gallery", title: "템플릿 갤러리", desc: "영상 템플릿 컬렉션", icon: LayoutGrid, color: "#10B981" },
                { href: "/studio", title: "통합 스튜디오", desc: "전체 워크플로우 허브", icon: MonitorPlay, color: "#A855F7" },
                { href: "/dashboard", title: "대시보드", desc: "KPI + 캠페인 현황", icon: Activity, color: "#60A5FA" },
              ].map((node, i) => (
                <FadeIn key={node.href} delay={i * 0.06}>
                  <a href={node.href} className="group flex items-start gap-4 p-5 bg-white/[0.02] border border-white/[0.06] rounded-2xl hover:bg-white/[0.05] hover:border-white/[0.12] transition-all">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: `${node.color}15`, border: `1px solid ${node.color}30` }}>
                      <node.icon className="w-5 h-5" style={{ color: node.color }} />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-white mb-1">{node.title}</h3>
                      <p className="text-sm text-gray-400">{node.desc}</p>
                    </div>
                  </a>
                </FadeIn>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── System Architecture ── */}
      <section className="py-16 relative z-10 border-t border-white/5">
        <div className="container mx-auto px-10">
          <FadeIn className="mb-12">
            <div className="flex items-center gap-6">
              <div className="w-10 h-[2px] bg-brand-accent-500" />
              <h3 className="text-sm font-black text-gray-500 uppercase tracking-wider">System Architecture</h3>
            </div>
          </FadeIn>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { href: "http://localhost:8000/redoc", title: "레지스트리", desc: "API 인벤토리", icon: Database },
              { href: "http://localhost:7474", title: "GraphRAG", desc: "지식 그래프 브라우저", icon: Share2 },
              { href: "#", title: "컴퓨팅 코어", desc: "GPU 렌더링 클러스터", icon: Cpu },
            ].map((sys, i) => (
              <FadeIn key={sys.title} delay={i * 0.1}>
                <a href={sys.href} target="_blank" className="p-6 bg-black/40 border border-white/5 rounded-[1.5rem] flex items-center gap-6 hover:bg-black/60 hover:border-white/10 transition-all">
                  <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center">
                    <sys.icon className="w-5 h-5 text-gray-400" />
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-white">{sys.title}</h4>
                    <span className="text-sm text-gray-400">{sys.desc}</span>
                  </div>
                </a>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* Auth Modal */}
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />

      {/* Footer */}
      <footer className="py-16 border-t border-white/5 bg-black/20 relative z-10">
        <div className="container mx-auto px-10 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="flex items-center gap-4 opacity-50">
            <Zap className="w-4 h-4" />
            <span className="text-sm font-semibold text-white/50">OmniVibe Pro · 2026</span>
          </div>
          <div className="flex items-center gap-8 text-sm text-white/30">
            <a href="#" className="hover:text-white/60 transition-colors">개인정보처리방침</a>
            <a href="#" className="hover:text-white/60 transition-colors">이용약관</a>
            <a href="/pricing" className="hover:text-white/60 transition-colors">가격</a>
          </div>
        </div>
      </footer>
    </main>
  );
}
