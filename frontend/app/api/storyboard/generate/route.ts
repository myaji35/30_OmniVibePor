import { NextRequest, NextResponse } from 'next/server'

/**
 * POST /api/storyboard/generate
 * 스크립트로부터 콘티 블록 자동 생성
 */
export async function POST(request: NextRequest) {
  try {
    const { script, campaign_concept } = await request.json()

    if (!script || typeof script !== 'string') {
      return NextResponse.json(
        { error: '스크립트를 입력해주세요' },
        { status: 400 }
      )
    }

    // Backend API 호출
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/api/v1/storyboard/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        script,
        campaign_concept: campaign_concept || {
          mood: 'professional',
          color_tone: 'warm',
          style: 'modern'
        }
      })
    })

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.statusText}`)
    }

    const data = await response.json()
    return NextResponse.json(data)

  } catch (error) {
    console.error('콘티 블록 생성 실패:', error)
    return NextResponse.json(
      { error: '콘티 블록 생성에 실패했습니다' },
      { status: 500 }
    )
  }
}
