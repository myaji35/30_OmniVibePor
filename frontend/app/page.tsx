"use client";

import { useEffect, useState } from "react";
import {
  LogIn,
  User,
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
  Cpu
} from "lucide-react";
import { useAuth } from "../lib/contexts/AuthContext";
import AuthModal from "../components/AuthModal";

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

export default function Home() {
  const [apiStatus, setApiStatus] = useState<APIStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const { user, isAuthenticated, logout } = useAuth();

  useEffect(() => {
    fetch("/api/backend-status")
      .then((res) => res.json())
      .then((data) => {
        setApiStatus(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("API 연결 실패:", err);
        setLoading(false);
      });
  }, []);

  return (
    <main className="min-h-screen bg-[#050505] text-white selection:bg-brand-primary-500/30 overflow-x-hidden font-inter">
      {/* Dynamic Background Aesthetic */}
      <div className="fixed -top-24 -left-24 w-[800px] h-[800px] bg-brand-primary-500/10 rounded-full blur-[150px] pointer-events-none animate-pulse" />
      <div className="fixed top-1/2 -right-24 w-[600px] h-[600px] bg-brand-secondary-500/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="fixed -bottom-48 left-1/2 -translate-x-1/2 w-[1000px] h-[400px] bg-brand-accent-500/5 rounded-full blur-[100px] pointer-events-none" />

      {/* Navigation / Auth */}
      <nav className="fixed top-0 inset-x-0 h-24 z-50 px-10 flex items-center justify-between">
        <div className="flex items-center gap-4 group cursor-pointer">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-primary-500 to-brand-secondary-600 flex items-center justify-center shadow-[0_10px_30px_-5px_rgba(168,85,247,0.5)] group-hover:scale-110 group-hover:rotate-6 transition-all duration-500">
            <Zap className="w-7 h-7 text-white fill-white/20" />
          </div>
          <div className="flex flex-col">
            <h1 className="text-xl font-black font-outfit premium-gradient-text tracking-tighter leading-none mb-1">
              OMNIVIBE
            </h1>
            <span className="text-[10px] font-black text-white/30 tracking-[0.4em] uppercase">Control Center</span>
          </div>
        </div>

        <div className="flex items-center gap-5">
          {isAuthenticated ? (
            <>
              <div className="flex items-center gap-4 px-6 py-3 bg-white/[0.03] backdrop-blur-3xl border border-white/5 rounded-2xl shadow-2xl">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_#10b981]" />
                <span className="text-[11px] font-black text-white/70 uppercase tracking-widest">{user?.name} 대표님</span>
              </div>
              <button
                onClick={logout}
                className="px-6 py-3 bg-white/5 hover:bg-red-500/20 border border-white/10 hover:border-red-500/30 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-500"
              >
                Logout
              </button>
            </>
          ) : (
            <button
              onClick={() => setShowAuthModal(true)}
              className="flex items-center gap-3 px-8 py-3.5 bg-brand-primary-600 hover:bg-brand-primary-500 rounded-2xl text-[11px] font-black uppercase tracking-[0.2em] transition-all duration-500 shadow-2xl shadow-purple-500/20 active:scale-95"
            >
              <LogIn className="w-4 h-4" />
              인증 초기화 / 로그인
            </button>
          )}
        </div>
      </nav>

      <div className="container mx-auto px-10 pt-44 pb-32 relative z-10">
        {/* Hero Section */}
        <div className="text-center mb-32">
          <div className="inline-flex items-center gap-3 px-5 py-2 bg-brand-primary-500/10 border border-brand-primary-500/20 rounded-full mb-10 animate-fade-in">
            <Sparkles className="w-4 h-4 text-brand-primary-400" />
            <span className="text-[10px] font-black text-brand-primary-400 uppercase tracking-[0.3em]">AI Video Synthesis Engine v2.0</span>
          </div>
          <h2 className="text-7xl font-black font-outfit text-white tracking-tighter mb-8 italic uppercase leading-[0.9]">
            The Future of <br />
            <span className="premium-gradient-text">Omnichannel Automation</span>
          </h2>
          <p className="max-w-2xl mx-auto text-sm font-medium text-gray-500 leading-relaxed uppercase tracking-[0.15em]">
            고성능 영상 제작 및 전략적 콘텐츠 생태계 관리를 위한 <br />차세대 AI 오케스트레이터 시스템입니다.
          </p>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-8">
            <div className="w-20 h-20 border-[3px] border-brand-primary-500/20 border-t-brand-primary-500 rounded-full animate-spin shadow-[0_0_30px_rgba(168,85,247,0.3)]" />
            <p className="text-[10px] font-black text-white/20 uppercase tracking-[0.5em] animate-pulse pl-2">AI 코어 동기화 중...</p>
          </div>
        ) : apiStatus ? (
          <div className="max-w-6xl mx-auto space-y-20">
            {/* System Health Monitor */}
            <section className="premium-card rounded-[3rem] p-12 border border-white/5 relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-96 h-96 bg-brand-primary-500/5 rounded-full blur-[100px] pointer-events-none" />

              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-10 mb-12">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <Activity className="w-5 h-5 text-emerald-500" />
                    <h3 className="text-[10px] font-black text-emerald-500 uppercase tracking-[0.4em]">System Diagnostic</h3>
                  </div>
                  <h2 className="text-4xl font-black font-outfit text-white tracking-tighter uppercase italic">메인 엔진 상태</h2>
                </div>
                <div className="flex items-center gap-5">
                  <div className="px-8 py-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center gap-4">
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_15px_#10b981] animate-pulse" />
                    <span className="text-xs font-black text-emerald-400 tracking-widest uppercase">{apiStatus.status}</span>
                  </div>
                  <div className="px-8 py-4 bg-white/5 border border-white/10 rounded-2xl flex flex-col">
                    <span className="text-[8px] font-black text-gray-600 uppercase tracking-widest mb-1">Architecture</span>
                    <span className="text-xs font-black text-white font-mono tracking-wider">{apiStatus.version}</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                  { label: "AI 목소리 복제", val: apiStatus.features?.voice_cloning, icon: Mic2, color: "text-purple-400", bg: "bg-purple-500/10" },
                  { label: "Zero-Fault 오디오", val: apiStatus.features?.zero_fault_audio, icon: ShieldCheck, color: "text-blue-400", bg: "bg-blue-500/10" },
                  { label: "퍼포먼스 트래커", val: apiStatus.features?.performance_tracking, icon: Activity, color: "text-emerald-400", bg: "bg-emerald-500/10" },
                  { label: "뉴럴 썸네일", val: apiStatus.features?.thumbnail_learning, icon: Sparkles, color: "text-orange-400", bg: "bg-orange-500/10" },
                ].map((f, i) => (
                  <div key={i} className="p-6 bg-white/[0.02] border border-white/5 rounded-3xl hover:bg-white/[0.04] transition-all group/feat relative overflow-hidden">
                    <div className={`w-12 h-12 ${f.bg} rounded-2xl flex items-center justify-center mb-6 group-hover/feat:scale-110 transition-transform`}>
                      <f.icon className={`w-6 h-6 ${f.color}`} />
                    </div>
                    <p className="text-[9px] font-black text-gray-600 uppercase tracking-widest mb-1">{f.label}</p>
                    <p className="text-xs font-black text-white tracking-wider">{f.val || "최적화 완료"}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* Core Workflow Trigger */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
              <a
                href="/studio"
                className="lg:col-span-12 group relative overflow-hidden rounded-[3.5rem] p-16 bg-[#0a0a0c] border border-brand-primary-500/20 hover:border-brand-primary-500/50 transition-all duration-700 shadow-2xl hover:shadow-purple-500/20"
              >
                <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-brand-primary-500/10 rounded-full blur-[120px] pointer-events-none group-hover:bg-brand-primary-500/20 transition-colors duration-700" />
                <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-12">
                  <div className="max-w-2xl text-center md:text-left">
                    <div className="w-20 h-20 bg-gradient-to-br from-brand-primary-500 to-brand-primary-700 rounded-[2rem] flex items-center justify-center mb-10 shadow-2xl shadow-purple-500/40 group-hover:scale-110 group-hover:rotate-6 transition-all duration-700">
                      <MonitorPlay className="w-10 h-10 text-white fill-white/20" />
                    </div>
                    <h2 className="text-5xl font-black font-outfit text-white tracking-tighter mb-6 uppercase italic">통합 옴니 스튜디오</h2>
                    <p className="text-lg font-medium text-gray-400 leading-relaxed max-w-xl border-l-2 border-brand-primary-500/30 pl-8">
                      인텔리전스 스튜디오를 가동합니다. 모든 캠페인 데이터, 스크립트 에이전트,
                      그리고 렌더링 엔진을 하나의 코어에서 관리하세요.
                    </p>
                  </div>
                  <div className="w-32 h-32 rounded-full border border-white/10 flex items-center justify-center group-hover:border-brand-primary-500/50 group-hover:scale-110 transition-all duration-700">
                    <ArrowRight className="w-16 h-16 text-white group-hover:translate-x-4 transition-transform duration-700" />
                  </div>
                </div>
              </a>

              {/* Neural Agents Grid */}
              <div className="lg:col-span-12">
                <div className="flex items-center gap-6 mb-12">
                  <div className="w-10 h-[2px] bg-brand-primary-500" />
                  <h3 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.5em]">Neural Processing Units</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {[
                    { href: "/schedule", title: "스케줄러", desc: "데이터 오케스트레이터", icon: Calendar, color: "border-cyan-500/30" },
                    { href: "/writer", title: "라이터", desc: "스크립트 고도화 엔진", icon: PenTool, color: "border-purple-500/30" },
                    { href: "/audio", title: "오디오", desc: "Zero-Fault 보이스", icon: Mic2, color: "border-blue-500/30" },
                    { href: "/production", title: "디렉터", desc: "비주얼 씬 어셈블리", icon: Layout, color: "border-red-500/30" },
                    { href: "/presentation", title: "덱 엔진", desc: "PDF 인텔리전트 변환", icon: BookOpen, color: "border-orange-500/30" },
                    { href: "http://localhost:8000/docs", title: "API 문서", desc: "뉴럴 API 명세서", icon: BookOpen, color: "border-white/20", external: true },
                  ].map((node, i) => (
                    <a
                      key={i}
                      href={node.href}
                      target={node.external ? "_blank" : undefined}
                      className={`group relative p-10 bg-white/[0.02] border ${node.color} rounded-[2.5rem] hover:bg-white/[0.05] transition-all hover:scale-[1.02] active:scale-95 flex flex-col gap-8 overflow-hidden`}
                    >
                      <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-2xl group-hover:bg-white/10 transition-colors" />
                      <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center group-hover:scale-110 group-hover:rotate-6 transition-all duration-500">
                        <node.icon className="w-7 h-7 text-gray-400 group-hover:text-white transition-colors" />
                      </div>
                      <div className="flex flex-col">
                        <h3 className="text-2xl font-black font-outfit text-white tracking-tight italic uppercase mb-1">{node.title}</h3>
                        <p className="text-[9px] font-black text-gray-600 uppercase tracking-widest">{node.desc}</p>
                      </div>
                    </a>
                  ))}
                </div>
              </div>

              {/* Tech Stack / Dev Tools */}
              <div className="lg:col-span-12">
                <div className="flex items-center gap-6 mb-12 mt-10">
                  <div className="w-10 h-[2px] bg-brand-accent-500" />
                  <h3 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.5em]">System Architecture</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {[
                    { href: "http://localhost:8000/redoc", title: "레지스트리", desc: "API 인벤토리", icon: Database },
                    { href: "http://localhost:7474", title: "GraphRAG", desc: "지식 그래프 브라우저", icon: Share2 },
                    { href: "#", title: "컴퓨팅 코어", desc: "GPU 렌더링 클러스터", icon: Cpu },
                  ].map((sys, i) => (
                    <a
                      key={i}
                      href={sys.href}
                      target="_blank"
                      className="p-8 bg-black/40 border border-white/5 rounded-[2.5rem] flex items-center gap-8 hover:bg-black/60 hover:border-white/10 transition-all font-outfit"
                    >
                      <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center">
                        <sys.icon className="w-6 h-6 text-gray-600" />
                      </div>
                      <div className="flex flex-col">
                        <h4 className="text-lg font-black text-white tracking-tighter uppercase italic">{sys.title}</h4>
                        <span className="text-[9px] font-black text-gray-700 uppercase tracking-widest">{sys.desc}</span>
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-2xl mx-auto text-center p-16 glass-panel rounded-[3rem] border-red-500/20 bg-red-500/[0.02]">
            <div className="w-20 h-20 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-10">
              <Activity className="w-10 h-10 text-red-500 animate-pulse" />
            </div>
            <h2 className="text-3xl font-black font-outfit text-white tracking-tighter uppercase italic mb-6">시스템 연결 오류</h2>
            <p className="text-sm font-medium text-gray-500 leading-relaxed mb-10">
              AI 코어 서버(localhost:8000)와의 통신이 원활하지 않습니다. <br />
              백엔드 엔진이 정상적으로 가동 중인지 시스템 로그를 점검하십시오.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-10 py-4 bg-red-600 hover:bg-red-500 rounded-2xl text-xs font-black uppercase tracking-widest transition-all shadow-2xl shadow-red-500/20"
            >
              엔진 재동기화
            </button>
          </div>
        )}
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />

      {/* Glossy Footer Strip */}
      <footer className="py-20 border-t border-white/5 relative z-10 bg-black/20">
        <div className="container mx-auto px-10 flex flex-col md:flex-row items-center justify-between gap-10">
          <div className="flex items-center gap-4 opacity-30">
            <Zap className="w-5 h-5" />
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
