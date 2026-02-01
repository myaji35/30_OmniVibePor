import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const response = await fetch('http://localhost:8000/api/v1/sheets/status', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend API returned ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Sheets status check failed:', error)
    return NextResponse.json(
      {
        available: false,
        message: 'Backend API 연결 실패'
      },
      { status: 503 }
    )
  }
}
