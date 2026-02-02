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

  // Narration editing
  const [editingSlideIndex, setEditingSlideIndex] = useState<number | null>(null);
  const [editedScript, setEditedScript] = useState<string>("");

  // File input ref
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load presentation data
  useEffect(() => {
    if (presentationId) {
      loadPresentation(presentationId);
    }
  }, [presentationId]);

  // ==================== API Functions ====================

  const loadPresentation = async (id: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.get(`${API_BASE_URL}/api/v1/presentation/${id}`);
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

      const response = await axios.post(
        `${API_BASE_URL}/api/v1/presentation/upload`,
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
        `${API_BASE_URL}/api/v1/presentation/${presentationId}/generate-script`,
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
        `${API_BASE_URL}/api/v1/presentation/${presentationId}/generate-audio`,
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
        `${API_BASE_URL}/api/v1/presentation/${presentationId}/analyze-timing`,
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
        `${API_BASE_URL}/api/v1/presentation/${presentationId}/generate-video`,
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
        const response = await axios.get(`${API_BASE_URL}/api/v1/presentation/${id}`);
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

  const selectedSlide = presentation?.slides[selectedSlideIndex];

  // ==================== Render ====================

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">프리젠테이션 모드</h1>
              <p className="text-gray-600 mt-1">PDF를 업로드하여 나레이션 영상을 생성하세요</p>
            </div>

            {presentation && (
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                  {STATUS_LABELS[presentation.status]}
                </span>
                <span className="text-sm text-gray-600">
                  {presentation.total_slides}개 슬라이드
                </span>
              </div>
            )}
          </div>

          {/* Progress Bar */}
          {presentation && (
            <div className="mt-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">전체 진행률</span>
                <span className="text-sm font-medium text-gray-900">
                  {Math.round(getProgressPercentage())}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${getProgressPercentage()}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-red-900">오류 발생</h3>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Upload Section */}
        {!presentation && (
          <div className="bg-white border border-gray-200 rounded-lg p-8">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="hidden"
            />

            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <Upload className="w-8 h-8 text-blue-600" />
              </div>

              <h3 className="text-lg font-semibold text-gray-900 mb-2">PDF 파일 업로드</h3>
              <p className="text-gray-600 text-sm mb-6">
                프리젠테이션 PDF를 업로드하면 자동으로 슬라이드를 분석합니다
              </p>

              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 mx-auto"
              >
                {isLoading ? (
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
            </div>
          </div>
        )}

        {/* Main Content */}
        {presentation && (
          <div className="grid grid-cols-12 gap-6">
            {/* Left Sidebar - Slide List */}
            <div className="col-span-3 bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
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
                        ? "border-blue-600 bg-blue-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Thumbnail */}
                      <div className="w-16 h-12 bg-gray-100 rounded flex-shrink-0 overflow-hidden">
                        <img
                          src={`${API_BASE_URL}${slide.image_path}`}
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
                          <span className="font-medium text-gray-900">
                            #{slide.slide_number}
                          </span>
                          {slide.script && (
                            <Check className="w-4 h-4 text-green-600" />
                          )}
                        </div>

                        {slide.duration !== null && slide.duration !== undefined && (
                          <div className="flex items-center gap-1 text-xs text-gray-600">
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
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    슬라이드 #{selectedSlide?.slide_number}
                  </h3>

                  {selectedSlide?.start_time !== null &&
                    selectedSlide?.start_time !== undefined && (
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span>시작: {formatTime(selectedSlide.start_time)}</span>
                        <span>종료: {formatTime(selectedSlide.end_time)}</span>
                        <span className="font-medium">
                          길이: {formatTime(selectedSlide.duration)}
                        </span>
                      </div>
                    )}
                </div>

                {/* Large Preview */}
                <div className="bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center h-96">
                  {selectedSlide && (
                    <img
                      src={`${API_BASE_URL}${selectedSlide.image_path}`}
                      alt={`Slide ${selectedSlide.slide_number}`}
                      className="max-w-full max-h-full object-contain"
                      onError={(e) => {
                        e.currentTarget.parentElement!.innerHTML =
                          '<div class="text-gray-400">이미지를 불러올 수 없습니다</div>';
                      }}
                    />
                  )}
                </div>
              </div>

              {/* Narration Editor */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    <Volume2 className="w-5 h-5" />
                    나레이션 스크립트
                  </h3>

                  {selectedSlide?.script && editingSlideIndex !== selectedSlideIndex && (
                    <button
                      onClick={() => handleEditSlide(selectedSlideIndex)}
                      className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-lg flex items-center gap-1"
                    >
                      <Edit3 className="w-4 h-4" />
                      편집
                    </button>
                  )}
                </div>

                {!selectedSlide?.script ? (
                  <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
                    <p className="text-gray-500 mb-4">
                      스크립트가 아직 생성되지 않았습니다
                    </p>
                  </div>
                ) : editingSlideIndex === selectedSlideIndex ? (
                  <div className="space-y-4">
                    <textarea
                      value={editedScript}
                      onChange={(e) => setEditedScript(e.target.value)}
                      className="w-full h-40 px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="나레이션 스크립트를 입력하세요..."
                    />

                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">
                        {editedScript.length}자 | 예상 시간:{" "}
                        {Math.round((editedScript.length / 300) * 60)}초
                      </span>

                      <div className="flex gap-2">
                        <button
                          onClick={handleCancelEdit}
                          className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                        >
                          취소
                        </button>
                        <button
                          onClick={handleSaveSlideScript}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                        >
                          <Save className="w-4 h-4" />
                          저장
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <p className="text-gray-700 whitespace-pre-wrap">{selectedSlide.script}</p>

                    <div className="mt-3 flex items-center gap-4 text-sm text-gray-600">
                      <span>{selectedSlide.script.length}자</span>
                      {selectedSlide.duration && (
                        <span>예상 시간: {formatTime(selectedSlide.duration)}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="font-semibold text-gray-900 mb-4">작업 단계</h3>

                <div className="grid grid-cols-2 gap-4">
                  {/* Generate Script */}
                  <button
                    onClick={handleGenerateScript}
                    disabled={!canGenerateScript || isLoading}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <FileText className="w-5 h-5" />
                    스크립트 생성
                  </button>

                  {/* Generate Audio */}
                  <button
                    onClick={handleGenerateAudio}
                    disabled={!canGenerateAudio || isLoading}
                    className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Volume2 className="w-5 h-5" />
                    오디오 생성
                  </button>

                  {/* Analyze Timing */}
                  <button
                    onClick={handleAnalyzeTiming}
                    disabled={!canAnalyzeTiming || isLoading}
                    className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Clock className="w-5 h-5" />
                    타이밍 분석
                  </button>

                  {/* Generate Video */}
                  <button
                    onClick={handleGenerateVideo}
                    disabled={!canGenerateVideo || isLoading}
                    className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Video className="w-5 h-5" />
                    영상 생성
                  </button>
                </div>

                {isLoading && (
                  <div className="mt-4 flex items-center justify-center gap-2 text-gray-600">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>처리 중...</span>
                  </div>
                )}
              </div>

              {/* Video Ready */}
              {presentation.status === PresentationStatus.VIDEO_READY &&
                presentation.video_path && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Check className="w-8 h-8 text-green-600" />
                        <div>
                          <h3 className="font-semibold text-green-900">영상 생성 완료!</h3>
                          <p className="text-green-700 text-sm mt-1">
                            프리젠테이션 영상이 성공적으로 생성되었습니다
                          </p>
                        </div>
                      </div>

                      <a
                        href={`${API_BASE_URL}${presentation.video_path}`}
                        download
                        className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                      >
                        <Download className="w-5 h-5" />
                        다운로드
                      </a>
                    </div>
                  </div>
                )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
