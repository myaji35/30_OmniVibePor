'use client'

import React from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'

// ── 에러 코드별 사용자 메시지 ────────────────────────────────────────
const ERROR_MESSAGES: Record<string, { title: string; desc: string; action: string }> = {
  CREDIT_EXHAUSTED: {
    title: 'API 크레딧 부족',
    desc:  '이번 달 사용량이 초과되었습니다. 플랜을 업그레이드하세요.',
    action: '빌링 페이지로 이동',
  },
  QUOTA_EXCEEDED: {
    title: '사용량 한도 초과',
    desc:  '플랜의 월 한도를 초과했습니다.',
    action: '플랜 업그레이드',
  },
  RENDER_OOM: {
    title: '렌더링 메모리 부족',
    desc:  '영상 해상도를 낮추거나 길이를 줄여보세요.',
    action: '다시 시도',
  },
  WORKER_DOWN: {
    title: '서버 점검 중',
    desc:  '잠시 후 다시 시도해주세요.',
    action: '새로고침',
  },
  DEFAULT: {
    title: '예상치 못한 오류',
    desc:  '일시적인 오류가 발생했습니다.',
    action: '새로고침',
  },
}

interface ErrorBoundaryState {
  hasError:  boolean
  errorCode: string
  message:   string
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  /** 에러 발생 시 fallback으로 보여줄 커스텀 UI (선택) */
  fallback?: React.ReactNode
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, errorCode: 'DEFAULT', message: '' }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    const errorCode = (error as any).error_code ?? 'DEFAULT'
    return { hasError: true, errorCode, message: error.message }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary]', error, info)
    // TODO: 프로덕션에서 Sentry 등으로 전송
  }

  handleRetry = () => {
    this.setState({ hasError: false, errorCode: 'DEFAULT', message: '' })
  }

  render() {
    if (!this.state.hasError) return this.props.children
    if (this.props.fallback) return this.props.fallback

    const info = ERROR_MESSAGES[this.state.errorCode] ?? ERROR_MESSAGES.DEFAULT

    return (
      <div className="min-h-[400px] flex items-center justify-center p-8">
        <div className="max-w-md w-full text-center space-y-5">
          {/* 아이콘 */}
          <div className="w-16 h-16 mx-auto rounded-full bg-red-500/10 border border-red-500/20
            flex items-center justify-center">
            <AlertTriangle className="w-7 h-7 text-red-400" />
          </div>

          {/* 에러 코드 뱃지 */}
          <div className="inline-block px-3 py-1 rounded-full bg-white/[0.05]
            border border-white/10 text-[10px] font-mono text-white/40 uppercase tracking-widest">
            {this.state.errorCode}
          </div>

          {/* 제목 & 설명 */}
          <div>
            <h2 className="text-lg font-bold text-white mb-1">{info.title}</h2>
            <p className="text-sm text-white/50">{info.desc}</p>
            {this.state.message && (
              <p className="mt-2 text-xs text-white/30 font-mono bg-white/[0.03]
                rounded-md px-3 py-2 text-left break-all">
                {this.state.message}
              </p>
            )}
          </div>

          {/* 액션 버튼 */}
          <div className="flex gap-3 justify-center">
            <button
              onClick={this.handleRetry}
              className="flex items-center gap-1.5 px-5 py-2 rounded-lg
                text-sm font-semibold transition-all
                bg-purple-500/15 border border-purple-500/30 text-purple-300
                hover:bg-purple-500/25"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              {info.action}
            </button>
            <a href="/"
              className="flex items-center gap-1.5 px-5 py-2 rounded-lg
                text-sm font-semibold transition-all
                bg-white/[0.05] border border-white/10 text-white/50
                hover:text-white/70 hover:bg-white/[0.08]"
            >
              <Home className="w-3.5 h-3.5" />
              홈으로
            </a>
          </div>
        </div>
      </div>
    )
  }
}

// ── 함수형 래퍼 (간편 사용) ──────────────────────────────────────────
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: React.ReactNode,
) {
  return function WrappedWithBoundary(props: P) {
    return (
      <ErrorBoundary fallback={fallback}>
        <Component {...props} />
      </ErrorBoundary>
    )
  }
}
