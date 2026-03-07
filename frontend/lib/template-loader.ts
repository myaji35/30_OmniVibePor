import { REMOTION_SHOWCASE } from '@/data/remotion-showcase'
import type { ScriptBlock } from '@/lib/blocks/types'

export interface TemplatePreset {
  id: string
  name: string
  duration: number
  sceneCount: number
  tone: string[]
  platform: string[]
  githubUrl?: string
  liveUrl?: string
  authorName?: string
  description: string
}

export function loadTemplatePreset(templateId: string): TemplatePreset | null {
  const item = REMOTION_SHOWCASE.find((t) => t.id === templateId)
  if (!item) return null
  return {
    id: item.id,
    name: item.name,
    duration: item.duration,
    sceneCount: item.sceneCount,
    tone: item.tone,
    platform: item.platform,
    githubUrl: item.githubUrl,
    liveUrl: item.liveUrl,
    authorName: item.authorName,
    description: item.description,
  }
}

export function generateTemplateBlocks(preset: TemplatePreset): ScriptBlock[] {
  const blocks: ScriptBlock[] = []
  const perScene = Math.floor(preset.duration / preset.sceneCount)
  let cursor = 0

  // hook
  blocks.push({
    id: 'hook-0',
    type: 'hook',
    content: `[${preset.name}] 후킹 문구를 입력하세요`,
    duration: perScene,
    effects: { fadeIn: true },
    media: {},
    timing: { start: cursor, end: cursor + perScene },
    order: 0,
  })
  cursor += perScene

  // body
  const bodyCount = Math.max(1, preset.sceneCount - 2)
  for (let i = 0; i < bodyCount; i++) {
    blocks.push({
      id: `body-${i}`,
      type: 'body',
      content: `본문 ${i + 1}: 내용을 입력하세요`,
      duration: perScene,
      effects: {},
      media: {},
      timing: { start: cursor, end: cursor + perScene },
      order: i + 1,
    })
    cursor += perScene
  }

  // cta
  blocks.push({
    id: 'cta-0',
    type: 'cta',
    content: '좋아요와 구독 부탁드립니다!',
    duration: perScene,
    effects: { highlight: true, fadeOut: true },
    media: {},
    timing: { start: cursor, end: cursor + perScene },
    order: preset.sceneCount - 1,
  })

  return blocks
}
