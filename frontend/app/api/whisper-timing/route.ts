import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * POST /api/whisper-timing — Whisper 재분석 프록시
 * ScriptSubtitleSync에서 'Whisper 재분석' 버튼 클릭 시 호출
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const res = await fetch(`${BACKEND_URL}/api/v1/whisper/timing/reanalyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!res.ok) {
      const error = await res.text()
      return NextResponse.json(
        { error: `Backend error: ${error}` },
        { status: res.status }
      )
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: `Whisper timing failed: ${String(error)}` },
      { status: 500 }
    )
  }
}
