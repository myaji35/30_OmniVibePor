"use client";

import { Zap, Database, Plus, Upload } from "lucide-react";
import ClientsList from "@/components/ClientsList";

interface StudioSidebarProps {
    selectedCampaignName: string | null;
    onCampaignSelect: (campaign: any) => void;
    onSheetsModalOpen: () => void;
    onDriveSelectOpen: () => void;
}

export default function StudioSidebar({
    selectedCampaignName,
    onCampaignSelect,
    onSheetsModalOpen,
    onDriveSelectOpen,
}: StudioSidebarProps) {
    return (
        <aside className="w-80 glass-panel border-r border-white/5 flex flex-col z-20 relative overflow-hidden">
            {/* Background Aesthetic Blur */}
            <div className="absolute -top-24 -left-24 w-64 h-64 bg-brand-primary-500/10 rounded-full blur-[100px] pointer-events-none" />
            <div className="absolute top-1/2 -right-24 w-48 h-48 bg-brand-secondary-500/10 rounded-full blur-[80px] pointer-events-none" />

            <div className="p-10 relative">
                <div className="flex items-center gap-4 mb-12 group cursor-pointer">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-primary-500 via-brand-primary-600 to-brand-secondary-600 flex items-center justify-center shadow-[0_10px_30px_-5px_rgba(168,85,247,0.5)] group-hover:scale-110 group-hover:rotate-6 transition-all duration-500">
                        <Zap className="w-7 h-7 text-white fill-white/20" />
                    </div>
                    <div className="flex flex-col">
                        <h1 className="text-xl font-black font-outfit premium-gradient-text tracking-tighter leading-none mb-1">
                            OMNIVIBE
                        </h1>
                        <span className="text-[10px] font-black text-white/30 tracking-[0.4em] uppercase">Studio Pro</span>
                    </div>
                </div>

                <button
                    onClick={onSheetsModalOpen}
                    className="w-full relative group overflow-hidden p-0.5 rounded-2xl transition-all duration-500 hover:scale-[1.02] active:scale-95"
                >
                    <div className="absolute inset-0 bg-gradient-to-r from-brand-primary-500 via-brand-secondary-500 to-brand-primary-500 animate-gradient-x opacity-30 group-hover:opacity-100 transition-opacity" />
                    <div className="relative py-4 bg-[#0a0a0c] rounded-[calc(1rem-2px)] flex items-center justify-center gap-3 border border-white/5 group-hover:border-transparent transition-colors">
                        <Database className="w-5 h-5 text-brand-primary-400 group-hover:scale-110 transition-transform" />
                        <span className="text-xs font-black tracking-widest uppercase text-gray-300 group-hover:text-white transition-colors">에셋 라이브러리</span>
                    </div>
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-8 space-y-4 pb-8 custom-scrollbar">
                <div className="flex items-center justify-between px-2 mb-6">
                    <h3 className="text-[10px] font-black text-gray-600 uppercase tracking-[0.35em] flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-brand-primary-500/50 shadow-[0_0_8px_rgba(168,85,247,0.5)]" />
                        캠페인 오케스트레이터
                    </h3>
                    <button className="w-6 h-6 flex items-center justify-center bg-white/5 hover:bg-white/10 rounded-lg transition-all text-gray-500 hover:text-white border border-white/5">
                        <Plus className="w-3.5 h-3.5" />
                    </button>
                </div>

                <div className="relative">
                    <ClientsList onCampaignSelect={onCampaignSelect} />
                </div>
            </div>

            {/* 하단 미디어 슬라이드 (Glass Card) */}
            <div className="p-8 mt-auto border-t border-white/5 bg-white/[0.01] relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-t from-brand-primary-500/5 to-transparent pointer-events-none" />
                <div className="premium-card rounded-[2rem] p-5 bg-white/[0.03] border-white/10 group cursor-pointer relative overflow-hidden shadow-2xl">
                    <div className="absolute inset-0 bg-gradient-to-tr from-brand-primary-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                    <div className="flex flex-col items-center justify-center py-8 border-2 border-dashed border-white/5 rounded-[1.5rem] group-hover:border-brand-primary-500/40 transition-all duration-500">
                        <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 group-hover:shadow-[0_0_20px_rgba(168,85,247,0.3)] transition-all">
                            <Upload className="w-6 h-6 text-gray-500 group-hover:text-brand-primary-400 group-hover:animate-bounce transition-colors" />
                        </div>
                        <span className="text-[10px] font-black text-gray-600 group-hover:text-white tracking-[0.2em] uppercase transition-colors">즉시 미디어 업로드</span>
                    </div>
                </div>
            </div>
        </aside>
    );
}
