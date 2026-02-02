'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';

// ===========================
// TypeScript Interfaces
// ===========================

interface Section {
  section_id: string;
  type: 'hook' | 'body' | 'cta';
  start_time: number;
  end_time: number;
  duration: number;
  thumbnail_url?: string;
}

interface VideoTimelineProps {
  projectId: string;
  videoUrl: string;
  duration: number;  // 초 단위
  sections: Section[];
  onSectionClick?: (sectionId: string) => void;
  onTimeUpdate?: (currentTime: number) => void;
}

// ===========================
// Section Colors
// ===========================

const SECTION_COLORS: Record<Section['type'], string> = {
  hook: '#EF4444',  // 빨강
  body: '#3B82F6',  // 파랑
  cta: '#10B981',   // 초록
};

const SECTION_LABELS: Record<Section['type'], string> = {
  hook: '훅',
  body: '본문',
  cta: 'CTA',
};

// ===========================
// Main Component
// ===========================

export default function VideoTimeline({
  projectId,
  videoUrl,
  duration,
  sections,
  onSectionClick,
  onTimeUpdate,
}: VideoTimelineProps) {
  // ===========================
  // State Management
  // ===========================

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1); // 1 = 100%
  const [isDraggingPlayhead, setIsDraggingPlayhead] = useState(false);

  // ===========================
  // Refs
  // ===========================

  const videoRef = useRef<HTMLVideoElement>(null);
  const timelineCanvasRef = useRef<HTMLCanvasElement>(null);
  const timelineContainerRef = useRef<HTMLDivElement>(null);

  // ===========================
  // Video Control Handlers
  // ===========================

  const togglePlayPause = useCallback(() => {
    if (!videoRef.current) return;

    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const handleVolumeChange = useCallback((newVolume: number) => {
    if (!videoRef.current) return;
    videoRef.current.volume = newVolume;
    setVolume(newVolume);
    if (newVolume === 0) {
      setIsMuted(true);
    } else {
      setIsMuted(false);
    }
  }, []);

  const toggleMute = useCallback(() => {
    if (!videoRef.current) return;
    const newMutedState = !isMuted;
    videoRef.current.muted = newMutedState;
    setIsMuted(newMutedState);
  }, [isMuted]);

  const seekTo = useCallback((time: number) => {
    if (!videoRef.current) return;
    const clampedTime = Math.max(0, Math.min(time, duration));
    videoRef.current.currentTime = clampedTime;
    setCurrentTime(clampedTime);
    onTimeUpdate?.(clampedTime);
  }, [duration, onTimeUpdate]);

  // ===========================
  // Timeline Interaction
  // ===========================

  const handleTimelineClick = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!timelineCanvasRef.current) return;

    const rect = timelineCanvasRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const timelineWidth = rect.width;

    const clickedTime = (x / timelineWidth) * duration * zoomLevel;
    seekTo(clickedTime);
  }, [duration, zoomLevel, seekTo]);

  const handlePlayheadDragStart = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDraggingPlayhead(true);
  }, []);

  const handlePlayheadDrag = useCallback((event: MouseEvent) => {
    if (!isDraggingPlayhead || !timelineCanvasRef.current) return;

    const rect = timelineCanvasRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(event.clientX - rect.left, rect.width));
    const timelineWidth = rect.width;

    const newTime = (x / timelineWidth) * duration * zoomLevel;
    seekTo(newTime);
  }, [isDraggingPlayhead, duration, zoomLevel, seekTo]);

  const handlePlayheadDragEnd = useCallback(() => {
    setIsDraggingPlayhead(false);
  }, []);

  // ===========================
  // Zoom Control
  // ===========================

  const handleZoomIn = useCallback(() => {
    setZoomLevel(prev => Math.min(prev + 0.5, 5));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoomLevel(prev => Math.max(prev - 0.5, 1));
  }, []);

  // ===========================
  // Section Navigation
  // ===========================

  const handleSectionClick = useCallback((section: Section) => {
    seekTo(section.start_time);
    onSectionClick?.(section.section_id);
  }, [seekTo, onSectionClick]);

  // ===========================
  // Video Event Handlers
  // ===========================

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      const time = video.currentTime;
      setCurrentTime(time);
      onTimeUpdate?.(time);
    };

    const handleEnded = () => {
      setIsPlaying(false);
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('ended', handleEnded);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('ended', handleEnded);
    };
  }, [onTimeUpdate]);

  // ===========================
  // Playhead Drag Event Listeners
  // ===========================

  useEffect(() => {
    if (isDraggingPlayhead) {
      document.addEventListener('mousemove', handlePlayheadDrag);
      document.addEventListener('mouseup', handlePlayheadDragEnd);
    } else {
      document.removeEventListener('mousemove', handlePlayheadDrag);
      document.removeEventListener('mouseup', handlePlayheadDragEnd);
    }

    return () => {
      document.removeEventListener('mousemove', handlePlayheadDrag);
      document.removeEventListener('mouseup', handlePlayheadDragEnd);
    };
  }, [isDraggingPlayhead, handlePlayheadDrag, handlePlayheadDragEnd]);

  // ===========================
  // Canvas Timeline Rendering
  // ===========================

  useEffect(() => {
    const canvas = timelineCanvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const container = timelineContainerRef.current;
    if (!container) return;

    // Set canvas size
    const rect = container.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = 120; // 3 layers × 40px

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Timeline dimensions
    const timelineWidth = canvas.width;
    const layerHeight = 40;
    const layers = ['영상', '오디오', '자막'];

    // Draw layers
    layers.forEach((layer, index) => {
      const y = index * layerHeight;

      // Layer background
      ctx.fillStyle = '#1F2937'; // gray-800
      ctx.fillRect(0, y, timelineWidth, layerHeight);

      // Layer border
      ctx.strokeStyle = '#374151'; // gray-700
      ctx.lineWidth = 1;
      ctx.strokeRect(0, y, timelineWidth, layerHeight);

      // Layer label
      ctx.fillStyle = '#9CA3AF'; // gray-400
      ctx.font = '12px sans-serif';
      ctx.fillText(layer, 8, y + 24);
    });

    // Draw sections on first layer (영상)
    sections.forEach(section => {
      const startX = (section.start_time / duration) * timelineWidth;
      const sectionWidth = (section.duration / duration) * timelineWidth;

      // Section rectangle
      ctx.fillStyle = SECTION_COLORS[section.type];
      ctx.fillRect(startX, 0, sectionWidth, layerHeight);

      // Section border
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 1;
      ctx.strokeRect(startX, 0, sectionWidth, layerHeight);

      // Section label
      if (sectionWidth > 40) { // Only show label if enough space
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 11px sans-serif';
        ctx.fillText(SECTION_LABELS[section.type], startX + 8, 24);
      }
    });

    // Draw playhead indicator
    const playheadX = (currentTime / duration) * timelineWidth;
    ctx.strokeStyle = '#FBBF24'; // amber-400
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(playheadX, 0);
    ctx.lineTo(playheadX, canvas.height);
    ctx.stroke();

    // Playhead handle (top)
    ctx.fillStyle = '#FBBF24';
    ctx.beginPath();
    ctx.arc(playheadX, 0, 6, 0, 2 * Math.PI);
    ctx.fill();

  }, [currentTime, duration, sections, zoomLevel]);

  // ===========================
  // Time Formatting
  // ===========================

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // ===========================
  // Render
  // ===========================

  return (
    <div className="w-full bg-gray-900 rounded-lg shadow-xl overflow-hidden">
      {/* Video Player */}
      <div className="relative bg-black aspect-video">
        <video
          ref={videoRef}
          src={videoUrl}
          className="w-full h-full"
          onClick={togglePlayPause}
        >
          <track kind="captions" />
        </video>

        {/* Play/Pause Overlay */}
        {!isPlaying && (
          <div
            className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 cursor-pointer"
            onClick={togglePlayPause}
          >
            <svg className="w-20 h-20 text-white opacity-80" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
        )}
      </div>

      {/* Timeline Container */}
      <div className="p-4">
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-400">타임라인</span>
            <div className="flex gap-2">
              <button
                onClick={handleZoomOut}
                disabled={zoomLevel <= 1}
                className="px-2 py-1 bg-gray-700 text-white rounded text-sm hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                -
              </button>
              <span className="text-sm text-gray-400 px-2 py-1">{Math.round(zoomLevel * 100)}%</span>
              <button
                onClick={handleZoomIn}
                disabled={zoomLevel >= 5}
                className="px-2 py-1 bg-gray-700 text-white rounded text-sm hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                +
              </button>
            </div>
          </div>

          {/* Timeline Canvas */}
          <div ref={timelineContainerRef} className="relative w-full">
            <canvas
              ref={timelineCanvasRef}
              className="w-full cursor-pointer"
              onClick={handleTimelineClick}
              onMouseDown={handlePlayheadDragStart}
            />
          </div>
        </div>

        {/* Section Buttons */}
        <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
          {sections.map(section => (
            <button
              key={section.section_id}
              onClick={() => handleSectionClick(section)}
              className="px-3 py-2 rounded text-sm font-medium whitespace-nowrap transition-all hover:opacity-80"
              style={{
                backgroundColor: SECTION_COLORS[section.type],
                color: '#FFFFFF',
              }}
            >
              {SECTION_LABELS[section.type]} ({formatTime(section.start_time)})
            </button>
          ))}
        </div>

        {/* Controls */}
        <div className="flex items-center gap-4">
          {/* Play/Pause */}
          <button
            onClick={togglePlayPause}
            className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            {isPlaying ? (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>

          {/* Time Display */}
          <div className="text-sm text-gray-300 font-mono">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>

          {/* Volume Control */}
          <div className="flex items-center gap-2 ml-auto">
            <button
              onClick={toggleMute}
              className="p-2 text-gray-300 hover:text-white transition-colors"
            >
              {isMuted || volume === 0 ? (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z" />
                </svg>
              )}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={isMuted ? 0 : volume}
              onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
              className="w-20 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
