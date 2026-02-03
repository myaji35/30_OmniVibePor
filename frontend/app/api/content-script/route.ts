import { NextRequest, NextResponse } from 'next/server'
import sqlite3 from 'sqlite3'
import { open, Database } from 'sqlite'
import path from 'path'

let db: Database | null = null

async function getDb() {
  if (!db) {
    const dbPath = path.join(process.cwd(), 'data', 'omnivibe.db')
    db = await open({
      filename: dbPath,
      driver: sqlite3.Database,
    })
  }
  return db
}

// GET: 스크립트 불러오기
export async function GET(req: NextRequest) {
  try {
    const contentId = req.nextUrl.searchParams.get('content_id')

    if (!contentId) {
      return NextResponse.json(
        { success: false, error: 'content_id is required' },
        { status: 400 }
      )
    }

    const database = await getDb()
    const content = await database.get(
      'SELECT script_data FROM content_schedule WHERE id = ?',
      [contentId]
    )

    if (!content) {
      return NextResponse.json(
        { success: false, error: 'Content not found' },
        { status: 404 }
      )
    }

    // script_data가 JSON 문자열이면 파싱
    let scriptData = null
    if (content.script_data) {
      try {
        scriptData = JSON.parse(content.script_data)
      } catch (e) {
        scriptData = null
      }
    }

    return NextResponse.json({
      success: true,
      script_data: scriptData
    })
  } catch (error: any) {
    console.error('스크립트 로드 실패:', error)
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    )
  }
}

// PUT: 스크립트 저장
export async function PUT(req: NextRequest) {
  try {
    const body = await req.json()
    const { content_id, blocks } = body

    if (!content_id) {
      return NextResponse.json(
        { success: false, error: 'content_id is required' },
        { status: 400 }
      )
    }

    if (!blocks || !Array.isArray(blocks)) {
      return NextResponse.json(
        { success: false, error: 'blocks must be an array' },
        { status: 400 }
      )
    }

    const database = await getDb()

    // blocks를 JSON 문자열로 변환
    const scriptDataJson = JSON.stringify(blocks)

    await database.run(
      'UPDATE content_schedule SET script_data = ? WHERE id = ?',
      [scriptDataJson, content_id]
    )

    return NextResponse.json({
      success: true,
      message: 'Script saved successfully'
    })
  } catch (error: any) {
    console.error('스크립트 저장 실패:', error)
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    )
  }
}
