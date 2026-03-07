/**
 * VIDEOGEN — Scene Analyzer
 * SRT 자막 파일을 파싱하여 씬(Scene) 구조로 변환
 *
 * 실행: npx ts-node .claude/skills/videogen/scene-analyzer.ts
 * 입력: videogen/input/subtitles.srt
 * 출력: videogen/workspace/scenes.json
 */

import * as fs from 'fs'
import * as path from 'path'

// ── 타입 정의 ────────────────────────────────────────

export interface SubtitleToken {
  index: number
  startMs: number
  endMs: number
  text: string
}

export interface Scene {
  id: number
  startMs: number
  endMs: number
  durationMs: number
  durationFrames: number  // 30fps 기준
  subtitles: SubtitleToken[]
  layout: string          // layout-selector가 채움
  contentType: 'hook' | 'intro' | 'body' | 'cta'
  visualHint: string      // 레이아웃 선택 힌트
}

export interface ScenesJson {
  totalDurationMs: number
  totalDurationFrames: number
  sceneCount: number
  subtitleCount: number
  fps: number
  scenes: Scene[]
  generatedAt: string
}

// ── 설정 ─────────────────────────────────────────────

const INPUT_SRT  = path.resolve('videogen/input/subtitles.srt')
const OUTPUT_JSON = path.resolve('videogen/workspace/scenes.json')
const SCENE_GAP_THRESHOLD_MS = 1500  // 자막 간 gap > 1.5초 → 씬 분리
const FPS = 30

// ── SRT 타임코드 파싱 ─────────────────────────────────

function parseTimecode(tc: string): number {
  // "00:01:23,456" → ms
  const [hms, ms] = tc.trim().split(',')
  const [h, m, s] = hms.split(':').map(Number)
  return (h * 3600 + m * 60 + s) * 1000 + Number(ms)
}

// ── SRT 파싱 ─────────────────────────────────────────

function parseSRT(content: string): SubtitleToken[] {
  const tokens: SubtitleToken[] = []
  // SRT 블록: 숫자\n타임코드\n텍스트\n\n
  const blocks = content.trim().split(/\n\n+/)

  for (const block of blocks) {
    const lines = block.trim().split('\n')
    if (lines.length < 2) continue

    const index = parseInt(lines[0].trim(), 10)
    const timeLine = lines[1]
    const textLines = lines.slice(2)

    if (!timeLine.includes('-->')) continue

    const [startTc, endTc] = timeLine.split('-->').map(s => s.trim())
    const text = textLines.join(' ').replace(/<[^>]+>/g, '').trim() // HTML 태그 제거

    if (!text) continue

    tokens.push({
      index,
      startMs: parseTimecode(startTc),
      endMs:   parseTimecode(endTc),
      text,
    })
  }

  return tokens.sort((a, b) => a.startMs - b.startMs)
}

// ── 씬 경계 판단 ──────────────────────────────────────

function groupIntoScenes(tokens: SubtitleToken[]): SubtitleToken[][] {
  if (tokens.length === 0) return []

  const scenes: SubtitleToken[][] = []
  let current: SubtitleToken[] = [tokens[0]]

  for (let i = 1; i < tokens.length; i++) {
    const prev = tokens[i - 1]
    const curr = tokens[i]
    const gap = curr.startMs - prev.endMs

    if (gap > SCENE_GAP_THRESHOLD_MS) {
      scenes.push(current)
      current = [curr]
    } else {
      current.push(curr)
    }
  }
  scenes.push(current)
  return scenes
}

// ── contentType 자동 추론 ─────────────────────────────

function inferContentType(
  sceneIndex: number,
  totalScenes: number,
  startMs: number,
  totalDurationMs: number
): 'hook' | 'intro' | 'body' | 'cta' {
  if (sceneIndex === 0) return 'hook'
  if (sceneIndex === totalScenes - 1) return 'cta'
  if (startMs / totalDurationMs < 0.15) return 'intro'
  return 'body'
}

// ── visualHint 생성 ───────────────────────────────────

function buildVisualHint(subtitles: SubtitleToken[], contentType: string): string {
  const text = subtitles.map(s => s.text).join(' ')
  const hints: string[] = []

  // 수치 포함 여부
  if (/\d+[%억원만천배]|\d+\.\d+/.test(text)) hints.push('numbers')
  // 목록 키워드
  if (/첫째|둘째|셋째|①|②|③|1\.|2\.|3\./.test(text)) hints.push('list')
  // 비교 키워드
  if (/vs|versus|비교|대비|반면|차이/.test(text)) hints.push('comparison')
  // 그래프 키워드
  if (/그래프|차트|통계|데이터|추이|성장/.test(text)) hints.push('graph')
  // 이미지 키워드
  if (/사진|이미지|모습|장면|화면/.test(text)) hints.push('image')

  if (contentType === 'hook') hints.push('impact')
  if (contentType === 'cta')  hints.push('action')

  return hints.join(',') || 'text'
}

// ── 메인 실행 ─────────────────────────────────────────

function main() {
  console.log('🎬 VIDEOGEN Scene Analyzer 시작\n')

  // 입력 파일 확인
  if (!fs.existsSync(INPUT_SRT)) {
    console.error(`❌ 입력 파일 없음: ${INPUT_SRT}`)
    console.error('   videogen/input/subtitles.srt 파일을 먼저 준비하세요.')
    process.exit(1)
  }

  const srtContent = fs.readFileSync(INPUT_SRT, 'utf-8')
  console.log(`✅ SRT 파일 로드: ${INPUT_SRT}`)

  // 파싱
  const tokens = parseSRT(srtContent)
  console.log(`✅ 자막 토큰 파싱: ${tokens.length}개`)

  if (tokens.length === 0) {
    console.error('❌ 파싱된 자막이 없습니다. SRT 형식을 확인하세요.')
    process.exit(1)
  }

  // 씬 그룹핑
  const sceneGroups = groupIntoScenes(tokens)
  const totalDurationMs = tokens[tokens.length - 1].endMs

  // Scene 객체 생성
  const scenes: Scene[] = sceneGroups.map((group, i) => {
    const startMs = group[0].startMs
    const endMs   = group[group.length - 1].endMs
    const durationMs = endMs - startMs
    const contentType = inferContentType(i, sceneGroups.length, startMs, totalDurationMs)
    const visualHint = buildVisualHint(group, contentType)

    return {
      id:             i + 1,
      startMs,
      endMs,
      durationMs,
      durationFrames: Math.round(durationMs / 1000 * FPS),
      subtitles:      group,
      layout:         '',   // layout-selector가 채움
      contentType,
      visualHint,
    }
  })

  // 결과 JSON
  const result: ScenesJson = {
    totalDurationMs,
    totalDurationFrames: Math.round(totalDurationMs / 1000 * FPS),
    sceneCount:    scenes.length,
    subtitleCount: tokens.length,
    fps:           FPS,
    scenes,
    generatedAt:   new Date().toISOString(),
  }

  // 출력 디렉토리 보장
  const outDir = path.dirname(OUTPUT_JSON)
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true })

  fs.writeFileSync(OUTPUT_JSON, JSON.stringify(result, null, 2), 'utf-8')

  // 결과 출력
  console.log('\n📊 분석 결과')
  console.log('─────────────────────────────────────')
  console.log(`  총 재생시간: ${(totalDurationMs / 1000).toFixed(1)}초`)
  console.log(`  총 자막 수:  ${tokens.length}개`)
  console.log(`  씬 수:       ${scenes.length}개`)
  console.log('\n  씬별 요약:')
  scenes.forEach(s => {
    console.log(`  Scene ${s.id}: [${s.contentType.toUpperCase().padEnd(5)}] ` +
      `${(s.durationMs/1000).toFixed(1)}s  ` +
      `자막${s.subtitles.length}개  ` +
      `hint:${s.visualHint}`)
  })
  console.log('\n✅ 출력 완료:', OUTPUT_JSON)
}

main()
