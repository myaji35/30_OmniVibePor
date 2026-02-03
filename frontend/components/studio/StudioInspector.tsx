"use client";

import { Settings, Brain, ShieldCheck, Activity, Database, BarChart, Sparkles } from "lucide-react";
import BlockEffectsEditor from "@/components/BlockEffectsEditor";
import { ScriptBlock } from "@/lib/blocks/types";

interface StudioInspectorProps {
    selectedBlock: ScriptBlock | null;
    onBlockUpdate: (id: string, updates: Partial<ScriptBlock>) => void;
    onAutoSplit?: (id: string) => void;
    blockCount: number;
    totalDuration: number;
}

export default function StudioInspector({
    selectedBlock,
    onBlockUpdate,
    onAutoSplit,
    blockCount,
    totalDuration,
}: StudioInspectorProps) {
    return (
        <aside className="w-[450px] glass-panel border-l border-white/5 flex flex-col z-20 overflow-hidden relative">
            {/* Background Aesthetic */}
            <div className="absolute top-1/2 -left-24 w-64 h-64 bg-brand-secondary-500/5 rounded-full blur-[100px] pointer-events-none" />

            <div className="p-10 border-b border-white/5 flex items-center justify-between bg-white/[0.01]">
                <div className="flex flex-col">
                    <h3 className="text-[10px] font-black font-outfit uppercase tracking-[0.4em] text-white/40 mb-1">Properties</h3>
                    <h2 className="text-xl font-black font-outfit text-white tracking-tight flex items-center gap-3">
                        Inspector Engine
                        <Activity className="w-4 h-4 text-brand-primary-500 animate-pulse" />
                    </h2>
                </div>
                <button className="p-4 bg-white/5 hover:bg-white/10 rounded-2xl border border-white/5 transition-all group">
                    <Settings className="w-5 h-5 text-gray-500 group-hover:text-white group-hover:rotate-90 transition-all duration-500" />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-10 py-12 space-y-12 custom-scrollbar relative z-10">
                {/* AI Core Intelligence Card */}
                <div className="premium-card rounded-[2.5rem] p-8 border border-brand-primary-500/20 bg-brand-primary-500/[0.03] space-y-6 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-brand-primary-500/10 rounded-full blur-3xl group-hover:bg-brand-primary-500/20 transition-all duration-700" />

                    <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-2xl bg-brand-primary-600/20 border border-brand-primary-500/30 flex items-center justify-center">
                            <Brain className="w-8 h-8 text-brand-primary-400" />
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] font-black text-brand-primary-400 uppercase tracking-widest pl-0.5">Neural Process</span>
                            <span className="text-lg font-black text-white italic tracking-tight">AI Context Splitting</span>
                        </div>
                    </div>

                    <p className="text-xs font-medium text-gray-500 leading-relaxed border-l-2 border-brand-primary-500/30 pl-4 py-1 italic">
                        Advanced AI logic analyzing block transitions and semantic flow for optimal retention.
                    </p>

                    <button className="w-full py-4 bg-gradient-to-r from-brand-primary-600 to-brand-primary-800 rounded-2xl text-[10px] font-black uppercase tracking-[0.3em] text-white shadow-xl shadow-purple-900/40 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-3">
                        <Sparkles className="w-4 h-4" /> Optimise Intelligence
                    </button>
                </div>

                {/* Transitions & Effects */}
                <div className="space-y-8">
                    <div className="flex items-center gap-4">
                        <div className="w-8 h-[2px] bg-brand-primary-500" />
                        <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.4em]">Visual Modifiers</h4>
                    </div>

                    {selectedBlock ? (
                        <BlockEffectsEditor
                            block={selectedBlock}
                            onUpdate={(effects) => onBlockUpdate(selectedBlock.id, { effects })}
                        />
                    ) : (
                        <div className="p-16 border-2 border-dashed border-white/5 rounded-[2.5rem] flex flex-col items-center justify-center text-center space-y-4">
                            <div className="w-16 h-16 bg-white/5 rounded-[1.5rem] flex items-center justify-center">
                                <Activity className="w-8 h-8 text-white/10" />
                            </div>
                            <p className="text-[10px] font-black text-white/20 uppercase tracking-[0.4em]">Idle Canvas</p>
                        </div>
                    )}
                </div>

                {/* System Compliance & Environment Health */}
                <div className="space-y-6 pt-6">
                    <div className="flex items-center gap-4">
                        <div className="w-8 h-[2px] bg-emerald-500" />
                        <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.4em]">Environmental Compliance</h4>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="p-5 bg-white/[0.02] border border-white/5 rounded-3xl flex flex-col gap-3 group/stat hover:bg-white/[0.04] transition-all relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-12 h-12 bg-emerald-500/5 rounded-full blur-xl animate-pulse" />
                            <ShieldCheck className="w-5 h-5 text-emerald-500 group-hover/stat:scale-110 transition-transform" />
                            <div className="flex flex-col">
                                <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest">Aesthetic Integrity</span>
                                <span className="text-xs font-black text-emerald-400 tracking-wider">PREMIUM VERIFIED</span>
                            </div>
                        </div>
                        <div className="p-5 bg-white/[0.02] border border-white/5 rounded-3xl flex flex-col gap-3 group/stat hover:bg-white/[0.04] transition-all relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-12 h-12 bg-brand-primary-500/5 rounded-full blur-xl" />
                            <Activity className="w-5 h-5 text-brand-primary-400 group-hover/stat:scale-110 transition-transform" />
                            <div className="flex flex-col">
                                <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest">UX Consistency</span>
                                <span className="text-xs font-black text-white tracking-wider">STABLE (100%)</span>
                            </div>
                        </div>
                        <div className="p-5 bg-white/[0.02] border border-white/5 rounded-3xl flex flex-col gap-3 group/stat hover:bg-white/[0.04] transition-all border-l-brand-primary-500/50">
                            <Sparkles className="w-5 h-5 text-brand-secondary-400 group-hover/stat:scale-110 transition-transform" />
                            <div className="flex flex-col">
                                <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest">Design Asset Load</span>
                                <span className="text-xs font-black text-white tracking-wider">SYNCED</span>
                            </div>
                        </div>
                        <div className="p-5 bg-white/[0.02] border border-white/5 rounded-3xl flex flex-col gap-3 group/stat hover:bg-white/[0.04] transition-all border-l-brand-secondary-500/50">
                            <Brain className="w-5 h-5 text-brand-primary-400 group-hover/stat:scale-110 transition-transform" />
                            <div className="flex flex-col">
                                <span className="text-[9px] font-black text-gray-600 uppercase tracking-widest">AI Logic Health</span>
                                <span className="text-xs font-black text-white tracking-wider">OPTIMAL</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Project Intelligence Summary */}
            <div className="p-10 mt-auto bg-gradient-to-t from-brand-primary-500/5 to-transparent border-t border-white/5">
                <div className="flex items-center justify-between mb-8">
                    <div className="flex flex-col">
                        <span className="text-[10px] font-black text-gray-500 uppercase tracking-[0.3em] mb-1">Architecture Complexity</span>
                        <div className="flex items-center gap-3">
                            <BarChart className="w-4 h-4 text-brand-primary-400" />
                            <span className="text-2xl font-black text-white italic tracking-tighter">{blockCount} Blocks</span>
                        </div>
                    </div>
                    <div className="text-right">
                        <span className="text-[10px] font-black text-gray-500 uppercase tracking-[0.3em] mb-1">Estimated Engine Runtime</span>
                        <div className="text-2xl font-black text-brand-primary-400 italic tracking-tighter tabular-nums">{totalDuration}s</div>
                    </div>
                </div>

                <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full w-[68%] bg-gradient-to-r from-brand-primary-600 to-brand-primary-400 shadow-[0_0_10px_rgba(168,85,247,0.5)]" />
                </div>
            </div>
        </aside>
    );
}
