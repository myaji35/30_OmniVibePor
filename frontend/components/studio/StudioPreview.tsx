"use client";

import { Play, SkipBack, SkipForward, Maximize2, Settings2, Zap } from "lucide-react";

interface StudioPreviewProps {
    workflowStep: string | null;
    videoUrl: string | null;
    isPlaying: boolean;
    setIsPlaying: (playing: boolean) => void;
    currentTime: number;
}

export default function StudioPreview({
    workflowStep,
    videoUrl,
    isPlaying,
    setIsPlaying,
    currentTime,
}: StudioPreviewProps) {
    return (
        <div className="h-full flex flex-col p-12 items-center justify-center relative bg-[#050505]">
            {/* Background Light Effect */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-brand-primary-500/5 rounded-full blur-[120px] pointer-events-none" />

            <div className="relative w-full max-w-6xl aspect-video premium-card rounded-[3rem] overflow-hidden shadow-[0_50px_120px_-30px_rgba(0,0,0,0.9)] flex items-center justify-center p-0 group border border-white/10 group">
                {/* AI Viewport Status Overlay */}
                <div className="absolute top-8 left-8 z-20 flex items-center gap-4">
                    <div className="flex items-center gap-2 px-4 py-2 bg-black/40 backdrop-blur-2xl rounded-full border border-white/5">
                        <div className="w-2 h-2 rounded-full bg-brand-primary-500 animate-pulse shadow-[0_0_10px_#a855f7]" />
                        <span className="text-[10px] font-black text-white/70 uppercase tracking-[0.2em]">AI Engine v1.0</span>
                    </div>
                </div>

                <div className="absolute top-8 right-8 z-20 flex items-center gap-3">
                    <button className="p-3 bg-white/5 hover:bg-white/10 backdrop-blur-3xl rounded-2xl border border-white/10 transition-all">
                        <Settings2 className="w-4 h-4 text-gray-400" />
                    </button>
                    <button className="p-3 bg-white/5 hover:bg-white/10 backdrop-blur-3xl rounded-2xl border border-white/10 transition-all">
                        <Maximize2 className="w-4 h-4 text-gray-400" />
                    </button>
                </div>

                {/* Video Engine Canvas */}
                <div className="absolute inset-0 bg-[#0a0a0c] flex flex-col items-center justify-center">
                    {workflowStep === "video_ready" && videoUrl ? (
                        <video className="w-full h-full object-contain" src={videoUrl} controls={false} autoPlay muted loop />
                    ) : (
                        <div className="flex flex-col items-center">
                            <div className="w-32 h-32 rounded-[2.5rem] bg-gradient-to-br from-brand-primary-500/10 to-brand-secondary-500/10 border border-brand-primary-500/20 flex items-center justify-center mb-10 relative">
                                <div className="absolute inset-0 rounded-[2.5rem] bg-brand-primary-500/10 animate-ping opacity-20" />
                                <div className="absolute inset-0 rounded-[2.5rem] border border-brand-primary-500/30 animate-pulse" />
                                <Zap className="w-12 h-12 text-brand-primary-400 fill-brand-primary-400/20" />
                            </div>
                            <h3 className="text-3xl font-black font-outfit premium-gradient-text tracking-tighter mb-4 italic uppercase">
                                Neural Rendering
                            </h3>
                            <p className="text-xs font-black text-white/20 tracking-[0.5em] uppercase pl-2">Initialising AI Viewport</p>
                        </div>
                    )}
                </div>

                {/* Advanced Controller UI */}
                <div className="absolute bottom-12 inset-x-12 p-3 bg-black/40 backdrop-blur-3xl border border-white/10 rounded-[2.5rem] flex items-center gap-8 shadow-3xl transition-all translate-y-6 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 duration-700">
                    <div className="flex items-center gap-3 ml-2">
                        <button className="p-4 hover:bg-white/10 rounded-2xl transition-colors"><SkipBack className="w-5 h-5 text-gray-500" /></button>
                        <button
                            onClick={() => setIsPlaying(!isPlaying)}
                            className="w-16 h-16 bg-gradient-to-br from-brand-primary-600 to-brand-primary-700 rounded-[1.5rem] flex items-center justify-center shadow-2xl shadow-purple-500/50 active:scale-90 transition-all"
                        >
                            <Play className="w-8 h-8 fill-white text-white" />
                        </button>
                        <button className="p-4 hover:bg-white/10 rounded-2xl transition-colors"><SkipForward className="w-5 h-5 text-gray-500" /></button>
                    </div>

                    <div className="flex-1 flex flex-col gap-2">
                        <div className="flex justify-between text-[10px] font-black font-mono text-brand-primary-400 tracking-widest uppercase italic">
                            <span>Scanning Frame 0429</span>
                            <span>24.00 FPS</span>
                        </div>
                        <div className="h-2 bg-white/5 rounded-full relative overflow-hidden ring-1 ring-white/5">
                            <div className="absolute top-0 left-0 h-full w-[42%] bg-gradient-to-r from-brand-primary-600 via-brand-secondary-500 to-brand-primary-600 rounded-full shadow-[0_0_20px_#a855f7]" />
                        </div>
                    </div>

                    <div className="mr-8 font-mono font-black text-sm text-white/60 tabular-nums">
                        00:42 <span className="text-white/20">/ 03:00</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
