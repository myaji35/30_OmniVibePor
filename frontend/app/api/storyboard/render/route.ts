import { NextRequest, NextResponse } from 'next/server'

/**
 * POST /api/storyboard/render
 * 콘티 블록으로 영상 렌더링 요청
 */
export async function POST(request: NextRequest) {
  try {
    const { blocks } = await request.json()

    if (!blocks || !Array.isArray(blocks) || blocks.length === 0) {
      return NextResponse.json(
        { error: '콘티 블록이 없습니다' },
        { status: 400 }
      )
    }

    // Backend API 호출 (Director Agent)
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/api/v1/video/render-storyboard`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        storyboard_blocks: blocks,
        render_options: {
          resolution: '1920x1080',
          fps: 30,
          format: 'mp4',
          quality: 'high'
        }
      })
    })

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.statusText}`)
    }

    const data = await response.json()

    return NextResponse.json({
      task_id: data.task_id,
      status: 'processing',
      message: '영상 렌더링이 시작되었습니다',
      estimated_time: data.estimated_time || 120 // 초 단위
    })

  } catch (error) {
    console.error('영상 렌더링 실패:', error)
    return NextResponse.json(
      { error: '영상 렌더링 요청에 실패했습니다' },
      { status: 500 }
    )
  }
}

/**
 * GET /api/storyboard/render?task_id=xxx
 * 영상 렌더링 상태 조회
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const taskId = searchParams.get('task_id')

    if (!taskId) {
      return NextResponse.json(
        { error: 'task_id가 필요합니다' },
        { status: 400 }
      )
    }

    // Backend API 호출
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/api/v1/video/render-status/${taskId}`)

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.statusText}`)
    }

    const data = await response.json()

    return NextResponse.json({
      task_id: taskId,
      status: data.status, // 'processing' | 'completed' | 'failed'
      progress: data.progress, // 0-100
      video_url: data.video_url,
      error: data.error
    })

  } catch (error) {
    console.error('렌더링 상태 조회 실패:', error)
    return NextResponse.json(
      { error: '렌더링 상태 조회에 실패했습니다' },
      { status: 500 }
    )
  }
}
