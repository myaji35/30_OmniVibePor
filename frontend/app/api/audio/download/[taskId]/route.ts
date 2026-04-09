import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

// ISS-062: Next.js fetch 캐싱 방지 (파일 응답이라 캐시되면 안 됨)
export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET(
  _request: NextRequest,
  { params }: { params: { taskId: string } }
) {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/audio/download/${params.taskId}`,
      { cache: 'no-store' }
    )

    if (!response.ok) {
      return NextResponse.json({ error: '다운로드 실패' }, { status: response.status })
    }

    const blob = await response.blob()
    return new NextResponse(blob, {
      status: 200,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'audio/mpeg',
        'Content-Disposition': `attachment; filename="audio_${params.taskId}.mp3"`,
      },
    })
  } catch (error) {
    console.error('Audio download proxy error:', error)
    return NextResponse.json({ error: '다운로드 요청 실패' }, { status: 500 })
  }
}
