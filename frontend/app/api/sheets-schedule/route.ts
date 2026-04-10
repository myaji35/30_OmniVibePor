import { NextRequest, NextResponse } from 'next/server'
import { getAllContentSchedules } from '@/lib/db/service'

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const page = parseInt(searchParams.get('page') || '1')
    const limit = parseInt(searchParams.get('limit') || '10')
    const search = searchParams.get('search') || ''
    const platform = searchParams.get('platform') || ''
    const status = searchParams.get('status') || ''

    const all = await getAllContentSchedules()

    // 필터링
    let filtered = all
    if (search) {
      const q = search.toLowerCase()
      filtered = filtered.filter((s: any) =>
        (s['소제목'] || s.subtitle || '').toLowerCase().includes(q) ||
        (s['주제'] || s.topic || '').toLowerCase().includes(q) ||
        (s['캠페인명'] || s.campaign_name || '').toLowerCase().includes(q)
      )
    }
    if (platform) {
      filtered = filtered.filter((s: any) =>
        (s['플랫폼'] || s.platform || '').toLowerCase() === platform.toLowerCase()
      )
    }
    if (status) {
      filtered = filtered.filter((s: any) =>
        (s['상태'] || s.status || '').toLowerCase() === status.toLowerCase()
      )
    }

    const total = filtered.length
    const totalPages = Math.ceil(total / limit)
    const start = (page - 1) * limit
    const schedule = filtered.slice(start, start + limit)

    return NextResponse.json({
      success: true,
      schedule,
      count: schedule.length,
      total,
      page,
      limit,
      totalPages,
      filters: { search, platform, status, campaign_id: '' }
    })
  } catch (error: any) {
    console.error('Schedule load error:', error)
    return NextResponse.json({
      success: true,
      schedule: [],
      count: 0,
      total: 0,
      page: 1,
      limit: 10,
      totalPages: 0,
      filters: { search: '', platform: '', status: '', campaign_id: '' }
    })
  }
}
