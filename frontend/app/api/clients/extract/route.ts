/**
 * POST /api/clients/extract — ISS-085 Stage 3
 *
 * 거래처 URL에서 브랜드 자산 자동 추출.
 * Backend brand_extractor_service 호출.
 */
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function POST(request: Request) {
  try {
    const { website_url } = await request.json()

    if (!website_url) {
      return NextResponse.json(
        { success: false, error: 'website_url is required' },
        { status: 400 }
      )
    }

    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8030'

    const resp = await fetch(`${backendUrl}/api/v1/clients/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ website_url }),
    })

    if (!resp.ok) {
      // Backend 미구현 시 fallback: 프론트에서 직접 기본값 반환
      return NextResponse.json({
        success: true,
        extracted: {
          name: new URL(website_url.startsWith('http') ? website_url : `https://${website_url}`).hostname.replace('www.', ''),
          logo_url: null,
          brand_color: '#00A1E0',
          tagline: null,
          address: null,
          phone: null,
          industry: 'general',
        },
        confidence: 0.17,
        fallback: true,
      })
    }

    const data = await resp.json()
    return NextResponse.json({ success: true, ...data })
  } catch (error: any) {
    console.error('Extract error:', error)
    return NextResponse.json(
      { success: false, error: error.message || 'Extraction failed' },
      { status: 500 }
    )
  }
}
