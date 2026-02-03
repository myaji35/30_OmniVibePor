import { NextRequest, NextResponse } from 'next/server'

/**
 * POST /api/storyboard/generate-image
 * AI로 배경 이미지 생성
 */
export async function POST(request: NextRequest) {
  try {
    const { prompt } = await request.json()

    if (!prompt || typeof prompt !== 'string') {
      return NextResponse.json(
        { error: '프롬프트를 입력해주세요' },
        { status: 400 }
      )
    }

    // Backend API 호출 (Google Veo 또는 DALL-E)
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/api/v1/media/generate-image`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt })
    })

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.statusText}`)
    }

    const data = await response.json()
    return NextResponse.json({
      image_url: data.url,
      prompt: prompt
    })

  } catch (error) {
    console.error('AI 이미지 생성 실패:', error)
    return NextResponse.json(
      { error: 'AI 이미지 생성에 실패했습니다' },
      { status: 500 }
    )
  }
}
