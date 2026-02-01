/**
 * 실시간 진행률 표시 컴포넌트
 *
 * Features:
 * - WebSocket 기반 실시간 진행률 업데이트
 * - 폴링 Fallback 지원
 * - 연결 상태 표시
 * - 에러 처리
 */

'use client'

import { useWebSocket, WebSocketMessage } from '@/hooks/useWebSocket'
import { useState } from 'react'

interface ProgressBarProps {
  projectId: string
  onCompleted?: (result: any) => void
  onError?: (error: string) => void
  className?: string
  backendUrl?: string
  showConnectionStatus?: boolean
}

export function ProgressBar({
  projectId,
  onCompleted,
  onError: onErrorProp,
  className = '',
  backendUrl = 'localhost:8000',
  showConnectionStatus = true
}: ProgressBarProps) {
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle')

  const { isConnected, isFallback, reconnectAttempts } = useWebSocket({
    projectId,
    backendUrl,
    onProgress: (prog, msg) => {
      setProgress(prog * 100) // 0-1을 0-100으로
      setMessage(msg)
      setStatus('running')
      setError(null)
    },
    onError: (err) => {
      setError(err)
      setStatus('error')
      onErrorProp?.(err)
    },
    onCompleted: (result) => {
      setProgress(100)
      setMessage('완료!')
      setStatus('completed')
      onCompleted?.(result)
    },
    onMessage: (msg: WebSocketMessage) => {
      // 추가 메시지 처리
      if (msg.type === 'connected') {
        setStatus('idle')
      }
    }
  })

  // 진행률에 따른 색상 결정
  const getProgressColor = () => {
    if (status === 'error') return 'bg-red-600'
    if (status === 'completed') return 'bg-green-600'
    if (progress < 30) return 'bg-blue-400'
    if (progress < 70) return 'bg-blue-500'
    return 'bg-blue-600'
  }

  // 연결 상태 색상
  const getConnectionColor = () => {
    if (isConnected) return 'bg-green-500'
    if (isFallback) return 'bg-yellow-500'
    if (reconnectAttempts > 0) return 'bg-orange-500'
    return 'bg-gray-400'
  }

  // 연결 상태 텍스트
  const getConnectionText = () => {
    if (isFallback) return '폴링 모드'
    if (isConnected) return '실시간 연결'
    if (reconnectAttempts > 0) return `재연결 중... (${reconnectAttempts})`
    return '연결 중...'
  }

  return (
    <div className={`w-full ${className}`}>
      {/* 연결 상태 표시 */}
      {showConnectionStatus && (
        <div className="flex items-center gap-2 mb-2">
          <div className={`w-2 h-2 rounded-full ${getConnectionColor()} animate-pulse`} />
          <span className="text-sm text-gray-600">
            {getConnectionText()}
          </span>
        </div>
      )}

      {/* 진행률 바 */}
      <div className="w-full bg-gray-200 rounded-full h-4 mb-2 overflow-hidden">
        <div
          className={`h-4 rounded-full transition-all duration-300 ${getProgressColor()}`}
          style={{ width: `${progress}%` }}
        >
          {/* 애니메이션 효과 (로딩 중일 때) */}
          {status === 'running' && progress < 100 && (
            <div className="h-full w-full bg-gradient-to-r from-transparent via-white to-transparent opacity-20 animate-shimmer" />
          )}
        </div>
      </div>

      {/* 메시지 및 진행률 */}
      <div className="flex justify-between text-sm">
        <span className={`${
          status === 'error' ? 'text-red-700' :
          status === 'completed' ? 'text-green-700' :
          'text-gray-700'
        }`}>
          {message || '대기 중...'}
        </span>
        <span className="text-gray-500 font-medium">
          {progress.toFixed(1)}%
        </span>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="mt-2 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
          <div className="flex items-start gap-2">
            <svg
              className="w-5 h-5 flex-shrink-0 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1">
              <div className="font-semibold">오류 발생</div>
              <div className="mt-1">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* 완료 메시지 */}
      {status === 'completed' && (
        <div className="mt-2 p-3 bg-green-50 border border-green-200 text-green-700 rounded-md text-sm">
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <span className="font-semibold">작업이 성공적으로 완료되었습니다!</span>
          </div>
        </div>
      )}
    </div>
  )
}

// Shimmer 애니메이션을 위한 global CSS 추가 필요
// globals.css에 다음 추가:
/*
@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.animate-shimmer {
  animation: shimmer 2s infinite;
}
*/
