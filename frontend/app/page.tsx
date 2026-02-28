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
          <span className="text-[10px] text-slate-400 w-16 text-right shrink-0 font-mono">{s.label}</span>
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
          <span className="text-[10px] font-bold w-8 shrink-0" style={{ color: s.color }}>{s.pct}%</span>
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
            className="flex-1 text-[9px] font-bold py-1.5 rounded-lg transition-all relative overflow-hidden"
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
          <span className="text-[9px] font-bold text-white">Remotion</span>
        </div>
        {/* 하단 정보 */}
        <div className="absolute bottom-0 left-0 right-0 p-2 pointer-events-none"
          style={{ background: "linear-gradient(to top, rgba(0,0,0,0.75), transparent)" }}>
          <p className="text-[10px] font-bold text-white">{sample.title}</p>
          <p className="text-[9px] text-white/50">by {sample.author}</p>
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
          <div className="flex-1 bg-white/[0.07] rounded-md h-5 text-[10px] text-slate-400 flex items-center px-3 font-mono">
            omnivibepro.com/studio
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]" />
            <span className="text-[9px] text-emerald-400 font-bold font-mono">LIVE</span>
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
                <p className="text-[9px] text-slate-400 mb-1 relative">{label}</p>
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
              <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest">AI Pipeline</p>
              <span className="text-[9px] font-bold px-2.5 py-1 rounded-full animate-pulse"
                style={{ color: "#a78bfa", background: "rgba(167,139,250,0.15)", border: "1px solid rgba(167,139,250,0.3)" }}>
                ⚡ 처리 중
              </span>
            </div>
            <PipelineBar steps={pipelineSteps} visible={visible} />
          </div>

          {/* Recent jobs */}
          <div className="rounded-xl p-3"
            style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}>
            <p className="text-[9px] text-slate-400 uppercase tracking-widest mb-2.5 font-black">최근 작업</p>
            <div className="space-y-2">
              {[
                { name: "Q1_전략_브리핑.pdf", status: "완료", statusColor: "#34d399", bg: "rgba(52,211,153,0.1)", dot: "#34d399" },
                { name: "제품소개_2026.pdf", status: "생성 중", statusColor: "#a78bfa", bg: "rgba(167,139,250,0.1)", dot: "#a78bfa", pulse: true },
                { name: "채용공고_개발자.pdf", status: "대기", statusColor: "#64748b", bg: "rgba(100,116,139,0.1)", dot: "#64748b" },
              ].map(({ name, status, statusColor, bg, dot, pulse }) => (
                <div key={name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: dot, boxShadow: pulse ? `0 0 6px ${dot}` : "none" }} />
                    <span className="text-slate-300 font-mono text-[10px]">{name}</span>
                  </div>
                  <span className="text-[9px] font-bold px-2 py-0.5 rounded-full" style={{ color: statusColor, background: bg }}>
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
    <main className="min-h-screen bg-[#050505] text-white selection:bg-brand-primary-500/30 overflow-x-hidden font-inter">
      {/* Ambient Background */}
      <div className="fixed -top-24 -left-24 w-[800px] h-[800px] bg-brand-primary-500/8 rounded-full blur-[150px] pointer-events-none" />
      <div className="fixed top-1/2 -right-24 w-[600px] h-[600px] bg-brand-secondary-500/5 rounded-full blur-[120px] pointer-events-none" />

      {/* ── Sticky Nav ── */}
      <nav className={`fixed top-0 inset-x-0 h-20 z-50 px-10 flex items-center justify-between transition-all duration-300 ${scrolled ? "bg-[#050505]/90 backdrop-blur-xl border-b border-white/5" : ""}`}>
        <div className="flex items-center gap-4 group cursor-pointer">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-primary-500 to-brand-secondary-600 flex items-center justify-center shadow-[0_8px_24px_-4px_rgba(168,85,247,0.5)] group-hover:scale-110 transition-all duration-300">
            <Zap className="w-5 h-5 text-white fill-white/20" />
          </div>
          <div className="flex flex-col">
            <h1 className="text-base font-black font-outfit premium-gradient-text tracking-tighter leading-none mb-0.5">OMNIVIBE</h1>
            <span className="text-[9px] font-black text-white/30 tracking-[0.4em] uppercase">Control Center</span>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-8 text-[11px] font-semibold text-white/40 uppercase tracking-widest">
          <a href="#features" className="hover:text-white/80 transition-colors">기능</a>
          <a href="#studio" className="hover:text-white/80 transition-colors">스튜디오</a>
          <a href="/gallery" className="hover:text-white/80 transition-colors">템플릿</a>
        </div>

        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <div className="flex items-center gap-3 px-5 py-2.5 bg-white/[0.03] border border-white/5 rounded-xl">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] font-black text-white/60 uppercase tracking-widest">{user?.name} 대표님</span>
              </div>
              <button onClick={logout} className="px-5 py-2.5 bg-white/5 hover:bg-red-500/20 border border-white/10 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all">
                Logout
              </button>
            </>
          ) : (
            <button
              onClick={() => setShowAuthModal(true)}
              className="flex items-center gap-2 px-6 py-2.5 bg-brand-primary-600 hover:bg-brand-primary-500 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-purple-500/20 active:scale-95"
            >
              <LogIn className="w-3.5 h-3.5" />
              로그인
            </button>
          )}
        </div>
      </nav>

      {/* ════════════════════════════════════════════════
          Hero — Option A: 좌측 카피 + 우측 Product Mockup
      ════════════════════════════════════════════════ */}
      <section className="relative flex items-start pt-20 pb-10 overflow-hidden">
        {/* 좌측 그라디언트 페이드 */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#050505]/80 via-transparent to-transparent pointer-events-none" />

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
                <span className="text-[10px] font-black text-brand-primary-400 uppercase tracking-[0.3em]">AI Video Synthesis Engine v2.0</span>
              </div>

              {/* 헤드라인 */}
              <h2
                className="animate-fade-in text-5xl md:text-6xl font-black font-outfit tracking-tighter leading-[0.92] mb-6 uppercase italic"
                style={{ animationDelay: "0.2s" }}
              >
                <span className="text-white">영상 제작의</span>
                <br />
                <span className="premium-gradient-text">모든 것을 자동화.</span>
              </h2>

              {/* 서브카피 */}
              <p className="animate-fade-in text-base text-gray-400 leading-relaxed mb-10" style={{ animationDelay: "0.32s" }}>
                PDF 하나면 충분합니다. AI가 스크립트를 쓰고,<br />
                <span className="text-gray-300">목소리를 복제하고, 영상을 완성합니다.</span>
              </p>

              {/* CTA 버튼 */}
              <div className="animate-fade-in flex flex-col sm:flex-row gap-3 mb-10" style={{ animationDelay: "0.42s" }}>
                <a
                  href="/studio"
                  className="flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl text-sm font-black uppercase tracking-widest transition-all group active:scale-95"
                  style={{ background: "linear-gradient(135deg, #a855f7, #6366f1)", boxShadow: "0 0 24px rgba(168,85,247,0.35)" }}
                >
                  <Play className="w-4 h-4 fill-white" />
                  스튜디오 시작하기
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </a>
                <a
                  href="/gallery"
                  className="flex items-center justify-center gap-2 px-7 py-3.5 border border-white/10 bg-white/5 hover:bg-white/10 rounded-xl text-sm font-black uppercase tracking-widest transition-all"
                >
                  <LayoutGrid className="w-4 h-4" />
                  템플릿 갤러리
                </a>
              </div>

              {/* 신뢰 텍스트 */}
              <div className="animate-fade-in flex flex-wrap gap-5 text-xs text-gray-600" style={{ animationDelay: "0.52s" }}>
                {["PDF 업로드만으로 시작", "99% Zero-Fault 오디오", "20개 영상 템플릿 무료"].map((text) => (
                  <span key={text} className="flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-brand-primary-500" />
                    {text}
                  </span>
                ))}
              </div>

              {/* 플랫폼 지원 뱃지 */}
              <div className="animate-fade-in flex items-center gap-3 mt-10" style={{ animationDelay: "0.62s" }}>
                <span className="text-[9px] text-gray-700 uppercase tracking-widest">지원 플랫폼</span>
                <div className="flex gap-2">
                  {[
                    { label: "YouTube", color: "bg-red-500/20 text-red-400 border-red-500/20" },
                    { label: "Instagram", color: "bg-pink-500/20 text-pink-400 border-pink-500/20" },
                    { label: "TikTok", color: "bg-white/10 text-white/60 border-white/10" },
                  ].map(({ label, color }) => (
                    <span key={label} className={`text-[9px] font-bold px-2.5 py-1 rounded-full border ${color}`}>{label}</span>
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
              <span className="text-[10px] text-gray-700 uppercase tracking-widest">AI 파이프라인</span>
              {["ElevenLabs TTS", "OpenAI Whisper", "GPT-4 Writer", "Remotion Render", "Neo4j GraphRAG"].map((tech, i) => (
                <FadeIn key={tech} delay={i * 0.06}>
                  <span className="text-xs text-gray-600 font-mono">{tech}</span>
                </FadeIn>
              ))}
            </div>
          </FadeIn>
        </div>
      </div>

      {/* ── Features / Neural Units ── */}
      <section id="features" className="py-24 relative z-10">
        <div className="container mx-auto px-10">
          <FadeIn className="mb-16">
            <div className="flex items-center gap-6">
              <div className="w-10 h-[2px] bg-brand-primary-500" />
              <h3 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.5em]">Neural Processing Units</h3>
            </div>
          </FadeIn>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="studio">
            {[
              { href: "/studio", title: "통합 스튜디오", desc: "AI 오케스트레이터", icon: MonitorPlay, color: "border-brand-primary-500/40 bg-brand-primary-500/5", highlight: true },
              { href: "/schedule", title: "스케줄러", desc: "데이터 오케스트레이터", icon: Calendar, color: "border-cyan-500/20" },
              { href: "/writer", title: "라이터", desc: "스크립트 고도화 엔진", icon: PenTool, color: "border-purple-500/20" },
              { href: "/audio", title: "오디오", desc: "Zero-Fault 보이스", icon: Mic2, color: "border-blue-500/20" },
              { href: "/production", title: "디렉터", desc: "비주얼 씬 어셈블리", icon: Layout, color: "border-red-500/20" },
              { href: "/presentation", title: "덱 엔진", desc: "PDF → 영상 변환", icon: BookOpen, color: "border-orange-500/20" },
              { href: "/gallery", title: "템플릿 갤러리", desc: "20개 영상 템플릿", icon: LayoutGrid, color: "border-emerald-500/20" },
              { href: "http://localhost:8000/docs", title: "API 문서", desc: "뉴럴 API 명세서", icon: BookOpen, color: "border-white/10", external: true },
            ].map((node, i) => (
              <FadeIn key={node.href + i} delay={i * 0.07}>
                <a
                  href={node.href}
                  target={node.external ? "_blank" : undefined}
                  className={`group relative p-8 bg-white/[0.02] border ${node.color} rounded-[2rem] hover:bg-white/[0.04] transition-all hover:scale-[1.02] active:scale-95 flex flex-col gap-6 overflow-hidden ${node.highlight ? "lg:col-span-1" : ""}`}
                >
                  <div className="absolute top-0 right-0 w-24 h-24 bg-white/3 rounded-full blur-xl group-hover:bg-white/8 transition-colors" />
                  <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center group-hover:scale-110 group-hover:rotate-6 transition-all duration-500">
                    <node.icon className={`w-6 h-6 ${node.highlight ? "text-brand-primary-400" : "text-gray-500 group-hover:text-white"} transition-colors`} />
                  </div>
                  <div>
                    <h3 className="text-xl font-black font-outfit text-white tracking-tight italic uppercase mb-1">{node.title}</h3>
                    <p className="text-[9px] font-black text-gray-600 uppercase tracking-widest">{node.desc}</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-700 group-hover:text-white group-hover:translate-x-1 transition-all mt-auto" />
                </a>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ── System Architecture ── */}
      <section className="py-16 relative z-10 border-t border-white/5">
        <div className="container mx-auto px-10">
          <FadeIn className="mb-12">
            <div className="flex items-center gap-6">
              <div className="w-10 h-[2px] bg-brand-accent-500" />
              <h3 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.5em]">System Architecture</h3>
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
                    <sys.icon className="w-5 h-5 text-gray-600" />
                  </div>
                  <div>
                    <h4 className="text-base font-black text-white tracking-tighter uppercase italic">{sys.title}</h4>
                    <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">{sys.desc}</span>
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
          <div className="flex items-center gap-4 opacity-40">
            <Zap className="w-4 h-4" />
            <span className="text-[9px] font-black uppercase tracking-[0.4em]">OmniVibe Pro Protocol 2026</span>
          </div>
          <div className="flex items-center gap-8 text-[9px] font-black text-white/20 uppercase tracking-[0.3em]">
            <a href="#" className="hover:text-brand-primary-400 transition-colors">Privacy</a>
            <a href="#" className="hover:text-brand-primary-400 transition-colors">Compliance</a>
            <a href="#" className="hover:text-brand-primary-400 transition-colors">Infrastructure</a>
          </div>
        </div>
      </footer>
    </main>
  );
}
