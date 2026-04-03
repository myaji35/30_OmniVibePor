import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * POST /api/strategy — 전략 생성 프록시
 * 백엔드 연결 시 프록시, 미연결 시 로컬 fallback
 */
export async function POST(request: NextRequest) {
  const body = await request.json()
  const isPreview = request.nextUrl.searchParams.get('preview') === 'true'

  // 백엔드 연결 시도
  try {
    const endpoint = isPreview ? 'preview' : 'generate'
    const res = await fetch(`${BACKEND_URL}/api/v1/strategy/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(5000),
    })

    if (res.ok) {
      return NextResponse.json(await res.json())
    }
  } catch {
    // 백엔드 미연결 → fallback
  }

  // 로컬 fallback 전략 생성
  const formats = body.channels || body.formats || ['promo', 'explainer']
  const weeks = body.duration_weeks || 4
  const brandName = body.brand_name || 'Brand'
  const goal = body.business_goal || '목표'
  const audience = body.target_audience || '타겟'
  const tone = body.tone || 'professional'

  const FORMAT_DEFAULTS: Record<string, { type: string; freq: string; kpi: string }> = {
    promo: { type: '홍보 영상 (2~3분)', freq: '주 1회', kpi: '조회수, 전환율' },
    explainer: { type: '설명 영상 (3~5분)', freq: '주 1회', kpi: '시청 완료율, 문의' },
    presentation: { type: '프레젠테이션 (10~15슬라이드)', freq: '격주 1회', kpi: '다운로드, 공유' },
    shorts: { type: '숏폼 (60초)', freq: '주 2회', kpi: '조회수, 도달' },
  }

  const DAYS = ['월', '화', '수', '목', '금']

  const channelStrategies = formats.map((f: string) => {
    const d = FORMAT_DEFAULTS[f] || { type: '콘텐츠', freq: '주 1회', kpi: '도달' }
    return {
      channel: f,
      goal: `${goal} — ${f} 포맷 활용`,
      content_type: d.type,
      posting_frequency: d.freq,
      key_topics: [`${brandName} 소개`, '고객 후기', '활용 팁'],
      tone,
      cta: '자세히 알아보기',
      kpi: d.kpi,
    }
  })

  const calendar: any[] = []
  for (const f of formats) {
    const d = FORMAT_DEFAULTS[f] || { freq: '주 1회' }
    const freq = d.freq.includes('2') ? 2 : 1
    for (let week = 1; week <= weeks; week++) {
      for (let i = 0; i < freq; i++) {
        calendar.push({
          week,
          day: DAYS[(i + formats.indexOf(f)) % DAYS.length],
          channel: f,
          content_type: (FORMAT_DEFAULTS[f]?.type || '콘텐츠').split(' ')[0],
          topic: `Week ${week} — ${brandName} ${f} 콘텐츠 ${i + 1}`,
          hook: `${brandName}의 핵심 가치를 전달합니다`,
          cta: '지금 시작하세요',
          estimated_duration: f === 'shorts' ? 60 : f === 'promo' ? 150 : 180,
        })
      }
    }
  }

  return NextResponse.json({
    brand_name: brandName,
    business_goal: goal,
    target_audience: audience,
    overall_strategy: `${brandName}의 ${goal}을 달성하기 위해 ${formats.join(', ')} 포맷을 활용한 영상 콘텐츠 전략입니다.`,
    channel_strategies: channelStrategies,
    content_calendar: calendar,
    total_contents: calendar.length,
    estimated_weekly_hours: calendar.length / weeks * 2,
    generated_at: new Date().toISOString(),
  })
}
