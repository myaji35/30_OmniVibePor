"use client";

/**
 * SlideEditor Example Usage
 *
 * 이 파일은 SlideEditor 컴포넌트를 PresentationMode에 통합하는 예제입니다.
 */

import React, { useState, useEffect } from 'react';
import SlideEditor from './SlideEditor';
import {
  SlideData,
  SlideTiming,
  TransitionEffect,
  BGMSettings,
} from '@/lib/types/slideEditor';

export default function SlideEditorExample() {
  // State
  const [slides, setSlides] = useState<SlideData[]>([]);
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [timings, setTimings] = useState<Map<string, SlideTiming>>(new Map());
  const [transitions, setTransitions] = useState<Map<string, TransitionEffect>>(new Map());
  const [bgmSettings, setBgmSettings] = useState<Map<string, BGMSettings>>(new Map());
  const [isLoading, setIsLoading] = useState(true);

  const projectId = 'example-project-123';

  // Load slides from API
  useEffect(() => {
    loadSlides();
  }, [projectId]);

  const loadSlides = async () => {
    setIsLoading(true);
    try {
      // Example API call (replace with actual endpoint)
      const response = await fetch(
        `http://localhost:8000/api/v1/projects/${projectId}/slides`
      );
      const data = await response.json();

      setSlides(data.slides);

      // Initialize timings, transitions, and BGM settings
      const timingsMap = new Map();
      const transitionsMap = new Map();
      const bgmMap = new Map();

      data.slides.forEach((slide: any) => {
        timingsMap.set(slide.slide_id, {
          start_time: slide.start_time || 0,
          end_time: slide.end_time || 5,
          duration: (slide.end_time || 5) - (slide.start_time || 0),
        });

        transitionsMap.set(
          slide.slide_id,
          slide.transition_effect || 'fade'
        );

        bgmMap.set(slide.slide_id, {
          enabled: slide.bgm_enabled || false,
          volume: slide.bgm_volume || 0.5,
          fade_in_duration: slide.bgm_fade_in || 1,
          fade_out_duration: slide.bgm_fade_out || 1,
        });
      });

      setTimings(timingsMap);
      setTransitions(transitionsMap);
      setBgmSettings(bgmMap);
    } catch (error) {
      console.error('Failed to load slides:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle timing change
  const handleTimingChange = async (slideId: string, start: number, end: number) => {
    const newTiming: SlideTiming = {
      start_time: start,
      end_time: end,
      duration: end - start,
    };

    // Update local state
    setTimings((prev) => new Map(prev).set(slideId, newTiming));

    // Save to API
    try {
      await fetch(`http://localhost:8000/api/v1/slides/${slideId}/timing`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ start_time: start, end_time: end }),
      });
    } catch (error) {
      console.error('Failed to save timing:', error);
    }
  };

  // Handle transition change
  const handleTransitionChange = async (
    slideId: string,
    effect: TransitionEffect
  ) => {
    // Update local state
    setTransitions((prev) => new Map(prev).set(slideId, effect));

    // Save to API
    try {
      await fetch(`http://localhost:8000/api/v1/slides/${slideId}/transition`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transition_effect: effect }),
      });
    } catch (error) {
      console.error('Failed to save transition:', error);
    }
  };

  // Handle BGM change
  const handleBGMChange = async (slideId: string, settings: BGMSettings) => {
    // Update local state
    setBgmSettings((prev) => new Map(prev).set(slideId, settings));

    // Save to API
    try {
      await fetch(`http://localhost:8000/api/v1/slides/${slideId}/bgm`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bgm_settings: settings }),
      });
    } catch (error) {
      console.error('Failed to save BGM settings:', error);
    }
  };

  // Get adjacent slides for validation
  const getAdjacentSlides = (index: number) => {
    const previous =
      index > 0
        ? { end_time: timings.get(slides[index - 1].slide_id)?.end_time || 0 }
        : undefined;

    const next =
      index < slides.length - 1
        ? { start_time: timings.get(slides[index + 1].slide_id)?.start_time || 0 }
        : undefined;

    return { previous, next };
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (slides.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-gray-600 text-lg">슬라이드가 없습니다</p>
          <p className="text-gray-500 text-sm mt-2">
            먼저 슬라이드를 생성해주세요
          </p>
        </div>
      </div>
    );
  }

  const currentSlide = slides[currentSlideIndex];
  const currentTiming = timings.get(currentSlide.slide_id) || {
    start_time: 0,
    end_time: 5,
    duration: 5,
  };
  const currentTransition = transitions.get(currentSlide.slide_id) || 'fade';
  const currentBGM = bgmSettings.get(currentSlide.slide_id);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            프레젠테이션 에디터
          </h1>
          <p className="text-gray-600 mt-2">
            슬라이드 타이밍, 전환 효과, BGM을 조정하세요
          </p>
        </div>

        {/* Slide Navigation */}
        <div className="mb-6 flex items-center gap-4">
          <button
            onClick={() => setCurrentSlideIndex(Math.max(0, currentSlideIndex - 1))}
            disabled={currentSlideIndex === 0}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← 이전 슬라이드
          </button>
          <span className="text-gray-700 font-medium">
            {currentSlideIndex + 1} / {slides.length}
          </span>
          <button
            onClick={() =>
              setCurrentSlideIndex(Math.min(slides.length - 1, currentSlideIndex + 1))
            }
            disabled={currentSlideIndex === slides.length - 1}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            다음 슬라이드 →
          </button>
        </div>

        {/* SlideEditor Component */}
        <SlideEditor
          slide={currentSlide}
          timing={currentTiming}
          transitionEffect={currentTransition}
          bgmSettings={currentBGM}
          adjacentSlides={getAdjacentSlides(currentSlideIndex)}
          whisperTiming={
            currentSlide.whisper_start_time && currentSlide.whisper_end_time
              ? {
                  start_time: currentSlide.whisper_start_time,
                  end_time: currentSlide.whisper_end_time,
                }
              : undefined
          }
          onTimingChange={(start, end) =>
            handleTimingChange(currentSlide.slide_id, start, end)
          }
          onTransitionChange={(effect) =>
            handleTransitionChange(currentSlide.slide_id, effect)
          }
          onBGMChange={(settings) =>
            handleBGMChange(currentSlide.slide_id, settings)
          }
        />

        {/* Timeline Preview */}
        <div className="mt-6 p-6 bg-white rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            타임라인 프리뷰
          </h3>
          <div className="space-y-2">
            {slides.map((slide, index) => {
              const timing = timings.get(slide.slide_id);
              const transition = transitions.get(slide.slide_id);
              if (!timing) return null;

              return (
                <div
                  key={slide.slide_id}
                  className={`p-3 border rounded cursor-pointer transition-colors ${
                    index === currentSlideIndex
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300 hover:bg-gray-50'
                  }`}
                  onClick={() => setCurrentSlideIndex(index)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-semibold text-gray-700">
                        #{slide.slide_number}
                      </span>
                      <span className="text-sm text-gray-600">
                        {slide.title || slide.extracted_text.slice(0, 30) + '...'}
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-xs text-gray-500">
                        {transition === 'fade' ? '🌫️' : transition === 'slide' ? '➡️' : '🔍'}{' '}
                        {transition}
                      </span>
                      <span className="text-xs font-medium text-gray-700">
                        {timing.start_time.toFixed(1)}s - {timing.end_time.toFixed(1)}s
                      </span>
                      <span className="text-xs text-gray-500">
                        ({timing.duration.toFixed(1)}s)
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Export Button */}
        <div className="mt-6 flex justify-end">
          <button className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium">
            🎬 프레젠테이션 영상 생성
          </button>
        </div>
      </div>
    </div>
  );
}
