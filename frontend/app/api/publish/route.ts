import { NextRequest, NextResponse } from 'next/server'

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 로컬 임시 저장소
let localHistory: any[] = []
let localFeedback: any[] = []

/**
 * GET /api/publish — channels 또는 history
 * ?action=channels | history
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get('action') || 'channels'

  // 백엔드 프록시 시도
  try {
    const endpoint = action === 'channels' ? 'channels' : `history?limit=20`
    const res = await fetch(`${BACKEND}/api/v1/publish/${endpoint}`, {
      signal: AbortSignal.timeout(3000),
    })
    if (res.ok) return NextResponse.json(await res.json())
  } catch { /* fallback */ }

  // Fallback
  if (action === 'channels') {
    return NextResponse.json({
      channels: [
        { id: 'video', name: 'MP4 영상', formats: ['mp4'], status: 'ready', api_connected: true, description: 'Remotion 렌더링 영상 내보내기' },
        { id: 'presentation', name: '프레젠테이션', formats: ['html', 'pdf'], status: 'ready', api_connected: true, description: 'HTML 슬라이드 프레젠테이션' },
        { id: 'narration', name: 'AI 나레이션', formats: ['mp3'], status: 'ready', api_connected: true, description: 'edge-tts 한국어 음성 8종' },
        { id: 'shorts', name: '숏폼 (60초)', formats: ['mp4'], status: 'ready', api_connected: true, description: '60초 이내 숏폼 영상' },
      ],
    })
  }

  // history
  return NextResponse.json({ total: localHistory.length, items: localHistory.slice(0, 20) })
}

/**
 * POST /api/publish — schedule 또는 feedback
 * ?action=schedule | feedback
 */
export async function POST(request: NextRequest) {
  const action = request.nextUrl.searchParams.get('action') || 'schedule'
  const body = await request.json()

  // 백엔드 프록시 시도
  try {
    const res = await fetch(`${BACKEND}/api/v1/publish/${action}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(5000),
    })
    if (res.ok) return NextResponse.json(await res.json())
  } catch { /* fallback */ }

  // Fallback: 로컬 저장
  if (action === 'schedule') {
    const id = `pub_${Date.now().toString(36)}`
    const item = {
      publish_id: id,
      channel: body.channel || 'video',
      status: body.schedule_at ? 'scheduled' : 'published',
      scheduled_at: body.schedule_at || null,
      published_at: body.schedule_at ? null : new Date().toISOString(),
      title: body.title,
      message: body.schedule_at ? '예약 완료 (로컬)' : '발행 완료 (로컬)',
    }
    localHistory.unshift({
      id: localHistory.length + 1,
      topic: body.title,
      platform: body.channel || 'video',
      status: item.status,
      publish_date: item.published_at || item.scheduled_at,
    })
    return NextResponse.json(item)
  }

  if (action === 'feedback') {
    localFeedback.push({ ...body, recorded_at: new Date().toISOString() })
    const score = body.score || 0
    return NextResponse.json({
      status: 'recorded',
      content_id: body.content_id,
      score,
      tags: score >= 8 ? ['high_performer'] : score >= 5 ? ['average'] : ['needs_improvement'],
      message: '성과 데이터가 기록되었습니다 (로컬).',
    })
  }

  return NextResponse.json({ error: 'Unknown action' }, { status: 400 })
}
