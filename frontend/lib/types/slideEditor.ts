/**
 * Type definitions for SlideEditor component
 *
 * Usage:
 * import { SlideData, SlideTiming, BGMSettings, TransitionEffect } from '@/lib/types/slideEditor';
 */

export interface SlideData {
  slide_id: string;
  slide_number: number;
  image_path: string;
  extracted_text: string;
  title?: string;
}

export interface SlideTiming {
  start_time: number;  // 초
  end_time: number;    // 초
  duration: number;    // 초 (read-only, calculated)
}

export interface BGMSettings {
  enabled: boolean;
  volume: number;           // 0.0-1.0
  fade_in_duration: number; // 초
  fade_out_duration: number; // 초
  custom_file_path?: string;
}

export type TransitionEffect = 'fade' | 'slide' | 'zoom';

export interface SlideEditorProps {
  slide: SlideData;
  timing: SlideTiming;
  transitionEffect: TransitionEffect;
  bgmSettings?: BGMSettings;
  adjacentSlides?: {
    previous?: { end_time: number };
    next?: { start_time: number };
  };
  whisperTiming?: {
    start_time: number;
    end_time: number;
  };
  onTimingChange?: (start: number, end: number) => void;
  onTransitionChange?: (effect: TransitionEffect) => void;
  onBGMChange?: (settings: BGMSettings) => void;
}

// API Request/Response Types

export interface UpdateSlideTimingRequest {
  slide_id: string;
  start_time: number;
  end_time: number;
}

export interface UpdateSlideTimingResponse {
  success: boolean;
  slide_id: string;
  timing: SlideTiming;
}

export interface UpdateSlideTransitionRequest {
  slide_id: string;
  transition_effect: TransitionEffect;
}

export interface UpdateSlideTransitionResponse {
  success: boolean;
  slide_id: string;
  transition_effect: TransitionEffect;
}

export interface UpdateSlideBGMRequest {
  slide_id: string;
  bgm_settings: BGMSettings;
}

export interface UpdateSlideBGMResponse {
  success: boolean;
  slide_id: string;
  bgm_settings: BGMSettings;
}

export interface GetSlideDataResponse {
  slide: SlideData;
  timing: SlideTiming;
  transition_effect: TransitionEffect;
  bgm_settings: BGMSettings;
  whisper_timing?: {
    start_time: number;
    end_time: number;
  };
}

// Validation Types

export interface TimingValidationResult {
  valid: boolean;
  error?: string;
}

export interface SlideEditorState {
  slide: SlideData;
  timing: SlideTiming;
  transitionEffect: TransitionEffect;
  bgmSettings: BGMSettings;
  validationError: string | null;
  isLoading: boolean;
  isSaving: boolean;
}
