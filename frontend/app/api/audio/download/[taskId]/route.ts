import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function GET(
  _request: NextRequest,
  { params }: { params: { taskId: string } }
) {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/audio/download/${params.taskId}`
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
