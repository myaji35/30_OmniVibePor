import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

// ISS-062: Next.js 14 fetch 기본 force-cache 동작으로 인해 task 상태가 첫 응답에 고정됨
// polling이 무한히 "진행 중" 상태로 멈추는 버그 방지를 위해 dynamic 강제 + no-store
export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET(
  _request: NextRequest,
  { params }: { params: { taskId: string } }
) {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/audio/status/${params.taskId}`,
      {
        // 캐시 비활성화 — 매 polling마다 최신 상태 조회 (Next.js는 cache:no-store만 사용)
        cache: 'no-store',
      }
    )

    const data = await response.json()
    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Cache-Control': 'no-store, no-cache, must-revalidate',
      },
    })
  } catch (error) {
    console.error('Audio status proxy error:', error)
    return NextResponse.json({ error: '상태 확인 실패' }, { status: 500 })
  }
}
