import { NextRequest, NextResponse } from 'next/server'
import { createContentSchedule, getContentSchedulesByCampaign, getAllContentSchedules } from '@/lib/db/service'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()

    if (!body.campaign_id || !body.subtitle) {
      return NextResponse.json({
        success: false,
        error: 'campaign_id와 subtitle은 필수입니다'
      }, { status: 400 })
    }

    const contentId = await createContentSchedule({
      campaign_id: body.campaign_id,
      subtitle: body.subtitle,
      topic: body.topic || '',
      platform: body.platform || 'Youtube',
      publish_date: body.publish_date || new Date().toISOString().split('T')[0],
      status: body.status || 'draft',
      target_audience: body.target_audience || null,
      keywords: body.keywords || null,
      notes: body.notes || null
    })

    return NextResponse.json({
      success: true,
      content_id: contentId,
      message: '콘텐츠가 추가되었습니다'
    })
  } catch (error: any) {
    console.error('콘텐츠 생성 실패:', error)
    return NextResponse.json({
      success: false,
      error: error.message
    }, { status: 500 })
  }
}

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const campaignId = searchParams.get('campaign_id')

    let contents;

    if (campaignId) {
      contents = await getContentSchedulesByCampaign(parseInt(campaignId))
    } else {
      // campaign_id가 없으면 전체 목록 반환
      contents = await getAllContentSchedules()
    }

    return NextResponse.json({
      success: true,
      contents
    })
  } catch (error: any) {
    console.error('콘텐츠 조회 실패:', error)
    return NextResponse.json({
      success: false,
      error: error.message
    }, { status: 500 })
  }
}
