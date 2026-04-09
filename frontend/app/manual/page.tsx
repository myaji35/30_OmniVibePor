'use client'

import { useState } from 'react'
import Link from 'next/link'
import AppShell from '@/components/AppShell'
import {
  BookOpen, Download, FileText, Film, Mic, Upload, Play,
  CheckCircle2, ArrowRight, Clock, Users, Sparkles, Stethoscope,
} from 'lucide-react'

// ── 매뉴얼 섹션 데이터 ──────────────────────────────────────
// 버전 관리: docs/manual/manual.meta.json 에서 동적 로드 예정 (v2)
const MANUAL_SECTIONS = [
  {
    id: 'quick-start',
    icon: Sparkles,
    title: '빠른 시작 (5분)',
    description: 'PDF 업로드부터 영상 다운로드까지 5분 안에 첫 영상을 만들어 봅니다.',
    steps: [
      'PDF 업로드: 병원 팜플렛 또는 시술 소개서',
      'AI 스크립트 자동 생성',
      'TTS 음성 + 자막 자동 합성',
      '영상 렌더링 + MP4 다운로드',
    ],
  },
  {
    id: 'clinic-case',
    icon: Stethoscope,
    title: '병의원 홍보 영상 — 실전 예시',
    description: '피부과·치과·한의원의 월간 프로모션 영상을 OmniVibe로 제작하는 전체 과정',
    steps: [
      '거래처 정보 등록 (원장 사진, 로고, 시술 목록)',
      '이달의 시술 선택 (예: 5월 어버이날 보톡스)',
      'Compliance Pack 자동 검증 (의료광고법)',
      '9개 영상 자동 생성 (60s/30s/15s × 9:16/1:1/16:9)',
      '검수 링크 원장에게 발송 → 승인 → 자동 배포',
    ],
  },
  {
    id: 'strategy',
    icon: Film,
    title: '전략 수립',
    description: 'AI Director가 채널별 전략과 주간 캘린더를 자동 생성',
    href: '/strategy',
  },
  {
    id: 'concept',
    icon: FileText,
    title: '컨셉 기획',
    description: '스크립트 자동 생성 + 스토리보드 시각화',
    href: '/concept',
  },
  {
    id: 'produce',
    icon: Film,
    title: '콘텐츠 생산',
    description: '영상 · 프레젠테이션 · 나레이션 자동 제작',
    href: '/produce',
  },
  {
    id: 'audio',
    icon: Mic,
    title: 'Zero-Fault 오디오',
    description: 'TTS + STT 검증 루프로 99% 정확도 달성',
    href: '/audio',
  },
]

const FAQ = [
  {
    q: 'PDF가 없어도 영상을 만들 수 있나요?',
    a: '네. 스크립트 텍스트만으로도 영상 생성이 가능합니다. "콘텐츠 생산" 메뉴에서 "스크립트 모드"를 선택하세요.',
  },
  {
    q: '의료 광고 영상은 법적으로 문제없나요?',
    a: 'OmniVibe Pro의 Compliance Pack이 의료광고법 위반 표현을 자동으로 검출하고 대체 표현을 제안합니다. 단, 최종 광고 송출 책임은 회원사와 거래처에 있으며, 필요시 의료광고심의위원회의 사전 심의를 받으시기 바랍니다.',
  },
  {
    q: 'iPhone에서 영상이 깨져요.',
    a: 'OmniVibe Pro는 iOS 호환 표준(H.264 High@4.1, yuv420p, 30fps CFR, 48kHz AAC, faststart)을 자동 적용합니다. 카카오톡 공유 시에도 정상 재생됩니다. 만약 문제가 있으면 "공유 & 추적"에서 영상을 다시 내보내세요.',
  },
  {
    q: '월 몇 편까지 만들 수 있나요?',
    a: 'Starter 플랜 월 9편, Pro 플랜 월 50편, Studio 플랜 무제한입니다. 자세한 내용은 "가격" 페이지를 참조하세요.',
  },
  {
    q: '회원사(거래처)를 여러 개 관리할 수 있나요?',
    a: '네. 1인 에이전시 회원은 여러 거래처를 독립적으로 관리할 수 있습니다. 각 거래처마다 브랜드 템플릿·시술 라이브러리·프로모션 캘린더가 분리되어 있습니다.',
  },
]

export default function ManualPage() {
  const [activeSection, setActiveSection] = useState<string>('quick-start')

  return (
    <AppShell
      title="사용자 매뉴얼"
      subtitle="OmniVibe Pro 사용법 가이드 — 병의원 홍보 영상 제작 예시 포함"
      actions={
        <a
          href="/docs/manual/omnivibe-pro-manual.pdf"
          download
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#00A1E0] hover:bg-[#0090CC] text-white text-sm font-semibold transition-colors"
        >
          <Download className="w-4 h-4" />
          PDF 다운로드
        </a>
      }
    >
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* 상단 메타 카드 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-2 text-gray-600 mb-1">
              <Clock className="w-4 h-4" />
              <span className="text-xs font-semibold">버전</span>
            </div>
            <p className="text-lg font-bold text-[#16325C]">v1.0 (2026-04-09)</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-2 text-gray-600 mb-1">
              <Users className="w-4 h-4" />
              <span className="text-xs font-semibold">대상</span>
            </div>
            <p className="text-sm font-bold text-[#16325C]">1인 마케팅 에이전시</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-2 text-gray-600 mb-1">
              <BookOpen className="w-4 h-4" />
              <span className="text-xs font-semibold">섹션</span>
            </div>
            <p className="text-sm font-bold text-[#16325C]">
              {MANUAL_SECTIONS.length}개 + FAQ {FAQ.length}개
            </p>
          </div>
        </div>

        {/* 섹션 네비게이션 */}
        <div className="flex flex-wrap gap-2 mb-6 pb-4 border-b border-gray-200">
          {MANUAL_SECTIONS.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setActiveSection(s.id)}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                activeSection === s.id
                  ? 'bg-[#00A1E0] text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <s.icon className="w-4 h-4" />
              {s.title}
            </button>
          ))}
        </div>

        {/* 활성 섹션 */}
        {MANUAL_SECTIONS.filter((s) => s.id === activeSection).map((s) => (
          <div key={s.id} className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <div className="flex items-start gap-4 mb-4">
              <div className="w-12 h-12 rounded-lg bg-[#00A1E0]/10 flex items-center justify-center shrink-0">
                <s.icon className="w-6 h-6 text-[#00A1E0]" />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-bold text-[#16325C] mb-1">{s.title}</h2>
                <p className="text-sm text-gray-600">{s.description}</p>
              </div>
            </div>

            {s.steps && (
              <ol className="space-y-3 mt-6">
                {s.steps.map((step, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-[#00A1E0] text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                      {idx + 1}
                    </div>
                    <p className="text-sm text-gray-900 leading-relaxed">{step}</p>
                  </li>
                ))}
              </ol>
            )}

            {s.href && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <Link
                  href={s.href}
                  className="inline-flex items-center gap-2 text-sm font-semibold text-[#00A1E0] hover:text-[#0090CC]"
                >
                  {s.title} 페이지로 이동
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            )}
          </div>
        ))}

        {/* FAQ 섹션 */}
        <div className="mt-12">
          <h2 className="text-xl font-bold text-[#16325C] mb-4">자주 묻는 질문</h2>
          <div className="space-y-3">
            {FAQ.map((item, idx) => (
              <details
                key={idx}
                className="bg-white rounded-lg border border-gray-200 p-4 group"
              >
                <summary className="cursor-pointer list-none flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-[#00A1E0] shrink-0 mt-0.5" />
                  <span className="flex-1 text-sm font-semibold text-[#16325C]">
                    {item.q}
                  </span>
                  <ArrowRight className="w-4 h-4 text-gray-400 group-open:rotate-90 transition-transform shrink-0 mt-0.5" />
                </summary>
                <p className="mt-3 ml-8 text-sm text-gray-700 leading-relaxed">
                  {item.a}
                </p>
              </details>
            ))}
          </div>
        </div>

        {/* 하단 지원 카드 */}
        <div className="mt-12 bg-gradient-to-br from-[#00A1E0]/5 to-[#16325C]/5 rounded-lg border border-[#00A1E0]/20 p-6 text-center">
          <h3 className="text-lg font-bold text-[#16325C] mb-2">추가 도움이 필요하신가요?</h3>
          <p className="text-sm text-gray-600 mb-4">
            매뉴얼에서 답을 찾지 못하셨다면 문의 채널로 연락 주세요.
          </p>
          <div className="flex justify-center gap-3">
            <a
              href="mailto:support@omnivibepro.com"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#00A1E0] hover:bg-[#0090CC] text-white text-sm font-semibold transition-colors"
            >
              이메일 문의
            </a>
            <a
              href="/docs/manual/omnivibe-pro-manual.pdf"
              download
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-gray-300 hover:bg-gray-50 text-[#16325C] text-sm font-semibold transition-colors"
            >
              <Download className="w-4 h-4" />
              PDF 다운로드
            </a>
          </div>
        </div>

        {/* 푸터 메타 */}
        <div className="mt-12 pt-6 border-t border-gray-200 text-xs text-gray-500 text-center">
          OmniVibe Pro 사용자 매뉴얼 · v1.0 · 2026-04-09 ·{' '}
          <Link href="/docs/manual/CHANGELOG.md" className="text-[#00A1E0] hover:underline">
            변경 이력
          </Link>
        </div>
      </div>
    </AppShell>
  )
}
