import { NextRequest, NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import path from 'path'
import fs from 'fs'

const execAsync = promisify(exec)
const OUTPUT_DIR = path.join(process.cwd(), 'public', 'rendered')

// 렌더링 가능한 Composition 목록
const COMPOSITIONS = ['promo', 'promo-ko', 'chopd', 'insuregraph', 'bobot-safety']

/**
 * POST /api/render-promo — Remotion CLI로 MP4 렌더링
 */
export async function POST(request: NextRequest) {
  try {
    const { compositionId } = await request.json()

    if (!COMPOSITIONS.includes(compositionId)) {
      return NextResponse.json(
        { error: `Invalid composition: ${compositionId}. Available: ${COMPOSITIONS.join(', ')}` },
        { status: 400 }
      )
    }

    fs.mkdirSync(OUTPUT_DIR, { recursive: true })

    const outputFile = `${compositionId}.mp4`
    const outputPath = path.join(OUTPUT_DIR, outputFile)

    // 기존 파일 삭제
    if (fs.existsSync(outputPath)) {
      fs.unlinkSync(outputPath)
    }

    const entryPoint = path.join(process.cwd(), 'remotion', 'index.ts')
    const cmd = `npx remotion render ${compositionId} ${entryPoint} --output="${outputPath}" --codec=h264`

    const { stdout, stderr } = await execAsync(cmd, {
      cwd: process.cwd(),
      timeout: 300000, // 5분
    })

    if (!fs.existsSync(outputPath)) {
      return NextResponse.json(
        { error: 'Render failed — output file not created', stderr },
        { status: 500 }
      )
    }

    const stats = fs.statSync(outputPath)

    return NextResponse.json({
      success: true,
      compositionId,
      file: outputFile,
      downloadUrl: `/rendered/${outputFile}`,
      size: stats.size,
      sizeHuman: `${(stats.size / 1024 / 1024).toFixed(1)}MB`,
    })
  } catch (error: any) {
    return NextResponse.json(
      { error: `Render failed: ${error.message}` },
      { status: 500 }
    )
  }
}

/**
 * GET /api/render-promo — 렌더링된 파일 목록 조회
 */
export async function GET() {
  try {
    if (!fs.existsSync(OUTPUT_DIR)) {
      return NextResponse.json({ files: [] })
    }

    const files = fs.readdirSync(OUTPUT_DIR)
      .filter(f => f.endsWith('.mp4'))
      .map(f => {
        const stats = fs.statSync(path.join(OUTPUT_DIR, f))
        return {
          name: f,
          compositionId: f.replace('.mp4', ''),
          downloadUrl: `/rendered/${f}`,
          size: stats.size,
          sizeHuman: `${(stats.size / 1024 / 1024).toFixed(1)}MB`,
          createdAt: stats.birthtime.toISOString(),
        }
      })
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())

    return NextResponse.json({ files })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}

/**
 * DELETE /api/render-promo — 렌더링된 파일 삭제
 */
export async function DELETE(request: NextRequest) {
  try {
    const { compositionId } = await request.json()
    const filePath = path.join(OUTPUT_DIR, `${compositionId}.mp4`)

    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: 'File not found' }, { status: 404 })
    }

    fs.unlinkSync(filePath)

    return NextResponse.json({
      success: true,
      deleted: `${compositionId}.mp4`,
    })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
