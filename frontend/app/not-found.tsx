export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f1117] text-white">
      <div className="text-center space-y-4">
        <h2 className="text-xl font-bold">페이지를 찾을 수 없습니다</h2>
        <a
          href="/"
          className="inline-block px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-medium hover:bg-purple-500 transition-colors"
        >
          홈으로 돌아가기
        </a>
      </div>
    </div>
  )
}
