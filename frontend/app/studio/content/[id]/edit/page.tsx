"use client";

import { useParams, useRouter } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { Video, FileText, ArrowLeft, Upload, Clock, Check, Sparkles, Layout, MonitorPlay, AlertCircle } from "lucide-react";

interface Content {
  id: number;
  title: string;
  platform: string;
  status: string;
}

export default function ContentEditPage() {
  const params = useParams();
  const router = useRouter();
  const contentId = params.id as string;

  const [content, setContent] = useState<Content | null>(null);
  const [loading, setLoading] = useState(true);
  const [videoDuration, setVideoDuration] = useState<number>(180); // Default 3 mins
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadContent();
  }, [contentId]);

  const loadContent = async () => {
    if (!contentId) return;

    try {
      // 127.0.0.1 대신 localhost 사용 시도 및 타임아웃 추가
      const fetchPromise = fetch(`/api/content-schedule?content_id=${contentId}`);
      const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000));

      const res = await Promise.race([fetchPromise, timeoutPromise]) as Response;

      if (res.ok) {
        const data = await res.json();
        // 백엔드 API 구조에 따라 유연하게 매핑
        if (data.success && data.content) {
          setContent({
            ...data.content,
            title: data.content.subtitle || data.content.topic || data.content.title || "제목 없음"
          });
        } else if (data.success && data.contents && Array.isArray(data.contents)) {
          // 배열로 올 경우 해당 ID 찾기
          const found = data.contents.find((c: any) => c.id.toString() === contentId);
          if (found) {
            setContent({
              ...found,
              title: found.subtitle || found.topic || found.title || "제목 없음"
            });
          }
        }
      }
    } catch (error) {
      console.error("❌ 콘텐츠 로드 실패:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleVideoGeneration = () => {
    router.push(`/studio?contentId=${contentId}&mode=video&duration=${videoDuration}`);
  };

  const handlePresentationMode = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== "application/pdf") {
      alert("PDF 파일만 업로드 가능합니다.");
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("project_id", "1");
    formData.append("dpi", "200");
    formData.append("lang", "kor+eng");

    try {
      const res = await fetch("http://localhost:8000/api/v1/presentation/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();
      router.push(`/presentation/${data.presentation_id}`);
    } catch (error) {
      console.error("PDF upload error:", error);
      alert("PDF 업로드 중 오류가 발생했습니다.");
    } finally {
      setIsUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="flex flex-col items-center gap-6">
          <div className="w-16 h-16 border-4 border-brand-primary-500/20 border-t-brand-primary-500 rounded-full animate-spin shadow-[0_0_20px_rgba(168,85,247,0.3)]"></div>
          <span className="text-[10px] font-black text-white/30 tracking-[0.4em] uppercase">Initialising AI Core</span>
        </div>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center p-10">
        <div className="max-w-md w-full glass-panel rounded-[3rem] p-12 text-center border-red-500/20">
          <div className="w-20 h-20 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-8">
            <AlertCircle className="w-10 h-10 text-red-500" />
          </div>
          <h2 className="text-2xl font-black font-outfit text-white uppercase italic mb-4">데이터 로드 실패</h2>
          <p className="text-gray-500 text-sm leading-relaxed mb-10">
            콘텐츠(ID: {contentId}) 정보를 불러올 수 없습니다. <br />
            네트워크 연결이나 데이터를 다시 확인해 주세요.
          </p>
          <button
            onClick={() => router.push('/studio')}
            className="w-full py-4 bg-white/5 hover:bg-white/10 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all"
          >
            ← 스튜디오로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] text-white overflow-x-hidden font-inter selection:bg-purple-500/30">
      {/* Background Aesthetic Blur */}
      <div className="fixed -top-24 -left-24 w-[600px] h-[600px] bg-brand-primary-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="fixed bottom-0 -right-24 w-[500px] h-[500px] bg-brand-secondary-500/5 rounded-full blur-[100px] pointer-events-none" />

      {/* 헤더 */}
      <header className="sticky top-0 h-24 glass-panel border-b border-white/5 px-10 flex items-center justify-between z-50">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none" />
        <div className="max-w-7xl mx-auto w-full flex items-center justify-between">
          <div className="flex items-center gap-8">
            <button
              onClick={() => router.push("/studio")}
              className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 hover:scale-110 transition-all group"
            >
              <ArrowLeft className="w-5 h-5 text-gray-400 group-hover:text-white transition-colors" />
            </button>
            <div className="flex flex-col">
              <div className="flex items-center gap-2 text-[10px] font-black text-gray-600 uppercase tracking-[0.25em] mb-1">
                <span>Orchestrator</span>
                <div className="w-1.5 h-1.5 rounded-full bg-brand-primary-500" />
                <span className="text-brand-primary-400/80">워크플로우 모드 선택</span>
              </div>
              <h1 className="text-2xl font-black font-outfit text-white tracking-tighter">
                {content.title}
              </h1>
            </div>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="max-w-6xl mx-auto px-10 py-24 relative z-10">
        <div className="text-center mb-24">
          <div className="inline-flex items-center gap-3 px-5 py-2 bg-brand-primary-500/10 border border-brand-primary-500/20 rounded-full mb-8">
            <Sparkles className="w-4 h-4 text-brand-primary-400" />
            <span className="text-[10px] font-black text-brand-primary-400 uppercase tracking-[0.2em]">Engine Selection Required</span>
          </div>
          <h2 className="text-5xl font-black font-outfit premium-gradient-text tracking-tighter mb-6 italic uppercase">
            Define Your Workflow
          </h2>
          <p className="text-[10px] font-black text-white/40 tracking-[0.4em] uppercase">
            콘텐츠 합성을 위한 뉴럴 패키지 엔진을 선택하십시오.
          </p>
        </div>

        {/* 선택 카드 */}
        <div className="grid md:grid-cols-2 gap-10">
          {/* 1. 영상 생성 (Script to Video) */}
          <div
            onClick={handleVideoGeneration}
            className="group relative h-[600px] premium-card rounded-[3rem] p-12 cursor-pointer border border-white/5 hover:border-brand-primary-500/50 hover:shadow-[0_50px_100px_-20px_rgba(168,85,247,0.2)] transition-all duration-700 overflow-hidden"
          >
            {/* Glossy Reflect */}
            <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-white/5 to-transparent pointer-events-none" />
            <div className="absolute inset-0 bg-gradient-to-br from-brand-primary-500/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />

            <div className="relative h-full flex flex-col justify-between">
              <div>
                <div className="w-20 h-20 bg-gradient-to-br from-brand-primary-500 to-brand-primary-700 rounded-[2rem] flex items-center justify-center mb-10 shadow-2xl shadow-purple-500/40 group-hover:scale-110 group-hover:rotate-6 transition-all duration-700">
                  <MonitorPlay className="w-10 h-10 text-white fill-white/20" />
                </div>

                <h3 className="text-3xl font-black font-outfit text-white tracking-tighter mb-4 italic uppercase">
                  Script Engine
                </h3>
                <p className="text-sm font-medium text-gray-400 leading-relaxed mb-10 border-l-2 border-brand-primary-500/30 pl-6">
                  LLM 기반의 스크립트 작성부터 AI 성우 보이스,
                  스토리보드 매핑 및 영상 렌더링까지 이어지는
                  엔드투엔드 동영상 제작 워크플로우를 가동합니다.
                </p>

                <div className="space-y-4">
                  <div className="bg-black/40 backdrop-blur-3xl p-6 rounded-[2rem] border border-white/5 space-y-4">
                    <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.3em] flex items-center gap-2">
                      <Clock className="w-4 h-4 text-brand-primary-400" />
                      목표 영상 분량 선택
                    </h4>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { label: "Shorts", value: 60, desc: "60초" },
                        { label: "Normal", value: 180, desc: "180초" },
                        { label: "Cinema", value: 600, desc: "600초" },
                      ].map((opt) => (
                        <button
                          key={opt.value}
                          onClick={(e) => {
                            e.stopPropagation();
                            setVideoDuration(opt.value);
                          }}
                          className={`py-3 rounded-2xl text-center transition-all border ${videoDuration === opt.value
                            ? "bg-brand-primary-500 border-brand-primary-400 text-white shadow-lg shadow-purple-500/40 scale-[1.05]"
                            : "bg-white/5 border-white/5 text-gray-500 hover:text-white hover:border-white/10"
                            }`}
                        >
                          <div className="font-black text-[9px] uppercase tracking-widest">{opt.label}</div>
                          <div className="text-[10px] font-black opacity-60 font-mono">{opt.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center gap-3 text-[10px] font-black text-gray-600 uppercase tracking-widest">
                  <Check className="w-4 h-4 text-brand-primary-400" />
                  <span>VREW Style Context Blocks</span>
                </div>
                <button className="w-full py-5 bg-white text-black rounded-[1.5rem] font-black text-[11px] uppercase tracking-[0.3em] hover:bg-brand-primary-400 hover:text-white transition-all duration-500 shadow-2xl active:scale-95 group-hover:scale-[1.02]">
                  스크립트 생성 엔진 초기화 →
                </button>
              </div>
            </div>
          </div>

          {/* 2. 프레젠테이션 (PDF to Video) */}
          <div
            onClick={handlePresentationMode}
            className="group relative h-[600px] premium-card rounded-[3rem] p-12 cursor-pointer border border-white/5 hover:border-brand-secondary-500/50 hover:shadow-[0_50px_100px_-20px_rgba(236,72,153,0.2)] transition-all duration-700 overflow-hidden"
          >
            {/* Glossy Reflect */}
            <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-white/5 to-transparent pointer-events-none" />
            <div className="absolute inset-0 bg-gradient-to-br from-brand-secondary-500/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />

            <div className="relative h-full flex flex-col justify-between">
              <div>
                <div className="w-20 h-20 bg-gradient-to-br from-brand-secondary-500 to-brand-secondary-700 rounded-[2rem] flex items-center justify-center mb-10 shadow-2xl shadow-pink-500/40 group-hover:scale-110 group-hover:rotate-6 transition-all duration-700">
                  <Layout className="w-10 h-10 text-white fill-white/20" />
                </div>

                <h3 className="text-3xl font-black font-outfit text-white tracking-tighter mb-4 italic uppercase">
                  Deck Engine
                </h3>
                <p className="text-sm font-medium text-gray-400 leading-relaxed mb-10 border-l-2 border-brand-secondary-500/30 pl-6">
                  준비된 PDF 자료를 업로드하여 페이지별 스크립트와
                  시각 요소를 AI로 자동 추출합니다. 교육 및 비즈니스
                  발표 영상을 위한 페이지 기반 스마트 워크플로우입니다.
                </p>

                <div className="p-8 border-2 border-dashed border-white/5 rounded-[2.5rem] flex flex-col items-center justify-center text-center gap-4 bg-black/20 group-hover:border-brand-secondary-500/30 transition-all duration-700">
                  <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center group-hover:scale-125 group-hover:rotate-12 transition-all">
                    <Upload className="w-6 h-6 text-gray-500 group-hover:text-brand-secondary-400" />
                  </div>
                  <span className="text-[10px] font-black text-gray-700 group-hover:text-white uppercase tracking-[0.2em] transition-colors">이곳에 PDF 파일을 업로드하세요</span>
                </div>

                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  accept=".pdf"
                  onChange={handleFileChange}
                  onClick={(e) => e.stopPropagation()}
                />
              </div>

              <div className="space-y-4">
                <div className="flex items-center gap-3 text-[10px] font-black text-gray-600 uppercase tracking-widest">
                  <Check className="w-4 h-4 text-brand-secondary-400" />
                  <span>Multi-Page Neural Extraction</span>
                </div>
                <button
                  disabled={isUploading}
                  className="w-full py-5 bg-white text-black rounded-[1.5rem] font-black text-[11px] uppercase tracking-[0.3em] hover:bg-brand-secondary-400 hover:text-white transition-all duration-500 shadow-2xl active:scale-95 group-hover:scale-[1.02] flex items-center justify-center gap-3"
                >
                  {isUploading ? (
                    <>
                      <div className="animate-spin w-4 h-4 border-2 border-brand-secondary-200 border-t-transparent rounded-full"></div>
                      데이터 분석 중...
                    </>
                  ) : (
                    "PDF 업로드 워크플로우 가동 →"
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 선택 가이드 (Aesthetic Details) */}
        <div className="mt-32 p-12 glass-panel rounded-[3rem] border-white/5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-brand-primary-500/5 rounded-full blur-3xl" />
          <h4 className="text-lg font-black font-outfit text-white tracking-tight mb-10 flex items-center gap-4 italic uppercase">
            <span className="text-2xl text-brand-primary-400">⚡</span>
            Architectural Guidance
          </h4>
          <div className="grid md:grid-cols-2 gap-12 text-xs font-medium text-gray-500">
            <div className="space-y-4">
              <p className="font-black text-brand-primary-400 uppercase tracking-widest border-b border-brand-primary-500/20 pb-2">
                Use Script Engine if:
              </p>
              <ul className="space-y-4">
                <li className="flex gap-4">
                  <div className="w-1.5 h-1.5 rounded-full bg-brand-primary-500 mt-1" />
                  <span>자유로운 AI 스크립트 기반 생성이 필요한 도메인</span>
                </li>
                <li className="flex gap-4">
                  <div className="w-1.5 h-1.5 rounded-full bg-brand-primary-500 mt-1" />
                  <span>유튜브 쇼츠, 틱톡 등 고밀도 자막 연출이 핵심인 경우</span>
                </li>
              </ul>
            </div>
            <div className="space-y-4">
              <p className="font-black text-brand-secondary-400 uppercase tracking-widest border-b border-brand-secondary-500/20 pb-2">
                Use Deck Engine if:
              </p>
              <ul className="space-y-4">
                <li className="flex gap-4">
                  <div className="w-1.5 h-1.5 rounded-full bg-brand-secondary-500 mt-1" />
                  <span>기존 강의 자료나 보고서가 PDF로 이미 존재하는 프로젝트</span>
                </li>
                <li className="flex gap-4">
                  <div className="w-1.5 h-1.5 rounded-full bg-brand-secondary-500 mt-1" />
                  <span>안정적인 페이지 기반의 정보 전달이 우선순위인 경우</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
