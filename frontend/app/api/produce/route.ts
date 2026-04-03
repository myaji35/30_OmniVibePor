import { NextRequest, NextResponse } from 'next/server'

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * POST /api/produce — 프레젠테이션/나레이션 생성 프록시 + fallback
 * ?type=presentation | narration
 */
export async function POST(request: NextRequest) {
  const body = await request.json()
  const type = request.nextUrl.searchParams.get('type') || body.format || 'presentation'

  // 백엔드 프록시 시도
  try {
    const res = await fetch(`${BACKEND}/api/v1/produce/${type}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30000),
    })
    if (res.ok) return NextResponse.json(await res.json())
  } catch { /* fallback */ }

  // Fallback: 로컬 생성
  const ts = Date.now()

  if (type === 'narration') {
    // edge-tts는 서버 사이드에서만 실행 가능 → 안내 메시지
    return NextResponse.json({
      filename: `narration_${ts}.mp3`,
      download_url: null,
      size_human: '—',
      voice: body.voice || 'ko-KR-SunHiNeural',
      message: '나레이션 생성은 백엔드 서버가 필요합니다. backend를 실행해주세요.',
      fallback: true,
    })
  }

  // presentation fallback: HTML 슬라이드 생성
  const script = body.script || ''
  const brand = body.brand_name || 'OmniVibe Pro'
  const lines = script.split('\n').filter((l: string) => l.trim())

  const slides: { title: string; bullets: string[] }[] = []
  let currentTitle = ''
  let currentBullets: string[] = []

  for (const line of lines) {
    if (line.startsWith('[') && line.includes(']')) {
      if (currentTitle || currentBullets.length) {
        slides.push({ title: currentTitle || 'Slide', bullets: currentBullets })
      }
      currentTitle = line.replace(/[\[\]]/g, '').trim()
      currentBullets = []
    } else {
      currentBullets.push(line.trim())
    }
  }
  if (currentTitle || currentBullets.length) {
    slides.push({ title: currentTitle || 'Slide', bullets: currentBullets })
  }
  if (!slides.length) {
    slides.push({ title: 'Content', bullets: lines.slice(0, 5) })
  }

  return NextResponse.json({
    filename: `presentation_${ts}.html`,
    download_url: null,
    slide_count: slides.length,
    slides,
    message: `${slides.length}슬라이드 미리보기 생성됨 (HTML 파일 저장은 백엔드 필요)`,
    fallback: true,
  })
}
