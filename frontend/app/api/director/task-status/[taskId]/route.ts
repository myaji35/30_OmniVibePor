import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function GET(
  _request: NextRequest,
  { params }: { params: { taskId: string } }
) {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/director/task-status/${params.taskId}`
    )

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('Director task-status proxy error:', error)
    return NextResponse.json({ error: '상태 확인 실패' }, { status: 500 })
  }
}
