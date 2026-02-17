import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function POST(
  request: NextRequest,
  { params }: { params: { campaignId: string; contentId: string } }
) {
  try {
    const body = await request.json()

    const response = await fetch(
      `${BACKEND_URL}/api/v1/storyboard/campaigns/${params.campaignId}/content/${params.contentId}/generate`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }
    )

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('Storyboard campaign/content generate proxy error:', error)
    return NextResponse.json({ error: '스토리보드 생성 실패' }, { status: 500 })
  }
}
