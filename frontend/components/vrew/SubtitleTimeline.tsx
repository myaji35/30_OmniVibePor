'use client'

/**
 * SubtitleTimeline — 오디오 파형 + 자막 토큰 타임라인 통합 뷰 (경로 A, VREW 레이어)
 *
 * 기능:
 * - WaveSurfer.js 오디오 파형 시각화
 * - 자막 토큰 단위 클릭 편집
 * - 타이밍 핀 드래그 조정
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { Play, Pause, ZoomIn, ZoomOut } from 'lucide-react'

export interface SubtitleToken {
  index:   number
  startMs: number
  endMs:   number
  text:    string
}

interface SubtitleTimelineProps {
  audioUrl:   string
  subtitles:  SubtitleToken[]
  duration:   number                              // 전체 오디오 길이 (ms)
  onChange?:  (updated: SubtitleToken[]) => void  // 토큰 수정 콜백
}

const TIMELINE_HEIGHT   = 60  // px — 파형 높이
const TOKEN_TRACK_HEIGHT = 36  // px — 토큰 트랙 높이
const MIN_ZOOM = 1
const MAX_ZOOM = 8

export default function SubtitleTimeline({
  audioUrl,
  subtitles,
  duration,
  onChange,
}: SubtitleTimelineProps) {
  const waveformRef  = useRef<HTMLDivElement>(null)
  const timelineRef  = useRef<HTMLDivElement>(null)
  const wavesurferRef = useRef<any>(null)

  const [isPlaying,    setIsPlaying]    = useState(false)
  const [currentMs,    setCurrentMs]    = useState(0)
  const [zoom,         setZoom]         = useState(1)
  const [editingIdx,   setEditingIdx]   = useState<number | null>(null)
  const [editText,     setEditText]     = useState('')
  const [draggingPin,  setDraggingPin]  = useState<{ idx: number; edge: 'start' | 'end' } | null>(null)
  const [wsReady,      setWsReady]      = useState(false)

  // WaveSurfer 초기화
  useEffect(() => {
    if (!waveformRef.current || !audioUrl) return
    let ws: any

    const init = async () => {
      try {
        const WaveSurfer = (await import('wavesurfer.js')).default
        ws = WaveSurfer.create({
          container:        waveformRef.current!,
          waveColor:        '#3A3A3A',
          progressColor:    '#00FF88',
          cursorColor:      '#00FF88',
          height:           TIMELINE_HEIGHT,
          barWidth:         2,
          barGap:           1,
          barRadius:        2,
          normalize:        true,
          interact:         true,
          minPxPerSec:      50 * zoom,
        })
        ws.load(audioUrl)
        ws.on('ready',         () => setWsReady(true))
        ws.on('play',          () => setIsPlaying(true))
        ws.on('pause',         () => setIsPlaying(false))
        ws.on('finish',        () => setIsPlaying(false))
        ws.on('audioprocess',  (t: number) => setCurrentMs(t * 1000))
        wavesurferRef.current = ws
      } catch (e) {
        console.warn('[SubtitleTimeline] WaveSurfer 초기화 실패:', e)
      }
    }
    init()
    return () => { ws?.destroy() }
  }, [audioUrl])

  // 줌 변경 시 WaveSurfer 업데이트
  useEffect(() => {
    if (wavesurferRef.current && wsReady) {
      wavesurferRef.current.zoom(50 * zoom)
    }
  }, [zoom, wsReady])

  const togglePlay = useCallback(() => {
    wavesurferRef.current?.playPause()
  }, [])

  // 토큰 텍스트 편집 확정
  const commitEdit = useCallback(() => {
    if (editingIdx === null) return
    const updated = subtitles.map((s, i) =>
      i === editingIdx ? { ...s, text: editText } : s
    )
    onChange?.(updated)
    setEditingIdx(null)
  }, [editingIdx, editText, subtitles, onChange])

  // 타임라인 클릭 → 재생 위치 이동
  const handleTimelineClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!timelineRef.current || !wsReady) return
    const rect = timelineRef.current.getBoundingClientRect()
    const ratio = (e.clientX - rect.left) / rect.width
    const seekMs = ratio * duration
    wavesurferRef.current?.seekTo(seekMs / (duration))
    setCurrentMs(seekMs)
  }, [duration, wsReady])

  // 핀 드래그 — 시작
  const startPinDrag = useCallback(
    (e: React.MouseEvent, idx: number, edge: 'start' | 'end') => {
      e.stopPropagation()
      setDraggingPin({ idx, edge })
    }, []
  )

  // 핀 드래그 — 이동 (window mousemove)
  useEffect(() => {
    if (!draggingPin || !timelineRef.current) return
    const onMove = (e: MouseEvent) => {
      const rect = timelineRef.current!.getBoundingClientRect()
      const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
      const newMs = Math.round(ratio * duration)
      const updated = subtitles.map((s, i) => {
        if (i !== draggingPin.idx) return s
        if (draggingPin.edge === 'start') return { ...s, startMs: Math.min(newMs, s.endMs - 100) }
        return { ...s, endMs: Math.max(newMs, s.startMs + 100) }
      })
      onChange?.(updated)
    }
    const onUp = () => setDraggingPin(null)
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [draggingPin, duration, subtitles, onChange])

  const msToPercent = (ms: number) => `${(ms / duration) * 100}%`
  const msToTime    = (ms: number) => {
    const s  = Math.floor(ms / 1000)
    const ms_ = ms % 1000
    return `${String(Math.floor(s / 60)).padStart(2,'0')}:${String(s % 60).padStart(2,'0')}.${String(ms_).padStart(3,'0').slice(0,1)}`
  }

  return (
    <div className="flex flex-col gap-2 bg-[#141414] rounded-xl border border-white/[0.07] p-3 select-none">
      {/* 컨트롤 바 */}
      <div className="flex items-center gap-3">
        <button
          onClick={togglePlay}
          disabled={!wsReady}
          className="w-8 h-8 rounded-full flex items-center justify-center
            bg-[#00FF88]/10 border border-[#00FF88]/30 text-[#00FF88]
            hover:bg-[#00FF88]/20 transition-all disabled:opacity-30"
        >
          {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
        </button>

        <span className="font-mono text-[11px] text-white/50">
          {msToTime(currentMs)} / {msToTime(duration)}
        </span>

        <div className="ml-auto flex items-center gap-1">
          <button onClick={() => setZoom(z => Math.max(MIN_ZOOM, z - 1))}
            className="p-1 rounded text-white/40 hover:text-white/70 hover:bg-white/5 transition-all">
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="text-[10px] font-mono text-white/30 w-8 text-center">{zoom}x</span>
          <button onClick={() => setZoom(z => Math.min(MAX_ZOOM, z + 1))}
            className="p-1 rounded text-white/40 hover:text-white/70 hover:bg-white/5 transition-all">
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 파형 */}
      <div ref={waveformRef} className="w-full rounded overflow-hidden" />

      {/* 타임라인 토큰 트랙 */}
      <div
        ref={timelineRef}
        className="relative w-full cursor-crosshair"
        style={{ height: TOKEN_TRACK_HEIGHT }}
        onClick={handleTimelineClick}
      >
        {/* 현재 재생 위치 선 */}
        <div
          className="absolute top-0 bottom-0 w-px bg-[#00FF88] pointer-events-none z-20"
          style={{ left: msToPercent(currentMs) }}
        />

        {/* 자막 토큰 */}
        {subtitles.map((sub, idx) => (
          <div
            key={idx}
            className="absolute top-1 bottom-1 rounded flex items-center overflow-hidden group"
            style={{
              left:  msToPercent(sub.startMs),
              width: msToPercent(sub.endMs - sub.startMs),
              background: currentMs >= sub.startMs && currentMs <= sub.endMs
                ? 'rgba(0,255,136,0.20)'
                : 'rgba(255,255,255,0.06)',
              border: currentMs >= sub.startMs && currentMs <= sub.endMs
                ? '1px solid rgba(0,255,136,0.40)'
                : '1px solid rgba(255,255,255,0.10)',
            }}
            onClick={e => { e.stopPropagation(); setEditingIdx(idx); setEditText(sub.text) }}
          >
            {editingIdx === idx ? (
              <input
                autoFocus
                value={editText}
                onChange={e => setEditText(e.target.value)}
                onBlur={commitEdit}
                onKeyDown={e => { if (e.key === 'Enter') commitEdit() }}
                className="w-full h-full px-1 text-[10px] font-mono bg-transparent
                  text-[#00FF88] outline-none"
                onClick={e => e.stopPropagation()}
              />
            ) : (
              <span className="px-1 text-[10px] font-mono text-white/70 truncate">
                {sub.text}
              </span>
            )}

            {/* 시작 핀 */}
            <div
              className="absolute left-0 top-0 bottom-0 w-1.5 cursor-ew-resize
                bg-[#00FF88]/60 opacity-0 group-hover:opacity-100 transition-opacity"
              onMouseDown={e => startPinDrag(e, idx, 'start')}
            />
            {/* 끝 핀 */}
            <div
              className="absolute right-0 top-0 bottom-0 w-1.5 cursor-ew-resize
                bg-[#00FF88]/60 opacity-0 group-hover:opacity-100 transition-opacity"
              onMouseDown={e => startPinDrag(e, idx, 'end')}
            />
          </div>
        ))}
      </div>
    </div>
  )
}
