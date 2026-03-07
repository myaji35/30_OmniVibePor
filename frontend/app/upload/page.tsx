"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
    Mic,
    FileText,
    Upload,
    CheckCircle,
    AlertCircle,
    Loader2,
    ArrowRight,
    X,
    Volume2,
    Play,
    Zap,
} from "lucide-react";
import Link from "next/link";
import AppShell from "@/components/AppShell";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── 타입 ────────────────────────────────────────────────────────────────────

interface UploadState {
    file: File | null;
    uploading: boolean;
    done: boolean;
    error: string | null;
}

interface VoiceResult {
    voice_id: string;
    voice_name: string;
    status: string;
}

interface PdfResult {
    presentation_id: string;
    slide_count: number;
    message: string;
}

// ─── 드래그앤드롭 훅 ─────────────────────────────────────────────────────────

function useDrop(onDrop: (file: File) => void, accept: string[]) {
    const [dragging, setDragging] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleDrag = useCallback((e: React.DragEvent, active: boolean) => {
        e.preventDefault();
        e.stopPropagation();
        setDragging(active);
    }, []);

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            setDragging(false);
            const file = e.dataTransfer.files[0];
            if (file) onDrop(file);
        },
        [onDrop]
    );

    const handleInput = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const file = e.target.files?.[0];
            if (file) onDrop(file);
        },
        [onDrop]
    );

    return { dragging, inputRef, handleDrag, handleDrop, handleInput };
}

// ─── 파일 크기 포맷 ──────────────────────────────────────────────────────────

function formatSize(bytes: number) {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ─── 메인 컴포넌트 ────────────────────────────────────────────────────────────

export default function UploadPage() {
    const router = useRouter();

    // Voice 상태
    const [voiceState, setVoiceState] = useState<UploadState>({
        file: null, uploading: false, done: false, error: null,
    });
    const [voiceName, setVoiceName] = useState("");
    const [voiceDesc, setVoiceDesc] = useState("");
    const [voiceResult, setVoiceResult] = useState<VoiceResult | null>(null);
    const [audioPreview, setAudioPreview] = useState<string | null>(null);

    // PDF 상태
    const [pdfState, setPdfState] = useState<UploadState>({
        file: null, uploading: false, done: false, error: null,
    });
    const [pdfResult, setPdfResult] = useState<PdfResult | null>(null);

    // ─── Voice 드롭 ────────────────────────────────────────────────────────

    const handleVoiceDrop = useCallback((file: File) => {
        const ok = /\.(mp3|wav|m4a|flac|ogg)$/i.test(file.name);
        if (!ok) {
            setVoiceState(s => ({ ...s, error: "MP3, WAV, M4A, FLAC, OGG 파일만 지원합니다." }));
            return;
        }
        setVoiceState({ file, uploading: false, done: false, error: null });
        setAudioPreview(URL.createObjectURL(file));
        setVoiceResult(null);
    }, []);

    const voiceDrop = useDrop(handleVoiceDrop, ["mp3", "wav", "m4a", "flac", "ogg"]);

    // ─── PDF 드롭 ──────────────────────────────────────────────────────────

    const handlePdfDrop = useCallback((file: File) => {
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            setPdfState(s => ({ ...s, error: "PDF 파일만 지원합니다." }));
            return;
        }
        setPdfState({ file, uploading: false, done: false, error: null });
        setPdfResult(null);
    }, []);

    const pdfDrop = useDrop(handlePdfDrop, ["pdf"]);

    // ─── Voice 업로드 ──────────────────────────────────────────────────────

    const uploadVoice = async () => {
        if (!voiceState.file) return;
        if (!voiceName.trim()) {
            setVoiceState(s => ({ ...s, error: "목소리 이름을 입력해주세요." }));
            return;
        }

        setVoiceState(s => ({ ...s, uploading: true, error: null }));

        try {
            const form = new FormData();
            form.append("audio_file", voiceState.file);
            form.append("user_id", "local_user");
            form.append("voice_name", voiceName.trim());
            form.append("description", voiceDesc.trim() || "사용자 음성 샘플");

            const res = await fetch(`${API_BASE}/api/v1/voice/clone`, {
                method: "POST",
                body: form,
            });

            const data = await res.json();

            if (!res.ok) throw new Error(data.detail || "업로드 실패");

            setVoiceResult({
                voice_id: data.voice_id || data.elevenlabs_voice_id || "test_voice_id",
                voice_name: voiceName,
                status: "completed",
            });
            setVoiceState(s => ({ ...s, uploading: false, done: true }));
        } catch (err) {
            const msg = err instanceof Error ? err.message : "업로드 중 오류가 발생했습니다.";
            setVoiceState(s => ({ ...s, uploading: false, error: msg }));
        }
    };

    // ─── PDF 업로드 ────────────────────────────────────────────────────────

    const uploadPdf = async () => {
        if (!pdfState.file) return;

        setPdfState(s => ({ ...s, uploading: true, error: null }));

        try {
            const form = new FormData();
            form.append("file", pdfState.file);
            form.append("project_id", `proj_${Date.now()}`);
            form.append("dpi", "200");
            form.append("lang", "kor+eng");

            const res = await fetch(`${API_BASE}/api/v1/presentations/upload`, {
                method: "POST",
                body: form,
            });

            const data = await res.json();

            if (!res.ok) throw new Error(data.detail || "PDF 업로드 실패");

            setPdfResult({
                presentation_id: data.presentation_id || `pres_${Date.now()}`,
                slide_count: data.total_slides || 0,
                message: data.message || "PDF가 성공적으로 업로드되었습니다.",
            });
            setPdfState(s => ({ ...s, uploading: false, done: true }));
        } catch (err) {
            const msg = err instanceof Error ? err.message : "PDF 업로드 중 오류가 발생했습니다.";
            setPdfState(s => ({ ...s, uploading: false, error: msg }));
        }
    };

    // ─── 영상 만들기 (PDF + Voice → Studio) ───────────────────────────────

    const goToStudio = () => {
        const params = new URLSearchParams();
        if (pdfResult?.presentation_id) params.set("presentation_id", pdfResult.presentation_id);
        if (voiceResult?.voice_id) params.set("voice_id", voiceResult.voice_id);
        router.push(`/studio?${params.toString()}`);
    };

    const bothReady = voiceState.done && pdfState.done;

    // ─── 렌더 ──────────────────────────────────────────────────────────────

    return (
        <AppShell
            title="미디어 업로드"
            subtitle="목소리 샘플과 PDF를 업로드하면 AI가 영상을 자동 완성합니다"
            actions={bothReady ? (
                <button
                    onClick={goToStudio}
                    className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all active:scale-95"
                    style={{ background: 'linear-gradient(135deg, #a855f7, #6366f1)', boxShadow: '0 0 16px rgba(168,85,247,0.3)' }}
                >
                    영상 만들기
                    <ArrowRight className="w-3.5 h-3.5" />
                </button>
            ) : undefined}
        >
            {/* 파이프라인 설명 */}
            <div className="flex items-center gap-2 flex-wrap mb-8">
                {["목소리 샘플 등록", "→", "PDF 슬라이드 등록", "→", "AI 스크립트 생성", "→", "영상 완성"].map((step, i) => (
                    <span key={i} className={step === "→" ? "text-white/15 text-xs" : "px-3 py-1.5 rounded-full text-xs font-bold text-white/50"} style={step !== "→" ? { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' } : {}}>
                        {step}
                    </span>
                ))}
            </div>

            <div className="max-w-4xl grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* ─── VOICE SECTION ─── */}
                    <section className="relative">
                        <div className="absolute -top-2 -left-2 w-32 h-32 bg-brand-primary-500/10 rounded-full blur-[60px] pointer-events-none" />

                        <div className="relative premium-card rounded-3xl overflow-hidden border border-white/10 p-6">
                            {/* 섹션 헤더 */}
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-brand-primary-500/20 to-brand-primary-600/10 border border-brand-primary-500/30 flex items-center justify-center">
                                    <Mic className="w-5 h-5 text-brand-primary-400" />
                                </div>
                                <div>
                                    <h2 className="font-black text-white text-sm">목소리 샘플 등록</h2>
                                    <p className="text-white/50 text-[10px] mt-0.5">MP3 · WAV · M4A · FLAC · OGG</p>
                                </div>
                                {voiceState.done && (
                                    <CheckCircle className="w-5 h-5 text-green-400 ml-auto" />
                                )}
                            </div>

                            {/* 드롭존 */}
                            {!voiceState.file ? (
                                <div
                                    onDragEnter={e => voiceDrop.handleDrag(e, true)}
                                    onDragLeave={e => voiceDrop.handleDrag(e, false)}
                                    onDragOver={e => voiceDrop.handleDrag(e, true)}
                                    onDrop={voiceDrop.handleDrop}
                                    onClick={() => voiceDrop.inputRef.current?.click()}
                                    className={`relative border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all duration-300 ${
                                        voiceDrop.dragging
                                            ? "border-brand-primary-500 bg-brand-primary-500/10"
                                            : "border-white/10 hover:border-brand-primary-500/50 hover:bg-white/[0.02]"
                                    }`}
                                >
                                    <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center mb-4">
                                        <Upload className="w-7 h-7 text-white/30" />
                                    </div>
                                    <p className="text-white/50 text-sm font-bold mb-1">파일을 드래그하거나 클릭</p>
                                    <p className="text-white/45 text-xs">최소 1분 · 권장 3-5분</p>
                                    <input
                                        ref={voiceDrop.inputRef}
                                        type="file"
                                        accept=".mp3,.wav,.m4a,.flac,.ogg"
                                        className="hidden"
                                        onChange={voiceDrop.handleInput}
                                    />
                                </div>
                            ) : (
                                <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-4 mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 bg-brand-primary-500/20 rounded-xl flex items-center justify-center flex-shrink-0">
                                            <Volume2 className="w-5 h-5 text-brand-primary-400" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-bold text-white truncate">{voiceState.file.name}</p>
                                            <p className="text-xs text-white/30">{formatSize(voiceState.file.size)}</p>
                                        </div>
                                        {!voiceState.done && (
                                            <button
                                                onClick={() => {
                                                    setVoiceState({ file: null, uploading: false, done: false, error: null });
                                                    setAudioPreview(null);
                                                }}
                                                className="w-7 h-7 bg-white/5 hover:bg-white/10 rounded-lg flex items-center justify-center transition-colors"
                                            >
                                                <X className="w-3.5 h-3.5 text-white/50" />
                                            </button>
                                        )}
                                    </div>
                                    {audioPreview && (
                                        <audio controls src={audioPreview} className="mt-3 w-full h-8 opacity-70" />
                                    )}
                                </div>
                            )}

                            {/* 메타 입력 */}
                            {voiceState.file && !voiceState.done && (
                                <div className="space-y-3 mt-4">
                                    <div>
                                        <label className="text-[10px] font-black text-white/50 uppercase tracking-widest block mb-1.5">
                                            목소리 이름 *
                                        </label>
                                        <input
                                            value={voiceName}
                                            onChange={e => setVoiceName(e.target.value)}
                                            placeholder="예: 강대표 목소리"
                                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-brand-primary-500/50 transition-colors"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] font-black text-white/50 uppercase tracking-widest block mb-1.5">
                                            설명 (선택)
                                        </label>
                                        <input
                                            value={voiceDesc}
                                            onChange={e => setVoiceDesc(e.target.value)}
                                            placeholder="예: 남성, 차분한 톤, 비즈니스용"
                                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-brand-primary-500/50 transition-colors"
                                        />
                                    </div>

                                    {voiceState.error && (
                                        <div className="flex items-center gap-2 text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
                                            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                                            {voiceState.error}
                                        </div>
                                    )}

                                    <button
                                        onClick={uploadVoice}
                                        disabled={voiceState.uploading || !voiceName.trim()}
                                        className="w-full py-3 bg-gradient-to-r from-brand-primary-600 to-brand-primary-700 rounded-xl font-black text-sm tracking-wider disabled:opacity-40 hover:opacity-90 active:scale-95 transition-all flex items-center justify-center gap-2"
                                    >
                                        {voiceState.uploading ? (
                                            <>
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                학습 중...
                                            </>
                                        ) : (
                                            <>
                                                <Mic className="w-4 h-4" />
                                                목소리 등록
                                            </>
                                        )}
                                    </button>
                                </div>
                            )}

                            {/* 완료 상태 */}
                            {voiceState.done && voiceResult && (
                                <div className="mt-4 bg-green-500/10 border border-green-500/20 rounded-2xl p-4">
                                    <div className="flex items-center gap-2 mb-2">
                                        <CheckCircle className="w-4 h-4 text-green-400" />
                                        <span className="text-green-400 font-bold text-sm">목소리 등록 완료</span>
                                    </div>
                                    <p className="text-white/50 text-xs">이름: {voiceResult.voice_name}</p>
                                    <p className="text-white/50 text-[10px] font-mono mt-1 truncate">
                                        ID: {voiceResult.voice_id}
                                    </p>
                                </div>
                            )}
                        </div>
                    </section>

                    {/* ─── PDF SECTION ─── */}
                    <section className="relative">
                        <div className="absolute -top-2 -right-2 w-32 h-32 bg-brand-secondary-500/10 rounded-full blur-[60px] pointer-events-none" />

                        <div className="relative premium-card rounded-3xl overflow-hidden border border-white/10 p-6">
                            {/* 섹션 헤더 */}
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-brand-secondary-500/20 to-brand-secondary-600/10 border border-brand-secondary-500/30 flex items-center justify-center">
                                    <FileText className="w-5 h-5 text-brand-secondary-400" />
                                </div>
                                <div>
                                    <h2 className="font-black text-white text-sm">PDF 슬라이드 등록</h2>
                                    <p className="text-white/50 text-[10px] mt-0.5">NotebookLM · PowerPoint 내보내기</p>
                                </div>
                                {pdfState.done && (
                                    <CheckCircle className="w-5 h-5 text-green-400 ml-auto" />
                                )}
                            </div>

                            {/* 드롭존 */}
                            {!pdfState.file ? (
                                <div
                                    onDragEnter={e => pdfDrop.handleDrag(e, true)}
                                    onDragLeave={e => pdfDrop.handleDrag(e, false)}
                                    onDragOver={e => pdfDrop.handleDrag(e, true)}
                                    onDrop={pdfDrop.handleDrop}
                                    onClick={() => pdfDrop.inputRef.current?.click()}
                                    className={`relative border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all duration-300 ${
                                        pdfDrop.dragging
                                            ? "border-brand-secondary-500 bg-brand-secondary-500/10"
                                            : "border-white/10 hover:border-brand-secondary-500/50 hover:bg-white/[0.02]"
                                    }`}
                                >
                                    <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center mb-4">
                                        <FileText className="w-7 h-7 text-white/30" />
                                    </div>
                                    <p className="text-white/50 text-sm font-bold mb-1">PDF를 드래그하거나 클릭</p>
                                    <p className="text-white/45 text-xs">NotebookLM 슬라이드 PDF 권장</p>
                                    <input
                                        ref={pdfDrop.inputRef}
                                        type="file"
                                        accept=".pdf"
                                        className="hidden"
                                        onChange={pdfDrop.handleInput}
                                    />
                                </div>
                            ) : (
                                <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-4 mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 bg-brand-secondary-500/20 rounded-xl flex items-center justify-center flex-shrink-0">
                                            <FileText className="w-5 h-5 text-brand-secondary-400" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-bold text-white truncate">{pdfState.file.name}</p>
                                            <p className="text-xs text-white/30">{formatSize(pdfState.file.size)}</p>
                                        </div>
                                        {!pdfState.done && (
                                            <button
                                                onClick={() => setPdfState({ file: null, uploading: false, done: false, error: null })}
                                                className="w-7 h-7 bg-white/5 hover:bg-white/10 rounded-lg flex items-center justify-center transition-colors"
                                            >
                                                <X className="w-3.5 h-3.5 text-white/50" />
                                            </button>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* 업로드 버튼 */}
                            {pdfState.file && !pdfState.done && (
                                <div className="mt-4 space-y-3">
                                    {pdfState.error && (
                                        <div className="flex items-center gap-2 text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
                                            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                                            {pdfState.error}
                                        </div>
                                    )}

                                    <button
                                        onClick={uploadPdf}
                                        disabled={pdfState.uploading}
                                        className="w-full py-3 bg-gradient-to-r from-brand-secondary-600 to-brand-secondary-700 rounded-xl font-black text-sm tracking-wider disabled:opacity-40 hover:opacity-90 active:scale-95 transition-all flex items-center justify-center gap-2"
                                    >
                                        {pdfState.uploading ? (
                                            <>
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                슬라이드 분석 중...
                                            </>
                                        ) : (
                                            <>
                                                <FileText className="w-4 h-4" />
                                                PDF 등록
                                            </>
                                        )}
                                    </button>
                                </div>
                            )}

                            {/* 완료 상태 */}
                            {pdfState.done && pdfResult && (
                                <div className="mt-4 bg-green-500/10 border border-green-500/20 rounded-2xl p-4">
                                    <div className="flex items-center gap-2 mb-2">
                                        <CheckCircle className="w-4 h-4 text-green-400" />
                                        <span className="text-green-400 font-bold text-sm">PDF 등록 완료</span>
                                    </div>
                                    <p className="text-white/50 text-xs">
                                        {pdfResult.slide_count > 0
                                            ? `슬라이드 ${pdfResult.slide_count}장 추출됨`
                                            : pdfResult.message}
                                    </p>
                                    <p className="text-white/50 text-[10px] font-mono mt-1 truncate">
                                        ID: {pdfResult.presentation_id}
                                    </p>
                                </div>
                            )}
                        </div>
                    </section>
                </div>

                {/* ─── 하단: 영상 만들기 CTA ─── */}
                {bothReady && (
                    <div className="mt-10 relative">
                        <div className="absolute inset-0 bg-gradient-to-r from-brand-primary-500/10 via-brand-secondary-500/10 to-brand-primary-500/10 rounded-3xl blur-xl" />
                        <div className="relative premium-card rounded-3xl border border-white/10 p-8 flex flex-col items-center text-center">
                            <div className="w-16 h-16 rounded-[2rem] bg-gradient-to-br from-brand-primary-500 to-brand-secondary-600 flex items-center justify-center mb-5 shadow-2xl shadow-purple-500/40">
                                <Zap className="w-8 h-8 text-white fill-white/20" />
                            </div>
                            <h3 className="text-2xl font-black font-outfit premium-gradient-text tracking-tighter mb-2">
                                재료 준비 완료!
                            </h3>
                            <p className="text-white/40 text-sm mb-8">
                                목소리와 PDF가 모두 등록되었습니다. 스튜디오에서 AI가 영상을 완성합니다.
                            </p>
                            <button
                                onClick={goToStudio}
                                className="flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-brand-primary-600 to-brand-secondary-600 rounded-2xl font-black text-base shadow-2xl shadow-purple-500/30 hover:shadow-purple-500/50 hover:scale-105 active:scale-95 transition-all"
                            >
                                <Play className="w-5 h-5 fill-white" />
                                영상 만들기 →
                            </button>
                        </div>
                    </div>
                )}

                {/* ─── 가이드 ─── */}
                <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                        {
                            step: "01",
                            title: "목소리 샘플",
                            desc: "3-5분 분량의 맑은 음성 파일을 준비하세요. 소음이 없는 환경에서 녹음하면 최상의 결과를 얻을 수 있습니다.",
                            color: "brand-primary",
                        },
                        {
                            step: "02",
                            title: "PDF 슬라이드",
                            desc: "NotebookLM이나 PowerPoint에서 PDF로 내보낸 슬라이드를 업로드하면 AI가 슬라이드별 스크립트를 자동 생성합니다.",
                            color: "brand-secondary",
                        },
                        {
                            step: "03",
                            title: "AI 영상 완성",
                            desc: "등록된 재료를 기반으로 AI가 스크립트 → 음성 → 영상 렌더링을 자동으로 처리합니다.",
                            color: "brand-primary",
                        },
                    ].map(({ step, title, desc, color }) => (
                        <div key={step} className="bg-white/[0.02] border border-white/5 rounded-2xl p-5">
                            <div className={`text-${color}-500 text-xs font-black tracking-widest mb-3`}>{step}</div>
                            <h4 className="font-bold text-white text-sm mb-2">{title}</h4>
                            <p className="text-white/50 text-xs leading-relaxed">{desc}</p>
                        </div>
                    ))}
                </div>
        </AppShell>
    );
}
