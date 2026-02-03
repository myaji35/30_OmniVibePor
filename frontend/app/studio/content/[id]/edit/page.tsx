"use client";

import { useParams, useRouter } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { Video, FileText, ArrowLeft, Upload, Clock, Check } from "lucide-react";

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
    if (!contentId) {
      console.log("Waiting for contentId...");
      return;
    }

    try {
      console.log(`Fetching content contentId=${contentId}`);
      const res = await fetch(`http://127.0.0.1:8000/api/v1/content-schedule/${contentId}`);

      if (res.ok) {
        const data = await res.json();
        console.log("Content fetched:", data);

        if (data.success && data.content) {
          setContent({
            ...data.content,
            title: data.content.subtitle || data.content.topic || "제목 없음"
          });
        } else {
          console.error("Content data is missing or success is false:", data);
        }
      } else {
        console.error("Fetch failed:", res.status, res.statusText);
      }
    } catch (error) {
      console.error("❌ 콘텐츠 로드 실패:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleVideoGeneration = () => {
    // Studio 페이지로 이동 (영상 생성 모드)
    router.push(`/studio?contentId=${contentId}&mode=video&duration=${videoDuration}`);
  };

  const handlePresentationMode = () => {
    // PDF 업로드 트리거
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
    formData.append("project_id", "1"); // TODO: 실제 프로젝트 ID 사용
    formData.append("dpi", "200");
    formData.append("lang", "kor+eng");

    try {
      const res = await fetch("http://localhost:8000/api/v1/presentation/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Upload failed");
      }

      const data = await res.json();
      console.log("PDF Upload success:", data);

      // Presentation 페이지로 이동
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
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="text-gray-400">로딩 중...</div>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="text-red-400">콘텐츠를 찾을 수 없습니다.</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* 헤더 */}
      <header className="bg-[#1a1a1a] border-b border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push("/studio")}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 via-blue-400 to-pink-400 bg-clip-text text-transparent">
                {content.title}
              </h1>
              <p className="text-sm text-gray-400 mt-1">
                플랫폼: {content.platform} | 상태: {content.status}
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">
            어떤 방식으로 콘텐츠를 생성하시겠습니까?
          </h2>
          <p className="text-gray-400">
            스크립트 기반 영상 생성 또는 PDF 프레젠테이션 변환을 선택하세요
          </p>
        </div>

        {/* 선택 카드 */}
        <div className="grid md:grid-cols-2 gap-8">
          {/* 1. 영상 생성 */}
          <div
            onClick={handleVideoGeneration}
            className="group relative bg-gradient-to-br from-purple-900/30 to-blue-900/30 border-2 border-purple-500/30 rounded-3xl p-8 cursor-pointer hover:border-purple-500 hover:shadow-2xl hover:shadow-purple-500/20 transition-all duration-300"
          >
            <div className="absolute top-6 right-6 opacity-10 group-hover:opacity-20 transition-opacity">
              <Video className="w-32 h-32" />
            </div>

            <div className="relative z-10">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-500 rounded-2xl flex items-center justify-center mb-6">
                <Video className="w-8 h-8" />
              </div>

              <h3 className="text-2xl font-bold mb-3">영상 생성</h3>
              <p className="text-gray-300 mb-6 leading-relaxed">
                스크립트를 작성하고 AI가 자동으로 영상을 생성합니다.
                <br />
                음성, 자막, 영상 클립이 모두 포함됩니다.
              </p>

              <div className="space-y-4">
                <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-700">
                  <h4 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-purple-400" />
                    영상 분량 선택
                  </h4>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { label: "Shorts", value: 60, desc: "1분 이내" },
                      { label: "Medium", value: 180, desc: "3분 내외" },
                      { label: "Long", value: 600, desc: "10분 내외" },
                    ].map((opt) => (
                      <button
                        key={opt.value}
                        onClick={(e) => {
                          e.stopPropagation();
                          setVideoDuration(opt.value);
                        }}
                        className={`p-2 rounded-lg text-center transition-all ${videoDuration === opt.value
                          ? "bg-purple-600 text-white shadow-lg ring-1 ring-white/50"
                          : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                          }`}
                      >
                        <div className="font-bold text-sm">{opt.label}</div>
                        <div className="text-[10px] opacity-80">{opt.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Check className="w-4 h-4 text-purple-400" />
                  <span>블록 단위 스크립트 편집</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Check className="w-4 h-4 text-purple-400" />
                  <span>Zero-Fault Audio (정확도 95%+)</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Check className="w-4 h-4 text-purple-400" />
                  <span>실시간 렌더링 진행률</span>
                </div>
              </div>

              <button className="mt-8 w-full py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 rounded-xl font-semibold transition-all duration-300 hover:scale-105">
                스크립트 작성 시작 →
              </button>
            </div>
          </div>

          {/* 2. 프레젠테이션 */}
          <div
            onClick={handlePresentationMode}
            className="group relative bg-gradient-to-br from-pink-900/30 to-orange-900/30 border-2 border-pink-500/30 rounded-3xl p-8 cursor-pointer hover:border-pink-500 hover:shadow-2xl hover:shadow-pink-500/20 transition-all duration-300"
          >
            <div className="absolute top-6 right-6 opacity-10 group-hover:opacity-20 transition-opacity">
              <FileText className="w-32 h-32" />
            </div>

            <div className="relative z-10">
              <div className="w-16 h-16 bg-gradient-to-br from-pink-500 to-orange-500 rounded-2xl flex items-center justify-center mb-6">
                <FileText className="w-8 h-8" />
              </div>

              <h3 className="text-2xl font-bold mb-3">프레젠테이션</h3>
              <p className="text-gray-300 mb-6 leading-relaxed">
                PDF 파일을 업로드하면 각 페이지를 기반으로
                <br />
                스크립트와 영상을 자동 생성합니다.
              </p>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Check className="w-4 h-4 text-pink-400" />
                  <span>PDF 업로드 (최대 50페이지)</span>
                  <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept=".pdf"
                    onChange={handleFileChange}
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Check className="w-4 h-4 text-pink-400" />
                  <span>페이지별 스크립트 자동 생성</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Check className="w-4 h-4 text-pink-400" />
                  <span>콘티 자동 분할 (페이지 단위)</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Check className="w-4 h-4 text-pink-400" />
                  <span>슬라이드별 타이밍 조정</span>
                </div>
              </div>

              <button
                className="mt-8 w-full py-4 bg-gradient-to-r from-pink-600 to-orange-600 hover:from-pink-700 hover:to-orange-700 rounded-xl font-semibold transition-all duration-300 hover:scale-105 flex items-center justify-center gap-2"
                disabled={isUploading}
              >
                {isUploading ? (
                  <>
                    <div className="animate-spin w-5 h-5 border-2 border-white/50 border-t-white rounded-full"></div>
                    업로드 중...
                  </>
                ) : (
                  <>
                    PDF 업로드 시작 →
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* 도움말 */}
        <div className="mt-12 bg-[#1a1a1a] border border-gray-800 rounded-xl p-6">
          <h4 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <span className="text-2xl">💡</span>
            선택 가이드
          </h4>
          <div className="grid md:grid-cols-2 gap-6 text-sm text-gray-400">
            <div>
              <p className="font-semibold text-purple-400 mb-2">
                영상 생성을 추천하는 경우
              </p>
              <ul className="space-y-1 list-disc list-inside">
                <li>자유로운 스크립트 작성이 필요한 경우</li>
                <li>다양한 영상 클립을 사용하고 싶은 경우</li>
                <li>블록 단위로 세밀하게 편집하고 싶은 경우</li>
                <li>YouTube 쇼츠, TikTok 등 짧은 영상</li>
              </ul>
            </div>
            <div>
              <p className="font-semibold text-pink-400 mb-2">
                프레젠테이션을 추천하는 경우
              </p>
              <ul className="space-y-1 list-disc list-inside">
                <li>이미 준비된 PDF 자료가 있는 경우</li>
                <li>교육용 강의 영상을 만들고 싶은 경우</li>
                <li>슬라이드 기반의 설명 영상</li>
                <li>비즈니스 프레젠테이션 영상화</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
