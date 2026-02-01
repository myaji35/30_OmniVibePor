/**
 * WebSocket 테스트 페이지
 *
 * ProgressBar 컴포넌트와 useWebSocket 훅을 테스트하는 전용 페이지
 *
 * 사용법:
 * 1. npm run dev로 프론트엔드 실행
 * 2. http://localhost:3020/test-websocket 접속
 * 3. Task ID 입력 후 "연결 시작" 클릭
 * 4. 백엔드에서 WebSocket 메시지를 전송하면 실시간으로 진행률 업데이트
 */

'use client'

import { useState } from 'react'
import { ProgressBar } from '@/components/ProgressBar'

export default function TestWebSocketPage() {
  const [taskId, setTaskId] = useState('')
  const [isMonitoring, setIsMonitoring] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handleStart = () => {
    if (!taskId.trim()) {
      alert('Task ID를 입력하세요')
      return
    }

    setIsMonitoring(true)
    setResult(null)
    setError(null)
  }

  const handleReset = () => {
    setTaskId('')
    setIsMonitoring(false)
    setResult(null)
    setError(null)
  }

  const handleCompleted = (completedResult: any) => {
    console.log('[TestPage] Task completed:', completedResult)
    setResult(completedResult)
    setIsMonitoring(false)
  }

  const handleError = (errorMessage: string) => {
    console.error('[TestPage] Task failed:', errorMessage)
    setError(errorMessage)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">
            WebSocket 진행률 테스트
          </h1>
          <p className="text-gray-400 max-w-2xl mx-auto">
            ProgressBar 컴포넌트와 useWebSocket 훅의 실시간 진행률 추적, 자동 재연결, 폴링 Fallback 기능을 테스트합니다.
          </p>
        </div>

        {/* Main Card */}
        <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-2xl overflow-hidden">
          {/* Card Header */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6">
            <h2 className="text-2xl font-bold text-white mb-2">
              실시간 작업 모니터링
            </h2>
            <p className="text-blue-100">
              Task ID를 입력하여 백엔드 작업의 진행 상황을 추적하세요
            </p>
          </div>

          {/* Card Body */}
          <div className="p-8">
            {/* Input Section */}
            {!isMonitoring && (
              <div className="space-y-6">
                <div>
                  <label htmlFor="taskId" className="block text-sm font-medium text-gray-700 mb-2">
                    Task ID
                  </label>
                  <input
                    id="taskId"
                    type="text"
                    value={taskId}
                    onChange={(e) => setTaskId(e.target.value)}
                    placeholder="예: audio_generation_12345"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                    onKeyPress={(e) => e.key === 'Enter' && handleStart()}
                  />
                  <p className="mt-2 text-sm text-gray-500">
                    백엔드에서 생성된 Task ID를 입력하세요
                  </p>
                </div>

                <button
                  onClick={handleStart}
                  className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 font-semibold text-lg shadow-lg transition-all"
                >
                  연결 시작
                </button>

                {/* Example Tasks */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-2">예시 Task ID</h3>
                  <div className="space-y-2">
                    <button
                      onClick={() => setTaskId('test_task_001')}
                      className="w-full text-left px-3 py-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-sm text-gray-700"
                    >
                      test_task_001
                    </button>
                    <button
                      onClick={() => setTaskId('audio_generation_12345')}
                      className="w-full text-left px-3 py-2 bg-white border border-gray-300 rounded hover:bg-gray-50 text-sm text-gray-700"
                    >
                      audio_generation_12345
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Progress Section */}
            {isMonitoring && (
              <div className="space-y-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-800">
                    <span className="font-semibold">Task ID:</span> {taskId}
                  </p>
                </div>

                {/* ProgressBar Component */}
                <ProgressBar
                  projectId={taskId}
                  onCompleted={handleCompleted}
                  onError={handleError}
                  showConnectionStatus={true}
                />

                <button
                  onClick={handleReset}
                  className="w-full px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium"
                >
                  초기화
                </button>
              </div>
            )}

            {/* Result Section */}
            {result && (
              <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  작업 완료 결과
                </h3>
                <pre className="bg-white border border-green-300 rounded p-4 text-sm text-gray-800 overflow-x-auto">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>

        {/* Features List */}
        <div className="max-w-3xl mx-auto mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg p-6 shadow-lg">
            <div className="text-3xl mb-3">🔄</div>
            <h3 className="font-semibold text-gray-900 mb-2">자동 재연결</h3>
            <p className="text-sm text-gray-600">
              연결이 끊어지면 exponential backoff 알고리즘으로 자동 재연결합니다
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-lg">
            <div className="text-3xl mb-3">📊</div>
            <h3 className="font-semibold text-gray-900 mb-2">폴링 Fallback</h3>
            <p className="text-sm text-gray-600">
              WebSocket 실패 시 자동으로 HTTP 폴링으로 전환하여 안정성을 보장합니다
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-lg">
            <div className="text-3xl mb-3">💓</div>
            <h3 className="font-semibold text-gray-900 mb-2">Keep-alive</h3>
            <p className="text-sm text-gray-600">
              30초마다 ping을 전송하여 연결 상태를 유지하고 타임아웃을 방지합니다
            </p>
          </div>
        </div>

        {/* Backend Setup Instructions */}
        <div className="max-w-3xl mx-auto mt-12 bg-gray-800 rounded-lg p-6 text-gray-100">
          <h3 className="font-semibold text-xl mb-4 flex items-center gap-2">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            백엔드 설정 방법
          </h3>
          <div className="space-y-3 text-sm">
            <p>
              1. 백엔드 서버가 <code className="bg-gray-700 px-2 py-1 rounded">localhost:8000</code>에서 실행 중이어야 합니다
            </p>
            <p>
              2. WebSocket 엔드포인트: <code className="bg-gray-700 px-2 py-1 rounded">ws://localhost:8000/api/v1/ws/projects/{`{task_id}`}/stream</code>
            </p>
            <p>
              3. 폴링 엔드포인트: <code className="bg-gray-700 px-2 py-1 rounded">GET /api/v1/projects/{`{task_id}`}/status</code>
            </p>
            <p className="text-yellow-400">
              ⚠️ 백엔드에서 위 엔드포인트가 구현되어 있어야 정상 작동합니다
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
