"use client";

/**
 * PresentationMode - PDF 프리젠테이션 영상 생성 UI
 *
 * REALPLAN.md Phase 7 구현
 *
 * PDF 업로드 → 스크립트 생성 → 오디오 생성 → 타이밍 분석 → 영상 생성
 */

import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import {
  Upload,
  FileText,
  Volume2,
  Clock,
  Video,
  Download,
  Check,
  AlertCircle,
  Loader2,
  Play,
  Edit3,
  Save,
  RefreshCw,
} from "lucide-react";
import {
  PresentationStatus,
  TransitionEffect,
  type SlideInfo,
  type Presentation,
  type GenerateScriptRequest,
  type GenerateAudioRequest,
  type GenerateVideoRequest,
} from "@/lib/types/presentation";
import {
  getDemoPresentation,
  DEMO_VOICE_CONFIG,
  type VoiceConfig,
} from "@/data/demo-presentation";
import SlidePlayer from "@/components/SlidePlayer";

// ==================== Constants ====================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STATUS_LABELS: Record<PresentationStatus, string> = {
  [PresentationStatus.UPLOADED]: "업로드 완료",
  [PresentationStatus.SCRIPT_GENERATED]: "스크립트 생성 완료",
  [PresentationStatus.AUDIO_GENERATED]: "오디오 생성 완료",
  [PresentationStatus.TIMING_ANALYZED]: "타이밍 분석 완료",
  [PresentationStatus.VIDEO_RENDERING]: "영상 렌더링 중",
  [PresentationStatus.VIDEO_READY]: "영상 생성 완료",
  [PresentationStatus.FAILED]: "실패",
};

// ==================== Types ====================

interface PresentationModeProps {
  projectId: string;
  presentationId?: string | null;
  onComplete?: (videoPath: string) => void;
}

// ==================== Component ====================

export default function PresentationMode({
  projectId,
  presentationId: initialPresentationId,
  onComplete,
}: PresentationModeProps) {
  // State
  const [presentationId, setPresentationId] = useState<string | null>(
    initialPresentationId || null
  );
  const [presentation, setPresentation] = useState<Presentation | null>(null);
  const [selectedSlideIndex, setSelectedSlideIndex] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Demo mode
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [demoStep, setDemoStep] = useState<string | null>(null);
  const [voiceConfig, setVoiceConfig] = useState<VoiceConfig>(DEMO_VOICE_CONFIG);

  // Brand template
  const [brandTemplates, setBrandTemplates] = useState<Array<{ id: string; name: string; is_default: boolean }>>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');

  // Narration editing
  const [editingSlideIndex, setEditingSlideIndex] = useState<number | null>(null);
  const [editedScript, setEditedScript] = useState<string>("");

  // File input ref
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load brand templates on mount
  useEffect(() => {
    fetch('/api/brand-templates?project_id=default')
      .then(r => r.json())
      .then(data => {
        const tpls = data.templates || [];
        setBrandTemplates(tpls);
        const defaultTpl = tpls.find((t: any) => t.is_default);
        if (defaultTpl) setSelectedTemplateId(defaultTpl.id);
      })
      .catch(() => {});
  }, []);

  // Load presentation data (skip in demo mode)
  useEffect(() => {
    if (presentationId && !isDemoMode) {
      loadPresentation(presentationId);
    }
  }, [presentationId, isDemoMode]);

  // ==================== API Functions ====================

  const loadPresentation = async (id: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.get(`${API_BASE_URL}/api/v1/presentations/${id}`);
      setPresentation(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "프리젠테이션을 불러오는데 실패했습니다.");
      console.error("Load presentation error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("PDF 파일만 업로드 가능합니다.");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      setUploadProgress(0);

      const formData = new FormData();
      formData.append("file", file);
      formData.append("project_id", projectId);
      formData.append("dpi", "200");
      formData.append("lang", "kor+eng");
      if (selectedTemplateId) {
        formData.append("template_id", selectedTemplateId);
      }

      const response = await axios.post(
        `${API_BASE_URL}/api/v1/presentations/upload`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / (progressEvent.total || 1)
            );
            setUploadProgress(percentCompleted);
          },
        }
      );

      setPresentationId(response.data.presentation_id);
      setPresentation(response.data);
      setSelectedSlideIndex(0);
    } catch (err: any) {
      setError(err.response?.data?.detail || "파일 업로드에 실패했습니다.");
      console.error("Upload error:", err);
    } finally {
      setIsLoading(false);
      setUploadProgress(0);
    }
  };

  const handleGenerateScript = async () => {
    if (!presentationId) return;

    try {
      setIsLoading(true);
      setError(null);

      const request: GenerateScriptRequest = {
        tone: "professional",
        target_duration_per_slide: 15.0,
        include_slide_numbers: false,
      };

      const response = await axios.post(
        `${API_BASE_URL}/api/v1/presentations/${presentationId}/generate-script`,
        request
      );

      setPresentation(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "스크립트 생성에 실패했습니다.");
      console.error("Generate script error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateAudio = async () => {
    if (!presentationId) return;

    try {
      setIsLoading(true);
      setError(null);

      const request: GenerateAudioRequest = {
        model: "tts-1",
      };

      const response = await axios.post(
        `${API_BASE_URL}/api/v1/presentations/${presentationId}/generate-audio`,
        request
      );

      // Reload presentation to get updated data
      await loadPresentation(presentationId);
    } catch (err: any) {
      setError(err.response?.data?.detail || "오디오 생성에 실패했습니다.");
      console.error("Generate audio error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzeTiming = async () => {
    if (!presentationId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.post(
        `${API_BASE_URL}/api/v1/presentations/${presentationId}/analyze-timing`,
        {}
      );

      setPresentation(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "타이밍 분석에 실패했습니다.");
      console.error("Analyze timing error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateVideo = async () => {
    if (!presentationId) return;

    try {
      setIsLoading(true);
      setError(null);

      const request: GenerateVideoRequest = {
        transition_effect: TransitionEffect.FADE,
        transition_duration: 0.5,
        bgm_volume: 0.3,
      };

      const response = await axios.post(
        `${API_BASE_URL}/api/v1/presentations/${presentationId}/generate-video`,
        request
      );

      // Start polling for video status
      pollVideoStatus(presentationId);
    } catch (err: any) {
      setError(err.response?.data?.detail || "영상 생성에 실패했습니다.");
      console.error("Generate video error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const pollVideoStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/v1/presentations/${id}`);
        const data: Presentation = response.data;

        setPresentation(data);

        if (
          data.status === PresentationStatus.VIDEO_READY ||
          data.status === PresentationStatus.FAILED
        ) {
          clearInterval(interval);

          if (data.status === PresentationStatus.VIDEO_READY && data.video_path) {
            onComplete?.(data.video_path);
          }
        }
      } catch (err) {
        console.error("Poll status error:", err);
        clearInterval(interval);
      }
    }, 3000);
  };

  // ==================== Slide Editing ====================

  const handleEditSlide = (slideIndex: number) => {
    const slide = presentation?.slides[slideIndex];
    if (!slide) return;

    setEditingSlideIndex(slideIndex);
    setEditedScript(slide.script || "");
  };

  const handleSaveSlideScript = async () => {
    if (editingSlideIndex === null || !presentation) return;

    // Update local state
    const updatedSlides = [...presentation.slides];
    updatedSlides[editingSlideIndex] = {
      ...updatedSlides[editingSlideIndex],
      script: editedScript,
    };

    setPresentation({
      ...presentation,
      slides: updatedSlides,
    });

    setEditingSlideIndex(null);
    setEditedScript("");

    // TODO: Call API to update slide script in backend
  };

  const handleCancelEdit = () => {
    setEditingSlideIndex(null);
    setEditedScript("");
  };

  // ==================== Demo Mode ====================

  const handleStartDemo = () => {
    setIsDemoMode(true);
    setError(null);
    setDemoStep("uploading");
    setIsLoading(true);

    // Simulate upload delay
    setTimeout(() => {
      const demoData = getDemoPresentation(PresentationStatus.UPLOADED);
      setPresentationId(demoData.presentation_id);
      setPresentation(demoData);
      setSelectedSlideIndex(0);
      setDemoStep(null);
      setIsLoading(false);
    }, 1500);
  };

  const handleDemoGenerateScript = () => {
    setIsLoading(true);
    setDemoStep("generating_script");

    setTimeout(() => {
      const demoData = getDemoPresentation(PresentationStatus.SCRIPT_GENERATED);
      setPresentation(demoData);
      setDemoStep(null);
      setIsLoading(false);
    }, 2000);
  };

  const handleDemoGenerateAudio = () => {
    setIsLoading(true);
    setDemoStep("generating_audio");

    setTimeout(() => {
      const demoData = getDemoPresentation(PresentationStatus.AUDIO_GENERATED);
      setPresentation(demoData);
      setDemoStep(null);
      setIsLoading(false);
    }, 2500);
  };

  const handleDemoAnalyzeTiming = () => {
    setIsLoading(true);
    setDemoStep("analyzing_timing");

    setTimeout(() => {
      const demoData = getDemoPresentation(PresentationStatus.TIMING_ANALYZED);
      setPresentation(demoData);
      setDemoStep(null);
      setIsLoading(false);
    }, 1500);
  };

  const handleDemoGenerateVideo = () => {
    setIsLoading(true);
    setDemoStep("rendering_video");

    setTimeout(() => {
      const demoData = getDemoPresentation(PresentationStatus.VIDEO_READY);
      setPresentation(demoData);
      setDemoStep(null);
      setIsLoading(false);
    }, 3000);
  };

  const handleResetDemo = () => {
    setIsDemoMode(false);
    setPresentationId(null);
    setPresentation(null);
    setSelectedSlideIndex(0);
    setDemoStep(null);
    setError(null);
  };

  const demoStepLabels: Record<string, string> = {
    uploading: "PDF 슬라이드 분석 중...",
    generating_script: "AI 나레이션 스크립트 생성 중...",
    generating_audio: "ElevenLabs 남성 TTS 생성 + Whisper 검증 중...",
    analyzing_timing: "슬라이드-오디오 타이밍 동기화 중...",
    rendering_video: "FFmpeg 영상 렌더링 중...",
  };

  // ==================== Helpers ====================

  const formatTime = (seconds?: number | null): string => {
    if (seconds === null || seconds === undefined) return "--:--";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const getProgressPercentage = (): number => {
    if (!presentation) return 0;

    const statusOrder = [
      PresentationStatus.UPLOADED,
      PresentationStatus.SCRIPT_GENERATED,
      PresentationStatus.AUDIO_GENERATED,
      PresentationStatus.TIMING_ANALYZED,
      PresentationStatus.VIDEO_RENDERING,
      PresentationStatus.VIDEO_READY,
    ];

    const currentIndex = statusOrder.indexOf(presentation.status);
    return ((currentIndex + 1) / statusOrder.length) * 100;
  };

  const canGenerateScript = presentation?.status === PresentationStatus.UPLOADED;
  const canGenerateAudio = presentation?.status === PresentationStatus.SCRIPT_GENERATED;
  const canAnalyzeTiming = presentation?.status === PresentationStatus.AUDIO_GENERATED;
  const canGenerateVideo = presentation?.status === PresentationStatus.TIMING_ANALYZED;

  // Demo mode overrides
  const onGenerateScript = isDemoMode ? handleDemoGenerateScript : handleGenerateScript;
  const onGenerateAudio = isDemoMode ? handleDemoGenerateAudio : handleGenerateAudio;
  const onAnalyzeTiming = isDemoMode ? handleDemoAnalyzeTiming : handleAnalyzeTiming;
  const onGenerateVideo = isDemoMode ? handleDemoGenerateVideo : handleGenerateVideo;

  const selectedSlide = presentation?.slides[selectedSlideIndex];

  // ==================== Render ====================

  return (
    <div className="min-h-screen bg-[#1a1a1a] text-white p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-[#2a2a2a] border border-gray-800 rounded-lg p-6">
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent">프리젠테이션 모드</h1>
                {isDemoMode && (
                  <span className="px-2 py-0.5 bg-blue-600 text-white text-xs font-bold rounded">DEMO</span>
                )}
              </div>
              <p className="text-gray-400 mt-1">
                {isDemoMode
                  ? "신선식품 B2B 스케일업 아키텍처 — 남성 보이스 데모"
                  : "PDF를 업로드하여 나레이션 영상을 생성하세요"}
              </p>
            </div>

            {presentation && (
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 bg-purple-600/20 text-purple-300 rounded-full text-sm font-medium">
                  {STATUS_LABELS[presentation.status]}
                </span>
                <span className="text-sm text-gray-400">
                  {presentation.total_slides}개 슬라이드
                </span>
              </div>
            )}
          </div>

          {/* Progress Bar */}
          {presentation && (
            <div className="mt-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-300">전체 진행률</span>
                <span className="text-sm font-medium text-white">
                  {Math.round(getProgressPercentage())}%
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-purple-600 to-pink-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${getProgressPercentage()}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-red-300">오류 발생</h3>
              <p className="text-red-400 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Upload Section */}
        {!presentation && (
          <div className="bg-[#2a2a2a] border border-gray-800 rounded-lg p-8">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="hidden"
            />

            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-purple-600/20 rounded-full flex items-center justify-center mb-4">
                <Upload className="w-8 h-8 text-purple-400" />
              </div>

              <h3 className="text-lg font-semibold text-white mb-2">PDF 파일 업로드</h3>
              <p className="text-gray-400 text-sm mb-4">
                프리젠테이션 PDF를 업로드하면 자동으로 슬라이드를 분석합니다
              </p>

              {/* 브랜드 템플릿 선택 */}
              {brandTemplates.length > 0 && (
                <div className="mb-6 max-w-xs mx-auto">
                  <label className="block text-xs font-semibold text-gray-400 mb-1.5 text-left">브랜드 템플릿 (인트로/아웃트로)</label>
                  <select value={selectedTemplateId} onChange={e => setSelectedTemplateId(e.target.value)}
                    className="w-full px-3 py-2.5 border border-gray-600 rounded-lg text-sm text-white bg-[#2a2a2a] focus:outline-none focus:border-purple-500">
                    <option value="">템플릿 없음</option>
                    {brandTemplates.map(t => (
                      <option key={t.id} value={t.id}>{t.name}{t.is_default ? ' (기본)' : ''}</option>
                    ))}
                  </select>
                </div>
              )}

              <div className="flex items-center gap-4 justify-center">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isLoading}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
                >
                  {isLoading && !isDemoMode ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      업로드 중... {uploadProgress}%
                    </>
                  ) : (
                    <>
                      <Upload className="w-5 h-5" />
                      PDF 선택
                    </>
                  )}
                </button>

                <span className="text-gray-500">또는</span>

                <button
                  onClick={handleStartDemo}
                  disabled={isLoading}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg hover:from-blue-700 hover:to-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all"
                >
                  {isLoading && isDemoMode ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      {demoStep && demoStepLabels[demoStep]}
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5" />
                      데모 체험 (신선식품 B2B)
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        {presentation && (
          <div className="grid grid-cols-12 gap-6">
            {/* Left Sidebar - Slide List */}
            <div className="col-span-3 bg-[#2a2a2a] border border-gray-800 rounded-lg p-4">
              <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5" />
                슬라이드 목록
              </h3>

              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {presentation.slides.map((slide, index) => (
                  <button
                    key={slide.slide_number}
                    onClick={() => setSelectedSlideIndex(index)}
                    className={`w-full p-3 rounded-lg border-2 transition-all text-left ${
                      selectedSlideIndex === index
                        ? "border-purple-600 bg-purple-600/10"
                        : "border-gray-700 hover:border-gray-600"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Thumbnail */}
                      <div className="w-16 h-12 bg-gray-800 rounded flex-shrink-0 overflow-hidden">
                        <img
                          src={isDemoMode ? slide.image_path : `${API_BASE_URL}${slide.image_path}`}
                          alt={`Slide ${slide.slide_number}`}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.currentTarget.style.display = "none";
                          }}
                        />
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-white">
                            #{slide.slide_number}
                          </span>
                          {slide.script && (
                            <Check className="w-4 h-4 text-green-400" />
                          )}
                        </div>

                        {slide.duration !== null && slide.duration !== undefined && (
                          <div className="flex items-center gap-1 text-xs text-gray-400">
                            <Clock className="w-3 h-3" />
                            {formatTime(slide.duration)}
                          </div>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Main Area - Slide Preview & Editor */}
            <div className="col-span-9 space-y-6">
              {/* Slide Preview */}
              <div className="bg-[#2a2a2a] border border-gray-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-white flex items-center gap-2">
                    슬라이드 #{selectedSlide?.slide_number}
                  </h3>

                  {selectedSlide?.start_time !== null &&
                    selectedSlide?.start_time !== undefined && (
                      <div className="flex items-center gap-4 text-sm text-gray-400">
                        <span>시작: {formatTime(selectedSlide.start_time)}</span>
                        <span>종료: {formatTime(selectedSlide.end_time)}</span>
                        <span className="font-medium text-purple-400">
                          길이: {formatTime(selectedSlide.duration)}
                        </span>
                      </div>
                    )}
                </div>

                {/* Large Preview */}
                <div className="bg-[#1a1a1a] rounded-lg overflow-hidden flex items-center justify-center h-96">
                  {selectedSlide && (
                    <img
                      src={isDemoMode ? selectedSlide.image_path : `${API_BASE_URL}${selectedSlide.image_path}`}
                      alt={`Slide ${selectedSlide.slide_number}`}
                      className="max-w-full max-h-full object-contain"
                      onError={(e) => {
                        e.currentTarget.parentElement!.innerHTML =
                          '<div class="text-gray-500">이미지를 불러올 수 없습니다</div>';
                      }}
                    />
                  )}
                </div>
              </div>

              {/* Narration Editor */}
              <div className="bg-[#2a2a2a] border border-gray-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-white flex items-center gap-2">
                    <Volume2 className="w-5 h-5" />
                    나레이션 스크립트
                  </h3>

                  {selectedSlide?.script && editingSlideIndex !== selectedSlideIndex && (
                    <button
                      onClick={() => handleEditSlide(selectedSlideIndex)}
                      className="px-3 py-1 text-sm text-purple-400 hover:bg-purple-600/10 rounded-lg flex items-center gap-1 transition-colors"
                    >
                      <Edit3 className="w-4 h-4" />
                      편집
                    </button>
                  )}
                </div>

                {!selectedSlide?.script ? (
                  <div className="text-center py-8 border-2 border-dashed border-gray-700 rounded-lg">
                    <p className="text-gray-500 mb-4">
                      스크립트가 아직 생성되지 않았습니다
                    </p>
                  </div>
                ) : editingSlideIndex === selectedSlideIndex ? (
                  <div className="space-y-4">
                    <textarea
                      value={editedScript}
                      onChange={(e) => setEditedScript(e.target.value)}
                      className="w-full h-40 px-4 py-3 bg-[#1a1a1a] border border-gray-700 rounded-lg resize-none text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="나레이션 스크립트를 입력하세요..."
                    />

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-400">
                        {editedScript.length}자 | 예상 시간:{" "}
                        {Math.round((editedScript.length / 300) * 60)}초
                      </span>

                      <div className="flex gap-2">
                        <button
                          onClick={handleCancelEdit}
                          className="px-4 py-2 text-gray-300 border border-gray-700 rounded-lg hover:bg-gray-800 transition-colors"
                        >
                          취소
                        </button>
                        <button
                          onClick={handleSaveSlideScript}
                          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2 transition-colors"
                        >
                          <Save className="w-4 h-4" />
                          저장
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-[#1a1a1a] border border-gray-700 rounded-lg p-4">
                    <p className="text-gray-300 whitespace-pre-wrap">{selectedSlide.script}</p>

                    <div className="mt-3 flex items-center gap-4 text-sm text-gray-400">
                      <span>{selectedSlide.script.length}자</span>
                      {selectedSlide.duration && (
                        <span>예상 시간: {formatTime(selectedSlide.duration)}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="bg-[#2a2a2a] border border-gray-800 rounded-lg p-6">
                <h3 className="font-semibold text-white mb-4">작업 단계</h3>

                <div className="grid grid-cols-2 gap-4">
                  {/* Generate Script */}
                  <button
                    onClick={onGenerateScript}
                    disabled={!canGenerateScript || isLoading}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
                  >
                    {isLoading && demoStep === "generating_script" ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <FileText className="w-5 h-5" />
                    )}
                    스크립트 생성
                  </button>

                  {/* Generate Audio */}
                  <button
                    onClick={onGenerateAudio}
                    disabled={!canGenerateAudio || isLoading}
                    className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
                  >
                    {isLoading && demoStep === "generating_audio" ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Volume2 className="w-5 h-5" />
                    )}
                    오디오 생성 (남성)
                  </button>

                  {/* Analyze Timing */}
                  <button
                    onClick={onAnalyzeTiming}
                    disabled={!canAnalyzeTiming || isLoading}
                    className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
                  >
                    {isLoading && demoStep === "analyzing_timing" ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Clock className="w-5 h-5" />
                    )}
                    타이밍 분석
                  </button>

                  {/* Generate Video */}
                  <button
                    onClick={onGenerateVideo}
                    disabled={!canGenerateVideo || isLoading}
                    className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
                  >
                    {isLoading && demoStep === "rendering_video" ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Video className="w-5 h-5" />
                    )}
                    영상 생성
                  </button>
                </div>

                {isLoading && (
                  <div className="mt-4 flex items-center justify-center gap-2 text-gray-400">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>{(demoStep && demoStepLabels[demoStep]) || "처리 중..."}</span>
                  </div>
                )}

                {/* Demo Voice Config */}
                {isDemoMode && (
                  <div className="mt-4 flex items-center justify-between px-4 py-3 bg-blue-900/20 border border-blue-700/30 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Volume2 className="w-4 h-4 text-blue-400" />
                      <span className="text-sm text-blue-300">
                        보이스: <span className="font-medium text-white">{voiceConfig.voiceLabel}</span>
                      </span>
                      <span className="text-sm text-blue-300">
                        톤: <span className="font-medium text-white">{voiceConfig.tone}</span>
                      </span>
                      <span className="text-sm text-blue-300">
                        총 시간: <span className="font-medium text-white">4분 10초</span>
                      </span>
                    </div>
                    <button
                      onClick={handleResetDemo}
                      className="px-3 py-1 text-sm text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg flex items-center gap-1 transition-colors"
                    >
                      <RefreshCw className="w-3 h-3" />
                      초기화
                    </button>
                  </div>
                )}
              </div>

              {/* Video Ready — Slide Player + MP4 Download */}
              {presentation.status === PresentationStatus.VIDEO_READY && (
                <div className="space-y-4">
                  {/* Completion Banner */}
                  <div className="bg-green-900/20 border border-green-700 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Check className="w-6 h-6 text-green-400" />
                        <div>
                          <h3 className="font-semibold text-green-300">영상 생성 완료!</h3>
                          <p className="text-green-400 text-xs mt-0.5">
                            프리뷰에서 확인 후 MP4로 다운로드하세요
                          </p>
                        </div>
                      </div>

                      {presentation.video_path && (
                        <a
                          href={isDemoMode ? "#" : `${API_BASE_URL}${presentation.video_path}`}
                          download={!isDemoMode}
                          onClick={isDemoMode ? (e) => { e.preventDefault(); alert("데모 모드에서는 MP4 다운로드가 제공되지 않습니다.\n실제 백엔드 연동 시 FFmpeg 렌더링 후 다운로드됩니다."); } : undefined}
                          className="px-5 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 transition-colors text-sm"
                        >
                          <Download className="w-4 h-4" />
                          MP4 다운로드
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Slide Player — 인트로/아웃트로 가상 슬라이드 포함 */}
                  <SlidePlayer
                    slides={(() => {
                      const tpl = brandTemplates.find(t => t.id === selectedTemplateId) as any;
                      let allSlides = [...presentation.slides];
                      if (tpl?.intro?.enabled && tpl.intro.script) {
                        const introDur = tpl.intro.duration || 3;
                        const firstStart = allSlides[0]?.start_time ?? 0;
                        allSlides.unshift({
                          slide_number: 0,
                          image_path: '/intro-placeholder.svg',
                          script: `[인트로] ${tpl.intro.script}`,
                          start_time: firstStart - introDur,
                          end_time: firstStart,
                          duration: introDur,
                        } as any);
                      }
                      if (tpl?.outro?.enabled && tpl.outro.script) {
                        const outroDur = tpl.outro.duration || 4;
                        const lastEnd = allSlides[allSlides.length - 1]?.end_time ?? 0;
                        allSlides.push({
                          slide_number: allSlides.length + 1,
                          image_path: '/outro-placeholder.svg',
                          script: `[아웃트로] ${tpl.outro.script}`,
                          start_time: lastEnd,
                          end_time: lastEnd + outroDur,
                          duration: outroDur,
                        } as any);
                      }
                      return allSlides;
                    })()}
                    localImages={isDemoMode}
                    apiBaseUrl={API_BASE_URL}
                    audioSrc={
                      isDemoMode
                        ? "/demo/audio/narration.mp3"
                        : presentation.audio_path
                          ? `${API_BASE_URL}${presentation.audio_path}`
                          : null
                    }
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
