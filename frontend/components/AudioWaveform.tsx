'use client'

import { useState, useRef, useEffect } from 'react'
import WaveSurfer from 'wavesurfer.js'
import { Play, Pause, Volume2, Activity } from 'lucide-react'

interface AudioWaveformProps {
    audioUrl: string | null
    duration: number
    onTimeUpdate?: (time: number) => void
    className?: string
}

export default function AudioWaveform({
    audioUrl,
    duration,
    onTimeUpdate,
    className = ''
}: AudioWaveformProps) {
    const waveformRef = useRef<HTMLDivElement>(null)
    const wavesurfer = useRef<WaveSurfer | null>(null)
    const [isPlaying, setIsPlaying] = useState(false)
    const [currentTime, setCurrentTime] = useState(0)

    useEffect(() => {
        if (!waveformRef.current || !audioUrl) return

        wavesurfer.current = WaveSurfer.create({
            container: waveformRef.current,
            waveColor: 'rgba(168, 85, 247, 0.2)',
            progressColor: '#a855f7',
            cursorColor: '#f472b6',
            barWidth: 3,
            barRadius: 4,
            cursorWidth: 2,
            height: 100,
            barGap: 3,
            normalize: true,
            backend: 'WebAudio',
            fillParent: true,
        })

        wavesurfer.current.load(audioUrl).catch((error) => {
            console.warn('⚠️ Audio file load failed:', error.message)
        })

        wavesurfer.current.on('audioprocess', (time) => {
            setCurrentTime(time)
            onTimeUpdate?.(time)
        })

        wavesurfer.current.on('play', () => setIsPlaying(true))
        wavesurfer.current.on('pause', () => setIsPlaying(false))

        return () => {
            wavesurfer.current?.destroy()
        }
    }, [audioUrl, onTimeUpdate])

    const handlePlayPause = () => {
        wavesurfer.current?.playPause()
    }

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    if (!audioUrl) {
        return (
            <div className={`premium-card rounded-[2rem] p-10 border-2 border-dashed border-white/5 flex flex-col items-center justify-center gap-4 bg-white/[0.01] ${className}`}>
                <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center animate-pulse">
                    <Volume2 className="w-6 h-6 text-gray-700" />
                </div>
                <p className="text-[10px] font-black text-gray-600 uppercase tracking-[0.3em]">Waiting for Engine Audio</p>
            </div>
        )
    }

    return (
        <div className={`p-8 bg-black/40 rounded-[2.5rem] border border-white/5 shadow-inner relative group overflow-hidden ${className}`}>
            {/* Background Kinetic Effect */}
            <div className="absolute top-0 left-0 w-1/2 h-full bg-gradient-to-r from-brand-primary-500/5 to-transparent pointer-events-none" />

            <div className="relative flex flex-col gap-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 px-4 py-2 bg-brand-primary-500/10 rounded-xl border border-brand-primary-500/20">
                        <Activity className="w-4 h-4 text-brand-primary-400" />
                        <span className="text-[10px] font-black text-brand-primary-400 uppercase tracking-widest">Master Audio Stream</span>
                    </div>
                    <div className="flex items-center gap-4 font-mono text-[11px] font-black text-white/40 tracking-widest uppercase">
                        <span className="text-white">{formatTime(currentTime)}</span>
                        <div className="w-8 h-px bg-white/10" />
                        <span>{formatTime(duration)}</span>
                    </div>
                </div>

                {/* Waveform Canvas */}
                <div className="relative">
                    <div ref={waveformRef} className="opacity-80 group-hover:opacity-100 transition-opacity duration-500" />
                    {/* Glossy Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/[0.02] to-transparent pointer-events-none" />
                </div>

                <div className="flex items-center gap-6">
                    <button
                        onClick={handlePlayPause}
                        className="w-14 h-14 bg-white/5 hover:bg-brand-primary-600 rounded-2xl border border-white/10 hover:border-brand-primary-500 flex items-center justify-center transition-all shadow-xl active:scale-90 group/btn"
                    >
                        {isPlaying ? (
                            <Pause className="w-6 h-6 text-white fill-white" />
                        ) : (
                            <Play className="w-6 h-6 text-white fill-white ml-1" />
                        )}
                    </button>

                    <div className="flex-1 h-[2px] bg-white/5 rounded-full relative overflow-hidden">
                        <div
                            className="absolute top-0 left-0 h-full bg-brand-primary-500 shadow-[0_0_10px_#a855f7] transition-all duration-100"
                            style={{ width: `${(currentTime / duration) * 100}%` }}
                        />
                    </div>
                </div>
            </div>
        </div>
    )
}
