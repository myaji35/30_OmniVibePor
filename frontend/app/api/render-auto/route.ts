import { NextRequest, NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import path from 'path'
import fs from 'fs'

const execAsync = promisify(exec)

/**
 * POST /api/render-auto — 스크립트 텍스트 → ScriptBlock[] → Remotion 영상 자동 렌더
 *
 * 입력: { script, brandName?, primaryColor?, audioUrl? }
 * 출력: MP4 파일 다운로드 URL
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const script: string = body.script || ''
    const brandName: string = body.brandName || 'OmniVibe Pro'
    const primaryColor: string = body.primaryColor || '#6366F1'
    const audioUrl: string = body.audioUrl || ''

    if (!script.trim()) {
      return NextResponse.json({ error: '스크립트를 입력하세요' }, { status: 400 })
    }

    // 스크립트 → ScriptBlock[] 변환
    const blocks = parseScriptToBlocks(script)

    if (blocks.length === 0) {
      return NextResponse.json({ error: '스크립트에서 블록을 추출할 수 없습니다' }, { status: 400 })
    }

    // Remotion inputProps JSON
    const inputProps = {
      blocks,
      audioUrl,
      branding: { logo: '', primaryColor, fontFamily: 'Pretendard' },
    }

    const outputDir = path.join(process.cwd(), 'public', 'rendered')
    fs.mkdirSync(outputDir, { recursive: true })

    const ts = Date.now()
    const filename = `auto_${ts}.mp4`
    const outputPath = path.join(outputDir, filename)
    const propsPath = path.join(outputDir, `props_${ts}.json`)

    // props를 임시 파일로 저장
    fs.writeFileSync(propsPath, JSON.stringify(inputProps))

    const entryPoint = path.join(process.cwd(), 'remotion', 'index.ts')
    const cmd = `npx remotion render auto "${entryPoint}" --output="${outputPath}" --codec=h264 --props="${propsPath}"`

    const { stdout, stderr } = await execAsync(cmd, {
      cwd: process.cwd(),
      timeout: 300000, // 5분
    })

    // props 파일 정리
    if (fs.existsSync(propsPath)) fs.unlinkSync(propsPath)

    if (!fs.existsSync(outputPath)) {
      return NextResponse.json({
        error: '렌더링 실패 — 출력 파일 미생성',
        stderr: stderr?.slice(0, 500),
      }, { status: 500 })
    }

    const stats = fs.statSync(outputPath)

    return NextResponse.json({
      success: true,
      filename,
      downloadUrl: `/rendered/${filename}`,
      size: stats.size,
      sizeHuman: `${(stats.size / 1024 / 1024).toFixed(1)}MB`,
      blocks: blocks.length,
      totalDuration: blocks.reduce((s, b) => Math.max(s, b.startTime + b.duration), 0),
    })
  } catch (error: any) {
    return NextResponse.json({ error: `렌더링 실패: ${error.message}` }, { status: 500 })
  }
}

/**
 * 스크립트 텍스트 → ScriptBlock[] 변환
 *
 * [Hook], [Body], [CTA] 등의 섹션 헤더로 분할.
 * 헤더 없으면 자동으로 hook/body/cta 3분할.
 */
function parseScriptToBlocks(script: string) {
  const lines = script.split('\n').filter(l => l.trim())
  const sections: { type: string; lines: string[] }[] = []
  let currentType = ''
  let currentLines: string[] = []

  const TYPE_MAP: Record<string, string> = {
    'hook': 'hook', '훅': 'hook', '오프닝': 'hook', 'intro': 'intro', '인트로': 'intro',
    'body': 'body', '본문': 'body', '내용': 'body', 'main': 'body',
    'cta': 'cta', '행동유도': 'cta', '마무리': 'cta', 'outro': 'outro', '아웃트로': 'outro',
    'mission': 'body', '미션': 'body', 'impact': 'body', '성과': 'body',
    'problem': 'body', '문제': 'body',
  }

  for (const line of lines) {
    // [Hook], [Body], [CTA] 등의 섹션 헤더 감지
    const headerMatch = line.match(/^\[(.+?)\]/)
    if (headerMatch) {
      if (currentType || currentLines.length) {
        sections.push({ type: currentType || 'body', lines: currentLines })
      }
      const label = headerMatch[1].trim().toLowerCase()
      currentType = TYPE_MAP[label] || 'body'
      currentLines = []
    } else if (line.startsWith('#')) {
      if (currentType || currentLines.length) {
        sections.push({ type: currentType || 'body', lines: currentLines })
      }
      currentType = 'body'
      currentLines = [line.replace(/^#+\s*/, '')]
    } else {
      currentLines.push(line.trim())
    }
  }
  if (currentType || currentLines.length) {
    sections.push({ type: currentType || 'body', lines: currentLines })
  }

  // 섹션이 없으면 전체를 3분할
  if (sections.length === 0) {
    const third = Math.ceil(lines.length / 3)
    sections.push(
      { type: 'hook', lines: lines.slice(0, third) },
      { type: 'body', lines: lines.slice(third, third * 2) },
      { type: 'cta', lines: lines.slice(third * 2) },
    )
  }

  // ScriptBlock[] 생성 — 한글 기준 1글자 = 0.15초
  const CHARS_PER_SECOND = 6.5 // 한국어 평균 발화 속도
  let currentTime = 0

  return sections.map((sec, i) => {
    const text = sec.lines.join('\n')
    const charCount = text.replace(/\s/g, '').length
    const duration = Math.max(3, charCount / CHARS_PER_SECOND + 1) // 최소 3초

    const block = {
      id: i,
      type: sec.type as any,
      text,
      startTime: Math.round(currentTime * 100) / 100,
      duration: Math.round(duration * 100) / 100,
      fontSize: sec.type === 'hook' ? 64 : sec.type === 'cta' ? 48 : 40,
      textAlign: 'center' as const,
    }
    currentTime += duration
    return block
  })
}
