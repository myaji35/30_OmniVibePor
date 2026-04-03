"use client";

/**
 * SlidePlayer - 슬라이드 프리뷰 플레이어
 *
 * 타이밍 데이터에 맞춰 슬라이드를 자동 전환하고
 * 나레이션 텍스트를 동기화하여 표시합니다.
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Maximize2,
  Minimize2,
  Volume2,
  VolumeX,
} from "lucide-react";
import type { SlideInfo } from "@/lib/types/presentation";

interface SlidePlayerProps {
  slides: SlideInfo[];
  /** true면 이미지 경로를 그대로 사용 (데모), false면 API_BASE_URL 프리픽스 */
  localImages?: boolean;
  apiBaseUrl?: string;
  autoPlay?: boolean;
  /** 나레이션 오디오 파일 경로 (mp3/wav). 있으면 오디오 기반 동기화 */
  audioSrc?: string | null;
}

export default function SlidePlayer({
  slides,
  localImages = true,
  apiBaseUrl = "",
  autoPlay = false,
  audioSrc = null,
}: SlidePlayerProps) {
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [currentTime, setCurrentTime] = useState(0);
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [audioReady, setAudioReady] = useState(false);

  const playerRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);
  const pausedTimeRef = useRef<number>(0);

  const hasAudio = !!audioSrc;

  const totalDuration =
    slides.length > 0
      ? (slides[slides.length - 1].end_time ?? 0)
      : 0;

  // Find current slide based on time
  const findSlideIndex = useCallback(
    (time: number): number => {
      for (let i = slides.length - 1; i >= 0; i--) {
        const start = slides[i].start_time ?? 0;
        if (time >= start) return i;
      }
      return 0;
    },
    [slides]
  );

  // Audio element event handlers
  useEffect(() => {
    if (!audioRef.current || !hasAudio) return;
    const audio = audioRef.current;

    const onCanPlay = () => setAudioReady(true);
    const onEnded = () => {
      setIsPlaying(false);
      setCurrentTime(totalDuration);
    };

    audio.addEventListener("canplaythrough", onCanPlay);
    audio.addEventListener("ended", onEnded);
    return () => {
      audio.removeEventListener("canplaythrough", onCanPlay);
      audio.removeEventListener("ended", onEnded);
    };
  }, [hasAudio, totalDuration]);

  // Play/pause logic — audio mode vs timer mode
  useEffect(() => {
    if (hasAudio && audioRef.current) {
      // === Audio-driven sync ===
      if (isPlaying) {
        audioRef.current.play().catch(() => {});
        timerRef.current = setInterval(() => {
          const t = audioRef.current!.currentTime;
          setCurrentTime(t);
          setCurrentSlideIndex(findSlideIndex(t));
        }, 100);
      } else {
        audioRef.current.pause();
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
      }
    } else {
      // === Timer-driven sync (no audio) ===
      if (isPlaying) {
        startTimeRef.current = Date.now() - pausedTimeRef.current * 1000;

        timerRef.current = setInterval(() => {
          const elapsed = (Date.now() - startTimeRef.current) / 1000;

          if (elapsed >= totalDuration) {
            setCurrentTime(totalDuration);
            setIsPlaying(false);
            if (timerRef.current) clearInterval(timerRef.current);
            return;
          }

          setCurrentTime(elapsed);
          setCurrentSlideIndex(findSlideIndex(elapsed));
        }, 100);
      } else {
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        pausedTimeRef.current = currentTime;
      }
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, totalDuration, findSlideIndex, hasAudio]);

  // Controls
  const handlePlayPause = () => setIsPlaying((prev) => !prev);

  const handlePrevSlide = () => {
    const newIndex = Math.max(0, currentSlideIndex - 1);
    seekTo(slides[newIndex].start_time ?? 0);
  };

  const handleNextSlide = () => {
    const newIndex = Math.min(slides.length - 1, currentSlideIndex + 1);
    seekTo(slides[newIndex].start_time ?? 0);
  };

  const handleToggleMute = () => {
    setIsMuted((prev) => {
      if (audioRef.current) audioRef.current.muted = !prev;
      return !prev;
    });
  };

  const seekTo = (newTime: number) => {
    setCurrentTime(newTime);
    setCurrentSlideIndex(findSlideIndex(newTime));
    pausedTimeRef.current = newTime;
    if (hasAudio && audioRef.current) {
      audioRef.current.currentTime = newTime;
    } else if (isPlaying) {
      startTimeRef.current = Date.now() - newTime * 1000;
    }
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    seekTo(ratio * totalDuration);
  };

  const handleSlideClick = (index: number) => {
    seekTo(slides[index].start_time ?? 0);
  };

  const handleFullscreen = () => {
    if (!playerRef.current) return;
    if (!isFullscreen) {
      playerRef.current.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
    setIsFullscreen(!isFullscreen);
  };

  // Format time
  const fmt = (seconds: number): string => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const currentSlide = slides[currentSlideIndex];
  const imageSrc = localImages
    ? currentSlide?.image_path
    : `${apiBaseUrl}${currentSlide?.image_path}`;

  // Progress within current slide (0~1)
  const slideStart = currentSlide?.start_time ?? 0;
  const slideEnd = currentSlide?.end_time ?? 0;
  const slideDuration = slideEnd - slideStart;
  const slideProgress =
    slideDuration > 0
      ? Math.min(1, (currentTime - slideStart) / slideDuration)
      : 0;

  if (slides.length === 0) return null;

  return (
    <>
      {/* Hidden audio element */}
      {hasAudio && (
        <audio ref={audioRef} src={audioSrc!} preload="auto" muted={isMuted} />
      )}
    <div
      ref={playerRef}
      className={`bg-[#111] rounded-lg overflow-hidden border border-gray-800 ${
        isFullscreen ? "fixed inset-0 z-50 rounded-none" : ""
      }`}
    >
      {/* Main Display */}
      <div className="relative">
        {/* Slide Image */}
        <div
          className={`bg-black flex items-center justify-center ${
            isFullscreen ? "h-[calc(100vh-180px)]" : "h-[480px]"
          }`}
        >
          <img
            src={imageSrc}
            alt={`Slide ${currentSlide?.slide_number}`}
            className="max-w-full max-h-full object-contain transition-opacity duration-300"
          />
        </div>

        {/* Slide Counter Overlay */}
        <div className="absolute top-4 right-4 px-3 py-1 bg-black/70 rounded-full text-white text-sm font-medium">
          {currentSlideIndex + 1} / {slides.length}
        </div>

        {/* Current Slide Progress Bar (thin line at bottom of image) */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-800">
          <div
            className="h-full bg-purple-500 transition-all duration-100"
            style={{ width: `${slideProgress * 100}%` }}
          />
        </div>
      </div>

      {/* Narration Text */}
      <div className="px-6 py-4 bg-[#1a1a1a] border-t border-gray-800 min-h-[80px]">
        {currentSlide?.script ? (
          <p className="text-gray-200 text-sm leading-relaxed">
            {currentSlide.script}
          </p>
        ) : (
          <p className="text-gray-500 text-sm italic">
            나레이션 스크립트가 없습니다
          </p>
        )}
      </div>

      {/* Timeline & Controls */}
      <div className="px-6 py-3 bg-[#0d0d0d] border-t border-gray-800">
        {/* Seekbar */}
        <div
          className="relative w-full h-6 cursor-pointer group mb-2"
          onClick={handleSeek}
        >
          {/* Track background */}
          <div className="absolute top-2.5 left-0 right-0 h-1.5 bg-gray-700 rounded-full">
            {/* Played */}
            <div
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
              style={{
                width: `${totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0}%`,
              }}
            />
          </div>

          {/* Slide markers */}
          {slides.map((slide, i) => {
            const pos =
              totalDuration > 0
                ? ((slide.start_time ?? 0) / totalDuration) * 100
                : 0;
            return (
              <div
                key={i}
                className={`absolute top-1 w-0.5 h-4 rounded-full transition-colors ${
                  i <= currentSlideIndex ? "bg-purple-400" : "bg-gray-600"
                }`}
                style={{ left: `${pos}%` }}
                title={`슬라이드 ${i + 1}`}
              />
            );
          })}

          {/* Playhead */}
          <div
            className="absolute top-1 w-3 h-3 bg-white rounded-full shadow-lg transform -translate-x-1/2 group-hover:scale-125 transition-transform"
            style={{
              left: `${totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0}%`,
            }}
          />
        </div>

        {/* Controls row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={handlePrevSlide}
              className="p-2 text-gray-400 hover:text-white transition-colors"
              title="이전 슬라이드"
            >
              <SkipBack className="w-4 h-4" />
            </button>

            <button
              onClick={handlePlayPause}
              className="p-2 bg-purple-600 text-white rounded-full hover:bg-purple-700 transition-colors"
              title={isPlaying ? "일시정지" : "재생"}
            >
              {isPlaying ? (
                <Pause className="w-5 h-5" />
              ) : (
                <Play className="w-5 h-5 ml-0.5" />
              )}
            </button>

            <button
              onClick={handleNextSlide}
              className="p-2 text-gray-400 hover:text-white transition-colors"
              title="다음 슬라이드"
            >
              <SkipForward className="w-4 h-4" />
            </button>

            <span className="text-sm text-gray-400 ml-2 font-mono">
              {fmt(currentTime)} / {fmt(totalDuration)}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">
              슬라이드 {currentSlideIndex + 1}: {fmt(slideDuration)}
            </span>
            {hasAudio && (
              <button
                onClick={handleToggleMute}
                className="p-2 text-gray-400 hover:text-white transition-colors"
                title={isMuted ? "음소거 해제" : "음소거"}
              >
                {isMuted ? (
                  <VolumeX className="w-4 h-4" />
                ) : (
                  <Volume2 className="w-4 h-4" />
                )}
              </button>
            )}
            <button
              onClick={handleFullscreen}
              className="p-2 text-gray-400 hover:text-white transition-colors"
              title={isFullscreen ? "전체화면 종료" : "전체화면"}
            >
              {isFullscreen ? (
                <Minimize2 className="w-4 h-4" />
              ) : (
                <Maximize2 className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Slide Thumbnails Strip */}
      <div className="px-4 py-3 bg-[#0a0a0a] border-t border-gray-800 flex gap-2 overflow-x-auto">
        {slides.map((slide, i) => (
          <button
            key={i}
            onClick={() => handleSlideClick(i)}
            className={`flex-shrink-0 w-20 h-12 rounded border-2 overflow-hidden transition-all ${
              i === currentSlideIndex
                ? "border-purple-500 ring-1 ring-purple-500/50"
                : i < currentSlideIndex
                  ? "border-gray-600 opacity-60"
                  : "border-gray-700 opacity-40"
            }`}
          >
            <img
              src={localImages ? slide.image_path : `${apiBaseUrl}${slide.image_path}`}
              alt={`Slide ${slide.slide_number}`}
              className="w-full h-full object-cover"
            />
          </button>
        ))}
      </div>
    </div>
    </>
  );
}
