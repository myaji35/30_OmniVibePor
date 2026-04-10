"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Globe,
  Loader2,
  Check,
  Building2,
  Phone,
  MapPin,
  Palette,
  Image as ImageIcon,
  AlertCircle,
  ArrowRight,
  Sparkles,
} from "lucide-react";

interface ExtractedBrand {
  name: string | null;
  logo_url: string | null;
  brand_color: string | null;
  tagline: string | null;
  address: string | null;
  phone: string | null;
  industry: string;
}

type Step = "input" | "extracting" | "review" | "saving";

export default function NewClientPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("input");
  const [url, setUrl] = useState("");
  const [extracted, setExtracted] = useState<ExtractedBrand | null>(null);
  const [confidence, setConfidence] = useState(0);
  const [error, setError] = useState("");

  // 편집 가능 필드
  const [editName, setEditName] = useState("");
  const [editColor, setEditColor] = useState("#00A1E0");
  const [editPhone, setEditPhone] = useState("");
  const [editAddress, setEditAddress] = useState("");
  const [editIndustry, setEditIndustry] = useState("general");

  const industries = [
    { value: "medical", label: "병의원" },
    { value: "academy", label: "학원" },
    { value: "mart", label: "마트" },
    { value: "beauty", label: "뷰티" },
    { value: "restaurant", label: "음식점" },
    { value: "fitness", label: "피트니스" },
    { value: "realestate", label: "부동산" },
    { value: "general", label: "일반" },
  ];

  async function handleExtract() {
    if (!url.trim()) return;
    setError("");
    setStep("extracting");

    try {
      const resp = await fetch("/api/clients/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ website_url: url.trim() }),
      });
      const data = await resp.json();

      if (data.success && data.extracted) {
        const ex = data.extracted;
        setExtracted(ex);
        setConfidence(data.confidence || 0);
        setEditName(ex.name || "");
        setEditColor(ex.brand_color || "#00A1E0");
        setEditPhone(ex.phone || "");
        setEditAddress(ex.address || "");
        setEditIndustry(ex.industry || "general");
        setStep("review");
      } else {
        setError(data.error || "추출 실패");
        setStep("input");
      }
    } catch (e: any) {
      setError(e.message || "네트워크 오류");
      setStep("input");
    }
  }

  async function handleSave() {
    setStep("saving");
    try {
      const resp = await fetch("/api/clients", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: editName,
          brand_color: editColor,
          logo_url: extracted?.logo_url || null,
          industry: editIndustry,
          contact_email: "",
          website_url: url,
          address: editAddress,
          phone: editPhone,
          tagline: extracted?.tagline || null,
        }),
      });
      if (resp.ok) {
        router.push("/dashboard");
      } else {
        setError("저장 실패");
        setStep("review");
      }
    } catch {
      setError("저장 실패");
      setStep("review");
    }
  }

  return (
    <div className="min-h-screen bg-[#F3F2F2] flex items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-lg" role="main" aria-label="새 거래처 등록">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl mb-4" style={{ background: "linear-gradient(135deg, #00A1E0 0%, #a855f7 100%)" }}>
            <Building2 className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-[#16325C]">새 거래처 등록</h1>
          <p className="text-sm text-[#706E6B] mt-1">
            홈페이지 URL만 입력하면 브랜드 정보를 자동 추출합니다
          </p>
        </div>

        {/* D1 Fix: Step Indicator */}
        <div className="flex items-center justify-center gap-2 mb-6">
          {[
            { key: "input", label: "URL 입력" },
            { key: "extracting", label: "추출" },
            { key: "review", label: "확인" },
          ].map((s, idx) => {
            const steps: Step[] = ["input", "extracting", "review", "saving"];
            const currentIdx = steps.indexOf(step);
            const thisIdx = idx;
            const isActive = thisIdx <= currentIdx;
            const isCurrent = s.key === step || (step === "saving" && s.key === "review");
            return (
              <div key={s.key} className="flex items-center gap-2">
                {idx > 0 && (
                  <div className={`w-8 h-0.5 ${isActive ? "bg-[#00A1E0]" : "bg-gray-200"}`} />
                )}
                <div className="flex items-center gap-1.5">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold ${
                      isCurrent
                        ? "bg-[#00A1E0] text-white"
                        : isActive
                        ? "bg-[#4BCA81] text-white"
                        : "bg-gray-200 text-gray-500"
                    }`}
                  >
                    {isActive && !isCurrent ? (
                      <Check className="w-3.5 h-3.5" />
                    ) : (
                      idx + 1
                    )}
                  </div>
                  <span
                    className={`text-xs ${
                      isCurrent ? "font-semibold text-[#16325C]" : "text-[#706E6B]"
                    }`}
                  >
                    {s.label}
                  </span>
                </div>
              </div>
            );
          })}</div>

        {/* Step 1: URL 입력 */}
        {step === "input" && (
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <label className="block text-xs font-semibold text-gray-600 mb-1.5">
              거래처 홈페이지 URL
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example-clinic.com"
                  className="w-full pl-10 px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#00A1E0] focus:ring-1 focus:ring-[#00A1E0]"
                  onKeyDown={(e) => e.key === "Enter" && handleExtract()}
                  autoFocus
                />
              </div>
              <button
                onClick={handleExtract}
                disabled={!url.trim()}
                className="px-5 py-2.5 text-white text-sm font-semibold rounded-lg disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 transition-all hover:shadow-md hover:scale-[1.02]"
                style={{ background: "linear-gradient(135deg, #00A1E0 0%, #a855f7 100%)" }}
              >
                <Sparkles className="w-4 h-4" />
                추출
              </button>
            </div>

            {error && (
              <div className="mt-3 flex items-center gap-2 text-sm" style={{ color: "#EA001E" }}>
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            )}

            <div className="mt-4 pt-4 border-t border-gray-100">
              <button
                onClick={() => {
                  setExtracted(null);
                  setStep("review");
                }}
                className="text-sm text-[#706E6B] hover:text-[#16325C] transition-colors"
              >
                홈페이지 없이 수동 입력 →
              </button>
            </div>
          </div>
        )}

        {/* Step 2: 추출 중 (D2 Fix: pulse progress) */}
        {step === "extracting" && (
          <div className="bg-white rounded-lg border border-gray-200 p-8 shadow-sm text-center">
            <Loader2 className="w-8 h-8 text-[#00A1E0] animate-spin mx-auto mb-4" />
            <p className="text-sm font-semibold text-[#16325C]">
              브랜드 정보 추출 중...
            </p>
            <p className="text-xs text-[#706E6B] mt-1 mb-4">{url}</p>
            <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-[#00A1E0] rounded-full animate-pulse" style={{ width: "70%" }} />
            </div>
            <div className="flex justify-between mt-2 text-[10px] text-[#706E6B]">
              <span>HTML 파싱</span>
              <span>로고 감지</span>
              <span>주소 추출</span>
            </div>
          </div>
        )}

        {/* Step 3: 리뷰 + 수정 */}
        {step === "review" && (
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
            {/* Confidence badge */}
            {extracted && (
              <div className="px-6 pt-5 pb-3 border-b border-gray-100 flex items-center justify-between">
                <span className="text-xs text-[#706E6B]">자동 추출 결과</span>
                <span
                  className="px-2.5 py-1 rounded-full text-xs font-semibold text-white"
                  style={{
                    background:
                      confidence >= 0.7
                        ? "#4BCA81"
                        : confidence >= 0.4
                        ? "#FFB75D"
                        : "#EA001E",
                  }}
                >
                  신뢰도 {Math.round(confidence * 100)}%
                </span>
              </div>
            )}

            {/* D5 Fix: Brand Preview Card */}
            {(editName || extracted?.logo_url) && (
              <div
                className="mx-6 mt-5 p-4 rounded-lg border border-gray-200 flex items-center gap-4"
                style={{ borderLeftWidth: 4, borderLeftColor: editColor }}
              >
                {extracted?.logo_url ? (
                  <img
                    src={extracted.logo_url}
                    alt=""
                    className="w-12 h-12 rounded-lg border border-gray-200 object-contain bg-white"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = "none";
                    }}
                  />
                ) : (
                  <div
                    className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-lg"
                    style={{ background: editColor }}
                  >
                    {editName.charAt(0) || "?"}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-[#16325C] truncate">
                    {editName || "거래처명"}
                  </p>
                  <p className="text-xs text-[#706E6B] truncate">
                    {extracted?.tagline || url || "태그라인"}
                  </p>
                </div>
                <div
                  className="w-8 h-8 rounded-full border-2 border-white shadow-sm"
                  style={{ background: editColor }}
                />
              </div>
            )}

            <div className="p-6 space-y-4">
              {/* 거래처명 */}
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                  거래처명
                </label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    placeholder="OO 병원"
                    className="w-full pl-10 px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#00A1E0] focus:ring-1 focus:ring-[#00A1E0]"
                  />
                </div>
              </div>

              {/* 업종 */}
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                  업종
                </label>
                <select
                  value={editIndustry}
                  onChange={(e) => setEditIndustry(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 bg-white focus:outline-none focus:border-[#00A1E0] focus:ring-1 focus:ring-[#00A1E0]"
                >
                  {industries.map((ind) => (
                    <option key={ind.value} value={ind.value}>
                      {ind.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* 브랜드 컬러 */}
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                  브랜드 컬러
                </label>
                <div className="flex items-center gap-3">
                  <Palette className="w-4 h-4 text-gray-400" />
                  <input
                    type="color"
                    value={editColor}
                    onChange={(e) => setEditColor(e.target.value)}
                    className="w-10 h-10 rounded border border-gray-300 cursor-pointer"
                  />
                  <span className="text-sm text-gray-600 font-mono">
                    {editColor}
                  </span>
                </div>
              </div>

              {/* 로고 미리보기 */}
              {extracted?.logo_url && (
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                    로고
                  </label>
                  <div className="flex items-center gap-3">
                    <ImageIcon className="w-4 h-4 text-gray-400" />
                    <img
                      src={extracted.logo_url}
                      alt="logo"
                      className="w-10 h-10 rounded border border-gray-200 object-contain"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = "none";
                      }}
                    />
                    <span className="text-xs text-[#706E6B] truncate max-w-[200px]">
                      {extracted.logo_url}
                    </span>
                  </div>
                </div>
              )}

              {/* D3 Fix: 태그라인 */}
              {extracted?.tagline && (
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                    태그라인 (자동 추출)
                  </label>
                  <p className="text-sm text-[#16325C] bg-gray-50 rounded-lg px-3 py-2 border border-gray-200">
                    {extracted.tagline}
                  </p>
                </div>
              )}

              {/* 전화번호 */}
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                  전화번호
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    value={editPhone}
                    onChange={(e) => setEditPhone(e.target.value)}
                    placeholder="02-1234-5678"
                    className="w-full pl-10 px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#00A1E0] focus:ring-1 focus:ring-[#00A1E0]"
                  />
                </div>
              </div>

              {/* 주소 */}
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                  주소
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                  <textarea
                    value={editAddress}
                    onChange={(e) => setEditAddress(e.target.value)}
                    placeholder="서울특별시 강남구..."
                    rows={2}
                    className="w-full pl-10 px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#00A1E0] focus:ring-1 focus:ring-[#00A1E0] resize-none"
                  />
                </div>
              </div>
            </div>

            {/* Actions (D10 Fix: sticky CTA for 0.5s rule) */}
            <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between sticky bottom-0 bg-white rounded-b-lg">
              <button
                onClick={() => {
                  setStep("input");
                  setExtracted(null);
                  setError("");
                }}
                className="text-sm text-[#706E6B] hover:text-[#16325C] transition-colors"
              >
                ← 다시 입력
              </button>
              <button
                onClick={handleSave}
                disabled={!editName.trim()}
                className="px-6 py-2.5 bg-[#00A1E0] text-white text-sm font-semibold rounded-lg hover:bg-[#0090c7] disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 transition-colors shadow-sm"
              >
                거래처 등록
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 4: 저장 중 / 성공 (D4 Fix) */}
        {step === "saving" && (
          <div className="bg-white rounded-lg border border-gray-200 p-8 shadow-sm text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[#4BCA81]/10 mb-4">
              <Loader2 className="w-7 h-7 text-[#00A1E0] animate-spin" />
            </div>
            <p className="text-sm font-semibold text-[#16325C]">
              거래처를 등록하고 있습니다...
            </p>
            <p className="text-xs text-[#706E6B] mt-1">{editName}</p>
          </div>
        )}
      </div>
    </div>
  );
}
