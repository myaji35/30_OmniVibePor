import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const campaignId = params.id
    const formData = await request.formData()

    // Backend API로 파일 전달 (Cloudinary 업로드)
    const response = await fetch(`${BACKEND_URL}/api/v1/campaigns/${campaignId}/resources`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(
        { success: false, error: error.detail || 'Upload failed' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json({ success: true, ...data })
  } catch (error) {
    console.error('Resource upload error:', error)
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }
}
