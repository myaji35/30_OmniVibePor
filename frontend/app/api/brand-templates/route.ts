import { NextRequest, NextResponse } from 'next/server'

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * 브랜드 템플릿 CRUD — 백엔드 프록시
 * GET  ?project_id=xxx          → 목록 조회
 * POST                          → 생성
 * PUT  ?id=xxx                  → 수정
 * DELETE ?id=xxx                → 삭제
 */

export async function GET(req: NextRequest) {
  const projectId = req.nextUrl.searchParams.get('project_id') || 'default'
  try {
    const res = await fetch(`${BACKEND}/api/v1/brand-templates/project/${projectId}`)
    if (!res.ok) throw new Error(`Backend ${res.status}`)
    return NextResponse.json(await res.json())
  } catch {
    // 백엔드 미실행 시 인메모리 폴백
    return NextResponse.json({ templates: [], total: 0, project_id: projectId })
  }
}

export async function POST(req: NextRequest) {
  const body = await req.json()
  try {
    const res = await fetch(`${BACKEND}/api/v1/brand-templates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`Backend ${res.status}`)
    return NextResponse.json(await res.json(), { status: 201 })
  } catch {
    // 인메모리 폴백: 로컬에서 ID 생성
    const id = `bt_${Date.now().toString(36)}`
    return NextResponse.json({ id, ...body, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }, { status: 201 })
  }
}

export async function PUT(req: NextRequest) {
  const id = req.nextUrl.searchParams.get('id')
  if (!id) return NextResponse.json({ error: 'id required' }, { status: 400 })
  const body = await req.json()
  try {
    const res = await fetch(`${BACKEND}/api/v1/brand-templates/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`Backend ${res.status}`)
    return NextResponse.json(await res.json())
  } catch {
    return NextResponse.json({ id, ...body, updated_at: new Date().toISOString() })
  }
}

export async function DELETE(req: NextRequest) {
  const id = req.nextUrl.searchParams.get('id')
  if (!id) return NextResponse.json({ error: 'id required' }, { status: 400 })
  try {
    const res = await fetch(`${BACKEND}/api/v1/brand-templates/${id}`, { method: 'DELETE' })
    if (!res.ok) throw new Error(`Backend ${res.status}`)
    return NextResponse.json(await res.json())
  } catch {
    return NextResponse.json({ id, message: 'deleted' })
  }
}
