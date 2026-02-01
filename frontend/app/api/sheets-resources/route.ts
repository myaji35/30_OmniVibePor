import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const spreadsheet_id = searchParams.get('spreadsheet_id')
    const campaign_name = searchParams.get('campaign_name')
    const topic = searchParams.get('topic')

    if (!spreadsheet_id) {
      return NextResponse.json(
        { success: false, message: 'spreadsheet_id is required' },
        { status: 400 }
      )
    }

    let url = `http://localhost:8000/api/v1/sheets/resources/${spreadsheet_id}?`
    if (campaign_name) url += `campaign_name=${encodeURIComponent(campaign_name)}&`
    if (topic) url += `topic=${encodeURIComponent(topic)}&`

    const response = await fetch(url.slice(0, -1), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Resources fetch failed:', error)
    return NextResponse.json(
      {
        success: false,
        message: 'Backend API 연결 실패'
      },
      { status: 503 }
    )
  }
}
