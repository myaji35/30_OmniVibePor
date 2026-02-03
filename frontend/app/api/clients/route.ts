import { NextResponse } from 'next/server'
import { getAllClients, getAllCampaigns } from '@/lib/db/service'

export async function GET() {
  try {
    const clients = await getAllClients()
    const campaigns = await getAllCampaigns()

    return NextResponse.json({
      success: true,
      clients,
      campaigns
    })
  } catch (error) {
    console.error('Error loading clients:', error)
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to load clients'
      },
      { status: 500 }
    )
  }
}
