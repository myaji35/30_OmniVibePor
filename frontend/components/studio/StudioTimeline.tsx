"use client";

import { Clock, Volume2, Mic2, Layers, Zap } from "lucide-react";
import AudioWaveform from "@/components/AudioWaveform";
import { ScriptBlock } from "@/lib/blocks/types";

interface StudioTimelineProps {
    blocks: ScriptBlock[];
    selectedBlockId: string | null;
    onBlockSelect: (id: string) => void;
    audioUrl: string | null;
    currentTime: number;
    onTimeUpdate: (time: number) => void;
    totalDuration: number;
}

export default function StudioTimeline({
    blocks,
    selectedBlockId,
    onBlockSelect,
    audioUrl,
    currentTime,
    onTimeUpdate,
    totalDuration,
}: StudioTimelineProps) {
    return (
        <div className="h-96 glass-panel border-t border-white/5 p-10 flex flex-col gap-8 relative overflow-hidden">
            {/* Aesthetic Glow */}
            <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-brand-primary-500/5 rounded-full blur-[120px] pointer-events-none" />

            <div className="flex items-center justify-between relative z-10">
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-3 px-5 py-2.5 bg-brand-primary-500/10 border border-brand-primary-500/20 rounded-2xl shadow-xl">
                        <div className="w-2 h-2 bg-brand-primary-500 rounded-full animate-pulse shadow-[0_0_10px_#a855f7]" />
                        <h3 className="text-xs font-black text-brand-primary-400 uppercase tracking-[0.4em] italic leading-none">Temporal Flow</h3>
                    </div>

                    <div className="flex items-center gap-4 text-[10px] font-black text-gray-600 uppercase tracking-widest bg-white/5 px-6 py-2.5 rounded-2xl border border-white/5">
                        <Layers className="w-4 h-4" />
                        <span>3 Active Layers</span>
                    </div>
                </div>

                <div className="flex gap-3">
                    <button className="px-6 py-2.5 bg-white/5 hover:bg-white/10 rounded-xl text-[9px] font-black uppercase tracking-[0.3em] text-gray-500 hover:text-white transition-all border border-white/5">Zoom In</button>
                    <button className="px-6 py-2.5 bg-white/5 hover:bg-white/10 rounded-xl text-[9px] font-black uppercase tracking-[0.3em] text-gray-500 hover:text-white transition-all border border-white/5">Zoom Out</button>
                </div>
            </div>

            <div className="flex-1 bg-black/40 rounded-[2.5rem] p-10 border border-white/5 overflow-x-auto custom-scrollbar relative shadow-inner group">
                {/* Timeline Grid (Background) */}
                <div className="absolute inset-0 flex pointer-events-none opacity-5">
                    {[...Array(20)].map((_, i) => (
                        <div key={i} className="flex-1 border-l border-white" />
                    ))}
                </div>

                {/* Blocks Layer */}
                <div className="flex h-24 gap-3 px-4 mb-10 relative z-10">
                    {blocks.map((block) => (
                        <div
                            key={block.id}
                            onClick={() => onBlockSelect(block.id)}
                            className={`h-full min-w-[220px] rounded-[1.8rem] flex flex-col items-center justify-center border-2 transition-all duration-500 cursor-pointer hover:scale-[1.05] active:scale-95 group relative overflow-hidden
                                ${selectedBlockId === block.id
                                    ? "border-brand-primary-500/50 bg-brand-primary-500/[0.08] shadow-[0_20px_40px_-10px_rgba(168,85,247,0.3)] z-20"
                                    : "border-white/5 bg-white/[0.02] hover:border-white/20"}
                            `}
                        >
                            <div className={`absolute inset-0 opacity-10 group-hover:opacity-20 transition-opacity
                                ${block.type === 'hook' ? 'bg-red-500' : block.type === 'body' ? 'bg-brand-primary-500' : 'bg-green-500'}
                            `} />
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 mb-1 leading-none relative z-10">{block.type}</span>
                            <span className="text-[11px] font-black text-white relative z-10">{block.duration}s</span>

                            {selectedBlockId === block.id && (
                                <div className="absolute bottom-0 inset-x-0 h-1 bg-brand-primary-500 shadow-[0_0_15px_#a855f7]" />
                            )}
                        </div>
                    ))}
                </div>

                {/* Audio Master Layer */}
                <div className="flex items-center gap-10 mt-6 relative z-10">
                    <div className="w-20 h-20 bg-gradient-to-br from-brand-primary-600/10 to-brand-primary-700/20 rounded-[2rem] border border-brand-primary-500/20 flex items-center justify-center shadow-2xl shadow-purple-500/10 group/audio cursor-pointer">
                        <Mic2 className="w-8 h-8 text-brand-primary-400 group-hover/audio:scale-110 transition-transform" />
                    </div>
                    <div className="flex-1 bg-black/30 rounded-[2.5rem] p-6 border border-white/5 shadow-inner">
                        <AudioWaveform
                            audioUrl={audioUrl}
                            duration={totalDuration}
                            onTimeUpdate={onTimeUpdate}
                            className="h-24"
                        />
                    </div>
                </div>

                {/* Playhead */}
                <div
                    className="absolute top-0 bottom-0 w-0.5 bg-brand-primary-500 z-30 shadow-[0_0_15px_#a855f7] pointer-events-none transition-all duration-100"
                    style={{ left: `${(currentTime / totalDuration) * 100}%` }}
                >
                    <div className="absolute -top-1 -left-1.5 w-4 h-4 bg-brand-primary-500 rounded-full shadow-[0_0_10px_#a855f7] flex items-center justify-center">
                        <div className="w-1 h-1 bg-white rounded-full" />
                    </div>
                </div>
            </div>
        </div>
    );
}
