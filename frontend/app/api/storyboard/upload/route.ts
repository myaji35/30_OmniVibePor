import { NextRequest, NextResponse } from 'next/server'
import { writeFile } from 'fs/promises'
import { join } from 'path'

/**
 * POST /api/storyboard/upload
 * 배경 이미지/영상 파일 업로드
 */
export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File

    if (!file) {
      return NextResponse.json(
        { error: '파일을 선택해주세요' },
        { status: 400 }
      )
    }

    // 파일 타입 검증
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'video/mp4', 'video/webm']
    if (!allowedTypes.includes(file.type)) {
      return NextResponse.json(
        { error: '지원하지 않는 파일 형식입니다' },
        { status: 400 }
      )
    }

    // 파일 크기 검증 (최대 50MB)
    const maxSize = 50 * 1024 * 1024 // 50MB
    if (file.size > maxSize) {
      return NextResponse.json(
        { error: '파일 크기는 최대 50MB까지 가능합니다' },
        { status: 400 }
      )
    }

    // 파일 저장
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)

    // 파일명 생성 (타임스탬프 + 원본 이름)
    const timestamp = Date.now()
    const ext = file.name.split('.').pop()
    const filename = `storyboard-${timestamp}.${ext}`

    // public/uploads 디렉토리에 저장
    const uploadDir = join(process.cwd(), 'public', 'uploads')
    const filepath = join(uploadDir, filename)

    // 디렉토리가 없으면 생성
    try {
      await writeFile(filepath, buffer)
    } catch (error) {
      // 디렉토리 생성 필요
      const { mkdir } = await import('fs/promises')
      await mkdir(uploadDir, { recursive: true })
      await writeFile(filepath, buffer)
    }

    // URL 반환
    const url = `/uploads/${filename}`

    return NextResponse.json({
      url,
      filename,
      size: file.size,
      type: file.type
    })

  } catch (error) {
    console.error('파일 업로드 실패:', error)
    return NextResponse.json(
      { error: '파일 업로드에 실패했습니다' },
      { status: 500 }
    )
  }
}
