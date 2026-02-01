import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  try {
    const body = await request.json()

    const response = await fetch('http://localhost:8000/api/v1/sheets/connect', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body)
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Sheets connection failed:', error)
    return NextResponse.json(
      {
        success: false,
        message: 'Backend API 연결 실패'
      },
      { status: 503 }
    )
  }
}
