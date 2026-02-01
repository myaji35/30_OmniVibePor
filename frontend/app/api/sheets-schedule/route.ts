import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const spreadsheetId = searchParams.get('spreadsheet_id')

    if (!spreadsheetId) {
      return NextResponse.json(
        { success: false, message: 'spreadsheet_id is required' },
        { status: 400 }
      )
    }

    const response = await fetch(
      `http://localhost:8000/api/v1/sheets/schedule/${spreadsheetId}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Schedule fetch failed:', error)
    return NextResponse.json(
      {
        success: false,
        message: 'Backend API 연결 실패'
      },
      { status: 503 }
    )
  }
}
