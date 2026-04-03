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
    // Next.js API Route에서 edge-tts 직접 실행 (Node.js child_process)
    try {
      const { execSync } = await import('child_process')
      const path = await import('path')
      const fs = await import('fs')

      const voice = body.voice || 'ko-KR-SunHiNeural'
      const rate = body.voice_rate || '-5%'
      const text = body.script || ''
      const outputDir = path.join(process.cwd(), 'public', 'rendered')
      fs.mkdirSync(outputDir, { recursive: true })

      const filename = `narration_${ts}.mp3`
      const outputPath = path.join(outputDir, filename)

      // edge-tts CLI 실행
      const escapedText = text.replace(/"/g, '\\"').replace(/\n/g, ' ')
      execSync(
        `edge-tts --voice "${voice}" --rate="${rate}" --text "${escapedText}" --write-media "${outputPath}"`,
        { timeout: 60000 }
      )

      if (fs.existsSync(outputPath)) {
        const size = fs.statSync(outputPath).size
        return NextResponse.json({
          filename,
          download_url: `/rendered/${filename}`,
          size_human: `${Math.round(size / 1024)}KB`,
          voice,
          message: '나레이션 생성 완료',
          fallback: false,
        })
      }
    } catch (e: any) {
      // edge-tts CLI 미설치 시 fallback
      console.warn('edge-tts CLI not available:', e.message)
    }

    return NextResponse.json({
      filename: `narration_${ts}.mp3`,
      download_url: null,
      size_human: '—',
      voice: body.voice || 'ko-KR-SunHiNeural',
      message: 'edge-tts CLI를 설치해주세요: pip install edge-tts',
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
