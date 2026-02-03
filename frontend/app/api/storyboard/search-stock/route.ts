import { NextRequest, NextResponse } from 'next/server'

/**
 * GET /api/storyboard/search-stock?query=keyword
 * Unsplash API를 통한 스톡 이미지 검색
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const query = searchParams.get('query')

    if (!query) {
      return NextResponse.json(
        { error: '검색 키워드를 입력해주세요' },
        { status: 400 }
      )
    }

    // Unsplash API 호출
    const unsplashAccessKey = process.env.UNSPLASH_ACCESS_KEY
    if (!unsplashAccessKey) {
      // 환경 변수가 없으면 더미 데이터 반환
      return NextResponse.json({
        images: [
          'https://images.unsplash.com/photo-1496917756835-20cb06e75b4e?w=800',
          'https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800',
          'https://images.unsplash.com/photo-1484807352052-23338990c6c6?w=800',
          'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800',
        ]
      })
    }

    const response = await fetch(
      `https://api.unsplash.com/search/photos?query=${encodeURIComponent(query)}&per_page=12&orientation=landscape`,
      {
        headers: {
          'Authorization': `Client-ID ${unsplashAccessKey}`
        }
      }
    )

    if (!response.ok) {
      throw new Error(`Unsplash API error: ${response.statusText}`)
    }

    const data = await response.json()
    const images = data.results.map((result: any) => result.urls.regular)

    return NextResponse.json({ images })

  } catch (error) {
    console.error('스톡 이미지 검색 실패:', error)
    return NextResponse.json(
      { error: '스톡 이미지 검색에 실패했습니다' },
      { status: 500 }
    )
  }
}
