import { NextRequest, NextResponse } from 'next/server'
import { createCampaign } from '@/lib/db/service'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()

    const campaign = await createCampaign({
      client_id: body.client_id,
      name: body.name,
      description: body.description || null,
      start_date: body.start_date || new Date().toISOString().split('T')[0],
      end_date: body.end_date || null,
      status: body.status || 'active',
      concept_gender: body.concept_gender || null,
      concept_tone: body.concept_tone || null,
      concept_style: body.concept_style || null,
      target_duration: body.target_duration || null,
      voice_id: body.voice_id || null,
      voice_name: body.voice_name || null,
      bgm_volume: body.bgm_volume !== undefined ? body.bgm_volume : 0.3,
      publish_schedule: body.publish_schedule || null,
      auto_deploy: body.auto_deploy ? true : false
    })

    return NextResponse.json({
      success: true,
      campaign
    })
  } catch (error: any) {
    console.error('Campaign creation failed:', error)
    return NextResponse.json({
      success: false,
      error: error.message
    }, { status: 500 })
  }
}

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const clientId = searchParams.get('client_id')

    if (!clientId) {
      return NextResponse.json({
        success: false,
        error: 'client_id is required'
      }, { status: 400 })
    }

    const { getCampaignsByClient } = await import('@/lib/db/service')
    const campaigns = await getCampaignsByClient(parseInt(clientId))

    return NextResponse.json({
      success: true,
      campaigns
    })
  } catch (error: any) {
    console.error('Failed to fetch campaigns:', error)
    return NextResponse.json({
      success: false,
      error: error.message
    }, { status: 500 })
  }
}
