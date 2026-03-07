/**
 * VIDEOGEN — Remotion Code Generator
 * scenes.json → Remotion 컴포넌트 자동 생성
 *
 * 실행: npx ts-node .claude/skills/videogen/remotion-codegen.ts
 * 입력: videogen/workspace/scenes.json (layout-selector 출력)
 * 출력: videogen/workspace/src/compositions/GeneratedVideo.tsx
 *       videogen/workspace/src/scenes/Scene{N}.tsx
 *       videogen/workspace/src/index.ts
 *       videogen/workspace/remotion.config.ts
 */

import * as fs from 'fs'
import * as path from 'path'
import type { ScenesJson, Scene } from './scene-analyzer'

const SCENES_JSON  = path.resolve('videogen/workspace/scenes.json')
const WORKSPACE    = path.resolve('videogen/workspace/src')
const DEV_MODE     = process.env.DEV_MODE === 'true'

// ── 레이아웃 → 컴포넌트 임포트 매핑 ──────────────────

const LAYOUT_COMPONENT: Record<string, string> = {
  'text-center':  'TextCenter',
  'infographic':  'Infographic',
  'list-reveal':  'ListReveal',
  'text-image':   'TextCenter',   // fallback
  'graph-focus':  'Infographic',  // fallback
  'split-screen': 'TextCenter',   // fallback
  'full-visual':  'FullVisual',
}

// ── Scene 컴포넌트 코드 생성 ──────────────────────────

function generateSceneComponent(scene: Scene & { animation?: string }): string {
  const componentName = LAYOUT_COMPONENT[scene.layout] || 'TextCenter'
  const subtitlesJson = JSON.stringify(scene.subtitles, null, 4)
    .split('\n').map((l, i) => i === 0 ? l : '  ' + l).join('\n')

  return `/**
 * Scene ${scene.id} — ${scene.contentType.toUpperCase()}
 * Layout: ${scene.layout}
 * Duration: ${(scene.durationMs / 1000).toFixed(1)}s (${scene.durationFrames}frames)
 * Subtitles: ${scene.subtitles.length}개
 */
import React from 'react'
import { ${componentName} } from '../../../../.claude/skills/videogen/templates/${componentName}'

const SUBTITLES = ${subtitlesJson}

export const Scene${scene.id}: React.FC<{ startFrame: number }> = ({ startFrame }) => (
  <${componentName}
    sceneId={${scene.id}}
    subtitles={SUBTITLES}
    sceneStartFrame={startFrame}
    animation="${scene.animation || 'slideUp'}"
    devMode={${DEV_MODE}}
  />
)
`
}

// ── GeneratedVideo 컴포지션 코드 생성 ─────────────────

function generateComposition(data: ScenesJson): string {
  const imports = data.scenes.map(s => `import { Scene${s.id} } from './scenes/Scene${s.id}'`).join('\n')

  const sequences = data.scenes.map(scene => {
    return `      <Sequence from={${Math.round(scene.startMs / 1000 * data.fps)}} durationInFrames={${scene.durationFrames}}>
        <Scene${scene.id} startFrame={${Math.round(scene.startMs / 1000 * data.fps)}} />
      </Sequence>`
  }).join('\n')

  return `/**
 * VIDEOGEN — Generated Composition
 * 자동 생성됨: ${new Date().toISOString()}
 * 총 씬: ${data.sceneCount}개 | 총 재생시간: ${(data.totalDurationMs / 1000).toFixed(1)}s
 */
import React from 'react'
import { AbsoluteFill, Sequence, Audio } from 'remotion'
${imports}

export const GeneratedVideo: React.FC = () => (
  <AbsoluteFill style={{ background: '#0A0A0A' }}>
    {/* 더빙 오디오 */}
    <Audio src={require('../../../input/dubbing.mp3')} />

    {/* 씬 시퀀스 */}
${sequences}
  </AbsoluteFill>
)
`
}

// ── index.ts 생성 ─────────────────────────────────────

function generateIndex(data: ScenesJson): string {
  return `/**
 * VIDEOGEN — Remotion Entry Point
 */
import { registerRoot, Composition } from 'remotion'
import { GeneratedVideo } from './compositions/GeneratedVideo'

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="GeneratedVideo"
      component={GeneratedVideo}
      durationInFrames={${data.totalDurationFrames}}
      fps={${data.fps}}
      width={1920}
      height={1080}
    />
  </>
)

registerRoot(RemotionRoot)
`
}

// ── remotion.config.ts 생성 ──────────────────────────

function generateRemotionConfig(): string {
  return `import { Config } from '@remotion/cli/config'

Config.setVideoImageFormat('jpeg')
Config.setOverwriteOutput(true)
Config.setOutputLocation('../../output')
`
}

// ── package.json 생성 (workspace용) ──────────────────

function generatePackageJson(): string {
  return JSON.stringify({
    name: 'videogen-workspace',
    version: '1.0.0',
    scripts: {
      render: 'npx remotion render GeneratedVideo',
      preview: 'npx remotion studio',
    },
    dependencies: {
      remotion: '^4.0.0',
      '@remotion/cli': '^4.0.0',
      react: '^18.0.0',
      'react-dom': '^18.0.0',
    },
    devDependencies: {
      typescript: '^5.0.0',
      '@types/react': '^18.0.0',
    },
  }, null, 2)
}

// ── 메인 실행 ─────────────────────────────────────────

function main() {
  console.log('⚙️  VIDEOGEN Remotion Code Generator 시작\n')
  console.log(`   DEV_MODE: ${DEV_MODE ? '✅ ON (씬 번호 오버레이 표시)' : '❌ OFF'}`)

  if (!fs.existsSync(SCENES_JSON)) {
    console.error(`❌ scenes.json 없음: ${SCENES_JSON}`)
    console.error('   먼저 scene-analyzer.ts와 layout-selector.ts를 실행하세요.')
    process.exit(1)
  }

  const data: ScenesJson = JSON.parse(fs.readFileSync(SCENES_JSON, 'utf-8'))

  // 레이아웃 배정 확인
  const unassigned = data.scenes.filter(s => !s.layout)
  if (unassigned.length > 0) {
    console.error(`❌ 레이아웃 미배정 씬: ${unassigned.map(s => s.id).join(', ')}`)
    console.error('   layout-selector.ts를 먼저 실행하세요.')
    process.exit(1)
  }

  // 디렉토리 생성
  const scenesDir = path.join(WORKSPACE, 'scenes')
  const compositionsDir = path.join(WORKSPACE, 'compositions')
  fs.mkdirSync(scenesDir, { recursive: true })
  fs.mkdirSync(compositionsDir, { recursive: true })

  // Scene 컴포넌트 생성
  console.log('\n  씬 컴포넌트 생성:')
  for (const scene of data.scenes) {
    const code = generateSceneComponent(scene as any)
    const filePath = path.join(scenesDir, `Scene${scene.id}.tsx`)
    fs.writeFileSync(filePath, code, 'utf-8')
    console.log(`  ✅ Scene${scene.id}.tsx  [${scene.layout}]`)
  }

  // GeneratedVideo 컴포지션 생성
  const compositionCode = generateComposition(data)
  fs.writeFileSync(path.join(compositionsDir, 'GeneratedVideo.tsx'), compositionCode, 'utf-8')
  console.log('\n  ✅ GeneratedVideo.tsx 생성')

  // index.ts
  fs.writeFileSync(path.join(WORKSPACE, 'index.ts'), generateIndex(data), 'utf-8')
  console.log('  ✅ index.ts 생성')

  // remotion.config.ts
  const workspaceRoot = path.resolve('videogen/workspace')
  fs.writeFileSync(path.join(workspaceRoot, 'remotion.config.ts'), generateRemotionConfig(), 'utf-8')
  console.log('  ✅ remotion.config.ts 생성')

  // package.json (없을 때만)
  const pkgPath = path.join(workspaceRoot, 'package.json')
  if (!fs.existsSync(pkgPath)) {
    fs.writeFileSync(pkgPath, generatePackageJson(), 'utf-8')
    console.log('  ✅ package.json 생성')
  }

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('✅ 코드 생성 완료!')
  console.log(`   총 씬: ${data.sceneCount}개`)
  console.log(`   재생시간: ${(data.totalDurationMs / 1000).toFixed(1)}초`)
  console.log('\n다음 단계:')
  console.log('  cd videogen/workspace && npm install')
  console.log('  DEV_MODE=true npx remotion render GeneratedVideo')
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
}

main()
