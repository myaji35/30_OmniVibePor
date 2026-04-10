'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f1117] text-white">
      <div className="text-center space-y-4">
        <h2 className="text-xl font-bold">오류가 발생했습니다</h2>
        <p className="text-white/50 text-sm">{error.message}</p>
        <button
          onClick={reset}
          className="px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-medium hover:bg-purple-500 transition-colors"
        >
          다시 시도
        </button>
      </div>
    </div>
  )
}
