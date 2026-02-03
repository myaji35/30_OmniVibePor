/**
 * Presentation API Type Definitions
 *
 * Backend API: /api/v1/presentation/*
 * Based on: backend/app/models/presentation.py
 */

// ==================== Enums ====================

export enum TransitionEffect {
  FADE = "fade",
  SLIDE = "slide",
  ZOOM = "zoom",
  NONE = "none",
}

export enum PresentationStatus {
  UPLOADED = "uploaded",
  SCRIPT_GENERATED = "script_generated",
  AUDIO_GENERATED = "audio_generated",
  TIMING_ANALYZED = "timing_analyzed",
  VIDEO_RENDERING = "video_rendering",
  VIDEO_READY = "video_ready",
  FAILED = "failed",
}

// ==================== Core Models ====================

export interface SlideInfo {
  slide_number: number;
  image_path: string;
  ocr_text?: string | null;
  script?: string | null;
  start_time?: number | null;
  end_time?: number | null;
  duration?: number | null;
}

export interface Presentation {
  presentation_id: string;
  project_id: string;
  pdf_path: string;
  total_slides: number;
  slides: SlideInfo[];
  full_script?: string | null;
  audio_path?: string | null;
  video_path?: string | null;
  status: PresentationStatus;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

// ==================== Request Models ====================

export interface PresentationUploadRequest {
  project_id: string;
  dpi?: number;
  lang?: string;
}

export interface GenerateScriptRequest {
  tone?: string;
  target_duration_per_slide?: number;
  include_slide_numbers?: boolean;
}

export interface GenerateAudioRequest {
  voice_id?: string | null;
  script?: string | null;
  model?: string;
}

export interface AnalyzeTimingRequest {
  audio_path?: string | null;
  manual_timings?: number[] | null;
}

export interface GenerateVideoRequest {
  transition_effect?: TransitionEffect;
  transition_duration?: number;
  bgm_path?: string | null;
  bgm_volume?: number;
}

// ==================== Response Models ====================

export interface PresentationUploadResponse {
  presentation_id: string;
  pdf_path: string;
  total_slides: number;
  slides: SlideInfo[];
  status: PresentationStatus;
}

export interface GenerateScriptResponse {
  presentation_id: string;
  full_script: string;
  slides: SlideInfo[];
  estimated_total_duration: number;
  status: PresentationStatus;
}

export interface GenerateAudioResponse {
  presentation_id: string;
  audio_path: string;
  duration: number;
  whisper_result: {
    text: string;
    duration: number;
    segments?: any[];
  };
  accuracy: number;
  status: PresentationStatus;
}

export interface AnalyzeTimingResponse {
  presentation_id: string;
  slides: SlideInfo[];
  total_duration: number;
  status: PresentationStatus;
}

export interface GenerateVideoResponse {
  presentation_id: string;
  video_path: string | null;
  celery_task_id: string;
  status: PresentationStatus;
  estimated_completion_time: number;
}

export interface PresentationDetailResponse {
  presentation_id: string;
  project_id: string;
  pdf_path: string;
  total_slides: number;
  slides: SlideInfo[];
  full_script?: string | null;
  audio_path?: string | null;
  video_path?: string | null;
  status: PresentationStatus;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface PresentationListItem {
  presentation_id: string;
  project_id: string;
  total_slides: number;
  status: PresentationStatus;
  created_at: string;
  updated_at: string;
  thumbnail_url?: string | null;
}

export interface PresentationListResponse {
  presentations: PresentationListItem[];
  total: number;
  page: number;
  page_size: number;
}
