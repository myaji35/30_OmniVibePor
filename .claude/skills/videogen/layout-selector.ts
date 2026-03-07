/**
 * VIDEOGEN — Layout Selector
 * 씬 내용 분석 → 7종 레이아웃 자동 결정
 *
 * 실행: npx ts-node .claude/skills/videogen/layout-selector.ts
 * 입력: videogen/workspace/scenes.json (scene-analyzer 출력)
 * 출력: videogen/workspace/scenes.json (layout 필드 추가)
 */

import * as fs from 'fs'
import * as path from 'path'
import type { Scene, ScenesJson } from './scene-analyzer'

// ── 레이아웃 타입 ─────────────────────────────────────

export type LayoutType =
  | 'text-center'   // 중앙 대형 텍스트 (기본)
  | 'infographic'   // 카운터/수치 중앙집중
  | 'list-reveal'   // 목록 순차 등장
  | 'text-image'    // 텍스트 + 이미지 분할
  | 'graph-focus'   // 그래프/차트 중앙
  | 'split-screen'  // 2분할 비교
  | 'full-visual'   // 전체 배경 + 자막 오버레이

// ── 헬퍼 함수 ────────────────────────────────────────

function hasNumber(text: string): boolean {
  return /\d+/.test(text)
}

function isStatOrPercentage(text: string): boolean {
  return /\d+[%배억원만천]|\d+\.\d+배|\+\d+|\-\d+%/.test(text)
}

function hasBulletOrList(text: string): boolean {
  return /첫째|둘째|셋째|넷째|①|②|③|④|1\.|2\.|3\.|4\.|•|-\s/.test(text)
}

function hasComparison(text: string): boolean {
  return /vs\.?|versus|비교|대비|반면|차이|vs\s|보다\s더/.test(text)
}

function hasGraph(text: string): boolean {
  return /그래프|차트|통계|데이터|추이|성장률|상승|하락|트렌드/.test(text)
}

function hasImage(text: string): boolean {
  return /사진|이미지|화면|모습|장면|보면/.test(text)
}

// ── 레이아웃 선택 로직 ────────────────────────────────

export function selectLayout(scene: Scene): LayoutType {
  const text = scene.subtitles.map(s => s.text).join(' ')
  const hints = scene.visualHint.split(',')
  const subtitleCount = scene.subtitles.length

  // 1. visualHint 기반 우선 판단
  if (hints.includes('graph'))       return 'graph-focus'
  if (hints.includes('comparison'))  return 'split-screen'

  // 2. 수치/퍼센트가 있으면 인포그래픽
  if (hasNumber(text) && isStatOrPercentage(text)) return 'infographic'

  // 3. 목록형 (자막 4개 이상 or 목록 키워드)
  if (hasBulletOrList(text) || subtitleCount >= 4) return 'list-reveal'

  // 4. 이미지 언급이 있으면 텍스트+이미지
  if (hasImage(text)) return 'text-image'

  // 5. 훅/CTA는 항상 중앙 텍스트
  if (scene.contentType === 'hook') return 'text-center'
  if (scene.contentType === 'cta')  return 'text-center'

  // 6. 기본값
  return 'text-center'
}

// ── 애니메이션 효과 선택 ──────────────────────────────

export type AnimEffect =
  | 'fadeIn'
  | 'slideUp'
  | 'typewriter'
  | 'wordPop'
  | 'highlight'
  | 'counter'
  | 'drawLine'
  | 'glitch'

export function selectAnimation(scene: Scene, layout: LayoutType): AnimEffect {
  if (scene.contentType === 'hook')        return 'glitch'
  if (scene.contentType === 'cta')         return 'wordPop'
  if (layout === 'infographic')            return 'counter'
  if (layout === 'list-reveal')            return 'slideUp'
  if (layout === 'graph-focus')            return 'drawLine'
  if (scene.subtitles[0]?.text?.length > 30) return 'typewriter'
  return 'slideUp'
}

// ── 메인 실행 ─────────────────────────────────────────

const SCENES_JSON = path.resolve('videogen/workspace/scenes.json')

function main() {
  console.log('🎨 VIDEOGEN Layout Selector 시작\n')

  if (!fs.existsSync(SCENES_JSON)) {
    console.error(`❌ scenes.json 없음: ${SCENES_JSON}`)
    console.error('   먼저 scene-analyzer.ts를 실행하세요.')
    process.exit(1)
  }

  const data: ScenesJson = JSON.parse(fs.readFileSync(SCENES_JSON, 'utf-8'))

  console.log(`✅ scenes.json 로드: 씬 ${data.sceneCount}개\n`)
  console.log('  씬별 레이아웃 배정:')

  data.scenes = data.scenes.map(scene => {
    const layout = selectLayout(scene)
    const animation = selectAnimation(scene, layout)
    console.log(`  Scene ${scene.id}: [${scene.contentType.toUpperCase().padEnd(5)}] → ${layout.padEnd(14)} (anim: ${animation})`)
    return { ...scene, layout, animation }
  })

  fs.writeFileSync(SCENES_JSON, JSON.stringify(data, null, 2), 'utf-8')
  console.log('\n✅ 레이아웃 배정 완료:', SCENES_JSON)
}

main()
