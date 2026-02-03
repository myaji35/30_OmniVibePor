"use client";

/**
 * ProductionContext - 영상 제작 워크플로우 전역 상태 관리
 *
 * REALPLAN.md Phase 1.4 구현
 *
 * Writer → Director → Marketer → Deployment 단계별 데이터 관리
 */

import React, { createContext, useContext, useReducer, ReactNode, useCallback } from 'react';

// ==================== Types ====================

export type ProductionStep = 'writer' | 'director' | 'marketer' | 'deployment';

export interface ScriptData {
  script_id: string;
  content: string;
  platform: string;
  word_count: number;
  estimated_duration: number;
  version: number;
  created_at: string;
  selected?: boolean;
}

export interface AudioData {
  audio_id: string;
  file_path: string;
  voice_id: string;
  duration: number;
  stt_accuracy: number;
  retry_count: number;
  created_at: string;
}

export interface VideoData {
  video_id: string;
  file_path: string;
  duration: number;
  resolution: string;
  format: string;
  veo_prompt: string;
  lipsync_enabled: boolean;
  created_at: string;
}

export interface ProductionState {
  // 프로젝트 정보
  projectId: string | null;
  projectTitle: string | null;
  projectTopic: string | null;
  platform: string | null;

  // 현재 단계
  currentStep: ProductionStep;

  // 단계별 데이터
  script: ScriptData | null;
  audio: AudioData | null;
  video: VideoData | null;

  // 작업 상태
  isLoading: boolean;
  error: string | null;

  // 진행률 (0-100)
  progress: number;
}

// ==================== Actions ====================

type ProductionAction =
  | { type: 'SET_PROJECT'; payload: { projectId: string; title: string; topic: string; platform: string } }
  | { type: 'SET_STEP'; payload: ProductionStep }
  | { type: 'SET_SCRIPT'; payload: ScriptData }
  | { type: 'SET_AUDIO'; payload: AudioData }
  | { type: 'SET_VIDEO'; payload: VideoData }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_PROGRESS'; payload: number }
  | { type: 'RESET_PRODUCTION' };

// ==================== Reducer ====================

const initialState: ProductionState = {
  projectId: null,
  projectTitle: null,
  projectTopic: null,
  platform: null,
  currentStep: 'writer',
  script: null,
  audio: null,
  video: null,
  isLoading: false,
  error: null,
  progress: 0,
};

function productionReducer(state: ProductionState, action: ProductionAction): ProductionState {
  switch (action.type) {
    case 'SET_PROJECT':
      return {
        ...state,
        projectId: action.payload.projectId,
        projectTitle: action.payload.title,
        projectTopic: action.payload.topic,
        platform: action.payload.platform,
        progress: 10, // 프로젝트 생성 10%
      };

    case 'SET_STEP':
      return {
        ...state,
        currentStep: action.payload,
        error: null, // 단계 전환 시 에러 초기화
      };

    case 'SET_SCRIPT':
      return {
        ...state,
        script: action.payload,
        currentStep: 'director', // 스크립트 완료 시 자동으로 다음 단계로
        progress: 35, // Writer 완료 35%
      };

    case 'SET_AUDIO':
      return {
        ...state,
        audio: action.payload,
        progress: 60, // Director (Audio) 완료 60%
      };

    case 'SET_VIDEO':
      return {
        ...state,
        video: action.payload,
        progress: 85, // Director (Video) 완료 85%
      };

    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };

    case 'SET_PROGRESS':
      return {
        ...state,
        progress: Math.min(100, Math.max(0, action.payload)),
      };

    case 'RESET_PRODUCTION':
      return initialState;

    default:
      return state;
  }
}

// ==================== Context ====================

interface ProductionContextValue {
  state: ProductionState;

  // Actions
  setProject: (projectId: string, title: string, topic: string, platform: string) => void;
  setStep: (step: ProductionStep) => void;
  setScript: (script: ScriptData) => void;
  setAudio: (audio: AudioData) => void;
  setVideo: (video: VideoData) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setProgress: (progress: number) => void;
  resetProduction: () => void;

  // Computed properties
  canProceedToDirector: boolean;
  canProceedToMarketer: boolean;
  canProceedToDeployment: boolean;
}

const ProductionContext = createContext<ProductionContextValue | undefined>(undefined);

// ==================== Provider ====================

interface ProductionProviderProps {
  children: ReactNode;
}

export function ProductionProvider({ children }: ProductionProviderProps) {
  const [state, dispatch] = useReducer(productionReducer, initialState);

  // Actions
  const setProject = useCallback((projectId: string, title: string, topic: string, platform: string) => {
    dispatch({ type: 'SET_PROJECT', payload: { projectId, title, topic, platform } });
  }, []);

  const setStep = useCallback((step: ProductionStep) => {
    dispatch({ type: 'SET_STEP', payload: step });
  }, []);

  const setScript = useCallback((script: ScriptData) => {
    dispatch({ type: 'SET_SCRIPT', payload: script });
  }, []);

  const setAudio = useCallback((audio: AudioData) => {
    dispatch({ type: 'SET_AUDIO', payload: audio });
  }, []);

  const setVideo = useCallback((video: VideoData) => {
    dispatch({ type: 'SET_VIDEO', payload: video });
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  }, []);

  const setError = useCallback((error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  }, []);

  const setProgress = useCallback((progress: number) => {
    dispatch({ type: 'SET_PROGRESS', payload: progress });
  }, []);

  const resetProduction = useCallback(() => {
    dispatch({ type: 'RESET_PRODUCTION' });
  }, []);

  // Computed properties
  const canProceedToDirector = state.script !== null;
  const canProceedToMarketer = state.audio !== null && state.video !== null;
  const canProceedToDeployment = canProceedToMarketer; // 추후 썸네일 조건 추가

  const value: ProductionContextValue = {
    state,
    setProject,
    setStep,
    setScript,
    setAudio,
    setVideo,
    setLoading,
    setError,
    setProgress,
    resetProduction,
    canProceedToDirector,
    canProceedToMarketer,
    canProceedToDeployment,
  };

  return (
    <ProductionContext.Provider value={value}>
      {children}
    </ProductionContext.Provider>
  );
}

// ==================== Hook ====================

export function useProduction() {
  const context = useContext(ProductionContext);

  if (context === undefined) {
    throw new Error('useProduction must be used within a ProductionProvider');
  }

  return context;
}

// ==================== Helper Functions ====================

/**
 * 단계별 진행률 계산
 */
export function calculateStepProgress(step: ProductionStep): number {
  const stepProgress: Record<ProductionStep, number> = {
    writer: 25,
    director: 50,
    marketer: 75,
    deployment: 100,
  };

  return stepProgress[step];
}

/**
 * 단계별 한글 이름
 */
export function getStepName(step: ProductionStep): string {
  const stepNames: Record<ProductionStep, string> = {
    writer: '작가',
    director: '감독',
    marketer: '마케터',
    deployment: '배포',
  };

  return stepNames[step];
}

/**
 * 단계별 설명
 */
export function getStepDescription(step: ProductionStep): string {
  const stepDescriptions: Record<ProductionStep, string> = {
    writer: '주제를 입력하면 AI가 스크립트를 작성합니다',
    director: '스크립트를 오디오와 영상으로 변환합니다',
    marketer: '썸네일과 카피를 생성합니다',
    deployment: '플랫폼별로 최적화하여 배포합니다',
  };

  return stepDescriptions[step];
}
