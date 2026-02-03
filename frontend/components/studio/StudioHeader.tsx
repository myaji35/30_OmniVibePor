"use client";

import { Folder, ChevronRight, Play, Type, Layout, BarChart3, Share2 } from "lucide-react";

interface StudioHeaderProps {
    activeTab: "preview" | "script" | "storyboard";
    setActiveTab: (tab: "preview" | "script" | "storyboard") => void;
    selectedCampaignName: string | null;
    onABTestClick: () => void;
    onExport: () => void;
}

export default function StudioHeader({
    activeTab,
    setActiveTab,
    selectedCampaignName,
    onABTestClick,
    onExport,
}: StudioHeaderProps) {
    return (
        <header className="h-24 glass-panel border-b border-white/5 px-10 flex items-center justify-between z-10 relative overflow-hidden">
            {/* Glossy Reflection Effect */}
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none" />

            <div className="flex items-center gap-12">
                <div className="flex items-center gap-5">
                    <div className="w-12 h-12 rounded-[1.2rem] bg-indigo-500/10 border border-white/5 flex items-center justify-center shadow-inner relative group">
                        <Folder className="w-5 h-5 text-indigo-400 group-hover:scale-110 transition-transform" />
                        <div className="absolute -top-1 -right-1 w-3 h-3 bg-brand-primary-500 rounded-full border-2 border-[#0a0a0c] scale-0 group-hover:scale-100 transition-transform duration-300" />
                    </div>
                    <div className="flex flex-col">
                        <div className="flex items-center gap-2 text-[10px] font-black text-gray-600 uppercase tracking-[0.25em] mb-1.5">
                            <span>Project</span>
                            <ChevronRight className="w-2.5 h-2.5 text-gray-800" />
                            <span className="text-brand-primary-400/80">Active Engine</span>
                        </div>
                        <h2 className="text-xl font-black font-outfit text-white tracking-tight flex items-center gap-3">
                            {selectedCampaignName || "Untitled Campaign"}
                            <div className="px-2 py-0.5 rounded bg-brand-primary-500/10 border border-brand-primary-500/20 text-[9px] font-black text-brand-primary-400 uppercase tracking-widest">Live</div>
                        </h2>
                    </div>
                </div>

                <nav className="flex items-center bg-black/40 backdrop-blur-3xl rounded-[1.5rem] p-1.5 border border-white/5 shadow-2xl">
                    {[
                        { id: "preview", label: "PREVIEW", icon: Play },
                        { id: "script", label: "SCRIPTING", icon: Type },
                        { id: "storyboard", label: "STORYBOARD", icon: Layout },
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={`flex items-center gap-3 px-8 py-3 rounded-[1.2rem] text-[10px] font-black tracking-[0.2em] uppercase transition-all duration-500 relative group
                                ${activeTab === tab.id
                                    ? "text-white scale-[1.05]"
                                    : "text-gray-600 hover:text-gray-300"
                                }`}
                        >
                            {activeTab === tab.id && (
                                <div className="absolute inset-0 bg-gradient-to-r from-brand-primary-600 to-brand-secondary-600 rounded-[1.2rem] shadow-[0_10px_25px_-5px_rgba(168,85,247,0.5)] z-0" />
                            )}
                            <tab.icon className={`w-4 h-4 relative z-10 transition-transform duration-500 group-hover:rotate-12 ${activeTab === tab.id ? "text-white" : "text-gray-700"}`} />
                            <span className="relative z-10">{tab.label}</span>
                        </button>
                    ))}
                </nav>
            </div>

            <div className="flex items-center gap-5">
                <button
                    onClick={onABTestClick}
                    className="group relative flex items-center gap-3 px-6 py-3.5 bg-white/[0.02] hover:bg-brand-secondary-500/10 border border-white/5 hover:border-brand-secondary-500/30 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-500"
                >
                    <BarChart3 className="w-4 h-4 text-brand-secondary-400 group-hover:rotate-12 transition-transform" />
                    <span className="text-gray-400 group-hover:text-brand-secondary-300">A/B Intelligence</span>
                    <div className="absolute -top-1 -right-1 flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-secondary-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-brand-secondary-500"></span>
                    </div>
                </button>
                <button
                    onClick={onExport}
                    className="group relative flex items-center gap-3 px-10 py-4 bg-white/5 overflow-hidden rounded-[1.5rem] text-[11px] font-black uppercase tracking-[0.3em] transition-all duration-700 active:scale-95 shadow-2xl"
                >
                    <div className="absolute inset-0 bg-brand-primary-600 transition-transform duration-700 translate-y-[100%] group-hover:translate-y-0" />
                    <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-1000 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.4)_0%,transparent_70%)]" />
                    <Share2 className="w-4.5 h-4.5 relative z-10 text-brand-primary-400 group-hover:text-white transition-colors duration-500" />
                    <span className="relative z-10 text-white leading-none">Export</span>
                </button>
            </div>
        </header>
    );
}
