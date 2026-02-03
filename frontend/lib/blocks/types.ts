// 스크립트 블록 타입 정의
export interface ScriptBlock {
    id: string
    type: 'hook' | 'body' | 'cta'
    content: string
    duration: number
    effects: BlockEffects
    media: BlockMedia
    timing: BlockTiming
    order: number
}

export interface BlockEffects {
    fadeIn?: boolean
    fadeOut?: boolean
    zoomIn?: boolean
    zoomOut?: boolean
    slide?: 'left' | 'right' | 'up' | 'down' | null
    highlight?: boolean
}

export interface BlockMedia {
    background?: string // 이미지/영상 URL
    overlay?: string
    thumbnail?: string
}

export interface BlockTiming {
    start: number // 초 단위
    end: number
}

export interface AudioTrack {
    id: string
    url: string
    duration: number
    waveform: number[]
    silentRegions: SilentRegion[]
}

export interface SilentRegion {
    start: number
    end: number
    duration: number
}

// 스크립트를 블록으로 자동 분할하는 함수
export function splitScriptIntoBlocks(
    hook: string,
    body: string,
    cta: string
): ScriptBlock[] {
    const blocks: ScriptBlock[] = []
    let currentTime = 0
    let order = 0

    // 훅 블록
    const hookSentences = hook.split(/[.!?]\s+/).filter(s => s.trim())
    hookSentences.forEach((sentence, index) => {
        const duration = estimateDuration(sentence)
        blocks.push({
            id: `hook-${index}`,
            type: 'hook',
            content: sentence.trim() + (sentence.match(/[.!?]$/) ? '' : '.'),
            duration,
            effects: { fadeIn: index === 0 },
            media: {},
            timing: { start: currentTime, end: currentTime + duration },
            order: order++
        })
        currentTime += duration
    })

    // 본문 블록
    const bodySentences = body.split(/[.!?]\s+/).filter(s => s.trim())
    bodySentences.forEach((sentence, index) => {
        const duration = estimateDuration(sentence)
        blocks.push({
            id: `body-${index}`,
            type: 'body',
            content: sentence.trim() + (sentence.match(/[.!?]$/) ? '' : '.'),
            duration,
            effects: {},
            media: {},
            timing: { start: currentTime, end: currentTime + duration },
            order: order++
        })
        currentTime += duration
    })

    // CTA 블록
    const ctaSentences = cta.split(/[.!?]\s+/).filter(s => s.trim())
    ctaSentences.forEach((sentence, index) => {
        const duration = estimateDuration(sentence)
        blocks.push({
            id: `cta-${index}`,
            type: 'cta',
            content: sentence.trim() + (sentence.match(/[.!?]$/) ? '' : '.'),
            duration,
            effects: { highlight: true, fadeOut: index === ctaSentences.length - 1 },
            media: {},
            timing: { start: currentTime, end: currentTime + duration },
            order: order++
        })
        currentTime += duration
    })

    return blocks
}

// 문장 길이로 대략적인 재생 시간 추정 (한글 기준)
function estimateDuration(text: string): number {
    // 한글: 초당 약 4-5자
    // 영어: 초당 약 2-3단어
    const koreanChars = (text.match(/[가-힣]/g) || []).length
    const englishWords = (text.match(/[a-zA-Z]+/g) || []).length

    const koreanDuration = koreanChars / 4.5
    const englishDuration = englishWords / 2.5

    return Math.max(2, Math.ceil(koreanDuration + englishDuration))
}

// 블록 순서 재정렬
export function reorderBlocks(blocks: ScriptBlock[]): ScriptBlock[] {
    let currentTime = 0

    return blocks
        .sort((a, b) => a.order - b.order)
        .map(block => ({
            ...block,
            timing: {
                start: currentTime,
                end: currentTime + block.duration
            },
            order: blocks.indexOf(block)
        }))
        .map(block => {
            currentTime = block.timing.end
            return block
        })
}

// 블록 타입별 색상 반환
export function getBlockColor(type: ScriptBlock['type']): string {
    switch (type) {
        case 'hook':
            return 'bg-red-500'
        case 'body':
            return 'bg-blue-500'
        case 'cta':
            return 'bg-green-500'
        default:
            return 'bg-gray-500'
    }
}

// 블록 타입별 아이콘 반환
export function getBlockIcon(type: ScriptBlock['type']): string {
    switch (type) {
        case 'hook':
            return '🔵'
        case 'body':
            return '🟢'
        case 'cta':
            return '🔴'
        default:
            return '⚪'
    }
}
